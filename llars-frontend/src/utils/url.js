/**
 * URL-Sicherheitshelfer (XSS-Schutz für gespeicherte Links).
 *
 * Vue sanitisiert `:href`/`:src`-Bindings NICHT. Bindet man eine vom Nutzer
 * gespeicherte URL (z.B. Conference-/Paper-Links, die in Gruppen geteilt werden)
 * direkt an ein Anchor, kann ein Wert wie `javascript:fetch(...)` beim Klick im
 * Kontext eines Kollegen Code ausführen (Stored XSS / Token-Diebstahl).
 *
 * `safeExternalUrl` lässt nur http(s)- und mailto-URLs durch und liefert sonst
 * `null`, sodass das `:href` leer bleibt statt zu „feuern“.
 */

const SAFE_SCHEMES = ['http:', 'https:', 'mailto:'];

/**
 * Gibt die URL zurück, wenn ihr Schema sicher ist, sonst null.
 *
 * @param {string} url - die zu prüfende, ggf. vom Nutzer stammende URL
 * @returns {string|null} sichere URL oder null
 */
export function safeExternalUrl(url) {
  if (!url || typeof url !== 'string') return null;
  const trimmed = url.trim();
  if (!trimmed) return null;

  // Schema-loses "example.com" als externen Link interpretieren → https voranstellen.
  // (Kein "//host" zulassen, das wäre protokoll-relativ und schwerer zu prüfen.)
  const candidate = /^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(trimmed)
    ? trimmed
    : `https://${trimmed.replace(/^\/+/, '')}`;

  try {
    const parsed = new URL(candidate);
    if (SAFE_SCHEMES.includes(parsed.protocol)) {
      return candidate;
    }
  } catch {
    // Unparsebar → als unsicher behandeln
    return null;
  }
  return null;
}
