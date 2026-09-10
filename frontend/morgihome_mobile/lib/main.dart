import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/application_detail_screen.dart';
import 'screens/property_form_screen.dart';
import 'screens/mortgage_application_screen.dart';
import 'models/property.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MorgiHome',
      theme: ThemeData(
        primaryColor: const Color(0xFF0077B6),
        colorScheme: const ColorScheme.light(
          primary: Color(0xFF0077B6),
          secondary: Color(0xFF0A2B4E),
          background: Colors.white,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0A2B4E),
          foregroundColor: Colors.white,
          elevation: 0,
        ),
        bottomNavigationBarTheme: const BottomNavigationBarThemeData(
          selectedItemColor: Color(0xFF0077B6),
          unselectedItemColor: Colors.grey,
        ),
        inputDecorationTheme: InputDecorationTheme(
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          focusedBorder: OutlineInputBorder(
            borderSide: const BorderSide(color: Color(0xFF0077B6)),
            borderRadius: BorderRadius.circular(12),
          ),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF0077B6),
            foregroundColor: Colors.white,
            minimumSize: const Size(double.infinity, 50),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),
      ),
      home: const LoginScreen(),
      routes: {
        '/login': (context) => const LoginScreen(),
        '/home': (context) => const HomeScreen(),
      },
      onGenerateRoute: (settings) {
        if (settings.name == '/application_detail' && settings.arguments is int) {
          return MaterialPageRoute(builder: (_) => ApplicationDetailScreen(applicationId: settings.arguments as int));
        }
        if (settings.name == '/property_add') {
          return MaterialPageRoute(builder: (_) => const PropertyFormScreen());
        }
        if (settings.name == '/apply' && settings.arguments is Property) {
          return MaterialPageRoute(builder: (_) => MortgageApplicationScreen(property: settings.arguments as Property));
        }
        return null;
      },
    );
  }
}
