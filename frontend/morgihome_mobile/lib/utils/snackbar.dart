import 'package:flutter/material.dart';

// Stacked Bootstrap 5 style toast - multiple toasts visible at once
enum SnackBarType { success, error, info, warning }

class _ToastEntry {
  final OverlayEntry entry;
  final DateTime createdAt;
  _ToastEntry(this.entry, this.createdAt);
}

class _StackedToastManager {
  static final List<_ToastEntry> _entries = [];

  static void show(
    BuildContext context,
    String message, {
    SnackBarType type = SnackBarType.info,
    String? title,
    Duration duration = const Duration(milliseconds: 4000),
  }) {
    final overlay = Overlay.of(context, rootOverlay: true);
    final Color accent;
    final IconData icon;
    final String defaultTitle;
    switch (type) {
      case SnackBarType.success:
        accent = const Color(0xFF1B7A43);
        icon = Icons.check_circle_outline;
        defaultTitle = 'Success';
        break;
      case SnackBarType.error:
        accent = const Color(0xFFC0392B);
        icon = Icons.error_outline;
        defaultTitle = 'Error';
        break;
      case SnackBarType.warning:
        accent = const Color(0xFFE67E22);
        icon = Icons.warning_amber_outlined;
        defaultTitle = 'Warning';
        break;
      case SnackBarType.info:
        accent = const Color(0xFF0077B6);
        icon = Icons.info_outline;
        defaultTitle = 'Notice';
        break;
    }

    late OverlayEntry entry;
    entry = OverlayEntry(
      builder: (ctx) {
        // calculate vertical offset based on existing entries
        final index = _entries.indexWhere((e) => e.entry == entry);
        final topOffset = 40.0 + (index < 0 ? _entries.length : index) * 86.0;
        return Positioned(
          top: topOffset,
          right: 16,
          left: 16,
          child: SafeArea(
            child: Align(
              alignment: Alignment.topCenter,
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 420),
                child: Material(
                  color: Colors.transparent,
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(14),
                      border: Border(left: BorderSide(color: accent, width: 5)),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.15),
                          blurRadius: 18,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    padding: const EdgeInsets.fromLTRB(14, 12, 12, 12),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 34,
                          height: 34,
                          decoration: BoxDecoration(
                            color: accent,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(icon, color: Colors.white, size: 20),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                title ?? defaultTitle,
                                style: const TextStyle(
                                  fontSize: 14,
                                  fontWeight: FontWeight.w700,
                                  color: Color(0xFF0A2B4E),
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                message,
                                style: const TextStyle(
                                  fontSize: 13,
                                  color: Color(0xFF4A5568),
                                  height: 1.4,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 8),
                        InkWell(
                          onTap: () {
                            entry.remove();
                            _entries.removeWhere((e) => e.entry == entry);
                          },
                          child: const Padding(
                            padding: EdgeInsets.all(4),
                            child: Icon(Icons.close, size: 18, color: Color(0xFFA0AEC0)),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );

    _entries.add(_ToastEntry(entry, DateTime.now()));
    overlay.insert(entry);

    // Rebuild all entries to update positions when stacking
    for (final e in _entries) {
      e.entry.markNeedsBuild();
    }

    Future.delayed(duration, () {
      if (entry.mounted) {
        entry.remove();
        _entries.removeWhere((e) => e.entry == entry);
        // re-layout remaining
        for (final e in _entries) {
          if (e.entry.mounted) e.entry.markNeedsBuild();
        }
      }
    });
  }
}

void showAppSnackBar(
  BuildContext context,
  String message, {
  SnackBarType type = SnackBarType.info,
  String? title,
  Duration duration = const Duration(milliseconds: 4000),
}) {
  _StackedToastManager.show(
    context,
    message,
    type: type,
    title: title,
    duration: duration,
  );
}
