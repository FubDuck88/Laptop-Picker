const assert = require('node:assert/strict');
const test = require('node:test');
const { offerFreshness } = require('../js/release.js');

test('freshness ages at read time even when a daily run is missed', () => {
  const offer = { observed_at: '2026-10-20T00:00:00Z' };
  assert.equal(offerFreshness(offer, '2026-10-21T23:59:59Z').state, 'fresh');
  assert.equal(offerFreshness(offer, '2026-10-22T00:00:00Z').state, 'stale');
  assert.equal(offerFreshness(offer, '2026-10-27T00:00:00Z').show_by_default, false);
  assert.equal(offerFreshness(offer, '2026-10-19T00:00:00Z').show_by_default, false);
  assert.equal(offerFreshness({observed_at: 'invalid'}).show_by_default, false);
});

test('release reader checks the pointer, file hash, and current offer age', async () => {
  const fs = require('node:fs');
  const vm = require('node:vm');
  const { createHash, webcrypto } = require('node:crypto');
  const pointerFile = JSON.parse(fs.readFileSync(require('node:path').join(__dirname, '../data/current.json')));
  const actual = JSON.parse(fs.readFileSync(require('node:path').join(__dirname, '../data', pointerFile.path)));
  for (const offer of actual.catalog.offers) offer.observed_at = '2000-01-01T00:00:00Z';
  const oldId = actual.catalog.offers[0].id;
  const bytes = Buffer.from(JSON.stringify(actual));
  const sha256 = createHash('sha256').update(bytes).digest('hex');
  let pointer = { release_version: 1, path: `releases/${sha256}.json`, sha256 };
  let payload = bytes;
  const context = vm.createContext({ URL, TextDecoder, crypto: webcrypto,
    location: { href: 'https://picker.example/project/index.html' },
    fetch: async url => String(url).endsWith('current.json')
      ? { ok: true, json: async () => pointer }
      : { ok: true, arrayBuffer: async () => payload.buffer.slice(payload.byteOffset, payload.byteOffset + payload.byteLength) } });
  vm.runInContext(fs.readFileSync(require('node:path').join(__dirname, '../js/release.js'), 'utf8'), context);
  const release = await context.loadVerifiedRelease();
  assert.equal(release.freshness[oldId].show_by_default, false);
  payload = Buffer.from('{}');
  await assert.rejects(context.loadVerifiedRelease(), /integrity/);
  pointer = { ...pointer, path: '../outside.json' };
  await assert.rejects(context.loadVerifiedRelease(), /pointer/);
});
