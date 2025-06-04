from django.urls import path
from .views import create_trip, trip_list, create_expense, trip_detail, edit_expense, delete_trip, edit_trip, delete_expense

urlpatterns = [
    path('', trip_list, name='trip_list'),
    path('create/', create_trip, name='create_trip'),
    path('<int:trip_id>/', trip_detail, name='trip_detail'),
    path('<int:trip_id>/edit/', edit_trip, name='edit_trip'),
    path('<int:trip_id>/delete/', delete_trip, name='delete_trip'),
    path('<int:trip_id>/expense/create/', create_expense, name='create_expense'),
    path('<int:trip_id>/expense/<int:expense_id>/edit/', edit_expense, name='edit_expense'),
    path('<int:trip_id>/expense/<int:expense_id>/delete/', delete_expense, name='delete_expense'),
] 