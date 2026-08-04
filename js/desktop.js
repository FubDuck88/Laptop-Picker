/**
 * desktop.js — Desktop-specific logic for Laptop Picker
 * Requires: core.js loaded first, PapaParse
 */

let allRows = [];
const selectedIds = new Set();
let isSteamSpecActive = false;
let displayedCount = 0;
const PAGE_SIZE = 40;

const activeFilters = {
  store: new Set(),
  cpu: new Set(),
  gpu: new Set(),
  mem: new Set(),
  sto: new Set(),
  disp: new Set()
};

const dropzone = document.getElementById('dropzone');
const dzBox = document.getElementById('dzBox');
const fileInput = document.getElementById('fileInput');
const appArea = document.getElementById('appArea');
const sidebar = document.getElementById('sidebar');

const homeBtn = document.getElementById('homeBtn');
const backToTopBtn = document.getElementById('backToTopBtn');
const steamSpecBtn = document.getElementById('steamSpecBtn');
const steamBtnText = document.getElementById('steamBtnText');
const steamBanner = document.getElementById('steamBanner');
const clearSteamBanner = document.getElementById('clearSteamBanner');
const steamInfoBtn = document.getElementById('steamInfoBtn');
const steamInfoModalOverlay = document.getElementById('steamInfoModalOverlay');
const closeSteamInfoModal = document.getElementById('closeSteamInfoModal');
const applySteamFromModal = document.getElementById('applySteamFromModal');

const searchInput = document.getElementById('searchInput');
const minPrice = document.getElementById('minPrice');
const maxPrice = document.getElementById('maxPrice');
const sortSelect = document.getElementById('sortSelect');
const resultCount = document.getElementById('resultCount');
const grid = document.getElementById('grid');
const resetBtn = document.getElementById('resetBtn');

const tray = document.getElementById('tray');
const trayChips = document.getElementById('trayChips');
const openCompare = document.getElementById('openCompare');
const clearCompare = document.getElementById('clearCompare');
const modalOverlay = document.getElementById('modalOverlay');
const closeModal = document.getElementById('closeModal');
const compareTableWrap = document.getElementById('compareTableWrap');

// ── Drag & Drop CSV ──────────────────────────────────────────────────────────

if (dzBox && fileInput) {
  dzBox.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', e => {
    if (e.target.files.length) handleFile(e.target.files[0]);
  });
  dzBox.addEventListener('dragover', e => { e.preventDefault(); dzBox.classList.add('drag-over'); });
  dzBox.addEventListener('dragleave', () => dzBox.classList.remove('drag-over'));
  dzBox.addEventListener('drop', e => {
    e.preventDefault(); dzBox.classList.remove('drag-over');
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
  });
}

function handleFile(file) {
  Papa.parse(file, {
    header: true,
    skipEmptyLines: true,
    complete: results => processRows(results.data),
    error: err => alert('CSV Error: ' + err.message)
  });
}

// ── Scroll Back to Top ───────────────────────────────────────────────────────

window.addEventListener('scroll', () => {
  if (window.scrollY > 300) {
    backToTopBtn.classList.add('show');
  } else {
    backToTopBtn.classList.remove('show');
  }
});

