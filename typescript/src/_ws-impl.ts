/** Isomorphic WebSocket resolution. @packageDocumentation
 *
 * Browser and Node ≥21/22 expose a global `WebSocket`; only Node 18/20 need the
 * `ws` package (an optional peer dependency, loaded lazily so the browser bundle
 * never pulls it in).
 */
let cached: typeof WebSocket | undefined;

export async function getWebSocket(): Promise<typeof WebSocket> {
  if (cached) return cached;
  if (typeof globalThis.WebSocket !== "undefined") {
    cached = globalThis.WebSocket;
    return cached;
  }
  try {
    const mod = (await import("ws")) as unknown as { default: typeof WebSocket };
    cached = mod.default;
    return cached;
  } catch {
    throw new Error(
      "no WebSocket available: on Node < 21 install the optional peer dependency `ws`",
    );
  }
}
