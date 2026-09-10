"""
URL configuration for morgihome_backend project.
"""
import os
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from mortgages.views import CustomerApplyView
from properties.views import SellerAddPropertyView, SellerBuyersView, SellerPropertyListView

from accounts.views import (
    BankDocumentUploadView,
    BankListView,
    BankVerificationPageView,
    rate_limit_exceeded,
)
from accounts.dashboard_views import (
    DashboardRedirectView,
    ProfileView, CustomerProfileView, SellerProfileView, RealEstateProfileView,
    CustomerDashboardView, CustomerPropertiesView, CustomerApplyViewApex, CustomerApplicationsView, CustomerTrackView, CustomerCorrectionRespondView, CustomerContractsView, CustomerVerifyPropertyView, CustomerBankRequirementsView, CustomerRepaymentView, CustomerNotificationsView, CustomerSearchView,
    SellerDashboardView, SellerPropertiesView, SellerAddPropertyViewApex, SellerEditPropertyView, SellerBuyersViewApex, SellerContractsViewApex, SellerSalesView, SellerPropertyDetailView, SellerNotificationsView,
    RealEstateDashboardView, RealEstatePropertiesView, RealEstateAddPropertyView, RealEstateEditPropertyView, RealEstateApplicationsView, RealEstateContractsView, RealEstateBuyersView, RealEstateBuyerDetailView, RealEstateBanksView, RealEstateReportsView, RealEstateNotificationsView, RealEstateSearchView,
    PropertyDetailCoronaView, PublicPropertyDetailView, CustomerPropertyDetailView,
)

