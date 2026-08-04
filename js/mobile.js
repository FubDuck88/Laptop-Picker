/**
 * mobile.js — Mobile-specific logic for Laptop Picker
 * Requires: core.js loaded first, PapaParse
 */

let allRows = [];
let isSteamActive = false;
let displayedCount = 0;
const PAGE_SIZE = 30;

const activeFilters = {
  store: new Set(),
  cpu: new Set(),
  gpu: new Set(),
  mem: new Set(),
  sto: new Set(),
  disp: new Set()
};

// ── Data Load ────────────────────────────────────────────────────────────────

loadData(function (rawRows) {
  allRows = rawRows.map((r, i) => normalizeRow(r, i, 'm'));
  populateStoreFilter();
  bindCheckboxEvents();
  renderMobile();
});

// ── Store Filter ─────────────────────────────────────────────────────────────

function populateStoreFilter() {
  const storeList = document.getElementById('mcblist-store');
  const storeWrap = document.getElementById('mfg-store-wrap');
  if (!storeList || !storeWrap) return;

  const storeSet = new Set();
  allRows.forEach(r => {
    const deals = parseVendorDeals(r);
    deals.forEach(d => { if (d.vendor) storeSet.add(d.vendor); });
    if (r.series) storeSet.add(r.series);
  });

  const stores = [...storeSet].sort();
  if (stores.length === 0) return;

  storeWrap.style.display = 'block';
  storeList.innerHTML = stores.map(store => {
    const id = 'mcb-store-' + store.toLowerCase().replace(/[^a-z0-9]/g, '');
    return '<li class="m-cb-item">'
      + '<input type="checkbox" id="' + id + '" data-key="store" data-val="' + escapeHtml(store) + '" />'
      + '<label for="' + id + '">' + escapeHtml(store) + '</label>'
      + '</li>';
  }).join('');

  bindCheckboxEvents();
}

function bindCheckboxEvents() {
  document.querySelectorAll('.m-sheet input[type="checkbox"]').forEach(cb => {
    cb.onchange = () => {
      const key = cb.dataset.key;
      const val = cb.dataset.val;
      if (!key || !val) return;
      if (cb.checked) activeFilters[key].add(val);
      else activeFilters[key].delete(val);
      updateActiveFilterCount();
    };
  });
}

function updateActiveFilterCount() {
  let count = 0;
  Object.values(activeFilters).forEach(s => count += s.size);
  if (document.getElementById('mMinPrice').value) count++;
  if (document.getElementById('mMaxPrice').value) count++;
  if (isSteamActive) count++;
  document.getElementById('mActiveFilterCount').textContent = count;
}

// ── Filtering ────────────────────────────────────────────────────────────────

function getMobileFiltered() {
  const q = document.getElementById('mSearchInput').value.trim();
  const minP = parseFloat(document.getElementById('mMinPrice').value);
  const maxP = parseFloat(document.getElementById('mMaxPrice').value);

  let rows = allRows.filter(r => matchesFilters(r, activeFilters, isSteamActive, q, minP, maxP));

  const s = document.getElementById('mSortSelect').value;
  sortRows(rows, s);
  return rows;
}

// ── Render ────────────────────────────────────────────────────────────────────

function renderMobile() {
  displayedCount = 0;
  const rows = getMobileFiltered();
  document.getElementById('mCount').textContent = rows.length + ' laptops match';
  const grid = document.getElementById('mGrid');

  if (!rows.length) {
    grid.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-dim);">No models match mobile filters.</div>';
    return;
  }

  window._mFilteredRows = rows;
  grid.innerHTML = '';
  loadMoreMobileCards();
}

