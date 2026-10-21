const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname, '..');
const pointer = JSON.parse(fs.readFileSync(path.join(root, 'data/current.json')));
const actual = JSON.parse(fs.readFileSync(path.join(root, 'data', pointer.path)));
function setup() {
  const context = vm.createContext({URL, document:{addEventListener(){}}, console});
  for (const file of ['release.js','catalog.js','core.js']) vm.runInContext(fs.readFileSync(path.join(root,'js',file),'utf8'), context);
  return context;
}

test('verified rows preserve sen, variant purchase URL and stable identity without title guesses', () => {
  const c = setup();
  const release = structuredClone(actual);
  const offer = release.catalog.offers[0];
  const config = release.catalog.configurations.find(v => v.id === offer.configuration_id);
  config.title = 'Laptop RTX 5090 64GB 4TB';
  config.memory = {capacity_gb:null,label:null}; config.gpu_model = null; config.storage = {capacity_gb:null,label:null};
  const rows = c.verifiedCatalogRows(release, {asOf:release.generated_at});
  const row = rows.find(r => r.offer_ids.includes(offer.id));
  assert.equal(row.price * 100, offer.price_sen);
  assert.equal(row.url, offer.url);
  assert.equal(row.memory, ''); assert.equal(row.graphics, ''); assert.equal(row.storage, '');
  assert.equal(c.systemRamGb(row), null);
  assert.equal(c.normalizeRow(row, 99, 'x')._rid, row._rid);
});

test('expired prices are hidden unless explicitly included and unknown times stay hidden', () => {
  const c = setup();
  const release = structuredClone(actual);
  for (const o of release.catalog.offers) o.observed_at = '2026-10-01T00:00:00Z';
  assert.equal(c.verifiedCatalogRows(release, {asOf:'2026-10-08T00:00:00Z'}).length, 0);
  const old = c.verifiedCatalogRows(release, {asOf:'2026-10-08T00:00:00Z',includeExpired:true});
  assert.equal(old.length, release.catalog.offers.length);
  assert.ok(old.every(r => r.freshness === 'expired'));
  release.catalog.offers[0].observed_at = 'invalid';
  assert.equal(c.verifiedCatalogRows(release, {asOf:'2026-10-08T00:00:00Z',includeExpired:true}).length, old.length - 1);
});

test('cross-seller grouping requires identical complete hardware; unknown and different RAM stay separate', () => {
  const c = setup();
  const release = structuredClone(actual);
  const o = release.catalog.offers[0];
  const config = release.catalog.configurations.find(v => v.id === o.configuration_id);
  Object.assign(config, {gpu_kind:'integrated',gpu_model:'Intel Arc Graphics',vram_gb:null,
    display:{diagonal_inches:14,resolution_width:1920,resolution_height:1200,refresh_hz:60,label:'14 inch'}});
  const second = {...structuredClone(config),id:'second'};
  release.catalog.configurations = [config, second];
  release.catalog.offers = [o, {...o,id:'seller2',configuration_id:'second',seller:'Seller B', price_sen:o.price_sen+100}];
  let rows = c.verifiedCatalogRows(release, {asOf:release.generated_at});
  assert.equal(rows.length,1); assert.equal(rows[0].vendor_count,2); assert.equal(rows[0].deals.length,2);
  const selected = c.rowForStores(rows[0], new Set(['Seller B']));
  assert.equal(selected.url, release.catalog.offers[1].url);
  assert.equal(selected.price_sen, release.catalog.offers[1].price_sen);
  assert.equal(selected.best_vendor,'Seller B');
  assert.equal(selected.vendor_count,1);
  second.memory.capacity_gb = 32;
  assert.equal(c.verifiedCatalogRows(release, {asOf:release.generated_at}).length,2);
  second.memory = structuredClone(config.memory); second.gpu_kind = 'unknown';
  assert.equal(c.verifiedCatalogRows(release, {asOf:release.generated_at}).length,2);
});

test('history uses exact offer observations, deduplicates equivalent instants and never fills gaps', () => {
  const c = setup();
  const receipt = structuredClone(actual.history.receipts[0]);
  const next = structuredClone(receipt);
  next.observation.observed_at = '2026-10-23T00:00:00Z'; next.observation.price_sen -= 100;
  const other = structuredClone(next); other.observation.offer_id = 'other-configuration';
  const release = {generated_at:'2026-10-24T00:00:00Z',history:{receipts:[receipt,receipt,next,other]}};
  const points = c.recordedHistory(release,receipt.observation.offer_id);
  assert.equal(points.length,2);
  assert.equal(points[0].price_sen,receipt.observation.price_sen);
  assert.equal(points[1].price_sen,next.observation.price_sen);
  const conflict = structuredClone(next); conflict.observation.price_sen += 500;
  release.history.receipts.push(conflict);
  assert.throws(() => c.recordedHistory(release,receipt.observation.offer_id), /Conflicting/);
});

test('malformed references or purchase URLs fail closed even in a correctly hashed payload', () => {
  const c = setup(); const release = structuredClone(actual);
  release.catalog.offers[0].configuration_id = 'missing';
  assert.throws(() => c.validateClientRelease(release), /Invalid/);
  release.catalog.offers[0].configuration_id = actual.catalog.offers[0].configuration_id;
  release.catalog.offers[0].url = 'javascript:alert(1)';
  assert.throws(() => c.validateClientRelease(release), /Invalid/);
});
