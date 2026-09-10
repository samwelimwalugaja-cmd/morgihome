/* My Contracts */
(function(){
  const grid=document.getElementById('contractsGrid');
  let allContracts=[];

  // Mock data if API not available
  const mockContracts=[
    {id:1, number:'CTR-2025-001', property:'Modern Villa at Mikocheni', loan:'TZS 50,000,000', created:'2025-01-20', status:'pending_signature', signatures:{customer:'signed', seller:'pending', bank:'pending', lawyer:'pending'}},
    {id:2, number:'CTR-2025-002', property:'Beach House Oysterbay', loan:'TZS 80,000,000', created:'2025-01-18', status:'signed', signatures:{customer:'signed', seller:'signed', bank:'signed', lawyer:'pending'}},
  ];

  function render(){
    if(!grid) return;
    if(!allContracts.length){
      grid.innerHTML='<div class="col-12 text-center py-5"><i class="bi bi-file-text" style="font-size:48px;color:#cbd5e0"></i><p class="text-muted mt-3">No contracts found.</p></div>';
      return;
    }
    grid.innerHTML=allContracts.map(c=>{
      const statusMap={draft:{label:'Draft',cls:'status-draft'},pending_signature:{label:'Pending Signature',cls:'status-pending_signature'},signed:{label:'Signed',cls:'status-signed'},executed:{label:'Executed',cls:'status-executed'}};
      const s=statusMap[c.status]||statusMap.draft;
      const sig=(k)=> c.signatures[k]==='signed'?'<span class="signature-badge sig-signed">✅ '+k+'</span>':'<span class="signature-badge sig-pending">⏳ '+k+' (Pending)</span>';
      return `<div class="col-md-6"><div class="contract-card"><div class="contract-card-header"><h6>📄 Contract ${c.number}</h6><small class="text-muted">Property: ${c.property} | Loan: ${c.loan} | Created: ${c.created}</small></div><div class="contract-card-body"><div><span class="badge ${s.cls}">${s.label}</span></div><div class="mt-3"><small class="text-muted d-block mb-1">Signatures Status:</small><div class="d-flex gap-2 flex-wrap">${sig('customer')} ${sig('seller')} ${sig('bank')} ${sig('lawyer')}</div></div></div><div class="card-footer d-flex gap-2 flex-wrap p-3 bg-light"><button class="btn btn-sm btn-outline-primary" onclick="viewContract(${c.id})"><i class="bi bi-eye me-1"></i> View Details</button><button class="btn btn-sm btn-primary" style="background:#0077B6;border-color:#0077B6" onclick="signContractModal(${c.id})"><i class="bi bi-pen me-1"></i> Sign Contract</button><button class="btn btn-sm btn-outline-secondary" onclick="downloadContract(${c.id})"><i class="bi bi-download me-1"></i> Download PDF</button></div></div></div>`;
    }).join('');
  }

  // Try fetch from API if exists, fallback to mock
  async function fetchContracts(){
    try{
      const res=await fetch('/api/contracts/', {headers: {'Authorization':'Bearer '+(localStorage.getItem('access')||'')}});
      if(res.ok){
        const data=await res.json();
        allContracts=Array.isArray(data)?data:(data.results||mockContracts);
      } else {
        allContracts=mockContracts;
      }
    }catch(e){ allContracts=mockContracts; }
    render();
  }

  window.viewContract=function(id){
    const c=allContracts.find(x=>x.id===id);
    if(!c) return;
    const modal=new bootstrap.Modal(document.getElementById('contractDetailModal'));
    document.getElementById('contractDetailTitle').textContent='Contract '+c.number;
    document.getElementById('contractDetailBody').innerHTML=`
      <div class="row g-4">
        <div class="col-md-6"><h6>Contract Header</h6><ul class="list-group small"><li class="list-group-item d-flex justify-content-between"><span>Contract Number</span><strong>${c.number}</strong></li><li class="list-group-item d-flex justify-content-between"><span>Property</span><strong>${c.property}</strong></li><li class="list-group-item d-flex justify-content-between"><span>Loan Amount</span><strong>${c.loan}</strong></li><li class="list-group-item d-flex justify-content-between"><span>Status</span><span class="badge ${c.status==='pending_signature'?'bg-warning':'bg-success'}">${c.status}</span></li></ul></div>
        <div class="col-md-6"><h6>Parties Involved</h6><ul class="list-group small"><li class="list-group-item">Customer: John Doe (customer@test.com)</li><li class="list-group-item">Seller: Jane Seller</li><li class="list-group-item">Bank: CRDB</li><li class="list-group-item">Lawyer: Advocate Smith</li></ul></div>
      </div>
      <div class="mt-4"><h6>Signature Status</h6><div class="d-flex gap-2 flex-wrap"><span class="badge ${c.signatures.customer==='signed'?'bg-success':'bg-warning'}">Customer: ${c.signatures.customer}</span><span class="badge ${c.signatures.seller==='signed'?'bg-success':'bg-warning'}">Seller: ${c.signatures.seller}</span><span class="badge ${c.signatures.bank==='signed'?'bg-success':'bg-warning'}">Bank: ${c.signatures.bank}</span><span class="badge ${c.signatures.lawyer==='signed'?'bg-success':'bg-warning'}">Lawyer: ${c.signatures.lawyer}</span></div></div>
      <div class="mt-4"><h6>Timeline</h6><ul class="list-group small"><li class="list-group-item">Contract Created: ${c.created}</li><li class="list-group-item">Signed Date: ${c.status==='signed'?'2025-01-22':'—'}</li><li class="list-group-item">Executed: —</li></ul></div>
      <div class="mt-4 d-flex gap-2"><button class="btn btn-primary" onclick="signContractModal(${c.id})">Sign Contract</button><button class="btn btn-outline-secondary" onclick="downloadContract(${c.id})">Download PDF</button></div>
    `;
    modal.show();
  };
  window.signContractModal=function(id){
    const c=allContracts.find(x=>x.id===id);
    if(c && c.signatures.customer==='signed'){
      showToast('You have already signed this contract','info');
      return;
    }
    document.getElementById('signContractSummary').innerHTML=`<strong>${c?c.number:'Contract'}</strong> - ${c?c.property:''}<br>Loan: ${c?c.loan:''}`;
    document.getElementById('signDateInput').value=new Date().toISOString().split('T')[0];
    document.getElementById('signAcceptCheck').checked=false;
    document.getElementById('signNameInput').value='';
    new bootstrap.Modal(document.getElementById('signContractModal')).show();
  };
  document.getElementById('signConfirmBtn')?.addEventListener('click', ()=>{
    if(!document.getElementById('signAcceptCheck').checked){ showToast('Please accept terms','warning'); return; }
    const name=document.getElementById('signNameInput').value.trim();
    if(!name){ showToast('Please enter your full name','warning'); return; }
    showToast('Contract signed successfully!','success');
    bootstrap.Modal.getInstance(document.getElementById('signContractModal')).hide();
  });
  window.downloadContract=function(id){ showToast('Downloading PDF for '+id,'info'); };

  fetchContracts();
})();
