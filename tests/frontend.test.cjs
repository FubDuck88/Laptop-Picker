const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const root = path.join(__dirname, '..');
const cases = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures/regressions.json'), 'utf8'));

function loadFrontend() {
  const elements = new Map();
  const document = {
    readyState: 'loading',
    addEventListener() {},
    getElementById(id) { return elements.get(id) || null; },
    querySelectorAll() { return []; },
  };
  const context = vm.createContext({ document, console });
  for (const file of ['core.js', 'analytics.js']) {
    vm.runInContext(fs.readFileSync(path.join(root, 'js', file), 'utf8'), context, { filename: file });
  }
  return { context, elements };
}

test('price history is unavailable in initial HTML, including before data loads', () => {
  const html = fs.readFileSync(path.join(root, 'analytics.html'), 'utf8');
  assert.match(html, /Load a verified catalog to see recorded observations\./);
  assert.doesNotMatch(html, /priceTrendSvg|trendXAxisLabels|trend-time-btn|vs last week|Aug 04 \(Today\)/);
  assert.equal(fs.existsSync(path.join(root, 'data', 'price_history.json')), false);
});

test('current catalog statistics stay correct when data changes or filters return no results', () => {
  const { context, elements } = loadFrontend();
  for (const id of ['statMeanPrice', 'statMedianPrice', 'statModePrice', 'statLowestPrice', 'statHighestPrice', 'statTotalCount']) {
    elements.set(id, { textContent: '' });
  }
  // Isolate summary behavior from unrelated table/chart DOM layout.
  vm.runInContext('renderPriceHistogram = () => {}; renderLaptopTable = () => {};', context);
  const rows = [
    { id: 'one', title: 'Laptop One', price: 3000, processor: 'Intel Core i7', memory: '16GB', vendor_count: 1 },
    { id: 'two', title: 'Laptop Two', price: 5000, processor: 'Intel Core i7', memory: '32GB', vendor_count: 2 },
  ];
  context.inputRows = rows;
  vm.runInContext('globalRawRows = inputRows; renderAnalyticsView();', context);
  assert.equal(elements.get('statMeanPrice').textContent, context.fmtPrice(4000));
  assert.equal(elements.get('statMedianPrice').textContent, context.fmtPrice(4000));
  assert.equal(elements.get('statLowestPrice').textContent, context.fmtPrice(3000));
  assert.equal(elements.get('statHighestPrice').textContent, context.fmtPrice(5000));
  assert.equal(elements.get('statTotalCount').textContent, '2 Models');

  rows[1].price = 7000;
  vm.runInContext('renderAnalyticsView();', context);
  assert.equal(elements.get('statMeanPrice').textContent, context.fmtPrice(5000));
  elements.set('analyticsBrandFilter', { value: 'no such brand' });
  vm.runInContext('renderAnalyticsView();', context);
  assert.equal(elements.get('statMeanPrice').textContent, 'RM -');
  assert.equal(elements.get('statTotalCount').textContent, '0 Models');
});

test('analytics never calculates weekly changes without recorded history', () => {
  const { context, elements } = loadFrontend();
  const ids = ['meanPriceTrend', 'medianPriceTrend', 'modePriceTrend', 'lowestPriceTrend', 'highestPriceTrend', 'statTrend'];
  for (const id of ids) elements.set(id, { textContent: '', className: '' });
  vm.runInContext('renderPriceHistogram = () => {}; renderLaptopTable = () => {};', context);
  context.inputRows = [cases.gaming_laptop];
  vm.runInContext('globalRawRows = inputRows; renderAnalyticsView();', context);
  for (const id of ids) assert.equal(elements.get(id).textContent, '', id);
});

test('Steam preset accepts an explicit 16GB gaming configuration without VRAM text', () => {
  const { context } = loadFrontend();
  assert.equal(context.matchesSteamSpecs({ ...cases.gaming_laptop, graphics: 'RTX 4060' }), true);
});

test('BUG-07: Steam preset must use system RAM instead of GPU VRAM', () => {
  const { context } = loadFrontend();
  assert.equal(context.matchesSteamSpecs(cases.gaming_laptop), true);
});

test('BUG-08: unknown RAM must not qualify for a RAM-specific preset', () => {
  const { context } = loadFrontend();
  assert.equal(context.matchesSteamSpecs({ ...cases.gaming_laptop, graphics: 'RTX 4060', memory: '' }), false);
});

test('BUG-09: the Integrated filter must include Intel Arc integrated graphics', () => {
  const { context } = loadFrontend();
  context.integratedRow = { ...cases.gaming_laptop, graphics: 'Intel Arc Graphics' };
  // Construct Sets inside the browser realm, using the existing UI filter value.
  const result = vm.runInContext(`matchesFilters(integratedRow, {
    store: new Set(), cpu: new Set(), gpu: new Set(['Iris']),
    mem: new Set(), sto: new Set(), disp: new Set()
  }, false, '', NaN, NaN)`, context);
  assert.equal(result, true);
});

test('analytics filters use recorded VRAM and system RAM independently', () => {
  const {context,elements} = loadFrontend();
  elements.set('statTotalCount',{textContent:''});
  elements.set('analyticsVramFilter',{value:'8gb'});
  context.inputRows = [{id:'test',title:'Laptop',price:4000,processor:'Intel Core i7',graphics:'RTX 4060',
    memory:'16GB',memory_gb:16,vram_gb:null,verified:true}];
  vm.runInContext('renderPriceHistogram=()=>{}; renderLaptopTable=()=>{}; globalRawRows=inputRows; renderAnalyticsView();',context);
  assert.equal(elements.get('statTotalCount').textContent,'0 Models');
  elements.get('analyticsVramFilter').value='';
  elements.set('analyticsRamFilter',{value:'8gb'});
  vm.runInContext('globalRawRows[0].graphics="RTX 4060 8GB GDDR6"; renderAnalyticsView();',context);
  assert.equal(elements.get('statTotalCount').textContent,'0 Models');
});

test('installed RAM excludes upgrade maxima and verified unknowns never fall back to titles', () => {
  const {context} = loadFrontend();
  assert.equal(context.systemRamGb({memory:'8GB*2 DDR4, Max 64GB'}),16);
  assert.equal(context.systemRamGb({memory:'Up to 64GB'}),null);
  assert.equal(context.systemRamGb({verified:true,memory_gb:null,title:'16GB RAM',memory:''}),null);
  assert.equal(context.normalizeRow({id:'x',title:'RTX 4090 32GB RAM 1TB SSD'},0).memory,'');
});

test('every catalog entry point loads verified releases without legacy fallback', () => {
  for (const name of ['index.html','mobile.html','analytics.html']) {
    const html=fs.readFileSync(path.join(root,name),'utf8');
    assert.match(html,/js\/release\.js/);
    assert.match(html,/js\/catalog\.js/);
    assert.doesNotMatch(html,/data\/data\.js|papaparse|user-scalable=no/);
  }
  const core=fs.readFileSync(path.join(root,'js/core.js'),'utf8');
  assert.doesNotMatch(core,/preloadedRows|Papa\.parse|fetch\('data\/laptops/);
});
