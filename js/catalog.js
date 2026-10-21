/** Read models for the verified catalog. No title-based specification inference. */
function canonicalFacts(value) {
  if (Array.isArray(value)) return value.map(canonicalFacts);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(k => [k, canonicalFacts(value[k])]));
  return value;
}

function comparisonKey(config) {
  const d = config.display || {};
  const complete = config.cpu_model && config.gpu_model && ['integrated', 'discrete'].includes(config.gpu_kind)
    && (config.gpu_kind !== 'discrete' || config.vram_gb != null)
    && config.memory?.capacity_gb && config.storage?.capacity_gb
    && ['diagonal_inches', 'resolution_width', 'resolution_height', 'refresh_hz'].every(k => d[k] != null);
  if (!complete) return config.id;
  return JSON.stringify(canonicalFacts(Object.fromEntries(Object.entries(config).filter(([k]) => !['id', 'title', 'evidence'].includes(k)))));
}

function verifiedCatalogRows(release, { asOf = new Date(), includeExpired = false } = {}) {
  const configs = new Map(release.catalog.configurations.map(c => [c.id, c]));
  const groups = new Map();
  for (const offer of release.catalog.offers) {
    const age = offerFreshness(offer, asOf);
    if (age.state === 'unknown' || (!includeExpired && !age.show_by_default)) continue;
    const config = configs.get(offer.configuration_id);
    if (!config) throw new Error('Offer references an unknown configuration');
    const key = comparisonKey(config);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push({ offer, config, age });
  }
  return [...groups.values()].map(entries => {
    // Prefer current usable offers over an unavailable/expired recorded price.
    entries.sort((a, b) => Number(a.age.state === 'expired') - Number(b.age.state === 'expired')
      || Number(a.offer.availability === 'out_of_stock') - Number(b.offer.availability === 'out_of_stock')
      || a.offer.price_sen - b.offer.price_sen || a.offer.id.localeCompare(b.offer.id));
    const { offer: o, config: c, age } = entries[0];
    const display = c.display || {};
    const displayParts = [display.diagonal_inches ? `${display.diagonal_inches}"` : '',
      display.resolution_width && display.resolution_height ? `${display.resolution_width}×${display.resolution_height}` : '',
      display.refresh_hz ? `${display.refresh_hz}Hz` : 'Refresh rate unknown'];
    const deals = entries.map(({ offer, age }) => ({ id: offer.id, vendor: offer.seller,
      price: offer.price_sen / 100, price_sen: offer.price_sen, url: offer.url,
      image_url: offer.image_url || '',
      availability: offer.availability, observed_at: offer.observed_at, freshness: age.state,
      isLowest: age.state !== 'expired' && offer.availability !== 'out_of_stock' && offer.price_sen === o.price_sen }));
    return { verified: true, _rid: entries.map(e => e.offer.id).sort()[0], id: c.manufacturer_part_number,
      title: c.title.replace(/\s*[—–-]\s*Default Title$/i, ''), brand: c.brand,
      configuration_id: c.id, offer_ids: entries.map(e => e.offer.id),
      price: o.price_sen / 100, price_sen: o.price_sen, url: o.url,
      image_url: o.image_url || '', processor: c.cpu_model || '', graphics: c.gpu_model || '',
      gpu_kind: c.gpu_kind, vram_gb: c.vram_gb, memory_gb: c.memory?.capacity_gb ?? null,
      storage_gb: c.storage?.capacity_gb ?? null,
      memory: c.memory?.capacity_gb ? `${c.memory.capacity_gb}GB` : '',
      storage: c.storage?.capacity_gb ? (c.storage.label || `${c.storage.capacity_gb}GB`) : '',
      display: display.diagonal_inches ? displayParts.filter(Boolean).join(' ') : '',
      wifi: c.wifi || '', battery: c.battery_wh != null ? `${c.battery_wh}Wh` : '',
      others: c.warranty || '', best_vendor: o.seller, series: o.seller,
      vendor_count: new Set(deals.map(d => d.vendor)).size, deals,
      availability: o.availability, observed_at: o.observed_at, freshness: age.state,
      evidence: { configuration: c.evidence, offer: o.evidence } };
  });
}

function recordedHistory(release, offerId) {
  const unique = new Map();
  for (const receipt of release.history?.receipts || []) {
    const o = receipt.observation;
    if (o.offer_id !== offerId || !Number.isSafeInteger(o.price_sen) || o.price_sen <= 0 || o.currency !== 'MYR') continue;
    const time = Date.parse(o.observed_at);
    if (!Number.isFinite(time) || time > Date.parse(release.generated_at)) continue;
    const key = `${o.offer_id}:${time}`;
    const prior = unique.get(key);
    if (prior && (prior.price_sen !== o.price_sen || prior.availability !== o.availability)) throw new Error('Conflicting price history');
    unique.set(key, o);
  }
  return [...unique.values()].sort((a, b) => Date.parse(a.observed_at) - Date.parse(b.observed_at));
}

if (typeof module !== 'undefined' && module.exports) module.exports = { comparisonKey, verifiedCatalogRows, recordedHistory };
