from django.contrib import admin

# Register your models here.
from yourguy.models import Address, Area
from yourguy.models import OrderItem, Order, OrderDeliveryStatus
from yourguy.models import Product, ProductCategory
from yourguy.models import DeliveryGuy, DeliveryTeamLead, DGAttendance, Employee
from yourguy.models import Vendor, VendorAgent, Industry, VendorAccount, Consumer
from yourguy.models import ProofOfDelivery, Picture
from yourguy.models import TimeSlot
from yourguy.models import Location, ServiceableCity, ServiceablePincode
from yourguy.models import NotificationType, Notification
from yourguy.models import DeliveryAction, DeliveryTransaction


admin.site.register(TimeSlot)

admin.site.register(Address)
admin.site.register(Area)

admin.site.register(DeliveryGuy)
admin.site.register(DGAttendance)

admin.site.register(Industry)
admin.site.register(Vendor)
admin.site.register(VendorAgent)
admin.site.register(VendorAccount)

admin.site.register(Consumer)

class OrderAdmin(admin.ModelAdmin):
    raw_id_fields = ('vendor','consumer','order_items','pickup_address','delivery_address','created_by_user')
admin.site.register(Order, OrderAdmin)

class DeliveryStatusAdmin(admin.ModelAdmin):
    raw_id_fields = ('order','pickup_guy','delivery_guy','pickup_proof','delivery_proof')
admin.site.register(OrderDeliveryStatus, DeliveryStatusAdmin)

admin.site.register(Product)
admin.site.register(ProductCategory)
admin.site.register(OrderItem)
admin.site.register(Employee)

admin.site.register(Picture)
admin.site.register(ProofOfDelivery)

admin.site.register(ServiceableCity)
admin.site.register(ServiceablePincode)

admin.site.register(DeliveryTeamLead)
admin.site.register(NotificationType)
admin.site.register(Notification)
admin.site.register(DeliveryAction)
admin.site.register(DeliveryTransaction)