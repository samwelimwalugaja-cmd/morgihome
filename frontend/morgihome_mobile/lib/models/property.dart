class Property {
  final int id;
  final String title;
  final String description;
  final double price;
  final String location;
  final int bedrooms;
  final int bathrooms;
  final double area;
  final String propertyType;
  final String status;
  final String? image;
  final String? sellerName;
  final DateTime createdAt;

  Property({
    required this.id,
    required this.title,
    required this.description,
    required this.price,
    required this.location,
    required this.bedrooms,
    required this.bathrooms,
    required this.area,
    required this.propertyType,
    required this.status,
    this.image,
    this.sellerName,
    required this.createdAt,
  });

  factory Property.fromJson(Map<String, dynamic> json) {
    return Property(
      id: json['id'],
      title: json['title'],
      description: json['description'] ?? '',
      price: (json['price'] ?? 0).toDouble(),
      location: json['location'] ?? '',
      bedrooms: json['bedrooms'] ?? 0,
      bathrooms: json['bathrooms'] ?? 0,
      area: (json['area'] ?? 0).toDouble(),
      propertyType: json['property_type'] ?? 'house',
      status: json['status'] ?? 'available',
      image: json['image'],
      sellerName: json['seller_name'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}
