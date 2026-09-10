import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import '../services/api_service.dart';
import '../widgets/custom_button.dart';
import '../utils/constants.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});
  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _first = TextEditingController();
  final _last = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _pass = TextEditingController();
  final _confirm = TextEditingController();
  bool _agree = false;
  bool _loading = false;
  bool _obscure1 = true;
  bool _obscure2 = true;
  // customer = Mortgage Applicant, seller = Seller
  String _role = 'customer';
  final _api = ApiService();

  @override
  void dispose() {
    _first.dispose();
    _last.dispose();
    _email.dispose();
    _phone.dispose();
    _pass.dispose();
    _confirm.dispose();
    super.dispose();
  }

  void _register() async {
    // Checkbox ina validator yake ndani ya Form - error nyekundu inaonekana hapo hapo
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await _api.register(
        firstName: _first.text.trim(),
        lastName: _last.text.trim(),
        email: _email.text.trim(),
        phone: _phone.text.trim(),
        password: _pass.text,
        confirmPassword: _confirm.text,
        role: _role,
      );
      if (!mounted) return;
      Fluttertoast.showToast(msg: 'Registration successful! Please login');
      Navigator.pushReplacementNamed(context, '/login');
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
            // ===== Header with wave (dark blue) =====
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
                          onPressed: () => Navigator.pop(context),
                        ),
                        const Text('Create Account',
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
                    const Text('Join MorgiHome',
                        style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w800)),
                    const Text('Choose your role then fill the form',
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
                    const Text('Who are you?',
                        style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15, color: Color(AppConstants.secondaryColorValue))),
                    const SizedBox(height: 10),
                    // ===== Role selector: 2 cards =====
                    Row(
                      children: [
                        Expanded(child: _roleCard(
                          value: 'customer',
                          icon: Icons.home,
                          title: 'Mortgage Applicant',
                          subtitle: 'Applicant — I am looking for a house',
                        )),
                        const SizedBox(width: 12),
                        Expanded(child: _roleCard(
                          value: 'seller',
                          icon: Icons.store,
                          title: 'Seller',
                          subtitle: 'Seller — I have a house',
                        )),
                      ],
                    ),
                    const SizedBox(height: 20),
                    TextFormField(controller: _first, decoration: const InputDecoration(labelText: 'First Name', prefixIcon: Icon(Icons.person), border: OutlineInputBorder()), validator: (v) => v == null || v.trim().length < 2 ? 'Required (min 2)' : null),
                    const SizedBox(height: 12),
                    TextFormField(controller: _last, decoration: const InputDecoration(labelText: 'Last Name', prefixIcon: Icon(Icons.person_outline), border: OutlineInputBorder()), validator: (v) => v == null || v.trim().length < 2 ? 'Required (min 2)' : null),
                    const SizedBox(height: 12),
                    TextFormField(controller: _email, keyboardType: TextInputType.emailAddress, decoration: const InputDecoration(labelText: 'Email', prefixIcon: Icon(Icons.email), border: OutlineInputBorder()), validator: (v) => v == null || !v.contains('@') ? 'Invalid email' : null),
                    const SizedBox(height: 12),
                    TextFormField(controller: _phone, keyboardType: TextInputType.phone, decoration: const InputDecoration(labelText: 'Phone (+255 ...)', prefixIcon: Icon(Icons.phone), border: OutlineInputBorder()), validator: (v) => v == null || v.trim().isEmpty ? 'Required' : null),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _pass,
                      obscureText: _obscure1,
                      decoration: InputDecoration(
                        labelText: 'Password (min 8)',
                        prefixIcon: const Icon(Icons.lock),
                        border: const OutlineInputBorder(),
                        suffixIcon: IconButton(icon: Icon(_obscure1 ? Icons.visibility : Icons.visibility_off), onPressed: () => setState(() => _obscure1 = !_obscure1)),
                      ),
                      validator: (v) => v == null || v.length < 8 ? 'Min 8 chars' : null,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _confirm,
                      obscureText: _obscure2,
                      decoration: InputDecoration(
                        labelText: 'Confirm Password',
                        prefixIcon: const Icon(Icons.lock_outline),
                        border: const OutlineInputBorder(),
                        suffixIcon: IconButton(icon: Icon(_obscure2 ? Icons.visibility : Icons.visibility_off), onPressed: () => setState(() => _obscure2 = !_obscure2)),
                      ),
                      validator: (v) => v != _pass.text ? 'Passwords do not match' : null,
                    ),
                    const SizedBox(height: 12),
                    FormField<bool>(
                      initialValue: _agree,
                      validator: (v) => (v ?? false) ? null : 'You must tick to agree to Terms and Conditions',
                      builder: (state) {
                        final hasError = state.hasError;
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              decoration: BoxDecoration(
                                border: Border.all(
                                  color: hasError ? const Color(AppConstants.errorColorValue) : Colors.transparent,
                                  width: hasError ? 1.5 : 1,
                                ),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Row(children: [
                                Checkbox(
                                  value: state.value ?? false,
                                  activeColor: const Color(AppConstants.primaryColorValue),
                                  side: BorderSide(
                                    color: hasError ? const Color(AppConstants.errorColorValue) : Colors.grey,
                                    width: hasError ? 2 : 1,
                                  ),
                                  onChanged: (v) {
                                    state.didChange(v ?? false);
                                    setState(() => _agree = v ?? false);
                                  },
                                ),
                                const Expanded(child: Text('I agree to Terms and Conditions', style: TextStyle(fontSize: 12))),
                              ]),
                            ),
                            if (hasError)
                              Padding(
                                padding: const EdgeInsets.only(left: 12, top: 6),
                                child: Text(
                                  state.errorText!,
                                  style: const TextStyle(color: Color(AppConstants.errorColorValue), fontSize: 12),
                                ),
                              ),
                          ],
                        );
                      },
                    ),
                    const SizedBox(height: 12),
                    CustomButton(text: 'Register', onPressed: _register, isLoading: _loading),
                    const SizedBox(height: 16),
                    Wrap(alignment: WrapAlignment.center, crossAxisAlignment: WrapCrossAlignment.center, spacing: 4, children: [
                      const Text('Already have an account? '),
                      GestureDetector(onTap: () => Navigator.pushReplacementNamed(context, '/login'), child: const Text('Login', style: TextStyle(color: Color(AppConstants.primaryColorValue), fontWeight: FontWeight.w700))),
                    ]),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _roleCard({required String value, required IconData icon, required String title, required String subtitle}) {
    final selected = _role == value;
    return GestureDetector(
      onTap: () => setState(() => _role = value),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 10),
        decoration: BoxDecoration(
          color: selected ? const Color(0xFFE8F3FA) : Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: selected ? const Color(AppConstants.primaryColorValue) : const Color(0xFFE5E7EB),
            width: selected ? 2 : 1,
          ),
        ),
        child: Column(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: selected ? const Color(AppConstants.primaryColorValue) : const Color(0xFFF3F4F6),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: selected ? Colors.white : const Color(AppConstants.secondaryColorValue)),
            ),
            const SizedBox(height: 8),
            Text(title, textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.w800, fontSize: 12, color: selected ? const Color(AppConstants.primaryColorValue) : const Color(AppConstants.secondaryColorValue))),
            const SizedBox(height: 2),
            Text(subtitle, textAlign: TextAlign.center, style: const TextStyle(fontSize: 10, color: Colors.grey)),
            const SizedBox(height: 6),
            Icon(selected ? Icons.radio_button_checked : Icons.radio_button_off,
                color: selected ? const Color(AppConstants.primaryColorValue) : Colors.grey, size: 18),
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
