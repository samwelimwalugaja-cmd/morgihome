import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../utils/snackbar.dart';

/// Property add/edit parity: max 5 photos, each <=2MB, cover selectable.
class PropertyFormScreen extends StatefulWidget {
  final Map<String, dynamic>? existing;
  const PropertyFormScreen({super.key, this.existing});

  @override
  State<PropertyFormScreen> createState() => _PropertyFormScreenState();
}

class _PropertyFormScreenState extends State<PropertyFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _title = TextEditingController();
  final _desc = TextEditingController();
  final _price = TextEditingController();
  final _location = TextEditingController();
  final List<XFile> _images = [];
  int _coverIndex = 0;

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    if (e != null) {
      _title.text = (e['title'] ?? '').toString();
      _desc.text = (e['description'] ?? '').toString();
      _price.text = (e['price'] ?? '').toString();
      _location.text = (e['location'] ?? '').toString();
    }
  }

  Future<void> _pick() async {
    final picker = ImagePicker();
    final files = await picker.pickMultiImage();
    if (files.isEmpty) return;
    if (_images.length + files.length > 5) {
      if (!mounted) return;
      showAppSnackBar(context, 'Maximum 5 photos allowed.', type: SnackBarType.error, title: 'Too many');
      return;
    }
    for (final f in files) {
      final len = await f.length();
      if (len > 2 * 1024 * 1024) {
        if (!mounted) return;
        showAppSnackBar(context, 'Photo "${f.name}" exceeds 2MB.', type: SnackBarType.error, title: 'Too large');
        return;
      }
    }
    setState(() => _images.addAll(files));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.existing == null ? 'Add Property' : 'Edit Property')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextFormField(controller: _title, decoration: const InputDecoration(labelText: 'Title *'), validator: (v) => v == null || v.isEmpty ? 'Required' : null),
            const SizedBox(height: 8),
            TextFormField(controller: _desc, decoration: const InputDecoration(labelText: 'Description *'), maxLines: 3, validator: (v) => v == null || v.isEmpty ? 'Required' : null),
            const SizedBox(height: 8),
            TextFormField(controller: _price, decoration: const InputDecoration(labelText: 'Price TZS *'), keyboardType: TextInputType.number, validator: (v) => v == null || v.isEmpty ? 'Required' : null),
            const SizedBox(height: 8),
            TextFormField(controller: _location, decoration: const InputDecoration(labelText: 'Location *'), validator: (v) => v == null || v.isEmpty ? 'Required' : null),
            const SizedBox(height: 12),
            Row(
              children: [
                const Text('Photos (max 5, 2MB each)', style: TextStyle(fontWeight: FontWeight.bold)),
                const Spacer(),
                TextButton.icon(onPressed: _pick, icon: const Icon(Icons.upload), label: const Text('Choose')),
              ],
            ),
            if (_images.isEmpty) const Text('No new photos selected.', style: TextStyle(color: Colors.grey)),
            Wrap(
              spacing: 8,
              children: [
                for (int i = 0; i < _images.length; i++)
                  Column(
                    children: [
                      Image.file(File(_images[i].path), width: 90, height: 70, fit: BoxFit.cover),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Radio<int>(value: i, groupValue: _coverIndex, onChanged: (v) => setState(() => _coverIndex = v ?? 0)),
                          const Text('Cover', style: TextStyle(fontSize: 11)),
                          IconButton(icon: const Icon(Icons.close, size: 16), onPressed: () => setState(() => _images.removeAt(i))),
                        ],
                      ),
                    ],
                  ),
              ],
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                if (!_formKey.currentState!.validate()) return;
                // NOTE: multipart upload wired to backend in next iteration; for now validate + confirm parity
                showAppSnackBar(context, 'Property validated successfully (${_images.length} photos, cover #${_coverIndex + 1}).', type: SnackBarType.success, title: 'Ready to submit');
              },
              child: const Text('Submit'),
            ),
          ],
        ),
      ),
    );
  }
}
