from django.urls import path

from .views import ChangePasswordView, CustomerNotificationsApiView, LoginView, LogoutView, ProfileView, RealEstateNotificationsApiView, RegisterView, SellerNotificationsApiView

urlpatterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('notifications/', CustomerNotificationsApiView.as_view(), name='customer_notifications_api'),
    path('notifications/realestate/', RealEstateNotificationsApiView.as_view(), name='realestate_notifications_api'),
    path('notifications/seller/', SellerNotificationsApiView.as_view(), name='seller_notifications_api'),
]
