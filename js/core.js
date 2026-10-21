/**
 * core.js — Shared logic for Laptop Picker (Desktop & Mobile)
 * Contains: data loading, vendor parsing, filters, scoring, sorting, image URL formatting
 */

// ── Utility ──────────────────────────────────────────────────────────────────

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function formatImgUrl(raw, vendorStr, titleStr, productUrl) {
  const value = (raw || '').trim();
  if (!value || /^(data:|javascript:|blob:)/i.test(value) || /\s/.test(value)) return '';
  const knownStores = [
    [/techhypermart/i, 'https://www.techhypermart.com/'],
    [/pc\s?image/i, 'https://store.pcimage.com.my/'],
    [/all\s?it/i, 'https://www.allithypermarket.com.my/'],
    [/acer/i, 'https://store.acer.com/'],
    [/gloo/i, 'https://www.gloo.com.my/']
  ];
  try {
    const base = productUrl && /^https?:\/\//i.test(productUrl) ? productUrl
      : knownStores.find(([pattern]) => pattern.test(vendorStr || ''))?.[1];
    if (!base && !/^(https?:)?\/\//i.test(value)) return '';
    const url = new URL(value.startsWith('//') ? 'https:' + value : value, base);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) return '';
    return url.href;
  } catch (_) { return ''; }
}

function renderProductImage(row, mobile = false, height = mobile ? 100 : 110) {
  const url = formatImgUrl(row.image_url, row.series || row.best_vendor, row.title, row.url);
  const compactStyle = height <= 48 ? "width:64px;flex:0 0 64px;margin:0;" : "";
  return '<div class="product-photo" style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:8px;text-align:center;margin:10px 0;height:' + height + 'px;display:flex;align-items:center;justify-content:center;' + compactStyle + '">'
    + (url ? '<img data-product-photo src="' + escapeHtml(url) + '" alt="' + escapeHtml(row.title) + '" loading="lazy" referrerpolicy="no-referrer" style="max-height:' + (height - 15) + 'px;width:auto;max-width:100%;object-fit:contain;" />' : '')
    + '<span class="photo-unavailable" role="img" aria-label="Product photo unavailable"' + (url ? ' hidden' : '') + ' style="color:var(--text-dim);font-size:12px;">Photo unavailable</span></div>';
}

// Capture image failures, including cards inserted by Load More. Never retry a broken URL forever.
document.addEventListener('error', event => {
  const image = event.target;
  if (!image || !image.matches || !image.matches('img[data-product-photo]')) return;
  image.hidden = true;
  const placeholder = image.parentElement.querySelector('.photo-unavailable');
  if (placeholder) placeholder.hidden = false;
}, true);

function fmtPrice(n) {
  if (!n) return 'RM -';
  return 'RM ' + n.toLocaleString('en-MY', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ── Data Loading ─────────────────────────────────────────────────────────────

let verifiedRelease = null;
let catalogTimer = null;
let catalogRefresh = null;
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && catalogRefresh) catalogRefresh();
});
function loadData(callback) {
  const message = document.getElementById('catalogMessage');
  const retry = document.getElementById('catalogRetry');
  const expired = document.getElementById('showExpired');
  if (message) message.textContent = 'Loading verified offers…';
  if (retry) { retry.hidden = true; retry.onclick = () => loadData(callback); }
  if (catalogTimer) clearInterval(catalogTimer);
  catalogRefresh = null;
  return loadVerifiedRelease().then(release => {
    verifiedRelease = release;
    function refresh() {
      const includeExpired = !!expired?.checked;
      const rows = verifiedCatalogRows(release, { includeExpired });
      const hidden = release.catalog.offers.filter(o => !offerFreshness(o).show_by_default).length;
      const sellers = [...new Set(release.catalog.offers.map(o => o.seller))].join(', ');
      const retained = release.source_decisions.filter(s => s.state === 'retained').length;
      if (message) message.textContent = `${rows.length} verified configurations from ${sellers || 'qualified sources'}. `
        + `${hidden} offers older than seven days hidden by default. `
        + (retained ? `${retained} sources retained their last successful observations. ` : '')
        + 'Public MYR prices exclude shipping and conditional discounts. Check stock with the seller.';
      callback(rows);
    }
    if (expired) expired.onchange = refresh;
    catalogRefresh = refresh;
    refresh();
    catalogTimer = setInterval(refresh, 60000);
    return release;
  }).catch(() => {
    verifiedRelease = null;
    if (message) message.textContent = 'Verified catalog could not be loaded. Please retry.';
    if (retry) retry.hidden = false;
    callback([]);
    return null;
  });
}

