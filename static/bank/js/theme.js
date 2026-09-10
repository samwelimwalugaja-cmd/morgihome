/**
 * MorgiHome - Theme Toggle
 * - Inahifadhi mfumo wa template: kuongeza/kuondoa class 'dark' kwenye <html>
 * - Inakumbuka chaguo la mtumiaji kupitia localStorage
 * - Inaheshimu prefers-color-scheme kama hakuna chaguo lililohifadhiwa
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
    if (btn) btn.setAttribute('aria-label', theme === 'dark' ? 'Badilisha kwenda Light Mode' : 'Badilisha kwenda Dark Mode');
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

  // 1. Apply theme kabla ya paint (inaitwa mara moja head script inapopakia)
  //    Hii script inapaswa kupakiwa kwenye <head> kabla ya CSS ili kuepuka FOUC
  const initialTheme = getPreferredTheme();
  applyTheme(initialTheme);

  // Expose kwa matumizi ya nje
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

  // 2. Baada ya DOM kupakia, funga event listener kwenye button
  document.addEventListener('DOMContentLoaded', function () {
    // Verifysha theme sahihi baada ya DOM (kama script ya head haikukimbia)
    applyTheme(getPreferredTheme());

    const btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.addEventListener('click', function () {
        window.MorgiTheme.toggle();
      });
    }

    // Sikiliza system changes tu kama mtumiaji hajaweka preference
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
