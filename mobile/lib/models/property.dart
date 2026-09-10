class PropertyGalleryImage {
  final int id;
  final String? image;
  final bool isCover;
  final int order;

  PropertyGalleryImage({required this.id, this.image, this.isCover = false, this.order = 0});

  factory PropertyGalleryImage.fromJson(Map<String, dynamic> json) => PropertyGalleryImage(
        id: json['id'] is int ? json['id'] : int.tryParse(json['id']?.toString() ?? '0') ?? 0,
        image: json['image']?.toString(),
        isCover: json['is_cover'] == true,
        order: json['order'] is int ? json['order'] : int.tryParse(json['order']?.toString() ?? '0') ?? 0,
      );
}

class Property {
  final int id;
  final String title;
  final String description;
  final String price;
  final String location;
  final String propertyCategory; // house | plot
  final String propertyType;
  final String status;
  final String? image;
  final String? sellerName;
  final String? sellerEmail;
  final String? sellerPhone;
  final int bedrooms;
  final int bathrooms;
  final String area;
  final String? coverImageUrl;
  final List<PropertyGalleryImage> gallery;

  // House specific
  final int? floorNumber;
  final int? totalFloors;
  final int parking;
  final String furnished;
  final bool security;
  final bool swimmingPool;
  final bool garden;
  final bool balcony;
  final bool elevator;
  final bool airConditioning;
  final bool backupGenerator;
  final int? yearBuilt;
  final String propertyCondition;
  final String? propertySize;
  final String? landSize;
  final String? napa;
  // Plot specific
  final String landType;
  final String plotDimensions;
  final String landUse;
  final bool infraRoad;
  final bool infraElectricity;
  final bool infraWater;
  final bool infraSewage;
  final bool infraInternet;
  final bool infraFenced;
  final String titleDeedAvailable;
  final String surveyPlanAvailable;
  final String zoning;
  // Documents
  final String? titleDeedFile;
  final String? surveyPlanFile;
  final String? taxClearanceFile;
  final String? landCertificateFile;
  final String? buildingPermitFile;

  Property({
    required this.id,
    required this.title,
    required this.description,
    required this.price,
    required this.location,
    this.propertyCategory = 'house',
    required this.propertyType,
    required this.status,
    this.image,
    this.sellerName,
    this.sellerEmail,
    this.sellerPhone,
    this.bedrooms = 0,
    this.bathrooms = 0,
    this.area = '0',
    this.coverImageUrl,
    this.gallery = const [],
    this.floorNumber,
    this.totalFloors,
    this.parking = 0,
    this.furnished = '',
    this.security = false,
    this.swimmingPool = false,
    this.garden = false,
    this.balcony = false,
    this.elevator = false,
    this.airConditioning = false,
    this.backupGenerator = false,
    this.yearBuilt,
    this.propertyCondition = '',
    this.propertySize,
    this.landSize,
    this.napa,
    this.landType = '',
    this.plotDimensions = '',
    this.landUse = '',
    this.infraRoad = false,
    this.infraElectricity = false,
    this.infraWater = false,
    this.infraSewage = false,
    this.infraInternet = false,
    this.infraFenced = false,
    this.titleDeedAvailable = '',
    this.surveyPlanAvailable = '',
    this.zoning = '',
    this.titleDeedFile,
    this.surveyPlanFile,
    this.taxClearanceFile,
    this.landCertificateFile,
    this.buildingPermitFile,
  });

  bool get isPlot => propertyCategory == 'plot' || propertyType == 'land';
  bool get hasHouseFeatures =>
      bedrooms > 0 || bathrooms > 0 || parking > 0 || security || swimmingPool || garden || balcony || elevator || airConditioning || backupGenerator;
  bool get hasPlotFeatures =>
      landType.isNotEmpty || plotDimensions.isNotEmpty || infraRoad || infraElectricity || infraWater || infraSewage || infraInternet || infraFenced;

