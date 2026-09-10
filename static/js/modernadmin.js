// ModernAdmin helpers - avatar fallback + theme + sidebar
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
    var wh = size==='lg' ? '96px' : size==='header' ? '36px' : '36px';
    return '<img src="'+url+'" alt="'+(user.username||'')+'" class="rounded-circle" style="width:'+wh+';height:'+wh+';object-fit:cover;border-radius:50%;" onerror="this.outerHTML=\'<span class=\\\''+cls+'\\\'\'>'+initials+'</span>\'">';
  } else {
    return '<span class="'+cls+'">'+initials+'</span>';
  }
}
// Theme toggle - ModernAdmin uses data-theme="dark"
(function(){
  const html=document.documentElement;
  const saved=localStorage.getItem('mh-theme') || 'light';
  html.setAttribute('data-theme', saved);
  document.addEventListener('DOMContentLoaded', ()=>{
    document.querySelectorAll('.theme-toggle').forEach(btn=>{
      btn.addEventListener('click', (e)=>{
        e.preventDefault();
        const cur=html.getAttribute('data-theme')==='dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', cur);
        localStorage.setItem('mh-theme', cur);
      });
    });
  });
})();
