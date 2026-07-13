const facts = document.querySelector('#facts');
let reconnectDelay = 1000;
let eventSource;
function setText(id, value){document.querySelector(id).textContent = value || '—'}
function render(state){
  document.querySelector('#mode').textContent = state.selection_mode === 'manual' ? `Manual selection · ${state.selection_reason}` : `Automatic selection · ${state.selection_reason}`;
  const p = state.primary;
  if(!p){ setText('#flight','Waiting for aircraft'); document.querySelector('#nearby').innerHTML=''; return; }
  setText('#flight', p.airline_name || p.flight_identifier || p.callsign);
  setText('#origin', p.origin_code || 'Route'); setText('#destination', p.destination_code || 'unavailable');
  const rows = [['Flight',p.flight_identifier],['Origin city',p.origin_city],['Destination city',p.destination_city],['Aircraft',p.aircraft_model],['Tail',p.registration],['Altitude',p.altitude_ft?`${p.altitude_ft.toLocaleString()} ft`:null],['Speed',p.ground_speed_mph?`${p.ground_speed_mph} mph`:null],['Distance',`${p.distance_miles} mi ${p.bearing_compass}`],['State',p.approach_state],['Quality',p.data_quality]];
  facts.innerHTML = rows.filter(r=>r[1]).map(r=>`<div><dt>${r[0]}</dt><dd>${r[1]}</dd></div>`).join('');
  const resume = state.selection_mode === 'manual' ? '<button id="resume-auto">Resume automatic selection</button>' : '';
  document.querySelector('#nearby').innerHTML = resume + state.nearby.map(a=>`<button class="card" data-icao="${a.icao_hex}"><strong>${a.flight_identifier || a.callsign}</strong><br>${a.distance_miles} mi ${a.bearing_compass}<br>${a.altitude_ft || '—'} ft</button>`).join('');
  document.querySelectorAll('[data-icao]').forEach(b=>b.addEventListener('click',()=>fetch('/api/v1/manual-selection',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({icao_hex:b.dataset.icao})}).then(load)));
  document.querySelector('#resume-auto')?.addEventListener('click',()=>fetch('/api/v1/manual-selection',{method:'DELETE'}).then(load));
}
async function load(){render(await (await fetch('/api/v1/state')).json())}
function connect(){
  if(!window.EventSource){setInterval(load,10000); load(); return;}
  eventSource = new EventSource('/api/v1/events');
  eventSource.addEventListener('state', e=>{reconnectDelay=1000; render(JSON.parse(e.data));});
  eventSource.addEventListener('heartbeat', ()=>{reconnectDelay=1000;});
  eventSource.onerror=()=>{eventSource.close(); setTimeout(()=>{load(); connect();}, reconnectDelay); reconnectDelay=Math.min(reconnectDelay*2,30000);};
}
document.querySelector('#theme').addEventListener('click',()=>{const n=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=n;localStorage.setItem('theme',n)});
connect();
