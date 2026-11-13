'use strict';
const $ = id => document.getElementById(id);
document.querySelectorAll('[data-port]').forEach(link => {
  const url = new URL(location.href); url.port = link.dataset.port;
  url.pathname = link.dataset.path || '/'; url.search = ''; url.hash = '';
  link.href = url.href; link.target = '_blank'; link.rel = 'noopener';
});
async function json(url, options) {
  const response = await fetch(url, {...options, signal: AbortSignal.timeout(15000)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error_description || data.error || `HTTP ${response.status}`);
  return data;
}
async function students() {
  $('student-state').textContent = 'Đang tải…'; $('reload').disabled = true;
  $('student-body').replaceChildren(); $('student-head').replaceChildren();
  try {
    const rows = await json($('source').value); const db = $('source').value.endsWith('students-db');
    const fields = db ? ['id','student_id','fullname','dob','major'] : ['id','name','major','gpa'];
    const labels = db ? ['ID','Mã sinh viên','Họ tên','Ngày sinh','Ngành'] : ['ID','Họ tên','Ngành','GPA'];
    const heading = document.createElement('tr');
    labels.forEach(label => {const cell=document.createElement('th'); cell.textContent=label; heading.append(cell);}); $('student-head').append(heading);
    rows.forEach(row => {const tr=document.createElement('tr'); fields.forEach(field => {const td=document.createElement('td'); td.textContent=row[field] ?? ''; tr.append(td);}); $('student-body').append(tr);});
    $('student-state').textContent = `${rows.length} sinh viên · ${db ? 'MariaDB' : 'JSON'}`;
  } catch(error) { $('student-state').textContent = `Không tải được dữ liệu: ${error.message}`; }
  finally {$('reload').disabled=false;}
}
if ($('source')) {
  $('source').onchange=()=>{ $('raw-api').href=$('source').value; students(); };
  $('reload').onclick=students;
}
if ($('balance')) $('balance').onclick=async()=>{
  $('balance').disabled=true; const servers=[];
  try {for(let i=0;i<6;i++){const r=await fetch('/?probe='+Date.now()+'-'+i,{cache:'no-store',signal:AbortSignal.timeout(8000)}); if(!r.ok)throw new Error(`HTTP ${r.status}`); servers.push(r.headers.get('X-Served-By') || 'Không có header'); await r.text();} $('balance-result').textContent=servers.join(' → ');
  } catch(e){$('balance-result').textContent=e.message;} finally{$('balance').disabled=false;}
};
if ($('dns-reload')) $('dns-reload').onclick=async()=>{ $('dns-result').textContent='Đang tra cứu…'; try {const rows=await json('/api/dns'); $('dns-result').textContent=rows.map(r=>`${r.name} → ${r.addresses.join(', ')}`).join('\n');}catch(e){$('dns-result').textContent=e.message;} };
if ($('login')) $('login').onsubmit=async event=>{
  event.preventDefault(); const form=event.currentTarget; const button=form.querySelector('[type=submit]'); button.disabled=true; $('login-state').textContent='Đang đăng nhập…';
  try {const body=new URLSearchParams(new FormData(form)); body.set('client_id','flask-app'); body.set('grant_type','password');
    const token=await json('/auth/realms/realm_sv001/protocol/openid-connect/token',{method:'POST',body});
    const resource=await json('/api/secure',{headers:{Authorization:`Bearer ${token.access_token}`}});
    $('login-state').textContent=`Đã xác thực: ${resource.preferred_username} · ${resource.message}`;
  }catch(e){$('login-state').textContent=`Đăng nhập thất bại: ${e.message}`;}finally{form.elements.password.value='';button.disabled=false;}
};
if ($('service-title')) {
  const view = new URLSearchParams(location.search).get('view');
  const views = {students:['students','API sinh viên'], database:['students','MariaDB'], identity:['identity','Keycloak'], dns:['dns','DNS nội bộ'], gateway:['gateway','Gateway & cân bằng tải']};
  const selected = views[view];
  if (selected) {
    $(selected[0]).hidden=false;
    $('service-title').textContent=selected[1];
    document.title=`${selected[1]} | MiniCloud`;
    if (selected[0]==='students') {
      $('source').value=view==='database'?'/api/students-db':'/api/student';
      $('raw-api').href=$('source').value;
      $('students-title').textContent=view==='database'?'Sinh viên từ MariaDB':'Sinh viên từ JSON';
      students();
    }
  } else $('not-found').hidden=false;
}
