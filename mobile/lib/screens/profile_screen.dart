import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:image_picker/image_picker.dart';
import '../services/api_service.dart';
import '../models/user.dart';
import '../utils/constants.dart';
import '../widgets/custom_button.dart';
import '../widgets/customer_drawer.dart';

/// Profile like web: view + edit + photo upload + change password.
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});
  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _api = ApiService();
  final _picker = ImagePicker();
  User? _user;
  bool _loading = true;
  bool _editing = false;
  bool _saving = false;
  bool _uploading = false;

  final _first = TextEditingController();
  final _last = TextEditingController();
  final _phone = TextEditingController();
  final _oldPass = TextEditingController();
  final _newPass = TextEditingController();
  bool _changingPass = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _first.dispose();
    _last.dispose();
    _phone.dispose();
    _oldPass.dispose();
    _newPass.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final u = await _api.getProfile();
      if (!mounted) return;
      setState(() {
        _user = u;
        _loading = false;
        _first.text = u.firstName;
        _last.text = u.lastName;
        _phone.text = u.phoneNumber;
      });
    } catch (_) {
      final stored = await _api.getStoredUser();
      if (!mounted) return;
      setState(() {
        _user = stored;
        _loading = false;
        if (stored != null) {
          _first.text = stored.firstName;
          _last.text = stored.lastName;
          _phone.text = stored.phoneNumber;
        }
      });
    }
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      final u = await _api.updateProfile(firstName: _first.text.trim(), lastName: _last.text.trim(), phone: _phone.text.trim());
      if (!mounted) return;
      setState(() { _user = u; _editing = false; });
      Fluttertoast.showToast(msg: 'Profile updated successfully');
    } catch (e) {
      Fluttertoast.showToast(msg: e.toString().replaceAll('Exception:', '').trim(), backgroundColor: const Color(AppConstants.errorColorValue));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _pickPhoto() async {
    final img = await _picker.pickImage(source: ImageSource.gallery, maxWidth: 1024, imageQuality: 85);
    if (img == null) return;
    setState(() => _uploading = true);
    try {
      final u = await _api.uploadProfilePhoto(img);
      if (!mounted) return;
      setState(() => _user = u);
      Fluttertoast.showToast(msg: 'Profile photo updated');
    } catch (e) {
      Fluttertoast.showToast(msg: e.toString().replaceAll('Exception:', '').trim(), backgroundColor: const Color(AppConstants.errorColorValue));
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  Future<void> _changePassword() async {
    if (_oldPass.text.isEmpty || _newPass.text.length < 8) {
      Fluttertoast.showToast(msg: 'Enter current password and a new one (min 8 chars)');
      return;
    }
    setState(() => _changingPass = true);
    try {
      await _api.changePassword(oldPassword: _oldPass.text, newPassword: _newPass.text);
      if (!mounted) return;
      _oldPass.clear();
      _newPass.clear();
      Fluttertoast.showToast(msg: 'Password changed successfully');
    } catch (e) {
      Fluttertoast.showToast(msg: e.toString().replaceAll('Exception:', '').trim(), backgroundColor: const Color(AppConstants.errorColorValue));
    } finally {
      if (mounted) setState(() => _changingPass = false);
    }
  }

  Future<void> _logout() async {
    await _api.logout();
    if (!mounted) return;
    Navigator.pushReplacementNamed(context, '/welcome');
  }

  @override
  Widget build(BuildContext context) {
    final isSeller = (_user?.role ?? '') == 'seller';
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      drawer: isSeller ? null : const CustomerDrawer(active: 'profile'),
      appBar: AppBar(
        backgroundColor: const Color(AppConstants.secondaryColorValue),
        title: const Text('Profile', style: TextStyle(color: Colors.white)),
        centerTitle: true,
        actions: [
          if (!_loading && _user != null)
            IconButton(
              icon: Icon(_editing ? Icons.close : Icons.edit, color: Colors.white),
              onPressed: () => setState(() => _editing = !_editing),
            ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _user == null
              ? const Center(child: Text('No user data'))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16), border: Border.all(color: const Color(0xFFE5E7EB))),
                        child: Column(children: [
                          Stack(children: [
                            _avatar(),

                            Positioned(
                              bottom: 0, right: 0,
                              child: InkWell(
                                onTap: _uploading ? null : _pickPhoto,
                                child: Container(
                                  width: 30, height: 30,
                                  decoration: const BoxDecoration(shape: BoxShape.circle, color: Color(AppConstants.primaryColorValue)),
                                  child: _uploading
                                      ? const Padding(padding: EdgeInsets.all(7), child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                                      : const Icon(Icons.camera_alt, size: 15, color: Colors.white),
                                ),
                              ),
                            ),
                          ]),
                          const SizedBox(height: 12),
                          Text(_user!.fullName, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                          Text(_user!.email, style: const TextStyle(color: Colors.grey)),
                          const SizedBox(height: 8),
                          Container(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6), decoration: BoxDecoration(color: const Color(0xFFDCFCE7), borderRadius: BorderRadius.circular(20)), child: Text(_user!.role.toUpperCase(), style: const TextStyle(color: Color(0xFF15803D), fontSize: 11, fontWeight: FontWeight.w700))),
                        ]),
                      ),
                      const SizedBox(height: 16),
                      if (_editing) ...[
                        TextField(controller: _first, decoration: const InputDecoration(labelText: 'First Name', border: OutlineInputBorder())),
                        const SizedBox(height: 12),
                        TextField(controller: _last, decoration: const InputDecoration(labelText: 'Last Name', border: OutlineInputBorder())),
                        const SizedBox(height: 12),
                        TextField(controller: _phone, keyboardType: TextInputType.phone, decoration: const InputDecoration(labelText: 'Phone', border: OutlineInputBorder())),
                        const SizedBox(height: 12),
                        CustomButton(text: 'Save Changes', onPressed: _save, isLoading: _saving),
                        const SizedBox(height: 16),
                      ] else ...[
                        _row(Icons.email, 'Email', _user!.email),
                        _row(Icons.phone, 'Phone', _user!.phoneNumber),
                        _row(Icons.verified_user, 'Verified', _user!.isVerified ? 'Yes' : 'No'),
                      ],
                      _row(Icons.lock, 'Change Password', ''),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(0, 0, 0, 12),
                        child: Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE5E7EB))),
                          child: Column(children: [
                            TextField(controller: _oldPass, obscureText: true, decoration: const InputDecoration(labelText: 'Current Password', border: OutlineInputBorder())),
                            const SizedBox(height: 12),
                            TextField(controller: _newPass, obscureText: true, decoration: const InputDecoration(labelText: 'New Password (min 8)', border: OutlineInputBorder())),
                            const SizedBox(height: 12),
                            CustomButton(text: 'Change Password', onPressed: _changePassword, isLoading: _changingPass),
                          ]),
                        ),
                      ),
                      const SizedBox(height: 12),
                      CustomButton(text: 'Logout', icon: Icons.logout, onPressed: _logout),
                    ],
                  ),
                ),
      bottomNavigationBar: isSeller
          ? null
          : BottomNavigationBar(
              currentIndex: 2,
              selectedItemColor: const Color(AppConstants.primaryColorValue),
              onTap: (i) {
                if (i == 0) Navigator.pushReplacementNamed(context, '/home');
                if (i == 1) Navigator.pushReplacementNamed(context, '/applications');
              },
              items: const [
                BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
                BottomNavigationBarItem(icon: Icon(Icons.description), label: 'Applications'),
                BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
              ],
            ),
    );
  }

  /// Avatar salama: picha ikishindikana, initials zinaonekana (hakuna crash).
  Widget _avatar() {
    final photo = (_user?.profileImage ?? '').trim();
    final hasPhoto = photo.isNotEmpty;
    return Container(
      width: 80,
      height: 80,
      decoration: const BoxDecoration(shape: BoxShape.circle, color: Color(AppConstants.primaryColorValue)),
      clipBehavior: Clip.antiAlias,
      child: hasPhoto
          ? Image.network(
              _api.buildImageUrl(photo),
              width: 80,
              height: 80,
              fit: BoxFit.cover,
              gaplessPlayback: true,
              errorBuilder: (_, __, ___) => Center(
                child: Text(_user?.initials ?? '?', style: const TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w800)),
              ),
            )
          : Center(
              child: Text(_user?.initials ?? '?', style: const TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w800)),
            ),
    );
  }

  Widget _row(IconData icon, String label, String value) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE5E7EB))),
      child: Row(children: [
        Container(width: 40, height: 40, decoration: BoxDecoration(color: const Color(0xFFF0F9FF), borderRadius: BorderRadius.circular(8)), child: Icon(icon, color: const Color(AppConstants.primaryColorValue))),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)), if (value.isNotEmpty) Text(value, style: const TextStyle(fontWeight: FontWeight.w600))])),
      ]),
    );
  }
}
