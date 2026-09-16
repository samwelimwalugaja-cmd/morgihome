/* Seller Add Property - Step 5 */
(function(){
  const form=document.getElementById('sellerAddForm');
  if(!form) return;
  function getToken(){ return localStorage.getItem('access'); }
  function authHeaders(){ const t=getToken(); const h={}; if(t) h['Authorization']='Bearer '+t; return h; }
  const preview=document.getElementById('spPreview');
  const coverHelp=document.getElementById('spCoverHelp');
  const imgInput=document.getElementById('spImages');
  let coverIndex=0;
  let currentFiles=[];
  function renderPreview(){
    if(!currentFiles.length){ preview.innerHTML=''; if(coverHelp) coverHelp.classList.add('d-none'); return; }
    if(coverHelp) coverHelp.classList.remove('d-none');
    preview.innerHTML=currentFiles.map((f,idx)=>{
      if(f.size>5242880) return `<div class="col-6 col-md-2"><div class="alert alert-danger small p-1">${f.name} large >5MB</div></div>`;
      const url=URL.createObjectURL(f);
      const isCover=idx===coverIndex;
      return `<div class="col-6 col-md-2"><div class="card ${isCover?'border-warning':''}" style="${isCover?'border:2px solid #FFC107;box-shadow:0 4px 12px rgba(255,193,7,.3)':''}"><img src="${url}" style="height:100px;object-fit:cover" class="card-img-top"><div class="card-body p-1 text-center"><small class="d-block text-truncate" style="font-size:10px">${f.name}</small><button type="button" class="btn btn-sm mt-1 ${isCover?'btn-warning':'btn-outline-secondary'}" onclick="setCover(${idx})" style="font-size:11px">${isCover?'★ Cover':'☆ Cover'}</button></div></div></div>`;
    }).join('');
  }
  if(imgInput){
    imgInput.addEventListener('change', e=>{
      currentFiles=Array.from(e.target.files).slice(0,5);
      if(e.target.files.length>5){ if(window.showToast) showToast('Uploaded >5, only the first 5 will be saved','warning'); }
      if(coverIndex>=currentFiles.length) coverIndex=0;
      renderPreview();
    });
  }
  window.setCover=function(idx){ coverIndex=idx; renderPreview(); if(window.showToast) showToast('Cover set: Image '+(idx+1),'info'); };
  function showAlert(type, msg){
    const el=document.getElementById('spAlert');
    if(el){ el.className='alert alert-'+(type==='success'?'success':type==='error'?'danger':type==='warning'?'warning':'info'); el.textContent=msg; el.classList.remove('d-none'); el.style.display='block'; el.scrollIntoView({behavior:'smooth',block:'center'}); }
    // also toast and browser alert as backup
    try{ if(window.showToast) showToast(msg, type==='success'?'success':type==='error'?'error':'info', type==='success'?'Success ✅':type==='error'?'Failed ❌':'Info'); }catch(e){}
    if(type==='error' || type==='success'){ try{ console.log('[SellerAdd]',type,msg); }catch(e){} }
  }
  form.addEventListener('submit', async e=>{
    e.preventDefault();
    console.log('SellerAdd submit triggered');
    const btn=document.getElementById('spSubmit');
    const orig=btn.innerHTML;
    const title=document.getElementById('spTitle').value.trim();
    const price=document.getElementById('spPrice').value;
    const location=document.getElementById('spLocation').value.trim();
    const area=document.getElementById('spArea').value;
    const desc=document.getElementById('spDesc').value.trim();
    if(!title || !price || !location || !area || !desc){ showAlert('warning','Please fill all required fields *'); return; }
    btn.disabled=true; btn.innerHTML='<span class="spinner-border spinner-border-sm me-2"></span> Sending...';
    try{
      const fd=new FormData();
      fd.append('title', title);
      fd.append('description', desc);
      fd.append('price', price);
      fd.append('location', location);
      fd.append('area', area);
      fd.append('napa', document.getElementById('spNapa') ? document.getElementById('spNapa').value.trim() : '');
      fd.append('property_type', document.getElementById('spType').value);
      fd.append('status', document.getElementById('spStatus').value);
      fd.append('bedrooms', document.getElementById('spBeds').value||0);
      fd.append('bathrooms', document.getElementById('spBaths').value||0);
      // 5 picha na cover index
      const files=currentFiles.slice(0,5);
      files.forEach(f=> fd.append('images', f));
      fd.append('cover_index', coverIndex);
      // backward compat: pia weka cover kama image kuu
      if(files[coverIndex]) fd.append('image', files[coverIndex]);
      const res=await fetch('/api/properties/', {method:'POST', headers: authHeaders(), body: fd});
      const text=await res.text();
      let data={}; try{ data=text?JSON.parse(text):{} }catch(e){ data={detail:text}; }
      if(res.ok || res.status===201){
        showAlert('success','Property added successfully! ✅ - Redirecting to listings...');
        setTimeout(()=> window.location.href='/seller/properties/', 1500);
      } else {
        const msg=data.title?data.title[0]: (data.price?data.price[0] : (data.napa?data.napa[0] : (data.detail||data.error||text.slice(0,300)||'Failed')));
        showAlert('error','Failed: '+(msg));
        console.error('Add property failed', res.status, text);
      }
    }catch(err){
      console.error(err);
      showAlert('error','Failed: '+(err.message||'Network error - please make sure you are logged in'));
    } finally { btn.disabled=false; btn.innerHTML=orig; }
  });
})();
