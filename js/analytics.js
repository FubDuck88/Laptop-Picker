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

function initAnalytics(rawRows) {
  console.log('[analytics] Initializing analytics with rows:', rawRows ? rawRows.length : 0);
  globalRawRows = rawRows || [];
  renderRecordedHistory();

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
        if (btnText) btnText.textContent = 'Gaming preset Filter ON ✓';
      } else {
        steamBtn.style.background = 'transparent';
        steamBtn.style.color = 'var(--accent-2)';
        if (btnText) btnText.textContent = 'Filter Gaming preset';
      }
      renderAnalyticsView();
    });
  }

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
        if (btnText) btnText.textContent = 'Filter Gaming preset';
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
    if (r.graphics) gpuSet.add(JSON.stringify({val: r.graphics.toLowerCase(), label: r.graphics}));
    if (r.processor) cpuSet.add(JSON.stringify({val: r.processor.toLowerCase(), label: r.processor}));
    const gb = systemRamGb(r);
    if (gb != null) ramSet.add(gb);
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
    const cpu = (r.processor || '').toLowerCase();
    const gpu = (r.graphics || '').toLowerCase();
    if (brandVal && (r.brand ? r.brand.toLowerCase() !== brandVal : !r.title.toLowerCase().includes(brandVal))) return;
    if (cpuBrandVal === 'intel' && !/intel|core|i[3579]|ultra/.test(cpu)) return;
    if (cpuBrandVal === 'amd' && !/amd|ryzen/.test(cpu)) return;
    if (gpuBrandVal === 'nvidia' && !/geforce|rtx|gtx|nvidia/.test(gpu)) return;
    if (gpuBrandVal === 'amd' && !/radeon|\brx\s*\d/.test(gpu)) return;
    if (gpuBrandVal === 'intel' && !/intel|arc|iris|uhd/.test(gpu)) return;
    if (vramVal) {
      const gb = r.vram_gb;
      if (vramVal === 'shared' ? !isIntegratedGpu(r)
        : gb == null || (vramVal.endsWith('+') ? gb < parseInt(vramVal) : gb !== parseInt(vramVal))) return;
    }
    if (storageVal) {
      const gb = r.storage_gb;
      const target = storageVal.includes('tb') ? parseInt(storageVal) * 1000 : parseInt(storageVal);
      if (gb == null || (storageVal.endsWith('+') ? gb < target : gb !== target)) return;
    }
    if (gpuVal && !gpu.includes(gpuVal)) return;
    if (ramVal && systemRamGb(r) !== parseInt(ramVal)) return;
    if (cpuVal && !cpu.includes(cpuVal)) return;
    if (isSteamFilterActive && !isSteamMatch) return;

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
    for (const id of ['lowestLaptopName','highestLaptopName','modeSubtext','statTotalSubtext','chartYAxis','chartXAxis','priceChartRange']) { const el = document.getElementById(id); if (el) el.textContent = ''; }
    for (const id of ['statLowestPrice','statHighestPrice']) { const el = document.getElementById(id); if (el) { el.href = '#'; el.title = ''; } }
    currentMeanPrice = currentMedianPrice = currentModePrice = 0;
    currentBenchmark = {name:'mean', val:0};
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

  const totalEl = document.getElementById('statTotalCount');
  if (totalEl) {
    totalEl.textContent = isSteamFilterActive
      ? `${activeSubset.length} / ${count} Gaming preset models`
      : count.toLocaleString() + ' Models';
  }
  const totalSubEl = document.getElementById('statTotalSubtext');
  if (totalSubEl) {
    const unpricedCount = rows.length - count;
    totalSubEl.textContent = `${count} Priced Models (${unpricedCount} Unpriced Excluded)`;
  }

  const meanEl = document.getElementById('statMeanPrice');
  if (meanEl) meanEl.textContent = fmtPrice(meanPrice);
  const medianEl = document.getElementById('statMedianPrice');
  if (medianEl) medianEl.textContent = fmtPrice(medianPrice);
  const modeEl = document.getElementById('statModePrice');
  if (modeEl) modeEl.textContent = fmtPrice(modePrice);
  const modeSub = document.getElementById('modeSubtext');
  if (modeSub) modeSub.textContent = `Peak Frequency (${maxFreq} models at RM ${modePrice.toLocaleString()})`;
  // Lowest and highest currently listed prices with store links
  const minLink = document.getElementById('statLowestPrice');
  if (minLink) {
    minLink.textContent = fmtPrice(minPrice);
    minLink.href = lowestLaptop.url || '#';
    minLink.title = lowestLaptop.title;
  }
  const maxLink = document.getElementById('statHighestPrice');
  if (maxLink) {
    maxLink.textContent = fmtPrice(maxPrice);
    maxLink.href = highestLaptop.url || '#';
    maxLink.title = highestLaptop.title;
  }
  const lowNameEl = document.getElementById('lowestLaptopName');
  if (lowNameEl) lowNameEl.textContent = lowestLaptop.title.slice(0, 45) + '...';

  const highNameEl = document.getElementById('highestLaptopName');
  if (highNameEl) highNameEl.textContent = highestLaptop.title.slice(0, 45) + '...';

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
          ? `RM ${bin.min.toLocaleString()}+: ${bin.matchingCount} gaming preset matches (${bin.count} total)`
          : `RM ${bin.min.toLocaleString()} – RM ${(bin.max - 1).toLocaleString()}: ${bin.matchingCount} gaming preset matches (${bin.count} total)`;
      } else {
        barCol.className = 'hist-bar-col shaded-bin' + (bin.overflow ? ' overflow-bin' : '');
        barCol.innerHTML = `<div class="hist-bar-fill" style="height:${pct}%;"></div>`;
        barCol.title = bin.overflow
          ? `RM ${bin.min.toLocaleString()}+: 0 gaming preset matches (${bin.count} total)`
          : `RM ${bin.min.toLocaleString()} – RM ${(bin.max - 1).toLocaleString()}: 0 gaming preset matches (${bin.count} total)`;
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
      ? ` · ${laptops.filter(r => r.isSteamMatch).length} match gaming preset`
      : '';
    rangeLabel.textContent = `RM ${minPrice.toLocaleString()} – RM ${cappedMax.toLocaleString()} · ${bins.length} bars · ${laptops.length} laptops total${tailNote}${matchNote}`;
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
      ? `<span class="badge-steam-match">✓ Gaming preset match</span>`
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
          ${renderProductImage(r, false, 40)}
          <div>
            <a href="${r.url}" target="_blank" rel="noopener" class="table-laptop-title" data-noexpand="1">${escapeHtml(r.title)}</a>
            <div class="table-laptop-vendor">
              ${escapeHtml(r.best_vendor || r.series || 'Retailer')} 
              ${offerStatusHtml(r)}
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
      ${renderProductImage(laptop, false, 120)}
      ${offerStatusHtml(laptop)}
      ${offerHistoryHtml(laptop)}
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
function renderRecordedHistory() {
  const select = document.getElementById('historyOffer');
  const hint = document.getElementById('priceHistoryUnavailable');
  const body = document.getElementById('priceHistoryBody');
  if (!select || !hint || !body) return;
  const offers = new Map();
  for (const receipt of verifiedRelease?.history?.receipts || []) offers.set(receipt.offer.id, receipt.offer);
  const configs = verifiedRelease?.history?.configurations || {};
  const selected = select.value;
  select.innerHTML = [...offers.values()].map(o => '<option value="' + escapeHtml(o.id) + '">'
    + escapeHtml(`${configs[o.configuration_id]?.title || o.source_product_id} — ${o.seller} (${o.variant_id})`) + '</option>').join('');
  if (offers.has(selected)) select.value = selected;
  select.disabled = offers.size === 0;
  function show() {
    const offer = offers.get(select.value);
    if (!offer) { hint.textContent = 'No recorded price observations are available.'; body.innerHTML = ''; return; }
    const points = recordedHistory(verifiedRelease, offer.id);
    hint.textContent = points.length === 1 ? 'One observation; no price trend yet.' : `${points.length} recorded observations for this exact seller offer.`;
    body.innerHTML = offerHistoryHtml({verified:true, offer_ids:[offer.id], deals:[{id:offer.id, vendor:offer.seller}]});
  }
  select.onchange = show;
  show();
}
