from datetime import datetime
from django.db.models import Sum
from django.utils.decorators import method_decorator

from api_v3.utils import cod_actions, response_access_denied, get_object_or_404, \
    response_error_with_message, response_with_payload, response_incomplete_parameters, response_success_with_message, response_invalid_pagenumber
from api_v3 import constants
from yourguy.models import CODTransaction, DeliveryGuy, OrderDeliveryStatus, DeliveryTeamLead, ProofOfBankDeposit, \
    Picture, Employee
from rest_framework import authentication, viewsets
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated
from api_v3.utils import user_role, log_exception, paginate
from api_v3.push import send_push
import uuid
import pytz
from django.contrib.auth.decorators import user_passes_test

error_message_1 = 'This is a deactivated dg'
response_error_with_message(error_message_1)

error_message_2 = 'Not a delivery guy'
response_error_with_message(error_message_2)


def active_check(self):
    role = user_role(self)
    if role == constants.DELIVERY_GUY:
        dg = get_object_or_404(DeliveryGuy, user=self)
        if dg.is_active is True:
            return True
        else:
            return response_error_with_message(error_message_1)
    else:
        return response_error_with_message(error_message_2)


def send_cod_status_notification(dg, dg_tl, cod_amount, is_transaction_successful):
    try:
        if is_transaction_successful is True:
            data = {
                'message': 'Amount %d was transferred to %s successfully ' % (cod_amount, dg_tl.user.first_name),
                'type': 'cod_transfer_to_tl',
                'data': {
                    'is_transaction_successful': is_transaction_successful
                }
            }
            send_push(dg.device_token, data)
        else:
            data = {
                'message': 'Transfer of amount %d to %s was declined ' % (cod_amount, dg_tl.user.first_name),
                'type': 'cod_transfer_to_tl',
                'data': {
                    'is_transaction_successful': is_transaction_successful
                }
            }
            send_push(dg.device_token, data)
    except Exception as e:
        log_exception(e, 'Push notification not sent in send_cod_status_notification ')


def send_timeout_notification(dg, cod_amount, is_time_out, is_transaction_successful):
    try:
        data = {
            'message': 'Transfer to %s of amount %d timed out.' % (dg.user.first_name, cod_amount),
            'type': 'cod_transfer_to_tl',
            'data': {
                'is_time_out': is_time_out,
                'is_transaction_successful': is_transaction_successful
            }
        }
        send_push(dg.device_token, data)
    except Exception as e:
        log_exception(e, 'Push notification not sent in send_cod_status_notification ')


def create_cod_transaction(transaction, user, dg_id, dg_tl_id, cod_amount, transaction_uuid, delivery_ids):
    created_time_stamp = datetime.now()
    cod_transaction = CODTransaction.objects.create(transaction=transaction,
                                                    created_by_user=user,
                                                    created_time_stamp=created_time_stamp,
                                                    dg_id=dg_id, dg_tl_id=dg_tl_id,
                                                    cod_amount=cod_amount,
                                                    transaction_uuid=transaction_uuid,
                                                    deliveries=delivery_ids)
    cod_transaction.save()
    return cod_transaction


def add_cod_transaction_to_delivery(cod_transaction, delivery):
    delivery.cod_transactions.add(cod_transaction)
    delivery.save()


def dg_collections_dict(delivery_status):
    dg_collections = {
        'delivery_id': delivery_status.id,
        'cod_collected': delivery_status.cod_collected_amount,
        'delivery_date_time': delivery_status.completed_datetime,
        'customer': delivery_status.order.consumer.full_name,
        'vendor': delivery_status.order.vendor.store_name
    }

    return dg_collections


def dg_total_cod_amount_dict(delivery_status):
    dg_total_cod_amount = {
        'total_cod_amount': None,
        'dg_collections': []
    }
    return dg_total_cod_amount


def associated_dgs_collections_dict(dg):
    associated_dgs_collections = {
        'dg_id': dg.id,
        'dg_name': dg.user.first_name,
        'cod_transferred': None,
        'transferred_time': None,
        'delivery_ids': []
    }
    return associated_dgs_collections


