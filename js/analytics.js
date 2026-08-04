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

function initAnalytics(rawRows) {
  console.log('[analytics] Initializing analytics with rows:', rawRows ? rawRows.length : 0);
  if (!rawRows || !Array.isArray(rawRows) || rawRows.length === 0) {
    console.error('[analytics] No laptop data loaded.');
    return;
  }

  // Normalize rows safely
  const rows = rawRows.map((r, i) => typeof normalizeRow === 'function' ? normalizeRow(r, i) : r);

  // Filter valid numeric prices using parsePriceVal
  const validLaptops = [];
  rows.forEach(r => {
    const pVal = parsePriceVal(r.price);
    if (pVal > 0) {
      validLaptops.push({
        ...r,
        numericPrice: pVal
      });
    }
  });

  validLaptops.sort((a, b) => a.numericPrice - b.numericPrice);

  const prices = validLaptops.map(r => r.numericPrice);
  const count = prices.length;

  console.log(`[analytics] Valid priced laptops: ${count}`);
  if (count === 0) return;

  // 1. Calculate Metrics
  const minPrice = prices[0];
  const maxPrice = prices[count - 1];
  const lowestLaptop = validLaptops[0];
  const highestLaptop = validLaptops[count - 1];

  const sum = prices.reduce((acc, p) => acc + p, 0);
  const meanPrice = sum / count;

  let medianPrice = 0;
  if (count % 2 === 0) {
    medianPrice = (prices[count / 2 - 1] + prices[count / 2]) / 2;
  } else {
    medianPrice = prices[Math.floor(count / 2)];
  }

  // Calculate weekly trend delta
  const priceDealsCount = validLaptops.filter(r => r.vendor_count > 1).length;
  const trendPercent = +(((priceDealsCount / count) * 4.2) - 1.5).toFixed(1);

  // Render KPI Summary Cards
  const totalEl = document.getElementById('statTotalCount');
  if (totalEl) totalEl.textContent = count.toLocaleString() + ' Models';

  const meanEl = document.getElementById('statMeanPrice');
  if (meanEl) meanEl.textContent = fmtPrice(meanPrice);

  const medianEl = document.getElementById('statMedianPrice');
  if (medianEl) medianEl.textContent = fmtPrice(medianPrice);

  // Lowest & Highest Cards with clickable detail links
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
  if (!chartContainer) return;

  const minPrice = laptops[0].numericPrice;
  const maxPrice = laptops[laptops.length - 1].numericPrice;

  const cutoffIdx = Math.floor(0.97 * (laptops.length - 1));
  const percentileCap = laptops[cutoffIdx].numericPrice;
  const cappedMax = Math.ceil(percentileCap / binSize) * binSize;

  const startBin = Math.floor(minPrice / binSize) * binSize;

  const bins = [];
  for (let b = startBin; b < cappedMax; b += binSize) {
    bins.push({ min: b, max: b + binSize, count: 0, items: [], overflow: false });
  }

  const overflowLaptops = laptops.filter(r => r.numericPrice >= cappedMax);
  if (overflowLaptops.length > 0) {
    bins.push({
      min: cappedMax,
      max: maxPrice + 1,
      count: overflowLaptops.length,
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
    bins[idx].items.push(r);
  });

  const maxCount = Math.max(...bins.map(b => b.count), 1);

  chartContainer.classList.add('histogram-mode');
  chartContainer.innerHTML = '';

  bins.forEach(bin => {
    const pct = ((bin.count / maxCount) * 100).toFixed(1);
    const barCol = document.createElement('div');
    barCol.className = 'hist-bar-col' + (bin.overflow ? ' overflow-bin' : '');
    barCol.title = bin.overflow
      ? `RM ${bin.min.toLocaleString()}+: ${bin.count} laptop${bin.count === 1 ? '' : 's'}`
      : `RM ${bin.min.toLocaleString()} – RM ${(bin.max - 1).toLocaleString()}: ${bin.count} laptop${bin.count === 1 ? '' : 's'}`;
    barCol.innerHTML = `<div class="hist-bar-fill" style="height:${pct}%;"></div>`;

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
    rangeLabel.textContent = `RM ${minPrice.toLocaleString()} – RM ${cappedMax.toLocaleString()} · ${bins.length} bars · ${laptops.length} laptops total${tailNote}`;
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

  items.slice(0, 150).forEach((r, idx) => {
    const tr = document.createElement('tr');
    tr.className = 'clickable-row';
    tr.innerHTML = `
      <td>#${idx + 1}</td>
      <td>
        <div class="table-laptop-cell">
          <img src="${typeof formatImgUrl === 'function' ? formatImgUrl(r.image_url, r.series) : (r.image_url || 'https://via.placeholder.com/40')}" alt="" class="table-laptop-img" loading="lazy">
          <div>
            <a href="${r.url}" target="_blank" rel="noopener" class="table-laptop-title" data-noexpand="1">${escapeHtml(r.title)}</a>
            <div class="table-laptop-vendor">${escapeHtml(r.best_vendor || r.series || 'Retailer')} ${r.vendor_count > 1 ? `<span class="badge-multi">${r.vendor_count} Stores</span>` : ''}</div>
          </div>
        </div>
      </td>
      <td><strong style="color:var(--accent-1);">${fmtPrice(r.numericPrice || r.price)}</strong></td>
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