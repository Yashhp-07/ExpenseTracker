from django.urls import path
from . import views

urlpatterns = [
    path('',views.index, name='index'),
    path('register/', views.register, name='register'),
    path('otp/', views.otp_page, name='otp_page'),
    path('login/', views.login_page, name='login'),
    path('landing/', views.landing_page, name='landing_page'),
    path('logout/',views.logout_page, name='logout'),
    path('add_expense/', views.add_expense, name='add_expense'),
    path('edit_expense/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('delete_expense/<int:expense_id>/', views.delete_expense, name='delete_expense'),
    path('personal/', views.personal_dashboard, name='personal_dashboard'),
    path('friends/', views.friends_dashboard, name='friends_dashboard'),
    path('groups/', views.groups_dashboard, name='groups_dashboard'),
    path('activity/', views.activity_dashboard, name='activity_dashboard'),
    path('add_friend/',views.add_friend, name='add_friend'),
    path('friend_details/<int:friend_id>/',views.friend_details, name='friend_details'),
    path('remove_friend/<int:friend_id>/',views.remove_friend, name='remove_friend'),
    path('add_expense_with_friend/<int:friend_id>/',views.add_expense_with_friend, name='add_expense_with_friend'),
    path('expense_details/<int:friend_id>/', views.expense_details, name='expense_details'),
    path('save_split_expense/<int:friend_id>/', views.save_split_expense, name='save_split_expense'),
    path('delete_friend_expense/<int:expense_id>/', views.delete_friend_expense, name='delete_friend_expense'),

    #Phase 3
    path('groups/',views.groups_dashboard,name='groups'),
    path('create-group/',views.create_group,name='create_group'),
    #Group expense details
    path('group/<int:group_id>/', views.group_details, name='group_details'),
    path('group/<int:group_id>/remove/', views.remove_from_group, name='remove_from_group'),
    path('group/<int:group_id>/add_members/', views.add_members, name='add_members'),
    path('group/<int:group_id>/add_expense/', views.add_group_expense, name='add_group_expense'),
    path('group/<int:group_id>/save_expense/', views.save_group_split_expense, name='save_group_split_expense'),
    path('delete_group_expense/<int:expense_id>/', views.delete_group_expense, name='delete_group_expense'),

    #Settle Up Balances
    path('record_payment/<int:friend_id>/', views.record_payment, name='record_payment'),

    #Activity Log
    path('activity/', views.activity_dashboard, name='activity_dashboard'),
]