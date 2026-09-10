import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:image_picker/image_picker.dart';
import '../../models/property.dart';
import '../../services/api_service.dart';
import '../../widgets/custom_button.dart';
import '../../utils/constants.dart';

/// Add/Edit property like web (4 types: House/Apartment/Commercial/Plot + photos).
/// Arguments: Property? (null = add).
class SellerPropertyFormScreen extends StatefulWidget {
  const SellerPropertyFormScreen({super.key});
  @override
  State<SellerPropertyFormScreen> createState() => _SellerPropertyFormScreenState();
}

class _SellerPropertyFormScreenState extends State<SellerPropertyFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _api = ApiService();
  final _picker = ImagePicker();
  Property? _existing;
  bool _inited = false;
  bool _saving = false;

  String _category = 'house'; // house | apartment | commercial | plot
  final _title = TextEditingController();
  final _desc = TextEditingController();
  final _price = TextEditingController();
  final _location = TextEditingController();
  final _area = TextEditingController();
  final _napa = TextEditingController();
  String _status = 'available';
  String _propertyType = 'house';
  // house
  final _beds = TextEditingController(text: '3');
  final _baths = TextEditingController(text: '2');
  final _floor = TextEditingController();
  final _totalFloors = TextEditingController();
  final _parking = TextEditingController(text: '0');
  String _furnished = '';
  final _year = TextEditingController();
  String _condition = 'good';
  final _houseSize = TextEditingController();
  final _landSize = TextEditingController();
  bool _security = false, _pool = false, _garden = false, _balcony = false, _elevator = false, _ac = false, _gen = false;
  // plot
  String _landType = 'residential';
  final _dims = TextEditingController();
  String _landUse = 'residential';
  bool _road = false, _elec = false, _water = false, _sewage = false, _net = false, _fenced = false;
  String _deed = 'yes', _survey = 'yes', _zoning = '';
  XFile? _cover;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_inited) return;
    _inited = true;
    final arg = ModalRoute.of(context)!.settings.arguments;
    if (arg is Property) {
      _existing = arg;
      final p = arg;
      _category = p.isPlot ? 'plot' : (p.propertyType == 'apartment' ? 'apartment' : (p.propertyType == 'commercial' ? 'commercial' : 'house'));
      _title.text = p.title;
      _desc.text = p.description;
      _price.text = p.price;
      _location.text = p.location;
      _area.text = p.area;
      _napa.text = p.napa ?? '';
      _status = p.status;
      _propertyType = p.propertyType;
      _beds.text = '${p.bedrooms}';
      _baths.text = '${p.bathrooms}';
      if (p.floorNumber != null) _floor.text = '${p.floorNumber}';
      if (p.totalFloors != null) _totalFloors.text = '${p.totalFloors}';
      _parking.text = '${p.parking}';
      _furnished = p.furnished;
      if (p.yearBuilt != null) _year.text = '${p.yearBuilt}';
      _condition = p.propertyCondition.isNotEmpty ? p.propertyCondition : 'good';
      _houseSize.text = p.propertySize ?? '';
      _landSize.text = p.landSize ?? '';
      _security = p.security; _pool = p.swimmingPool; _garden = p.garden; _balcony = p.balcony;
      _elevator = p.elevator; _ac = p.airConditioning; _gen = p.backupGenerator;
      _landType = p.landType.isNotEmpty ? p.landType : 'residential';
      _dims.text = p.plotDimensions;
      _landUse = p.landUse.isNotEmpty ? p.landUse : 'residential';
      _road = p.infraRoad; _elec = p.infraElectricity; _water = p.infraWater;
      _sewage = p.infraSewage; _net = p.infraInternet; _fenced = p.infraFenced;
      _deed = p.titleDeedAvailable.isNotEmpty ? p.titleDeedAvailable : 'yes';
      _survey = p.surveyPlanAvailable.isNotEmpty ? p.surveyPlanAvailable : 'yes';
      _zoning = p.zoning;
    }
  }

  bool get _isPlot => _category == 'plot';

  Future<void> _pickCover() async {
    final img = await _picker.pickImage(source: ImageSource.gallery, maxWidth: 1600, imageQuality: 85);
    if (img != null) setState(() => _cover = img);
  }

  Map<String, String> _fields() {
    final m = <String, String>{
      'title': _title.text.trim(),
      'description': _desc.text.trim(),
      'price': _price.text.trim(),
      'location': _location.text.trim(),
      'area': _area.text.trim().isEmpty ? '0' : _area.text.trim(),
      'status': _status,
      'napa': _napa.text.trim(),
    };
    if (_isPlot) {
      m.addAll({
        'property_category': 'plot',
        'property_type': 'land',
        'land_type': _landType,
        'plot_dimensions': _dims.text.trim(),
        'land_use': _landUse,
        'title_deed_available': _deed,
        'survey_plan_available': _survey,
        'zoning': _zoning,
      });
      for (final e in {'infrastructure_road': _road, 'infrastructure_electricity': _elec, 'infrastructure_water': _water, 'infrastructure_sewage': _sewage, 'infrastructure_internet': _net, 'infrastructure_fenced': _fenced}.entries) {
        if (e.value) m[e.key] = 'on';
      }
    } else {
      final ptype = _category == 'apartment' ? 'apartment' : (_category == 'commercial' ? 'commercial' : _propertyType);
      m.addAll({
        'property_category': 'house',
        'property_type': ptype,
        'bedrooms': _beds.text.trim().isEmpty ? '0' : _beds.text.trim(),
        'bathrooms': _baths.text.trim().isEmpty ? '0' : _baths.text.trim(),
        'parking': _parking.text.trim().isEmpty ? '0' : _parking.text.trim(),
        'furnished': _furnished,
        'property_condition': _condition,
      });
      if (_floor.text.trim().isNotEmpty) m['floor_number'] = _floor.text.trim();
      if (_totalFloors.text.trim().isNotEmpty) m['total_floors'] = _totalFloors.text.trim();
      if (_year.text.trim().isNotEmpty) m['year_built'] = _year.text.trim();
      if (_houseSize.text.trim().isNotEmpty) m['property_size'] = _houseSize.text.trim();
      if (_landSize.text.trim().isNotEmpty) m['land_size'] = _landSize.text.trim();
      for (final e in {'security': _security, 'swimming_pool': _pool, 'garden': _garden, 'balcony': _balcony, 'elevator': _elevator, 'air_conditioning': _ac, 'backup_generator': _gen}.entries) {
        if (e.value) m[e.key] = 'on';
      }
    }
    return m;
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    try {
      if (_existing == null) {
        await _api.createProperty(_fields(), images: _cover == null ? null : [_cover!]);
        if (!mounted) return;
        Fluttertoast.showToast(msg: 'Property added successfully');
      } else {
        await _api.updateProperty(_existing!.id, _fields());
        if (_cover != null) {
          try {
            await _api.uploadGallery(_existing!.id, [_cover!]);
          } catch (_) {}
        }
        if (!mounted) return;
        Fluttertoast.showToast(msg: 'Property updated successfully');
      }
      if (mounted) Navigator.pop(context);
    } catch (e) {
      Fluttertoast.showToast(msg: e.toString().replaceAll('Exception:', '').trim(), backgroundColor: const Color(AppConstants.errorColorValue), toastLength: Toast.LENGTH_LONG);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: const Color(AppConstants.secondaryColorValue),
        title: Text(_existing == null ? 'Add Property' : 'Edit Property', style: const TextStyle(color: Colors.white)),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Property Type', style: TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Wrap(spacing: 8, children: [
              _cat('house', 'House', Icons.home),
              _cat('apartment', 'Apartment', Icons.apartment),
              _cat('commercial', 'Commercial', Icons.business),
              _cat('plot', 'Plot', Icons.map),
            ]),
            const SizedBox(height: 16),
            _field(_title, 'Title *', required: true),
            _field(_desc, 'Description *', required: true, lines: 3),
            Row(children: [
              Expanded(child: _field(_price, 'Price (TZS) *', required: true, number: true)),
              const SizedBox(width: 12),
              Expanded(child: _field(_area, 'Area (sqm) *', required: true, number: true)),
            ]),
            _field(_location, 'Location *', required: true),
            Row(children: [
              Expanded(child: _dropdown('Status', _status, const ['available', 'sold', 'rented', 'pending', 'reserved', 'under_construction'], (v) => setState(() => _status = v))),
              const SizedBox(width: 12),
              Expanded(child: _field(_napa, 'Plot No. (NaPa)')),
            ]),
            if (!_isPlot && _category == 'house') ...[
              _dropdown('Subtype', _propertyType, const ['house', 'townhouse', 'villa', 'bungalow', 'duplex'], (v) => setState(() => _propertyType = v)),
            ],
            if (!_isPlot) ...[
              const SizedBox(height: 8),
              const Text('Features', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
              const SizedBox(height: 8),
              Row(children: [
                Expanded(child: _field(_beds, 'Bedrooms', number: true)),
                const SizedBox(width: 12),
                Expanded(child: _field(_baths, 'Bathrooms', number: true)),
                const SizedBox(width: 12),
                Expanded(child: _field(_parking, 'Parking', number: true)),
              ]),
              Row(children: [
                Expanded(child: _field(_floor, 'Floor No.', number: true)),
                const SizedBox(width: 12),
                Expanded(child: _field(_totalFloors, 'Total Floors', number: true)),
              ]),
              Row(children: [
                Expanded(child: _dropdown('Furnished', _furnished, const ['', 'yes', 'no', 'partially'], (v) => setState(() => _furnished = v))),
                const SizedBox(width: 12),
                Expanded(child: _field(_year, 'Year Built', number: true)),
              ]),
              Row(children: [
                Expanded(child: _dropdown('Condition', _condition, const ['new', 'good', 'needs_renovation', 'under_construction'], (v) => setState(() => _condition = v))),
                const SizedBox(width: 12),
                Expanded(child: _field(_houseSize, 'House Size (sqm)', number: true)),
              ]),
              _field(_landSize, 'Land Size (sqm)', number: true),
              Wrap(spacing: 4, children: [
                _check('Security', _security, (v) => setState(() => _security = v)),
                _check('Pool', _pool, (v) => setState(() => _pool = v)),
                _check('Garden', _garden, (v) => setState(() => _garden = v)),
                _check('Balcony', _balcony, (v) => setState(() => _balcony = v)),
                _check('Elevator', _elevator, (v) => setState(() => _elevator = v)),
                _check('AC', _ac, (v) => setState(() => _ac = v)),
                _check('Generator', _gen, (v) => setState(() => _gen = v)),
              ]),
            ],
            if (_isPlot) ...[
              const SizedBox(height: 8),
              const Text('Plot Details', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
              const SizedBox(height: 8),
              Row(children: [
                Expanded(child: _dropdown('Land Type', _landType, const ['residential', 'commercial', 'agricultural', 'mixed'], (v) => setState(() => _landType = v))),
                const SizedBox(width: 12),
                Expanded(child: _dropdown('Land Use', _landUse, const ['residential', 'commercial', 'agricultural', 'mixed'], (v) => setState(() => _landUse = v))),
              ]),
              Row(children: [
                Expanded(child: _field(_dims, 'Dimensions (m x m)')),
                const SizedBox(width: 12),
                Expanded(child: _dropdown('Zoning', _zoning, const ['', 'residential', 'commercial', 'industrial', 'agricultural'], (v) => setState(() => _zoning = v))),
              ]),
              Row(children: [
                Expanded(child: _dropdown('Title Deed', _deed, const ['yes', 'no', 'in_process'], (v) => setState(() => _deed = v))),
                const SizedBox(width: 12),
                Expanded(child: _dropdown('Survey Plan', _survey, const ['yes', 'no'], (v) => setState(() => _survey = v))),
              ]),
              Wrap(spacing: 4, children: [
                _check('Road', _road, (v) => setState(() => _road = v)),
                _check('Electricity', _elec, (v) => setState(() => _elec = v)),
                _check('Water', _water, (v) => setState(() => _water = v)),
                _check('Sewage', _sewage, (v) => setState(() => _sewage = v)),
                _check('Internet', _net, (v) => setState(() => _net = v)),
                _check('Fenced', _fenced, (v) => setState(() => _fenced = v)),
              ]),
            ],
            const SizedBox(height: 16),
            const Text('Cover Photo', style: TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            InkWell(
              onTap: _pickCover,
              child: Container(
                height: 120,
                width: double.infinity,
                decoration: BoxDecoration(color: const Color(0xFFF3F4F6), borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE5E7EB))),
                child: _cover != null
                    ? Center(child: Text(_cover!.name, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)))
                    : const Column(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(Icons.add_a_photo, color: Colors.grey), SizedBox(height: 4), Text('Tap to choose photo', style: TextStyle(color: Colors.grey, fontSize: 12))]),
              ),
            ),
            const SizedBox(height: 20),
            CustomButton(text: _existing == null ? 'Submit Property' : 'Save Changes', onPressed: _save, isLoading: _saving),
            const SizedBox(height: 24),
          ]),
        ),
      ),
    );
  }

  Widget _cat(String value, String label, IconData icon) {
    final sel = _category == value;
    return ChoiceChip(
      label: Row(mainAxisSize: MainAxisSize.min, children: [Icon(icon, size: 16, color: sel ? Colors.white : const Color(AppConstants.primaryColorValue)), const SizedBox(width: 4), Text(label)]),
      selected: sel,
      selectedColor: const Color(AppConstants.primaryColorValue),
      labelStyle: TextStyle(color: sel ? Colors.white : Colors.black87, fontWeight: FontWeight.w600, fontSize: 12),
      onSelected: (_) => setState(() => _category = value),
    );
  }

  Widget _field(TextEditingController c, String label, {bool required = false, bool number = false, int lines = 1}) => Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: TextFormField(
          controller: c,
          keyboardType: number ? TextInputType.number : TextInputType.text,
          maxLines: lines,
          decoration: InputDecoration(labelText: label, border: const OutlineInputBorder()),
          validator: required ? (v) => (v == null || v.trim().isEmpty) ? 'Required' : null : null,
        ),
      );

  Widget _dropdown(String label, String value, List<String> options, ValueChanged<String> onChanged) => Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: DropdownButtonFormField<String>(
          initialValue: options.contains(value) ? value : options.first,
          decoration: InputDecoration(labelText: label, border: const OutlineInputBorder()),
          items: options.map((o) => DropdownMenuItem(value: o, child: Text(o.isEmpty ? '--' : o, overflow: TextOverflow.ellipsis))).toList(),
          onChanged: (v) { if (v != null) onChanged(v); },
        ),
      );

  Widget _check(String label, bool value, ValueChanged<bool> onChanged) => Row(mainAxisSize: MainAxisSize.min, children: [
        Checkbox(value: value, onChanged: (v) => onChanged(v ?? false), activeColor: const Color(AppConstants.primaryColorValue)),
        Text(label, style: const TextStyle(fontSize: 12)),
      ]);
}
