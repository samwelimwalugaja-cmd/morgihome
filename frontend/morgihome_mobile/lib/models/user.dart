class User {
  final int id;
  final String username;
  final String email;
  final String role;
  final String? phoneNumber;
  final bool isVerified;

  User({
    required this.id,
    required this.username,
    required this.email,
    required this.role,
    this.phoneNumber,
    required this.isVerified,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      username: json['username'],
      email: json['email'],
      role: json['role'],
      phoneNumber: json['phone_number'],
      isVerified: json['is_verified'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'role': role,
      'phone_number': phoneNumber,
      'is_verified': isVerified,
    };
  }
}
