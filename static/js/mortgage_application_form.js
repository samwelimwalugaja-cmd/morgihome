/* Mortgage Application Form - Live AI Affordability (Customer) */
(function(){
  const API_BASE = '/api/';
  function getToken(){ return localStorage.getItem('access'); }
  function authHeaders(){ const t=getToken(); return t? {'Authorization':'Bearer '+t} : {}; }
  function authHeadersJson(){ const t=getToken(); const h={'Content-Type':'application/json'}; if(t) h['Authorization']='Bearer '+t; return h; }

  // Elements
  const form = document.getElementById('mortgageApplyForm');
  if(!form) return;
  const propSel = document.getElementById('maProperty');
  const bankSel = document.getElementById('maBank');
  const bankDetails = document.getElementById('maBankDetails');
  const loanEl = document.getElementById('maLoanAmount');
  const downEl = document.getElementById('maDownPayment');
  const periodEl = document.getElementById('maRepaymentPeriod');
  const incomeEl = document.getElementById('maMonthlyIncome');
  const expensesEl = document.getElementById('maMonthlyExpenses');
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
  let banksData = [];

  // Property preview helpers - professional
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
      }
    }catch(e){ console.error(e); }
  }
  if(propSel){
    propSel.addEventListener('change', function(){ showPropertyPreview(this.value); });
  }

  // Load properties
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
      // Pre-fill from ?property= param (when coming from detail page View Details -> Apply Mortgage)
      const params=new URLSearchParams(window.location.search);
      const preProp=params.get('property')||params.get('id');
      if(preProp){
        propSel.value=preProp;
        showPropertyPreview(preProp);
        // Scroll to form
        setTimeout(()=> previewCard?.scrollIntoView({behavior:'smooth',block:'center'}), 400);
      }
    }catch(e){ console.error(e); }
  }
  async function loadBanks(){
    try{
      const res = await fetch('/api/banks/', {headers: authHeadersJson()});
      if(!res.ok) {
        if(bankSel) bankSel.innerHTML='<option value="">No banks available (default 12% will be used)</option>';
        return;
      }
      const data = await res.json();
      banksData = Array.isArray(data)?data:(data.results||data);
      if(bankSel){
        bankSel.innerHTML = '<option value="">-- Select Bank --</option>';
        banksData.forEach(b=>{
          const o=document.createElement('option');
          o.value=b.id;
          o.textContent=b.name + ' - ' + (b.interest_rate ? b.interest_rate+'%' : '12%') + ' | Fee: ' + (b.processing_fee ? Number(b.processing_fee).toLocaleString()+' TZS' : 'N/A');
          o.dataset.bank = JSON.stringify(b);
          bankSel.appendChild(o);
        });
        // auto-select if only one
        if(banksData.length===1) { bankSel.value=banksData[0].id; showBankDetails(banksData[0]); }
      }
    }catch(e){ console.error(e); }
  }
  function showBankDetails(b){
    if(!bankDetails) return;
    if(!b){ bankDetails.classList.add('d-none'); bankDetails.innerHTML=''; return; }
    bankDetails.classList.remove('d-none');
    bankDetails.innerHTML = `
      <strong>${b.name}</strong> <span class="badge bg-primary ms-2">${b.interest_rate ? b.interest_rate+'% Interest' : '12% default'}</span>
      <div class="mt-2 row g-2 small">
        <div class="col-6">Processing Fee: <strong>${b.processing_fee ? Number(b.processing_fee).toLocaleString()+' TZS' : '—'}</strong></div>
        <div class="col-6">Loan Range: <strong>${b.min_loan_amount ? Number(b.min_loan_amount).toLocaleString() : '0'} - ${b.max_loan_amount ? Number(b.max_loan_amount).toLocaleString() : '∞'} TZS</strong></div>
        <div class="col-12">Requirements: <em>${b.bank_requirements || '—'}</em></div>
      </div>`;
  }
  loadProperties();
  loadBanks().then(()=>{
    // auto-select from query param ?bank= id (Hatua 6 -> Hatua 7)
    const params = new URLSearchParams(window.location.search);
    const qBank = params.get('bank') || params.get('bank_id');
    if(qBank && bankSel){
      bankSel.value = qBank;
      const sel = banksData.find(x=> String(x.id)===String(qBank));
      if(sel) showBankDetails(sel);
    }
  });
  if(bankSel){
    bankSel.addEventListener('change', function(){
      const sel = banksData.find(x=> String(x.id)===this.value);
      showBankDetails(sel||null);
      scheduleCalc();
    });
  }

  // Wizard 5 steps - chain ya namba (green/yellow/grey) kama alivyoomba
  let currentStep=1;
  const totalSteps=5;
  function isStepComplete(n){
    if(n===1) return !!propSel.value;
    if(n===2) return !!bankSel.value;
    if(n===3) return !!(loanEl.value && downEl.value && periodEl.value);
    if(n===4) return !!(incomeEl.value && expensesEl.value && empEl.value);
    if(n===5) return true; // documents optional
    return false;
  }
  function updateStepper(){
    for(let i=1;i<=totalSteps;i++){
      const el=document.getElementById('step'+i);
      if(!el) continue;
      const done=isStepComplete(i);
      const isCurrent=i===currentStep;
      const isPast=i<currentStep;
      // grey = not started, yellow = attempted but incomplete, green = done
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
      // pia current step progress
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
    updateStepper();
    window.scrollTo({top:0,behavior:'smooth'});
  }
  document.querySelectorAll('.wizard-next').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const next=parseInt(btn.dataset.next);
      // validate current step before going next
      if(!isStepComplete(currentStep)){
        updateStepper();
        if(window.showToast) showToast('Please complete step '+currentStep+' before next','warning');
        // mark current as yellow
        const el=document.getElementById('step'+currentStep);
        if(el){ el.style.background='#FFC107'; el.style.color='#000'; }
        return;
      }
      showStep(next);
    });
  });
  document.querySelectorAll('.wizard-prev').forEach(btn=>{
    btn.addEventListener('click', ()=> showStep(parseInt(btn.dataset.prev)));
  });
  // Update stepper on input change
  [propSel, bankSel, loanEl, downEl, periodEl, incomeEl, expensesEl, empEl].forEach(el=>{
    if(el) el.addEventListener('input', updateStepper);
    if(el) el.addEventListener('change', updateStepper);
  });
  // Init
  showStep(1);
  // Wizard submit button
  const wizardSubmit=document.getElementById('maWizardSubmit');
  if(wizardSubmit){
    wizardSubmit.addEventListener('click', ()=> form.requestSubmit());
  }

  // File list preview
  if(docsEl){
    docsEl.addEventListener('change', ()=>{
      const files = docsEl.files;
      if(!files.length){ fileList.textContent=''; return; }
      let html = '<strong>Selected files:</strong><ul class="mb-0 ps-3">';
      for(let f of files){
        html += `<li>${f.name} (${(f.size/1024).toFixed(1)} KB) - ${f.type||'unknown'}</li>`;
      }
      html += '</ul>';
      fileList.innerHTML = html;
    });
  }

  // Live calculation
  let calcTimeout=null;
  function scheduleCalc(){
    clearTimeout(calcTimeout);
    calcTimeout=setTimeout(calculateLive, 400);
  }
  const schedEls=[loanEl, downEl, periodEl, incomeEl, expensesEl, empEl, bankSel].filter(Boolean);
  schedEls.forEach(el=>{
    if(el) el.addEventListener('input', scheduleCalc);
    if(el) el.addEventListener('change', scheduleCalc);
  });

  function formatTZS(n){
    return Number(n).toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2}) + ' TZS';
  }

  async function calculateLive(){
    const loan = parseFloat(loanEl.value) || 0;
    const income = parseFloat(incomeEl.value) || 0;
    const expenses = parseFloat(expensesEl.value) || 0;
    const months = parseInt(periodEl.value) || 0;
    const emp = empEl.value || '';
    const bankId = bankSel ? bankSel.value : null;

    // Need at least loan, months, income
    if(!loan || !months || !income){
      aiCard.classList.add('d-none');
      return;
    }

    // Try backend AJAX first for accurate AI, fallback to client calc
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
    }catch(e){ /* fallback to client */ }

    // Client fallback calc - tumia bank rate kama ipo
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
    if(disposable>0 && monthlyInstallment>0){
      afford=Math.min(100, (disposable/monthlyInstallment)*100);
    }
    let risk=100-afford;
    const empFactors={employed:-10,self_employed:0,business:5,business_owner:5,unemployed:30};
    risk+=(empFactors[emp]||0);
    risk=Math.max(0,Math.min(100,risk));
    renderAi({
      monthly_installment: monthlyInstallment,
      affordability_score: afford,
      risk_score: risk,
      dti_ratio: dti
    });
  }

  function renderAi(data){
    aiCard.classList.remove('d-none');
    const monthly = parseFloat(data.monthly_installment)||0;
    const afford = parseFloat(data.affordability_score)||0;
    const risk = parseFloat(data.risk_score)||0;
    const dti = parseFloat(data.dti_ratio)||0;

    monthlyEl.textContent = formatTZS(monthly);
    affordEl.textContent = afford.toFixed(1)+'%';
    riskEl.textContent = risk.toFixed(1)+'%';
    dtiEl.textContent = dti.toFixed(1)+'%';

    // Affordability colors
    affordBar.style.width = Math.min(100,afford)+'%';
    affordEl.className='ai-metric-value';
    affordBar.className='progress-bar';
    if(afford>100){ affordEl.classList.add('afford-green'); affordBar.classList.add('bg-success'); affordDesc.textContent='Uko salama (Safe)'; affordDesc.className='text-success'; }
    else if(afford>=80){ affordEl.classList.add('afford-yellow'); affordBar.classList.add('bg-warning'); affordDesc.textContent='Uko hatarini kidogo (Caution)'; affordDesc.className='text-warning'; }
    else { affordEl.classList.add('afford-red'); affordBar.classList.add('bg-danger'); affordDesc.textContent='Hauwezi kumudu (Not affordable)'; affordDesc.className='text-danger'; }

    // Risk colors
    riskBar.style.width = Math.min(100,risk)+'%';
    riskEl.className='ai-metric-value';
    riskBar.className='progress-bar';
    if(risk<40){ riskEl.classList.add('risk-green'); riskBar.classList.add('bg-success'); riskDesc.textContent='Risk ndogo (Low risk)'; riskDesc.className='text-success'; }
    else if(risk<=70){ riskEl.classList.add('risk-yellow'); riskBar.classList.add('bg-warning'); riskDesc.textContent='Risk wastani (Medium risk)'; riskDesc.className='text-warning'; }
    else { riskEl.classList.add('risk-red'); riskBar.classList.add('bg-danger'); riskDesc.textContent='Risk kubwa (High risk)'; riskDesc.className='text-danger'; }

    // DTI bar (0-100%)
    dtiBar.style.width = Math.min(100,dti)+'%';

    // Recommendation
    recEl.style.display='block';
    if(afford<80 || risk>70 || dti>40){
      recEl.className='alert alert-warning mt-4 mb-0';
      recEl.innerHTML='<i class="bi bi-exclamation-triangle me-2"></i><strong>Mapendekezo:</strong> Punguza kiasi cha mkopo au ongeza muda wa marejesho. Affordability yako ni chini au risk kubwa. <br><small>Recommendation: Reduce loan amount or extend repayment period.</small>';
    } else {
      recEl.className='alert alert-success mt-4 mb-0';
      recEl.innerHTML='<i class="bi bi-check-circle me-2"></i><strong>Mapendekezo:</strong> Unaweza kuendelea na maombi. Uko salama. <br><small>Recommendation: You can proceed with the application.</small>';
    }
  }

  // Submit
  form.addEventListener('submit', async (e)=>{
    e.preventDefault();
    if(!propSel.value){ showToast('Please select a property','warning'); propSel.focus(); return; }
    if(bankSel && !bankSel.value){ showToast('Please select a bank (Hatua 6)','warning'); bankSel.focus(); return; }
    const required=[loanEl, downEl, periodEl, incomeEl, expensesEl, empEl];
    for(let el of required){ if(!el.value){ showToast('Please fill all required fields','warning'); el.focus(); return; } }

    submitBtn.disabled=true;
    submitBtn.innerHTML='<span class="spinner-border spinner-border-sm me-2"></span> Submitting...';
    try{
      const fd=new FormData();
      fd.append('property', propSel.value);
      if(bankSel && bankSel.value) fd.append('bank', bankSel.value);
      fd.append('loan_amount', loanEl.value);
      fd.append('down_payment', downEl.value);
      fd.append('repayment_period', periodEl.value);
      fd.append('monthly_income', incomeEl.value);
      fd.append('monthly_expenses', expensesEl.value);
      fd.append('employment_status', empEl.value);
      if(docsEl.files.length){
        for(let f of docsEl.files){
          fd.append('documents', f);
        }
      }
      const headers=authHeaders();
      const res=await fetch(API_BASE+'mortgages/', {
        method:'POST',
        headers: headers,
        body: fd
      });
      const data=await res.json();
      if(res.ok || res.status===201){
        showToast('Application submitted successfully! Status: pending','success');
        setTimeout(()=>{ window.location.href='/dashboard/'; }, 1200);
      } else {
        showToast(JSON.stringify(data).slice(0,300),'error','Failed');
      }
    }catch(err){
      showToast(err.message||'Network error','error');
    } finally {
      submitBtn.disabled=false;
      submitBtn.innerHTML='<i class="bi bi-send me-1"></i> Submit Application';
    }
  });

})();