def dg_tl_collections_dict():
    dg_tl_collections = {
        'total_cod_amount': None,
        'associated_dg_collections': [],
        'tls_collections': []
    }

    return dg_tl_collections


def associated_dgs_pending_cod_details(delivery_guy):
    associated_dgs_pending_cod_details_dict = {
        'dg_id': delivery_guy.id,
        'dg_name': delivery_guy.user.first_name,
        'cod_amount': None
    }
    return associated_dgs_pending_cod_details_dict


def cod_balance_calculation(dg):
    deliveries = []
    delivery_statuses = OrderDeliveryStatus.objects.filter(delivery_guy=dg,
                                                           cod_status=constants.COD_STATUS_COLLECTED)
    delivery_statuses_total = delivery_statuses.values('delivery_guy__user__username').\
        annotate(sum_of_cod_collected=Sum('cod_collected_amount'))
    balance_amount = None
    if len(delivery_statuses_total) > 0:
        balance_amount = delivery_statuses_total[0]['sum_of_cod_collected']
        if dg.is_teamlead is True:
            dg_tl_id = dg.id
            delivery_guy_tl = DeliveryTeamLead.objects.get(delivery_guy=dg)
            associated_dgs = delivery_guy_tl.associate_delivery_guys.all()
            associated_dgs = associated_dgs.filter(is_active=True)
            for single_dg in associated_dgs:
                delivery_statuses = OrderDeliveryStatus.objects.filter(delivery_guy=single_dg,
                                                                       cod_status=constants.COD_STATUS_TRANSFERRED_TO_TL,
                                                                       cod_transactions__transaction_status=constants.VERIFIED,
                                                                       cod_transactions__dg_tl_id=dg_tl_id)
                for single in delivery_statuses:
                    deliveries.append(single.id)
                delivery_statuses = delivery_statuses.values('delivery_guy__user__username').annotate(sum_of_cod_collected=Sum('cod_collected_amount'))
                if len(delivery_statuses) > 0:
                    balance_amount = balance_amount + delivery_statuses[0]['sum_of_cod_collected']
    return balance_amount


def create_proof(bank_deposit_proof, user, cod_amount, bank_receipt_number):
    receipt = bank_deposit_proof
    total_cod = cod_amount
    try:
        proof = ProofOfBankDeposit.objects.create(created_by_user=user, total_cod=total_cod)
        proof.receipt = (Picture.objects.create(name=receipt))
        proof.receipt_number = bank_receipt_number

        proof.save()
    except Exception as e:
        error_message = 'Failed to create the bank deposit proof'
        return response_error_with_message(error_message)
    return proof


def all_bank_deposit_cod_transactions_list(cod_transaction):
    all_bank_deposit_cod_transactions_dict = {
        'created_by_user': cod_transaction.created_by_user.first_name,
        'created_time_stamp': cod_transaction.created_time_stamp.date(),
        'cod_amount': cod_transaction.cod_amount,
        'transaction_status': cod_transaction.transaction_status,
        'transaction_id': cod_transaction.transaction_uuid
    }
    return all_bank_deposit_cod_transactions_dict


def pagination_count():
    pagination_count_dict = {
        'total_pages': None,
        'total_bank_deposit_count': None
    }
    return pagination_count_dict


