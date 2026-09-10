from rest_framework import serializers

from .models import Property, PropertyImage


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'is_cover', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class PropertySerializer(serializers.ModelSerializer):
    seller_name = serializers.SerializerMethodField()
    gallery = PropertyImageSerializer(many=True, read_only=True)
    cover_image_url = serializers.ReadOnlyField()
    # Seller can upload up to 5 photos and choose cover
    images = serializers.ListField(child=serializers.ImageField(), write_only=True, required=False, allow_empty=True)
    cover_index = serializers.IntegerField(write_only=True, required=False, min_value=0, max_value=4)

    class Meta:
        model = Property
        fields = ['id', 'title', 'description', 'price', 'location', 'bedrooms',
                  'bathrooms', 'area', 'property_type', 'status', 'seller',
                  'seller_name', 'image', 'napa', 'gallery', 'cover_image_url',
                  'images', 'cover_index', 'created_at', 'updated_at']
        read_only_fields = ['seller', 'created_at', 'updated_at']

    def get_seller_name(self, obj):
        return obj.seller.get_full_name() if obj.seller else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add seller contact for detail - will be used to contact seller
        if instance.seller:
            data['seller_email'] = instance.seller.email
            data['seller_phone'] = instance.seller.phone_number
            data['seller_is_verified'] = instance.seller.is_verified
            data['seller_verification_level'] = instance.seller.verification_level
            data['seller_avatar'] = instance.seller.avatar_url
            data['seller_initials'] = instance.seller.initials
        return data

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_images(self, value):
        if len(value) > 5:
            raise serializers.ValidationError("You can upload up to 5 photos only.")
        for f in value:
            if f.size > 5242880:
                raise serializers.ValidationError(f"Photo {f.name} is too large (max 5MB).")
            if f.content_type not in ['image/jpeg','image/jpg','image/png','image/webp'] and not f.name.lower().endswith(('.jpg','.jpeg','.png','.webp')):
                raise serializers.ValidationError(f"Photo type {f.name} is not allowed (JPG/PNG only).")
        return value

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        cover_index = validated_data.pop('cover_index', 0)
        # Main image as legacy cover - if no gallery, use first one as image
        if images and not validated_data.get('image'):
            # do not set main image here, gallery will handle cover
            pass
        prop = Property.objects.create(**validated_data)
        for idx, img in enumerate(images[:5]):
            is_cover = (idx == cover_index)
            PropertyImage.objects.create(property=prop, image=img, is_cover=is_cover, order=idx)
            # If it is cover and no main image yet, also set as main image for backward compat
            if is_cover and not prop.image:
                prop.image = img
                prop.save(update_fields=['image'])
        return prop

    def update(self, instance, validated_data):
        images = validated_data.pop('images', None)
        cover_index = validated_data.pop('cover_index', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if images is not None:
            # Delete old gallery if new one exists? Or append - for now delete and recreate if new
            if images:
                instance.gallery.all().delete()
                for idx, img in enumerate(images[:5]):
                    is_cover = (cover_index is not None and idx == cover_index) or (cover_index is None and idx==0)
                    PropertyImage.objects.create(property=instance, image=img, is_cover=is_cover, order=idx)
                    if is_cover and not instance.image:
                        instance.image = img
                        instance.save(update_fields=['image'])
            # If cover_index only without images, change cover
            elif cover_index is not None:
                gallery = list(instance.gallery.all().order_by('order'))
                for idx, g in enumerate(gallery):
                    g.is_cover = (idx == cover_index)
                    g.save(update_fields=['is_cover'])
                if gallery and 0 <= cover_index < len(gallery):
                    instance.image = gallery[cover_index].image
                    instance.save(update_fields=['image'])
        return instance
