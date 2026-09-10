from rest_framework import permissions


class IsSeller(permissions.BasePermission):
    message = "Only sellers are allowed to perform this action."
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'seller')

class IsRealEstate(permissions.BasePermission):
    message = "Only real estate companies are allowed to perform this action."
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'realestate')

class IsCustomer(permissions.BasePermission):
    message = "Only customers are allowed to perform this action."
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'customer')

class IsBank(permissions.BasePermission):
    message = "Only banks are allowed to perform this action."
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'bank')

# === REMOVED per spec - Email/Phone/NIN verification ===
# IsEmailVerified, IsFullyVerified, IsIdentityVerified have been removed.
# For now they return True for authenticated users (customers/sellers don't need verification)
# Or check is_fully_verified() for Bank/RealEstate

class IsEmailVerified(permissions.BasePermission):
    message = "Email verification removed - no longer required."
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

class IsFullyVerified(permissions.BasePermission):
    message = "Full verification - customer/seller always True, bank/realestate check business docs."
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Customers/Sellers don't need any verification
        if request.user.role in ['customer','seller']:
            return True
        return request.user.is_fully_verified()

class IsIdentityVerified(permissions.BasePermission):
    message = "Identity verification removed - no longer required."
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
