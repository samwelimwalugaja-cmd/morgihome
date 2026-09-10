/* Seller My Properties - Hatua 6 + 7 Edit/Delete */
(function(){
  function getToken(){ return localStorage.getItem('access'); }
  function authHeaders(){ const t=getToken(); const h={'Content-Type':'application/json'}; if(t) h['Authorization']='Bearer '+t; return h; }
  function authHeadersNoJson(){ const t=getToken(); const h={}; if(t) h['Authorization']='Bearer '+t; return h; }
  const grid=document.getElementById('spGrid');
  const empty=document.getElementById('spEmpty');
  const stats=document.getElementById('spStats');
  if(!grid) return;
  // Support header search ?q=
  function getQuery(){ try{ return new URLSearchParams(window.location.search).get('q')||'' }catch(e){ return '' } }
  async function load(){
    grid.innerHTML='<div class="col-12 text-center py-5"><div class="spinner-border text-primary"></div></div>';
    try{
      const res=await fetch('/api/properties/', {headers: authHeaders()});
      const data=await res.json();
      let arr=Array.isArray(data)?data:(data.results||[]);
      const user=JSON.parse(localStorage.getItem('user')||'{}');
      // Seller anaona nyumba zake tu (sio za seller mwingine) - kama alivyoomba
      let myProps=arr.filter(p=> String(p.seller)===String(user.id));
      // Header search filter ?q=
      const q=getQuery().toLowerCase();
      if(q){ myProps=myProps.filter(p=> (p.title||'').toLowerCase().includes(q) || (p.location||'').toLowerCase().includes(q) || (p.description||'').toLowerCase().includes(q)); }
      const total=myProps.length;
      const available=myProps.filter(p=>p.status==='available').length;
      const sold=myProps.filter(p=>p.status==='sold').length;
      const pending=myProps.filter(p=>p.status==='pending').length;
      if(stats) stats.innerHTML=`<span class="badge bg-primary me-1">Total: ${total}</span> <span class="badge bg-success me-1">Available: ${available}</span> <span class="badge bg-secondary me-1">Sold: ${sold}</span> <span class="badge bg-warning text-dark">Pending: ${pending}</span> ${q?`<span class="badge bg-info ms-2">Search: "${q}"</span>`:''}`;
      if(!total){ grid.classList.add('d-none'); empty.classList.remove('d-none'); grid.innerHTML=''; if(q) empty.innerHTML=`<div class="card mx-auto" style="max-width:480px"><div class="card-body text-center py-4"><i class="bi bi-search" style="font-size:48px;color:#cbd5e0"></i><h6 class="mt-3">No results for "${q}"</h6><p class="text-muted small">No properties match your search.</p><a href="/seller/properties/" class="btn btn-outline-secondary btn-sm">Clear search</a></div></div>`; return; }
      empty.classList.add('d-none'); grid.classList.remove('d-none');
      grid.innerHTML=myProps.map(p=>{
        let img=p.cover_image_url || p.image || (p.gallery && p.gallery.find(g=>g.is_cover)?.image) || (p.gallery && p.gallery[0]?.image) || ''; if(img && img.startsWith('/')) img=window.location.origin+img;
        const imgHtml=img?`<img src="${img}" class="card-img-top" style="height:160px;object-fit:cover" onerror="this.style.display='none'">`:`<div style="height:160px;background:#eef2f7;display:flex;align-items:center;justify-content:center"><i class="bi bi-house" style="font-size:32px;color:#a0aec0"></i></div>`;
        const isMine = !user.id || p.seller==user.id;
        return `<div class="col-md-6 col-xl-4"><div class="card h-100" style="${isMine?'border-left:4px solid #0077B6':''}">${imgHtml}<div class="card-body"><h6 class="card-title mb-1">${p.title} ${isMine?'<span class="badge bg-primary ms-1">Yangu</span>':''}</h6><p class="text-muted small mb-1"><i class="bi bi-geo-alt me-1"></i>${p.location}</p><p class="fw-bold mb-1" style="color:#0077B6">${Number(p.price).toLocaleString()} TZS</p><p class="small text-muted">${(p.description||'').slice(0,80)}...</p><div class="d-flex gap-2 mt-2 flex-wrap"><span class="badge bg-light text-dark border">${p.bedrooms} Beds</span><span class="badge bg-light text-dark border">${p.bathrooms} Baths</span><span class="badge ${p.status==='available'?'bg-success':'bg-warning'}">${p.status}</span></div><div class="mt-3 d-flex gap-2 flex-wrap"><button class="btn btn-sm btn-outline-primary" onclick="editProp(${p.id})"><i class="bi bi-pencil me-1"></i> Edit</button><button class="btn btn-sm btn-outline-danger" onclick="deleteProp(${p.id})"><i class="bi bi-trash me-1"></i> Delete</button><a href="/seller/buyers/" class="btn btn-sm btn-outline-secondary"><i class="bi bi-eye me-1"></i> Buyers</a></div></div></div></div>`;
      }).join('');
    }catch(e){
      grid.innerHTML=`<div class="col-12"><div class="alert alert-danger">Imeshindwa kupakia: ${e.message}</div></div>`;
      if(window.showToast) showToast('Imeshindwa kupakia nyumba: '+e.message,'error');
    }
  }
  window.editProp=async function(id){
    const modalEl=document.getElementById('spEditModal');
    const body=document.getElementById('spEditBody');
    const modal=new bootstrap.Modal(modalEl);
    body.innerHTML='<div class="text-center py-3"><div class="spinner-border text-primary"></div></div>';
    modal.show();
    try{
      const res=await fetch('/api/properties/'+id+'/', {headers: authHeaders()});
      const p=await res.json();
      body.innerHTML=`
        <div class="row g-3">
          <div class="col-md-6"><label class="form-label">Title *</label><input id="editTitle" class="form-control" value="${p.title||''}"></div>
          <div class="col-md-6"><label class="form-label">Price *</label><input id="editPrice" type="number" class="form-control" value="${p.price||''}"></div>
          <div class="col-md-6"><label class="form-label">Location *</label><input id="editLocation" class="form-control" value="${p.location||''}"></div>
          <div class="col-md-6"><label class="form-label">Area *</label><input id="editArea" type="number" class="form-control" value="${p.area||''}"></div>
          <div class="col-md-4"><label class="form-label">Type</label><select id="editType" class="form-select"><option value="house" ${p.property_type==='house'?'selected':''}>House</option><option value="apartment" ${p.property_type==='apartment'?'selected':''}>Apartment</option><option value="land" ${p.property_type==='land'?'selected':''}>Land</option><option value="commercial" ${p.property_type==='commercial'?'selected':''}>Commercial</option></select></div>
          <div class="col-md-4"><label class="form-label">Status</label><select id="editStatus" class="form-select"><option value="available" ${p.status==='available'?'selected':''}>Available</option><option value="sold" ${p.status==='sold'?'selected':''}>Sold</option><option value="pending" ${p.status==='pending'?'selected':''}>Pending</option><option value="rented" ${p.status==='rented'?'selected':''}>Rented</option></select></div>
          <div class="col-md-4"><label class="form-label">Bedrooms</label><input id="editBeds" type="number" class="form-control" value="${p.bedrooms||0}"></div>
          <div class="col-12"><label class="form-label">Description</label><textarea id="editDesc" class="form-control" rows="3">${p.description||''}</textarea></div>
          <div class="col-12"><label class="form-label">New Image (optional)</label><input id="editImage" type="file" class="form-control" accept=".jpg,.jpeg,.png"></div>
        </div>
        <div class="d-flex justify-content-end gap-2 mt-3"><button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button class="btn btn-primary" onclick="submitEdit(${p.id})" style="background:#0077B6;border-color:#0077B6">Update Property</button></div>
      `;
    }catch(e){ body.innerHTML=`<div class="alert alert-danger">${e.message}</div>`; }
  };
  window.submitEdit=async function(id){
    try{
      const fd=new FormData();
      fd.append('title', document.getElementById('editTitle').value);
      fd.append('price', document.getElementById('editPrice').value);
      fd.append('location', document.getElementById('editLocation').value);
      fd.append('area', document.getElementById('editArea').value);
      fd.append('property_type', document.getElementById('editType').value);
      fd.append('status', document.getElementById('editStatus').value);
      fd.append('bedrooms', document.getElementById('editBeds').value);
      fd.append('description', document.getElementById('editDesc').value);
      const f=document.getElementById('editImage').files[0];
      if(f) fd.append('image', f);
      const res=await fetch('/api/properties/'+id+'/', {method:'PATCH', headers: authHeadersNoJson(), body: fd});
      const text=await res.text();
      if(res.ok){
        if(window.showToast) showToast('House imehaririwa kikamilifu! ✅','success','Imfanikiwa');
        bootstrap.Modal.getInstance(document.getElementById('spEditModal')).hide();
        load();
      } else {
        if(window.showToast) showToast('Imeshindwa kuhariri: '+text.slice(0,200),'error','Imeshindwa ❌');
        else alert(text);
      }
    }catch(e){ if(window.showToast) showToast('Imeshindwa: '+e.message,'error'); }
  };
  window.deleteProp=async function(id){
    if(!confirm('Are you sure you want to kufuta nyumba #'+id+'?')) return;
    try{
      const res=await fetch('/api/properties/'+id+'/', {method:'DELETE', headers: authHeaders()});
      if(res.ok || res.status===204){
        if(window.showToast) showToast('House imefutwa kikamilifu! ✅','success');
        load();
      } else {
        const t=await res.text();
        if(window.showToast) showToast('Imeshindwa kufuta: '+t.slice(0,200),'error');
      }
    }catch(e){ if(window.showToast) showToast('Imeshindwa: '+e.message,'error'); }
  };
  load();
})();
