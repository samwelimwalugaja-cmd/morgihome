/* Verification Account - Customer */
(function(){
  const API='/api/';
  function authHeaders(){ const t=localStorage.getItem('access'); const h={'Content-Type':'application/json'}; if(t) h['Authorization']='Bearer '+t; return h; }
  function authHeadersForm(){ const t=localStorage.getItem('access'); const h={}; if(t) h['Authorization']='Bearer '+t; return h; }

  async function loadVerification(){
    try{
      const res=await fetch(API+'verify/status/', {headers: authHeaders()});
      if(!res.ok) throw new Error('Failed');
      const data=await res.json();
      // Update header values
      document.getElementById('emailValue').textContent=data.email||'—';
      document.getElementById('phoneValue').textContent=data.phone_number||'—';
      document.getElementById('ninValue').textContent=data.nin_number||'—';

      // Email
      const emailBadge=document.getElementById('emailBadge2');
      const emailStatus=document.getElementById('emailStatus2');
      const emailPendingBox=document.getElementById('emailPendingBox');
      const emailVerifiedBox=document.getElementById('emailVerifiedBox');
      const emailIcon=document.getElementById('emailVerifiedIcon');
      const step1Icon=document.getElementById('step1Icon');
      const step1Status=document.getElementById('step1Status');
      if(data.email_verified){
        emailBadge.textContent='Verified'; emailBadge.className='badge bg-success';
        emailStatus.textContent='✅ Verified'; emailStatus.className='text-success';
        emailPendingBox.classList.add('d-none'); emailVerifiedBox.classList.remove('d-none');
        if(emailIcon) emailIcon.style.display='inline';
        step1Icon.textContent='✅'; step1Icon.style.background='#D4EDDA'; step1Icon.style.color='#155724';
        step1Status.textContent='Verified'; step1Status.className='text-success';
        document.getElementById('summaryEmailStatus').innerHTML='<span class="badge bg-success">Verified</span>';
        document.getElementById('summaryEmailDate').textContent=data.email_verified_at?new Date(data.email_verified_at).toLocaleDateString():'Verified';
      } else {
        emailBadge.textContent='Pending'; emailBadge.className='badge bg-warning';
        emailStatus.textContent='⏳ Pending'; emailStatus.className='text-warning';
        emailPendingBox.classList.remove('d-none'); emailVerifiedBox.classList.add('d-none');
        if(emailIcon) emailIcon.style.display='none';
        step1Icon.textContent='1'; step1Icon.style.background='#FFF3CD'; step1Icon.style.color='#856404';
        step1Status.textContent='Pending'; step1Status.className='text-warning';
        document.getElementById('summaryEmailStatus').innerHTML='<span class="badge bg-warning">Pending</span>';
      }

      // Phone
      const phoneBadge=document.getElementById('phoneBadge2');
      const phoneStatus=document.getElementById('phoneStatus2');
      const phonePendingBox=document.getElementById('phonePendingBox');
      const phoneVerifiedBox=document.getElementById('phoneVerifiedBox');
      const step2Icon=document.getElementById('step2Icon');
      const step2Status=document.getElementById('step2Status');
      if(data.phone_verified){
        phoneBadge.textContent='Verified'; phoneBadge.className='badge bg-success';
        phoneStatus.textContent='✅ Verified'; phoneStatus.className='text-success';
        phonePendingBox.classList.add('d-none'); phoneVerifiedBox.classList.remove('d-none');
        step2Icon.textContent='✅'; step2Icon.style.background='#D4EDDA'; step2Icon.style.color='#155724';
        step2Status.textContent='Verified';
        document.getElementById('summaryPhoneStatus').innerHTML='<span class="badge bg-success">Verified</span>';
      } else {
        phoneBadge.textContent='Pending'; phoneBadge.className='badge bg-warning';
        phoneStatus.textContent='⏳ Pending'; phoneStatus.className='text-warning';
        phonePendingBox.classList.remove('d-none'); phoneVerifiedBox.classList.add('d-none');
        step2Icon.textContent='2'; step2Icon.style.background='#FFF3CD';
        step2Status.textContent='Pending';
        document.getElementById('summaryPhoneStatus').innerHTML='<span class="badge bg-warning">Pending</span>';
      }

      // NIN
      const ninBadge=document.getElementById('ninBadge2');
      const ninStatus=document.getElementById('ninStatus2');
      const ninPendingBox=document.getElementById('ninPendingBox');
      const ninVerifiedBox=document.getElementById('ninVerifiedBox');
      const ninPendingAlert=document.getElementById('ninPendingAlert');
      const step3Icon=document.getElementById('step3Icon');
      const step3Status=document.getElementById('step3Status');
      if(data.nin_verified){
        ninBadge.textContent='Verified'; ninBadge.className='badge bg-success';
        ninStatus.textContent='✅ Verified'; ninStatus.className='text-success';
        ninPendingBox.classList.add('d-none'); ninVerifiedBox.classList.remove('d-none'); ninPendingAlert.classList.add('d-none');
        step3Icon.textContent='✅'; step3Icon.style.background='#D4EDDA'; step3Icon.style.color='#155724';
        step3Status.textContent='Verified';
        document.getElementById('summaryNinStatus').innerHTML='<span class="badge bg-success">Verified</span>';
      } else if(data.nin_status==='pending'){
        ninBadge.textContent='Pending'; ninBadge.className='badge bg-warning';
        ninStatus.textContent='⏳ Pending'; ninStatus.className='text-warning';
        ninPendingBox.classList.add('d-none'); ninVerifiedBox.classList.add('d-none'); ninPendingAlert.classList.remove('d-none');
        step3Icon.textContent='🔄'; step3Icon.style.background='#FFF3CD';
        step3Status.textContent='Pending';
        document.getElementById('summaryNinStatus').innerHTML='<span class="badge bg-warning">Pending</span>';
      } else {
        ninBadge.textContent='Not Submitted'; ninBadge.className='badge bg-secondary';
        ninStatus.textContent='⏳ Pending'; ninStatus.className='text-warning';
        ninPendingBox.classList.remove('d-none'); ninVerifiedBox.classList.add('d-none'); ninPendingAlert.classList.add('d-none');
        step3Icon.textContent='3'; step3Icon.style.background='#E9ECEF';
        step3Status.textContent='Pending';
        document.getElementById('summaryNinStatus').innerHTML='<span class="badge bg-secondary">Not Submitted</span>';
      }

      // Progress
      let completed=0;
      if(data.email_verified) completed++;
      if(data.phone_verified) completed++;
      if(data.nin_verified) completed++;
      const pct=(completed/3)*100;
      document.getElementById('verifyProgressBar').style.width=pct+'%';
      document.getElementById('verifyOverallBadge').textContent=completed+'/3 Completed';
      const overallBadge=document.getElementById('verifyOverallBadge');
      const overallStatus=document.getElementById('verifyOverallStatus');
      if(completed===3){
        overallBadge.className='badge bg-success';
        overallStatus.textContent='Fully Verified ✅';
        document.getElementById('summaryOverall').textContent='🟢 3/3 Verifications Completed';
        document.getElementById('summaryOverallBadge').textContent='Fully Verified';
        document.getElementById('summaryOverallBadge').className='badge bg-success';
      } else {
        overallBadge.className='badge bg-warning';
        overallStatus.textContent=completed+'/3 Completed';
        document.getElementById('summaryOverall').textContent='🟡 '+completed+'/3 Verifications Completed';
        document.getElementById('summaryOverallBadge').textContent=completed>0?'Partially Verified':'Not Verified';
      }

      // Update summary dates
      if(data.email_verified) document.getElementById('summaryEmailDate').textContent=new Date().toLocaleDateString();
      if(data.phone_verified) document.getElementById('summaryPhoneDate').textContent=new Date().toLocaleDateString();
      if(data.nin_verified) document.getElementById('summaryNinDate').textContent=new Date().toLocaleDateString();

    }catch(e){ console.error(e); }
  }

  // Resend Email
  document.getElementById('resendEmailBtn2')?.addEventListener('click', async ()=>{
    try{
      const res=await fetch(API+'verify/email/send/', {method:'POST', headers: authHeaders()});
      const data=await res.json();
      const el=document.getElementById('emailResendResult');
      el.style.display='block';
      if(res.ok){ el.className='alert alert-success mt-2 small'; el.textContent=data.message+' Token: '+(data.token||'sent'); if(window.showToast) showToast(data.message,'success'); }
      else { el.className='alert alert-danger mt-2 small'; el.textContent=data.error||'Failed'; }
    }catch(e){ showToast(e.message,'error'); }
  });

  // Verify Phone
  document.getElementById('verifyPhoneBtn2')?.addEventListener('click', async ()=>{
    const otp=document.getElementById('otpInput2').value.trim();
    if(!otp || otp.length!==6){ showToast('Please enter 6-digit OTP','warning'); return; }
    try{
      const res=await fetch(API+'verify/phone/confirm/', {method:'POST', headers: authHeaders(), body: JSON.stringify({otp})});
      const data=await res.json();
      const el=document.getElementById('phoneResult');
      el.style.display='block';
      if(res.ok){ el.className='alert alert-success'; el.textContent=data.message; showToast(data.message,'success'); loadVerification(); }
      else { el.className='alert alert-danger'; el.textContent=data.error; showToast(data.error,'error'); }
    }catch(e){ showToast(e.message,'error'); }
  });
  document.getElementById('resendOtpBtn2')?.addEventListener('click', async ()=>{
    try{
      const res=await fetch(API+'verify/phone/send/', {method:'POST', headers: authHeaders()});
      const data=await res.json();
      if(res.ok){ showToast(data.message+' OTP: '+(data.otp||''),'success'); document.getElementById('phoneResult').style.display='block'; document.getElementById('phoneResult').className='alert alert-info'; document.getElementById('phoneResult').textContent=data.message; }
      else showToast(data.error,'error');
    }catch(e){ showToast(e.message,'error'); }
  });

  // Submit NIN
  document.getElementById('ninFileInput')?.addEventListener('change', (e)=>{
    const file=e.target.files[0];
    const preview=document.getElementById('ninFilePreview');
    if(!file){ preview.innerHTML=''; return; }
    if(file.type.startsWith('image/')){
      const url=URL.createObjectURL(file);
      preview.innerHTML=`<img src="${url}" style="max-width:200px;max-height:150px;border-radius:8px;border:1px solid #eef2f7"><br><small>${file.name}</small>`;
    } else {
      preview.innerHTML=`<i class="bi bi-file-earmark-pdf" style="font-size:32px;color:#DC3545"></i><br><small>${file.name}</small>`;
    }
  });
  document.getElementById('submitNinBtn')?.addEventListener('click', async ()=>{
    const nin=document.getElementById('ninNumberInput').value.trim();
    const file=document.getElementById('ninFileInput').files[0];
    if(!nin){ showToast('Please enter NIN number','warning'); return; }
    if(!file){ showToast('Please select ID file','warning'); return; }
    const fd=new FormData();
    fd.append('nin_number', nin);
    fd.append('document', file);
    fd.append('document_type', 'id');
    try{
      const res=await fetch(API+'verify/nin/submit/', {method:'POST', headers:{'Authorization':'Bearer '+(localStorage.getItem('access')||'')}, body: fd});
      const data=await res.json();
      const el=document.getElementById('ninResult');
      el.style.display='block';
      if(res.ok){ el.className='alert alert-success'; el.textContent=data.message; showToast(data.message,'success'); loadVerification(); }
      else { el.className='alert alert-danger'; el.textContent=data.error||'Failed'; showToast(data.error,'error'); }
    }catch(e){ showToast(e.message,'error'); }
  });

  loadVerification();
})();
