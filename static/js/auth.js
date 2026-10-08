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

    // ============== Forgot Password page tabs & 3-method logic ==============
    (function initForgotPasswordPage(){
      var tabs = document.querySelectorAll('.auth-tab');
      var panels = document.querySelectorAll('.tab-panel');
      if(!tabs.length) return;
      tabs.forEach(function(tab){
        tab.addEventListener('click', function(){
          var target = this.getAttribute('data-tab');
          tabs.forEach(function(t){ t.classList.remove('active'); });
          panels.forEach(function(p){ p.classList.remove('active'); });
          this.classList.add('active');
          var panel = document.getElementById('panel-' + target);
          if(panel) panel.classList.add('active');
        });
      });

      // helpers
      function getCsrfToken(){
        try{ var m=document.cookie.match(/(?:^|; )csrftoken=([^;]*)/); if(m) return decodeURIComponent(m[1]); }catch(e){}
        return null;
      }
      function jsonHeaders(){
        var h={"Content-Type":"application/json"}; var t=getCsrfToken(); if(t) h["X-CSRFToken"]=t; return h;
      }
      function setText(el, text){ if(el) el.textContent=text; }
      function disableBtn(btn, text){ if(btn){ btn.disabled=true; setText(btn, text); } }
      function enableBtn(btn, html){ if(btn){ btn.disabled=false; btn.innerHTML=html; } }

      // --- Email method (reuses forgot-form) ---
      var forgotForm = document.getElementById('forgot-form');
      if(forgotForm){
        forgotForm.addEventListener('submit', async function(e){
          e.preventDefault();
          var emailEl = document.getElementById('email');
          var email = emailEl ? emailEl.value.trim() : '';
          setError('email','');
          if(!email){ setError('email','Email is required'); sweetAlert('warning','Required','Enter your email'); return; }
          if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){ setError('email','Enter a valid email'); sweetAlert('warning','Invalid','Enter a valid email'); return; }
          var btn = forgotForm.querySelector('button[type="submit"]');
          disableBtn(btn,'Sending...');
          try{
            var res = await fetch('/api/auth/forgot-password/', { method:'POST', headers:jsonHeaders(), body:JSON.stringify({email:email}), credentials:'same-origin' });
            var data = await res.json().catch(function(){ return {}; });
            if(res.ok){
              sweetAlert('success','Check your email', data.message || 'Reset link sent.');
              if(data.debug_reset_url) console.log('[DEBUG] reset URL:', data.debug_reset_url);
              forgotForm.reset();
            } else {
              var msg = data.error || data.detail || 'Failed to send reset link';
              if(Array.isArray(msg)) msg=msg[0];
              setError('email', msg);
              sweetAlert('error','Not found', msg);
            }
          }catch(err){ sweetAlert('error','Network error', err.message); }
          finally{ enableBtn(btn, 'Send Reset Link <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 5l7 7-7 7"></path></svg>'); }
        });
      }

      // --- Phone OTP method ---
      var phoneForm = document.getElementById('phone-form');
      if(phoneForm){
        var phoneStep1 = document.getElementById('phone-step-1');
        var phoneStep2 = document.getElementById('phone-step-2');
        var phoneInput = document.getElementById('phone_number');
        var otpBoxes = document.querySelectorAll('.otp-box');
        var otpFull = document.getElementById('otp-full');
        var sendOtpBtn = document.getElementById('btn-send-otp');

        // OTP box auto-focus & collection
        otpBoxes.forEach(function(box, idx){
          box.addEventListener('input', function(){
            this.value = this.value.replace(/\D/g,'').slice(0,1);
            var vals=[]; otpBoxes.forEach(function(b){ vals.push(b.value); });
            if(otpFull) otpFull.value = vals.join('');
            if(this.value && idx < otpBoxes.length-1) otpBoxes[idx+1].focus();
          });
          box.addEventListener('keydown', function(e){
            if(e.key==='Backspace' && !this.value && idx>0){ otpBoxes[idx-1].focus(); }
          });
          box.addEventListener('paste', function(e){
            e.preventDefault();
            var paste = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g,'').slice(0,6);
            paste.split('').forEach(function(ch,i){ if(otpBoxes[i]) otpBoxes[i].value=ch; });
            if(otpFull) otpFull.value = paste;
            var focusIdx = Math.min(paste.length,5); if(otpBoxes[focusIdx]) otpBoxes[focusIdx].focus();
          });
        });

        sendOtpBtn && sendOtpBtn.addEventListener('click', async function(){
          setError('phone_number','');
          var phone = phoneInput ? phoneInput.value.trim() : '';
          var digits = phone.replace(/\D/g,'');
          if(!phone){ setError('phone_number','Phone number is required'); return; }
          if(digits.length<9){ setError('phone_number','Enter a valid phone number'); return; }
          var orig = sendOtpBtn.innerHTML; disableBtn(sendOtpBtn,'Sending...');
          try{
            var res = await fetch('/api/auth/forgot-password/phone/send/', { method:'POST', headers:jsonHeaders(), body:JSON.stringify({phone_number:phone}), credentials:'same-origin' });
            var data = await res.json().catch(function(){ return {}; });
            if(res.ok){
              sweetAlert('success','Code sent', data.message || 'A 6-digit code has been sent.');
              if(data.debug_otp){ console.log('[DEBUG] OTP:', data.debug_otp); sweetAlert('info','Debug OTP', 'Your test code is: ' + data.debug_otp); }
              phoneStep1.classList.add('hidden-step'); phoneStep2.classList.remove('hidden-step');
              setTimeout(function(){ if(otpBoxes[0]) otpBoxes[0].focus(); }, 100);
            } else {
              var msg = data.error || data.detail || 'Failed to send code';
              setError('phone_number', msg);
              sweetAlert('error','Failed', msg);
            }
          }catch(err){ sweetAlert('error','Network error', err.message); }
          finally{ enableBtn(sendOtpBtn, orig); }
        });

        phoneForm.addEventListener('submit', async function(e){
          e.preventDefault();
          setError('otp',''); setError('new_password_phone',''); setError('confirm_password_phone','');
          var phone = phoneInput ? phoneInput.value.trim() : '';
          var otp = otpFull ? otpFull.value : '';
          var newPw = document.getElementById('new_password_phone').value;
          var confirmPw = document.getElementById('confirm_password_phone').value;
          var valid=true;
          if(!phone){ setError('phone_number','Phone number is required'); valid=false; }
          if(!otp || otp.length!==6){ setError('otp','Enter the 6-digit code'); valid=false; }
          if(!newPw){ setError('new_password_phone','New password is required'); valid=false; }
          else if(newPw.length<8){ setError('new_password_phone','At least 8 characters'); valid=false; }
          if(newPw!==confirmPw){ setError('confirm_password_phone','Passwords do not match'); valid=false; }
          if(!valid){ sweetAlert('warning','Validation','Please fix highlighted fields'); return; }
          var btn = phoneForm.querySelector('#phone-step-2 button[type="submit"]');
          disableBtn(btn,'Resetting...');
          try{
            var res = await fetch('/api/auth/forgot-password/phone/verify/', { method:'POST', headers:jsonHeaders(), body:JSON.stringify({phone_number:phone, otp:otp, new_password:newPw, confirm_password:confirmPw}), credentials:'same-origin' });
            var data = await res.json().catch(function(){ return {}; });
            if(res.ok){
              sweetAlert('success','Password reset', data.message || 'Password reset successfully');
              setTimeout(function(){ window.location.href='/login/'; }, 1500);
            } else {
              var msg = data.error || data.detail || 'Failed';
              if(msg.toLowerCase().indexOf('otp')!==-1 || msg.toLowerCase().indexOf('code')!==-1){ setError('otp',msg); }
              else if(msg.toLowerCase().indexOf('match')!==-1){ setError('confirm_password_phone',msg); }
              else { setError('new_password_phone',msg); }
              sweetAlert('error','Failed ('+res.status+')', msg);
            }
          }catch(err){ sweetAlert('error','Network error', err.message); }
          finally{ enableBtn(btn, 'Reset Password <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 5l7 7-7 7"></path></svg>'); }
        });
      }

      // --- Security questions method ---
      var securityForm = document.getElementById('security-form');
      if(securityForm){
        var sqStep1 = document.getElementById('security-step-1');
        var sqStep2 = document.getElementById('security-step-2');
        var verifySecurityBtn = document.getElementById('btn-verify-security');
        var sqUserId = document.getElementById('sq-user-id');
        var sqResetToken = document.getElementById('sq-reset-token');

        verifySecurityBtn && verifySecurityBtn.addEventListener('click', async function(){
          ['first_name','last_name','sq_email'].forEach(function(id){ setError(id,''); });
          var first = document.getElementById('sq_first_name').value.trim();
          var last = document.getElementById('sq_last_name').value.trim();
          var email = document.getElementById('sq_email').value.trim().toLowerCase();
          var valid=true;
          if(!first){ setError('first_name','First name is required'); valid=false; }
          if(!last){ setError('last_name','Last name is required'); valid=false; }
          if(!email){ setError('sq_email','Email is required'); valid=false; }
          else if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){ setError('sq_email','Enter a valid email'); valid=false; }
          if(!valid){ sweetAlert('warning','Required','Fill all security fields'); return; }
          var orig = verifySecurityBtn.innerHTML; disableBtn(verifySecurityBtn,'Verifying...');
          try{
            var res = await fetch('/api/auth/forgot-password/security/verify/', { method:'POST', headers:jsonHeaders(), body:JSON.stringify({first_name:first, last_name:last, email:email}), credentials:'same-origin' });
            var data = await res.json().catch(function(){ return {}; });
            if(res.ok){
              sweetAlert('success','Identity verified', data.message || 'You can now set a new password.');
              if(sqUserId) sqUserId.value = data.user_id || '';
              if(sqResetToken) sqResetToken.value = data.reset_token || '';
              sqStep1.classList.add('hidden-step'); sqStep2.classList.remove('hidden-step');
            } else {
              var msg = data.error || data.detail || 'Verification failed';
              setError('sq_email', msg);
              sweetAlert('error','Verification failed', msg);
            }
          }catch(err){ sweetAlert('error','Network error', err.message); }
          finally{ enableBtn(verifySecurityBtn, orig); }
        });

        securityForm.addEventListener('submit', async function(e){
          e.preventDefault();
          setError('new_password_security',''); setError('confirm_password_security','');
          var userId = sqUserId ? sqUserId.value : '';
          var resetToken = sqResetToken ? sqResetToken.value : '';
          var newPw = document.getElementById('new_password_security').value;
          var confirmPw = document.getElementById('confirm_password_security').value;
          var valid=true;
          if(!userId || !resetToken){ sweetAlert('error','Session expired','Please verify again'); return; }
          if(!newPw){ setError('new_password_security','New password is required'); valid=false; }
          else if(newPw.length<8){ setError('new_password_security','At least 8 characters'); valid=false; }
          if(newPw!==confirmPw){ setError('confirm_password_security','Passwords do not match'); valid=false; }
          if(!valid){ sweetAlert('warning','Validation','Please fix highlighted fields'); return; }
          var btn = securityForm.querySelector('#security-step-2 button[type="submit"]');
          disableBtn(btn,'Saving...');
          try{
            var res = await fetch('/api/auth/forgot-password/security/reset/', { method:'POST', headers:jsonHeaders(), body:JSON.stringify({user_id:userId, reset_token:resetToken, new_password:newPw, confirm_password:confirmPw}), credentials:'same-origin' });
            var data = await res.json().catch(function(){ return {}; });
            if(res.ok){
              sweetAlert('success','Password reset', data.message || 'Password reset successfully');
              setTimeout(function(){ window.location.href='/login/'; }, 1500);
            } else {
              var msg = data.error || data.detail || 'Failed';
              if(msg.toLowerCase().indexOf('match')!==-1){ setError('confirm_password_security',msg); }
              else { setError('new_password_security',msg); }
              sweetAlert('error','Failed ('+res.status+')', msg);
            }
          }catch(err){ sweetAlert('error','Network error', err.message); }
          finally{ enableBtn(btn, 'Set New Password <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 5l7 7-7 7"></path></svg>'); }
        });
      }
    })();

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
    attachLiveValidation('phone_number', function(v){ if(!v) return 'Phone is required'; if(/\s/.test(v)) return 'No spaces allowed. Use e.g. 0712345678'; if(!/^0[67]\d{8}$/.test(v)) return 'Start with 07 or 06, 10 digits, e.g. 0712345678'; return ''; });
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
            var isUnverified = msg.toLowerCase().indexOf("not been verified") !== -1 || msg.toLowerCase().indexOf("verification link") !== -1;
            if (isUnverified) {
              setError("email", msg);
              sweetAlert('warning','Account not verified', msg);
            } else {
              if (msg.toLowerCase().indexOf("invalid") !== -1 || msg.toLowerCase().indexOf("credentials") !== -1) { setError("password", msg); }
              sweetAlert('error','Login failed ('+res.status+')', msg);
            }
            console.error("Login failed", res.status, text);
          }
        } catch (err) {
          console.error("Login network error", err);
          sweetAlert('error','Network error', err.message || "Please check server is running (python manage.py runserver)");
        }
      });
    }

    // === Forgot Password Form ===
    var forgotForm = document.getElementById("forgot-form");
    if (forgotForm) {
      var forgotEmailEl = document.getElementById("email");
      if (forgotEmailEl) {
        forgotEmailEl.addEventListener("input", function(){ setError("email",""); clearValidation("email"); });
      }
      forgotForm.addEventListener("submit", async function(e){
        e.preventDefault();
        setError("email","");
        var email = forgotEmailEl ? forgotEmailEl.value.trim() : "";
        var emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!email) { setError("email","Email is required"); sweetAlert('warning','Validation','Please enter your email'); return; }
        if (!emailRe.test(email)) { setError("email","Enter a valid email"); sweetAlert('warning','Validation','Please enter a valid email'); return; }
        var btn = forgotForm.querySelector('button[type="submit"]');
        var origText = btn ? btn.innerHTML : "";
        if(btn){ btn.disabled=true; btn.innerHTML='Sending...'; }
        try{
          var csrfToken = null;
          try{ var m=document.cookie.match(/(?:^|; )csrftoken=([^;]*)/); if(m) csrfToken=decodeURIComponent(m[1]); }catch(e){}
          var headers={"Content-Type":"application/json"};
          if(csrfToken) headers["X-CSRFToken"]=csrfToken;
          var res = await fetch("/api/auth/forgot-password/", { method:"POST", headers:headers, body: JSON.stringify({email: email}), credentials:"same-origin"});
          var text = await res.text();
          var data={}; try{ data=text?JSON.parse(text):{};}catch(e){ data={detail:text.slice(0,300)}; }
          if(res.ok){
            sweetAlert('success','Email sent', data.message || 'If account exists, reset link sent. Check inbox & spam.');
            // Show debug link in console if provided (DEBUG mode)
            if(data.debug_reset_url){ console.log("Reset URL (DEBUG):", data.debug_reset_url); sweetAlert('success','Email sent (DEBUG)', 'Reset link: '+data.debug_reset_url); }
            forgotForm.reset();
            setValid("email");
          } else {
            var msg = data.error || data.detail || data.email || "Failed to send reset link";
            if(Array.isArray(msg)) msg=msg[0];
            if(data.email) setError("email", Array.isArray(data.email)?data.email[0]:data.email);
            else setError("email", msg);
            sweetAlert('error','Failed ('+res.status+')', msg);
          }
        }catch(err){
          console.error("Forgot network error", err);
          sweetAlert('error','Network error', err.message || "Check server is running");
        }finally{
          if(btn){ btn.disabled=false; btn.innerHTML=origText; }
        }
      });
    }

    // === Reset Password Form ===
    var resetForm = document.getElementById("reset-form");
    if (resetForm) {
      var newPwEl = document.getElementById("new_password");
      var confirmPwEl = document.getElementById("confirm_password");
      if(newPwEl) newPwEl.addEventListener("input", function(){ setError("new_password",""); });
      if(confirmPwEl) confirmPwEl.addEventListener("input", function(){ setError("confirm_password",""); });
      // Also live validate confirm matches
      if(newPwEl && confirmPwEl){
        newPwEl.addEventListener("input", function(){
          if(confirmPwEl.value && confirmPwEl.value !== this.value) setError("confirm_password","Passwords do not match"); else if(confirmPwEl.value) setValid("confirm_password");
        });
      }
      resetForm.addEventListener("submit", async function(e){
        e.preventDefault();
        setError("new_password",""); setError("confirm_password","");
        var newPw = newPwEl ? newPwEl.value : "";
        var confirmPw = confirmPwEl ? confirmPwEl.value : "";
        var valid=true;
        if(!newPw){ setError("new_password","New password is required"); valid=false; }
        else if(newPw.length<8){ setError("new_password","At least 8 characters"); valid=false; }
        if(!confirmPw){ setError("confirm_password","Please confirm password"); valid=false; }
        else if(newPw !== confirmPw){ setError("confirm_password","Passwords do not match"); valid=false; }
        if(!valid){ sweetAlert('warning','Validation failed','Please fix highlighted fields'); return; }
        // Parse uid/token from URL: /reset-password/<uid>/<token>/
        var path = window.location.pathname;
        var parts = path.split('/').filter(Boolean);
        // parts = ['reset-password','uid','token']
        var uid = parts.length >=2 ? parts[1] : "";
        var token = parts.length >=3 ? parts[2] : "";
        // token may contain trailing slash trimmed, but PasswordResetTokenGenerator tokens contain hyphens, no slashes
        if(!uid || !token){
          sweetAlert('error','Invalid link','Reset link is invalid. Please request a new one from Forgot Password page.');
          return;
        }
        var btn2 = resetForm.querySelector('button[type="submit"]');
        var orig2 = btn2 ? btn2.innerHTML : "";
        if(btn2){ btn2.disabled=true; btn2.innerHTML='Resetting...'; }
        try{
          var csrfToken2=null;
          try{ var m2=document.cookie.match(/(?:^|; )csrftoken=([^;]*)/); if(m2) csrfToken2=decodeURIComponent(m2[1]); }catch(e){}
          var headers2={"Content-Type":"application/json"};
          if(csrfToken2) headers2["X-CSRFToken"]=csrfToken2;
          var res = await fetch("/api/auth/reset-password/", { method:"POST", headers:headers2, body: JSON.stringify({uid: uid, token: token, new_password: newPw, confirm_password: confirmPw}), credentials:"same-origin"});
          var text = await res.text();
          var data={}; try{ data=text?JSON.parse(text):{};}catch(e){ data={detail:text.slice(0,300)}; }
          if(res.ok){
            sweetAlert('success','Password reset', data.message || 'Password reset successfully! Redirecting to login...');
            resetForm.reset();
            setTimeout(function(){ window.location.href="/login/"; }, 1500);
          } else {
            var msg = data.error || data.detail || "Failed to reset password";
            if(Array.isArray(msg)) msg=msg[0];
            if(msg.toLowerCase().indexOf('match')!==-1) setError("confirm_password", msg);
            else if(msg.toLowerCase().indexOf('password')!==-1) setError("new_password", msg);
            sweetAlert('error','Failed ('+res.status+')', msg);
          }
        }catch(err){
          console.error("Reset network error", err);
          sweetAlert('error','Network error', err.message || "Check server is running");
        }finally{
          if(btn2){ btn2.disabled=false; btn2.innerHTML=orig2; }
        }
      });
    }

    var signupForm = document.getElementById("signup-form");
    if (signupForm) {
      function isValidEmail(email) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email); }
      function isValidPhone(phone) { return /^0[67]\d{8}$/.test(phone) && !/\s/.test(phone); }

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
        else if (!isValidPhone(phone)) { setError("phone_number", "Start with 07 or 06, 10 digits, no spaces (e.g. 0712345678)"); valid = false; }

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
          if (res.status === 201 || (res.ok && data.redirect_url)) {
            var msg = data.message || 'Account created. Please verify your email to continue.';
            if (data.warning) msg += ' (' + data.warning + ')';
            sweetAlert(data.warning ? 'warning' : 'success', data.warning ? 'Account created' : 'Check your email', msg);
            setTimeout(function () { window.location.href = data.redirect_url || '/verify/email/sent/'; }, 1500);
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
            // Kama email tayari ipo na ime-verify: mwelekeze user kwenye Login.
            if (err.toLowerCase().indexOf('already registered') !== -1 && err.toLowerCase().indexOf('log in') !== -1) {
              if (window.Swal && typeof window.Swal.fire === 'function') {
                window.Swal.fire({icon: 'info', title: 'Already registered', text: err, confirmButtonColor: '#0077B6', showCancelButton: true, confirmButtonText: 'Go to Login', cancelButtonText: 'Stay here'}).then(function(r){ if (r.isConfirmed) window.location.href = '/login/'; });
              } else {
                sweetAlert('error','Registration failed ('+res.status+')', err + ' Go to Login page.');
              }
            } else {
              sweetAlert('error','Registration failed ('+res.status+')', err);
            }
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