  static bool _b(dynamic v) => v == true || v == 1 || v == '1' || v == 'true';
  static int _i(dynamic v) => v is int ? v : int.tryParse(v?.toString() ?? '') ?? 0;
  static int? _io(dynamic v) => v == null || v == '' ? null : (v is int ? v : int.tryParse(v.toString()));

  String get formattedPrice {
    try {
      final p = double.tryParse(price.toString());
      if (p == null) return price;
      return 'TZS ${p.toStringAsFixed(0).replaceAllMapped(RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'), (m) => '${m[1]},')}';
    } catch (_) {
      return price;
    }
  }

  String get typeDisplay {
    const map = {
      'house': 'House', 'apartment': 'Apartment', 'townhouse': 'Townhouse', 'villa': 'Villa',
      'bungalow': 'Bungalow', 'duplex': 'Duplex', 'land': 'Plot', 'commercial': 'Commercial',
    };
    return map[propertyType] ?? propertyType;
  }

  factory Property.fromJson(Map<String, dynamic> json) {
    String? img = json['image'] ?? json['cover_image_url'] ?? json['coverImageUrl'];
    final gal = <PropertyGalleryImage>[];
    final rawGal = json['gallery'];
    if (rawGal is List) {
      for (final e in rawGal) {
        if (e is Map<String, dynamic>) gal.add(PropertyGalleryImage.fromJson(e));
      }
    }
    return Property(
      id: json['id'] is int ? json['id'] : int.tryParse(json['id'].toString()) ?? 0,
      title: json['title'] ?? 'Property',
      description: json['description'] ?? '',
      price: json['price']?.toString() ?? '0',
      location: json['location'] ?? '',
      propertyCategory: json['property_category']?.toString() ?? 'house',
      propertyType: json['property_type'] ?? json['propertyType'] ?? 'house',
      status: json['status'] ?? 'available',
      image: img?.toString(),
      sellerName: json['seller_name'] ?? json['sellerName']?.toString(),
      sellerEmail: json['seller_email']?.toString(),
      sellerPhone: json['seller_phone']?.toString(),
      bedrooms: _i(json['bedrooms']),
      bathrooms: _i(json['bathrooms']),
      area: json['area']?.toString() ?? json['property_size']?.toString() ?? '0',
      coverImageUrl: json['cover_image_url']?.toString() ?? json['image']?.toString(),
      gallery: gal,
      floorNumber: _io(json['floor_number']),
      totalFloors: _io(json['total_floors']),
      parking: _i(json['parking']),
      furnished: json['furnished']?.toString() ?? '',
      security: _b(json['security']),
      swimmingPool: _b(json['swimming_pool']),
      garden: _b(json['garden']),
      balcony: _b(json['balcony']),
      elevator: _b(json['elevator']),
      airConditioning: _b(json['air_conditioning']),
      backupGenerator: _b(json['backup_generator']),
      yearBuilt: _io(json['year_built']),
      propertyCondition: json['property_condition']?.toString() ?? '',
      propertySize: json['property_size']?.toString(),
      landSize: json['land_size']?.toString(),
      napa: json['napa']?.toString(),
      landType: json['land_type']?.toString() ?? '',
      plotDimensions: json['plot_dimensions']?.toString() ?? '',
      landUse: json['land_use']?.toString() ?? '',
      infraRoad: _b(json['infrastructure_road']),
      infraElectricity: _b(json['infrastructure_electricity']),
      infraWater: _b(json['infrastructure_water']),
      infraSewage: _b(json['infrastructure_sewage']),
      infraInternet: _b(json['infrastructure_internet']),
      infraFenced: _b(json['infrastructure_fenced']),
      titleDeedAvailable: json['title_deed_available']?.toString() ?? '',
      surveyPlanAvailable: json['survey_plan_available']?.toString() ?? '',
      zoning: json['zoning']?.toString() ?? '',
      titleDeedFile: json['title_deed_file']?.toString(),
      surveyPlanFile: json['survey_plan_file']?.toString(),
      taxClearanceFile: json['tax_clearance_file']?.toString(),
      landCertificateFile: json['land_certificate_file']?.toString(),
      buildingPermitFile: json['building_permit_file']?.toString(),
    );
  }
}
