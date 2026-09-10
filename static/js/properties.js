/* Properties - filtering, sorting, grid/list */
(function(){
  const API='/api/';
  function authHeaders(){ const t=localStorage.getItem('access'); const h={'Content-Type':'application/json'}; if(t) h['Authorization']='Bearer '+t; return h; }
  let allProps=[];
  let currentView='grid';
  let currentPage=1;
  const perPage=6;

  const searchEl=document.getElementById('propSearchInput');
  const typeEl=document.getElementById('propTypeFilter');
  const bedEl=document.getElementById('propBedFilter');
  const locEl=document.getElementById('propLocationFilter');
  const sortEl=document.getElementById('propSort');
  const minEl=document.getElementById('propMinPrice');
  const maxEl=document.getElementById('propMaxPrice');
  const container=document.getElementById('propertiesContainer');
  const totalEl=document.getElementById('statTotal');
  const availEl=document.getElementById('statAvailable');
  const soldEl=document.getElementById('statSold');
  const reviewEl=document.getElementById('statReview');
  const infoEl=document.getElementById('propPaginationInfo');
  const pagination=document.getElementById('propPagination');

  async function fetchProps(){
    try{
      const res=await fetch(API+'properties/', {headers: authHeaders()});
      const data=await res.json();
      allProps=Array.isArray(data)?data:(data.results||[]);
      // Populate locations
      if(locEl){
        const locs=[...new Set(allProps.map(p=>p.location).filter(Boolean))];
        locs.forEach(l=>{
          const o=document.createElement('option'); o.value=l; o.textContent=l; locEl.appendChild(o);
        });
      }
      updateStats();
      render();
    }catch(e){ container.innerHTML=`<div class="alert alert-danger">Failed: ${e.message}</div>`; }
  }

  function updateStats(){
    if(totalEl) totalEl.textContent=allProps.length;
    if(availEl) availEl.textContent=allProps.filter(p=>p.status==='available').length;
    if(soldEl) soldEl.textContent=allProps.filter(p=>p.status==='sold').length;
    if(reviewEl) reviewEl.textContent=allProps.filter(p=>p.status==='pending').length;
  }

  function getFiltered(){
    let arr=[...allProps];
    const q=(searchEl?searchEl.value:'').toLowerCase().trim();
    const type=typeEl?typeEl.value:'all';
    const bed=bedEl?bedEl.value:'any';
    const loc=locEl?locEl.value:'all';
    const min=parseFloat(minEl?minEl.value:'')||0;
    const max=parseFloat(maxEl?maxEl.value:'')||Infinity;
    const sort=sortEl?sortEl.value:'newest';
    if(q) arr=arr.filter(p=> (p.title+' '+p.location+' '+(p.description||'')).toLowerCase().includes(q));
    if(type!=='all') arr=arr.filter(p=>p.property_type===type);
    if(bed!=='any') arr=arr.filter(p=>parseInt(p.bedrooms)>=parseInt(bed));
    if(loc!=='all') arr=arr.filter(p=>p.location===loc);
    arr=arr.filter(p=>{ const price=parseFloat(p.price); return price>=min && price<=max; });
    if(sort==='newest') arr.sort((a,b)=>new Date(b.created_at)-new Date(a.created_at));
    else if(sort==='price_low') arr.sort((a,b)=>parseFloat(a.price)-parseFloat(b.price));
    else if(sort==='price_high') arr.sort((a,b)=>parseFloat(b.price)-parseFloat(a.price));
    return arr;
  }

  function render(){
    const arr=getFiltered();
    const total=arr.length;
    const totalPages=Math.ceil(total/perPage)||1;
    if(currentPage>totalPages) currentPage=1;
    const start=(currentPage-1)*perPage;
    const paged=arr.slice(start, start+perPage);
    if(infoEl) infoEl.textContent=`Showing ${total?start+1:0}-${Math.min(start+perPage,total)} of ${total} properties`;
    if(pagination){
      let html='';
      html+=`<li class="page-item ${currentPage===1?'disabled':''}"><a class="page-link" href="#" data-page="${currentPage-1}">Previous</a></li>`;
      for(let i=1;i<=Math.min(totalPages,4);i++){
        html+=`<li class="page-item ${i===currentPage?'active':''}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
      }
      html+=`<li class="page-item ${currentPage===totalPages?'disabled':''}"><a class="page-link" href="#" data-page="${currentPage+1}">Next</a></li>`;
      pagination.innerHTML=html;
      pagination.querySelectorAll('a').forEach(a=>a.addEventListener('click', e=>{ e.preventDefault(); const p=parseInt(a.dataset.page); if(p>=1&&p<=totalPages){ currentPage=p; render(); }}));
    }
    if(!paged.length){
      container.innerHTML='<div class="col-12 text-center py-5"><i class="bi bi-houses" style="font-size:48px;color:#cbd5e0"></i><p class="text-muted mt-3">No properties match your filters.</p></div>';
      container.className='row g-4';
      return;
    }
     const isWebsite = !!document.querySelector('header#header.fixed-top');
     container.className=currentView==='grid'?'row g-4 properties-grid':'row g-4 properties-list';
    container.innerHTML=paged.map(p=>{
      const price='TZS '+Number(p.price).toLocaleString();
      const cover=p.cover_image_url || p.image || (p.gallery && p.gallery.find(g=>g.is_cover)?.image) || (p.gallery && p.gallery[0]?.image) || '';
      let imgSrc=cover||''; if(imgSrc && imgSrc.startsWith('/')) imgSrc=window.location.origin+imgSrc;
      const img=imgSrc?`<img src="${imgSrc}" alt="${p.title}" style="height:180px;object-fit:cover;width:100%;border-radius:12px 12px 0 0" onerror="this.style.display='none'">`:`<div style="height:180px;background:linear-gradient(135deg,#0077B6 0%,#0A2B4E 100%);display:flex;align-items:center;justify-content:center;border-radius:12px 12px 0 0"><i class="bi bi-house" style="font-size:42px;color:#fff"></i></div>`;
      const statusBadge=p.status==='available'?'<span class="badge bg-success">Available</span>':p.status==='sold'?'<span class="badge bg-danger">Sold</span>':'<span class="badge bg-warning text-dark">'+p.status+'</span>';
      const verifiedBadge=p.seller_is_verified?'<span class="badge ms-1" style="font-size:10px; background:rgba(16,185,129,0.15); color:#10b981; border:1px solid rgba(16,185,129,0.3);">Verified</span>':'';
      let actions='';
      actions=`<button onclick="openPropModal(${p.id})" class="btn btn-sm" style="border-radius:8px;font-weight:600; border:1px solid var(--accent-color); color:var(--accent-color); background:transparent;"><i class="bi bi-eye me-1"></i> View Details</button><button onclick="openPropModal(${p.id}, true)" class="btn btn-sm" style="border-radius:8px; border:1px solid rgba(255,255,255,0.2); color:#e5e6ea;"><i class="bi bi-chat-dots me-1"></i> Contact</button><a href="/customer/apply/?property=${p.id}" class="btn btn-sm btn-primary" style="background:var(--accent-color);border-color:var(--accent-color);border-radius:8px;font-weight:600"><i class="bi bi-bank me-1"></i> Apply Mortgage</a>`;
      const cardStyle = isWebsite
        ? 'border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.08);transition:all .2s;box-shadow:0 4px 20px rgba(0,0,0,0.25);background:var(--surface-color);'
        : 'border-radius:16px;overflow:hidden;border:1px solid #eef2f7;transition:all .2s;box-shadow:0 2px 12px rgba(10,43,78,.06);background:#fff;';
      const titleColor = isWebsite ? '#eeeff7' : '#0A2B4E';
      const priceColor = isWebsite ? '#2dd4bf' : '#0077B6';
      const mutedColor = isWebsite ? '#8f95ab' : '#6c757d';
      const badgeStyle = isWebsite ? 'background:rgba(255,255,255,0.08); color:#e5e6ea; border:1px solid rgba(255,255,255,0.12);' : 'background:#f8f9fa; color:#212529; border:1px solid #dee2e6;';
      if(currentView==='list'){
        return `<div class="col-12"><div class="card" style="${cardStyle}"><div class="row g-0"><div class="col-md-4" style="min-height:200px">${img}</div><div class="col-md-8"><div class="card-body p-3"><div class="d-flex justify-content-between align-items-start"><h6 style="font-weight:700;color:${titleColor}">${p.title} ${verifiedBadge}</h6>${statusBadge}</div><div class="price" style="font-weight:800;color:${priceColor};font-size:18px">${price}</div><div class="small mb-2" style="color:${mutedColor}"><i class="bi bi-geo-alt me-1"></i> ${p.location} • ${p.bedrooms} Beds • ${p.bathrooms} Baths • ${p.area||'250'} sqm</div><p class="small" style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden; color:${mutedColor}">${(p.description||'No description').slice(0,120)}...</p><div class="mt-3 d-flex gap-2 flex-wrap">${actions}</div></div></div></div></div></div>`;
      } else {
        return `<div class="col-md-6 col-xl-4"><div class="card h-100" style="${cardStyle}"><div style="position:relative">${img}<div style="position:absolute;top:12px;left:12px">${statusBadge}</div><div style="position:absolute;top:12px;right:12px;background:rgba(255,255,255,.9);border-radius:8px;padding:4px 8px;font-size:12px;font-weight:700;color:#0A2B4E">★ 4.8</div></div><div class="card-body p-3"><h6 style="font-weight:700;color:${titleColor}" class="mb-1">${p.title} ${verifiedBadge}</h6><div class="price mb-1" style="font-weight:800;color:${priceColor}">${price}</div><div class="small mb-2" style="color:${mutedColor}"><i class="bi bi-geo-alt me-1"></i> ${p.location}</div><div class="d-flex gap-2 mb-3 flex-wrap"><span class="badge" style="${badgeStyle}"><i class="bi bi-door-open me-1"></i> ${p.bedrooms}</span><span class="badge" style="${badgeStyle}"><i class="bi bi-droplet me-1"></i> ${p.bathrooms}</span><span class="badge" style="${badgeStyle}">${p.area||'250'} sqm</span><span class="badge" style="${badgeStyle}">${p.property_type}</span></div><div class="d-flex gap-2 flex-wrap">${actions}</div></div></div></div>`;
      }
    }).join('');
  }

  // Modal for View Details - professional
  window.openPropModal=async function(id, openContact=false){
    const modalEl=document.getElementById('propDetailModal');
    const loading=document.getElementById('propModalLoading');
    const content=document.getElementById('propModalContent');
    const errEl=document.getElementById('propModalError');
    const modal=new bootstrap.Modal(modalEl);
    loading.classList.remove('d-none'); content.classList.add('d-none'); errEl.classList.add('d-none');
    modal.show();
    try{
      const res=await fetch(API+'properties/'+id+'/', {headers: authHeaders()});
      if(!res.ok) throw new Error('HTTP '+res.status);
      const p=await res.json();
      loading.classList.add('d-none'); content.classList.remove('d-none');
      document.getElementById('propModalTitle').textContent=p.title;
      document.getElementById('propModalName').textContent=p.title;
      document.getElementById('propModalLocation').innerHTML='<i class="bi bi-geo-alt me-1"></i> '+p.location;
      document.getElementById('propModalPrice').textContent='TZS '+Number(p.price).toLocaleString();
      document.getElementById('propModalType').textContent=p.property_type;
      const st=document.getElementById('propModalStatus'); st.textContent=p.status; st.className='badge '+(p.status==='available'?'bg-success':'bg-warning text-dark');
      document.getElementById('propModalBeds').textContent=p.bedrooms;
      document.getElementById('propModalBaths').textContent=p.bathrooms;
      document.getElementById('propModalArea').textContent=(p.area||'250')+' sqm';
      document.getElementById('propModalNapa').textContent=p.napa||'-';
      document.getElementById('propModalDesc').textContent=p.description||'No description';
      // Seller
      const sellerName=p.seller_name||'Seller';
      document.getElementById('propModalSellerName').textContent=sellerName;
      document.getElementById('propModalSellerEmail').textContent=p.seller_email||'-';
      document.getElementById('propModalSellerPhone').textContent=p.seller_phone||'-';
      const av=document.getElementById('propModalSellerAvatar');
      const initials=p.seller_initials||sellerName.charAt(0).toUpperCase();
      if(p.seller_avatar){ let url=p.seller_avatar; if(url.startsWith('/')) url=window.location.origin+url; av.innerHTML=`<img src="${url}" style="width:48px;height:48px;border-radius:50%;object-fit:cover" onerror="this.outerHTML='<span style=\\'width:48px;height:48px;border-radius:50%;background:#0077B6;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800\\'>${initials}</span>'">`; } else av.textContent=initials;
      const verif=document.getElementById('propModalSellerVerified'); if(p.seller_is_verified){ verif.textContent='Verified ✅'; verif.className='badge bg-success'; } else { verif.textContent='Not Verified'; verif.className='badge bg-warning text-dark'; }
      // Gallery
      const cover=document.getElementById('propModalCover');
      const thumbs=document.getElementById('propModalThumbs');
      const gallery=p.gallery && p.gallery.length ? p.gallery : (p.image ? [{image:p.image,is_cover:true}] : []);
      let coverUrl=p.cover_image_url || p.image || (gallery[0]&& (gallery[0].image||gallery[0])) || '';
      if(coverUrl && coverUrl.startsWith('/')) coverUrl=window.location.origin+coverUrl;
      cover.src=coverUrl||'https://via.placeholder.com/800x320?text=No+Image';
      if(gallery.length){
        thumbs.innerHTML=gallery.map((g,i)=>{
          let url=g.image||g; if(typeof url!=='string') url=g.image; if(url && url.startsWith('/')) url=window.location.origin+url;
          return `<img src="${url}" style="width:70px;height:50px;object-fit:cover;border-radius:8px;cursor:pointer;border:2px solid ${g.is_cover?'#0077B6':'transparent'}" onclick="document.getElementById('propModalCover').src='${url}'">`;
        }).join('');
      } else thumbs.innerHTML='<small class="text-muted">No images</small>';
      // Buttons
      document.getElementById('propModalContactBtn').onclick=function(){
        const cm=new bootstrap.Modal(document.getElementById('propContactModal')); cm.show();
        const email=p.seller_email||''; const phone=(p.seller_phone||'').replace(/\s/g,'');
        document.getElementById('propContactEmailText').textContent=email||'-';
        document.getElementById('propContactPhoneText').textContent=phone||'-';
        document.getElementById('propContactEmail').href=email? 'mailto:'+email+'?subject='+encodeURIComponent('Inquiry about '+p.title)+'&body='+encodeURIComponent('Hello '+sellerName+',\n\nI am interested in '+p.title+' at '+p.location+' priced at TZS '+Number(p.price).toLocaleString()+'.') : '#';
        document.getElementById('propContactPhone').href=phone? 'tel:'+phone : '#';
      };
      document.getElementById('propModalApplyBtn').href='/customer/apply/?property='+p.id;
      if(openContact) setTimeout(()=> document.getElementById('propModalContactBtn').click(), 300);
    }catch(e){
      loading.classList.add('d-none'); errEl.classList.remove('d-none'); console.error(e);
    }
  };

  document.getElementById('propApplyFilters')?.addEventListener('click', ()=>{ currentPage=1; render(); });
  document.getElementById('propClearFilters')?.addEventListener('click', ()=>{
    if(searchEl) searchEl.value='';
    if(typeEl) typeEl.value='all';
    if(bedEl) bedEl.value='any';
    if(locEl) locEl.value='all';
    if(minEl) minEl.value='';
    if(maxEl) maxEl.value='';
    if(sortEl) sortEl.value='newest';
    currentPage=1; render();
  });
  document.getElementById('gridViewBtn')?.addEventListener('click', ()=>{ currentView='grid'; render(); });
  document.getElementById('listViewBtn')?.addEventListener('click', ()=>{ currentView='list'; render(); });
  [searchEl,typeEl,bedEl,locEl,sortEl,minEl,maxEl].forEach(el=>el&&el.addEventListener('change', ()=>{ currentPage=1; render(); }));
  if(searchEl) searchEl.addEventListener('input', ()=>{ currentPage=1; render(); });

  // Pre-fill filters from URL query params (e.g., /properties/?property_type=house&q=...)
  try{
    const params=new URLSearchParams(window.location.search);
    const qp=params.get('property_type')||params.get('type');
    if(qp && typeEl){ typeEl.value=qp; }
    const qq=params.get('q')||params.get('search');
    if(qq && searchEl){ searchEl.value=qq; }
    const qloc=params.get('location');
    if(qloc && locEl){ /* loc options not yet populated, set after fetch via timeout */ setTimeout(()=>{ if([...locEl.options].some(o=>o.value===qloc)) locEl.value=qloc; render(); },800); }
  }catch(e){}

  fetchProps();
})();
