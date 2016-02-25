from django.db.models import Sum
from api_v3.utils import cod_actions, response_access_denied, get_object_or_404, response_error_with_message, response_with_payload, response_incomplete_parameters
from api_v3 import constants
from yourguy.models import CODTransaction, DeliveryGuy, OrderDeliveryStatus, DeliveryTeamLead
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from api_v3.utils import user_role
import uuid


def add_cod_action_for_delivery(action, delivery, user, dg_id, dg_tl_id, cod_amount, transaction_id, delivery_ids):
    cod_transaction = CODTransaction.objects.create(action=action, by_user=user, dg_id=dg_id, dg_tl_id=dg_tl_id, cod_amount=cod_amount, transaction_id=transaction_id, deliveries=delivery_ids)
    cod_transaction.save()
    delivery.cod_transactions.add(cod_transaction)
    delivery.save()


def dg_collections_dict(delivery_status):
    dg_collections = {
        'delivery_id': delivery_status.id,
        'cod_collected': delivery_status.cod_collected_amount,
        'delivery_date_time': delivery_status.completed_datetime,
        'customer': delivery_status.order.consumer.user.first_name,
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
        'transferred_time': None
    }
    return associated_dgs_collections


def tl_total_cod_amount_dict(delivery_status):
    tl_total_cod_amount = {
        'total_cod_amount': None,
        'collections': []
    }
    return tl_total_cod_amount


def dg_tl_collections_dict():
    dg_tl_collections = {
        'associated_dg_collections': [],
        'tls_collections': []
    }

    return dg_tl_collections


# for dg tl, order object if he is the assigned dg(order id, cod amount collected, customer name, vendor name, delivery date time)
# dg object of his associated dg who has transferred the cod(dg id, dg name, transaction date time,
# for dg, filter OrderDeliveryStatus for cod status(this is cumulative cod not yet transferred to tl)
# for each order(order id, cod amount collected, customer name, vendor name, delivery date time)
@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def collections(request):
    role = user_role(request.user)
    if role == constants.DELIVERY_GUY:
        dg = get_object_or_404(DeliveryGuy, user=request.user)
        if dg.is_active is True:
            if dg.is_teamlead is True:
                dg_tl_entire_collections = []
                asso_dg_collections = []
                dg_tl_collections = dg_tl_collections_dict()
                delivery_statuses = OrderDeliveryStatus.objects.filter(delivery_guy=dg,
                                                                       cod_status=constants.COD_STATUS_COLLECTED)
                delivery_statuses_total = delivery_statuses.values('delivery_guy__user__username').\
                    annotate(sum_of_cod_collected=Sum('cod_collected_amount'))
                tl_total_cod_amount = tl_total_cod_amount_dict(delivery_statuses)
                balance_amount = None
                if len(delivery_statuses_total) >0:
                    tl_total_cod_amount = tl_total_cod_amount_dict(delivery_statuses_total[0])
                    balance_amount = delivery_statuses_total[0]['sum_of_cod_collected']
                    for single in delivery_statuses:
                        dg_collections = dg_collections_dict(single)
                        dg_tl_collections['tls_collections'] = dg_collections

                delivery_guy_tl = DeliveryTeamLead.objects.get(delivery_guy=dg)
                associated_dgs = delivery_guy_tl.associate_delivery_guys.all()
                associated_dgs = associated_dgs.filter(is_active=True)
                for single_dg in associated_dgs:
                    delivery_statuses = OrderDeliveryStatus.objects.filter(delivery_guy=single_dg, cod_status=constants.COD_STATUS_TRANSFERRED_TO_TL)
                    delivery_statuses = delivery_statuses.values('delivery_guy__user__username').annotate(sum_of_cod_collected=Sum('cod_collected_amount'))
                    if len(delivery_statuses) >0:
                        balance_amount = balance_amount + delivery_statuses[0]['sum_of_cod_collected']
                        tl_total_cod_amount['total_cod_amount'] = balance_amount
                        associated_dgs_collections = associated_dgs_collections_dict(single_dg)
                        associated_dgs_collections['cod_transferred'] = delivery_statuses[0]['sum_of_cod_collected']

                        # Need to figure out how to send this transferred time to client
                        # cod_action = cod_actions(constants.COD_TRANSFERRED_TO_TL_CODE)
                        # cod_transactions = CODTransaction.objects.filter(user=single_dg.user, action=cod_action, transaction_type=constants.TRANSFER_TO_TL)
                        # associated_dgs_collections['transferred_time'] =

                        asso_dg_collections.append(associated_dgs_collections)
                dg_tl_collections['associated_dg_collections'].append(asso_dg_collections)
                dg_tl_entire_collections.append(dg_tl_collections)
                tl_total_cod_amount['collections'] = dg_tl_entire_collections
                return response_with_payload(tl_total_cod_amount, None)
            else:
                dg_entire_collections = []
                delivery_statuses = OrderDeliveryStatus.objects.filter(delivery_guy=dg,
                                                                       cod_status=constants.COD_STATUS_COLLECTED)
                delivery_statuses_total = delivery_statuses.values('delivery_guy__user__username').\
                    annotate(sum_of_cod_collected=Sum('cod_collected_amount'))
                dg_total_cod_amount = dg_total_cod_amount_dict(delivery_statuses_total[0])
                dg_total_cod_amount['total_cod_amount'] = delivery_statuses_total[0]['sum_of_cod_collected']

                for single in delivery_statuses:
                    dg_collections = dg_collections_dict(single)
                    dg_entire_collections.append(dg_collections)
                dg_total_cod_amount['dg_collections'] = dg_entire_collections
                return response_with_payload(dg_total_cod_amount, None)
        else:
            error_message = 'This is a deactivated dg'
            return response_error_with_message(error_message)
    else:
        return response_access_denied()

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def qr_code(request):
    role = user_role(request.user)
    if role == constants.DELIVERY_GUY:
        dg = get_object_or_404(DeliveryGuy, user=request.user)
        if dg.is_active is True and dg.is_teamlead is False:
            try:
                dg_id = request.data['dg_id']
                dg_tl_id = request.data['dg_tl_id']
                cod_amount = request.data['cod_amount']
                delivery_ids = request.data['delivery_ids']
            except Exception as e:
                params = ['dg_id', 'dg_tl_id', 'cod_amount', 'order_ids']
                return response_incomplete_parameters(params)
            transaction_id = uuid.uuid4()
            for delivery_id in delivery_ids:
                delivery_status = get_object_or_404(OrderDeliveryStatus, pk=delivery_id)
                cod_action = cod_actions(constants.COD_COLLECTED_CODE)
                add_cod_action_for_delivery(cod_action, delivery_status, request.user, dg_id, dg_tl_id, cod_amount, transaction_id, delivery_ids)
            content = {'transaction_id': transaction_id}
            return response_with_payload(content, None)
        else:
            error_message = 'This is a deactivated dg OR a DG TL'
            return response_error_with_message(error_message)
    else:
        return response_access_denied()

