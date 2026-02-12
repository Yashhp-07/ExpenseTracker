from django.contrib import admin
from .models import UserRegistration, Expense, Friend, FriendExpense, Groups, GroupExpense, GroupExpenseSplit
# Register your models here.
admin.site.register(UserRegistration)
admin.site.register(Expense)
admin.site.register(Friend)
admin.site.register(FriendExpense)
admin.site.register(Groups)
admin.site.register(GroupExpense)
admin.site.register(GroupExpenseSplit)