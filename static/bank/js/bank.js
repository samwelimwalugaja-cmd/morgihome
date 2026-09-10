/* MorgiHome Bank JS - sidebar dropdown, search, pagination, charts helpers, modals */
(function () {
  // Sidebar dropdown (fallback kama onclick haipo)
  window.toggleBankSubmenu = function (id) {
    var el = document.getElementById(id);
    if (el) el.classList.toggle('hidden');
  };
  // Table search filter (client-side)
  window.bankTableSearch = function (inputId, tableId) {
    var q = (document.getElementById(inputId).value || '').toLowerCase();
    document.querySelectorAll('#' + tableId + ' tbody tr').forEach(function (tr) {
      tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  };
  // ESC hufunga modals
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      ['approveModal', 'rejectModal'].forEach(function (id) {
        var m = document.getElementById(id);
        if (m) m.classList.add('hidden');
      });
    }
  });
})();
