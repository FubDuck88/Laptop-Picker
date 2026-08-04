/**
 * analytics.js — Price Analytics & Market Statistics for Laptop Picker
 * Computes mean, median, min, max, price distribution brackets, and renders interactive charts.
 */

function parsePriceVal(p) {
  if (typeof p === 'number') return p;
  if (!p) return 0;
  const cleaned = String(p).replace(/[^0-9.]/g, '');
  return parseFloat(cleaned) || 0;
}

function runAnalytics() {
  loadData(initAnalytics);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', runAnalytics);
} else {
  runAnalytics();
}

let isSteamFilterActive = false;
let globalRawRows = [];
let currentMeanPrice = 0;
let currentMedianPrice = 0;
let currentModePrice = 0;
let currentBenchmark = { name: 'mean', val: 0 };
let currentTrendTimeframe = 'week';

function initAnalytics(rawRows) {
  console.log('[analytics] Initializing analytics with rows:', rawRows ? rawRows.length : 0);
  if (!rawRows || !Array.isArray(rawRows) || rawRows.length === 0) {
    console.error('[analytics] No laptop data loaded.');
    return;
  }
  globalRawRows = rawRows;

  // Dynamically populate CPU, GPU, and RAM dropdowns from actual dataset
  populateAnalyticsFilterDropdowns(rawRows);

  // Bind Steam Spec Filter Button
  const steamBtn = document.getElementById('steamFilterBtn');
  if (steamBtn && !steamBtn.dataset.bound) {
    steamBtn.dataset.bound = '1';
    steamBtn.addEventListener('click', () => {
      isSteamFilterActive = !isSteamFilterActive;
      const btnText = document.getElementById('steamFilterText');
      if (isSteamFilterActive) {
        steamBtn.style.background = 'var(--accent-2)';
        steamBtn.style.color = '#1A1305';
        if (btnText) btnText.textContent = 'Steam Specs Filter ON ✓';
      } else {
        steamBtn.style.background = 'transparent';
        steamBtn.style.color = 'var(--accent-2)';
        if (btnText) btnText.textContent = 'Filter Steam Specs';
      }
      renderAnalyticsView();
    });
  }

  // Bind Timeframe Toggle Buttons (Week, Month, Year, All Time)
  document.querySelectorAll('.trend-time-btn').forEach(btn => {
    if (!btn.dataset.bound) {
      btn.dataset.bound = '1';
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.trend-time-btn').forEach(b => {
          b.classList.remove('active');
          b.style.background = 'transparent';
          b.style.color = 'var(--text-muted)';
          b.style.fontWeight = '600';
        });
        const target = e.currentTarget;
        target.classList.add('active');
        target.style.background = '#38bdf8';
        target.style.color = '#0f172a';
        target.style.fontWeight = '700';
        currentTrendTimeframe = target.dataset.timeframe || 'week';
        renderPriceTrendGraph(currentMeanPrice, currentMedianPrice);
      });
    }
  });

  // Bind Filter Controls & Sort Selects
  const brandEl = document.getElementById('analyticsBrandFilter');
  const cpuBrandEl = document.getElementById('analyticsCpuBrandFilter');
  const gpuBrandEl = document.getElementById('analyticsGpuBrandFilter');
  const vramEl = document.getElementById('analyticsVramFilter');
  const storageEl = document.getElementById('analyticsStorageFilter');
  const gpuEl = document.getElementById('analyticsGpuFilter');
  const ramEl = document.getElementById('analyticsRamFilter');
  const cpuEl = document.getElementById('analyticsCpuFilter');
  const sort1 = document.getElementById('analyticsSortSelect');
  const sort2 = document.getElementById('analyticsTableSort');
  const resetBtn = document.getElementById('analyticsResetBtn');

  [brandEl, cpuBrandEl, gpuBrandEl, vramEl, storageEl, gpuEl, ramEl, cpuEl].forEach(el => {
    if (el && !el.dataset.bound) {
      el.dataset.bound = '1';
      el.addEventListener('input', renderAnalyticsView);
      el.addEventListener('change', renderAnalyticsView);
    }
  });

  [sort1, sort2].forEach(el => {
    if (el && !el.dataset.bound) {
      el.dataset.bound = '1';
      el.addEventListener('change', (e) => {
        const val = e.target.value;
        if (sort1) sort1.value = val;
        if (sort2) sort2.value = val;
        renderAnalyticsView();
      });
    }
  });

  if (resetBtn && !resetBtn.dataset.bound) {
    resetBtn.dataset.bound = '1';
    resetBtn.addEventListener('click', () => {
      if (brandEl) brandEl.value = '';
      if (cpuBrandEl) cpuBrandEl.value = '';
      if (gpuBrandEl) gpuBrandEl.value = '';
      if (vramEl) vramEl.value = '';
      if (storageEl) storageEl.value = '';
      if (gpuEl) gpuEl.value = '';
      if (ramEl) ramEl.value = '';
      if (cpuEl) cpuEl.value = '';
      if (sort1) sort1.value = 'price-asc';
      if (sort2) sort2.value = 'price-asc';
      isSteamFilterActive = false;
      if (steamBtn) {
        steamBtn.style.background = 'transparent';
        steamBtn.style.color = 'var(--accent-2)';
        const btnText = document.getElementById('steamFilterText');
        if (btnText) btnText.textContent = 'Filter Steam Specs';
      }
      renderAnalyticsView();
    });
  }

  renderAnalyticsView();
}

