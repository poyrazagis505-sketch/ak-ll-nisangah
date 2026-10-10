(() => {
'use strict';
const KEY = 'holosight.v1';
const ST = ['Beklemede', 'Algılama', 'Aktif', 'Hata'];
const SENS = {
  mag:{n:'Modül algılama noktası',c:'#19e6c1',d:'Modülün gövdeye oturup oturmadığını belirler.'},
  nfc:{n:'NFC kimlik modülü',c:'#7dff6a',d:'Her çıkarılabilir modüle ait benzersiz kimliği temsil eder. Simülasyonda kimlik okuma olayını görselleştirir.'},
  motion:{n:'Hareket sensörü',c:'#6aa8ff',d:'Cihazın hareket ettiğini bildiren temsili sensör.'},
  btn:{n:'Kontrol düğmesi',c:'#ffd166',d:'Optik göstergeyi ve sayaç görünümünü yöneten temsili düğme.'},
  optic:{n:'Optik gösterge',c:'#ffffff',d:'Modül kimliğini ve sayaç değerini holografik ekranda gösterir.'}
};
const EXTRA = {magbody:['Çıkarılabilir modül','Kayıtlı sayaç değerini taşıyan temsili modül. Takılıp çıkarılabilir.'], ctrl:['Denetleyici (MCU)','Sensör durumlarını toplayıp optik ekrana ileten temsili birim.']};
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const defaults = () => ({
  modules:[{id:'MAG-001',cap:30,count:30},{id:'MAG-002',cap:30,count:18},{id:'MAG-003',cap:20,count:7}],
  docked:null, selected:0, running:false, counterOn:true,
  sensors:{mag:'Beklemede',nfc:'Beklemede',motion:'Beklemede',btn:'Beklemede',optic:'Beklemede'},
  selSensor:'mag', read:'Beklemede', log:[]
});
let S = load(), busy = false;
function load(){ try { const s = JSON.parse(localStorage.getItem(KEY)); if (s && Array.isArray(s.modules) && s.modules.length) return {...defaults(), ...s, running:false, read:'Beklemede'}; } catch(e){} return defaults(); }
function save(){ try { localStorage.setItem(KEY, JSON.stringify(S)); } catch(e){} }
const sleep = ms => new Promise(r => setTimeout(r, ms));
const cur = () => S.docked === null ? null : S.modules[S.docked];

// --- günlük ve bildirim ---
function log(cat, msg){
  const t = new Date().toLocaleTimeString('tr-TR');
  S.log.unshift({t, cat, msg}); S.log = S.log.slice(0, 80); save(); renderLog(true);
}
function renderLog(anim){
  const ul = $('#logList');
  ul.innerHTML = S.log.map(e => `<li class="c-${e.cat}"><time>${e.t}</time><b>${{sys:'SİSTEM',mod:'MODÜL',id:'KİMLİK',sensor:'SENSÖR',err:'HATA'}[e.cat]}</b>${e.msg}</li>`).join('');
}
let toastT;
function toast(m){ const t = $('#toast'); t.textContent = m; t.classList.add('show'); clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove('show'), 2200); }

// --- durum değişimi ---
function setSensor(k, st, quiet){
  if (S.sensors[k] === st) return;
  S.sensors[k] = st; if (!quiet) log('sensor', `${SENS[k].n}: ${st}`); save(); render();
}
function needRun(){ if (!S.running){ toast('Önce simülasyonu başlatın.'); return true; } if (busy){ toast('Bir işlem sürüyor.'); return true; } return false; }

async function attach(){
  if (needRun()) return;
  const i = +$('#selMod').value;
  if (S.docked === i){ toast('Bu modül zaten takılı.'); return; }
  busy = true;
  if (S.docked !== null) await detach(true);
  S.docked = i; S.read = 'Okunuyor'; save(); render();
  const m = S.modules[i];
  log('mod', `Modül takılıyor: ${m.id}`);
  setSensor('mag', 'Algılama', true); await sleep(700);
  setSensor('mag', 'Aktif'); log('mod', 'Modül algılandı.');
  setSensor('nfc', 'Algılama', true); $('#scanFx').classList.add('on'); await sleep(1300);
  $('#scanFx').classList.remove('on');
  setSensor('nfc', 'Aktif', true); log('id', `Kimlik kaydı okundu (simülasyon): ${m.id}`);
  await sleep(500); log('mod', `Kayıtlı durum yüklendi: ${m.count}/${m.cap}`);
  S.read = 'Tamamlandı'; setSensor('optic', 'Aktif', true); log('sys', 'Optik arayüz güncellendi.');
  toast(`${m.id} takıldı`); busy = false; save(); render();
}
async function detach(internal){
  if (!internal && needRun()) return;
  if (S.docked === null){ toast('Takılı modül yok.'); return; }
  busy = true; const m = cur();
  log('mod', `Modül bağlantısı kesildi: ${m.id}`);
  S.docked = null; S.read = 'Beklemede';
  S.sensors.mag = 'Beklemede'; S.sensors.nfc = 'Beklemede'; S.sensors.optic = 'Beklemede'; save(); render();
  log('mod', `Son kayıtlı durum korundu: ${m.count}/${m.cap}`);
  await sleep(900); if (!internal) toast(`${m.id} çıkarıldı`); busy = false;
}
function bump(d){
  if (needRun()) return; const m = cur(); if (!m){ toast('Önce bir modül takın.'); return; }
  const n = m.count + d; if (n < 0 || n > m.cap){ toast(`Değer 0–${m.cap} aralığında olmalı.`); return; }
  m.count = n; log('mod', `${m.id} sayaç: ${n}/${m.cap}`); save(); render();
}

// --- çizim ---
let lastNum = null;
function render(){
  const m = cur(), run = S.running, nd = S.modules.length;
  document.body.classList.toggle('paused', !run);
  $('#stSys').textContent = !run ? 'Beklemede' : m ? 'Bağlı' : 'Modül yok';
  $('#stSim').textContent = run ? 'Çalışıyor' : 'Duraklatıldı';
  $('#stMod').textContent = m ? m.id : '—'; $('#stCount').textContent = nd;
  $('#stSens').textContent = Object.values(S.sensors).filter(v => v === 'Aktif').length + ' / 5';
  $('#btnStart').disabled = run; $('#btnPause').disabled = !run;
  // sensör listesi
  $('#sensList').innerHTML = Object.keys(SENS).map(k => `<div class="sens ${S.selSensor===k?'sel':''}" data-k="${k}" data-st="${S.sensors[k]}"><i></i><span>${SENS[k].n.split(' ')[0]} ${SENS[k].n.split(' ')[1]||''}</span><select data-k="${k}" aria-label="${SENS[k].n}">${ST.map(s=>`<option ${s===S.sensors[k]?'selected':''}>${s}</option>`).join('')}</select></div>`).join('');
  // model
  $('#mag').classList.toggle('out', !m); $('#mag').classList.toggle('docked', !!m);
  $('#magTag').textContent = m ? m.id.slice(-3) : '---';
  const rows = 8, lit = m ? Math.round(m.count / m.cap * rows) : 0;
  $('#magFill').innerHTML = Array.from({length:rows}, (_, i) => `<rect x="342" y="${318 - i*10}" width="46" height="7" rx="2" fill="${m && i < lit ? '#7dff6a' : '#0e1216'}" opacity="${m && i < lit ? .75 : .6}"/>`).join('').replace(/y="(\d+)"/g, (a, y) => +y < 244 ? '' : a);
  $$('.wire,.node').forEach(el => { const k = el.dataset.s; el.dataset.st = S.sensors[k]; el.style.setProperty('--c', SENS[k].c); });
  // optik
  const op = $('#optic'), linked = !!m && run;
  op.classList.toggle('nolink', !linked); op.classList.toggle('off', !S.counterOn);
  const num = !m ? '--' : S.counterOn ? String(m.count).padStart(2, '0') : '**';
  const n = $('#opNum'); if (n.textContent !== num){ n.textContent = num; n.classList.remove('roll'); void n.getBBox(); n.classList.add('roll'); }
  $('#opCap').textContent = m && S.counterOn ? `/ ${m.cap}` : '';
  $('#opId').textContent = 'KİMLİK: ' + (m ? m.id : '----');
  $('#opMsg').textContent = !run ? 'DURAKLATILDI' : !m ? 'BAĞLANTI YOK — MODÜL ÇIKARILDI' : !S.counterOn ? 'SAYAÇ KAPALI' : '';
  $('#opLink').textContent = m ? 'Bağlı' : 'Bağlantı yok'; $('#opRead').textContent = S.read; $('#opCnt').textContent = S.counterOn ? 'AÇIK' : 'KAPALI';
  // liste
  $('#modBody').innerHTML = S.modules.map((x, i) => `<tr class="${i===S.docked?'cur':''}"><td>${x.id}</td><td>${x.cap}</td><td>${x.count}</td><td>${i===S.docked?'Bağlı':'—'}</td></tr>`).join('');
  const sel = $('#selMod'), v = Math.min(S.selected, nd - 1);
  sel.innerHTML = S.modules.map((x, i) => `<option value="${i}" ${i===v?'selected':''}>${x.id} (${x.count}/${x.cap})</option>`).join('');
  S.selected = v;
}
(function ticks(){ let h=''; for(let a=0;a<360;a+=10){ const r=a%30?4:9, x=150+Math.sin(a*Math.PI/180), y=120-Math.cos(a*Math.PI/180); h+=`<line x1="${150+Math.sin(a*Math.PI/180)*105}" y1="${120-Math.cos(a*Math.PI/180)*105}" x2="${150+Math.sin(a*Math.PI/180)*(105-r)}" y2="${120-Math.cos(a*Math.PI/180)*(105-r)}"/>`; } $('#ticks').innerHTML = h; })();

// --- ipuçları ---
const tip = $('#tooltip');
document.addEventListener('mousemove', e => {
  const el = e.target.closest && e.target.closest('.tip');
  $$('.hl').forEach(x => x !== el && x.classList.remove('hl'));
  if (!el){ tip.style.opacity = 0; return; }
  el.classList.add('hl'); const k = el.dataset.k, s = el.dataset.s;
  const [n, d] = SENS[k] ? [SENS[k].n, SENS[k].d] : EXTRA[k];
  const st = s ? S.sensors[s] : k === 'magbody' ? (cur() ? 'Takılı: ' + cur().id : 'Çıkarılmış') : 'Simülasyon ' + (S.running ? 'çalışıyor' : 'duraklatıldı');
  tip.innerHTML = `<b>${n.toLocaleUpperCase('tr')}</b>${d}<em>Durum: ${st}</em>`;
  tip.style.left = Math.min(e.clientX + 14, innerWidth - 280) + 'px'; tip.style.top = (e.clientY + 14) + 'px'; tip.style.opacity = 1;
});

// --- ayarlar ---
function openSettings(){
  $('#modCount').value = S.modules.length; buildRows(S.modules); $('#setErr').textContent = ''; $('#dlgSettings').showModal();
}
function buildRows(list){
  $('#setRows').innerHTML = '<div class="setmod hint"><span>Kimlik</span><span>Kapasite</span><span>Kayıtlı değer</span></div>' + list.map((m, i) => `<div class="setmod"><input data-f="id" value="${m.id}" aria-label="Kimlik ${i+1}"><input data-f="cap" type="number" value="${m.cap}" aria-label="Kapasite ${i+1}"><input data-f="count" type="number" value="${m.count}" aria-label="Değer ${i+1}"></div>`).join('');
}
function readRows(){ return $$('#setRows .setmod:not(.hint)').map(r => ({id:r.querySelector('[data-f=id]').value.trim().toUpperCase(), cap:+r.querySelector('[data-f=cap]').value, count:+r.querySelector('[data-f=count]').value})); }
function validate(list){
  const seen = new Set();
  for (const [i, m] of list.entries()){
    const n = i + 1;
    if (!/^[A-Z]{3}-\d{3}$/.test(m.id)) return `Modül ${n}: kimlik "ABC-123" biçiminde olmalı.`;
    if (seen.has(m.id)) return `Modül ${n}: "${m.id}" kimliği tekrar ediyor; her kimlik benzersiz olmalı.`;
    seen.add(m.id);
    if (!Number.isInteger(m.cap) || m.cap < 1 || m.cap > 99) return `Modül ${n}: kapasite 1–99 arasında tam sayı olmalı.`;
    if (!Number.isInteger(m.count) || m.count < 0 || m.count > m.cap) return `Modül ${n}: kayıtlı değer 0 ile ${m.cap} arasında olmalı.`;
  }
  return '';
}
$('#modCount').addEventListener('change', () => {
  const n = Math.max(1, Math.min(6, +$('#modCount').value || 1)); $('#modCount').value = n;
  const l = readRows(); while (l.length < n){ let k = l.length + 1, id; do id = 'MAG-' + String(k++).padStart(3,'0'); while (l.some(x => x.id === id)); l.push({id, cap:30, count:30}); } buildRows(l.slice(0, n));
});
$('#setSave').onclick = () => {
  const l = readRows(), err = validate(l); $('#setErr').textContent = err; if (err) return;
  const dockedId = cur() && cur().id; S.modules = l; S.docked = dockedId ? l.findIndex(m => m.id === dockedId) : null;
  if (S.docked === -1){ S.docked = null; S.read = 'Beklemede'; S.sensors.mag = S.sensors.nfc = S.sensors.optic = 'Beklemede'; log('mod', 'Takılı modül listeden kaldırıldı.'); }
  log('sys', `Ayarlar kaydedildi: ${l.length} modül.`); save(); render(); $('#dlgSettings').close(); toast('Ayarlar kaydedildi');
};
$('#setCancel').onclick = () => $('#dlgSettings').close();

// --- olaylar ---
$('#btnStart').onclick = () => { S.running = true; log('sys', 'Simülasyon başlatıldı.'); render(); };
$('#btnPause').onclick = () => { if (busy) return toast('Bir işlem sürüyor.'); S.running = false; log('sys', 'Simülasyon duraklatıldı.'); render(); };
$('#btnReset').onclick = () => {
  if (!confirm('Sıfırlama; tüm modülleri, kayıtlı sayaç değerlerini, sensör durumlarını, ayarları ve olay günlüğünü varsayılan test verilerine döndürür. Devam edilsin mi?')) return;
  S = defaults(); busy = false; save(); log('sys', 'Simülasyon sıfırlandı (varsayılan veriler yüklendi).'); render(); toast('Sıfırlandı');
};
$('#btnAttach').onclick = attach; $('#btnDetach').onclick = () => detach(false);
$('#btnDec').onclick = () => bump(-1); $('#btnInc').onclick = () => bump(1);
$('#btnCounter').onclick = () => { S.counterOn = !S.counterOn; log('sys', `Sayaç göstergesi ${S.counterOn ? 'açıldı' : 'kapatıldı'} (kayıtlı veri korunuyor).`); save(); render(); };
$('#selMod').onchange = e => { S.selected = +e.target.value; save(); };
$('#btnCycle').onclick = () => { const k = S.selSensor; setSensor(k, ST[(ST.indexOf(S.sensors[k]) + 1) % 4]); };
$('#sensList').addEventListener('change', e => { if (e.target.dataset.k) setSensor(e.target.dataset.k, e.target.value); });
$('#sensList').addEventListener('click', e => { const r = e.target.closest('.sens'); if (r && e.target.tagName !== 'SELECT'){ S.selSensor = r.dataset.k; render(); } });
$('#btnSettings').onclick = openSettings;
$('#btnClearLog').onclick = () => { S.log = []; save(); renderLog(); toast('Günlük temizlendi'); };
$('#btnHelp').onclick = () => $('#dlgIntro').showModal();
$('#introOk').onclick = () => { $('#dlgIntro').close(); try { localStorage.setItem(KEY + '.intro', '1'); } catch(e){} };

render(); renderLog();
let seen = false; try { seen = localStorage.getItem(KEY + '.intro'); } catch(e){}
if (!seen) $('#dlgIntro').showModal();
if (!S.log.length) log('sys', 'HOLO-SIGHT hazır. Simülasyonu başlatın.');
})();