function systemRamGb(row) {
  if (row.verified) return row.memory_gb;
  const raw = (row.memory || '').split(/\b(?:max(?:imum)?|up to|upgrade)/i)[0];
  const modules = raw.match(/(\d+)\s*GB\s*[*×x]\s*(\d+)/i);
  if (modules) return Number(modules[1]) * Number(modules[2]);
  const values = [...raw.matchAll(/\b(\d+)\s*GB\b/gi)].map(m => Number(m[1]));
  return new Set(values).size === 1 ? values[0] : null;
}

function isIntegratedGpu(row) {
  if (row.verified) return row.gpu_kind === 'integrated';
  return /integrated|iris|uhd|intel arc graphics|radeon graphics/i.test(row.graphics || '')
    && !/RTX|GTX|\bRX\s*\d|Arc\s+[AB]\d/i.test(row.graphics || '');
}

function offerStatusHtml(row) {
  if (!row.verified) return '';
  const time = new Date(row.observed_at).toLocaleString('en-MY', { timeZone: 'Asia/Kuala_Lumpur' });
  const stock = {in_stock:'In stock', out_of_stock:'Out of stock', unknown:'Stock unknown'}[row.availability] || 'Stock unknown';
  return '<div class="offer-status">' + escapeHtml(`${row.freshness.toUpperCase()} · ${stock} · Observed ${time} MYT`) + '</div>';
}

function offerHistoryHtml(row) {
  if (!row.verified || !verifiedRelease) return '';
  return '<section class="offer-history"><h4>Recorded price history</h4>' + row.offer_ids.map(id => {
    const points = recordedHistory(verifiedRelease, id);
    if (!points.length) return '<p>No recorded observations for this offer.</p>';
    const seller = (row.deals || []).find(d => d.id === id)?.vendor || row.series;
    return '<h5>' + escapeHtml(seller) + '</h5><p>' + (points.length === 1 ? 'One observation; no price trend yet.' : points.length + ' recorded observations. Gaps mean no observation.')
      + '</p><div class="history-scroll"><table><thead><tr><th>Observed (Malaysia time)</th><th>Price</th><th>Stock</th></tr></thead><tbody>'
      + points.map(o => '<tr><td>' + escapeHtml(new Date(o.observed_at).toLocaleString('en-MY', {timeZone:'Asia/Kuala_Lumpur'}))
        + '</td><td>' + fmtPrice(o.price_sen / 100) + '</td><td>' + escapeHtml(o.availability.replaceAll('_', ' ')) + '</td></tr>').join('')
      + '</tbody></table></div>';
  }).join('') + '</section>';
}

function parseVendorDeals(r) {
  if (Array.isArray(r.deals)) return r.deals;
  if (!r.vendor_prices) {
    const vName = (r.best_vendor ? r.best_vendor.split(' (')[0] : r.series) || 'Store Deal';
    return [{ vendor: vName, price: r.price, url: r.url, isLowest: true }];
  }

  const priceParts = r.vendor_prices.split(' | ');
  const urlMap = {};
  if (r.vendor_urls) {
    r.vendor_urls.split(' | ').forEach(part => {
      const idx = part.indexOf(': ');
      if (idx !== -1) {
        urlMap[part.slice(0, idx).trim()] = part.slice(idx + 2).trim();
      }
    });
  }

  const deals = priceParts.map(part => {
    const idx = part.indexOf(': RM ');
    if (idx !== -1) {
      const vName = part.slice(0, idx).trim();
      const pStr = part.slice(idx + 5).replace(/,/g, '').trim();
      const priceNum = parseFloat(pStr) || 0;
      return { vendor: vName, price: priceNum, url: urlMap[vName] || r.url };
    }
    return { vendor: part, price: r.price, url: r.url };
  });

  deals.sort((a, b) => (a.price || 999999) - (b.price || 999999));
  const minP = deals[0] ? deals[0].price : r.price;
  deals.forEach(d => { d.isLowest = (d.price > 0 && d.price === minP); });

  return deals;
}

