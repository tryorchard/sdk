import React from "react";

/**
 * Embed a live Orchard device in your own React app.
 *
 * It renders the hosted, chrome-less viewer (`/embed/<uuid>`) in an iframe, so
 * there is exactly one renderer to maintain and the same security model as the
 * raw iframe form: the browser holds only a short-lived, single-sandbox embed
 * token (mint it server-side with `sandbox.embedToken()` / `sandbox.embed_token()`),
 * never your API key.
 *
 *   // server (Node/Python): mint a scoped token for ONE sandbox
 *   const { url } = await orchard.sandbox(uuid).embedToken({ input: true, base: UI_ORIGIN });
 *
 *   // client: hand the url straight to the component
 *   <OrchardViewer url={url} style={{ width: 360, height: 780 }} />
 *
 * Or build the src from parts (token + where the viewer and API live):
 *   <OrchardViewer uuid={uuid} token={token} input viewerBase={UI_ORIGIN} />
 */
export interface OrchardViewerProps {
  /** The absolute `url` returned by embedToken() — the simplest path. */
  url?: string;
  /** Or build the src from parts: */
  uuid?: string;
  token?: string;
  input?: boolean;
  /** Origin serving the Orchard UI (where /embed/<uuid> lives). */
  viewerBase?: string;
  /** Origin of the Orchard API, if different from the viewer's default guess. */
  apiBase?: string;
  /** Frames per second the viewer polls at (1..10, default 4). */
  fps?: number;
  style?: React.CSSProperties;
  className?: string;
  title?: string;
}

export function OrchardViewer(props: OrchardViewerProps): React.ReactElement {
  const { url, uuid, token, input, viewerBase, apiBase, fps, style, className, title } = props;
  let src = url;
  if (!src) {
    if (!uuid || !token) throw new Error("OrchardViewer: pass `url`, or both `uuid` and `token`");
    const base = (viewerBase || "").replace(/\/+$/, "");
    const q = new URLSearchParams({ token });
    if (input) q.set("input", "1");
    if (apiBase) q.set("api", apiBase);
    if (fps) q.set("fps", String(fps));
    src = `${base}/embed/${uuid}?${q.toString()}`;
  }
  return (
    <iframe
      src={src}
      title={title || "Orchard device"}
      allow="clipboard-write"
      style={{ border: 0, width: 448, height: 932, borderRadius: 14, background: "#0b0d10", ...style }}
      className={className}
    />
  );
}

export default OrchardViewer;
