const facts = document.querySelector('#facts');
const themeButton = document.querySelector('#theme');

function setText(id, value){document.querySelector(id).textContent = value || '—'}
function titleCase(value){
  if(!value || typeof value !== 'string') return value;
  return value.toLowerCase().replace(/\b([a-z])/g, c => c.toUpperCase());
}
function compass(value){
  return value && typeof value === 'string' ? value.toUpperCase() : value;
}
function airportCode(value){
  return value && typeof value === 'string' ? value.toUpperCase() : value;
}
function setTheme(theme){
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('theme', theme);
  themeButton.textContent = theme === 'dark' ? 'Light theme' : 'Dark theme';
}
function render(state){
  document.querySelector('#mode').textContent = state.selection_mode === 'manual' ? 'Manual selection' : 'Automatic selection';
  const p = state.primary;
  if(!p){ setText('#flight','Waiting for aircraft'); return; }
  setText('#flight', titleCase(p.airline_name || p.flight_identifier || p.callsign));
  setText('#origin', p.origin_code ? airportCode(p.origin_code) : 'Route'); setText('#destination', p.destination_code ? airportCode(p.destination_code) : 'Unavailable');
  const rows = [['Flight',titleCase(p.flight_identifier)],['Origin city',titleCase(p.origin_city)],['Destination city',titleCase(p.destination_city)],['Aircraft',titleCase(p.aircraft_model)],['Tail',titleCase(p.registration)],['Altitude',p.altitude_ft !== null && p.altitude_ft !== undefined ? `${p.altitude_ft.toLocaleString()} ft`:null],['Speed',p.ground_speed_mph !== null && p.ground_speed_mph !== undefined ? `${p.ground_speed_mph} mph`:null],['Distance',`${p.distance_miles} mi ${compass(p.bearing_compass)}`],['State',titleCase(p.approach_state)],['Quality',titleCase(p.data_quality)]];
  facts.innerHTML = rows.filter(r=>r[1]).map(r=>`<div><dt>${r[0]}</dt><dd>${r[1]}</dd></div>`).join('');
  document.querySelector('#nearby').innerHTML = state.nearby.map(a=>`<button class="card" data-icao="${a.icao_hex}"><strong>${a.flight_identifier || a.callsign}</strong><br>${a.distance_miles} mi ${a.bearing_compass}<br>${a.altitude_ft || '—'} ft</button>`).join('');
  document.querySelectorAll('[data-icao]').forEach(b=>b.addEventListener('click',()=>fetch('/api/v1/manual-selection',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({icao_hex:b.dataset.icao})}).then(load)));
}
async function load(){render(await (await fetch('/api/v1/state')).json())}
if(window.EventSource){const es = new EventSource('/api/v1/events'); es.addEventListener('state', e=>render(JSON.parse(e.data))); es.onerror=()=>setTimeout(load,3000);} else {setInterval(load,10000);}
setTheme(localStorage.getItem('theme') === 'dark' ? 'dark' : 'light');
themeButton.addEventListener('click',()=>setTheme(document.documentElement.dataset.theme==='dark'?'light':'dark'));
load();
