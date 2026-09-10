import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import '../services/api_service.dart';
import '../widgets/custom_button.dart';
import '../utils/constants.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  bool _obscure = true;
  bool _loading = false;
  final _api = ApiService();

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  void _login() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      final data = await _api.login(email: _emailCtrl.text.trim(), password: _passCtrl.text);
      if (!mounted) return;
      Fluttertoast.showToast(msg: 'Login successful');
      // Role-based home like web (customer -> /home, seller -> /seller)
      final user = data['user'];
      final role = user is Map ? user['role']?.toString() : null;
      Navigator.pushReplacementNamed(context, role == 'seller' ? '/seller' : '/home');
    } catch (e) {
      Fluttertoast.showToast(
          msg: e.toString().replaceAll('Exception:', '').trim(),
          backgroundColor: const Color(AppConstants.errorColorValue),
          toastLength: Toast.LENGTH_LONG);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SingleChildScrollView(
        child: Column(
          children: [
            // ===== Header with wave (solid dark blue, no gradient) =====
            ClipPath(
              clipper: _TopWaveClipper(),
              child: Container(
                width: double.infinity,
                color: const Color(AppConstants.secondaryColorValue),
                padding: const EdgeInsets.fromLTRB(24, 56, 24, 56),
                child: Column(
                  children: [
                    Row(
                      children: [
                        IconButton(
                          icon: const Icon(Icons.arrow_back, color: Colors.white),
                          onPressed: () => Navigator.pushReplacementNamed(context, '/welcome'),
                        ),
                        const Text('Welcome Back',
                            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 18)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Image.asset(
                        'assets/images/morgihome_logo.png',
                        height: 44,
                        fit: BoxFit.contain,
                        errorBuilder: (_, __, ___) => const Icon(Icons.home_work, color: Color(AppConstants.primaryColorValue), size: 36),
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text('Login to continue',
                        style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w800)),
                    const Text('Your mortgage journey awaits',
                        style: TextStyle(color: Colors.white70, fontSize: 13)),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(24),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    TextFormField(
                      controller: _emailCtrl,
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(labelText: 'Email', prefixIcon: Icon(Icons.email), border: OutlineInputBorder()),
                      validator: (v) => v == null || !v.contains('@') ? 'Enter valid email' : null,
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _passCtrl,
                      obscureText: _obscure,
                      decoration: InputDecoration(
                        labelText: 'Password',
                        prefixIcon: const Icon(Icons.lock),
                        border: const OutlineInputBorder(),
                        suffixIcon: IconButton(icon: Icon(_obscure ? Icons.visibility : Icons.visibility_off), onPressed: () => setState(() => _obscure = !_obscure)),
                      ),
                      validator: (v) => v == null || v.isEmpty ? 'Enter password' : null,
                    ),
                    const SizedBox(height: 24),
                    CustomButton(text: 'Login', onPressed: _login, isLoading: _loading),
                    const SizedBox(height: 16),
                    Wrap(alignment: WrapAlignment.center, crossAxisAlignment: WrapCrossAlignment.center, spacing: 4, children: [
                      const Text("Don't have an account? "),
                      GestureDetector(onTap: () => Navigator.pushNamed(context, '/register'), child: const Text('Sign Up', style: TextStyle(color: Color(AppConstants.primaryColorValue), fontWeight: FontWeight.w700))),
                    ]),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TopWaveClipper extends CustomClipper<Path> {
  @override
  Path getClip(Size size) {
    final path = Path();
    path.lineTo(0, size.height - 40);
    path.quadraticBezierTo(size.width * 0.25, size.height - 10, size.width * 0.5, size.height - 35);
    path.quadraticBezierTo(size.width * 0.75, size.height - 60, size.width, size.height - 30);
    path.lineTo(size.width, 0);
    path.close();
    return path;
  }

  @override
  bool shouldReclip(covariant CustomClipper<Path> oldClipper) => false;
}