function loadMoreMobileCards() {
  const rows = window._mFilteredRows || [];
  const grid = document.getElementById('mGrid');
  const end = Math.min(displayedCount + PAGE_SIZE, rows.length);

  let html = '';
  for (let idx = displayedCount; idx < end; idx++) {
    html += buildMobileCardHtml(rows[idx]);
  }

  // Remove old load-more button
  const oldBtn = document.getElementById('mLoadMoreBtn');
  if (oldBtn) oldBtn.remove();

  grid.insertAdjacentHTML('beforeend', html);
  displayedCount = end;

  // Add load-more button
  if (displayedCount < rows.length) {
    const btn = document.createElement('button');
    btn.id = 'mLoadMoreBtn';
    btn.className = 'm-btn secondary';
    btn.style.cssText = 'width:100%;padding:14px;font-size:13px;margin-top:8px;';
    btn.textContent = 'Load More (' + (rows.length - displayedCount) + ' remaining)';
    btn.addEventListener('click', loadMoreMobileCards);
    grid.appendChild(btn);
  }

  // Bind detail buttons for newly added cards
  grid.querySelectorAll('.m-detail-btn').forEach(btn => {
    if (btn.dataset.bound) return;
    btn.dataset.bound = '1';
    btn.addEventListener('click', () => {
      const row = allRows.find(r => r._rid === btn.dataset.rid);
      if (row) openMobileDetail(row);
    });
  });
}

