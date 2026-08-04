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

function formatImgUrl(raw, vendorStr) {
  if (!raw) return '';
  let u = raw.trim();
  if (u.startsWith('//')) return 'https:' + u;
  if (u.startsWith('http://') || u.startsWith('https://')) return u.replace(/([^:])\/{2,}/g, '$1/');
  if (u.startsWith('/')) {
    const v = (vendorStr || '').toLowerCase();
    if (v.includes('techhypermart')) return 'https://www.techhypermart.com' + u;
    if (v.includes('pcimage') || v.includes('pc image')) return 'https://store.pcimage.com.my' + u;
    if (v.includes('all it') || v.includes('allit')) return 'https://www.allithypermarket.com.my' + u;
    if (v.includes('acer')) return 'https://store.acer.com' + u;
    return 'https://p3-ofp.static.pub' + u;
  }
  return u;
}

function fmtPrice(n) {
  if (!n) return 'RM -';
  return 'RM ' + n.toLocaleString('en-MY', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ── Data Loading ─────────────────────────────────────────────────────────────

function loadData(callback) {
  // Try JSON first (smaller, faster), fall back to CSV
  fetch('laptops.json')
    .then(res => {
      if (!res.ok) throw new Error('JSON not found');
      return res.json();
    })
    .then(data => {
      console.log('[core] Loaded laptops.json (' + data.length + ' rows)');
      callback(data);
    })
    .catch(() => {
      console.log('[core] laptops.json not available, falling back to CSV...');
      Papa.parse('master_laptops.csv', {
        download: true,
        header: true,
        skipEmptyLines: true,
        complete: function (results) {
          console.log('[core] Loaded master_laptops.csv (' + results.data.length + ' rows)');
          callback(results.data);
        },
        error: function (err) {
          console.error('[core] Error loading data:', err);
          callback([]);
        }
      });
    });
}

// ── Vendor Deal Parsing ──────────────────────────────────────────────────────

function parseVendorDeals(r) {
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

// ── Steam Hardware Survey Matching (July 2026) ──────────────────────────────

function matchesSteamSpecs(r) {
  // 1. System RAM: 16 GB or higher (40.97% Steam Share)
  const memStr = (r.memory || r.title || '').toLowerCase();
  const memMatch = memStr.match(/(\d+)\s*gb/i);
  let ramGb = memMatch ? parseInt(memMatch[1]) : 0;
  if (ramGb > 0 && ramGb < 16) return false;

  // 2. Video Card: NVIDIA GeForce RTX (72.72% NVIDIA Market Share)
  const gfxStr = (r.graphics || r.title || '').toLowerCase();
  const hasRtxGpu = /rtx\s*(30|40|50)\d{2}/i.test(gfxStr) || /geforce\s+rtx/i.test(gfxStr);
  if (!hasRtxGpu) return false;

  // 3. Physical CPUs: 6 to 8+ Core Processor (55.37% Combined)
  const cpuStr = (r.processor || r.title || '').toLowerCase();
  const hasSteamCpu = /i5|i7|i9|ultra\s*[579]|ryzen\s*[579]/i.test(cpuStr);
  if (!hasSteamCpu) return false;

  return true;
}

// ── Scoring ──────────────────────────────────────────────────────────────────

function calcRecommendedScore(r) {
  let specPoints = 0;

  // GPU Tier Points
  const gfx = (r.graphics || r.title || '').toLowerCase();
  if (gfx.includes('5090') || gfx.includes('4090')) specPoints += 100;
  else if (gfx.includes('5080') || gfx.includes('4080')) specPoints += 85;
  else if (gfx.includes('5070') || gfx.includes('4070')) specPoints += 70;
  else if (gfx.includes('5060') || gfx.includes('4060')) specPoints += 55;
  else if (gfx.includes('5050') || gfx.includes('4050') || gfx.includes('3060') || gfx.includes('3050')) specPoints += 40;
  else specPoints += 15;

  // RAM Points
  const mem = (r.memory || r.title || '').toLowerCase();
  if (mem.includes('64gb')) specPoints += 40;
  else if (mem.includes('32gb')) specPoints += 30;
  else if (mem.includes('16gb')) specPoints += 20;

  // CPU Points
  const cpu = (r.processor || r.title || '').toLowerCase();
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
  const gfx = (r.graphics || r.title || '').toLowerCase();
  if (gfx.includes('4060')) score += 50;
  else if (gfx.includes('3060')) score += 45;
  else if (gfx.includes('5060')) score += 40;
  else if (gfx.includes('4050') || gfx.includes('3050')) score += 35;
  else if (gfx.includes('4070') || gfx.includes('5070')) score += 30;

  // 3. Most Popular RAM (16GB #1 at 41%, 32GB #2)
  const mem = (r.memory || r.title || '').toLowerCase();
  if (mem.includes('16gb') || mem.includes('16 gb')) score += 40;
  else if (mem.includes('32gb') || mem.includes('32 gb')) score += 30;

  // 4. Most Popular CPU Tiers
  const cpu = (r.processor || r.title || '').toLowerCase();
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

function detectBrand(proc) {
  const t = (proc || '').toLowerCase();
  if (t.includes('intel')) return 'intel';
  if (t.includes('amd') || t.includes('ryzen')) return 'amd';
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
    const proc = (r.processor || r.title || '').replace(/[®™©]/g, '').replace(/\s+/g, ' ').toLowerCase();
    const match = [...activeFilters.cpu].some(v => proc.includes(v.toLowerCase()));
    if (!match) return false;
  }

  // GPU Filter
  if (activeFilters.gpu.size) {
    const gfx = (r.graphics || r.title || '').replace(/[®™©]/g, '').toLowerCase();
    const sorted = [...activeFilters.gpu].sort((a, b) => b.length - a.length);
    const match = sorted.some(v => gfx.includes(v.toLowerCase()));
    if (!match) return false;
  }

  // RAM Filter
  if (activeFilters.mem.size) {
    const mem = (r.memory || r.title || '').toLowerCase();
    const match = [...activeFilters.mem].some(v => mem.includes(v.toLowerCase()));
    if (!match) return false;
  }

  // Storage Filter
  if (activeFilters.sto.size) {
    const sto = (r.storage || r.title || '').toLowerCase();
    const match = [...activeFilters.sto].some(v => sto.includes(v.toLowerCase()));
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
  return {
    _rid: (idPrefix || 'r') + i,
    id: r.id || '',
    title: r.title || 'Untitled model',
    price: parseFloat(r.price) || 0,
    best_vendor: r.best_vendor || '',
    vendor_prices: r.vendor_prices || '',
    vendor_count: parseInt(r.vendor_count) || 1,
    vendor_urls: r.vendor_urls || '',
    image_url: r.image_url || '',
    processor: r.processor || '',
    graphics: r.graphics || '',
    memory: r.memory || '',
    storage: r.storage || '',
    display: r.display || '',
    wifi: r.wifi || '',
    battery: r.battery || '',
    others: r.others || '',
    series: r.series || 'Store Catalog',
    url: (() => {
      let u = r.url || '#';
      if (u !== '#' && u.includes('lenovo.com') && !u.includes('/my/en/')) {
        u = u.replace('https://www.lenovo.com', 'https://www.lenovo.com/my/en');
      }
      return u;
    })()
  };
}
