from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('team/', views.user_list_view, name='user_list'),
    path('team/new/', views.user_create_view, name='user_create'),
    path('team/<int:pk>/edit/', views.user_edit_view, name='user_edit'),
]

