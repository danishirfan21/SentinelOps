const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
async function get(path) { const r = await fetch(base + path); if (!r.ok)
    throw Error('Unable to load SentinelOps data.'); return r.json(); }
export const api = { services: () => get('/api/v1/services'), health: (id) => get(`/api/v1/services/${id}/health`), checks: (id) => get(`/api/v1/services/${id}/checks`), history: (id) => get(`/api/v1/services/${id}/health-history`), alerts: () => get('/api/v1/alerts'), incidents: () => get('/api/v1/incidents'), incident: (id) => get(`/api/v1/incidents/${id}`), events: (id) => get(`/api/v1/incidents/${id}/events`) };
