import 'package:flutter/material.dart';
import '../utils/constants.dart';

class CustomButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final bool isLoading;
  final bool isOutlined;
  final IconData? icon;

  const CustomButton({
    super.key,
    required this.text,
    this.onPressed,
    this.isLoading = false,
    this.isOutlined = false,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 48,
      child: ElevatedButton(
        onPressed: isLoading ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: isOutlined ? Colors.white : const Color(AppConstants.primaryColorValue),
          foregroundColor: isOutlined ? const Color(AppConstants.primaryColorValue) : Colors.white,
          // Solid flat colors only - no gradient/tint/shadow
          surfaceTintColor: Colors.transparent,
          shadowColor: Colors.transparent,
          side: isOutlined ? const BorderSide(color: Color(AppConstants.primaryColorValue)) : null,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          elevation: 0,
        ),
        child: isLoading
            ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
            : Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (icon != null) ...[Icon(icon, size: 18), const SizedBox(width: 8)],
                  Text(text, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
                ],
              ),
      ),
    );
  }
}