class CODViewSet(viewsets.ViewSet):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @list_route(methods=['GET'])
    @method_decorator(user_passes_test(active_check))
    def cod_balance(self, request):
        role = user_role(request.user)
        if role == constants.DELIVERY_GUY:
            dg = get_object_or_404(DeliveryGuy, user=request.user)
            # if dg.is_active is True:
            balance_amount = cod_balance_calculation(dg)
            if balance_amount is None:
                balance_amount = 0
            else:
                pass
            return response_with_payload(balance_amount, None)
            # else:
            #     error_message = 'This is a deactivated dg'
            #     return response_error_with_message(error_message)
        else:
            return response_access_denied()


    # for dg tl, order object if he is the assigned dg(order id, cod amount collected, customer name, vendor name, delivery date time)
    # dg object of his associated dg who has transferred the cod(dg id, dg name, transaction date time,
    # for dg, filter OrderDeliveryStatus for cod status(this is cumulative cod not yet transferred to tl)
    # for each order(order id, cod amount collected, customer name, vendor name, delivery date time)
    @list_route(methods=['GET'])
    @method_decorator(user_passes_test(active_check))
    def collections(self, request):
        role = user_role(request.user)
        if role == constants.DELIVERY_GUY:
            dg = get_object_or_404(DeliveryGuy, user=request.user)
            # if dg.is_active is True:
            if dg.is_teamlead is True:
                dg_tl_id = dg.id
                tl_collections = []
                asso_dg_collections = []
                dg_tl_collections = dg_tl_collections_dict()
                delivery_statuses = OrderDeliveryStatus.objects.filter(delivery_guy=dg,
                                                                       cod_status=constants.COD_STATUS_COLLECTED)
                for single in delivery_statuses:
                    dg_collections = dg_collections_dict(single)
                    tl_collections.append(dg_collections)
                dg_tl_collections['tls_collections'] = tl_collections

                balance_amount = cod_balance_calculation(dg)

                delivery_guy_tl = DeliveryTeamLead.objects.get(delivery_guy=dg)
                associated_dgs = delivery_guy_tl.associate_delivery_guys.all()
                associated_dgs = associated_dgs.filter(is_active=True)
                for single_dg in associated_dgs:
                    deliveries = []
                    delivery_statuses = OrderDeliveryStatus.objects.filter(delivery_guy=single_dg,
                                                                           cod_status=constants.COD_STATUS_TRANSFERRED_TO_TL,
                                                                           cod_transactions__transaction_status=constants.VERIFIED,
                                                                           cod_transactions__dg_tl_id=dg_tl_id)
                    for single in delivery_statuses:
                        deliveries.append(single.id)
                    delivery_statuses = delivery_statuses.values('delivery_guy__user__username').annotate(sum_of_cod_collected=Sum('cod_collected_amount'))
                    if len(delivery_statuses) > 0:
                        associated_dgs_collections = associated_dgs_collections_dict(single_dg)
                        associated_dgs_collections['delivery_ids'] = deliveries
                        associated_dgs_collections['cod_transferred'] = delivery_statuses[0]['sum_of_cod_collected']
                        cod_action = cod_actions(constants.COD_TRANSFERRED_TO_TL_CODE)
                        cod_transaction = CODTransaction.objects.filter(transaction__title=cod_action,
                                                                        transaction_status=constants.VERIFIED,
                                                                        cod_amount=delivery_statuses[0]['sum_of_cod_collected'],
                                                                        deliveries__in=deliveries)
                        if len(cod_transaction) > 0 and cod_transaction[0].verified_time_stamp is not None:
                            associated_dgs_collections['transferred_time'] = cod_transaction[0].verified_time_stamp
                        else:
                            associated_dgs_collections['transferred_time'] = None

                        asso_dg_collections.append(associated_dgs_collections)

                dg_tl_collections['total_cod_amount'] = balance_amount
                dg_tl_collections['associated_dg_collections'] = asso_dg_collections
                return response_with_payload(dg_tl_collections, None)
            else:
                dg_entire_collections = []
                delivery_statuses = OrderDeliveryStatus.objects.filter(delivery_guy=dg,
                                                                       cod_status=constants.COD_STATUS_COLLECTED)
                delivery_statuses_total = delivery_statuses.values('delivery_guy__user__username').\
                    annotate(sum_of_cod_collected=Sum('cod_collected_amount'))
                if len(delivery_statuses) > 0 and len(delivery_statuses_total) > 0:
                    dg_total_cod_amount = dg_total_cod_amount_dict(delivery_statuses_total[0])
                    dg_total_cod_amount['total_cod_amount'] = delivery_statuses_total[0]['sum_of_cod_collected']

                    for single in delivery_statuses:
                        dg_collections = dg_collections_dict(single)
                        dg_entire_collections.append(dg_collections)
                    dg_total_cod_amount['dg_collections'] = dg_entire_collections
                    return response_with_payload(dg_total_cod_amount, None)
                else:
                    error_message = 'No COD collection pending to transfer to TL'
                    return response_error_with_message(error_message)
            # else:
            #     error_message = 'This is a deactivated dg'
            #     return response_error_with_message(error_message)
        else:
            return response_access_denied()

    @list_route(methods=['POST'])
    @method_decorator(user_passes_test(active_check))
    def qr_code(self, request):
        role = user_role(request.user)
        balance_amount = 0
        if role == constants.DELIVERY_GUY:
            dg = get_object_or_404(DeliveryGuy, user=request.user)
            dg_id = dg.id
            if dg.is_teamlead is False:
                try:
                    dg_tl_id = request.data['dg_tl_id']
                    cod_amount = request.data['cod_amount']
                    delivery_ids = request.data['delivery_ids']
                except Exception as e:
                    params = ['dg_tl_id', 'cod_amount', 'delivery_ids']
                    return response_incomplete_parameters(params)
                try:
                    for delivery_id in delivery_ids:
                        delivery_status = get_object_or_404(OrderDeliveryStatus, pk=delivery_id)
                        balance_amount = balance_amount + delivery_status.cod_collected_amount
                    if balance_amount == cod_amount:
                        transaction_uuid = uuid.uuid4()
                        cod_action = cod_actions(constants.COD_TRANSFERRED_TO_TL_CODE)
                        cod_transaction = create_cod_transaction(cod_action, request.user, dg_id, dg_tl_id, cod_amount, transaction_uuid, delivery_ids)
                        for delivery_id in delivery_ids:
                            delivery_status = get_object_or_404(OrderDeliveryStatus, pk=delivery_id)
                            add_cod_transaction_to_delivery(cod_transaction, delivery_status)
                        return response_with_payload(transaction_uuid, None)
                    else:
                        error_message = 'cod amount does not match with the total cod collection from all the deliveries selected'
                        return response_error_with_message(error_message)
                except Exception as e:
                    error_message = 'Order not found'
                    return response_error_with_message(error_message)
            else:
                error_message = 'This is a deactivated dg OR a DG TL'
                return response_error_with_message(error_message)
        else:
            return response_access_denied()

    @list_route(methods=['GET'])
    @method_decorator(user_passes_test(active_check))
    def associated_dgs_collections(self, request):
        all_associated_dgs = []
        role = user_role(request.user)
        if role == constants.DELIVERY_GUY:
            delivery_guy = get_object_or_404(DeliveryGuy, user=request.user)
            # and delivery_guy.is_active is True
            if delivery_guy.is_teamlead is True:
                try:
                    delivery_guy_tl = DeliveryTeamLead.objects.get(delivery_guy=delivery_guy)
                    associated_dgs = delivery_guy_tl.associate_delivery_guys.all()
                    associated_dgs = associated_dgs.filter(is_active=True)
                    for single in associated_dgs:
                        delivery_statuses = OrderDeliveryStatus.objects.filter(delivery_guy=single,
                                                                               cod_status=constants.COD_STATUS_COLLECTED)
                        delivery_statuses_total = delivery_statuses.values('delivery_guy__user__username').\
                            annotate(sum_of_cod_collected=Sum('cod_collected_amount'))
                        associated_guys_detail_dict = associated_dgs_pending_cod_details(single)
                        if len(delivery_statuses) > 0:
                            associated_guys_detail_dict['cod_amount'] = delivery_statuses_total[0]['sum_of_cod_collected']
                        else:
                            associated_guys_detail_dict['cod_amount'] = 0
                        all_associated_dgs.append(associated_guys_detail_dict)
                    return response_with_payload(all_associated_dgs, None)
                except Exception as e:
                    error_message = 'No such Delivery Team Lead exists'
                    return response_error_with_message(error_message)
            else:
                error_message = 'This is not a DG team lead or this is a deactivated DG team lead'
                return response_error_with_message(error_message)
        else:
            return response_access_denied()

    @list_route(methods=['PUT'])
    @method_decorator(user_passes_test(active_check))
    def verify_transfer_to_tl(self, request):
        deliveries_list = []
        role = user_role(request.user)
        if role == constants.DELIVERY_GUY:
            delivery_guy = get_object_or_404(DeliveryGuy, user=request.user)
            # and delivery_guy.is_active is True
            if delivery_guy.is_teamlead is True:
                try:
                    transaction_uuid = request.data['transaction_id']
                    is_accepted = request.data['is_accepted']
                except Exception as e:
                    params = ['transaction_id', 'is_accepted']
                    return response_incomplete_parameters(params)
                try:
                    cod_transaction = CODTransaction.objects.get(transaction_uuid=transaction_uuid)
                except Exception as e:
                    error_message = 'No such transaction id found'
                    return response_error_with_message(error_message)

                dg_tl_id = cod_transaction.dg_tl_id
                if delivery_guy.id == dg_tl_id:
                    current_time = datetime.now(pytz.utc)
                    if cod_transaction.created_time_stamp is not None and cod_transaction.created_time_stamp < current_time:
                        time_diff = (current_time - cod_transaction.created_time_stamp)
                        total_seconds_worked = int(time_diff.total_seconds())
                        minutes = total_seconds_worked/60
                        dg = DeliveryGuy.objects.get(id=cod_transaction.dg_id)
                        if minutes < 5:
                            if is_accepted is True:
                                cod_transaction.verified_by_user = request.user
                                cod_transaction.verified_time_stamp = current_time
                                cod_transaction.transaction_status = constants.VERIFIED
                                cod_transaction.save()

                                deliveries = cod_transaction.deliveries
                                deliveries = eval(deliveries)
                                for single in deliveries:
                                    delivery = OrderDeliveryStatus.objects.get(id=single)
                                    delivery.cod_status = constants.COD_STATUS_TRANSFERRED_TO_TL
                                    delivery.save()
                                    cod_collected_transaction = delivery.cod_transactions.filter(transaction__title='CODCollected')
                                    if len(cod_collected_transaction) > 0:
                                        cod_transaction.transaction_status = constants.VERIFIED
                                        cod_transaction.save()
                                send_cod_status_notification(dg, delivery_guy, cod_transaction.cod_amount, is_accepted)
                                success_message = 'Transfer to TL verified'
                                return response_success_with_message(success_message)
                            else:
                                cod_transaction.verified_by_user = request.user
                                cod_transaction.verified_time_stamp = current_time
                                cod_transaction.transaction_status = constants.DECLINED
                                cod_transaction.save()
                                send_cod_status_notification(dg, delivery_guy, cod_transaction.cod_amount, is_accepted)
                                success_message = 'Transfer to TL declined'
                                return response_success_with_message(success_message)
                        else:
                            is_time_out = True
                            is_accepted = False
                            send_timeout_notification(dg, cod_transaction.cod_amount, is_time_out, is_accepted)
                            send_timeout_notification(delivery_guy, cod_transaction.cod_amount, is_time_out, is_accepted)
                            error_message = 'Transfer to TL transaction timed out'
                            return response_error_with_message(error_message)
                    else:
                        error_message = 'Transaction does not have an initiated time'
                        return response_error_with_message(error_message)
                else:
                    error_message = 'Transaction does not belong to this dg tl'
                    return response_error_with_message(error_message)
            else:
                error_message = 'This is not a DG team lead or this is a deactivated DG team lead'
                return response_error_with_message(error_message)
        else:
            return response_access_denied()

    # For DG or DG TL, Client sends delivery ids
    #  use this to cross check cod_amount accuracy
    @list_route(methods=['POST'])
    @method_decorator(user_passes_test(active_check))
    def bank_deposit_proof(self, request):
        role = user_role(request.user)
        if role == constants.DELIVERY_GUY:
            delivery_guy = get_object_or_404(DeliveryGuy, user=request.user)
            if delivery_guy.is_teamlead is True:
                dg_tl_id = delivery_guy.id
                dg_id = None
            else:
                dg_id = delivery_guy.id
                dg_tl_id = None
            cod_amount_calc = 0
            try:
                delivery_ids = request.data['delivery_ids']
                cod_amount = request.data['cod_amount']
                bank_deposit_proof = request.data['bank_deposit_proof']
                bank_receipt_number = request.data['bank_receipt_number']
            except Exception as e:
                params = ['delivery_ids', 'cod_amount', 'bank_deposit_proof', 'bank_receipt_number']
                return response_incomplete_parameters(params)

            try:
                for delivery_id in delivery_ids:
                    delivery = get_object_or_404(OrderDeliveryStatus, pk=delivery_id)
                    cod_amount_calc = cod_amount_calc + delivery.cod_collected_amount

                if cod_amount == cod_amount_calc:
                    transaction_uuid = uuid.uuid4()
                    cod_action = cod_actions(constants.COD_BANK_DEPOSITED_CODE)
                    proof = create_proof(bank_deposit_proof, request.user, cod_amount, bank_receipt_number)
                    cod_transaction = create_cod_transaction(cod_action, request.user, dg_id, dg_tl_id, cod_amount, transaction_uuid, delivery_ids)
                    cod_transaction.bank_deposit_proof = proof
                    cod_transaction.save()
                    for delivery_id in delivery_ids:
                        delivery_status = get_object_or_404(OrderDeliveryStatus, pk=delivery_id)
                        delivery_status.cod_status = constants.COD_STATUS_BANK_DEPOSITED
                        delivery_status.save()
                        add_cod_transaction_to_delivery(cod_transaction, delivery_status)
                    success_message = 'Bank Deposit transaction initiated successfully'
                    return response_success_with_message(success_message)
                else:
                    error_message = 'cod amount does not match with the total cod collection from all the deliveries selected'
                    return response_error_with_message(error_message)
            except Exception as e:
                error_message = 'Order not found'
                return response_error_with_message(error_message)
        else:
            return response_access_denied()


    # This api is to pull out all the bank deposit transactions(initiated/verified/declined)
    # dict of created by user, created date, receipt, current transaction status,
    # Implement pagination, give count of pages
    # give count of total bank deposit transactions
    @list_route(methods=['GET'])
    def bank_deposits_list(self, request):
        page = request.QUERY_PARAMS.get('page', '1')
        role = user_role(request.user)
        if role == constants.ACCOUNTS:
            bank_deposit_list = []
            accounts = get_object_or_404(Employee, user=request.user)
            cod_action = cod_actions(constants.COD_BANK_DEPOSITED_CODE)
            all_bank_deposit_cod_transactions = CODTransaction.objects.filter(transaction__title=cod_action)
            if len(all_bank_deposit_cod_transactions) > 0:
                # PAGINATION  ----------------------------------------------------------------
                total_bank_deposit_count = len(all_bank_deposit_cod_transactions)
                page = int(page)
                total_pages = int(total_bank_deposit_count / constants.PAGINATION_PAGE_SIZE) + 1
                if page > total_pages or page <= 0:
                    return response_invalid_pagenumber()
                else:
                    all_bank_deposit_cod_transactions = paginate(all_bank_deposit_cod_transactions, page)
                # ----------------------------------------------------------------------------
                for single in all_bank_deposit_cod_transactions:
                    all_bank_deposit_cod_transactions_dict = all_bank_deposit_cod_transactions_list(single)
                    all_bank_deposit_cod_transactions_dict['receipt_number'] = single.bank_deposit_proof.receipt_number
                    if single.bank_deposit_proof is not None:
                        pic = ProofOfBankDeposit.objects.get(id=single.bank_deposit_proof.id)
                        if pic.receipt is not None:
                            all_bank_deposit_cod_transactions_dict['receipt'] = pic.receipt.name
                        else:
                            all_bank_deposit_cod_transactions_dict['receipt'] = None
                    bank_deposit_list.append(all_bank_deposit_cod_transactions_dict)
                pagination_count_dict = pagination_count()
                pagination_count_dict['total_pages'] = total_pages
                pagination_count_dict['total_bank_deposit_count'] = total_bank_deposit_count
                bank_deposit_list.append(pagination_count_dict)
                return response_with_payload(bank_deposit_list, None)
            else:
                error_message = 'No Bank Deposit COD transaction found.'
                return response_error_with_message(error_message)
        else:
            return response_access_denied()
