/* Application Tracking - Auto refresh every 30s */
(function(){
  const API_BASE='/api/';
  function getToken(){ return localStorage.getItem('access'); }
  function authHeaders(){ const t=getToken(); const h={'Content-Type':'application/json'}; if(t) h['Authorization']='Bearer '+t; return h; }
  const pathParts=window.location.pathname.split('/').filter(Boolean);
  let appId=null;
  // Try to get from URL /customer/track/<id>/ or ?id=
  const urlMatch=window.location.pathname.match(/\/track\/(\d+)\/?/);
  if(urlMatch) appId=urlMatch[1];
  else {
    const params=new URLSearchParams(window.location.search);
    appId=params.get('id') || params.get('application_id');
    if(!appId){
      const el=document.getElementById('trackAppId');
      if(el) appId=el.textContent.replace('#APP-','').replace('#','');
    }
  }
  // If still not found, try to get first pending application
  async function fetchAndRender(){
    if(!appId){
      // Try to fetch first application
      try{
        const res=await fetch(API_BASE+'mortgages/', {headers: authHeaders()});
        const data=await res.json();
        const arr=Array.isArray(data)?data:(data.results||[]);
        if(arr.length) appId=arr[0].id;
        else return;
      }catch(e){ return; }
    }
    try{
      const res=await fetch(API_BASE+'mortgages/'+appId+'/', {headers: authHeaders()});
      if(!res.ok) return;
      const app=await res.json();
      document.getElementById('trackAppId').textContent='#APP-'+String(app.id).padStart(4,'0');
      document.getElementById('trackRef').textContent='#APP-'+String(app.id).padStart(4,'0');
      document.getElementById('trackProperty').textContent=app.property_details?app.property_details.title:'Property #'+app.property;
      document.getElementById('trackLoan').textContent='TZS '+Number(app.loan_amount).toLocaleString();
      document.getElementById('trackDate').textContent=new Date(app.created_at).toLocaleDateString();
      const statusMap={pending:'Pending',document_verification:'Document Verification',valuation:'Valuation',credit_assessment:'Credit Assessment',approved:'Approved',rejected:'Rejected',disbursed:'Disbursed'};
      document.getElementById('trackStatus').textContent=statusMap[app.status]||app.status;
      document.getElementById('trackStatus').className='status-badge status-'+app.status;
      document.getElementById('trackAfford').textContent=(app.affordability_score!=null?app.affordability_score.toFixed(1)+'%':'—');
      document.getElementById('trackRisk').textContent=(app.risk_score!=null?app.risk_score.toFixed(1)+'%':'—');
      document.getElementById('trackDti').textContent=(app.dti_ratio!=null?app.dti_ratio.toFixed(1)+'%':'—');
      document.getElementById('trackRec').textContent=app.affordability_score<80?'Punguza kiasi cha mkopo au ongeza muda':'Unaweza kuendelea na maombi';
      // Progress bar
      const steps=['pending','document_verification','valuation','credit_assessment','approved','disbursed'];
      const idx=steps.indexOf(app.status);
      const progressIdx=idx===-1?0:idx;
      const pct=((progressIdx+1)/steps.length)*100;
      document.getElementById('trackProgressBar').style.width=pct+'%';
      // Update steps visual
      const stepEls=document.querySelectorAll('#trackSteps .col-2');
      stepEls.forEach((el,i)=>{
        const icon=el.querySelector('.step-icon');
        const statusEl=el.querySelector('.step-status');
        if(i<progressIdx){ icon.className='step-icon done'; icon.textContent='✅'; if(statusEl) statusEl.textContent='Done'; if(statusEl) statusEl.className='step-status text-success'; }
        else if(i===progressIdx){ icon.className='step-icon current'; icon.textContent='🔄'; if(statusEl) statusEl.textContent='Current'; if(statusEl) statusEl.style.color='#0077B6'; }
        else { icon.className='step-icon pending'; icon.textContent='⏳'; if(statusEl) statusEl.textContent='Pending'; }
      });
      const currentMap={pending:'Application Submitted',document_verification:'Document Verification',valuation:'Property Valuation',credit_assessment:'Credit Assessment',approved:'Approval',rejected:'Rejected',disbursed:'Disbursement'};
      document.getElementById('trackCurrent').textContent=currentMap[app.status]||app.status;
      const nextMap={pending:'Document Verification',document_verification:'Property Valuation',valuation:'Credit Assessment',credit_assessment:'Approval',approved:'Disbursement',disbursed:'Completed'};
      document.getElementById('trackNext').textContent=nextMap[app.status]||'—';
      document.getElementById('trackViewFull').href='/customer/applications/'+app.id+'/';
      // Notes
      if(app.notes) document.getElementById('trackNotes').textContent=app.notes;
    }catch(e){ console.error(e); }
  }
  fetchAndRender();
  setInterval(fetchAndRender, 30000);
  // Upload handler
  const uploadBtn=document.getElementById('trackUploadBtn');
  if(uploadBtn){
    uploadBtn.addEventListener('click', async ()=>{
      const input=document.getElementById('trackFileInput');
      if(!input.files.length){ showToast('Please select files','warning'); return; }
      const fd=new FormData();
      for(let f of input.files) fd.append('documents', f);
      try{
        const res=await fetch('/api/mortgages/'+appId+'/', {method:'PATCH', headers:{'Authorization':'Bearer '+getToken()}, body: fd});
        if(res.ok){ showToast('Documents uploaded','success'); bootstrap.Modal.getInstance(document.getElementById('uploadDocsModal')).hide(); fetchAndRender(); }
        else { const d=await res.json(); showToast(JSON.stringify(d).slice(0,200),'error'); }
      }catch(e){ showToast(e.message,'error'); }
    });
  }
})();
