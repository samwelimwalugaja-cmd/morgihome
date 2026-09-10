"""
MorgiHome - Bank URLs
All Bank Portal URLs using Shadcn Admin template
"""
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard - /bank/dashboard/
    path("dashboard/", views.bank_dashboard, name="bank_dashboard"),

    # Applications - /bank/applications/ (+ dropdown All/Pending/Approved/Rejected)
    path("applications/", views.bank_applications, name="bank_applications"),
    path("applications/all/", views.bank_applications_all, name="bank_applications_all"),
    path("applications/pending/", views.bank_applications_pending, name="bank_applications_pending"),
    path("applications/approved/", views.bank_applications_approved, name="bank_applications_approved"),
    path("applications/rejected/", views.bank_applications_rejected, name="bank_applications_rejected"),
    path("applications/<int:pk>/", views.bank_application_detail, name="bank_application_detail"),
    path("applications/<int:pk>/review/", views.bank_application_review, name="bank_application_review"),
    path("applications/<int:pk>/stage/", views.bank_application_stage, name="bank_application_stage"),
    path("applications/<int:pk>/correction/", views.bank_application_correction, name="bank_application_correction"),
    path("applications/<int:pk>/approve/", views.bank_application_approve, name="bank_application_approve"),
    path("applications/<int:pk>/reject/", views.bank_application_reject, name="bank_application_reject"),
    path("applications/<int:pk>/pdf/", views.bank_application_pdf, name="bank_application_pdf"),

    # Contracts - /bank/contracts/
    path("contracts/", views.bank_contracts, name="bank_contracts"),
    path("contracts/<int:pk>/", views.bank_contract_detail, name="bank_contract_detail"),

    # Repayments - /bank/repayments/
    path("repayments/", views.bank_repayments, name="bank_repayments"),
    path("repayments/<int:pk>/", views.bank_repayment_detail, name="bank_repayment_detail"),

    # Reports - /bank/reports/
    path("reports/", views.bank_reports, name="bank_reports"),

    # Profile - /bank/profile/
    path("profile/", views.bank_profile, name="bank_profile"),

    # Verification for Bank only - business docs (Email/Phone/NIN removed)
    path("verify/", views.bank_verify, name="bank_verify"),

    # Settings, Help, Search, Notifications
    path("notifications/", views.bank_notifications, name="bank_notifications"),
    path("notifications/read/", views.bank_notifications_read, name="bank_notifications_read"),
    path("settings/", views.bank_settings, name="bank_settings"),
    path("settings/deactivate/", views.bank_deactivate, name="bank_deactivate"),
    path("help/", views.bank_help, name="bank_help"),
    path("search/", views.bank_search, name="bank_search"),
    path("api/notifications/", views.bank_notifications_api, name="bank_notifications_api"),
]
