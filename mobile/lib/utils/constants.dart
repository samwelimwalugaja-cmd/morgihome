import 'package:flutter/foundation.dart';

class AppConstants {
  // Change this to your server IP when testing on physical device
  // Android emulator uses 10.0.2.2 to reach host localhost
  static String get baseUrl {
    if (kIsWeb) return 'http://127.0.0.1:8000/api';
    // For Android emulator, use 10.0.2.2
    // For iOS simulator, use 127.0.0.1
    // For physical device, use your PC IP e.g. http://192.168.1.10:8000/api
    return 'http://10.0.2.2:8000/api';
  }

  static const String loginEndpoint = '/auth/login/';
  static const String registerEndpoint = '/auth/signup/';
  static const String logoutEndpoint = '/auth/logout/';
  static const String changePasswordEndpoint = '/auth/change-password/';
  static const String propertiesEndpoint = '/properties/';
  static const String propertySearchEndpoint = '/properties/search/';
  static const String mortgagesEndpoint = '/mortgages/';
  static const String contractsEndpoint = '/contracts/';
  static const String transactionsEndpoint = '/transactions/';
  static const String banksEndpoint = '/banks/';
  static const String profileEndpoint = '/auth/profile/';
  static const String profileApiEndpoint = '/profile/';

  // MorgiHome Colors - Solid only, no gradients
  static const int primaryColorValue = 0xFF0077B6; // Ocean Blue
  static const int secondaryColorValue = 0xFF0A2B4E; // Dark Blue
  static const int backgroundColorValue = 0xFFFFFFFF; // White
  static const int errorColorValue = 0xFFDC3545;
  static const int successColorValue = 0xFF28A745;

  static const String appName = 'MorgiHome';
  static const String appSlogan = 'Your Home, Your Mortgage';

  // Property Types
  static const List<String> propertyTypes = ['House', 'Apartment', 'Land', 'Commercial'];
  static const List<String> propertyTypeValues = ['house', 'apartment', 'land', 'commercial'];
}
