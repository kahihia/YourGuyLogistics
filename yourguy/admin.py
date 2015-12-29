from django.contrib import admin

# Register your models here.
from models import Address, Area, OrderItem, Order, OrderDeliveryStatus, DeliveryGuy, DGAttendance, Employee, Industry, Vendor, VendorAgent, VendorAccount, Consumer, Group, UserGroup, Suggestion, Message, Account, Product, ProductCategory
from models import ProofOfDelivery, Picture
from models import TimeSlot

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

admin.site.register(Order)

class DeliveryStatusAdmin(admin.ModelAdmin):
    raw_id_fields = ('order','pickup_guy','delivery_guy','pickup_proof','delivery_proof')
admin.site.register(OrderDeliveryStatus, DeliveryStatusAdmin)

admin.site.register(Product)
admin.site.register(ProductCategory)
admin.site.register(OrderItem)
admin.site.register(Employee)

admin.site.register(Picture)
admin.site.register(ProofOfDelivery)

# admin.site.register(UserGroup)
# admin.site.register(Group)
# admin.site.register(Suggestion)
# admin.site.register(Message)
# admin.site.register(Account)