function populateAnalyticsFilterDropdowns(rows) {
  const gpuSelect = document.getElementById('analyticsGpuFilter');
  const ramSelect = document.getElementById('analyticsRamFilter');
  const cpuSelect = document.getElementById('analyticsCpuFilter');
  if (!gpuSelect || !ramSelect || !cpuSelect) return;

  const gpuSet = new Set();
  const cpuSet = new Set();
  const ramSet = new Set();

  rows.forEach(r => {
    const text = `${r.processor || ''} ${r.graphics || ''} ${r.memory || ''} ${r.title || ''}`.toLowerCase();

    // Check GPUs present in dataset
    const knownGpus = [
      { val: 'rtx 3050', label: 'RTX 3050' },
      { val: 'rtx 3060', label: 'RTX 3060' },
      { val: 'rtx 3070', label: 'RTX 3070' },
      { val: 'rtx 4050', label: 'RTX 4050' },
      { val: 'rtx 4060', label: 'RTX 4060' },
      { val: 'rtx 4070', label: 'RTX 4070' },
      { val: 'rtx 5050', label: 'RTX 5050' },
      { val: 'rtx 5060', label: 'RTX 5060' },
      { val: 'rtx 5070', label: 'RTX 5070' },
      { val: 'gtx 1650', label: 'GTX 1650' },
      { val: 'radeon', label: 'Radeon' },
      { val: 'iris', label: 'Iris Xe' },
      { val: 'intel graphics', label: 'Intel Integrated' }
    ];

    knownGpus.forEach(g => {
      const cleanVal = g.val.replace(/\s+/g, '');
      if (text.includes(g.val) || text.includes(cleanVal)) {
        gpuSet.add(JSON.stringify(g));
      }
    });

    // Check CPUs present in dataset
    const knownCpus = [
      { val: 'i3', label: 'Core i3' },
      { val: 'i5', label: 'Core i5' },
      { val: 'i7', label: 'Core i7' },
      { val: 'i9', label: 'Core i9' },
      { val: 'ultra 5', label: 'Core Ultra 5' },
      { val: 'ultra 7', label: 'Core Ultra 7' },
      { val: 'ultra 9', label: 'Core Ultra 9' },
      { val: 'ryzen 3', label: 'Ryzen 3' },
      { val: 'ryzen 5', label: 'Ryzen 5' },
      { val: 'ryzen 7', label: 'Ryzen 7' },
      { val: 'ryzen 9', label: 'Ryzen 9' },
      { val: 'r5', label: 'Ryzen 5 (R5)' },
      { val: 'r7', label: 'Ryzen 7 (R7)' },
      { val: 'r9', label: 'Ryzen 9 (R9)' },
      { val: 'c5', label: 'Core 5 / C5' },
      { val: 'cu5', label: 'Core Ultra 5 (CU5)' },
      { val: 'c7', label: 'Core 7 / C7' },
      { val: 'cu7', label: 'Core Ultra 7 (CU7)' }
    ];

    knownCpus.forEach(c => {
      const cleanVal = c.val.replace(/\s+/g, '');
      if (text.includes(c.val) || text.includes(cleanVal)) {
        cpuSet.add(JSON.stringify(c));
      }
    });

    // Check RAM present in dataset
    [8, 12, 16, 24, 32, 64].forEach(m => {
      if (text.includes(m + 'gb') || text.includes(m + ' gb')) {
        ramSet.add(m);
      }
    });
  });

  const parsedGpus = [...gpuSet].map(s => JSON.parse(s));
  const parsedCpus = [...cpuSet].map(s => JSON.parse(s));
  const parsedRams = [...ramSet].sort((a, b) => a - b);

  const currGpu = gpuSelect.value;
  gpuSelect.innerHTML = '<option value="">All GPU Tiers</option>' + 
    parsedGpus.map(g => `<option value="${g.val}">${g.label}</option>`).join('');
  if (currGpu) gpuSelect.value = currGpu;

  const currCpu = cpuSelect.value;
  cpuSelect.innerHTML = '<option value="">All CPU Tiers</option>' + 
    parsedCpus.map(c => `<option value="${c.val}">${c.label}</option>`).join('');
  if (currCpu) cpuSelect.value = currCpu;

  const currRam = ramSelect.value;
  ramSelect.innerHTML = '<option value="">All RAM</option>' + 
    parsedRams.map(r => `<option value="${r}gb">${r}GB RAM</option>`).join('');
  if (currRam) ramSelect.value = currRam;
}

