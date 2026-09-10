/* MorgiHome Auth - CSP compliant, email as login - SweetAlert2 + red border only */
(function () {
  "use strict";

  function togglePass(id) {
    var inp = document.getElementById(id);
    if (!inp) return;
    var wrapper = inp.closest(".input-icon");
    var btn = wrapper ? wrapper.querySelector(".eye-btn") : inp.parentNode.querySelector(".eye-btn");
    var ico = btn ? btn.querySelector("i") : null;
    var isPassword = inp.type === "password";
    inp.type = isPassword ? "text" : "password";
    if (ico) ico.className = isPassword ? "bi bi-eye-slash" : "bi bi-eye";
    if (btn) btn.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
    try { inp.focus({ preventScroll: true }); } catch(e) { inp.focus(); }
    try { var len = inp.value.length; inp.setSelectionRange(len, len); } catch(e) {}
  }

  function setError(fieldId, message) {
    var field = document.getElementById("field-" + fieldId);
    var errEl = document.getElementById(fieldId + "-error");
    if (message) {
      if (field) { field.classList.add("has-error"); field.classList.remove("is-valid"); }
      if (errEl) { errEl.textContent = message; errEl.style.display = "block"; }
    } else {
      if (field) field.classList.remove("has-error");
      if (errEl) { errEl.textContent = ""; errEl.style.display = "none"; }
    }
  }
  function setValid(fieldId) {
    var field = document.getElementById("field-" + fieldId);
    if (field) { field.classList.remove("has-error"); field.classList.add("is-valid"); }
    var errEl = document.getElementById(fieldId + "-error");
    if (errEl) { errEl.textContent = ""; errEl.style.display = "none"; }
  }
  function clearValidation(fieldId){
    var field = document.getElementById("field-" + fieldId);
    if(field){ field.classList.remove("has-error"); field.classList.remove("is-valid"); }
  }

  function sweetAlert(icon, title, text){
    if(window.Swal && typeof window.Swal.fire === 'function'){
      window.Swal.fire({icon: icon, title: title, text: text, confirmButtonColor: '#0077B6'});
    } else if(window.showToast){
      window.showToast(text, icon === 'error' ? 'error' : icon === 'success' ? 'success' : icon === 'warning' ? 'warning' : 'info', title);
    } else {
      alert(title + ': ' + text);
    }
  }

  function initEyeButtons() {
    document.querySelectorAll(".eye-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var target = btn.getAttribute("data-target") || btn.getAttribute("aria-controls");
        if (!target) {
          var wrapper = btn.closest(".input-icon");
          var input = wrapper ? wrapper.querySelector("input") : null;
          if (input && input.id) target = input.id;
        }
        if (target) togglePass(target);
      });
    });
  }

  window.togglePass = togglePass;

  document.addEventListener("DOMContentLoaded", function () {
    initEyeButtons();
    var roleInput = document.getElementById("role");
    if(roleInput){
      if(window.location.pathname.indexOf('/signup/seller') !== -1) roleInput.value = 'seller';
      roleInput.addEventListener("change", function(){
        var r = this.value;
        if(r==='seller' && window.location.pathname === '/signup/') { try{ history.replaceState(null,'','/signup/seller/'); }catch(e){} }
        if(r==='customer' && window.location.pathname === '/signup/seller/') { try{ history.replaceState(null,'','/signup/'); }catch(e){} }
        if(r) setValid('role'); else setError('role','Please select account type');
      });
      roleInput.addEventListener("input", function(){ if(this.value) setValid('role'); });
    }
    function attachLiveValidation(id, validator){
      var el = document.getElementById(id);
      if(!el) return;
      var handler = function(){
        var val = el.value ? el.value.trim() : '';
        if(el.type === 'checkbox') val = el.checked;
        var msg = validator(val, el);
        if(val === '' || val === false){
          clearValidation(id);
          if(el.required) setError(id, msg || 'This field is required');
        } else if(msg){
          setError(id, msg);
        } else {
          setValid(id);
        }
      };
      el.addEventListener("input", handler);
      el.addEventListener("change", handler);
      el.addEventListener("blur", handler);
    }
    attachLiveValidation('first_name', function(v){ if(!v) return 'First Name is required'; if(v.length<2) return 'At least 2 characters'; return ''; });
    attachLiveValidation('last_name', function(v){ if(!v) return 'Last Name is required'; if(v.length<2) return 'At least 2 characters'; return ''; });
    attachLiveValidation('email', function(v){ if(!v) return 'Email is required'; if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return 'Enter a valid email'; return ''; });
    attachLiveValidation('phone_number', function(v){ if(!v) return 'Phone is required'; if(!/^\+?\d{9,15}$/.test(v.replace(/\s/g,''))) return 'Enter valid phone e.g. +255 712 345 678'; return ''; });
    attachLiveValidation('role', function(v){ if(!v) return 'Please select account type'; return ''; });
    attachLiveValidation('password', function(v){ if(!v) return 'Password is required'; if(v.length<8) return 'At least 8 characters'; return ''; });
    attachLiveValidation('confirm_password', function(v, el){
      var pwd = document.getElementById('password');
      var pwdVal = pwd ? pwd.value : '';
      if(!v) return 'Please confirm password';
      if(v !== pwdVal) return 'Passwords do not match';
      return '';
    });
    var termsEl = document.getElementById('terms');
    if(termsEl){
      termsEl.addEventListener("change", function(){
        if(this.checked) setValid('terms'); else setError('terms','You must agree to Terms and Privacy Policy');
      });
    }
    var pwdEl = document.getElementById('password');
    var confirmEl = document.getElementById('confirm_password');
    if(pwdEl && confirmEl){
      pwdEl.addEventListener("input", function(){
        if(confirmEl.value) {
          if(confirmEl.value !== this.value) setError('confirm_password','Passwords do not match'); else setValid('confirm_password');
        }
      });
    }

    var loginForm = document.getElementById("login-form");
    if (loginForm) {
      var emailEl = document.getElementById("email");
      var passwordEl = document.getElementById("password");
      if (emailEl) emailEl.addEventListener("input", function () { setError("email", ""); });
      if (passwordEl) passwordEl.addEventListener("input", function () { setError("password", ""); });

      loginForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        setError("email", "");
        setError("password", "");
        var email = (emailEl ? emailEl.value.trim() : "");
        var password = passwordEl ? passwordEl.value : "";
        var valid = true;
        var emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!email) { setError("email", "Email is required"); valid = false; }
        else if (!emailRe.test(email)) { setError("email", "Please enter a valid email address"); valid = false; }
        if (!password) { setError("password", "Password is required"); valid = false; }
        else if (password.length < 6) { setError("password", "Password must be at least 6 characters"); valid = false; }
        if (!valid) { sweetAlert('warning','Validation failed','Please fix the highlighted fields (red border)'); return; }
        try {
          // Get CSRF token if present (fallback, backend is now csrf_exempt but keep for safety)
          var csrfToken = null;
          try {
            var m = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/);
            if (m) csrfToken = decodeURIComponent(m[1]);
            if (!csrfToken) {
              var meta = document.querySelector('meta[name="csrf-token"]');
              if (meta) csrfToken = meta.getAttribute('content');
            }
          } catch(e){}
          var headers = { "Content-Type": "application/json" };
          if (csrfToken) headers["X-CSRFToken"] = csrfToken;
          var res = await fetch("/api/auth/login/", {
            method: "POST",
            headers: headers,
            body: JSON.stringify({ email: email, password: password }),
            credentials: "same-origin"
          });
          var text = await res.text();
          var data = {};
          try { data = text ? JSON.parse(text) : {}; } catch(e) { data = { detail: text.slice(0,300) || "Server error ("+res.status+")" }; }
          if (res.ok && data.access) {
            try { localStorage.setItem("access", data.access); } catch(e){}
            try { localStorage.setItem("refresh", data.refresh); } catch(e){}
            try { localStorage.setItem("user", JSON.stringify(data.user)); } catch(e){}
            sweetAlert('success','Welcome back','Login successful! Redirecting to dashboard...');
            var role = (data.user && data.user.role) ? data.user.role.toLowerCase() : 'customer';
            var dest = "/customer/dashboard/";
            if(role === 'bank') dest = "/bank/dashboard/";
            else if(role === 'seller') dest = "/seller/dashboard/";
            else if(role === 'lawyer') dest = "/lawyer/dashboard/";
            else if(role === 'realestate') dest = "/realestate/dashboard/";
            else if(role === 'customer') dest = "/customer/dashboard/";
            setTimeout(function () { window.location.href = dest; }, 1200);
            setTimeout(function () { if(window.location.pathname === '/login/' || window.location.pathname === '/login') window.location.replace(dest); }, 1800);
          } else {
            var msg = data.error || data.detail || data.non_field_errors || "";
            if (Array.isArray(msg)) msg = msg[0];
            if (!msg && data.email) msg = Array.isArray(data.email) ? data.email[0] : data.email;
            if (!msg && res.status === 429) msg = "Too many attempts. Please wait a minute and try again.";
            if (!msg && res.status === 403) msg = data.error || data.detail || "Access denied. Account may be locked - wait 1 minute and try again.";
            if (!msg) msg = "Invalid credentials, please try again.";
            if (data.email) setError("email", Array.isArray(data.email) ? data.email[0] : data.email);
            if (msg.toLowerCase().indexOf("invalid") !== -1 || msg.toLowerCase().indexOf("credentials") !== -1) { setError("password", msg); }
            sweetAlert('error','Login failed ('+res.status+')', msg);
            console.error("Login failed", res.status, text);
          }
        } catch (err) {
          console.error("Login network error", err);
          sweetAlert('error','Network error', err.message || "Please check server is running (python manage.py runserver)");
        }
      });
    }

    var signupForm = document.getElementById("signup-form");
    if (signupForm) {
      function isValidEmail(email) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email); }
      function isValidPhone(phone) { return /^\+?\d{9,15}$/.test(phone.replace(/\s/g, "")); }

      var signupFields = ["first_name","last_name","email","phone_number","password","confirm_password","role"];
      signupFields.forEach(function (id) {
        var el = document.getElementById(id);
        if (el) {
          el.addEventListener("input", function () { setError(id, ""); });
          el.addEventListener("change", function () { setError(id, ""); });
        }
      });
      var termsEl2 = document.getElementById("terms");
      if (termsEl2) termsEl2.addEventListener("change", function () { setError("terms", ""); });

      function clearAllErrors() {
        ["first_name","last_name","email","phone_number","role","password","confirm_password","terms"].forEach(function (id) { setError(id, ""); });
      }

      signupForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        clearAllErrors();
        var first_name = (document.getElementById("first_name") ? document.getElementById("first_name").value.trim() : "");
        var last_name = (document.getElementById("last_name") ? document.getElementById("last_name").value.trim() : "");
        var email = (document.getElementById("email") ? document.getElementById("email").value.trim() : "");
        var phone = (document.getElementById("phone_number") ? document.getElementById("phone_number").value.trim() : "");
        var role = (document.getElementById("role") ? document.getElementById("role").value : "customer");
        var password = (document.getElementById("password") ? document.getElementById("password").value : "");
        var confirm = (document.getElementById("confirm_password") ? document.getElementById("confirm_password").value : "");
        var terms = (document.getElementById("terms") ? document.getElementById("terms").checked : false);
        var valid = true;

        if (!first_name) { setError("first_name", "First name is required"); valid = false; }
        else if (first_name.length < 2) { setError("first_name", "First name must be at least 2 characters"); valid = false; }

        if (!last_name) { setError("last_name", "Last name is required"); valid = false; }
        else if (last_name.length < 2) { setError("last_name", "Last name must be at least 2 characters"); valid = false; }

        if (!email) { setError("email", "Email is required"); valid = false; }
        else if (!isValidEmail(email)) { setError("email", "Please enter a valid email address"); valid = false; }

        if (!phone) { setError("phone_number", "Phone number is required"); valid = false; }
        else if (!isValidPhone(phone)) { setError("phone_number", "Please enter a valid phone number (e.g. +255 712 345 678)"); valid = false; }

        if (!role) { setError("role", "Please select an account type"); valid = false; }

        if (!password) { setError("password", "Password is required"); valid = false; }
        else if (password.length < 8) { setError("password", "Password must be at least 8 characters"); valid = false; }
        else if (!/(?=.*[A-Za-z])(?=.*\d)/.test(password)) { setError("password", "Password must contain letters and numbers"); valid = false; }

        if (!confirm) { setError("confirm_password", "Please confirm your password"); valid = false; }
        else if (password !== confirm) { setError("confirm_password", "Passwords do not match"); valid = false; }

        if (!terms) { setError("terms", "You must agree to Terms and Privacy Policy"); valid = false; }

        if (!valid) { sweetAlert('warning','Validation failed','Please fix the highlighted fields (red border)'); return; }

        try {
          var csrfToken2 = null;
          try {
            var m2 = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/);
            if (m2) csrfToken2 = decodeURIComponent(m2[1]);
          } catch(e){}
          var headers2 = { "Content-Type": "application/json" };
          if (csrfToken2) headers2["X-CSRFToken"] = csrfToken2;
          var body = { first_name: first_name, last_name: last_name, email: email, phone_number: phone, password: password, confirm_password: confirm, role: role || 'customer' };
          var res = await fetch("/api/auth/signup/", {
            method: "POST",
            headers: headers2,
            body: JSON.stringify(body),
            credentials: "same-origin"
          });
          var text = await res.text();
          var data = {};
          try { data = text ? JSON.parse(text) : {}; } catch(e) { data = { detail: text.slice(0,300) || "Server error ("+res.status+")" }; }
          if (res.status === 201) {
            sweetAlert('success','Account created!','Welcome to MorgiHome. Redirecting to login...');
            setTimeout(function () { window.location.href = "/login/"; }, 1500);
          } else {
            if (data.first_name) setError("first_name", Array.isArray(data.first_name) ? data.first_name[0] : data.first_name);
            if (data.last_name) setError("last_name", Array.isArray(data.last_name) ? data.last_name[0] : data.last_name);
            if (data.email) setError("email", Array.isArray(data.email) ? data.email[0] : data.email);
            if (data.phone_number) setError("phone_number", Array.isArray(data.phone_number) ? data.phone_number[0] : data.phone_number);
            if (data.password) setError("password", Array.isArray(data.password) ? data.password[0] : data.password);
            if (data.confirm_password) setError("confirm_password", Array.isArray(data.confirm_password) ? data.confirm_password[0] : data.confirm_password);
            if (data.role) setError("role", Array.isArray(data.role) ? data.role[0] : data.role);
            if (data.non_field_errors) setError("confirm_password", Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : data.non_field_errors);
            var err = data.email ? (Array.isArray(data.email)?data.email[0]:data.email) : (data.first_name ? (Array.isArray(data.first_name)?data.first_name[0]:data.first_name) : (data.last_name ? (Array.isArray(data.last_name)?data.last_name[0]:data.last_name) : (data.phone_number ? (Array.isArray(data.phone_number)?data.phone_number[0]:data.phone_number) : (data.password ? (Array.isArray(data.password)?data.password[0]:data.password) : (data.confirm_password ? (Array.isArray(data.confirm_password)?data.confirm_password[0]:data.confirm_password) : (data.detail || data.error || JSON.stringify(data).slice(0,200) || "Registration failed"))))));
            if (res.status === 429) err = "Too many attempts. Please wait a minute.";
            sweetAlert('error','Registration failed ('+res.status+')', err);
            console.error("Signup failed", res.status, text);
          }
        } catch (err) {
          console.error("Signup network error", err);
          sweetAlert('error','Network error', err.message || "Please check server is running");
        }
      });
    }
  });
})();
