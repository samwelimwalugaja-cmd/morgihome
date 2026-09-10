/* Bank Verification - 3 steps: Email, Business License, Tax, Company - English */
(function(){
  const API='/api/';
  function getToken(){return localStorage.getItem('access');}
  function authHeaders(){const t=getToken();const h={'Content-Type':'application/json'};if(t)h['Authorization']='Bearer '+t;return h;}
  function authHeadersForm(){const t=getToken();const h={};if(t)h['Authorization']='Bearer '+t;return h;}

  async function load(){
    try{
      const res=await fetch(API+'verify/status/',{headers:authHeaders()});
      if(!res.ok) throw new Error('Failed');
      const d=await res.json();
      // Email
      const emailBadge=document.getElementById('bankEmailBadge');
      const emailStatus=document.getElementById('bankEmailStatus');
      const emailDate=document.getElementById('bankEmailDate');
      const emailValue=document.getElementById('bankEmailValue');
      const emailPending=document.getElementById('bankEmailPending');
      const emailDone=document.getElementById('bankEmailDone');
      const emailIcon=document.getElementById('bankEmailIcon');
      const bEmailBadge=document.getElementById('sumEmail');
      if(emailValue) emailValue.textContent=d.email||'-';
      if(d.email_verified){
        if(emailBadge) emailBadge.textContent='Verified', emailBadge.className='badge bg-success';
        if(emailStatus) emailStatus.textContent='Verified';
        if(emailDate) emailDate.textContent=d.email_verified_at?new Date(d.email_verified_at).toLocaleDateString():'Verified';
        if(emailPending) emailPending.classList.add('d-none');
        if(emailDone) emailDone.classList.remove('d-none');
        if(emailIcon) emailIcon.classList.remove('d-none');
        if(bEmailBadge) bEmailBadge.innerHTML='<span class="badge bg-success">Verified</span>';
        document.getElementById('sumEmailDate').textContent=d.email_verified_at?new Date(d.email_verified_at).toLocaleDateString():'-';
        document.getElementById('bStep1Icon').textContent='✓'; document.getElementById('bStep1Icon').style.background='#dcfce7'; document.getElementById('bStep1Icon').style.color='#166534';
        document.getElementById('bStep1Status').textContent='Verified';
      } else {
        if(emailBadge) emailBadge.textContent='Pending', emailBadge.className='badge bg-warning text-dark';
        if(emailStatus) emailStatus.textContent='Pending';
        if(bEmailBadge) bEmailBadge.innerHTML='<span class="badge bg-warning text-dark">Pending</span>';
        document.getElementById('bStep1Icon').textContent='1'; document.getElementById('bStep1Icon').style.background='#fef3c7';
      }

      // Helper for bank docs
      function updateDoc(prefix, status, verified){
        const badge=document.getElementById('bank'+prefix+'Badge');
        const statusEl=document.getElementById('bank'+prefix+'Status');
        const dateEl=document.getElementById('bank'+prefix+'Date');
        const pending=document.getElementById('bank'+prefix+'Pending');
        const done=document.getElementById('bank'+prefix+'Done');
        const pendingAlert=document.getElementById('bank'+prefix+'PendingAlert');
        const sumCell=document.getElementById('sum'+prefix);
        const stepIcon=document.getElementById('bStep'+(prefix==='License'?2:prefix==='Tax'?3:4)+'Icon');
        const stepStatus=document.getElementById('bStep'+(prefix==='License'?2:prefix==='Tax'?3:4)+'Status');
        const statusKey=prefix.toLowerCase()+'_status';
        // status from d already, but we use passed status
        if(verified){
          if(badge) badge.textContent='Verified', badge.className='badge bg-success';
          if(statusEl) statusEl.textContent='Verified';
          if(pending) pending.classList.add('d-none');
          if(done) done.classList.remove('d-none');
          if(pendingAlert) pendingAlert.classList.add('d-none');
          if(sumCell) sumCell.innerHTML='<span class="badge bg-success">Verified</span>';
          if(stepIcon) stepIcon.textContent='✓', stepIcon.style.background='#dcfce7', stepIcon.style.color='#166534';
          if(stepStatus) stepStatus.textContent='Verified';
        } else if(status==='pending'){
          if(badge) badge.textContent='Pending', badge.className='badge bg-warning text-dark';
          if(statusEl) statusEl.textContent='Pending';
          if(pending) pending.classList.add('d-none');
          if(pendingAlert) pendingAlert.classList.remove('d-none');
          if(sumCell) sumCell.innerHTML='<span class="badge bg-warning text-dark">Pending</span>';
          if(stepIcon) stepIcon.textContent='⏳', stepIcon.style.background='#fef3c7';
          if(stepStatus) stepStatus.textContent='Pending';
        } else {
          if(badge) badge.textContent='Not Submitted', badge.className='badge bg-secondary';
          if(statusEl) statusEl.textContent='Not Submitted';
          if(pending) pending.classList.remove('d-none');
          if(done) done.classList.add('d-none');
          if(pendingAlert) pendingAlert.classList.add('d-none');
          if(sumCell) sumCell.innerHTML='<span class="badge bg-secondary">Not Submitted</span>';
          if(stepIcon) stepIcon.textContent=prefix==='License'?'2':prefix==='Tax'?'3':'4', stepIcon.style.background='#e2e8f0';
        }
      }
      updateDoc('License', d.business_license_status, d.business_license_verified);
      updateDoc('Tax', d.tax_clearance_status, d.tax_clearance_verified);
      updateDoc('Company', d.company_registration_status, d.company_registration_verified);

      // Progress
      let completed=0;
      if(d.email_verified) completed++;
      if(d.business_license_verified) completed++;
      if(d.tax_clearance_verified) completed++;
      if(d.company_registration_verified) completed++;
      const pct=(completed/4)*100;
      document.getElementById('bankProgressBar').style.width=pct+'%';
      document.getElementById('bankProgressText').textContent=completed+'/4 Completed';
      document.getElementById('sumOverall').textContent=completed+'/4 Completed';
      const sumBadge=document.getElementById('sumBadge');
      const topBadge=document.getElementById('bankVerifBadge');
      if(completed===4){
        sumBadge.textContent='Fully Verified'; sumBadge.className='badge bg-success';
        topBadge.textContent='Verified'; topBadge.className='badge bg-success';
        topBadge.style.background='#dcfce7'; topBadge.style.color='#166534';
      } else if(completed>0){
        sumBadge.textContent='Partially Verified'; sumBadge.className='badge bg-warning text-dark';
        topBadge.textContent='Partially Verified'; topBadge.className='badge bg-warning text-dark';
      } else {
        sumBadge.textContent='Not Verified'; sumBadge.className='badge bg-secondary';
        topBadge.textContent='Not Verified'; topBadge.className='badge bg-secondary';
      }
      // Summary dates
      if(d.business_license_submitted_at) document.getElementById('sumLicenseDate').textContent=new Date(d.business_license_submitted_at).toLocaleDateString();
      if(d.tax_clearance_submitted_at) document.getElementById('sumTaxDate').textContent=new Date(d.tax_clearance_submitted_at).toLocaleDateString();
      if(d.company_registration_submitted_at) document.getElementById('sumCompanyDate').textContent=new Date(d.company_registration_submitted_at).toLocaleDateString();
    }catch(e){ console.error(e); }
  }

  // Resend email
  document.getElementById('bankResendEmail')?.addEventListener('click', async ()=>{
    try{
      const res=await fetch(API+'verify/email/send/',{method:'POST',headers:authHeaders()});
      const data=await res.json();
      const el=document.getElementById('bankEmailResult');
      el.classList.remove('d-none');
      if(res.ok){ el.className='alert alert-success small'; el.textContent=data.message; if(window.showToast) showToast(data.message,'success'); }
      else { el.className='alert alert-danger small'; el.textContent=data.error||'Failed'; }
    }catch(e){ if(window.showToast) showToast(e.message,'error'); }
  });

  function setupUpload(inputId, previewId, btnId, resultId, docType){
    const input=document.getElementById(inputId);
    const preview=document.getElementById(previewId);
    const btn=document.getElementById(btnId);
    const result=document.getElementById(resultId);
    if(input && preview){
      input.addEventListener('change', ()=>{
        const f=input.files[0];
        if(!f){ preview.textContent=''; return; }
        if(f.size>5242880){ preview.innerHTML='<span class="text-danger">File too large, max 5MB</span>'; return; }
        preview.textContent=f.name+' ('+(f.size/1024).toFixed(1)+' KB)';
      });
    }
    if(btn){
      btn.addEventListener('click', async ()=>{
        const f=input.files[0];
        if(!f){ if(window.showToast) showToast('Please select a file','warning'); return; }
        btn.disabled=true; btn.innerHTML='<span class="spinner-border spinner-border-sm me-1"></span> Uploading...';
        try{
          const fd=new FormData(); fd.append('document', f);
          const res=await fetch(API+'verify/bank/'+docType+'/',{method:'POST',headers:authHeadersForm(),body:fd});
          const text=await res.text();
          let data={}; try{ data=JSON.parse(text); }catch(e){ data={detail:text}; }
          if(result){ result.classList.remove('d-none'); }
          if(res.ok){
            if(window.showToast) showToast(docType+' uploaded successfully!','success');
            if(result){ result.className='alert alert-success small'; result.textContent=data.message; }
            load();
          } else {
            if(window.showToast) showToast(data.error||'Upload failed','error');
            if(result){ result.className='alert alert-danger small'; result.textContent=data.error||text.slice(0,200); }
          }
        }catch(e){
          if(window.showToast) showToast(e.message,'error');
          if(result){ result.classList.remove('d-none'); result.className='alert alert-danger small'; result.textContent=e.message; }
        } finally { btn.disabled=false; btn.innerHTML='<i class="bi bi-cloud-upload me-1"></i> Upload '+(docType==='business_license'?'License':docType==='tax_clearance'?'Tax Clearance':'Registration'); }
      });
    }
  }
  setupUpload('bankLicenseFile','bankLicensePreview','bankLicenseBtn','bankLicenseResult','business_license');
  setupUpload('bankTaxFile','bankTaxPreview','bankTaxBtn','bankTaxResult','tax_clearance');
  setupUpload('bankCompanyFile','bankCompanyPreview','bankCompanyBtn','bankCompanyResult','company_registration');

  load();
})();
