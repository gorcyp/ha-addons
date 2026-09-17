const $ = (id) => document.getElementById(id);
let timer, busy = false, hasData = false, stopping = false, csrf = '';
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
  if (busy || stopping || document.hidden) return;
  busy = true;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60000);
  try {
    const response = await fetch('api/stats', {cache:'no-store', signal:controller.signal});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    csrf = data.csrf_token;
    $('knownRam').textContent = mib(data.summary.known_memory);
    $('knownPercent').textContent = 'Suma komponentów w tabeli, nie całego hosta';
    $('cpu').textContent = pct(data.summary.cpu_sum);
    const swap = data.swap;
    $('swapUsed').textContent = !swap?.available ? 'Niedostępne' : swap.total === 0 ? 'Wyłączony' : mib(swap.used);
    $('swapInfo').textContent = !swap?.available ? 'Brak odczytu liczników systemowych' : swap.total === 0 ? 'Brak aktywnej pamięci wymiany' : 'Z ' + mib(swap.total) + ' • ' + pct(swap.percent) + ' • wolne: ' + mib(swap.free);
    $('addons').textContent = data.summary.running_addons;
    $('coverage').textContent = 'Odczytano: ' + data.components.filter(x => x.kind === 'addon').length + ' z ' + data.summary.running_addons;
    $('rows').innerHTML = data.components.map(row).join('') || '<tr><td colspan="5" class="empty">Brak danych</td></tr>';
    [...$('rows').rows].forEach((tr, index) => {
      const item = data.components[index];
      const td = tr.insertCell();
      if (!item?.can_stop) { td.textContent = '—'; return; }
      const button = document.createElement('button');
      button.textContent = 'Zatrzymaj';
      button.onclick = () => stopApp(item, button);
      td.appendChild(button);
    });
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
document.addEventListener('visibilitychange', () => {
  if (document.hidden) clearInterval(timer);
  else { refresh(); schedule(); }
});
async function stopApp(item, button) {
  if (stopping || !confirm('Zatrzymać „' + item.name + '”? Usługi i automatyzacje zależne od tej aplikacji przestaną działać. Ponownie uruchomisz ją w ustawieniach HA.')) return;
  stopping = true;
  button.disabled = true;
  button.textContent = 'Zatrzymywanie…';
  $('rows').querySelectorAll('button').forEach(b => b.disabled = true);
  try {
    const response = await fetch('api/stop', {method:'POST', headers:{'Content-Type':'application/json', 'X-CSRF-Token':csrf}, body:JSON.stringify({slug:item.slug}), signal:AbortSignal.timeout(70000)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Błąd zatrzymania');
    $('status').textContent = data.message;
  } catch(error) {
    alert(error.message + '\nSprawdź aktualny stan aplikacji w HA.');
  } finally {
    stopping = false;
    $('rows').querySelectorAll('button').forEach(b => b.disabled = false);
    button.textContent = 'Zatrzymaj';
    refresh();
  }
}
