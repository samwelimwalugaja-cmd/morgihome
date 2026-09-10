import 'package:flutter/material.dart';
import '../utils/constants.dart';

/// Landing page — like the doctor-appointment template:
/// waves crossing the screen, big logo in the middle, two buttons at the bottom.
class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  static const _darkBlue = Color(AppConstants.secondaryColorValue);
  static const _bahari = Color(AppConstants.primaryColorValue);

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final topHeight = size.height * 0.52;

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        top: false,
        child: Column(
          children: [
            // ===== Top section: dark blue + crossing waves =====
            SizedBox(
              height: topHeight,
              child: Stack(
                children: [
                  // Background dark blue
                  Container(color: _darkBlue),
                  // Back wave (faint ocean blue) — crosses the screen
                  Positioned.fill(
                    child: ClipPath(
                      clipper: _CrossWaveClipper(peak: 0.62, depth: 46),
                      child: Container(color: _bahari.withValues(alpha: 0.35)),
                    ),
                  ),
                  // Front wave (white) — crosses below it
                  Positioned.fill(
                    child: ClipPath(
                      clipper: _CrossWaveClipper(peak: 0.74, depth: 56),
                      child: Container(color: Colors.white),
                    ),
                  ),
                  // Logo + name in the middle of the blue section
                  Positioned.fill(
                    child: Padding(
                      padding: EdgeInsets.only(bottom: topHeight * 0.22),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 16),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(28),
                              border: Border.all(color: Colors.white, width: 3),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black.withValues(alpha: 0.3),
                                  blurRadius: 18,
                                  offset: const Offset(0, 10),
                                ),
                              ],
                            ),
                            child: Image.asset(
                              'assets/images/morgihome_logo.png',
                              width: 150,
                              fit: BoxFit.contain,
                              errorBuilder: (_, __, ___) => const Icon(Icons.home_work, color: _bahari, size: 60),
                            ),
                          ),
                          const SizedBox(height: 14),
                          const Text(
                            'MorgiHome',
                            style: TextStyle(color: Colors.white, fontSize: 34, fontWeight: FontWeight.w900, letterSpacing: 0.5),
                          ),
                          const Text(
                            'Your Home, Your Mortgage',
                            style: TextStyle(color: Colors.white70, fontSize: 14, fontWeight: FontWeight.w500),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
            // ===== Bottom section: description + two buttons =====
            Expanded(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(28, 8, 28, 20),
                child: Column(
                  children: [
                    const Text(
                      'Welcome to MorgiHome',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: _darkBlue),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Apply for a mortgage, track your applications, or sell your houses — all in one place.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey, fontSize: 14, height: 1.5),
                    ),
                    const Spacer(),
                    SizedBox(
                      height: 54,
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: () => Navigator.pushNamed(context, '/login'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: _bahari,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                          elevation: 3,
                          textStyle: const TextStyle(fontWeight: FontWeight.w800, fontSize: 17),
                        ),
                        child: const Text('Login'),
                      ),
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      height: 54,
                      width: double.infinity,
                      child: OutlinedButton(
                        onPressed: () => Navigator.pushNamed(context, '/register'),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: _darkBlue,
                          side: const BorderSide(color: _darkBlue, width: 2),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                          textStyle: const TextStyle(fontWeight: FontWeight.w800, fontSize: 17),
                        ),
                        child: const Text('Register'),
                      ),
                    ),
                    const SizedBox(height: 14),
                    Image.asset(
                      'assets/images/morgihome_logo.png',
                      height: 26,
                      fit: BoxFit.contain,
                      errorBuilder: (_, __, ___) => const SizedBox.shrink(),
                    ),
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

/// Wave crossing the full screen width (like the doctor template).
class _CrossWaveClipper extends CustomClipper<Path> {
  /// peak: 0..1 — where the wave starts vertically (0=top, 1=bottom).
  final double peak;
  final double depth;
  _CrossWaveClipper({required this.peak, required this.depth});

  @override
  Path getClip(Size size) {
    final y = size.height * peak;
    final path = Path();
    path.moveTo(0, y);
    path.cubicTo(
      size.width * 0.25, y - depth,
      size.width * 0.35, y + depth,
      size.width * 0.55, y + depth * 0.4,
    );
    path.cubicTo(
      size.width * 0.72, y - depth * 0.2,
      size.width * 0.85, y - depth,
      size.width, y - depth * 0.3,
    );
    path.lineTo(size.width, size.height);
    path.lineTo(0, size.height);
    path.close();
    return path;
  }

  @override
  bool shouldReclip(covariant _CrossWaveClipper oldClipper) =>
      oldClipper.peak != peak || oldClipper.depth != depth;
}