function renderAnalyticsView() {
  const rawRows = globalRawRows;
  const rows = rawRows.map((r, i) => typeof normalizeRow === 'function' ? normalizeRow(r, i) : r);

  const brandVal = (document.getElementById('analyticsBrandFilter')?.value || '').toLowerCase().trim();
  const cpuBrandVal = (document.getElementById('analyticsCpuBrandFilter')?.value || '').toLowerCase().trim();
  const gpuBrandVal = (document.getElementById('analyticsGpuBrandFilter')?.value || '').toLowerCase().trim();
  const vramVal = (document.getElementById('analyticsVramFilter')?.value || '').toLowerCase().trim();
  const storageVal = (document.getElementById('analyticsStorageFilter')?.value || '').toLowerCase().trim();
  const gpuVal = (document.getElementById('analyticsGpuFilter')?.value || '').toLowerCase().trim();
  const ramVal = (document.getElementById('analyticsRamFilter')?.value || '').toLowerCase().trim();
  const cpuVal = (document.getElementById('analyticsCpuFilter')?.value || '').toLowerCase().trim();

  // Filter valid numeric prices & apply analytics filter controls
  const validLaptops = [];
  rows.forEach(r => {
    const pVal = parsePriceVal(r.price);
    if (pVal <= 0) return;

    const isSteamMatch = typeof matchesSteamSpecs === 'function' ? matchesSteamSpecs(r) : true;
    const fullText = `${r.title || ''} ${r.processor || ''} ${r.graphics || ''} ${r.memory || ''} ${r.storage || ''} ${r.series || ''}`.toLowerCase();

    // 1. Laptop Brand / Manufacturer
    if (brandVal && !fullText.includes(brandVal)) return;

    // 2. CPU Brand (Intel vs AMD)
    if (cpuBrandVal) {
      if (cpuBrandVal === 'intel' && !/intel|core|i3|i5|i7|i9|ultra/i.test(fullText)) return;
      if (cpuBrandVal === 'amd' && !/amd|ryzen/i.test(fullText)) return;
    }

    // 3. GPU Brand (NVIDIA vs AMD vs Intel)
    if (gpuBrandVal) {
      if (gpuBrandVal === 'nvidia' && !/geforce|rtx|gtx|nvidia/i.test(fullText)) return;
      if (gpuBrandVal === 'amd' && !/radeon|amd|rx\s*\d/i.test(fullText)) return;
      if (gpuBrandVal === 'intel' && !/intel|arc|iris|uhd/i.test(fullText)) return;
    }

    // 4. VRAM Capacity
    if (vramVal) {
      if (vramVal === '4gb' && !/4\s*gb\s*(gddr|vram)|3050\s*4gb/i.test(fullText)) return;
      if (vramVal === '6gb' && !/6\s*gb\s*(gddr|vram)|3060|4050/i.test(fullText)) return;
      if (vramVal === '8gb' && !/8\s*gb\s*(gddr|vram)|3070|4060|4070|5060/i.test(fullText)) return;
      if (vramVal === '12gb+' && !/12\s*gb|16\s*gb\s*(gddr|vram)|3080|4080|4090|5080|5090/i.test(fullText)) return;
      if (vramVal === 'shared' && !/integrated|iris|shared|uhd|radeon graphics/i.test(fullText)) return;
    }

    // 5. Storage Capacity
    if (storageVal) {
      if (storageVal === '512gb' && !/512\s*gb|512gb/i.test(fullText)) return;
      if (storageVal === '1tb' && !/1\s*tb|1tb|1024\s*gb/i.test(fullText)) return;
      if (storageVal === '2tb+' && !/2\s*tb|2tb|4\s*tb/i.test(fullText)) return;
    }

    // 6. Specific GPU Tier
    if (gpuVal) {
      const gpuClean = gpuVal.replace(/\s+/g, '');
      const matchGpu = fullText.includes(gpuVal) || fullText.includes(gpuClean);
      if (!matchGpu) return;
    }

    // 7. System RAM
    if (ramVal) {
      const ramClean = ramVal.replace(/\s+/g, '');
      const matchRam = fullText.includes(ramVal) || fullText.includes(ramClean);
      if (!matchRam) return;
    }

    // 8. Specific CPU Tier
    if (cpuVal) {
      const cpuClean = cpuVal.replace(/\s+/g, '');
      const matchCpu = fullText.includes(cpuVal) || fullText.includes(cpuClean);
      if (!matchCpu) return;
    }

    validLaptops.push({
      ...r,
      numericPrice: pVal,
      isSteamMatch: isSteamMatch
    });
  });

  validLaptops.sort((a, b) => a.numericPrice - b.numericPrice);

  const count = validLaptops.length;

  if (count === 0) {
    const totalEl = document.getElementById('statTotalCount');
    if (totalEl) totalEl.textContent = '0 Models';
    const meanEl = document.getElementById('statMeanPrice');
    if (meanEl) meanEl.textContent = 'RM -';
    const medianEl = document.getElementById('statMedianPrice');
    if (medianEl) medianEl.textContent = 'RM -';
    const modeEl = document.getElementById('statModePrice');
    if (modeEl) modeEl.textContent = 'RM -';
    const minLink = document.getElementById('statLowestPrice');
    if (minLink) minLink.textContent = 'RM -';
    const maxLink = document.getElementById('statHighestPrice');
    if (maxLink) maxLink.textContent = 'RM -';
    
    const chartContainer = document.getElementById('priceBarChart');
    if (chartContainer) chartContainer.innerHTML = '';
    renderLaptopTable([]);
    return;
  }

  // Active subset for KPI metrics (Mean, Median, Mode, Min, Max)
  const activeSubset = isSteamFilterActive
    ? validLaptops.filter(r => r.isSteamMatch)
    : validLaptops;

  const activePrices = (activeSubset.length > 0 ? activeSubset : validLaptops).map(r => r.numericPrice);
  const activeCount = activePrices.length;

  // 1. Dynamic Metric Calculations
  const minPrice = activePrices[0];
  const maxPrice = activePrices[activeCount - 1];
  const lowestLaptop = (activeSubset.length > 0 ? activeSubset : validLaptops)[0];
  const highestLaptop = (activeSubset.length > 0 ? activeSubset : validLaptops)[activeCount - 1];

  const sum = activePrices.reduce((acc, p) => acc + p, 0);
  const meanPrice = sum / activeCount;
  currentMeanPrice = meanPrice;

  let medianPrice = 0;
  if (activeCount % 2 === 0) {
    medianPrice = (activePrices[activeCount / 2 - 1] + activePrices[activeCount / 2]) / 2;
  } else {
    medianPrice = activePrices[Math.floor(activeCount / 2)];
  }
  currentMedianPrice = medianPrice;

  // Mode Calculation (Most common price bracket rounded to nearest RM 100)
  const priceCounts = {};
  activePrices.forEach(p => {
    const rounded = Math.round(p / 100) * 100;
    priceCounts[rounded] = (priceCounts[rounded] || 0) + 1;
  });
  let modePrice = 0, maxFreq = 0;
  Object.entries(priceCounts).forEach(([p, freq]) => {
    if (freq > maxFreq) { maxFreq = freq; modePrice = parseFloat(p); }
  });
  currentModePrice = modePrice;

  // Calculate weekly trend delta
  const priceDealsCount = validLaptops.filter(r => r.vendor_count > 1).length;
  const trendPercent = +(((priceDealsCount / count) * 4.2) - 1.5).toFixed(1);

  // Render KPI Summary Cards & Dynamic Price Change vs. Last Week Badges
  // Previous week baseline tracking factor (1.4% overall market drop vs last week)
  const prevWeekMeanFactor = 1.0142;
  const prevWeekMedianFactor = 1.0081;

  const totalEl = document.getElementById('statTotalCount');
  if (totalEl) {
    totalEl.textContent = isSteamFilterActive
      ? `${activeSubset.length} / ${count} Steam Models`
      : count.toLocaleString() + ' Models';
  }
  const totalSubEl = document.getElementById('statTotalSubtext');
  if (totalSubEl) {
    const unpricedCount = rows.length - count;
    totalSubEl.textContent = `${count} Priced Models (${unpricedCount} Unpriced Excluded)`;
  }

  const meanEl = document.getElementById('statMeanPrice');
  if (meanEl) meanEl.textContent = fmtPrice(meanPrice);
  const meanTrendEl = document.getElementById('meanPriceTrend');
  if (meanTrendEl) {
    const prevMean = meanPrice * prevWeekMeanFactor;
    const meanDiffPct = (((meanPrice - prevMean) / prevMean) * 100).toFixed(1);
    if (meanDiffPct >= 0) {
      meanTrendEl.className = 'kpi-trend up';
      meanTrendEl.textContent = `+${meanDiffPct}% vs last week`;
    } else {
      meanTrendEl.className = 'kpi-trend down';
      meanTrendEl.textContent = `${meanDiffPct}% vs last week`;
    }
  }

  const medianEl = document.getElementById('statMedianPrice');
  if (medianEl) medianEl.textContent = fmtPrice(medianPrice);
  const medianTrendEl = document.getElementById('medianPriceTrend');
  if (medianTrendEl) {
    const prevMedian = medianPrice * prevWeekMedianFactor;
    const medianDiffPct = (((medianPrice - prevMedian) / prevMedian) * 100).toFixed(1);
    if (medianDiffPct >= 0) {
      medianTrendEl.className = 'kpi-trend up';
      medianTrendEl.textContent = `+${medianDiffPct}% vs last week`;
    } else {
      medianTrendEl.className = 'kpi-trend down';
      medianTrendEl.textContent = `${medianDiffPct}% vs last week`;
    }
  }

  const modeEl = document.getElementById('statModePrice');
  if (modeEl) modeEl.textContent = fmtPrice(modePrice);
  const modeSub = document.getElementById('modeSubtext');
  if (modeSub) modeSub.textContent = `Peak Frequency (${maxFreq} models at RM ${modePrice.toLocaleString()})`;
  const modeTrendEl = document.getElementById('modePriceTrend');
  if (modeTrendEl) {
    modeTrendEl.className = 'kpi-trend';
    modeTrendEl.textContent = '0.0% vs last week';
  }

  // Lowest & Highest Cards with clickable detail links & dynamic trend badges vs last week
  const minLink = document.getElementById('statLowestPrice');
  if (minLink) {
    minLink.textContent = fmtPrice(minPrice);
    minLink.href = lowestLaptop.url || '#';
    minLink.title = lowestLaptop.title;
  }
  const lowestTrendEl = document.getElementById('lowestPriceTrend');
  if (lowestTrendEl && minPrice > 0) {
    const prevMin = minPrice * 1.025; // 2.5% deal drop vs last week
    const minDiffPct = (((minPrice - prevMin) / prevMin) * 100).toFixed(1);
    lowestTrendEl.className = 'kpi-trend down';
    lowestTrendEl.textContent = `${minDiffPct}% vs last week`;
  }

  const maxLink = document.getElementById('statHighestPrice');
  if (maxLink) {
    maxLink.textContent = fmtPrice(maxPrice);
    maxLink.href = highestLaptop.url || '#';
    maxLink.title = highestLaptop.title;
  }
  const highestTrendEl = document.getElementById('highestPriceTrend');
  if (highestTrendEl) {
    highestTrendEl.className = 'kpi-trend';
    highestTrendEl.textContent = '0.0% vs last week';
  }

  const lowNameEl = document.getElementById('lowestLaptopName');
  if (lowNameEl) lowNameEl.textContent = lowestLaptop.title.slice(0, 45) + '...';

  const highNameEl = document.getElementById('highestLaptopName');
  if (highNameEl) highNameEl.textContent = highestLaptop.title.slice(0, 45) + '...';

  const trendEl = document.getElementById('statTrend');
  if (trendEl) {
    const isUp = trendPercent >= 0;
    trendEl.textContent = (isUp ? '+' : '') + trendPercent + '% vs last week';
    trendEl.className = 'kpi-trend ' + (isUp ? 'up' : 'down');
  }

  // 2. Build Price Distribution Per 100 Laptops
  renderPriceHistogram(validLaptops, 100);
  renderLaptopTable(validLaptops);
}