backToTopBtn.addEventListener('click', () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ── Filters Reset ────────────────────────────────────────────────────────────

function resetAllFilters() {
  searchInput.value = ''; minPrice.value = ''; maxPrice.value = '';
  sortSelect.value = 'recommended';
  isSteamSpecActive = false;
  updateSteamUI();

  activeFilters.store.clear();
  activeFilters.cpu.clear();
  activeFilters.gpu.clear();
  activeFilters.mem.clear();
  activeFilters.sto.clear();
  activeFilters.disp.clear();

  document.querySelectorAll('.sidebar input[type=checkbox]').forEach(cb => cb.checked = false);

  // Close all filter groups except Price Range
  document.querySelectorAll('.filter-group-header').forEach(h => {
    if (h.getAttribute('data-target') === 'fg-price') {
      h.classList.add('open');
      const body = document.getElementById('fg-price');
      if (body) body.classList.add('open');
    } else {
      h.classList.remove('open');
      h.classList.remove('has-active');
      const bodyId = h.getAttribute('data-target');
      const body = document.getElementById(bodyId);
      if (body) body.classList.remove('open');
    }
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });
  render();
}

if (homeBtn) homeBtn.addEventListener('click', resetAllFilters);
if (resetBtn) resetBtn.addEventListener('click', resetAllFilters);

// ── Steam Spec Preset ────────────────────────────────────────────────────────

function updateSteamUI() {
  if (isSteamSpecActive) {
    steamSpecBtn.style.background = 'var(--accent-2)';
    steamSpecBtn.style.color = '#1A1305';
    steamBtnText.textContent = 'Steam July 2026 Filter ON ✓';
    steamBanner.style.display = 'flex';
  } else {
    steamSpecBtn.style.background = 'transparent';
    steamSpecBtn.style.color = 'var(--accent-2)';
    steamBtnText.textContent = 'Filter Steam July 2026 Specs';
    steamBanner.style.display = 'none';
  }
}

if (steamSpecBtn) {
  steamSpecBtn.addEventListener('click', () => {
    isSteamSpecActive = !isSteamSpecActive;
    updateSteamUI();
    render();
  });
}

if (clearSteamBanner) {
  clearSteamBanner.addEventListener('click', () => {
    isSteamSpecActive = false;
    updateSteamUI();
    render();
  });
}

if (steamInfoBtn) {
  steamInfoBtn.addEventListener('click', () => {
    steamInfoModalOverlay.classList.add('show');
  });
}
if (closeSteamInfoModal) {
  closeSteamInfoModal.addEventListener('click', () => {
    steamInfoModalOverlay.classList.remove('show');
  });
}
if (applySteamFromModal) {
  applySteamFromModal.addEventListener('click', () => {
    steamInfoModalOverlay.classList.remove('show');
    isSteamSpecActive = true;
    updateSteamUI();
    render();
  });
}

// ── Sidebar Checkbox Binding ─────────────────────────────────────────────────

function bindCheckboxEvents() {
  document.querySelectorAll('.sidebar input[type="checkbox"]').forEach(cb => {
    cb.onchange = () => {
      const key = cb.dataset.key;
      const val = cb.dataset.val;
      if (!key || !val) return;

      if (cb.checked) {
        activeFilters[key].add(val);
      } else {
        activeFilters[key].delete(val);
      }

      const groupBody = cb.closest('.filter-group-body');
      if (groupBody) {
        const targetId = groupBody.id;
        const hdr = document.querySelector('[data-target="' + targetId + '"]');
        if (hdr) {
          if (activeFilters[key].size > 0) hdr.classList.add('has-active');
          else hdr.classList.remove('has-active');
        }
      }
      render();
    };
  });
}

// ── Data Processing ──────────────────────────────────────────────────────────

function processRows(rawRows) {
  allRows = rawRows.map((r, i) => normalizeRow(r, i, 'r'));

  populateStoreFilter();
  bindCheckboxEvents();

  if (dropzone) dropzone.style.display = 'none';
  appArea.style.display = 'block';
  sidebar.classList.add('visible');
  render();
}

function populateStoreFilter() {
  const storeList = document.getElementById('cblist-store');
  const storeWrap = document.getElementById('fg-store-wrap');
  if (!storeList || !storeWrap) return;

  const storeSet = new Set();
  allRows.forEach(r => {
    const deals = parseVendorDeals(r);
    deals.forEach(d => { if (d.vendor) storeSet.add(d.vendor); });
    if (r.series) storeSet.add(r.series);
  });

  const stores = [...storeSet].sort();
  if (stores.length === 0) {
    storeWrap.style.display = 'none';
    return;
  }

  storeWrap.style.display = 'block';
  storeList.innerHTML = stores.map(store => {
    const id = 'cb-store-' + store.toLowerCase().replace(/[^a-z0-9]/g, '');
    const checked = activeFilters.store.has(store) ? 'checked' : '';
    return '<li class="cb-item">'
      + '<input type="checkbox" id="' + id + '" data-key="store" data-val="' + escapeHtml(store) + '" ' + checked + ' />'
      + '<label class="cb-label" for="' + id + '">' + escapeHtml(store) + '</label>'
      + '</li>';
  }).join('');

  bindCheckboxEvents();
}

// ── Spec Extraction Functions ────────────────────────────────────────────────

function splitAtMarkers(raw, markerRe) {
  const s = raw.replace(/[\u00ae\u2122\u00a9]/g, '').replace(/\s+/g, ' ');
  const hits = [];
  let m;
  const re = new RegExp(markerRe.source, 'gi');
  while ((m = re.exec(s)) !== null) hits.push({ index: m.index, text: m[0] });
  if (!hits.length) return [];
  return hits.map((h, i) => ({
    markerText: h.text.trim(),
    segment: s.slice(h.index, i + 1 < hits.length ? hits[i + 1].index : s.length).replace(/\s+/g, ' ').trim()
  }));
}

const CPU_TIERS = ['Core i3', 'Core i5', 'Core i7', 'Core i9', 'Core 3', 'Core 5', 'Core 7', 'Core 9', 'Core Ultra 5', 'Core Ultra 7', 'Core Ultra 9', 'Ryzen 3', 'Ryzen 5', 'Ryzen 7', 'Ryzen 9', 'Ryzen AI 5', 'Ryzen AI 7', 'Ryzen AI 9', 'Snapdragon'];
function cpuTierIdx(label) {
  const i = CPU_TIERS.findIndex(t => label.toLowerCase().includes(t.toLowerCase()));
  return i === -1 ? 999 : i;
}

function extractCpuOptions(raw) {
  if (!raw) return [];
  const cpuRe = /Core\s+Ultra\s+\d|Core\s+i\d|Core\s+\d|Ryzen\s+AI\s+\d|Ryzen\s+\d|Snapdragon[\w\s]{0,12}/i;
  const segs = splitAtMarkers(raw, cpuRe);
  if (!segs.length) return [];
  const seen = new Set();
  const results = [];
  segs.forEach(({ markerText, segment }) => {
    let label = markerText.replace(/\s+(processor|cpu|up|with|and|to|series)$/i, '').trim();
    if (label.length < 3 || seen.has(label.toLowerCase())) return;
    seen.add(label.toLowerCase());
    const detail = segment.replace(/\s+(processor|cpu)\b/gi, '').replace(/\s+/g, ' ').slice(0, 110).trim();
    results.push({ label, detail });
  });
  results.sort((a, b) => cpuTierIdx(a.label) - cpuTierIdx(b.label));
  return results;
}

const GPU_TIERS = ['Iris Xe', 'Integrated', 'Qualcomm', 'Radeon', 'Arc', 'RTX 3050', 'RTX 3060', 'RTX 3070', 'RTX 3080', 'RTX 3090', 'RTX 4050', 'RTX 4060', 'RTX 4070', 'RTX 4080', 'RTX 4090', 'RTX 5050', 'RTX 5060', 'RTX 5070', 'RTX 5070 Ti', 'RTX 5080', 'RTX 5090'];
function gpuTierIdx(label) {
  const i = GPU_TIERS.findIndex(t => label.toLowerCase().includes(t.toLowerCase()));
  return i === -1 ? 999 : i;
}

function extractGpuOptions(raw) {
  if (!raw) return [];
  const gpuRe = /(?:GeForce\s+)?(?:RTX|GTX)\s+\d{4}(?:\s+Ti)?|Radeon(?:\s+\w+){0,3}|Iris\s+Xe\w*|Arc\b[^\n,]{0,20}|Integrated(?:\s+Graphics)?|Qualcomm(?:\s+\w+)?/i;
  const segs = splitAtMarkers(raw, gpuRe);
  if (!segs.length) return [];
  const seen = new Set();
  const results = [];
  segs.forEach(({ markerText, segment }) => {
    let label = markerText.replace(/^GeForce\s+/i, '').replace(/Laptop\s+GPU/i, '').trim();
    if (label.length < 2 || seen.has(label.toLowerCase())) return;
    seen.add(label.toLowerCase());
    let detail = label;
    const vram = segment.match(/(\d+GB\s+GDDR\w+)/i);
    const power = segment.match(/(\d+W)\s*(?:TGP|incl|max|\()/i);
    const tops = segment.match(/([\d,]+)\s*(?:AI\s*)?TOPS/i);
    const clock = segment.match(/([\d,]+)\s*MHz\s*Boost/i);
    if (vram) detail += ', ' + vram[1];
    if (power) detail += ', ' + power[1];
    if (clock) detail += ', ' + clock[1].replace(',', '.') + 'MHz';
    if (tops) detail += ', ' + tops[1] + ' AI TOPS';
    results.push({ label, detail });
  });
  results.sort((a, b) => gpuTierIdx(a.label) - gpuTierIdx(b.label));
  return results;
}

function extractMemOptions(raw) {
  if (!raw) return [];
  const stripped = raw.replace(/\([^)]*\)/g, '   ');
  const sizeRe = /\b(\d+)\s*GB\b/gi;
  const hits = [];
  let m;
  while ((m = sizeRe.exec(stripped)) !== null) hits.push({ index: m.index, gb: parseInt(m[1]) });
  if (!hits.length) return [];
  const seen = new Set();
  const results = [];
  hits.forEach((h, i) => {
    const endIdx = i + 1 < hits.length ? hits[i + 1].index : raw.length;
    const label = h.gb + 'GB';
    if (seen.has(label)) return;
    seen.add(label);
    const segment = raw.slice(h.index, endIdx).replace(/\s+/g, ' ').trim();
    const memType = segment.match(/(LPDDR\w+|DDR\w+)/i);
    const speed = segment.match(/([\d,]+)\s*MT\/s/i);
    const chan = segment.match(/\b(dual|single)\s*channel/i);
    let detail = label;
    if (memType) detail += ' ' + memType[1];
    if (speed) detail += ' ' + speed[1].replace(',', '.') + ' MT/s';
    if (chan) detail += ', ' + chan[1] + '-channel';
    results.push({ label, detail });
  });
  results.sort((a, b) => parseInt(a.label) - parseInt(b.label));
  return results;
}

function extractStorageOptions(raw) {
  if (!raw) return [];
  const stripped = raw.replace(/\([^)]*\)/g, '   ');
  const sizeRe = /\b(\d+(?:\.\d+)?)\s*(TB|GB)\b/gi;
  const hits = [];
  let m;
  while ((m = sizeRe.exec(stripped)) !== null) {
    hits.push({ index: m.index, label: m[1] + m[2].toUpperCase(), bytes: m[2].toUpperCase() === 'TB' ? parseFloat(m[1]) * 1e12 : parseFloat(m[1]) * 1e9 });
  }
  if (!hits.length) return [];
  const seen = new Set();
  const results = [];
  hits.forEach((h, i) => {
    if (seen.has(h.label)) return;
    seen.add(h.label);
    const endIdx = i + 1 < hits.length ? hits[i + 1].index : raw.length;
    const segment = raw.slice(h.index, endIdx).replace(/\s+/g, ' ').trim();
    const form = segment.match(/\b(M\.2|NVMe|PCIe(?:\s+Gen\d)?|SSD|HDD)\b/i);
    let detail = h.label;
    if (form) detail += ' ' + form[1];
    else detail += ' SSD';
    results.push({ label: h.label, detail, bytes: h.bytes });
  });
  results.sort((a, b) => a.bytes - b.bytes);
  return results;
}

