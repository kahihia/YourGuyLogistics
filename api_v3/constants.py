from server import settings

# PAGINATION CONSTANT
PAGINATION_PAGE_SIZE = 50

# ROLES CONSTANTS
VENDOR = 'vendor'
CONSUMER = 'consumer'
OPERATIONS = 'operations'
SALES = 'sales'
DELIVERY_GUY = 'deliveryguy'

# CONTACTS CONSTANTS
OPS_PHONE_NUMBER = '+919820252216'
FROM_MAIL_ID = 'hi@yourguy.in'
TEST_GROUP_EMAILS = ['tech@yourguy.in', 'vinit@yourguy.in', 'prajakta@yourguy.in', 'aquid@yourguy.in']
SALES_EMAIL = ['sameet@yourguy.in', 'winston@yourguy.in']
EMAIL_SIGNATURE = "- \n Team YourGuy \nhttp://www.yourguy.in"
EMAIL_ERRORS = ['tech@yourguy.in', 'vinit@yourguy.in ', 'aquid@yourguy.in', 'prajakta@yourguy.in']

if settings.ENVIRONMENT == 'PRODUCTION':
    EMAIL_UNASSIGNED_ORDERS = ['tech@yourguy.in', 'alay@yourguy.in', 'ops@yourguy.in']
    EMAIL_DAILY_REPORT = ['tech@yourguy.in', 'alay@yourguy.in', 'ops@yourguy.in', 'bd@yourguy.in']
    EMAIL_REPORTED_ORDERS = ['ops@yourguy.in', 'bd@yourguy.in', 'cs@yourguy.in']
    EMAIL_WEBSITE = ['tech@yourguy.in', 'alay@yourguy.in', 'bd@yourguy.in', 'cs@yourguy.in']
    EMAIL_ADDITIONAL_ORDERS = ['ops@yourguy.in', 'bd@yourguy.in', 'cs@yourguy.in']
    EMAIL_COD_DISCREPENCY = ['ops@yourguy.in', 'cs@yourguy.in']
    TO_EMAIL_IDS = ['tech@yourguy.in', 'alay@yourguy.in', 'sameet@yourguy.in', 'winston@yourguy.in']
    OPS_EMAIL_IDS = ['tech@yourguy.in', 'alay@yourguy.in', 'rakesh@yourguy.in', 'santosh@yourguy.in',
                     'sameet@yourguy.in']
    EMAIL_IDS_EVERYBODY = ['tech@yourguy.in', 'alay@yourguy.in', 'sameet@yourguy.in', 'winston@yourguy.in',
                           'rakesh@yourguy.in', 'santosh@yourguy.in', 'vinit@yourguy.in', 'aquid@yourguy.in',
                           'saurabh@yourguy.in', 'smit@yourguy.in', 'kenneth@yourguy.in', 'bhawna.yourguy@gmail.com',
                           'sonali.a@yourguy.in', 'bernard.d@yourguy.in', 'sandesh.b@yourguy.in']
    RETAIL_EMAIL_ID = ['retail@yourguy.in']
else:
    EMAIL_UNASSIGNED_ORDERS = TEST_GROUP_EMAILS
    EMAIL_DAILY_REPORT = TEST_GROUP_EMAILS
    EMAIL_REPORTED_ORDERS = TEST_GROUP_EMAILS
    EMAIL_WEBSITE = TEST_GROUP_EMAILS
    EMAIL_ADDITIONAL_ORDERS = TEST_GROUP_EMAILS
    EMAIL_COD_DISCREPENCY = TEST_GROUP_EMAILS
    TO_EMAIL_IDS = TEST_GROUP_EMAILS
    OPS_EMAIL_IDS = TEST_GROUP_EMAILS
    EMAIL_IDS_EVERYBODY = TEST_GROUP_EMAILS
    RETAIL_EMAIL_ID = TEST_GROUP_EMAILS

# GCM CONSTANTS
GCM_PUSH_API_KEY = 'AIzaSyCmXulcUBViokrkYZ9Z9bWJgEWgXyeNh1U'
GCM_SENDER_ID = '559449819463'

