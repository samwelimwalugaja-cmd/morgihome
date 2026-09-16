/* Mortgage Application Form - Live AI + Validations (Customer) v4 */
(function(){
  const API_BASE = '/api/';
  function getToken(){ return localStorage.getItem('access'); }
  function authHeaders(){ const t=getToken(); return t? {'Authorization':'Bearer '+t} : {}; }
  function authHeadersJson(){ const t=getToken(); const h={'Content-Type':'application/json'}; if(t) h['Authorization']='Bearer '+t; return h; }

  const form = document.getElementById('mortgageApplyForm');
  if(!form) return;
  const propSel = document.getElementById('maProperty');
  const bankSel = document.getElementById('maBank');
  const bankDetails = document.getElementById('maBankDetails');
  const loanEl = document.getElementById('maLoanAmount');
  const downEl = document.getElementById('maDownPayment');
  const downHint = document.getElementById('maDownHint');
  const periodEl = document.getElementById('maRepaymentPeriod');
  const periodHint = document.getElementById('maPeriodHint');
  const bankMaxInfo = document.getElementById('maBankMaxInfo');
  const empEl = document.getElementById('maEmploymentStatus');
  const docsEl = document.getElementById('maDocuments');
  const fileList = document.getElementById('maFileList');
  const aiCard = document.getElementById('maAiCard');
  const monthlyEl = document.getElementById('maMonthlyInstallment');
  const affordEl = document.getElementById('maAffordabilityScore');
  const affordDesc = document.getElementById('maAffordabilityDesc');
  const affordBar = document.getElementById('maAffordabilityBar');
  const riskEl = document.getElementById('maRiskScore');
  const riskDesc = document.getElementById('maRiskDesc');
  const riskBar = document.getElementById('maRiskBar');
  const dtiEl = document.getElementById('maDtiRatio');
  const dtiBar = document.getElementById('maDtiBar');
  const recEl = document.getElementById('maRecommendation');
  const submitBtn = document.getElementById('maSubmitBtn');
  const wizardSubmit = document.getElementById('maWizardSubmit');
  // New fields
  const maritalEl = document.getElementById('maMaritalStatus');
  const marriedFields = document.getElementById('maMarriedFields');
  const mCertNo = document.getElementById('maMarriageCertNo');
  const mCertFile = document.getElementById('maMarriageCertFile');
  const dobEl = document.getElementById('maDob');
  const nidaEl = document.getElementById('maNidaNumber');
  const dobError = document.getElementById('maDobError');
  const nidaError = document.getElementById('maNidaError');
  const employeeFields = document.getElementById('maEmployeeFields');
  const businessFields = document.getElementById('maBusinessFields');
  const monthlyIncomeEl = document.getElementById('maMonthlyIncome'); // employee gross
  const monthlyExpEmp = document.getElementById('maMonthlyExpensesEmp');
  const annualIncomeEl = document.getElementById('maAnnualIncome');
  const monthlyExpBiz = document.getElementById('maMonthlyExpensesBiz');
  const monthlyHidden = document.getElementById('maMonthlyIncomeHidden');
  const expensesHidden = document.getElementById('maMonthlyExpensesHidden');
  const businessTypeEl = document.getElementById('maBusinessType');
  const businessRegEl = document.getElementById('maBusinessRegNo');
  // property preview
  const previewCard=document.getElementById('maPropertyPreview');
  const previewImg=document.getElementById('maPreviewImage');
  const previewTitle=document.getElementById('maPreviewTitle');
  const previewLoc=document.getElementById('maPreviewLocation');
  const previewPrice=document.getElementById('maPreviewPrice');
  const previewType=document.getElementById('maPreviewType');
  const previewStatus=document.getElementById('maPreviewStatus');
  const previewDesc=document.getElementById('maPreviewDesc');
  const previewSeller=document.getElementById('maPreviewSeller');
  const previewSellerVer=document.getElementById('maPreviewSellerVerified');

  let banksData = [];
  let bankMaxMonths = 0;

  // --- Property preview ---
  async function showPropertyPreview(pid){
    if(!pid){ if(previewCard) previewCard.classList.add('d-none'); return; }
    try{
      const res=await fetch(API_BASE+'properties/'+pid+'/', {headers: authHeadersJson()});
      if(!res.ok) return;
      const p=await res.json();
      if(previewCard){
        previewCard.classList.remove('d-none');
        let img=p.cover_image_url || p.image || (p.gallery && p.gallery.find(g=>g.is_cover)?.image) || (p.gallery && p.gallery[0]?.image) || '';
        if(img && img.startsWith('/')) img=window.location.origin+img;
        if(previewImg) previewImg.src=img||'https://via.placeholder.com/300x180?text=No+Image';
        if(previewTitle) previewTitle.textContent=p.title;
        if(previewLoc) previewLoc.innerHTML='<i class="bi bi-geo-alt me-1"></i> '+p.location;
        if(previewPrice) previewPrice.textContent='TZS '+Number(p.price).toLocaleString();
        if(previewType) previewType.textContent=p.property_type;
        if(previewStatus){ previewStatus.textContent=p.status; previewStatus.className='badge '+(p.status==='available'?'bg-success':'bg-warning text-dark'); }
        if(previewDesc) previewDesc.textContent=(p.description||'').slice(0,120);
        if(previewSeller) previewSeller.textContent=p.seller_name||'-';
        if(previewSellerVer){ if(p.seller_is_verified) {previewSellerVer.textContent='Verified'; previewSellerVer.className='badge bg-success ms-1';} else {previewSellerVer.textContent='Not Verified'; previewSellerVer.className='badge bg-warning text-dark ms-1';} }
        // Auto set loan amount to property price if empty
        if(p.price && loanEl && !loanEl.value){
          loanEl.value = Math.round(parseFloat(p.price));
          updateDownPayment();
        }
      }
    }catch(e){ console.error(e); }
  }
  if(propSel){ propSel.addEventListener('change', function(){ showPropertyPreview(this.value); updateDownPayment(); }); }

  // --- Banks ---
  async function loadProperties(){
    try{
      const res = await fetch(API_BASE+'properties/', {headers: authHeadersJson()});
      if(!res.ok) return;
      const data = await res.json();
      const arr = Array.isArray(data)?data:(data.results||[]);
      propSel.innerHTML = '<option value="">-- Select Property --</option>';
      arr.forEach(p=>{
        const o=document.createElement('option');
        o.value=p.id;
        o.textContent=p.title + ' ('+p.location+' - '+Number(p.price).toLocaleString()+' TZS)';
        propSel.appendChild(o);
      });
      const params=new URLSearchParams(window.location.search);
      const preProp=params.get('property')||params.get('id');
      if(preProp){ propSel.value=preProp; showPropertyPreview(preProp); setTimeout(()=> previewCard?.scrollIntoView({behavior:'smooth',block:'center'}), 400); }
    }catch(e){ console.error(e); }
  }
  async function loadBanks(){
    try{
      const res = await fetch('/api/banks/', {headers: authHeadersJson()});
      if(!res.ok) { if(bankSel) bankSel.innerHTML='<option value="">No banks available (default 12% will be used)</option>'; return; }
      const data = await res.json();
      banksData = Array.isArray(data)?data:(data.results||data);
      if(bankSel){
        bankSel.innerHTML = '<option value="">-- Select Bank --</option>';
        banksData.forEach(b=>{
          const o=document.createElement('option');
          o.value=b.id;
          o.textContent=b.name + ' - ' + (b.interest_rate ? b.interest_rate+'%' : '12%') + ' | Max ' + (b.max_repayment_period ? Math.round(b.max_repayment_period/12)+'y' : '—');
          o.dataset.bank = JSON.stringify(b);
          bankSel.appendChild(o);
        });
        if(banksData.length===1) { bankSel.value=banksData[0].id; showBankDetails(banksData[0]); populatePeriods(banksData[0]); }
      }
    }catch(e){ console.error(e); }
  }
  function showBankDetails(b){
    if(!bankDetails) return;
    if(!b){ bankDetails.classList.add('d-none'); bankDetails.innerHTML=''; return; }
    bankDetails.classList.remove('d-none');
    const maxY = b.max_repayment_period ? Math.round(b.max_repayment_period/12) : '—';
    const maxM = b.max_repayment_period || '—';
    bankDetails.innerHTML = `
      <strong>${b.name}</strong> <span class="badge bg-primary ms-2">${b.interest_rate ? b.interest_rate+'% Interest' : '12% default'}</span>
      <div class="mt-2 row g-2 small">
        <div class="col-6">Interest: <strong>${b.interest_rate ? b.interest_rate+'%' : '12%'}</strong> | Fee: <strong>${b.processing_fee ? b.processing_fee+'%' : '2%'}</strong></div>
        <div class="col-6">Max Period: <strong>${maxM} months (${maxY} years)</strong></div>
        <div class="col-6">Loan Range: <strong>${b.min_loan_amount ? Number(b.min_loan_amount).toLocaleString() : '0'} - ${b.max_loan_amount ? Number(b.max_loan_amount).toLocaleString() : '∞'} TZS</strong></div>
        <div class="col-12">Requirements: <em>${b.bank_requirements || '—'}</em></div>
      </div>`;
    if(bankMaxInfo){
      bankMaxInfo.classList.remove('d-none');
      bankMaxInfo.innerHTML = `<strong>${b.name}</strong> max is <strong>${maxM} months (${maxY} years)</strong> — choose less than this. If you exceed it, you will be warned.`;
    }
  }
  function populatePeriods(b){
    if(!periodEl) return;
    const max = b && b.max_repayment_period ? parseInt(b.max_repayment_period) : 240;
    bankMaxMonths = max;
    const options = [12,24,36,48,60,72,84,96,108,120,180,240,300,360];
    periodEl.innerHTML = '<option value="">-- Select Period --</option>';
    let hasSelected = false;
    options.forEach(v=>{
      if(v <= max){
        const o=document.createElement('option');
        o.value=v;
        o.textContent=v+' months ('+(v/12)+' years)'+(v===max ? ' — Max' : '');
        if(v===Math.min(240,max) && !hasSelected){ o.selected=true; hasSelected=true; }
        periodEl.appendChild(o);
      }
    });
    // Add exact max if not in list
    if(!options.includes(max)){
      const o=document.createElement('option');
      o.value=max;
      o.textContent=max+' months ('+(max/12)+' years) — Max';
      periodEl.appendChild(o);
    }
  }
  loadProperties();
  loadBanks().then(()=>{
    const params = new URLSearchParams(window.location.search);
    const qBank = params.get('bank') || params.get('bank_id');
    if(qBank && bankSel){
      bankSel.value = qBank;
      const sel = banksData.find(x=> String(x.id)===String(qBank));
      if(sel){ showBankDetails(sel); populatePeriods(sel); }
    }
  });
  if(bankSel){
    bankSel.addEventListener('change', function(){
      const sel = banksData.find(x=> String(x.id)===this.value);
      showBankDetails(sel||null);
      if(sel) populatePeriods(sel); else { periodEl.innerHTML='<option value="">-- Select Bank first --</option>'; bankMaxMonths=0; if(bankMaxInfo) bankMaxInfo.classList.add('d-none'); }
      scheduleCalc();
    });
  }
  if(periodEl){
    periodEl.addEventListener('change', function(){
      if(bankMaxMonths && parseInt(this.value) > bankMaxMonths){
        if(window.showToast) showToast('Repayment period exceeds bank max '+bankMaxMonths+' months ('+Math.round(bankMaxMonths/12)+'y). Bank limit is '+bankMaxMonths+' months.','warning');
        this.value = bankMaxMonths;
      }
      scheduleCalc();
    });
  }

  // --- Employment conditional ---
  function toggleEmployment(){
    const v = empEl ? empEl.value : '';
    if(employeeFields) employeeFields.classList.add('d-none');
    if(businessFields) businessFields.classList.add('d-none');
    // clear hidden sync
    if(v==='employed'){
      if(employeeFields) employeeFields.classList.remove('d-none');
      // Business fields hidden
      if(annualIncomeEl) annualIncomeEl.removeAttribute('required');
      if(businessTypeEl) businessTypeEl.removeAttribute('required');
      if(businessRegEl) businessRegEl.removeAttribute('required');
      if(monthlyIncomeEl) monthlyIncomeEl.setAttribute('required','');
      if(monthlyExpEmp) monthlyExpEmp.setAttribute('required','');
    } else if(v==='business_owner' || v==='business' || v==='self_employed'){
      if(businessFields) businessFields.classList.remove('d-none');
      if(monthlyIncomeEl) monthlyIncomeEl.removeAttribute('required');
      if(annualIncomeEl) annualIncomeEl.setAttribute('required','');
      if(businessTypeEl) businessTypeEl.setAttribute('required','');
      if(businessRegEl) businessRegEl.setAttribute('required','');
    } else {
      // for unemployed, hide both? Show generic?
      // No extra required
    }
    syncIncomeHidden();
  }
  if(empEl){ empEl.addEventListener('change', toggleEmployment); }

  function syncIncomeHidden(){
    const v = empEl ? empEl.value : '';
    let inc = 0, exp = 0;
    if(v==='business_owner' || v==='business' || v==='self_employed'){
      const annual = parseFloat(annualIncomeEl.value) || 0;
      inc = annual ? annual/12 : 0;
      exp = parseFloat(monthlyExpBiz.value) || 0;
    } else {
      inc = parseFloat(monthlyIncomeEl.value) || 0;
      exp = parseFloat(monthlyExpEmp.value) || 0;
      // fallback to old generic if new fields not used
      const genericInc = document.getElementById('maMonthlyIncome');
      const genericExp = document.getElementById('maMonthlyExpenses');
      if(!inc && genericInc) inc = parseFloat(genericInc.value)||0;
      if(!exp && genericExp) exp = parseFloat(genericExp.value)||0;
    }
    if(monthlyHidden) monthlyHidden.value = inc ? Math.round(inc) : '';
    if(expensesHidden) expensesHidden.value = exp ? Math.round(exp) : '';
  }
  // Bind sync
  [monthlyIncomeEl, monthlyExpEmp, annualIncomeEl, monthlyExpBiz].forEach(el=>{ if(el){ el.addEventListener('input', ()=>{ syncIncomeHidden(); scheduleCalc(); }); el.addEventListener('change', ()=>{ syncIncomeHidden(); scheduleCalc(); }); }});

  // --- Marital conditional ---
  function toggleMarital(){
    const v = maritalEl ? maritalEl.value : '';
    if(marriedFields){
      if(v==='married'){ marriedFields.classList.remove('d-none'); if(mCertNo) mCertNo.setAttribute('required',''); if(mCertFile) mCertFile.setAttribute('required',''); }
      else { marriedFields.classList.add('d-none'); if(mCertNo) mCertNo.removeAttribute('required'); if(mCertFile) mCertFile.removeAttribute('required'); }
    }
  }
  if(maritalEl){ maritalEl.addEventListener('change', toggleMarital); }

  // --- NIDA + DOB validation + age 18-57 ---
  function showErr(el, msg){ if(!el) return; const err = el.nextElementSibling && el.nextElementSibling.id && el.nextElementSibling.id.includes('Error') ? el.nextElementSibling : null; const target = el.id==='maDob' ? dobError : nidaError; if(target){ if(msg){ target.textContent=msg; target.classList.remove('d-none'); } else { target.classList.add('d-none'); } } el.setCustomValidity(msg||''); }
  function validateDobNida(){
    const nida = nidaEl ? nidaEl.value.trim() : '';
    const dobStr = dobEl ? dobEl.value : '';
    let dob = null;
    if(dobStr){
      var parts=dobStr.split('-');
      if(parts.length===3){ dob=new Date(parseInt(parts[0]), parseInt(parts[1])-1, parseInt(parts[2])); if(isNaN(dob.getTime())) dob=null; }
      else { dob = new Date(dobStr); if(isNaN(dob.getTime())) dob=null; }
    }
    // NIDA format 20 digits
    if(nida && !/^\d{20}$/.test(nida)){
      showErr(nidaEl, 'NIDA must be 20 digits (you have '+nida.length+'). First 8 = YYYYMMDD of birth.');
    } else if(nida && dob){
      try{
        var nidaYMD = nida.substr(0,8);
        var dobY = String(dob.getFullYear()).padStart(4,'0'), dobM = String(dob.getMonth()+1).padStart(2,'0'), dobD = String(dob.getDate()).padStart(2,'0');
        var dobYMD = dobY+dobM+dobD;
        if(nidaYMD !== dobYMD){
          showErr(nidaEl, 'NIDA first 8 digits ('+nidaYMD+') must equal DOB YYYYMMDD ('+dobYMD+'). Example DOB 1995-06-20 → NIDA 19950620xxxxxxxxxxxx');
        } else {
          showErr(nidaEl, '');
        }
      }catch(e){ showErr(nidaEl, 'Invalid NIDA date'); }
    } else {
      showErr(nidaEl, '');
    }
    // Age 18-57
    if(dob){
      const today = new Date();
      let age = today.getFullYear() - dob.getFullYear();
      const m = today.getMonth() - dob.getMonth();
      if(m<0 || (m===0 && today.getDate() < dob.getDate())) age--;
      if(dob.getFullYear() === today.getFullYear()){
        showErr(dobEl, 'Birth date cannot be this year.');
      } else if(age < 18){
        showErr(dobEl, 'Age '+age+' — must be at least 18 years.');
      } else if(age > 57){
        showErr(dobEl, 'Age '+age+' — maximum is 57 years.');
      } else {
        showErr(dobEl, '');
      }
    } else {
      showErr(dobEl, '');
    }
  }
  if(dobEl) dobEl.addEventListener('change', validateDobNida);
  if(nidaEl) nidaEl.addEventListener('input', validateDobNida);
  if(dobEl) dobEl.addEventListener('input', validateDobNida);

  // --- Down payment auto 10% — field shows actual money, hint shows 10%
  function updateDownPayment(){
    if(!loanEl || !downEl) return;
    const loan = parseFloat(loanEl.value) || 0;
    if(loan){
      const down = Math.round(loan * 0.10);
      downEl.value = down;
      if(downHint) downHint.textContent = 'TZS '+down.toLocaleString()+' (10% of TZS '+loan.toLocaleString()+')';
    } else {
      downEl.value='';
      if(downHint) downHint.textContent='10% of loan amount — will calculate as you type';
    }
    scheduleCalc();
  }
  if(loanEl){ loanEl.addEventListener('input', updateDownPayment); loanEl.addEventListener('change', updateDownPayment); }

  // --- Business reg validation ---
  function validateBusinessReg(){
    if(!businessRegEl) return;
    const v = businessRegEl.value.trim();
    if(!v) return;
    const brela = /^BRL-\d{4}-\d{6}$/;
    const lic = /^LIC-[A-Z]{2,4}-\d{4}-\d{6}$/;
    if(!brela.test(v) && !lic.test(v)){
      businessRegEl.setCustomValidity('Use BRL-2024-001234 or LIC-DSM-2024-005678');
    } else {
      businessRegEl.setCustomValidity('');
    }
  }
  if(businessRegEl){ businessRegEl.addEventListener('input', validateBusinessReg); businessRegEl.addEventListener('change', validateBusinessReg); }

  // --- Wizard ---
  let currentStep=1;
  const totalSteps=5;
  function isStepComplete(n){
    if(n===1) return !!propSel.value;
    if(n===2) return !!bankSel.value;
    if(n===3){
      const loanOk = !!loanEl.value && !!downEl.value && !!periodEl.value;
      if(!loanOk) return false;
      const loan = parseFloat(loanEl.value)||0;
      const down = parseFloat(downEl.value)||0;
      const expected = Math.round(loan*0.10);
      // allow small diff
      if(down!==expected) return false;
      if(bankMaxMonths && parseInt(periodEl.value) > bankMaxMonths) return false;
      return true;
    }
    if(n===4){
      const emp = empEl.value;
      if(!emp) return false;
      // Check conditional required
      if(emp==='employed'){
        if(!monthlyIncomeEl.value || !monthlyExpEmp.value) return false;
      } else if(emp==='business_owner' || emp==='business' || emp==='self_employed'){
        if(!annualIncomeEl.value || !businessTypeEl.value || !businessRegEl.value) return false;
        // Validate reg format
        const v=businessRegEl.value.trim();
        if(v && !/^BRL-\d{4}-\d{6}$/.test(v) && !/^LIC-[A-Z]{2,4}-\d{4}-\d{6}$/.test(v)) return false;
      } else {
        // unemployed still needs income? But minimal
        if(!monthlyIncomeEl.value && !annualIncomeEl.value) return false;
      }
      // Marital + NIDA + DOB
      if(!maritalEl.value) return false;
      if(maritalEl.value==='married' && (!mCertNo.value || !mCertFile.files.length)) return false;
      if(!dobEl.value || !nidaEl.value) return false;
      // Check validity
      if(dobEl.validationMessage || nidaEl.validationMessage || businessRegEl.validationMessage) return false;
      // Age check again
      const today=new Date(); const dob=new Date(dobEl.value);
      let age=today.getFullYear()-dob.getFullYear(); const m=today.getMonth()-dob.getMonth();
      if(m<0 || (m===0 && today.getDate()<dob.getDate())) age--;
      if(age<18 || age>57) return false;
      // NIDA match
      const nida=nidaEl.value.trim();
      if(!/^\d{20}$/.test(nida)) return false;
      const y=nida.substr(0,4), mo=nida.substr(4,2), d=nida.substr(6,2);
      const nidaDate=new Date(parseInt(y),parseInt(mo)-1,parseInt(d));
      if(nidaDate.toISOString().slice(0,10)!==dob.toISOString().slice(0,10)) return false;
      return true;
    }
    if(n===5) return true;
    return false;
  }
  function updateStepper(){
    for(let i=1;i<=totalSteps;i++){
      const el=document.getElementById('step'+i);
      if(!el) continue;
      const done=isStepComplete(i);
      const isCurrent=i===currentStep;
      const isPast=i<currentStep;
      if(done){
        el.style.background='#1B7A43'; el.style.color='#fff'; el.style.borderColor='#1B7A43'; el.innerHTML='✓';
      } else if(isCurrent){
        el.style.background='#FFC107'; el.style.color='#000'; el.style.borderColor='#FFC107'; el.textContent=i;
      } else if(isPast){
        el.style.background='#FFC107'; el.style.color='#000'; el.style.borderColor='#FFC107'; el.textContent=i;
      } else {
        el.style.background='#e2e8f0'; el.style.color='#64748b'; el.style.borderColor='#e2e8f0'; el.textContent=i;
      }
      if(isCurrent){ el.style.boxShadow='0 0 0 3px rgba(0,119,182,.2)'; } else el.style.boxShadow='none';
    }
    const progress=document.getElementById('maProgressLine');
    if(progress){
      const completed=[1,2,3,4,5].filter(n=> isStepComplete(n)).length;
      const pct=(completed/totalSteps)*100;
      const curPct=((currentStep-1)/ (totalSteps-1))*100;
      progress.style.width=Math.max(pct*0.5, curPct*0.5)+'%';
      if(completed===totalSteps) progress.style.background='#1B7A43';
      else progress.style.background='#0077B6';
    }
  }
  function showStep(n){
    for(let i=1;i<=totalSteps;i++){
      const el=document.getElementById('wizardStep'+i);
      if(el) el.classList.toggle('d-none', i!==n);
    }
    currentStep=n;
    toggleEmployment(); toggleMarital();
    updateStepper();
    window.scrollTo({top:0,behavior:'smooth'});
  }
  document.querySelectorAll('.wizard-next').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const next=parseInt(btn.dataset.next);
      if(!isStepComplete(currentStep)){
        updateStepper();
        if(window.showToast) showToast('Please complete step '+currentStep+' correctly before next','warning');
        const el=document.getElementById('step'+currentStep);
        if(el){ el.style.background='#FFC107'; el.style.color='#000'; }
        // Show specific errors
        if(currentStep===3){
          if(bankMaxMonths && parseInt(periodEl.value)>bankMaxMonths){
            showToast('Repayment period exceeds bank max '+bankMaxMonths+' months','warning');
          }
          if(!downEl.value) showToast('Down payment auto 10% required','warning');
        }
        if(currentStep===4){
          validateDobNida();
          validateBusinessReg();
        }
        return;
      }
      showStep(next);
    });
  });
  document.querySelectorAll('.wizard-prev').forEach(btn=>{
    btn.addEventListener('click', ()=> showStep(parseInt(btn.dataset.prev)));
  });
  [propSel, bankSel, loanEl, downEl, periodEl, empEl, maritalEl, dobEl, nidaEl, monthlyIncomeEl, monthlyExpEmp, annualIncomeEl, monthlyExpBiz, businessTypeEl, businessRegEl, mCertNo].forEach(el=>{
    if(el){ el.addEventListener('input', updateStepper); el.addEventListener('change', updateStepper); }
  });
  showStep(1);
  if(wizardSubmit){ wizardSubmit.addEventListener('click', ()=> form.requestSubmit()); }

  if(docsEl){
    docsEl.addEventListener('change', ()=>{
      const files = docsEl.files;
      if(!files.length){ fileList.textContent=''; return; }
      let html = '<strong>Selected files:</strong><ul class="mb-0 ps-3">';
      for(let f of files){ html += `<li>${f.name} (${(f.size/1024).toFixed(1)} KB) - ${f.type||'unknown'}</li>`; }
      html += '</ul>';
      fileList.innerHTML = html;
    });
  }

  // --- Live AI ---
  let calcTimeout=null;
  function scheduleCalc(){
    clearTimeout(calcTimeout);
    calcTimeout=setTimeout(calculateLive, 400);
  }
  // Listen to many
  [loanEl, downEl, periodEl, monthlyIncomeEl, monthlyExpEmp, annualIncomeEl, monthlyExpBiz, empEl, bankSel].forEach(el=>{
    if(el){ el.addEventListener('input', scheduleCalc); el.addEventListener('change', scheduleCalc); }
  });

  function formatTZS(n){ return Number(n).toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2}) + ' TZS'; }

  async function calculateLive(){
    // Need bank selected before calc (as per requirement 5)
    if(!bankSel || !bankSel.value){
      if(aiCard) aiCard.classList.add('d-none');
      return;
    }
    syncIncomeHidden();
    const loan = parseFloat(loanEl.value) || 0;
    const incomeHidden = parseFloat(monthlyHidden.value) || 0;
    const expHidden = parseFloat(expensesHidden.value) || 0;
    const income = incomeHidden;
    const expenses = expHidden;
    const months = parseInt(periodEl.value) || 0;
    const emp = empEl.value || '';
    const bankId = bankSel.value;

    if(!loan || !months || !income){
      aiCard.classList.add('d-none');
      syncSubmitDisabled(true);
      return;
    }

    // Backend
    try{
      const res = await fetch(API_BASE+'mortgages/calculate/', {
        method:'POST',
        headers: authHeadersJson(),
        body: JSON.stringify({
          loan_amount: loan,
          down_payment: parseFloat(downEl.value)||0,
          repayment_period: months,
          monthly_income: income,
          monthly_expenses: expenses,
          employment_status: emp,
          bank: bankId ? parseInt(bankId) : null,
          bank_id: bankId ? parseInt(bankId) : null
        })
      });
      if(res.ok){
        const data = await res.json();
        renderAi(data);
        return;
      }
    }catch(e){}

    let annualRate=0.12;
    if(bankId){
      const sel = banksData.find(x=> String(x.id)===String(bankId));
      if(sel && sel.interest_rate) annualRate = parseFloat(sel.interest_rate)/100.0;
    }
    const monthlyRate=annualRate/12;
    let monthlyInstallment=0;
    if(monthlyRate===0) monthlyInstallment=loan/months;
    else monthlyInstallment= loan * (monthlyRate*Math.pow(1+monthlyRate, months)) / (Math.pow(1+monthlyRate, months)-1);
    const disposable=income-expenses;
    const dti=(monthlyInstallment/income)*100;
    let afford=0;
    if(disposable>0 && monthlyInstallment>0){ afford=Math.min(100, (disposable/monthlyInstallment)*100); }
    let risk=100-afford;
    const empFactors={employed:-10,self_employed:0,business:5,business_owner:5,unemployed:30};
    risk+=(empFactors[emp]||0);
    risk=Math.max(0,Math.min(100,risk));
    renderAi({ monthly_installment: monthlyInstallment, affordability_score: afford, risk_score: risk, dti_ratio: dti, annual_rate: annualRate*100 });
  }

  function syncSubmitDisabled(disable){
    if(submitBtn) submitBtn.disabled = disable;
    if(wizardSubmit) wizardSubmit.disabled = disable;
    if(disable){
      if(submitBtn) submitBtn.style.opacity='0.5';
      if(wizardSubmit) wizardSubmit.style.opacity='0.5';
    } else {
      if(submitBtn) submitBtn.style.opacity='1';
      if(wizardSubmit) wizardSubmit.style.opacity='1';
    }
  }

  function renderAi(data){
    aiCard.classList.remove('d-none');
    const monthly = parseFloat(data.monthly_installment)||0;
    const afford = parseFloat(data.affordability_score)||0;
    const risk = parseFloat(data.risk_score)||0;
    const dti = parseFloat(data.dti_ratio)||0;
    const rate = parseFloat(data.annual_rate) || (banksData.find(x=> String(x.id)===String(bankSel.value))?.interest_rate || 12);

    monthlyEl.textContent = formatTZS(monthly) + ' @ '+Number(rate).toFixed(2)+'%';
    // Also show total interest?
    const months = parseInt(periodEl.value)||0;
    const total = monthly * months;
    const interestTotal = total - (parseFloat(loanEl.value)||0);
    monthlyEl.innerHTML = formatTZS(monthly) + ' <small class="text-muted" style="font-size:11px;">@ '+Number(rate).toFixed(2)+'% | Total: '+formatTZS(total)+' | Interest: '+formatTZS(interestTotal)+'</small>';

    affordEl.textContent = afford.toFixed(1)+'%';
    riskEl.textContent = risk.toFixed(1)+'%';
    dtiEl.textContent = dti.toFixed(1)+'%';

    affordBar.style.width = Math.min(100,afford)+'%';
    affordEl.className='ai-metric-value';
    affordBar.className='progress-bar';
    if(afford>=80){ affordEl.classList.add('afford-green'); affordBar.classList.add('bg-success'); affordDesc.textContent='Safe'; affordDesc.className='text-success'; }
    else if(afford>=40){ affordEl.classList.add('afford-yellow'); affordBar.classList.add('bg-warning'); affordDesc.textContent='Caution'; affordDesc.className='text-warning'; }
    else { affordEl.classList.add('afford-red'); affordBar.classList.add('bg-danger'); affordDesc.textContent='Not affordable'; affordDesc.className='text-danger'; }

    riskBar.style.width = Math.min(100,risk)+'%';
    riskEl.className='ai-metric-value';
    riskBar.className='progress-bar';
    if(risk<40){ riskEl.classList.add('risk-green'); riskBar.classList.add('bg-success'); riskDesc.textContent='Low risk'; riskDesc.className='text-success'; }
    else if(risk<=70){ riskEl.classList.add('risk-yellow'); riskBar.classList.add('bg-warning'); riskDesc.textContent='Medium risk'; riskDesc.className='text-warning'; }
    else { riskEl.classList.add('risk-red'); riskBar.classList.add('bg-danger'); riskDesc.textContent='High risk'; riskDesc.className='text-danger'; }

    dtiBar.style.width = Math.min(100,dti)+'%';
    dtiBar.className='progress-bar';
    if(dti<=30){ dtiBar.classList.add('bg-success'); dtiEl.style.color='#1B7A43'; }
    else if(dti<=40){ dtiBar.classList.add('bg-warning'); dtiEl.style.color='#f59e0b'; }
    else if(dti<=50){ dtiBar.classList.add('bg-danger'); dtiEl.style.color='#dc3545'; }
    else { dtiBar.classList.add('bg-danger'); dtiEl.style.color='#7f1d1d'; dtiBar.style.background='#7f1d1d'; }

    recEl.style.display='block';
    let disable=false;
    let html='';
    if(dti>50){
      recEl.className='alert alert-danger mt-4 mb-0';
      html='<i class="bi bi-x-octagon me-2"></i><strong>Very High Risk (DTI '+dti.toFixed(1)+'%)</strong> — Not allowed to apply. DTI >50% is very high risk. Reduce loan or increase income.<br><small>DTI must be ≤40% to apply. Yours is '+dti.toFixed(1)+'%. Reduce loan or increase income.</small>';
      disable=true;
    } else if(dti>40){
      recEl.className='alert alert-danger mt-4 mb-0';
      html='<i class="bi bi-exclamation-triangle me-2"></i><strong>High Risk (DTI '+dti.toFixed(1)+'%)</strong> — Not allowed to apply. DTI 41-50% high risk. Threshold is ≤40%.<br><small>Threshold is ≤40% (Very Good ≤30, Good 31-40). Yours '+dti.toFixed(1)+'%. Reduce amount or extend period.</small>';
      disable=true;
    } else if(dti>30){
      recEl.className='alert alert-warning mt-4 mb-0';
      html='<i class="bi bi-check-circle me-2"></i><strong>Good/Acceptable (DTI '+dti.toFixed(1)+'%)</strong> — You can apply. DTI 31-40 good/acceptable.<br><small>You can proceed. DTI within acceptable range.</small>';
      disable=false;
    } else {
      recEl.className='alert alert-success mt-4 mb-0';
      html='<i class="bi bi-check-circle me-2"></i><strong>Very Good (DTI '+dti.toFixed(1)+'%)</strong> — You can apply, DTI ≤30 very good.<br><small>You can proceed. Excellent affordability.</small>';
      disable=false;
    }
    // Also check afford/risk
    if(afford<40 || risk>70){
      // add warning but not necessarily disable if DTI ok? But per spec, error then disable
      html+='<div class="mt-2 small"><i class="bi bi-info-circle me-1"></i> Affordability '+afford.toFixed(1)+'% / Risk '+risk.toFixed(1)+'% — '+(afford<40?'Affordability low':'Risk high')+'. Consider adjusting loan.</div>';
      if(afford<30 || risk>80) disable=true;
    }
    recEl.innerHTML=html + `<div class="mt-2 small">Interest Rate: <strong>${Number(rate).toFixed(2)}%</strong> | Monthly: <strong>${formatTZS(monthly)}</strong> | Total Payment: <strong>${formatTZS(total)}</strong></div>`;
    syncSubmitDisabled(disable);
    // Store for download
    window._lastAiData = { monthly, total, rate, afford, risk, dti };
  }

  // Download form after good AI
  function downloadFormAsPdf(){
    const data = window._lastAiData;
    if(!data) return;
    // Simple print
    const w = window.open('', '_blank');
    w.document.write(`<html><head><title>Mortgage Form - ${loanEl.value}</title><style>body{font-family:Inter,sans-serif; padding:30px; color:#0A2B4E} h1{color:#0077B6} table{width:100%; border-collapse:collapse} td,th{border:1px solid #e2e8f0; padding:8px; font-size:13px} th{background:#f1f5f9; text-align:left}</style></head><body><h1>MorgiHome Mortgage Application</h1><p>Property: ${propSel.options[propSel.selectedIndex]?.text||''}</p><p>Bank: ${bankSel.options[bankSel.selectedIndex]?.text||''}</p><table><tr><th>Loan Amount</th><td>TZS ${Number(loanEl.value||0).toLocaleString()}</td></tr><tr><th>Down Payment (10%)</th><td>TZS ${Number(downEl.value||0).toLocaleString()}</td></tr><tr><th>Period</th><td>${periodEl.value} months</td></tr><tr><th>Interest</th><td>${data.rate}%</td></tr><tr><th>Monthly Payment</th><td>${formatTZS(data.monthly)}</td></tr><tr><th>Total Payment</th><td>${formatTZS(data.total)}</td></tr><tr><th>DTI</th><td>${data.dti.toFixed(1)}% (${data.dti<=30?'Very Good':data.dti<=40?'Good':data.dti<=50?'High Risk':'Very High'})</td></tr><tr><th>Affordability</th><td>${data.afford.toFixed(1)}%</td></tr><tr><th>Risk</th><td>${data.risk.toFixed(1)}%</td></tr></table><p style="margin-top:20px; font-size:11px; color:#64748b;">Generated by MorgiHome • ${new Date().toLocaleString()}</p></body></html>`);
    w.document.close();
    w.print();
  }
  // Add download button if AI good
  const aiHeader = aiCard ? aiCard.querySelector('.card-header') : null;
  if(aiHeader){
    const btn = document.createElement('button');
    btn.textContent='Download Form';
    btn.className='btn btn-sm btn-outline-primary';
    btn.style.fontSize='11px';
    btn.onclick = downloadFormAsPdf;
    aiHeader.appendChild(btn);
  }

  // --- Submit ---
  form.addEventListener('submit', async (e)=>{
    e.preventDefault();
    syncIncomeHidden();
    validateDobNida();
    validateBusinessReg();
    if(!propSel.value){ showToast('Please select a property','warning'); propSel.focus(); return; }
    if(!bankSel.value){ showToast('Please select a bank first — required before loan details','warning'); bankSel.focus(); return; }
    if(!isStepComplete(3)){ showToast('Complete Loan Details — down payment auto 10% and period within bank max','warning'); return; }
    if(!isStepComplete(4)){ showToast('Complete Financial & Personal details — check marital, NIDA, DOB (18-57), business fields','warning'); return; }
    // Final DTI check
    const dti = parseFloat(window._lastAiData?.dti || 0);
    if(dti>40){
      showToast('DTI '+dti.toFixed(1)+'% exceeds 40% threshold — not allowed to apply. Reduce loan or extend period.','error');
      recEl.scrollIntoView({behavior:'smooth'});
      return;
    }
    // Check disable
    if(submitBtn.disabled){
      showToast('Form has errors — correct AI warnings before submit','error');
      return;
    }
    submitBtn.disabled=true;
    submitBtn.innerHTML='<span class="spinner-border spinner-border-sm me-2"></span> Submitting...';
    try{
      const fd=new FormData();
      fd.append('property', propSel.value);
      fd.append('bank', bankSel.value);
      fd.append('loan_amount', loanEl.value);
      fd.append('down_payment', downEl.value);
      fd.append('repayment_period', periodEl.value);
      fd.append('monthly_income', monthlyHidden.value || 0);
      fd.append('monthly_expenses', expensesHidden.value || 0);
      fd.append('employment_status', empEl.value);
      // New fields
      if(maritalEl.value) fd.append('marital_status', maritalEl.value);
      if(dobEl.value) fd.append('dob', dobEl.value);
      if(nidaEl.value) fd.append('nida_number', nidaEl.value);
      if(mCertNo.value) fd.append('marriage_certificate_number', mCertNo.value);
      if(mCertFile.files.length) fd.append('marriage_certificate_file', mCertFile.files[0]);
      if(businessTypeEl.value) fd.append('business_type', businessTypeEl.value);
      if(businessRegEl.value) fd.append('business_registration_number', businessRegEl.value);
      const anonAnnual = document.getElementById('maAnnualIncome');
      if(anonAnnual && anonAnnual.value) fd.append('annual_income', anonAnnual.value);
      // Also pass business_name, employer etc in draft_data via extra? For now append as well
      const empName = document.getElementById('maEmployerName');
      if(empName && empName.value) fd.append('employer_name', empName.value);
      const bizName = document.getElementById('maBusinessName');
      if(bizName && bizName.value) fd.append('business_name', bizName.value);
      if(docsEl.files.length){ for(let f of docsEl.files){ fd.append('documents', f); } }
      const headers=authHeaders();
      const res=await fetch(API_BASE+'mortgages/', { method:'POST', headers: headers, body: fd });
      const data=await res.json();
      if(res.ok || res.status===201){
        showToast('Application submitted successfully! Status: pending','success');
        setTimeout(()=>{ window.location.href='/dashboard/'; }, 1200);
      } else {
        showToast(JSON.stringify(data).slice(0,400),'error','Failed');
      }
    }catch(err){
      showToast(err.message||'Network error','error');
    } finally {
      submitBtn.disabled=false;
      submitBtn.innerHTML='<i class="bi bi-send me-1"></i> Submit Application';
      syncSubmitDisabled(window._lastAiData && window._lastAiData.dti>40);
    }
  });

})();