function extractDisplayOptions(raw) {
  if (!raw) return [];
  const s = raw.replace(/[\u201c\u201d\u2033\u2032]/g, '"');
  const size = s.match(/^(\d{2}(?:\.\d)?)["\s]/);
  const res = s.match(/\b(FHD|QHD|WUXGA|WQXGA|4K|UHD|\d{3,4}\s*x\s*\d{3,4})\b/i);
  const panel = s.match(/\b(OLED|IPS|TN|VA|AMOLED)\b/i);
  const hz = s.match(/(\d{2,3})\s*Hz/i);
  let label = '';
  if (size) label += size[1] + '"';
  if (res) label += ' ' + res[1].toUpperCase();
  if (panel) label += ' ' + panel[1].toUpperCase();
  if (hz) label += ' ' + hz[1] + 'Hz';
  return [{ label: label.trim() || s.slice(0, 40), detail: label.trim() }];
}

function extractBatteryOptions(raw) {
  if (!raw) return [];
  const whr = raw.match(/(\d+(?:\.\d+)?)\s*Wh?r?\b/i);
  let label = whr ? whr[1] + 'Wh' : raw.slice(0, 20);
  return [{ label, detail: label }];
}

function specRow(label, raw) {
  if (!raw) return '';
  let options;
  switch (label) {
    case 'cpu': options = extractCpuOptions(raw); break;
    case 'gpu': options = extractGpuOptions(raw); break;
    case 'ram': options = extractMemOptions(raw); break;
    case 'disk': options = extractStorageOptions(raw); break;
    case 'screen': options = extractDisplayOptions(raw); break;
    case 'batt': options = extractBatteryOptions(raw); break;
    default: options = [{ label: raw.replace(/\s+/g, ' ').slice(0, 60), detail: raw.replace(/\s+/g, ' ').trim() }];
  }
  if (!options.length) {
    const fb = raw.replace(/\s+/g, ' ').trim();
    return '<li><span class="k">' + label + '</span><span class="v spec-val" title="' + fb.replace(/"/g, '&quot;') + '">' + escapeHtml(fb.slice(0, 60)) + '</span></li>';
  }
  const base = options[0];
  const top = options.length > 1 ? options[options.length - 1] : null;
  let html = '<li><span class="k">' + label + '</span><span class="v">'
    + '<span class="spec-val" title="' + base.detail.replace(/"/g, '&quot;') + '">' + escapeHtml(base.label) + '</span>';
  if (top) {
    html += ' <span class="upgrade-hint" title="' + top.detail.replace(/"/g, '&quot;') + '">up to ' + escapeHtml(top.label) + '</span>';
  }
  html += '</span></li>';
  return html;
}

// ── Filtering ────────────────────────────────────────────────────────────────

function getFiltered() {
  const q = searchInput.value.trim();
  const min = parseFloat(minPrice.value);
  const max = parseFloat(maxPrice.value);

  let rows = allRows.filter(r => matchesFilters(r, activeFilters, isSteamSpecActive, q, min, max));

  const sort = sortSelect.value;
  sortRows(rows, sort);
  return rows;
}

// ── Render ────────────────────────────────────────────────────────────────────

function render() {
  displayedCount = 0;
  const rows = getFiltered();
  resultCount.textContent = rows.length + (rows.length === 1 ? ' model matches' : ' models match');

  if (rows.length === 0) {
    grid.innerHTML = '<div class="empty-results">No models match these filters.</div>';
    return;
  }

  // Store filtered rows for load-more
  window._filteredRows = rows;
  grid.innerHTML = '';
  loadMoreCards();
}

function loadMoreCards() {
  const rows = window._filteredRows || [];
  const end = Math.min(displayedCount + PAGE_SIZE, rows.length);
  const fragment = document.createDocumentFragment();

  for (let idx = displayedCount; idx < end; idx++) {
    const r = rows[idx];
    const div = document.createElement('div');
    div.innerHTML = buildCardHtml(r);
    fragment.appendChild(div.firstChild);
  }

  grid.appendChild(fragment);
  displayedCount = end;

  // Remove old load-more button if exists
  const oldBtn = document.getElementById('loadMoreBtn');
  if (oldBtn) oldBtn.remove();

  // Add load-more button if more rows
  if (displayedCount < rows.length) {
    const btn = document.createElement('button');
    btn.id = 'loadMoreBtn';
    btn.className = 'btn secondary';
    btn.style.cssText = 'grid-column:1/-1;padding:14px;font-size:13px;margin-top:8px;';
    btn.textContent = 'Load More (' + (rows.length - displayedCount) + ' remaining)';
    btn.addEventListener('click', loadMoreCards);
    grid.appendChild(btn);
  }

  // Re-bind events for newly added cards
  grid.querySelectorAll('.compare-check').forEach(el => {
    if (el.dataset.bound) return;
    el.dataset.bound = '1';
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      const rid = el.dataset.rid;
      if (selectedIds.has(rid)) selectedIds.delete(rid);
      else {
        if (selectedIds.size >= 4) { alert('You can compare up to 4 models at a time.'); return; }
        selectedIds.add(rid);
      }
      render(); renderTray();
    });
  });

  grid.querySelectorAll('.detail-btn').forEach(btn => {
    if (btn.dataset.bound) return;
    btn.dataset.bound = '1';
    btn.addEventListener('click', () => {
      const rid = btn.dataset.rid;
      const row = allRows.find(r => r._rid === rid);
      if (row) openDetailModal(row);
    });
  });
}

function buildCardHtml(r) {
  const brand = detectBrand(r.processor);
  const bClass = brand === 'intel' ? 'intel' : (brand === 'amd' ? 'amd' : 'other');
  const bLabel = brand === 'intel' ? 'Intel' : (brand === 'amd' ? 'AMD' : 'Other');
  const checked = selectedIds.has(r._rid);
  const partId = r.id ? r.id.toUpperCase() : '';

  const deals = parseVendorDeals(r);
  const isMultiVendor = deals.length > 1;
  const bestVendorName = deals[0] ? deals[0].vendor : (r.best_vendor || r.series);

  let rawUrl = formatImgUrl(r.image_url, r.series || r.best_vendor);

  let imgHtml = '';
  if (rawUrl.length > 5) {
    imgHtml = '<div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:8px;text-align:center;margin:10px 0;height:110px;display:flex;align-items:center;justify-content:center;">'
      + '<img src="' + escapeHtml(rawUrl) + '" alt="' + escapeHtml(r.title) + '" loading="lazy" referrerpolicy="no-referrer" style="max-height:95px;width:auto;max-width:100%;object-fit:contain;filter:drop-shadow(0 4px 8px rgba(0,0,0,0.3));" onerror="this.parentElement.style.display=\'none\';" /></div>';
  }

  let dealBadgeHtml = '';
  if (isMultiVendor) {
    dealBadgeHtml = '<div style="margin-top:4px;"><span class="badge" style="background:#1B3830;color:var(--accent-2);border:1px solid #2B5E52;font-size:10px;padding:2px 7px;">🏷️ ' + deals.length + ' Deals (Best at ' + escapeHtml(bestVendorName) + ')</span></div>';
  }

  return '<div class="ticket">'
    + '<div class="ticket-head"><div class="ticket-title-wrap">'
    + '<p class="ticket-title">' + escapeHtml(r.title) + '</p>'
    + (partId ? '<div class="part-tag"><span class="pid">' + escapeHtml(partId) + '</span></div>' : '')
    + dealBadgeHtml
    + '</div>'
    + '<div class="compare-check ' + (checked ? 'checked' : '') + '" data-rid="' + r._rid + '">' + (checked ? '&#10003;' : '') + '</div></div>'
    + '<div><span class="badge ' + bClass + '">' + bLabel + '</span></div>'
    + imgHtml
    + '<div class="price-tag"><span class="cur">MYR</span>' + (r.price ? r.price.toLocaleString('en-MY', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—') + '</div>'
    + '<ul class="spec-list">'
    + specRow('cpu', r.processor) + specRow('gpu', r.graphics) + specRow('ram', r.memory)
    + specRow('disk', r.storage) + specRow('screen', r.display) + specRow('wifi', r.wifi) + specRow('batt', r.battery)
    + '</ul>'
    + '<div class="ticket-foot">'
    + '<button class="btn secondary sm detail-btn" data-rid="' + r._rid + '" style="font-size:11.5px;padding:6px 10px;">🔍 Specs & Deals</button>'
    + '<a class="view-link" href="' + escapeHtml(r.url) + '" target="_blank" rel="noopener">View deal &#8599;</a>'
    + '</div>'
    + '</div>';
}

// ── Image Rendering ──────────────────────────────────────────────────────────

function renderLaptopSvg(r) {
  let rawUrl = formatImgUrl(r.image_url, r.series || r.best_vendor);

  if (rawUrl.length > 5) {
    return '<img src="' + escapeHtml(rawUrl) + '" alt="' + escapeHtml(r.title) + '" loading="lazy" referrerpolicy="no-referrer" style="max-height:160px;max-width:100%;width:auto;height:auto;object-fit:contain;filter:drop-shadow(0 6px 14px rgba(0,0,0,0.5));display:block;margin:0 auto;" onerror="this.style.display=\'none\';if(this.nextElementSibling)this.nextElementSibling.style.display=\'block\';" />'
      + '<div style="display:none;">' + renderLaptopFallbackSvg(r) + '</div>';
  }
  return renderLaptopFallbackSvg(r);
}

function renderLaptopFallbackSvg(r) {
  const brand = detectBrand(r.processor || '');
  const accentColor = brand === 'intel' ? '#57D9C6' : (brand === 'amd' ? '#E2665C' : '#FFB020');
  return '<svg viewBox="0 0 300 180" fill="none" xmlns="http://www.w3.org/2000/svg">'
    + '<rect x="40" y="20" width="220" height="120" rx="10" fill="#1B1F26" stroke="#2D3545" stroke-width="2"/>'
    + '<rect x="48" y="28" width="204" height="104" rx="6" fill="#14171C"/>'
    + '<path d="M56 124 L244 124" stroke="' + accentColor + '" stroke-width="2" stroke-linecap="round"/>'
    + '<circle cx="150" cy="24" r="3" fill="#57D9C6"/>'
    + '<path d="M20 148 L280 148 C285 148 288 152 285 156 L275 165 C273 167 270 168 266 168 L34 168 C30 168 27 167 25 165 L15 156 C12 152 15 148 20 148 Z" fill="#252A34" stroke="#2D3545" stroke-width="2"/>'
    + '<rect x="120" y="152" width="60" height="4" rx="2" fill="#3A4354"/>'
    + '</svg>';
}

// ── Detail Modal ─────────────────────────────────────────────────────────────

const detailModalOverlay = document.getElementById('detailModalOverlay');
const closeDetailModal = document.getElementById('closeDetailModal');
const detailModalBody = document.getElementById('detailModalBody');

if (closeDetailModal) {
  closeDetailModal.addEventListener('click', () => {
    detailModalOverlay.classList.remove('show');
  });
}

function openDetailModal(r) {
  const partId = r.id ? r.id.toUpperCase() : 'N/A';
  const brand = detectBrand(r.processor);
  const bClass = brand === 'intel' ? 'intel' : (brand === 'amd' ? 'amd' : 'other');
  const bLabel = brand === 'intel' ? 'Intel' : (brand === 'amd' ? 'AMD' : 'Other');
  const priceStr = r.price ? 'RM ' + r.price.toLocaleString('en-MY', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'Unpriced / Inquiry';

  const deals = parseVendorDeals(r);

  let vendorTableHtml = '';
  if (deals.length > 0) {
    vendorTableHtml = '<div class="vendor-sec"><h3>/// Multi-Vendor Price & Deal Comparison (' + deals.length + ' Vendor Deals)</h3>'
      + '<table class="vendor-table"><thead><tr><th>Store / Vendor</th><th>Price (MYR)</th><th>Deal Status</th><th>Action</th></tr></thead><tbody>';

    deals.forEach(d => {
      const oPriceStr = d.price ? 'RM ' + d.price.toLocaleString('en-MY', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'Contact Store';
      const dealBadge = d.isLowest && d.price ? '<span class="best-deal-badge">★ BEST PRICE DEAL</span>' : '<span style="color:var(--text-faint);font-size:11px;">Standard Offer</span>';

      vendorTableHtml += '<tr>'
        + '<td><strong style="color:var(--text-bright);font-size:13px;">' + escapeHtml(d.vendor) + '</strong></td>'
        + '<td><strong style="color:var(--accent);font-size:14px;">' + oPriceStr + '</strong></td>'
        + '<td>' + dealBadge + '</td>'
        + '<td><a class="view-link" href="' + escapeHtml(d.url) + '" target="_blank" rel="noopener" style="padding:5px 12px;font-size:11.5px;background:var(--surface-raised);border:1px solid var(--border);border-radius:6px;">Buy Deal &#8599;</a></td>'
        + '</tr>';
    });
    vendorTableHtml += '</tbody></table></div>';
  }

  detailModalBody.innerHTML = ''
    + '<div class="detail-hero">'
    + '  <div class="detail-img-box">' + renderLaptopSvg(r) + '</div>'
    + '  <div class="detail-meta">'
    + '    <h2>' + escapeHtml(r.title) + '</h2>'
    + '    <div class="part-tag"><span class="pid">PART #: ' + escapeHtml(partId) + '</span> <span class="badge ' + bClass + '">' + bLabel + '</span></div>'
    + '    <div class="detail-price-box"><span class="price-num">' + priceStr + '</span><span class="price-cur">LOWEST MYR</span></div>'
    + '    <div><a class="view-link" href="' + escapeHtml(r.url) + '" target="_blank" rel="noopener" style="padding:8px 16px;background:var(--accent);color:#1A1305;border-radius:6px;font-weight:700;">Buy Lowest Price Deal &#8599;</a></div>'
    + '  </div>'
    + '</div>'
    + vendorTableHtml
    + '<div class="spec-sec"><h3>/// Full Technical Specifications</h3>'
    + '<div class="spec-grid-detail">'
    + '  <div class="spec-detail-card"><div class="spec-d-label">⚡ PROCESSOR (CPU)</div><div class="spec-d-val">' + escapeHtml(r.processor || 'N/A') + '</div></div>'
    + '  <div class="spec-detail-card"><div class="spec-d-label">🎮 GRAPHICS (GPU)</div><div class="spec-d-val">' + escapeHtml(r.graphics || 'N/A') + '</div></div>'
    + '  <div class="spec-detail-card"><div class="spec-d-label">🧠 MEMORY (RAM)</div><div class="spec-d-val">' + escapeHtml(r.memory || 'N/A') + '</div></div>'
    + '  <div class="spec-detail-card"><div class="spec-d-label">💾 STORAGE (SSD)</div><div class="spec-d-val">' + escapeHtml(r.storage || 'N/A') + '</div></div>'
    + '  <div class="spec-detail-card"><div class="spec-d-label">🖥️ DISPLAY PANEL</div><div class="spec-d-val">' + escapeHtml(r.display || 'N/A') + '</div></div>'
    + '  <div class="spec-detail-card"><div class="spec-d-label">📡 WI-FI & BLUETOOTH</div><div class="spec-d-val">' + escapeHtml(r.wifi || 'Standard WLAN') + '</div></div>'
    + '  <div class="spec-detail-card"><div class="spec-d-label">🔋 BATTERY & CHARGER</div><div class="spec-d-val">' + escapeHtml(r.battery || 'Integrated Battery') + '</div></div>'
    + '  <div class="spec-detail-card"><div class="spec-d-label">⚙️ OS, WARRANTY & OTHER DETAILS</div><div class="spec-d-val">' + escapeHtml(r.others || 'N/A') + '</div></div>'
    + '</div></div>';

  detailModalOverlay.classList.add('show');
}

// ── Compare Tray ─────────────────────────────────────────────────────────────

function renderTray() {
  if (selectedIds.size === 0) { tray.classList.remove('show'); return; }
  tray.classList.add('show');
  const items = allRows.filter(r => selectedIds.has(r._rid));
  trayChips.innerHTML = items.map(r => '<div class="tray-chip"><span>' + escapeHtml(r.title) + '</span><button data-rid="' + r._rid + '">&#10005;</button></div>').join('');
  trayChips.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', () => { selectedIds.delete(btn.dataset.rid); render(); renderTray(); });
  });
}

clearCompare.addEventListener('click', () => { selectedIds.clear(); render(); renderTray(); });

openCompare.addEventListener('click', () => {
  const items = allRows.filter(r => selectedIds.has(r._rid));
  if (!items.length) return;
  const fields = [
    ['Price (Lowest)', r => '<span class="price-cell">' + fmtPrice(r.price) + '</span>'],
    ['Best Deal Vendor', r => escapeHtml(r.best_vendor) || '—'],
    ['Vendor Deals', r => escapeHtml(r.vendor_prices) || '—'],
    ['Processor', r => escapeHtml(r.processor) || '—'],
    ['Graphics', r => escapeHtml(r.graphics) || '—'],
    ['Memory', r => escapeHtml(r.memory) || '—'],
    ['Storage', r => escapeHtml(r.storage) || '—'],
    ['Display', r => escapeHtml(r.display) || '—'],
    ['WiFi', r => escapeHtml(r.wifi) || '—'],
    ['Battery', r => escapeHtml(r.battery) || '—'],
    ['Direct Deal Link', r => '<a class="mini-link" href="' + escapeHtml(r.url) + '" target="_blank" rel="noopener">Buy Lowest Deal &#8599;</a>'],
  ];
  let html = '<table class="compare-table"><thead><tr><th></th>';
  items.forEach(r => { html += '<td class="model-name">' + escapeHtml(r.title) + '</td>'; });
  html += '</tr></thead><tbody>';
  fields.forEach(([label, fn]) => {
    html += '<tr><th>' + label + '</th>';
    items.forEach(r => { html += '<td>' + fn(r) + '</td>'; });
    html += '</tr>';
  });
  html += '</tbody></table>';
  compareTableWrap.innerHTML = html;
  modalOverlay.classList.add('show');
});

// ── Modals ───────────────────────────────────────────────────────────────────

function closeAllModals() {
  modalOverlay.classList.remove('show');
  detailModalOverlay.classList.remove('show');
  steamInfoModalOverlay.classList.remove('show');
}

if (closeModal) closeModal.addEventListener('click', closeAllModals);

modalOverlay.addEventListener('click', e => { if (e.target === modalOverlay) closeAllModals(); });
detailModalOverlay.addEventListener('click', e => { if (e.target === detailModalOverlay) closeAllModals(); });
steamInfoModalOverlay.addEventListener('click', e => { if (e.target === steamInfoModalOverlay) closeAllModals(); });

window.addEventListener('keydown', e => { if (e.key === 'Escape') closeAllModals(); });

// ── Event Bindings ───────────────────────────────────────────────────────────

[searchInput, minPrice, maxPrice].forEach(el => el.addEventListener('input', render));
sortSelect.addEventListener('change', render);

document.querySelectorAll('.filter-group-header').forEach(header => {
  header.addEventListener('click', () => {
    header.classList.toggle('open');
    const targetId = header.getAttribute('data-target');
    const body = document.getElementById(targetId);
    if (body) {
      body.classList.toggle('open');
    }
  });
});

// ── Data Load on Page Ready ──────────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', () => {
  if (window.preloadedRows && window.preloadedRows.length > 0) {
    processRows(window.preloadedRows);
  } else {
    loadData(processRows);
  }
});
