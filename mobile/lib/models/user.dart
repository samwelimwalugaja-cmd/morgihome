class User {
  final int id;
  final String email;
  final String firstName;
  final String lastName;
  final String role;
  final String phoneNumber;
  final bool isVerified;
  final String? profileImage;

  User({
    required this.id,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.role,
    required this.phoneNumber,
    required this.isVerified,
    this.profileImage,
  });

  String get fullName {
    final n = '$firstName $lastName'.trim();
    return n.isNotEmpty ? n : (email.contains('@') ? email.split('@')[0] : email);
  }

  String get initials {
    if (firstName.isNotEmpty) return firstName[0].toUpperCase();
    if (lastName.isNotEmpty) return lastName[0].toUpperCase();
    if (email.isNotEmpty) return email[0].toUpperCase();
    return '?';
  }

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] is int ? json['id'] : int.tryParse(json['id'].toString()) ?? 0,
      email: json['email'] ?? '',
      firstName: json['first_name'] ?? json['firstName'] ?? '',
      lastName: json['last_name'] ?? json['lastName'] ?? '',
      role: json['role'] ?? 'customer',
      phoneNumber: json['phone_number'] ?? json['phoneNumber'] ?? '',
      isVerified: json['is_verified'] ?? json['isVerified'] ?? false,
      profileImage: json['profile_image'] ?? json['avatar_url'],
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'first_name': firstName,
        'last_name': lastName,
        'role': role,
        'phone_number': phoneNumber,
      };
}
