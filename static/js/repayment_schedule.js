/* Repayment Schedule JS */
(function(){
  const API='/api/';
  function authHeaders(){ const t=localStorage.getItem('access'); const h={'Content-Type':'application/json'}; if(t) h['Authorization']='Bearer '+t; return h; }
  let allSchedules=[];
  let currentPage=1, perPage=8;
  async function fetchSchedule(){
    // Kama element haipo (dashboard overview), usifanye kitu - kuepuka TypeError
    if(!document.getElementById('repTableBody')) return;
    // Try to get first approved mortgage
    try{
      const res=await fetch(API+'mortgages/', {headers: authHeaders()});
      const data=await res.json();
      const arr=Array.isArray(data)?data:(data.results||[]);
      const approved=arr.find(a=>a.status==='approved' || a.status==='disbursed') || arr[0];
      if(!approved){ const el=document.getElementById('repTableBody'); if(el) el.innerHTML='<tr><td colspan="6" class="text-center text-muted py-4">No approved mortgage found. Repayment schedule generated after approval.</td></tr>'; return; }
      const repRef=document.getElementById('repRef'); if(repRef) repRef.textContent='#APP-'+String(approved.id).padStart(4,'0');
      const repTotal=document.getElementById('repTotalLoan'); if(repTotal) repTotal.textContent='TZS '+Number(approved.loan_amount).toLocaleString();
      const repMonthly=document.getElementById('repMonthly'); if(repMonthly) repMonthly.textContent='TZS '+Number(approved.monthly_installment||0).toLocaleString();
      const repPeriod=document.getElementById('repPeriod'); if(repPeriod) repPeriod.textContent=approved.repayment_period+' months';
      // Fetch schedule
      const res2=await fetch(API+'mortgages/'+approved.id+'/repayment_schedule/', {headers: authHeaders()});
      if(res2.ok){
        const sched=await res2.json();
        allSchedules=sched;
        // Calculate paid/balance
        const paid=sched.filter(s=>s.status==='paid').reduce((s, r)=>s+parseFloat(r.amount_paid||0),0);
        const balance=sched.length?parseFloat(sched[sched.length-1].balance_remaining):0;
        const repPaid=document.getElementById('repPaid'); if(repPaid) repPaid.textContent='TZS '+paid.toLocaleString();
        const repBal=document.getElementById('repBalance'); if(repBal) repBal.textContent='TZS '+balance.toLocaleString();
        // Next payment
        const next=sched.find(s=>s.status==='pending' || s.status==='overdue');
        const nextEl=document.getElementById('repNextInfo'); if(next && nextEl) nextEl.textContent=`Installment: #${next.installment_number} - Due Date: ${next.due_date} | Amount: TZS ${Number(next.amount_due).toLocaleString()} | Status: ${next.status}`;
        render();
        renderHistory(sched);
      } else {
        // Fallback generate mock schedule client side
        generateMock(approved);
      }
    }catch(e){ console.error(e); }
  }
  function generateMock(app){
    const months=parseInt(app.repayment_period)||12;
    const amount=parseFloat(app.monthly_installment)||500000;
    let balance=parseFloat(app.loan_amount);
    allSchedules=[];
    const today=new Date();
    for(let i=1;i<=Math.min(months,120);i++){
      const due=new Date(today); due.setMonth(due.getMonth()+i);
      const status=i<=5?'paid':(i===6?'pending':'pending');
      const paid=status==='paid'?amount:0;
      balance=Math.max(0,balance - (status==='paid'? amount*0.8 : 0));
      allSchedules.push({installment_number:i, due_date:due.toISOString().split('T')[0], amount_due:amount, amount_paid:paid, balance_remaining:balance, status});
    }
    render();
  }
  function render(){
    const tbody=document.getElementById('repTableBody');
    if(!tbody) return;
    const q=(document.getElementById('repSearch')?.value||'').toLowerCase();
    const filter=document.getElementById('repStatusFilter')?.value||'all';
    let filtered=[...allSchedules];
    if(q) filtered=filtered.filter(s=>String(s.installment_number).includes(q) || s.due_date.includes(q));
    if(filter!=='all') filtered=filtered.filter(s=>s.status===filter);
    const total=filtered.length;
    const totalPages=Math.ceil(total/perPage)||1;
    if(currentPage>totalPages) currentPage=1;
    const start=(currentPage-1)*perPage;
    const paged=filtered.slice(start,start+perPage);
    document.getElementById('repPaginationInfo').textContent=`Showing ${total?start+1:0}-${Math.min(start+perPage,total)} of ${total} installments`;
    const pag=document.getElementById('repPagination');
    if(pag){
      let html=`<li class="page-item ${currentPage===1?'disabled':''}"><a class="page-link" href="#" data-page="${currentPage-1}">Previous</a></li>`;
      for(let i=1;i<=Math.min(totalPages,5);i++) html+=`<li class="page-item ${i===currentPage?'active':''}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
      html+=`<li class="page-item ${currentPage===totalPages?'disabled':''}"><a class="page-link" href="#" data-page="${currentPage+1}">Next</a></li>`;
      pag.innerHTML=html;
      pag.querySelectorAll('a').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();const p=parseInt(a.dataset.page);if(p>=1&&p<=totalPages){currentPage=p;render();}}));
    }
    if(!paged.length){ tbody.innerHTML='<tr><td colspan="6" class="text-center text-muted py-3">No installments found</td></tr>'; return; }
    tbody.innerHTML=paged.map(s=>{
      const statusIcon=s.status==='paid'?'✅':s.status==='overdue'?'⚠️':'⏳';
      const statusClass=s.status==='paid'?'status-paid':s.status==='overdue'?'status-overdue':'status-pending';
      return `<tr><td>${s.installment_number}</td><td>${s.due_date}</td><td>TZS ${Number(s.amount_due).toLocaleString()}</td><td>TZS ${Number(s.amount_paid).toLocaleString()}</td><td>TZS ${Number(s.balance_remaining).toLocaleString()}</td><td class="${statusClass}">${statusIcon} ${s.status}</td></tr>`;
    }).join('');
  }
  function renderHistory(sched){
    const tbody=document.getElementById('repHistoryBody');
    if(!tbody) return;
    const paid=sched.filter(s=>s.status==='paid').slice(-5);
    if(!paid.length){ tbody.innerHTML='<tr><td colspan="5" class="text-center text-muted py-3">No payments yet</td></tr>'; return; }
    tbody.innerHTML=paid.map(s=>`<tr><td>${s.payment_date||s.due_date}</td><td>TZS ${Number(s.amount_paid).toLocaleString()}</td><td>TRX-${String(s.installment_number).padStart(4,'0')}</td><td><span class="badge bg-success">Paid</span></td><td>Bank Transfer</td></tr>`).join('');
  }
  document.getElementById('repSearch')?.addEventListener('input', ()=>{currentPage=1;render();});
  document.getElementById('repStatusFilter')?.addEventListener('change', ()=>{currentPage=1;render();});
  fetchSchedule();
})();
