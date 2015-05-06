from django.contrib import admin

# Register your models here.
from models import Address, Order, DeliveryGuy, Employee, DGAttendance, Vendor, Consumer, PushDetail, Group, UserGroup, Suggestion, Message, Account, Product

admin.site.register(DeliveryGuy)
admin.site.register(Vendor)
admin.site.register(Employee)
admin.site.register(Consumer)
admin.site.register(PushDetail)

admin.site.register(Address)
admin.site.register(Order)

admin.site.register(DGAttendance)

admin.site.register(UserGroup)
admin.site.register(Group)

admin.site.register(Suggestion)
admin.site.register(Message)
admin.site.register(Account)
admin.site.register(Product)