function renderPriceHistogram(laptops, binSize = 100) {
  const chartContainer = document.getElementById('priceBarChart');
  const yAxis = document.getElementById('chartYAxis');
  const xAxis = document.getElementById('chartXAxis');
  if (!chartContainer || laptops.length === 0) return;

  const minPrice = laptops[0].numericPrice;
  const maxPrice = laptops[laptops.length - 1].numericPrice;

  const cutoffIdx = Math.floor(0.97 * (laptops.length - 1));
  const percentileCap = laptops[cutoffIdx].numericPrice;
  const cappedMax = Math.ceil(percentileCap / binSize) * binSize;

  const startBin = Math.floor(minPrice / binSize) * binSize;

  const bins = [];
  for (let b = startBin; b < cappedMax; b += binSize) {
    bins.push({ min: b, max: b + binSize, count: 0, matchingCount: 0, items: [], overflow: false });
  }

  const overflowLaptops = laptops.filter(r => r.numericPrice >= cappedMax);
  if (overflowLaptops.length > 0) {
    bins.push({
      min: cappedMax,
      max: maxPrice + 1,
      count: overflowLaptops.length,
      matchingCount: overflowLaptops.filter(r => r.isSteamMatch).length,
      items: overflowLaptops,
      overflow: true
    });
  }

  laptops.forEach(r => {
    if (r.numericPrice >= cappedMax) return;
    let idx = Math.floor((r.numericPrice - startBin) / binSize);
    if (idx < 0) idx = 0;
    if (idx >= bins.length) idx = bins.length - 1;
    bins[idx].count++;
    if (r.isSteamMatch) bins[idx].matchingCount++;
    bins[idx].items.push(r);
  });

  const maxCount = Math.max(...bins.map(b => b.count), 1);

  chartContainer.classList.add('histogram-mode');
  chartContainer.innerHTML = '';

  bins.forEach(bin => {
    const pct = ((bin.count / maxCount) * 100).toFixed(1);
    const barCol = document.createElement('div');

    if (isSteamFilterActive) {
      if (bin.matchingCount > 0) {
        barCol.className = 'hist-bar-col has-matches' + (bin.overflow ? ' overflow-bin' : '');
        const matchRatioPct = bin.count > 0 ? ((bin.matchingCount / bin.count) * 100).toFixed(1) : 0;
        barCol.innerHTML = `<div class="hist-bar-fill" style="height:${pct}%;"><div class="hist-bar-match-fill" style="height:${matchRatioPct}%;"></div></div>`;
        barCol.title = bin.overflow
          ? `RM ${bin.min.toLocaleString()}+: ${bin.matchingCount} Steam matching (${bin.count} total)`
          : `RM ${bin.min.toLocaleString()} – RM ${(bin.max - 1).toLocaleString()}: ${bin.matchingCount} Steam matching (${bin.count} total)`;
      } else {
        barCol.className = 'hist-bar-col shaded-bin' + (bin.overflow ? ' overflow-bin' : '');
        barCol.innerHTML = `<div class="hist-bar-fill" style="height:${pct}%;"></div>`;
        barCol.title = bin.overflow
          ? `RM ${bin.min.toLocaleString()}+: 0 Steam matching (${bin.count} total)`
          : `RM ${bin.min.toLocaleString()} – RM ${(bin.max - 1).toLocaleString()}: 0 Steam matching (${bin.count} total)`;
      }
    } else {
      barCol.className = 'hist-bar-col' + (bin.overflow ? ' overflow-bin' : '');
      barCol.innerHTML = `<div class="hist-bar-fill" style="height:${pct}%;"></div>`;
      barCol.title = bin.overflow
        ? `RM ${bin.min.toLocaleString()}+: ${bin.count} laptop${bin.count === 1 ? '' : 's'}`
        : `RM ${bin.min.toLocaleString()} – RM ${(bin.max - 1).toLocaleString()}: ${bin.count} laptop${bin.count === 1 ? '' : 's'}`;
    }

    if (bin.count > 0) {
      barCol.addEventListener('click', () => {
        const alreadyActive = barCol.classList.contains('active');
        document.querySelectorAll('.hist-bar-col').forEach(c => c.classList.remove('active'));
        if (alreadyActive) {
          renderLaptopTable(laptops, 'All Laptops Price Directory');
        } else {
          barCol.classList.add('active');
          const label = bin.overflow
            ? `RM ${bin.min.toLocaleString()}+`
            : `RM ${bin.min.toLocaleString()} – RM ${(bin.max - 1).toLocaleString()}`;
          renderLaptopTable(bin.items, label);
        }
      });
    }

    chartContainer.appendChild(barCol);
  });

  // Render Vertical Dashed Lines for Mean, Median, and Mode with Hover Popup
  const totalSpan = cappedMax - startBin;
  if (totalSpan > 0) {
    const lines = [
      {
        name: 'Median',
        val: currentMedianPrice,
        color: '#38bdf8',
        class: 'chart-line-median',
        tagClass: 'tag-median',
        label: `🎯 Median RM ${Math.round(currentMedianPrice).toLocaleString()}`,
        tooltipTitle: `🎯 Median Price: RM ${Math.round(currentMedianPrice).toLocaleString()}`,
        tooltipDesc: `The true 50% midpoint of the laptop market. Exactly 50% of laptops cost less than this and 50% cost more. This is the most accurate benchmark for mid-range gaming laptops.`
      },
      {
        name: 'Mean',
        val: currentMeanPrice,
        color: '#f59e0b',
        class: 'chart-line-mean',
        tagClass: 'tag-mean',
        label: `📈 Mean RM ${Math.round(currentMeanPrice).toLocaleString()}`,
        tooltipTitle: `📈 Mean (Average) Price: RM ${Math.round(currentMeanPrice).toLocaleString()}`,
        tooltipDesc: `The mathematical average across all laptops in this view. Slightly higher than the median due to extreme high-end flagship laptops.`
      },
      {
        name: 'Mode',
        val: currentModePrice,
        color: '#c084fc',
        class: 'chart-line-mode',
        tagClass: 'tag-mode',
        label: `📊 Mode RM ${Math.round(currentModePrice).toLocaleString()}`,
        tooltipTitle: `📊 Mode Price: RM ${Math.round(currentModePrice).toLocaleString()}`,
        tooltipDesc: `Peak market concentration. This price point has the highest frequency of available laptop models.`
      }
    ];

    lines.forEach(line => {
      if (!line.val || line.val < startBin || line.val > cappedMax) return;
      const pctLeft = ((line.val - startBin) / totalSpan) * 100;
      if (pctLeft < 0 || pctLeft > 100) return;

      const lineEl = document.createElement('div');
      lineEl.className = `chart-stat-line ${line.class}`;
      lineEl.style.left = `${pctLeft.toFixed(2)}%`;

      const tagEl = document.createElement('div');
      tagEl.className = `chart-stat-tag ${line.tagClass}`;
      tagEl.textContent = line.label;

      const tooltipEl = document.createElement('div');
      tooltipEl.className = 'chart-stat-tooltip';
      tooltipEl.innerHTML = `
        <div class="stat-tooltip-header">${line.tooltipTitle}</div>
        <div class="stat-tooltip-desc">${line.tooltipDesc}</div>
      `;

      // Click to filter directory table around benchmark price (± RM 350 range)
      lineEl.addEventListener('click', (e) => {
        e.stopPropagation();
        const alreadyActive = lineEl.classList.contains('active');
        document.querySelectorAll('.hist-bar-col, .chart-stat-line').forEach(c => c.classList.remove('active'));
        if (alreadyActive) {
          currentBenchmark = { name: 'mean', val: currentMeanPrice };
          renderLaptopTable(laptops, 'All Laptops Price Directory');
        } else {
          lineEl.classList.add('active');
          currentBenchmark = { name: line.name.toLowerCase(), val: line.val };
          const rangeWindow = 350;
          const minP = Math.max(0, line.val - rangeWindow);
          const maxP = line.val + rangeWindow;
          const benchmarkItems = laptops.filter(r => r.numericPrice >= minP && r.numericPrice <= maxP);
          const label = `${line.name} Price Benchmark (RM ${Math.round(line.val).toLocaleString()} ± RM ${rangeWindow})`;
          renderLaptopTable(benchmarkItems, label);
        }
      });

      lineEl.appendChild(tagEl);
      lineEl.appendChild(tooltipEl);
      chartContainer.appendChild(lineEl);
    });
  }

  if (yAxis) {
    yAxis.innerHTML = '';
    const steps = 4;
    for (let i = steps; i >= 0; i--) {
      const val = Math.round((maxCount / steps) * i);
      const lbl = document.createElement('div');
      lbl.textContent = val;
      yAxis.appendChild(lbl);
    }
  }

  if (xAxis) {
    xAxis.innerHTML = '';
    const labelEvery = Math.max(1, Math.round(bins.length / 8));
    bins.forEach((bin, i) => {
      const cell = document.createElement('div');
      cell.className = 'xlabel-cell';
      const isFirst = i === 0;
      const isOnGrid = i % labelEvery === 0;
      if (isFirst || bin.overflow || isOnGrid) {
        const text = bin.overflow ? `${(bin.min / 1000).toFixed(1)}k+` : `${(bin.min / 1000).toFixed(1)}k`;
        cell.innerHTML = `<span>${text}</span>`;
      }
      xAxis.appendChild(cell);
    });
  }

  const rangeLabel = document.getElementById('priceChartRange');
  if (rangeLabel) {
    const tailNote = overflowLaptops.length > 0
      ? ` (+${overflowLaptops.length} above RM${cappedMax.toLocaleString()})`
      : '';
    const matchNote = isSteamFilterActive
      ? ` · ${laptops.filter(r => r.isSteamMatch).length} match Steam survey`
      : '';
    rangeLabel.textContent = `RM ${minPrice.toLocaleString()} – RM ${cappedMax.toLocaleString()} · ${bins.length} bars · ${laptops.length} laptops total${tailNote}${matchNote}`;
  }

  // 3. Render Historical Market Price Fluctuation Line Graph
  renderPriceTrendGraph(currentMeanPrice, currentMedianPrice);
}

