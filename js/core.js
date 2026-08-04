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
  if (window.preloadedRows && Array.isArray(window.preloadedRows) && window.preloadedRows.length > 0) {
    console.log('[core] Loaded preloadedRows (' + window.preloadedRows.length + ' rows)');
    return callback(window.preloadedRows);
  }

  // Try JSON endpoints, fall back to CSV
  fetch('data/laptops.json')
    .catch(() => fetch('laptops.json'))
    .then(res => {
      if (!res.ok) throw new Error('JSON not found');
      return res.json();
    })
    .then(data => {
      console.log('[core] Loaded laptops.json (' + data.length + ' rows)');
      callback(data);
    })
    .catch(() => {
      console.log('[core] JSON not available, falling back to CSV...');
      Papa.parse('data/master_laptops.csv', {
        download: true,
        header: true,
        skipEmptyLines: true,
        complete: function (results) {
          console.log('[core] Loaded data/master_laptops.csv (' + results.data.length + ' rows)');
          callback(results.data);
        },
        error: function () {
          Papa.parse('master_laptops.csv', {
            download: true,
            header: true,
            skipEmptyLines: true,
            complete: function (res2) {
              console.log('[core] Loaded master_laptops.csv (' + res2.data.length + ' rows)');
              callback(res2.data);
            },
            error: function (err) {
              console.error('[core] Error loading data:', err);
              callback([]);
            }
          });
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
  const fullText = `${r.processor || ''} ${r.graphics || ''} ${r.memory || ''} ${r.title || ''} ${r.others || ''}`.toLowerCase();

  // 1. Realistic Price Cap for Steam Survey Laptops (under RM 10,000)
  const pVal = typeof r.price === 'number' ? r.price : (parseFloat(r.price) || 0);
  if (pVal > 10000) return false;

  // 2. Realistic RAM Spec: 16GB to 32GB (Steam #1 & #2 Share)
  const memMatch = fullText.match(/(\d+)\s*gb/i);
  let ramGb = memMatch ? parseInt(memMatch[1], 10) : 0;
  if (ramGb === 0 && /16\s*gb|32\s*gb|16gb|32gb/i.test(fullText)) {
    ramGb = 16;
  }
  if (ramGb > 0 && (ramGb < 16 || ramGb > 32)) return false;

  // 3. Realistic GPU Spec: Steam sweet-spot gaming GPUs (RTX 3050, 3060, 3070, 4050, 4060, 4070, 5050, 5060, 5070, GTX 1650/1660)
  // Exclude extreme workstation / ultra-flagships (RTX 4080, 4090, 5080, 5090, Quadro)
  if (/4080|4090|5080|5090|quadro|workstation|rtx\s*a\d{4}/i.test(fullText)) return false;

  const hasRealisticGpu = /(3050|3060|3070|4050|4060|4070|5050|5060|5070|gtx\s*1650|gtx\s*1660)/i.test(fullText);
  if (!hasRealisticGpu) return false;

  // 4. Realistic CPU Spec: 6 to 8+ Core Mainstream CPUs (i5, i7, Ultra 5, Ultra 7, Ryzen 5, Ryzen 7)
  const hasRealisticCpu = /i5|i7|ultra\s*[57]|ryzen\s*[57]/i.test(fullText) || /\b(6|8|10|12|14|16)\s*core[s]?\b/i.test(fullText);
  if (!hasRealisticCpu) return false;

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

function extractTitleSpecs(title, others) {
  const text = (title + ' ' + (others || '')).trim();
  let proc = '', gfx = '', mem = '', sto = '', disp = '';

  const mCpu = text.match(/\b(Intel®?\s*Core™?\s*(?:Ultra\s*)?[iI\d][\w\d-]+\s*(?:processor)?|AMD\s*Ryzen™?\s*\d[\w\d-]+|Core\s*Ultra\s*\d\s*\d+[\w\d]*|[iI][3579][-\s]\d{4,5}[\w\d]*|Athlon[\w\d\s-]*|C5-\d+[\w\d]*|CU5-\d+[\w\d]*)\b/i);
  if (mCpu) proc = mCpu[1].trim();

  const mGpu = text.match(/\b(NVIDIA®?\s*GeForce\s*RTX™?\s*\d{4}\b[\w\d\s]*|RTX\s*\d{4}\b[\w\d\s]*|GTX\s*\d{4}\b[\w\d\s]*|AMD\s*Radeon™?\s*[\w\d\s]*|Intel®?\s*(?:Arc|Graphics|Iris\s*Xe)\b[\w\d\s]*)\b/i);
  if (mGpu) gfx = mGpu[1].trim();

  const mRam = text.match(/\b(\d{1,2}\s*GB\s*(?:DDR[45]|LPDDR[45]X?|RAM)?)\b/i);
  if (mRam) mem = mRam[1].trim();

  const mSto = text.match(/\b((?:\d{3,4}\s*GB|\d\s*TB)\s*(?:PCIe|NVMe|Gen\d|SSD)?)\b/i);
  if (mSto) sto = mSto[1].trim();

  const mDisp = text.match(/\b(1[34567]\.?[0-6]?"?\s*(?:diagonal)?\s*(?:FHD|WUXGA|QHD\+?|4K|2\.5K|OLED|IPS|144Hz|165Hz|240Hz)?)\b/i);
  if (mDisp) disp = mDisp[1].trim();

  return { proc, gfx, mem, sto, disp };
}

function normalizeRow(r, i, idPrefix) {
  const title = r.title || 'Untitled model';
  const parsed = extractTitleSpecs(title, r.others);

  return {
    _rid: (idPrefix || 'r') + i,
    id: r.id || '',
    title: title,
    price: parseFloat(r.price) || 0,
    best_vendor: r.best_vendor || '',
    vendor_prices: r.vendor_prices || '',
    vendor_count: parseInt(r.vendor_count) || 1,
    vendor_urls: r.vendor_urls || '',
    image_url: r.image_url || '',
    processor: r.processor && r.processor.length >= 3 ? r.processor : (parsed.proc || r.processor || ''),
    graphics: r.graphics && r.graphics.length >= 3 ? r.graphics : (parsed.gfx || r.graphics || ''),
    memory: r.memory && r.memory.length >= 2 ? r.memory : (parsed.mem || r.memory || ''),
    storage: r.storage && r.storage.length >= 2 ? r.storage : (parsed.sto || r.storage || ''),
    display: r.display && r.display.length >= 3 ? r.display : (parsed.disp || r.display || ''),
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