urlpatterns = [
    path(os.getenv('ADMIN_URL', 'admin-secure/'), admin.site.urls),
    path('rate-limit/', rate_limit_exceeded, name='rate_limit_exceeded'),
    path('accounts/lockout/', TemplateView.as_view(template_name='accounts/lockout.html'), name='lockout'),
    # Verification Pages - ZIMEONDOLEWA Email/Phone/NIN -> zimebaki Bank tu
    # ONDOLEWA: verify/email/<token>/, verify/phone/, verify/identity/, verify/status/, verify/account/
    # ZINAZOSALIA: verify/bank/, verify/admin/
    path('verify/bank/', BankVerificationPageView.as_view(), name='bank_verification_page'),
    # Verification API - ONDOLEWA Email/Phone/NIN -> inabaki bank docs tu
    path('api/verify/bank/<str:doc_type>/', BankDocumentUploadView.as_view(), name='api_bank_doc_upload'),
    # Step 6: Banks - Customer chooses a Bank
    path('api/banks/', BankListView.as_view(), name='api_banks'),
    path('banks/', TemplateView.as_view(template_name='banks.html'), name='banks_page'),
    path('banks/<int:id>/', TemplateView.as_view(template_name='bank_detail.html'), name='bank_detail'),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('faq/', TemplateView.as_view(template_name='faq.html'), name='faq_page'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login_page'),
    path('signup/', TemplateView.as_view(template_name='signup.html'), name='signup_page'),
    path('signup/seller/', TemplateView.as_view(template_name='signup.html'), name='signup_seller_page'),
    path('dashboard/', DashboardRedirectView.as_view(), name='dashboard'),
    # ========== Corona Dashboard - Customer (REAL DATA, Corona theme kama ilivyo, data tu) ==========
    path('customer/dashboard/', CustomerDashboardView.as_view(), name='customer_dashboard_apex'),
    path('customer/properties/', CustomerPropertiesView.as_view(), name='customer_properties_apex'),
    path('customer/apply/', CustomerApplyViewApex.as_view(), name='customer_apply_apex'),
    path('customer/applications/', CustomerApplicationsView.as_view(), name='customer_applications_apex'),
    path('customer/track/<int:id>/', CustomerTrackView.as_view(), name='customer_track_apex'),
    path('customer/track/<int:application_id>/', CustomerTrackView.as_view(), name='customer_track_apex2'),
    path('customer/corrections/<int:id>/respond/', CustomerCorrectionRespondView.as_view(), name='customer_correction_respond'),
    path('customer/track/', CustomerTrackView.as_view(), name='customer_track_generic_apex'),
    path('customer/contracts/', CustomerContractsView.as_view(), name='customer_contracts_apex'),
    path('customer/verify-property/', CustomerVerifyPropertyView.as_view(), name='customer_verify_property'),
    path('customer/bank-requirements/', CustomerBankRequirementsView.as_view(), name='customer_bank_requirements'),
    path('customer/repayment/', CustomerRepaymentView.as_view(), name='customer_repayment_apex'),
    path('customer/notifications/', CustomerNotificationsView.as_view(), name='customer_notifications'),
    path('customer/search/', CustomerSearchView.as_view(), name='customer_search'),
    path('customer/properties/<int:id>/', CustomerPropertyDetailView.as_view(), name='customer_property_detail'),
    path('customer/pay/<int:id>/', CustomerRepaymentView.as_view(), name='customer_pay_apex'),
    path('customer/pay/', CustomerRepaymentView.as_view(), name='customer_pay_generic_apex'),
    # ========== Corona Dashboard - Seller ==========
    path('seller/dashboard/', SellerDashboardView.as_view(), name='seller_dashboard_apex'),
    path('seller/properties/add/', SellerAddPropertyViewApex.as_view(), name='seller_add_property_apex'),
    path('seller/properties/edit/<int:id>/', SellerEditPropertyView.as_view(), name='seller_edit_property_apex'),
    path('seller/properties/<int:id>/', SellerPropertyDetailView.as_view(), name='seller_property_detail'),
    path('seller/properties/all/', SellerPropertiesView.as_view(), name='seller_properties_all'),
    path('seller/properties/', SellerPropertiesView.as_view(), name='seller_properties_apex'),
    path('seller/buyers/', SellerBuyersViewApex.as_view(), name='seller_buyers_apex'),
    path('seller/contracts/', SellerContractsViewApex.as_view(), name='seller_contracts_apex'),
    path('seller/sales/', SellerSalesView.as_view(), name='seller_sales_apex'),
    path('seller/notifications/', SellerNotificationsView.as_view(), name='seller_notifications'),
    # Legacy seller routes (keep for backwards compat - point to old plainadmin)
    path('seller/properties/list/', SellerPropertyListView.as_view(), name='seller_properties_list'),
    # Legacy customer routes (keep)
    path('customer/applications/list/', TemplateView.as_view(template_name='my_applications.html'), name='my_applications_list'),
    path('customer/applications/<int:id>/', TemplateView.as_view(template_name='application_detail.html'), name='application_detail'),
    path('properties/<int:id>/', PublicPropertyDetailView.as_view(), name='property_detail'),
    path('properties/', TemplateView.as_view(template_name='properties.html'), name='properties_page'),
    # ========== Corona Dashboard - Real Estate (kama dist/index.html halisi) ==========
    path('realestate/dashboard/', RealEstateDashboardView.as_view(), name='realestate_dashboard_apex'),
    path('realestate/properties/add/', RealEstateAddPropertyView.as_view(), name='realestate_add_property_apex'),
    path('realestate/properties/edit/<int:id>/', RealEstateEditPropertyView.as_view(), name='realestate_edit_property_apex'),
    path('realestate/properties/all/', RealEstatePropertiesView.as_view(), name='realestate_properties_all'),
    path('realestate/properties/<int:id>/', PropertyDetailCoronaView.as_view(), name='realestate_property_detail'),
    path('realestate/properties/', RealEstatePropertiesView.as_view(), name='realestate_properties_apex'),
    path('realestate/applications/', RealEstateApplicationsView.as_view(), name='realestate_applications_apex'),
    path('realestate/contracts/', RealEstateContractsView.as_view(), name='realestate_contracts_apex'),
    path('realestate/buyers/', RealEstateBuyersView.as_view(), name='realestate_buyers'),
    path('realestate/buyers/<int:id>/', RealEstateBuyerDetailView.as_view(), name='realestate_buyer_detail'),
    path('realestate/buyers/all/', RealEstateBuyersView.as_view(), name='realestate_buyers_all'),
    path('realestate/buyers/interested/', RealEstateBuyersView.as_view(), name='realestate_buyers_interested'),
    path('realestate/banks/', RealEstateBanksView.as_view(), name='realestate_banks'),
    path('realestate/reports/', RealEstateReportsView.as_view(), name='realestate_reports'),
    path('realestate/notifications/', RealEstateNotificationsView.as_view(), name='realestate_notifications'),
    path('realestate/search/', RealEstateSearchView.as_view(), name='realestate_search'),
    # ========== Profile - KILA ROLE ANA YAKWE (wasishare) - Corona style ==========
    path('profile/', ProfileView.as_view(), name='profile_page'),
    path('customer/profile/', CustomerProfileView.as_view(), name='customer_profile'),
    path('seller/profile/', SellerProfileView.as_view(), name='seller_profile'),
    path('realestate/profile/', RealEstateProfileView.as_view(), name='realestate_profile'),
    # Bank Shadcn Admin - 7 pages (kutoka sampleweb) - production Tailwind + theme toggle
    path('bank/', include('bank.urls')),
    # Catch-all for legacy dashboard SPA - keep at bottom
    path('customer/<path:path>', TemplateView.as_view(template_name='dashboard.html'), name='customer_dashboard_legacy'),
    path('seller/<path:path>', TemplateView.as_view(template_name='dashboard.html'), name='seller_dashboard_legacy'),
    path('realestate/<path:path>', TemplateView.as_view(template_name='dashboard.html'), name='realestate_dashboard_legacy'),
    path('api/auth/', include('accounts.urls')),
    path('api/', include('properties.urls')),
    path('api/', include('mortgages.urls')),
    path('api/', include('transactions.urls')),
    path('api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
