import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';
import '../widgets/custom_button.dart';

/// Forgot password + resend verification — like web
/// forgot-password / resend-verification pages.
class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});
  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _api = ApiService();
  final _emailCtrl = TextEditingController();
  bool _loading = false;
  bool _resending = false;

  @override
  void dispose() {
    _emailCtrl.dispose();
    super.dispose();
  }

  bool get _valid =>
      _emailCtrl.text.trim().contains('@') &&
      _emailCtrl.text.trim().contains('.');

  Future<void> _sendReset() async {
    if (!_valid) {
      Fluttertoast.showToast(msg: 'Enter a valid email address');
      return;
    }
    setState(() => _loading = true);
    try {
      final msg = await _api.forgotPassword(_emailCtrl.text.trim());
      if (!mounted) return;
      Fluttertoast.showToast(msg: msg, toastLength: Toast.LENGTH_LONG);
    } catch (e) {
      Fluttertoast.showToast(
          msg: e.toString().replaceAll('Exception:', '').trim(),
          backgroundColor: const Color(AppConstants.errorColorValue),
          toastLength: Toast.LENGTH_LONG);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _resend() async {
    if (!_valid) {
      Fluttertoast.showToast(msg: 'Enter a valid email address');
      return;
    }
    setState(() => _resending = true);
    try {
      final msg = await _api.resendVerification(_emailCtrl.text.trim());
      if (!mounted) return;
      Fluttertoast.showToast(msg: msg, toastLength: Toast.LENGTH_LONG);
    } catch (e) {
      Fluttertoast.showToast(
          msg: e.toString().replaceAll('Exception:', '').trim(),
          backgroundColor: const Color(AppConstants.errorColorValue),
          toastLength: Toast.LENGTH_LONG);
    } finally {
      if (mounted) setState(() => _resending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
          backgroundColor: const Color(AppConstants.secondaryColorValue),
          title: const Text('Account Help',
              style: TextStyle(color: Colors.white)),
          iconTheme: const IconThemeData(color: Colors.white)),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Icon(Icons.lock_reset,
                  size: 56,
                  color: Color(AppConstants.primaryColorValue)),
              const SizedBox(height: 12),
              const Text('Forgot password?',
                  textAlign: TextAlign.center,
                  style:
                      TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
              const SizedBox(height: 6),
              const Text(
                  'Enter your account email. We will send a reset link (same as web). If your email is not verified yet, resend the verification link below.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.grey, fontSize: 13)),
              const SizedBox(height: 20),
              TextField(
                  controller: _emailCtrl,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(
                      labelText: 'Email',
                      prefixIcon: Icon(Icons.email),
                      border: OutlineInputBorder())),
              const SizedBox(height: 16),
              CustomButton(
                  text: 'Send Reset Link',
                  icon: Icons.send,
                  onPressed: _sendReset,
                  isLoading: _loading),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                  onPressed: _resending ? null : _resend,
                  icon: _resending
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child:
                              CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.mark_email_read),
                  label: const Text('Resend Verification Email')),
            ]),
      ),
    );
  }
}
