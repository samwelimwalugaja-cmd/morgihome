// MorgiHome PlainAdmin helpers - sidebar + avatar fallback
(function(){
  // Preloader
  window.addEventListener('load', function(){
    var p=document.getElementById('preloader');
    if(p) p.style.display='none';
  });

  // Sidebar toggle (copy from demo main.js but defensive)
  var sidebarNavWrapper=document.querySelector('.sidebar-nav-wrapper');
  var mainWrapper=document.querySelector('.main-wrapper');
  var menuToggleButton=document.querySelector('#menu-toggle');
  var overlay=document.querySelector('.overlay');
  if(menuToggleButton && sidebarNavWrapper){
    var icon=menuToggleButton.querySelector('i');
    menuToggleButton.addEventListener('click', function(){
      sidebarNavWrapper.classList.toggle('active');
      if(overlay) overlay.classList.add('active');
      if(mainWrapper) mainWrapper.classList.toggle('active');
      if(icon){
        if(icon.classList.contains('lni-chevron-left')){icon.classList.remove('lni-chevron-left');icon.classList.add('lni-menu');}
        else if(icon.classList.contains('lni-menu')){icon.classList.remove('lni-menu');icon.classList.add('lni-chevron-left');}
      }
    });
  }
  if(overlay && sidebarNavWrapper){
    overlay.addEventListener('click', function(){
      sidebarNavWrapper.classList.remove('active');
      overlay.classList.remove('active');
      if(mainWrapper) mainWrapper.classList.remove('active');
    });
  }

  // Header shadow on scroll
  window.addEventListener('scroll', function(){
    var header=document.querySelector('.header');
    if(!header) return;
    if(window.scrollY>0) header.style.boxShadow='0px 0px 30px 0px rgba(200,208,216,0.30)';
    else header.style.boxShadow='none';
  });
})();

// Avatar fallback helpers - globally available
function getInitials(name){
  if(!name) return 'M';
  name=name.trim();
  if(!name) return 'M';
  return name.charAt(0).toUpperCase();
}
function avatarHtml(user, size){
  size=size||'md';
  var initials=user.initials || getInitials(user.username || user.first_name || 'M');
  var hasImage=!!(user.avatar_url || user.profile_image);
  var cls='avatar-initial avatar-initial--'+size;
  if(hasImage){
    var url=user.avatar_url || user.profile_image;
    var wh = size==='lg' ? '96px' : size==='sidebar' ? '64px' : '36px';
    // MOJA TU: kama picha ipo onyesha picha pekee, herufi isionekane. onerror badilisha na herufi
    var img='<img src="'+url+'" alt="'+(user.username||'')+'" class="rounded-circle" style="width:'+wh+';height:'+wh+';object-fit:cover;border-radius:50%;" onerror="this.outerHTML=\'<span class=\\\''+cls+'\\\'\'>'+initials+'</span>\'">';
    return img;
  } else {
    return '<span class="'+cls+'">'+initials+'</span>';
  }
}
function renderAvatarInto(el, user, size){
  if(!el) return;
  el.innerHTML=avatarHtml(user,size);
}
// For img elements with fallback to initials
function applyAvatarFallback(imgEl, user, size){
  if(!imgEl) return;
  var hasImage=!!(user.avatar_url || user.profile_image);
  if(hasImage){
    imgEl.src=user.avatar_url || user.profile_image;
    imgEl.style.display='';
    // hide sibling initials if exists
    var sib=imgEl.nextElementSibling;
    if(sib && sib.classList.contains('avatar-initial')) sib.style.display='none';
    imgEl.onerror=function(){
      imgEl.style.display='none';
      if(sib) sib.style.display='inline-flex';
    };
  } else {
    imgEl.style.display='none';
    var parent=imgEl.parentElement;
    var initials=user.initials || getInitials(user.username||'M');
    var cls='avatar-initial avatar-initial--'+(size||'md');
    var existing=parent.querySelector('.avatar-initial');
    if(!existing){
      var span=document.createElement('span');
      span.className=cls;
      span.textContent=initials;
      parent.appendChild(span);
    } else {
      existing.textContent=initials;
      existing.style.display='inline-flex';
    }
  }
}
