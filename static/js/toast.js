/* ============================================================
   MorgiHome Toast / Snackbar notifications
   Usage:  showToast(message, type, title)
   types: 'success' | 'error' | 'info' | 'warning'
   ============================================================ */
(function () {
  "use strict";

  function ensureContainer() {
    var c = document.getElementById("toast-container");
    if (!c) {
      c = document.createElement("div");
      c.id = "toast-container";
      c.className = "toast-container";
      document.body.appendChild(c);
    }
    return c;
  }

  var ICONS = { success: "✓", error: "!", info: "i", warning: "!" };
  var DEFAULT_TITLE = {
    success: "Success",
    error: "Error",
    info: "Notice",
    warning: "Warning",
  };

  function showToast(message, type, title) {
    type = type || "info";
    if (["success", "error", "info", "warning"].indexOf(type) === -1) {
      type = "info";
    }
    var container = ensureContainer();

    var el = document.createElement("div");
    el.className = "toast toast--" + type;

    var icon = document.createElement("div");
    icon.className = "toast__icon";
    icon.textContent = ICONS[type] || "i";

    var body = document.createElement("div");
    body.className = "toast__body";

    var t = document.createElement("p");
    t.className = "toast__title";
    t.textContent = title || DEFAULT_TITLE[type];

    var m = document.createElement("p");
    m.className = "toast__msg";
    m.textContent = message;

    body.appendChild(t);
    body.appendChild(m);

    var close = document.createElement("button");
    close.className = "toast__close";
    close.setAttribute("aria-label", "Close");
    close.textContent = "×";

    var progress = document.createElement("div");
    progress.className = "toast__progress";

    el.appendChild(icon);
    el.appendChild(body);
    el.appendChild(close);
    el.appendChild(progress);

    var DURATION = 4000;
    progress.style.animationDuration = DURATION / 1000 + "s";

    function dismiss() {
      if (el.classList.contains("leaving")) return;
      el.classList.add("leaving");
      setTimeout(function () {
        if (el.parentNode) el.parentNode.removeChild(el);
      }, 300);
    }

    close.addEventListener("click", dismiss);
    container.appendChild(el);
    setTimeout(dismiss, DURATION);
  }

  window.showToast = showToast;
})();
