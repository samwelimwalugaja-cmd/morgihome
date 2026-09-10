/* My Applications - Customer */
(function(){
  const API_BASE='/api/';
  function getToken(){ return localStorage.getItem('access'); }
  function authHeaders(){ const t=getToken(); const h={'Content-Type':'application/json'}; if(t) h['Authorization']='Bearer '+t; return h; }
  const grid=document.getElementById('applicationsGrid');
  const empty=document.getElementById('applicationsEmpty');
  const statusFilter=document.getElementById('appStatusFilter');
  const searchEl=document.getElementById('appSearch');
  const sortEl=document.getElementById('appSort');
  let allApps=[];

  const statusMap={
    pending:{label:'Pending', color:'pending', icon:'🟡'},
    document_verification:{label:'Document Verification', color:'document_verification', icon:'🟠'},
    valuation:{label:'Valuation', color:'valuation', icon:'🔵'},
    credit_assessment:{label:'Credit Assessment', color:'credit_assessment', icon:'🟣'},
    approved:{label:'Approved', color:'approved', icon:'🟢'},
    rejected:{label:'Rejected', color:'rejected', icon:'🔴'},
    disbursed:{label:'Disbursed', color:'disbursed', icon:'🟢'}
  };

  function formatTZS(n){ return 'TZS '+Number(n).toLocaleString('en-US'); }
  function formatDate(d){ return new Date(d).toLocaleString('en-US',{year:'numeric',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}); }

  async function fetchApps(){
    if(!grid) return;
    grid.innerHTML='<div class="text-center py-5 w-100" style="grid-column:1/-1"><div class="spinner-border text-primary"></div></div>';
    try{
      const res=await fetch(API_BASE+'mortgages/', {headers: authHeaders()});
      if(!res.ok) throw new Error('HTTP '+res.status);
      const data=await res.json();
      allApps=Array.isArray(data)?data:(data.results||[]);
      render();
    }catch(e){
      grid.innerHTML=`<div class="alert alert-danger w-100" style="grid-column:1/-1">Failed to load: ${e.message}</div>`;
    }
  }

  function getFiltered(){
    let arr=[...allApps];
    const status=statusFilter?statusFilter.value:'all';
    const q=(searchEl?searchEl.value:'').toLowerCase().trim();
    const sort=sortEl?sortEl.value:'newest';
    if(status!=='all') arr=arr.filter(a=>a.status===status);
    if(q){
      arr=arr.filter(a=>{
        const prop=(a.property_details?a.property_details.title:'')+' '+(a.property_details?a.property_details.location:'');
        const amt=String(a.loan_amount||'');
        return prop.toLowerCase().includes(q) || amt.includes(q);
      });
    }
    if(sort==='newest') arr.sort((a,b)=>new Date(b.created_at)-new Date(a.created_at));
    else if(sort==='oldest') arr.sort((a,b)=>new Date(a.created_at)-new Date(b.created_at));
    else if(sort==='highest') arr.sort((a,b)=>parseFloat(b.loan_amount)-parseFloat(a.loan_amount));
    else if(sort==='lowest') arr.sort((a,b)=>parseFloat(a.loan_amount)-parseFloat(b.loan_amount));
    return arr;
  }

  function render(){
    const arr=getFiltered();
    if(!arr.length){
      grid.classList.add('d-none');
      if(empty) empty.classList.remove('d-none');
      return;
    }
    if(empty) empty.classList.add('d-none');
    grid.classList.remove('d-none');
    grid.innerHTML=arr.map(app=>{
      const prop=app.property_details ? app.property_details.title : ('Property #'+app.property);
      const status=statusMap[app.status]||statusMap.pending;
      const afford=app.affordability_score!=null?Number(app.affordability_score).toFixed(1):'—';
      const risk=app.risk_score!=null?Number(app.risk_score).toFixed(1):'—';
      const monthly=app.monthly_installment?formatTZS(app.monthly_installment):'—';
      const statusClass='status-'+status.color;
      // Badge ya verified/not verified - inaonekana kwa bank/realestate/lawyer pia
      const verif = app.customer_is_verified ? '<span class="badge bg-success ms-1">Verified ✅</span>' : (app.customer_verification_level==='not_verified' ? '<span class="badge bg-danger ms-1">Not Verified ❌</span>' : '<span class="badge bg-warning text-dark ms-1">Partially Verified ⚠️</span>');
      const custLabel = app.customer_name ? `${app.customer_name} ${verif}` : '';
      // Actions per status
      let actions='';
      if(app.status==='pending'){
        actions=`<button class="btn btn-view btn-sm" onclick="viewApp(${app.id})"><i class="bi bi-eye me-1"></i> View Details</button><button class="btn btn-sm btn-outline-danger" onclick="cancelApp(${app.id})"><i class="bi bi-x-circle me-1"></i> Cancel</button>`;
      } else if(app.status==='document_verification'){
        actions=`<button class="btn btn-view btn-sm" onclick="viewApp(${app.id})"><i class="bi bi-eye me-1"></i> View Details</button><button class="btn btn-upload btn-sm" onclick="uploadDocs(${app.id})"><i class="bi bi-cloud-upload me-1"></i> Upload Documents</button>`;
      } else if(app.status==='valuation' || app.status==='credit_assessment'){
        actions=`<button class="btn btn-view btn-sm" onclick="viewApp(${app.id})"><i class="bi bi-eye me-1"></i> View Details</button><button class="btn btn-track btn-sm" onclick="trackApp(${app.id})"><i class="bi bi-graph-up me-1"></i> Track Progress</button>`;
      } else if(app.status==='approved'){
        actions=`<button class="btn btn-view btn-sm" onclick="viewApp(${app.id})"><i class="bi bi-eye me-1"></i> View Details</button><button class="btn btn-track btn-sm" onclick="viewRepayment(${app.id})"><i class="bi bi-calendar me-1"></i> View Repayment</button><button class="btn btn-sm btn-success" onclick="signContract(${app.id})"><i class="bi bi-pen me-1"></i> Sign Contract</button>`;
      } else if(app.status==='rejected'){
        actions=`<button class="btn btn-view btn-sm" onclick="viewApp(${app.id})"><i class="bi bi-eye me-1"></i> View Details</button><a href="/customer/apply/" class="btn btn-sm btn-primary"><i class="bi bi-arrow-repeat me-1"></i> Apply Again</a>`;
      } else if(app.status==='disbursed'){
        actions=`<button class="btn btn-view btn-sm" onclick="viewApp(${app.id})"><i class="bi bi-eye me-1"></i> View Details</button><button class="btn btn-track btn-sm" onclick="viewRepayment(${app.id})"><i class="bi bi-calendar me-1"></i> Repayment</button><button class="btn btn-sm btn-outline-primary" onclick="viewHistory(${app.id})"><i class="bi bi-clock-history me-1"></i> Payment History</button>`;
      } else {
        actions=`<button class="btn btn-view btn-sm" onclick="viewApp(${app.id})"><i class="bi bi-eye me-1"></i> View Details</button>`;
      }
      return `
      <div class="app-card">
        <div class="app-card-header">
          <h6>🏠 ${prop}</h6>
          ${custLabel ? `<div class="small mt-1">👤 ${custLabel}</div>` : ''}
          <div class="meta"><span>💰 ${formatTZS(app.loan_amount)}</span><span>📅 ${formatDate(app.created_at)}</span></div>
        </div>
        <div class="app-card-body">
          <div><span class="status-badge ${statusClass}">${status.icon} ${status.label}</span></div>
          <div class="ai-assessment-mini">
            <div class="ai-item"><div class="ai-label">Affordability</div><div class="ai-value">${afford}%</div><div class="ai-progress"><div class="ai-progress-bar" style="width:${afford!=='—'?afford:0}%;background:${afford>100?'#28A745':afford>=80?'#FFC107':'#DC3545'}"></div></div></div>
            <div class="ai-item"><div class="ai-label">Risk</div><div class="ai-value">${risk}%</div><div class="ai-progress"><div class="ai-progress-bar" style="width:${risk!=='—'?risk:0}%;background:${risk<40?'#28A745':risk<=70?'#FFC107':'#DC3545'}"></div></div></div>
          </div>
          <div class="small text-muted mt-2">Monthly Installment: <strong style="color:#0077B6">${monthly}</strong></div>
        </div>
        <div class="app-card-footer">
          ${actions}
        </div>
      </div>`;
    }).join('');
  }

  // Expose for inline handlers
  window.viewApp=async function(id){
    const modal=new bootstrap.Modal(document.getElementById('appDetailModal'));
    const body=document.getElementById('appDetailBody');
    const title=document.getElementById('appDetailTitle');
    body.innerHTML='<div class="text-center py-4"><div class="spinner-border text-primary"></div></div>';
    title.textContent='Application #'+id;
    modal.show();
    try{
      const res=await fetch(API_BASE+'mortgages/'+id+'/', {headers: authHeaders()});
      if(!res.ok) throw new Error('Not found');
      const app=await res.json();
      const prop=app.property_details?app.property_details.title:'Property #'+app.property;
      const status=statusMap[app.status]||statusMap.pending;
      body.innerHTML=`
        <div class="row g-4">
          <div class="col-md-6"><h6>Application Details</h6><ul class="list-group small">
            <li class="list-group-item d-flex justify-content-between"><span>Property</span><strong>${prop}</strong></li>
            <li class="list-group-item d-flex justify-content-between"><span>Loan Amount</span><strong>${formatTZS(app.loan_amount)}</strong></li>
            <li class="list-group-item d-flex justify-content-between"><span>Down Payment</span><strong>${formatTZS(app.down_payment)}</strong></li>
            <li class="list-group-item d-flex justify-content-between"><span>Repayment</span><strong>${app.repayment_period} months</strong></li>
            <li class="list-group-item d-flex justify-content-between"><span>Monthly Income</span><strong>${formatTZS(app.monthly_income)}</strong></li>
            <li class="list-group-item d-flex justify-content-between"><span>Monthly Expenses</span><strong>${formatTZS(app.monthly_expenses)}</strong></li>
            <li class="list-group-item d-flex justify-content-between"><span>Employment</span><strong>${app.employment_status||'—'}</strong></li>
          </ul></div>
          <div class="col-md-6"><h6>AI Assessment</h6><ul class="list-group small">
            <li class="list-group-item d-flex justify-content-between"><span>Affordability</span><strong>${app.affordability_score!=null?app.affordability_score+'%':'—'}</strong></li>
            <li class="list-group-item d-flex justify-content-between"><span>Risk Score</span><strong>${app.risk_score!=null?app.risk_score+'%':'—'}</strong></li>
            <li class="list-group-item d-flex justify-content-between"><span>Monthly Installment</span><strong>${app.monthly_installment?formatTZS(app.monthly_installment):'—'}</strong></li>
            <li class="list-group-item d-flex justify-content-between"><span>DTI Ratio</span><strong>${app.dti_ratio!=null?app.dti_ratio.toFixed(1)+'%':'—'}</strong></li>
            <li class="list-group-item d-flex justify-content-between"><span>Status</span><span class="status-badge ${'status-'+status.color}">${status.label}</span></li>
          </ul></div>
        </div>
        <div class="mt-4"><h6>Timeline</h6>
          <ul class="list-group small">
            <li class="list-group-item"><i class="bi bi-check-circle-fill text-success me-2"></i> Application Submitted - ${formatDate(app.created_at)}</li>
            <li class="list-group-item"><i class="bi bi-clock text-warning me-2"></i> Document Verification - ${app.status==='document_verification'?'Current':app.status==='pending'?'Pending':'Done'}</li>
            <li class="list-group-item"><i class="bi bi-clock me-2"></i> Valuation - Pending</li>
            <li class="list-group-item"><i class="bi bi-clock me-2"></i> Credit Assessment - Pending</li>
            <li class="list-group-item"><i class="bi bi-clock me-2"></i> Approval - ${app.status}</li>
            <li class="list-group-item"><i class="bi bi-clock me-2"></i> Disbursement - Pending</li>
          </ul>
        </div>
        <div class="mt-3">
          <a href="/customer/track/${app.id}/" class="btn btn-sm btn-primary"><i class="bi bi-graph-up me-1"></i> Track Progress</a>
          <button class="btn btn-sm btn-outline-secondary" data-bs-dismiss="modal">Close</button>
        </div>
      `;
    }catch(e){
      body.innerHTML=`<div class="alert alert-danger">Failed to load: ${e.message}</div>`;
    }
  };
  window.trackApp=function(id){ window.location.href='/customer/track/'+id+'/'; };
  window.viewRepayment=function(id){ window.location.href='/customer/repayment/'; };
  window.viewHistory=function(id){ window.location.href='/customer/repayment/'; };
  window.uploadDocs=function(id){ window.viewApp(id); showToast('Please upload documents in detail view','info'); };
  window.signContract=function(id){ window.location.href='/customer/contracts/'; };
  window.cancelApp=async function(id){
    if(!confirm('Cancel this application?')) return;
    try{
      const res=await fetch(API_BASE+'mortgages/'+id+'/', {method:'DELETE', headers: authHeaders()});
      if(res.ok){ showToast('Application cancelled','success'); fetchApps(); }
      else { const d=await res.json(); showToast(JSON.stringify(d).slice(0,200),'error'); }
    }catch(e){ showToast(e.message,'error'); }
  };

  if(statusFilter) statusFilter.addEventListener('change', render);
  if(searchEl) searchEl.addEventListener('input', render);
  if(sortEl) sortEl.addEventListener('change', render);

  // Auto-refresh every 30s if needed
  // setInterval(fetchApps, 30000);

  fetchApps();
})();
