/**
 * MorgiHome - Theme Toggle
 * - Saves template system: adds/removes 'dark' class on <html>
 * - Remembers user choice via localStorage
 * - Respects prefers-color-scheme if no stored choice
 */
(function () {
  const STORAGE_KEY = 'theme'; // 'dark' | 'light'
  const html = document.documentElement;

  function getStoredTheme() {
    try { return localStorage.getItem(STORAGE_KEY); } catch (e) { return null; }
  }
  function setStoredTheme(theme) {
    try { localStorage.setItem(STORAGE_KEY, theme); } catch (e) {}
  }

  function applyTheme(theme) {
    if (theme === 'dark') {
      html.classList.add('dark');
    } else {
      html.classList.remove('dark');
    }
    // Update toggle icons if present
    updateIcons(theme);
    // ARIA
    const btn = document.getElementById('theme-toggle');
    if (btn) btn.setAttribute('aria-label', theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode');
  }

  function updateIcons(theme) {
    const sun = document.getElementById('icon-sun');
    const moon = document.getElementById('icon-moon');
    if (!sun || !moon) return;
    if (theme === 'dark') {
      sun.classList.remove('hidden');
      moon.classList.add('hidden');
    } else {
      sun.classList.add('hidden');
      moon.classList.remove('hidden');
    }
  }

  function getPreferredTheme() {
    const stored = getStoredTheme();
    if (stored === 'dark' || stored === 'light') return stored;
    // System preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  }

  // 1. Apply theme before paint (called once head script loads)
  //    This script should be loaded in <head> before CSS to avoid FOUC
  const initialTheme = getPreferredTheme();
  applyTheme(initialTheme);

  // Expose for external use
  window.MorgiTheme = {
    toggle: function () {
      const isDark = html.classList.contains('dark');
      const next = isDark ? 'light' : 'dark';
      applyTheme(next);
      setStoredTheme(next);
      return next;
    },
    set: function (theme) {
      if (theme !== 'dark' && theme !== 'light') return;
      applyTheme(theme);
      setStoredTheme(theme);
    },
    get: function () {
      return html.classList.contains('dark') ? 'dark' : 'light';
    }
  };

  // 2. After DOM loads, attach event listener to button
  document.addEventListener('DOMContentLoaded', function () {
    // Verify correct theme after DOM (if head script didn't run)
    applyTheme(getPreferredTheme());

    const btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.addEventListener('click', function () {
        window.MorgiTheme.toggle();
      });
    }

    // Listen to system changes only if user hasn't set preference
    if (window.matchMedia) {
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      // Modern browsers
      const handler = (e) => {
        const stored = getStoredTheme();
        if (stored !== 'dark' && stored !== 'light') {
          applyTheme(e.matches ? 'dark' : 'light');
        }
      };
      if (mq.addEventListener) mq.addEventListener('change', handler);
      else if (mq.addListener) mq.addListener(handler);
    }
  });
})();