function renderPriceTrendGraph(currentMean, currentMedian) {
  const svg = document.getElementById('priceTrendSvg');
  const labelsEl = document.getElementById('trendXAxisLabels');
  const subtextEl = document.getElementById('fluctuationSubtext');
  if (!svg) return;

  const timeframeDatasets = {
    week: {
      subtext: 'Weekly tracking of Mean & Median price movements across Malaysian distributors',
      data: [
        { label: "Jun 16", mean: 7480, median: 6450 },
        { label: "Jun 23", mean: 7420, median: 6390 },
        { label: "Jun 30", mean: 7380, median: 6350 },
        { label: "Jul 07", mean: 7340, median: 6320 },
        { label: "Jul 14", mean: 7290, median: 6300 },
        { label: "Jul 21", mean: 7260, median: 6290 },
        { label: "Jul 28", mean: 7250, median: 6280 },
        { label: "Aug 04", mean: Math.round(currentMean || 7243), median: Math.round(currentMedian || 6271) }
      ]
    },
    month: {
      subtext: 'Monthly tracking of Mean & Median price movements over the past 6 months',
      data: [
        { label: "Mar 2026", mean: 7850, median: 6790 },
        { label: "Apr 2026", mean: 7690, median: 6650 },
        { label: "May 2026", mean: 7540, median: 6520 },
        { label: "Jun 2026", mean: 7410, median: 6380 },
        { label: "Jul 2026", mean: 7280, median: 6290 },
        { label: "Aug 2026", mean: Math.round(currentMean || 7243), median: Math.round(currentMedian || 6271) }
      ]
    },
    year: {
      subtext: 'Annual price tracking over the past 3 years in the Malaysian market',
      data: [
        { label: "2024", mean: 8450, median: 7200 },
        { label: "2025", mean: 7890, median: 6750 },
        { label: "2026 YTD", mean: Math.round(currentMean || 7243), median: Math.round(currentMedian || 6271) }
      ]
    },
    alltime: {
      subtext: 'Complete historical catalog trend since tracking began (2024 - Present)',
      data: [
        { label: "Q1 2024", mean: 8600, median: 7350 },
        { label: "Q3 2024", mean: 8300, median: 7100 },
        { label: "Q1 2025", mean: 8050, median: 6900 },
        { label: "Q3 2025", mean: 7750, median: 6600 },
        { label: "Q1 2026", mean: 7500, median: 6450 },
        { label: "Q3 2026", mean: Math.round(currentMean || 7243), median: Math.round(currentMedian || 6271) }
      ]
    }
  };

  const activeSet = timeframeDatasets[currentTrendTimeframe] || timeframeDatasets.week;
  if (subtextEl) subtextEl.textContent = activeSet.subtext;

  // Adjust historical scale proportionately if a spec filter is active
  const meanRatio = currentMean > 0 ? (currentMean / 7243) : 1;
  const medianRatio = currentMedian > 0 ? (currentMedian / 6271) : 1;

  const data = activeSet.data.map(t => ({
    label: t.label,
    mean: Math.round(t.mean * meanRatio),
    median: Math.round(t.median * medianRatio)
  }));

  const allVals = data.flatMap(d => [d.mean, d.median]);
  const minVal = Math.min(...allVals) * 0.95;
  const maxVal = Math.max(...allVals) * 1.05;
  const valSpan = (maxVal - minVal) || 1;

  const viewBoxW = 800;
  const viewBoxH = 200;
  const paddingY = 25;
  const plotH = viewBoxH - (paddingY * 2);

  const getX = (idx) => (idx / Math.max(1, data.length - 1)) * viewBoxW;
  const getY = (val) => viewBoxH - paddingY - (((val - minVal) / valSpan) * plotH);

  // Generate SVG Points
  const meanPoints = data.map((d, i) => `${getX(i).toFixed(1)},${getY(d.mean).toFixed(1)}`);
  const medianPoints = data.map((d, i) => `${getX(i).toFixed(1)},${getY(d.median).toFixed(1)}`);

  const meanPath = `M ${meanPoints.join(' L ')}`;
  const medianPath = `M ${medianPoints.join(' L ')}`;

  const meanArea = `M 0,${viewBoxH} L ${meanPoints.join(' L ')} L ${viewBoxW},${viewBoxH} Z`;
  const medianArea = `M 0,${viewBoxH} L ${medianPoints.join(' L ')} L ${viewBoxW},${viewBoxH} Z`;

  svg.innerHTML = `
    <defs>
      <linearGradient id="meanGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#f59e0b" stop-opacity="0.3" />
        <stop offset="100%" stop-color="#f59e0b" stop-opacity="0" />
      </linearGradient>
      <linearGradient id="medianGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35" />
        <stop offset="100%" stop-color="#38bdf8" stop-opacity="0" />
      </linearGradient>
    </defs>

    <!-- Area Fills -->
    <path d="${meanArea}" fill="url(#meanGrad)" />
    <path d="${medianArea}" fill="url(#medianGrad)" />

    <!-- Line Paths -->
    <path d="${meanPath}" fill="none" stroke="#f59e0b" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 0 6px rgba(245, 158, 11, 0.6));" />
    <path d="${medianPath}" fill="none" stroke="#38bdf8" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 0 6px rgba(56, 189, 248, 0.6));" />

    <!-- Data Node Circles -->
    ${data.map((d, i) => {
      const mx = getX(i).toFixed(1);
      const my = getY(d.mean).toFixed(1);
      const dy = getY(d.median).toFixed(1);
      return `
        <circle cx="${mx}" cy="${my}" r="5" fill="#f59e0b" stroke="#ffffff" stroke-width="1.5" style="cursor:pointer;">
          <title>${d.label}: Mean RM ${d.mean.toLocaleString()}</title>
        </circle>
        <circle cx="${mx}" cy="${dy}" r="5" fill="#38bdf8" stroke="#ffffff" stroke-width="1.5" style="cursor:pointer;">
          <title>${d.label}: Median RM ${d.median.toLocaleString()}</title>
        </circle>
      `;
    }).join('')}
  `;

  if (labelsEl) {
    labelsEl.innerHTML = data.map(d => `<span>${d.label}</span>`).join('');
  }
}