function rowForStores(row, stores) {
  if (!row.verified || !stores.size) return row;
  const deals = row.deals.filter(d => stores.has(d.vendor));
  if (!deals.length) return null;
  const best = deals[0];
  return {...row, price:best.price, price_sen:best.price_sen, url:best.url, image_url:best.image_url,
    best_vendor:best.vendor, series:best.vendor, availability:best.availability,
    observed_at:best.observed_at, freshness:best.freshness, deals,
    offer_ids:deals.map(d => d.id), vendor_count:new Set(deals.map(d => d.vendor)).size};
}

// ── Optional gaming preset matching ──────────────────────────────

function matchesSteamSpecs(r) {
  const gpuText = (r.graphics || '').toLowerCase();
  const cpuText = (r.processor || '').toLowerCase();

  // 1. Realistic Price Cap for Steam Survey Laptops (under RM 10,000)
  const pVal = typeof r.price === 'number' ? r.price : (parseFloat(r.price) || 0);
  if (pVal <= 0 || pVal > 10000) return false;

  // 2. Realistic RAM Spec: 16GB to 32GB (Steam #1 & #2 Share)
  const ramGb = systemRamGb(r);
  if (ramGb == null || ramGb < 16 || ramGb > 32) return false;

  // 3. Realistic GPU Spec: Steam sweet-spot gaming GPUs (RTX 3050, 3060, 3070, 4050, 4060, 4070, 5050, 5060, 5070, GTX 1650/1660)
  // Exclude extreme workstation / ultra-flagships (RTX 4080, 4090, 5080, 5090, Quadro)
  if (/4080|4090|5080|5090|quadro|workstation|rtx\s*a\d{4}/i.test(gpuText)) return false;

  const hasRealisticGpu = /(?:rtx\s*(?:3050|3060|3070|4050|4060|4070|5050|5060|5070)|gtx\s*(?:1650|1660))\b/i.test(gpuText);
  if (!hasRealisticGpu) return false;

  // 4. Realistic CPU Spec: 6 to 8+ Core Mainstream CPUs (i5, i7, Ultra 5, Ultra 7, Ryzen 5, Ryzen 7)
  const hasRealisticCpu = /i5|i7|ultra\s*[57]|ryzen\s*[57]/i.test(cpuText);
  if (!hasRealisticCpu) return false;

  return true;
}

// ── Scoring ──────────────────────────────────────────────────────────────────

function calcRecommendedScore(r) {
  let specPoints = 0;

  // GPU Tier Points
  const gfx = (r.graphics || '').toLowerCase();
  if (gfx.includes('5090') || gfx.includes('4090')) specPoints += 100;
  else if (gfx.includes('5080') || gfx.includes('4080')) specPoints += 85;
  else if (gfx.includes('5070') || gfx.includes('4070')) specPoints += 70;
  else if (gfx.includes('5060') || gfx.includes('4060')) specPoints += 55;
  else if (gfx.includes('5050') || gfx.includes('4050') || gfx.includes('3060') || gfx.includes('3050')) specPoints += 40;
  else specPoints += 15;

  // RAM Points
  const mem = (r.memory || '').toLowerCase();
  if (mem.includes('64gb')) specPoints += 40;
  else if (mem.includes('32gb')) specPoints += 30;
  else if (mem.includes('16gb')) specPoints += 20;

  // CPU Points
  const cpu = (r.processor || '').toLowerCase();
  if (cpu.includes('ultra 9') || cpu.includes('i9') || cpu.includes('ryzen 9')) specPoints += 30;
  else if (cpu.includes('ultra 7') || cpu.includes('i7') || cpu.includes('ryzen 7')) specPoints += 20;
  else if (cpu.includes('ultra 5') || cpu.includes('i5') || cpu.includes('ryzen 5')) specPoints += 10;

  // Multi-Vendor Price Deal Advantage
  if (r.vendor_count > 1) specPoints += 25;

  const price = r.price && r.price > 0 ? r.price : 999999;
  return specPoints / (price / 1000);
}

