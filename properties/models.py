from django.conf import settings
from django.db import models


class Property(models.Model):
    # Category: House vs Plot (as requested - sidebar choice)
    CATEGORY_CHOICES = (
        ('house', 'House'),
        ('plot', 'Plot'),
    )
    PROPERTY_TYPES = (
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('townhouse', 'Townhouse'),
        ('villa', 'Villa'),
        ('bungalow', 'Bungalow'),
        ('duplex', 'Duplex'),
        ('land', 'Land'),
        ('commercial', 'Commercial'),
    )

    STATUS_CHOICES = (
        ('available', 'Available'),
        ('applied', 'Applied'),
        ('verifying', 'Bank Verifying'),
        ('sold', 'Sold'),
        ('rented', 'Rented'),
        ('pending', 'Pending'),
        ('reserved', 'Reserved'),
        ('under_construction', 'Under Construction'),
    )

    LAND_TYPE_CHOICES = (
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('agricultural', 'Agricultural'),
        ('mixed', 'Mixed Use'),
    )
    ZONING_CHOICES = (
        ('residential', 'Residential Zone'),
        ('commercial', 'Commercial Zone'),
        ('industrial', 'Industrial Zone'),
        ('agricultural', 'Agricultural Zone'),
    )

    # --- Common ---
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=15, decimal_places=2)
    location = models.CharField(max_length=255)
    property_category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='house', help_text="House or Plot")
    area = models.DecimalField(max_digits=10, decimal_places=2, help_text="Area in square meters")
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES, default='house')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role__in': ['seller', 'realestate']})
    image = models.ImageField(upload_to='properties/', blank=True, null=True, help_text="Cover image - visible to banks and customers")
    napa = models.CharField(max_length=100, blank=True, null=True, help_text="Plot/Title No. - plot reference number (if available)")

    # --- House specific ---
    bedrooms = models.IntegerField(default=0)
    bathrooms = models.IntegerField(default=0)
    floor_number = models.IntegerField(null=True, blank=True, help_text="Floor number (for apartment)")
    total_floors = models.IntegerField(null=True, blank=True, help_text="Total floors in building")
    parking = models.IntegerField(default=0, help_text="Number of parking spaces")
    furnished = models.CharField(max_length=20, blank=True, choices=(('yes','Yes'),('no','No'),('partially','Partially')))
    security = models.BooleanField(default=False)
    swimming_pool = models.BooleanField(default=False)
    garden = models.BooleanField(default=False)
    balcony = models.BooleanField(default=False)
    elevator = models.BooleanField(default=False)
    air_conditioning = models.BooleanField(default=False)
    backup_generator = models.BooleanField(default=False)
    year_built = models.IntegerField(null=True, blank=True)
    property_condition = models.CharField(max_length=30, blank=True, choices=(('new','New'),('good','Good'),('needs_renovation','Needs Renovation'),('under_construction','Under Construction')))
    property_size = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="House size sqm")
    land_size = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Land size sqm (for house)")

    # --- Plot specific ---
    land_type = models.CharField(max_length=20, blank=True, choices=LAND_TYPE_CHOICES)
    plot_dimensions = models.CharField(max_length=100, blank=True, help_text="e.g. 20m x 25m")
    land_use = models.CharField(max_length=20, blank=True, choices=LAND_TYPE_CHOICES)
    infrastructure_road = models.BooleanField(default=False)
    infrastructure_electricity = models.BooleanField(default=False)
    infrastructure_water = models.BooleanField(default=False)
    infrastructure_sewage = models.BooleanField(default=False)
    infrastructure_internet = models.BooleanField(default=False)
    infrastructure_fenced = models.BooleanField(default=False)
    title_deed_available = models.CharField(max_length=20, blank=True, choices=(('yes','Yes'),('no','No'),('in_process','In Process')))
    survey_plan_available = models.CharField(max_length=10, blank=True, choices=(('yes','Yes'),('no','No')))
    zoning = models.CharField(max_length=20, blank=True, choices=ZONING_CHOICES)

    # --- Documents ---
    title_deed_file = models.FileField(upload_to='properties/documents/title_deed/', blank=True, null=True)
    survey_plan_file = models.FileField(upload_to='properties/documents/survey_plan/', blank=True, null=True)
    tax_clearance_file = models.FileField(upload_to='properties/documents/tax_clearance/', blank=True, null=True)
    land_certificate_file = models.FileField(upload_to='properties/documents/land_certificate/', blank=True, null=True)
    building_permit_file = models.FileField(upload_to='properties/documents/building_permit/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.price} TZS"

    @property
    def cover_image_url(self):
        # First cover: check gallery is_cover=True, if none use main image
        cover = self.gallery.filter(is_cover=True).first()
        if cover and cover.image:
            return cover.image.url
        if self.image:
            return self.image.url
        first = self.gallery.first()
        return first.image.url if first and first.image else None

    def get_gallery_urls(self):
        return [g.image.url for g in self.gallery.all() if g.image]

    class Meta:
        ordering = ['-created_at']


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='properties/gallery/')
    is_cover = models.BooleanField(default=False, help_text="Cover image visible to banks and customers")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.property.title} - Image {self.id} {'(Cover)' if self.is_cover else ''}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Ensure only one cover - if this is cover, remove cover from others
        if self.is_cover:
            PropertyImage.objects.filter(property=self.property).exclude(id=self.id).update(is_cover=False)
