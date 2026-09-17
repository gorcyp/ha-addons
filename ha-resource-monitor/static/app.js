const $ = (id) => document.getElementById(id);
let timer, busy = false, hasData = false;
const mib = (bytes) => `${(bytes / 1048576).toFixed(1)} MiB`;
const pct = (value) => `${Number(value).toFixed(2)}%`;
const rate = (bytes) => bytes < 1024 ? `${bytes} B` : bytes < 1048576 ? `${(bytes/1024).toFixed(1)} KiB` : `${(bytes/1048576).toFixed(1)} MiB`;
const esc = (value) => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function row(item) {
  const level = item.memory_percent > 20 ? 'very-hot' : item.memory_percent > 10 ? 'hot' : '';
  const icon = item.kind === 'core' ? 'HA' : item.kind === 'supervisor' ? 'S' : 'A';
  const kind = item.kind === 'core' ? 'Core' : item.kind === 'supervisor' ? 'Supervisor' : 'Dodatek';
  return `<tr class="${level}"><td><div class="component"><span class="icon">${icon}</span><div><b>${esc(item.name)}</b><small>${kind}</small></div></div></td><td><b>${mib(item.memory_usage)}</b></td><td><div class="barline"><span class="bar"><i style="width:${Math.min(100,item.memory_percent)}%"></i></span>${pct(item.memory_percent)}</div></td><td>${pct(item.cpu_percent)}</td><td>${rate(item.network_rx)} / ${rate(item.network_tx)}</td></tr>`;
}

async function refresh() {
  if (busy) return;
  busy = true;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60000);
  try {
    const response = await fetch('api/stats', {cache:'no-store', signal:controller.signal});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    $('knownRam').textContent = mib(data.summary.known_memory);
    $('knownPercent').textContent = 'Suma komponentów w tabeli, nie całego hosta';
    $('cpu').textContent = pct(data.summary.cpu_sum);
    $('addons').textContent = data.summary.running_addons;
    $('coverage').textContent = 'Odczytano: ' + data.components.filter(x => x.kind === 'addon').length + ' z ' + data.summary.running_addons;
    $('rows').innerHTML = data.components.map(row).join('') || '<tr><td colspan="5" class="empty">Brak danych</td></tr>';
    $('status').textContent = data.warnings?.length ? 'Niepełne dane' : 'Dane aktualne';
    $('updated').textContent = 'Ostatni pomiar: ' + new Date(data.timestamp * 1000).toLocaleTimeString('pl-PL');
    $('error').hidden = !data.warnings?.length;
    $('error').textContent = (data.warnings || []).join(' ');
    $('rows').classList.remove('stale');
    hasData = true;
  } catch (error) {
    $('status').textContent = 'Brak danych';
    $('error').textContent = `Nie udało się pobrać statystyk: ${error.message}`;
    $('error').hidden = false;
    $('rows').classList.add('stale');
    if (hasData) $('status').textContent = 'Dane nieaktualne';
    else $('rows').innerHTML = '<tr><td colspan="5" class="empty">Nie udało się pobrać statystyk.</td></tr>';
  } finally {
    clearTimeout(timeout);
    busy = false;
  }
}

function schedule() {
  clearInterval(timer);
  timer = setInterval(refresh, Number($('interval').value) * 1000);
}
$('interval').addEventListener('change', schedule);
refresh(); schedule();
