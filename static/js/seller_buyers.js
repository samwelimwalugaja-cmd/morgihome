/* Seller Buyers - Hatua 8 - Customers waliovutiwa */
(function(){
  function getToken(){ return localStorage.getItem('access'); }
  function authHeaders(){ const t=getToken(); const h={'Content-Type':'application/json'}; if(t) h['Authorization']='Bearer '+t; return h; }
  const tbody=document.getElementById('buyersBody');
  if(!tbody) return;
  async function load(){
    tbody.innerHTML='<tr><td colspan="6" class="text-center py-3"><div class="spinner-border text-primary"></div></td></tr>';
    try{
      const res=await fetch('/api/mortgages/', {headers: authHeaders()});
      const data=await res.json();
      const arr=Array.isArray(data)?data:(data.results||[]);
      if(!arr.length){
        tbody.innerHTML='<tr><td colspan="6" class="text-center text-muted py-4">No buyers yet</td></tr>';
        return;
      }
      tbody.innerHTML=arr.map(m=>{
        const cust=m.customer_name||'Customer #'+m.customer;
        const verif=m.customer_is_verified ? '<span class="badge bg-success ms-1">Verified ✅</span>' : '<span class="badge bg-warning text-dark ms-1">Not Verified</span>';
        const prop=m.property_details?m.property_details.title:'Property #'+m.property;
        const bank=m.bank_details?m.bank_details.name:'-';
        return `<tr>
          <td>${cust} ${verif}</td>
          <td>${m.customer || '-'}</td>
          <td>-</td>
          <td>${prop}</td>
          <td>${new Date(m.created_at).toLocaleDateString()}</td>
          <td><span class="badge bg-light text-dark border">${m.status}</span><br><small class="text-muted">${bank}</small></td>
        </tr>`;
      }).join('');
      // silent success - no toast needed
    }catch(e){
      tbody.innerHTML=`<tr><td colspan="6"><div class="alert alert-danger small">Failed to load: ${e.message}</div></td></tr>`;
      if(window.showToast) showToast('Failed to load buyers: '+e.message,'error');
    }
  }
  load();
})();
