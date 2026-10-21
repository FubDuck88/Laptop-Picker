/** Verified release reader used by every catalog page. */
function validateClientRelease(release) {
  const fail = () => { throw new Error('Invalid verified catalog'); };
  const catalog = release?.catalog;
  if (release?.release_version !== 1 || catalog?.schema_version !== 2 || !Number.isFinite(Date.parse(release.generated_at))
      || !Array.isArray(catalog.configurations) || !Array.isArray(catalog.offers)
      || !Array.isArray(release.source_decisions) || !Array.isArray(release.history?.receipts)) fail();
  const ids = new Set(catalog.configurations.map(c => c.id));
  if (ids.size !== catalog.configurations.length) fail();
  for (const c of catalog.configurations) {
    if (!c.id || typeof c.title !== 'string' || !c.brand || !c.manufacturer_part_number || c.identity_scope !== 'exact_variant') fail();
  }
  const offerIds = new Set();
  for (const o of catalog.offers) {
    if (!o.id || offerIds.has(o.id) || !ids.has(o.configuration_id) || !o.seller
      || !Number.isSafeInteger(o.price_sen) || o.price_sen <= 0 || o.currency !== 'MYR'
      || o.price_basis !== 'public' || o.condition !== 'new'
      || !['in_stock','out_of_stock','unknown'].includes(o.availability) || !Number.isFinite(Date.parse(o.observed_at))) fail();
    try { const u = new URL(o.url); if (!['https:','http:'].includes(u.protocol) || u.username || u.password) fail(); } catch (_) { fail(); }
    offerIds.add(o.id);
  }
  return release;
}
function offerFreshness(offer, asOf = new Date()) {
  const observed = Date.parse(offer.observed_at);
  const now = new Date(asOf).getTime();
  if (!Number.isFinite(observed) || !Number.isFinite(now) || observed > now) {
    return { state: 'unknown', show_by_default: false };
  }
  const age = (now - observed) / 1000;
  const state = age >= 7 * 86400 ? 'expired' : age >= 48 * 3600 ? 'stale' : 'fresh';
  return { state, show_by_default: state !== 'expired', age_seconds: Math.floor(age) };
}

async function loadVerifiedRelease(dataBase = 'data/') {
  const base = new URL(dataBase, location.href);
  const pointerResponse = await fetch(new URL('current.json', base), { cache: 'no-store' });
  if (!pointerResponse.ok) throw new Error('Verified catalog is unavailable');
  const pointer = await pointerResponse.json();
  if (pointer.release_version !== 1 || !/^releases\/[a-f0-9]{64}\.json$/.test(pointer.path) || pointer.path !== `releases/${pointer.sha256}.json`) {
    throw new Error('Invalid catalog pointer');
  }
  const response = await fetch(new URL(pointer.path, base));
  if (!response.ok) throw new Error('Catalog release is unavailable');
  const bytes = await response.arrayBuffer();
  const checksum = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), b => b.toString(16).padStart(2, '0')).join('');
  if (checksum !== pointer.sha256) throw new Error('Catalog integrity check failed');
  const release = JSON.parse(new TextDecoder().decode(bytes));
  validateClientRelease(release);
  // Recompute on every read: a missed scheduled run must not freeze an offer as fresh.
  release.freshness = Object.fromEntries(release.catalog.offers.map(offer => [offer.id, offerFreshness(offer)]));
  return release;
}

if (typeof module !== 'undefined' && module.exports) module.exports = { offerFreshness, loadVerifiedRelease, validateClientRelease };
