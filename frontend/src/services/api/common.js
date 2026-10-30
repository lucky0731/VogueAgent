// The monolith serves reads and writes from the same origin. /config can point
// writes elsewhere for a split deployment.
export const API_BASE = '';
export let INGESTION_API_BASE = '';

/** Call once at startup. Keeps the same-origin default if /config is unavailable. */
export async function initIngestionApiBase() {
    try {
        const res = await fetch(`${API_BASE}/config`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.ingestion_base_url !== undefined && data.ingestion_base_url !== null) {
            INGESTION_API_BASE = data.ingestion_base_url;
        }
    } catch {
        // same-origin default
    }
}
