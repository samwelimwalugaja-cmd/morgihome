/* Property Detail - Professional */
(function(){
  function getToken(){ return localStorage.getItem('access'); }
  function authHeaders(){ const t=getToken(); const h={'Content-Type':'application/json'}; if(t) h['Authorization']='Bearer '+t; return h; }
  function getId(){
    const parts=window.location.pathname.split('/').filter(Boolean);
    const last=parts[parts.length-1];
    if(/^\d+$/.test(last)) return last;
    const q=new URLSearchParams(window.location.search).get('id')||new URLSearchParams(window.location.search).get('property');
    return q;
  }
  const id=getId();
  const loading=document.getElementById('detailLoading');
  const content=document.getElementById('detailContent');
  const errorEl=document.getElementById('detailError');
  if(!id){
    if(loading) loading.classList.add('d-none');
    if(errorEl) errorEl.classList.remove('d-none');
    return;
  }
  async function load(){
    try{
      const res=await fetch('/api/properties/'+id+'/', {headers: authHeaders()});
      if(!res.ok) throw new Error('HTTP '+res.status);
      const p=await res.json();
      if(loading) loading.classList.add('d-none');
      if(content) content.classList.remove('d-none');
      // Title & breadcrumb
      document.getElementById('detailTitle').textContent=p.title;
      document.getElementById('detailBreadcrumb').textContent=p.title;
      document.getElementById('detailName').textContent=p.title;
      document.getElementById('detailLocation').innerHTML='<i class="bi bi-geo-alt me-1"></i> '+p.location;
      document.getElementById('detailLocation2').textContent=p.location;
      document.getElementById('detailPrice').textContent='TZS '+Number(p.price).toLocaleString();
      document.getElementById('detailTypeBadge').textContent=p.property_type;
      const statusEl=document.getElementById('detailStatusBadge');
      statusEl.textContent=p.status.charAt(0).toUpperCase()+p.status.slice(1);
      statusEl.className='badge '+(p.status==='available'?'bg-success':'bg-warning text-dark')+' ms-1';
      document.getElementById('detailStatusText').textContent=p.status;
      if(p.seller_is_verified) document.getElementById('detailVerifiedBadge').classList.remove('d-none');
      // Features
      document.getElementById('detailBeds').textContent=p.bedrooms;
      document.getElementById('detailBaths').textContent=p.bathrooms;
      document.getElementById('detailArea').textContent=(p.area||'250')+' sqm';
      document.getElementById('detailNapa').textContent=p.napa||'-';
      document.getElementById('detailDesc').textContent=p.description||'No description provided.';
      document.getElementById('detailDate').textContent=new Date(p.created_at).toLocaleDateString();
      // Gallery
      const cover=document.getElementById('detailCover');
      const thumbs=document.getElementById('detailThumbs');
      const gallery=p.gallery && p.gallery.length ? p.gallery : (p.image ? [{image:p.image, is_cover:true}] : []);
      // Normalize gallery images to urls
      const urls=gallery.map(g=> g.image || g).filter(Boolean);
      // If cover_image_url exists and not in gallery, use it as first
      const coverUrl=p.cover_image_url || p.image;
      let coverToShow = coverUrl || (urls[0] ? (typeof urls[0]==='string'?urls[0]:urls[0].image) : '');
      if(coverToShow && coverToShow.startsWith('/')) coverToShow=window.location.origin+coverToShow;
      if(cover) cover.src=coverToShow || 'https://via.placeholder.com/800x420?text=No+Image';
      if(thumbs){
        if(urls.length){
          thumbs.innerHTML=urls.map((g,idx)=>{
            let url=g.image||g;
            if(typeof url!=='string') url=g.image;
            if(url && url.startsWith('/')) url=window.location.origin+url;
            const isCover=g.is_cover || (coverUrl && url===coverToShow);
            return `<img src="${url}" alt="thumb ${idx+1}" class="${isCover?'active':''}" onclick="document.getElementById('detailCover').src='${url}'" title="${isCover?'Cover':''}">`;
          }).join('');
        } else {
          thumbs.innerHTML='<small class="text-muted">No additional images</small>';
        }
      }
      // Seller
      const sellerName=p.seller_name||'Seller';
      const sellerEmail=p.seller_email||'';
      const sellerPhone=p.seller_phone||'';
      document.getElementById('sellerName').textContent=sellerName;
      document.getElementById('sellerEmail').textContent=sellerEmail||'-';
      document.getElementById('sellerPhone').textContent=sellerPhone||'-';
      document.getElementById('contactEmailText').textContent=sellerEmail||'-';
      document.getElementById('contactPhoneText').textContent=sellerPhone||'-';
      // Avatar
      const avatarEl=document.getElementById('sellerAvatar');
      const initials=p.seller_initials||sellerName.charAt(0).toUpperCase();
      const avatarUrl=p.seller_avatar;
      if(avatarUrl){
        let url=avatarUrl; if(url.startsWith('/')) url=window.location.origin+url;
        avatarEl.innerHTML=`<img src="${url}" style="width:56px;height:56px;border-radius:50%;object-fit:cover" onerror="this.outerHTML='<span style=\\'width:56px;height:56px;border-radius:50%;background:rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:800\\'>${initials}</span>'">`;
      } else {
        avatarEl.textContent=initials;
      }
      const verifiedEl=document.getElementById('sellerVerified');
      if(p.seller_is_verified) verifiedEl.textContent='Verified ✅'; else verifiedEl.textContent='Not Verified';
      if(p.seller_email) document.getElementById('sellerEmailVerified').classList.remove('d-none');
      // Contact buttons
      const emailBtn=document.getElementById('contactEmailBtn');
      const phoneBtn=document.getElementById('contactPhoneBtn');
      if(sellerEmail){
        emailBtn.href='mailto:'+sellerEmail+'?subject='+encodeURIComponent('Inquiry about '+p.title)+'&body='+encodeURIComponent('Hello '+sellerName+',\n\nI am interested in your property "'+p.title+'" at '+p.location+' priced at TZS '+Number(p.price).toLocaleString()+'. Please provide more details.\n\nBest regards');
      } else emailBtn.classList.add('disabled');
      if(sellerPhone){
        // Normalize phone for tel:
        let tel=sellerPhone.replace(/\s/g,'');
        phoneBtn.href='tel:'+tel;
      } else phoneBtn.classList.add('disabled');
      // Apply mortgage
      const applyBtn=document.getElementById('btnApplyMortgage');
      applyBtn.onclick=function(){
        // Pre-fill mortgage form with property id
        window.location.href='/customer/apply/?property='+p.id;
      };
      document.getElementById('btnContact').onclick=function(){
        const modal=new bootstrap.Modal(document.getElementById('contactModal'));
        modal.show();
      };
    }catch(e){
      console.error(e);
      if(loading) loading.classList.add('d-none');
      if(errorEl) errorEl.classList.remove('d-none');
      if(window.showToast) showToast('Failed to load property: '+e.message,'error');
    }
  }
  load();
})();