# FRESHDESK CONSTATNS
FRESHDESK_TEST_KEY = 'wxMmvYfVzHCaYaXi1yln'
FRESHDESK_PRODUCTION_KEY = 'iUVZ8uJ1AywpVsQKL'

# URL CONSTANTS
FRESHDESK_BASEURL = 'https://yourguy.freshdesk.com'
URL_EXPIRY_TIME = 300  # 300 seconds
SMS_URL = "http://api.smscountry.com/SMSCwebservice_bulk.aspx?User=yourguy&passwd=yourguydotin&mobilenumber=" \
          "{mobile_number}&message={message_text}&sid=YOURGY&mtype=N&DR=Y"

# MESSAGES CONSTANTS
ORDER_PLACED_MESSAGE_OPS = 'A New order with order id {} has been placed by {}, please assign a DG.'
ORDER_PLACED_MESSAGE_CLIENT = 'Your order with order id {} has been placed and will be processed soon - Team YourGuy'
ORDER_DELIVERED_MESSAGE_CLIENT = 'Your order has been {} to {} at {} - Team YourGuy'
ORDER_APPROVED_MESSAGE_CLIENT = 'Your order for {} has been approved & QUEUED for delivery - Team YourGuy'
ORDER_REJECTED_MESSAGE_CLIENT = 'Your order for {} has been rejected because of {} - Team YourGuy'
ORDER_RESCHEDULED_MESSAGE_CLIENT = 'Your order for {} with order no {} has been rescheduled to {} - Team YourGuy'
ORDER_CANCELLED_MESSAGE_CLIENT = 'Your order for {} with order no {} has been canceled - Team YourGuy'
VENDOR_ACCOUNT_REQUESTED_MESSAGE_SALES = "A New Vendor has requested for an account. \nPlease find the below details: " \
                                         "\nStore Name:{} \nPhone Number: {} \nEmail: {} \nAddress : {}, {} " \
                                         "\nApproval link:{}"
VENDOR_ACCOUNT_APPROVED_MESSAGE = 'Your account has been approved. \n http://app.yourguy.in' \
                                  ' \nPlease login using following credentials: \nUsername:{} ' \
                                  '\nPassword:{} - Team YourGuy'
VENDOR_ACCOUNT_APPROVED_MESSAGE_SALES = 'YourGuy: An account has been created for {} and credentials are sent via SMS ' \
                                        'and Email.'
ERROR_EMAIL_BODY = 'FOLLOWING IS THE EXCEPTION: '

# ORDER STATUS CONSTANTS
ORDER_STATUS_PLACED = 'ORDER_PLACED'
ORDER_STATUS_QUEUED = 'QUEUED'
ORDER_STATUS_INTRANSIT = 'INTRANSIT'
ORDER_STATUS_PICKUP_ATTEMPTED = 'PICKUPATTEMPTED'
ORDER_STATUS_DELIVERED = 'DELIVERED'
ORDER_STATUS_DELIVERY_ATTEMPTED = 'DELIVERYATTEMPTED'
ORDER_STATUS_CANCELLED = 'CANCELLED'
ORDER_STATUS_REJECTED = 'REJECTED'

# DG WORKING STATUS CONSTANTS
DG_STATUS_WORKING = 'WORKING'
DG_STATUS_LEAVE = 'LEAVE'
DG_STATUS_UNKNOWN = 'UNKNOWN'
DG_STATUS_AVAILABLE = 'AVAILABLE'
DG_STATUS_UN_AVAILABLE = 'UN_AVAILABLE'
DG_STATUS_BUSY = 'BUSY'

# DELIVERY LOCATION CONSTANTS
DELIVERED_AT_NONE = 'NONE'

# TOBE REMOVED
ORDER_STATUS_OUTFORPICKUP = 'OUTFORPICKUP'
ORDER_STATUS_OUTFORDELIVERY = 'OUTFORDELIVERY'
ORDER_STATUS_ATTEMPTED = 'ATTEMPTED'
ORDER_STATUS_NOT_DELIVERED = 'NOT_DELIVERED'