function calcPopularityScore(r) {
  let score = 0;

  // 1. Retail availability across multiple stores
  score += (r.vendor_count || 1) * 25;

  // 2. High Demand GPUs (Steam Survey top cards)
  const gfx = (r.graphics || '').toLowerCase();
  if (gfx.includes('4060')) score += 50;
  else if (gfx.includes('3060')) score += 45;
  else if (gfx.includes('5060')) score += 40;
  else if (gfx.includes('4050') || gfx.includes('3050')) score += 35;
  else if (gfx.includes('4070') || gfx.includes('5070')) score += 30;

  // 3. Most Popular RAM (16GB #1 at 41%, 32GB #2)
  const mem = (r.memory || '').toLowerCase();
  if (mem.includes('16gb') || mem.includes('16 gb')) score += 40;
  else if (mem.includes('32gb') || mem.includes('32 gb')) score += 30;

  // 4. Most Popular CPU Tiers
  const cpu = (r.processor || '').toLowerCase();
  if (cpu.includes('i7') || cpu.includes('ultra 7') || cpu.includes('ryzen 7')) score += 35;
  else if (cpu.includes('i5') || cpu.includes('ultra 5') || cpu.includes('ryzen 5')) score += 30;
  else if (cpu.includes('i9') || cpu.includes('ultra 9') || cpu.includes('ryzen 9')) score += 25;

  return score;
}

// ── Display Helpers ──────────────────────────────────────────────────────────