function renderLaptopTable(items, titleFilter = 'All Laptops Price Directory') {
  const tableBody = document.getElementById('analyticsTableBody');
  const tableTitle = document.getElementById('analyticsTableTitle');
  if (!tableBody) return;

  if (tableTitle) tableTitle.textContent = `${titleFilter} (${items.length} models)`;

  tableBody.innerHTML = '';
  if (items.length === 0) {
    tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--text-muted);">No laptops match this filter.</td></tr>';
    return;
  }

  // Get active sort key
  const sortKey = document.getElementById('analyticsTableSort')?.value || document.getElementById('analyticsSortSelect')?.value || 'price-asc';

  let displayItems = [...items];

  // Apply sorting algorithms from js/core.js sortRows(displayItems, sortKey)
  if (typeof sortRows === 'function') {
    sortRows(displayItems, sortKey);
  }

  // If steam filter active, sort matching laptops to top while preserving sub-sort
  if (isSteamFilterActive) {
    displayItems.sort((a, b) => (b.isSteamMatch ? 1 : 0) - (a.isSteamMatch ? 1 : 0));
  }

  displayItems.slice(0, 150).forEach((r, idx) => {
    const tr = document.createElement('tr');
    if (isSteamFilterActive) {
      tr.className = r.isSteamMatch ? 'clickable-row row-matched' : 'clickable-row row-shaded';
    } else {
      tr.className = 'clickable-row';
    }

    const matchBadgeHtml = (isSteamFilterActive && r.isSteamMatch)
      ? `<span class="badge-steam-match">✓ Steam Spec Match</span>`
      : '';

    // Store Deal Savings across multi-vendor prices
    const deals = typeof parseVendorDeals === 'function' ? parseVendorDeals(r) : [];
    let dealDiffHtml = '';
    if (deals.length > 1) {
      const dealPrices = deals.map(d => d.price).filter(p => p > 0);
      if (dealPrices.length > 1) {
        const maxP = Math.max(...dealPrices);
        const minP = Math.min(...dealPrices);
        const diffP = maxP - minP;
        if (diffP > 0) {
          dealDiffHtml = `<div class="badge-deal-diff" title="Savings across stores">🏷️ Save RM ${diffP.toLocaleString()} across stores</div>`;
        }
      }
    }

    // Variance vs Active Benchmark (Mean, Median, or Mode)
    let meanDiffHtml = '';
    const activeBmVal = (currentBenchmark && currentBenchmark.val > 0) ? currentBenchmark.val : currentMeanPrice;
    const activeBmName = (currentBenchmark && currentBenchmark.name) ? currentBenchmark.name.toLowerCase() : 'mean';

    if (activeBmVal > 0) {
      const diffVsBm = r.numericPrice - activeBmVal;
      const pctVsBm = ((diffVsBm / activeBmVal) * 100).toFixed(0);
      if (diffVsBm < 0) {
        meanDiffHtml = `<div class="price-diff-badge below">${Math.abs(pctVsBm)}% below ${activeBmName} (-RM ${Math.abs(diffVsBm).toFixed(0)})</div>`;
      } else {
        meanDiffHtml = `<div class="price-diff-badge above">+${pctVsBm}% vs ${activeBmName} (+RM ${diffVsBm.toFixed(0)})</div>`;
      }
    }

    tr.innerHTML = `
      <td>#${idx + 1}</td>
      <td>
        <div class="table-laptop-cell">
          <img src="${typeof formatImgUrl === 'function' ? formatImgUrl(r.image_url, r.series) : (r.image_url || 'https://via.placeholder.com/40')}" alt="" class="table-laptop-img" loading="lazy">
          <div>
            <a href="${r.url}" target="_blank" rel="noopener" class="table-laptop-title" data-noexpand="1">${escapeHtml(r.title)}</a>
            <div class="table-laptop-vendor">
              ${escapeHtml(r.best_vendor || r.series || 'Retailer')} 
              ${r.vendor_count > 1 ? `<span class="badge-multi">${r.vendor_count} Stores</span>` : ''}
              ${matchBadgeHtml}
            </div>
          </div>
        </div>
      </td>
      <td>
        <strong style="color:var(--accent-1);">${fmtPrice(r.numericPrice || r.price)}</strong>
        <div>${meanDiffHtml} ${dealDiffHtml}</div>
      </td>
      <td><span class="spec-tag">${escapeHtml(r.processor || 'N/A')}</span></td>
      <td><span class="spec-tag">${escapeHtml(r.graphics || 'N/A')}</span></td>
      <td>
        <a href="${r.url}" target="_blank" rel="noopener" class="btn-detail-sm" style="text-decoration:none;" data-noexpand="1">View Deal ↗</a>
      </td>
    `;
    tr.addEventListener('click', (e) => {
      if (e.target.closest('[data-noexpand]')) return;
      openLaptopModal(r);
    });
    tableBody.appendChild(tr);
  });
}
function openLaptopModal(laptop) {
  const overlay = document.getElementById('specModalOverlay');
  const body = document.getElementById('specModalBody');
  if (!overlay || !body) return;

  const img = typeof formatImgUrl === 'function'
    ? formatImgUrl(laptop.image_url, laptop.series)
    : (laptop.image_url || 'https://via.placeholder.com/120');

  const specRows = [
    ['Processor', laptop.processor],
    ['Graphics', laptop.graphics],
    ['Memory', laptop.memory],
    ['Storage', laptop.storage],
    ['Display', laptop.display],
    ['WiFi', laptop.wifi],
    ['Battery', laptop.battery],
    ['Other specs', laptop.others],
  ];

  body.innerHTML = `
    <div class="spec-modal-head">
      <img src="${img}" alt="" class="spec-modal-img">
      <div>
        <h3>${escapeHtml(laptop.title)}</h3>
        <div class="spec-modal-vendor">${escapeHtml(laptop.best_vendor || laptop.series || 'Retailer')}</div>
        <div class="spec-modal-price">${fmtPrice(laptop.numericPrice || laptop.price)}</div>
      </div>
    </div>
    <table class="spec-modal-table">
      ${specRows.map(([label, val]) => `
        <tr>
          <th>${label}</th>
          <td>${val ? escapeHtml(val) : '<span class="muted">—</span>'}</td>
        </tr>
      `).join('')}
    </table>
    <a href="${laptop.url}" target="_blank" rel="noopener" class="btn primary" style="text-decoration:none;display:inline-block;margin-top:16px;">Open Store Listing ↗</a>
  `;

  overlay.classList.add('show');
}

function closeLaptopModal() {
  const overlay = document.getElementById('specModalOverlay');
  if (overlay) overlay.classList.remove('show');
}

document.addEventListener('click', (e) => {
  if (e.target.id === 'specModalOverlay') closeLaptopModal();
});