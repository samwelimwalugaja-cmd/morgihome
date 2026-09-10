import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/api_service.dart';
import 'screens/welcome_screen.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/home_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/search_screen.dart';
import 'screens/verify_property_screen.dart';
import 'screens/property_detail_screen.dart';
import 'screens/mortgage_application_screen.dart';
import 'screens/application_status_screen.dart';
import 'screens/application_detail_screen.dart';
import 'screens/contracts_screen.dart';
import 'screens/repayment_screen.dart';
import 'screens/banks_screen.dart';
import 'screens/notifications_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/seller/seller_home.dart';
import 'screens/seller/seller_properties_screen.dart';
import 'screens/seller/seller_property_form.dart';
import 'screens/seller/seller_buyers_screen.dart';
import 'screens/seller/seller_sales_screen.dart';
import 'utils/constants.dart';

void main() {
  runApp(const MorgiHomeApp());
}

class MorgiHomeApp extends StatelessWidget {
  const MorgiHomeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<ApiService>(create: (_) => ApiService()),
      ],
      child: MaterialApp(
        title: AppConstants.appName,
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          primaryColor: const Color(AppConstants.primaryColorValue),
          scaffoldBackgroundColor: Colors.white,
          colorScheme: const ColorScheme.light(
            primary: Color(AppConstants.primaryColorValue),
            secondary: Color(AppConstants.secondaryColorValue),
            error: Color(AppConstants.errorColorValue),
            surface: Colors.white,
          ),
          appBarTheme: const AppBarTheme(
            backgroundColor: Color(AppConstants.secondaryColorValue),
            foregroundColor: Colors.white,
            elevation: 0,
            centerTitle: true,
            titleTextStyle: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 18),
            iconTheme: IconThemeData(color: Colors.white),
          ),
          bottomNavigationBarTheme: const BottomNavigationBarThemeData(
            selectedItemColor: Color(AppConstants.primaryColorValue),
            unselectedItemColor: Colors.grey,
            backgroundColor: Colors.white,
            type: BottomNavigationBarType.fixed,
            selectedLabelStyle: TextStyle(fontWeight: FontWeight.w600, fontSize: 12),
          ),
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(AppConstants.primaryColorValue),
              foregroundColor: Colors.white,
              // Solid flat colors only - no Material3 tint/gradient
              surfaceTintColor: Colors.transparent,
              shadowColor: Colors.transparent,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              elevation: 0,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              textStyle: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
          inputDecorationTheme: InputDecorationTheme(
            filled: true,
            fillColor: Colors.white,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: Color(0xFFE5E7EB))),
            enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: Color(0xFFE5E7EB))),
            focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: Color(AppConstants.primaryColorValue), width: 2)),
            errorBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: Color(AppConstants.errorColorValue))),
            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
          ),
          cardTheme: CardThemeData(
            color: Colors.white,
            elevation: 1,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: const BorderSide(color: Color(0xFFE5E7EB))),
          ),
          useMaterial3: true,
        ),
        // NOTE: 'home' (AuthChecker) is the entry point — do not set initialRoute
        // together with home at the same time (it will cause blank/conflict).
        routes: {
          '/welcome': (context) => const WelcomeScreen(),
          '/login': (context) => const LoginScreen(),
          '/register': (context) => const RegisterScreen(),
          // Customer (mortgage applicant) — same items as web sidebar
          '/dashboard': (context) => const DashboardScreen(),
          '/home': (context) => const HomeScreen(),
          '/search': (context) => const SearchScreen(),
          '/verify-property': (context) => const VerifyPropertyScreen(),
          '/property-detail': (context) => const PropertyDetailScreen(),
          '/mortgage-apply': (context) => const MortgageApplicationScreen(),
          '/applications': (context) => const ApplicationStatusScreen(),
          '/application-detail': (context) => const ApplicationDetailScreen(),
          '/contracts': (context) => const ContractsScreen(),
          '/repayment': (context) => const RepaymentScreen(),
          '/banks': (context) => const BanksScreen(),
          '/notifications': (context) => const NotificationsScreen(),
          '/profile': (context) => const ProfileScreen(),
          // Seller portal
          '/seller': (context) => const SellerHomeScreen(),
          '/seller-properties': (context) => const SellerPropertiesScreen(),
          '/seller-property-form': (context) => const SellerPropertyFormScreen(),
          '/seller-buyers': (context) => const SellerBuyersScreen(),
          '/seller-sales': (context) => const SellerSalesScreen(),
        },
        // Splash logic: check token
        home: const AuthChecker(),
      ),
    );
  }
}

class AuthChecker extends StatefulWidget {
  const AuthChecker({super.key});
  @override
  State<AuthChecker> createState() => _AuthCheckerState();
}

class _AuthCheckerState extends State<AuthChecker> {
  @override
  void initState() {
    super.initState();
    _check();
  }

  Future<void> _check() async {
    final api = ApiService();
    final token = await api.getAccessToken();
    await Future.delayed(const Duration(milliseconds: 800));
    if (!mounted) return;
    if (token != null && token.isNotEmpty) {
      // Role-based home like web
      final user = await api.getStoredUser();
      Navigator.pushReplacementNamed(context, user?.role == 'seller' ? '/seller' : '/home');
    } else {
      Navigator.pushReplacementNamed(context, '/welcome');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(AppConstants.secondaryColorValue),
      body: Center(
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Container(width: 80, height: 80, decoration: BoxDecoration(color: const Color(AppConstants.primaryColorValue), borderRadius: BorderRadius.circular(16)), child: const Icon(Icons.home_work, color: Colors.white, size: 40)),
          const SizedBox(height: 16),
          const Text('MorgiHome', style: TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w800)),
          const Text('Your Home, Your Mortgage', style: TextStyle(color: Colors.white70)),
          const SizedBox(height: 32),
          const CircularProgressIndicator(color: Colors.white),
        ]),
      ),
    );
  }
}