function dispInchPrefix(displayStr) {
  const m = (displayStr || '').match(/^(\d{2}(?:\.\d)?)[\."\u201c\u201d\u2033\u2032\u0022\u0027\s]/);
  return m ? m[1] : null;
}

function detectBrand(proc, fullRow) {
  const text = `${proc || ''} ${fullRow && !fullRow.verified ? (fullRow.title || '') + ' ' + (fullRow.others || '') : ''}`.toLowerCase();

  // 1. AMD CPUs
  if (/amd|ryzen|\br[3579]\b|\br3-|\br5-|\br7-|\br9-|athlon|threadripper|7\d{3}hs|8\d{3}hs|5\d{3}u|7\d{3}u/i.test(text)) {
    return 'amd';
  }

  // 2. Intel CPUs
  if (/intel|core\s*i[3579]|\bi[3579][-\s]\d|ultra\s*[3579]|core\s*ultra|celeron|pentium|\bc[57][-\s]\d|\bcu[57][-\s]\d/i.test(text)) {
    return 'intel';
  }

  return 'other';
}

// ── Sorting ──────────────────────────────────────────────────────────────────

function sortRows(rows, sortKey) {
  if (sortKey === 'recommended') {
    rows.sort((a, b) => {
      const pA = a.price && a.price > 0 ? a.price : Infinity;
      const pB = b.price && b.price > 0 ? b.price : Infinity;
      if (pA === Infinity && pB === Infinity) return a.title.localeCompare(b.title);
      if (pA === Infinity) return 1;
      if (pB === Infinity) return -1;
      return calcRecommendedScore(b) - calcRecommendedScore(a);
    });
  } else if (sortKey === 'popular') {
    rows.sort((a, b) => {
      const pA = a.price && a.price > 0 ? a.price : Infinity;
      const pB = b.price && b.price > 0 ? b.price : Infinity;
      if (pA === Infinity && pB === Infinity) return a.title.localeCompare(b.title);
      if (pA === Infinity) return 1;
      if (pB === Infinity) return -1;
      return calcPopularityScore(b) - calcPopularityScore(a);
    });
  } else if (sortKey === 'price-asc') {
    rows.sort((a, b) => {
      const pA = a.price && a.price > 0 ? a.price : Infinity;
      const pB = b.price && b.price > 0 ? b.price : Infinity;
      if (pA === pB) return a.title.localeCompare(b.title);
      return pA - pB;
    });
  } else if (sortKey === 'price-desc') {
    rows.sort((a, b) => {
      const pA = a.price && a.price > 0 ? a.price : -1;
      const pB = b.price && b.price > 0 ? b.price : -1;
      if (pA === pB) return a.title.localeCompare(b.title);
      return pB - pA;
    });
  } else if (sortKey === 'name-asc') {
    rows.sort((a, b) => a.title.localeCompare(b.title));
  }
  return rows;
}

// ── Filter Matching Helpers ──────────────────────────────────────────────────

function matchesFilters(r, activeFilters, isSteamActive, searchQuery, minPrice, maxPrice) {
  if (!r.title || !r.id || r.title.toLowerCase() === 'untitled model' || r.title.toLowerCase() === 'untitled') return false;

  // Steam Specs Preset
  if (isSteamActive && !matchesSteamSpecs(r)) return false;

  // Search bar query
  if (searchQuery) {
    const q = searchQuery.toLowerCase();
    const matchTitle = r.title.toLowerCase().includes(q);
    const matchId = r.id.toLowerCase().includes(q);
    const matchVendor = (r.vendor_prices || r.series || '').toLowerCase().includes(q);
    const matchCpu = (r.processor || '').toLowerCase().includes(q);
    const matchGpu = (r.graphics || '').toLowerCase().includes(q);
    if (!matchTitle && !matchId && !matchVendor && !matchCpu && !matchGpu) return false;
  }

  // Price range
  if (!isNaN(minPrice) && r.price < minPrice) return false;
  if (!isNaN(maxPrice) && r.price > maxPrice) return false;

  // Store / Vendor Filter
  if (activeFilters.store.size) {
    const deals = parseVendorDeals(r);
    const hasMatch = deals.some(d => activeFilters.store.has(d.vendor)) || activeFilters.store.has(r.series);
    if (!hasMatch) return false;
  }

  // CPU Filter
  if (activeFilters.cpu.size) {
    const proc = (r.processor || '').replace(/[®™©]/g, '').replace(/\s+/g, ' ').toLowerCase();
    const match = [...activeFilters.cpu].some(v => proc.includes(v.toLowerCase()));
    if (!match) return false;
  }

  // GPU Filter
  if (activeFilters.gpu.size) {
    const gfx = (r.graphics || '').replace(/[®™©]/g, '').toLowerCase();
    const sorted = [...activeFilters.gpu].sort((a, b) => b.length - a.length);
    const match = sorted.some(v => ['Iris', 'integrated'].includes(v) ? isIntegratedGpu(r) : gfx.includes(v.toLowerCase()));
    if (!match) return false;
  }

  // RAM Filter
  if (activeFilters.mem.size) {
    const gb = systemRamGb(r);
    const match = gb != null && [...activeFilters.mem].some(v => v.endsWith('+') ? gb >= parseInt(v) : gb === parseInt(v));
    if (!match) return false;
  }

  // Storage Filter
  if (activeFilters.sto.size) {
    const sto = (r.storage || '').toLowerCase();
    const match = [...activeFilters.sto].some(v => r.verified
      ? r.storage_gb === parseFloat(v) * (/tb/i.test(v) ? 1000 : 1)
      : sto.includes(v.toLowerCase()));
    if (!match) return false;
  }

  // Display Filter
  if (activeFilters.disp.size) {
    const prefix = dispInchPrefix(r.display || r.title);
    if (!prefix) return false;
    const prefixInt = prefix.split('.')[0];
    const match = [...activeFilters.disp].some(v => v === prefix || v === prefixInt);
    if (!match) return false;
  }

  return true;
}

// ── Row Normalization ────────────────────────────────────────────────────────

function normalizeRow(r, i, idPrefix) {
  return { ...r, _rid: r._rid || (idPrefix || 'r') + i, id: r.id || '', title: r.title || 'Untitled model',
    price: Number(r.price) || 0, vendor_count: Number(r.vendor_count) || 1,
    processor: r.processor || '', graphics: r.graphics || '', memory: r.memory || '',
    storage: r.storage || '', display: r.display || '', wifi: r.wifi || '', battery: r.battery || '',
    others: r.others || '', url: r.url || '#', series: r.series || '' };
}
