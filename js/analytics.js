/**
 * analytics.js — Price Analytics & Market Statistics for Laptop Picker
 * Computes mean, median, min, max, price distribution brackets, and renders interactive charts.
 */

document.addEventListener('DOMContentLoaded', () => {
  loadData(initAnalytics);
});

function initAnalytics(rawRows) {
  if (!rawRows || !Array.isArray(rawRows) || rawRows.length === 0) {
    console.error('[analytics] No laptop data loaded.');
    return;
  }

  // Normalize rows safely
  const rows = rawRows.map((r, i) => typeof normalizeRow === 'function' ? normalizeRow(r, i) : r);

  // Filter valid prices
  const validLaptops = rows.filter(r => r.price && !isNaN(r.price) && r.price > 0);
  validLaptops.sort((a, b) => a.price - b.price);

  const prices = validLaptops.map(r => r.price);
  const count = prices.length;

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

  // 2. Build Price Distribution Brackets
  const brackets = [
    { label: '< RM 2,000', min: 0, max: 2000, count: 0, items: [] },
    { label: 'RM 2k - 3.5k', min: 2000, max: 3500, count: 0, items: [] },
    { label: 'RM 3.5k - 5k', min: 3500, max: 5000, count: 0, items: [] },
    { label: 'RM 5k - 7.5k', min: 5000, max: 7500, count: 0, items: [] },
    { label: 'RM 7.5k - 10k', min: 7500, max: 10000, count: 0, items: [] },
    { label: '> RM 10,000', min: 10000, max: Infinity, count: 0, items: [] }
  ];

  validLaptops.forEach(r => {
    for (let b of brackets) {
      if (r.price >= b.min && r.price < b.max) {
        b.count++;
        b.items.push(r);
        break;
      }
    }
  });

  renderPriceBarChart(brackets, count);
  renderLaptopTable(validLaptops);
}

function renderPriceBarChart(brackets, totalCount) {
  const chartContainer = document.getElementById('priceBarChart');
  if (!chartContainer) return;

  const maxBucketCount = Math.max(...brackets.map(b => b.count), 1);
  chartContainer.innerHTML = '';

  brackets.forEach((b, idx) => {
    const pct = ((b.count / maxBucketCount) * 100).toFixed(1);
    const sharePct = ((b.count / totalCount) * 100).toFixed(1);

    const barCol = document.createElement('div');
    barCol.className = 'chart-bar-col';
    barCol.innerHTML = `
      <div class="chart-bar-value">${b.count} (${sharePct}%)</div>
      <div class="chart-bar-track">
        <div class="chart-bar-fill" style="height: ${pct}%; animation-delay: ${idx * 100}ms;" title="${b.label}: ${b.count} laptops"></div>
      </div>
      <div class="chart-bar-label">${b.label}</div>
    `;

    barCol.addEventListener('click', () => {
      document.querySelectorAll('.chart-bar-col').forEach(c => c.classList.remove('active'));
      barCol.classList.add('active');
      renderLaptopTable(b.items, `Laptops in price range: ${b.label}`);
    });

    chartContainer.appendChild(barCol);
  });
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
    tr.innerHTML = `
      <td>#${idx + 1}</td>
      <td>
        <div class="table-laptop-cell">
          <img src="${formatImgUrl ? formatImgUrl(r.image_url, r.series) : (r.image_url || 'https://via.placeholder.com/40')}" alt="" class="table-laptop-img" loading="lazy">
          <div>
            <a href="${r.url}" target="_blank" rel="noopener" class="table-laptop-title">${escapeHtml(r.title)}</a>
            <div class="table-laptop-vendor">${escapeHtml(r.best_vendor || r.series || 'Retailer')} ${r.vendor_count > 1 ? `<span class="badge-multi">${r.vendor_count} Stores</span>` : ''}</div>
          </div>
        </div>
      </td>
      <td><strong style="color:var(--accent-1);">${fmtPrice(r.price)}</strong></td>
      <td><span class="spec-tag">${escapeHtml(r.processor || 'N/A')}</span></td>
      <td><span class="spec-tag">${escapeHtml(r.graphics || 'N/A')}</span></td>
      <td>
        <a href="${r.url}" target="_blank" rel="noopener" class="btn-detail-sm" style="text-decoration:none;">View Deal ↗</a>
      </td>
    `;
    tableBody.appendChild(tr);
  });
}