function buildMobileCardHtml(r) {
  const deals = parseVendorDeals(r);
  const bestVendor = deals[0] ? deals[0].vendor : (r.best_vendor || r.series);
  const priceStr = r.price ? 'RM ' + r.price.toLocaleString('en-MY', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'Unpriced / Inquiry';

  let badgeHtml = '';
  if (r.vendor_count > 1) {
    badgeHtml = '<div class="m-deal-badge">🏷️ ' + r.vendor_count + ' Vendor Deals (Best at ' + escapeHtml(bestVendor) + ')</div>';
  }

  let rawImg = formatImgUrl(r.image_url, r.series || r.best_vendor);
  let imgHtml = '';
  if (rawImg.length > 5) {
    imgHtml = '<div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:6px;text-align:center;margin:4px 0;height:100px;display:flex;align-items:center;justify-content:center;">'
      + '<img src="' + escapeHtml(rawImg) + '" alt="' + escapeHtml(r.title) + '" loading="lazy" referrerpolicy="no-referrer" style="max-height:88px;width:auto;max-width:100%;object-fit:contain;filter:drop-shadow(0 4px 8px rgba(0,0,0,0.3));" onerror="this.parentElement.style.display=\'none\';" /></div>';
  }

  return '<div class="m-card">'
    + '<div>'
    + '<div class="m-card-title">' + escapeHtml(r.title) + '</div>'
    + '<div class="m-part">MPN: ' + escapeHtml(r.id ? r.id.toUpperCase() : 'N/A') + '</div>'
    + badgeHtml
    + '</div>'
    + imgHtml
    + '<div class="m-price-tag"><span class="m-price-cur">MYR</span>' + priceStr + '</div>'
    + '<div class="m-specs">'
    + '<div>⚡ <strong>CPU:</strong> ' + escapeHtml(r.processor || 'N/A') + '</div>'
    + '<div>🎮 <strong>GPU:</strong> ' + escapeHtml(r.graphics || 'N/A') + '</div>'
    + '<div>🧠 <strong>RAM:</strong> ' + escapeHtml(r.memory || 'N/A') + ' | 💾 <strong>SSD:</strong> ' + escapeHtml(r.storage || 'N/A') + '</div>'
    + '</div>'
    + '<div class="m-actions">'
    + '<button class="m-btn secondary m-detail-btn" data-rid="' + r._rid + '">🔍 View Deals</button>'
    + '<a href="' + escapeHtml(r.url) + '" target="_blank" rel="noopener" class="m-btn primary">Buy Deal ↗</a>'
    + '</div>'
    + '</div>';
}

// ── Detail Sheet ─────────────────────────────────────────────────────────────

function openMobileDetail(r) {
  const deals = parseVendorDeals(r);
  const priceStr = r.price ? 'RM ' + r.price.toLocaleString('en-MY', { minimumFractionDigits: 2 }) : 'Inquiry';

  let tableHtml = '';
  if (deals.length > 0) {
    tableHtml = '<h4 style="font-size:12px;color:var(--accent-2);margin:12px 0 8px;">/// Multi-Vendor Price Deals (' + deals.length + ' Vendors)</h4>'
      + '<div class="table-scroll-box"><table style="width:100%;border-collapse:collapse;font-size:11.5px;background:var(--bg);border-radius:8px;overflow:hidden;">'
      + '<tr style="background:var(--surface-raised);text-align:left;"><th style="padding:6px 8px;">Vendor</th><th style="padding:6px 8px;">Price</th><th style="padding:6px 8px;">Link</th></tr>';

    deals.forEach(d => {
      const pStr = d.price ? 'RM ' + d.price.toLocaleString('en-MY', { minimumFractionDigits: 2 }) : 'Inquiry';
      const badge = d.isLowest ? ' <span style="color:var(--accent-2);font-weight:700;">★ BEST</span>' : '';
      tableHtml += '<tr style="border-bottom:1px solid var(--border);">'
        + '<td style="padding:8px;">' + escapeHtml(d.vendor) + badge + '</td>'
        + '<td style="padding:8px;color:var(--accent);font-weight:700;">' + pStr + '</td>'
        + '<td style="padding:8px;"><a href="' + escapeHtml(d.url) + '" target="_blank" style="color:var(--accent-2);text-decoration:none;font-weight:700;">Buy ↗</a></td>'
        + '</tr>';
    });
    tableHtml += '</table></div>';
  }

  let rawImg = formatImgUrl(r.image_url, r.series || r.best_vendor);
  let imgBox = '';
  if (rawImg.length > 5) {
    imgBox = '<div style="background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:12px;text-align:center;margin-bottom:12px;">'
      + '<img src="' + escapeHtml(rawImg) + '" alt="' + escapeHtml(r.title) + '" loading="lazy" referrerpolicy="no-referrer" style="max-height:130px;width:auto;max-width:100%;object-fit:contain;filter:drop-shadow(0 4px 10px rgba(0,0,0,0.4));" onerror="this.parentElement.style.display=\'none\';" />'
      + '</div>';
  }

  document.getElementById('mDetailBody').innerHTML = ''
    + imgBox
    + '<h3 style="font-size:15px;margin-bottom:6px;">' + escapeHtml(r.title) + '</h3>'
    + '<div style="font-size:12px;color:var(--text-dim);margin-bottom:10px;">MPN: <strong style="color:var(--accent);">' + escapeHtml(r.id.toUpperCase()) + '</strong></div>'
    + '<div style="font-size:20px;font-weight:700;color:var(--accent);margin-bottom:12px;">' + priceStr + '</div>'
    + tableHtml
    + '<h4 style="font-size:12px;color:var(--accent-2);margin:16px 0 8px;">/// Specifications</h4>'
    + '<div style="font-size:12px;line-height:1.6;background:var(--bg);padding:10px;border-radius:8px;border:1px solid var(--border);">'
    + '<div>⚡ <strong>CPU:</strong> ' + escapeHtml(r.processor || 'N/A') + '</div>'
    + '<div>🎮 <strong>GPU:</strong> ' + escapeHtml(r.graphics || 'N/A') + '</div>'
    + '<div>🧠 <strong>RAM:</strong> ' + escapeHtml(r.memory || 'N/A') + '</div>'
    + '<div>💾 <strong>Storage:</strong> ' + escapeHtml(r.storage || 'N/A') + '</div>'
    + '<div>🖥️ <strong>Display:</strong> ' + escapeHtml(r.display || 'N/A') + '</div>'
    + '</div>';

  document.getElementById('mDetailOverlay').classList.add('show');
}

// ── Accordion headers in mobile sheet ────────────────────────────────────────

document.querySelectorAll('.m-fg-hdr').forEach(hdr => {
  hdr.addEventListener('click', () => {
    const targetId = hdr.getAttribute('data-target');
    const body = document.getElementById(targetId);
    if (body) {
      body.classList.toggle('open');
    }
  });
});

// ── Preset Chip Buttons ──────────────────────────────────────────────────────

document.getElementById('chipAll').addEventListener('click', () => resetAllFilters());
document.getElementById('chipSteam').addEventListener('click', () => {
  isSteamActive = true;
  document.getElementById('mSteamBanner').style.display = 'flex';
  renderMobile();
});
document.getElementById('chipDeals').addEventListener('click', () => {
  activeFilters.store.clear();
  document.getElementById('mSearchInput').value = '';
  renderMobile();
});
document.getElementById('chipNvidia').addEventListener('click', () => {
  activeFilters.gpu.add('RTX');
  renderMobile();
});
document.getElementById('chip16Gb').addEventListener('click', () => {
  activeFilters.mem.add('16GB');
  renderMobile();
});

function resetAllFilters() {
  document.getElementById('mSearchInput').value = '';
  document.getElementById('mMinPrice').value = '';
  document.getElementById('mMaxPrice').value = '';
  isSteamActive = false;
  document.getElementById('mSteamBanner').style.display = 'none';

  Object.keys(activeFilters).forEach(k => activeFilters[k].clear());
  document.querySelectorAll('.m-sheet input[type="checkbox"]').forEach(cb => cb.checked = false);

  updateActiveFilterCount();
  renderMobile();
}

document.getElementById('mResetFiltersBtn').addEventListener('click', resetAllFilters);
document.getElementById('mClearSteam').addEventListener('click', () => {
  isSteamActive = false;
  document.getElementById('mSteamBanner').style.display = 'none';
  renderMobile();
});

document.getElementById('mSteamPresetToggle').addEventListener('click', () => {
  isSteamActive = !isSteamActive;
  document.getElementById('mSteamBanner').style.display = isSteamActive ? 'flex' : 'none';
  updateActiveFilterCount();
  renderMobile();
});

document.getElementById('applySteamFromSheet').addEventListener('click', () => {
  isSteamActive = true;
  document.getElementById('mSteamBanner').style.display = 'flex';
  document.getElementById('mSteamOverlay').classList.remove('show');
  renderMobile();
});

document.getElementById('mSearchInput').addEventListener('input', renderMobile);
document.getElementById('mMinPrice').addEventListener('input', () => { updateActiveFilterCount(); renderMobile(); });
document.getElementById('mMaxPrice').addEventListener('input', () => { updateActiveFilterCount(); renderMobile(); });
document.getElementById('mSortSelect').addEventListener('change', renderMobile);

// ── Sheet Triggers ───────────────────────────────────────────────────────────

document.getElementById('navFilterSheet').addEventListener('click', () => {
  document.getElementById('mFilterOverlay').classList.add('show');
});
document.getElementById('closeFilterSheet').addEventListener('click', () => {
  document.getElementById('mFilterOverlay').classList.remove('show');
});
document.getElementById('applyMobileFilterBtn').addEventListener('click', () => {
  document.getElementById('mFilterOverlay').classList.remove('show');
  renderMobile();
});
document.getElementById('closeDetailSheet').addEventListener('click', () => {
  document.getElementById('mDetailOverlay').classList.remove('show');
});
document.getElementById('navSteamSheet').addEventListener('click', () => {
  document.getElementById('mSteamOverlay').classList.add('show');
});
document.getElementById('closeSteamSheet').addEventListener('click', () => {
  document.getElementById('mSteamOverlay').classList.remove('show');
});

document.getElementById('navHome').addEventListener('click', () => {
  resetAllFilters();
  window.scrollTo({ top: 0, behavior: 'smooth' });
});
