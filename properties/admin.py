from django.contrib import admin
from .models import Property, PropertyImage

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'location', 'property_type', 'property_category', 'status', 'seller', 'bedrooms', 'bathrooms', 'area', 'created_at')
    list_filter = ('status', 'property_type', 'property_category', 'land_type')
    search_fields = ('title', 'location', 'description', 'seller__email')
    list_editable = ()
    fieldsets = (
        (None, {'fields': ('title', 'description', 'price', 'location', 'property_category', 'property_type', 'status', 'seller', 'image', 'napa', 'area')}),
        ('House Details', {'fields': ('bedrooms', 'bathrooms', 'floor_number', 'total_floors', 'parking', 'furnished', 'security', 'swimming_pool', 'garden', 'balcony', 'elevator', 'air_conditioning', 'backup_generator', 'year_built', 'property_condition', 'property_size', 'land_size'), 'classes': ('collapse',)}),
        ('Plot Details', {'fields': ('land_type', 'plot_dimensions', 'land_use', 'infrastructure_road', 'infrastructure_electricity', 'infrastructure_water', 'infrastructure_sewage', 'infrastructure_internet', 'infrastructure_fenced', 'title_deed_available', 'survey_plan_available', 'zoning'), 'classes': ('collapse',)}),
        ('Documents', {'fields': ('title_deed_file', 'survey_plan_file', 'tax_clearance_file', 'land_certificate_file', 'building_permit_file'), 'classes': ('collapse',)}),
    )
    inlines = [PropertyImageInline]
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'is_cover', 'order', 'created_at')
    list_filter = ('is_cover',)
    search_fields = ('property__title',)
