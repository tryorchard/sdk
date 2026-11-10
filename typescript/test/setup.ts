/** Test harness: a programmable mock WebSocket installed on globalThis so the
 * SDK's `getWebSocket()` uses it (no real sockets, no `ws` dependency). */

/** The frames + close code the next-opened MockWebSocket will emit. */
export const wsScript: { frames: unknown[]; code: number; reason: string } = {
  frames: [],
  code: 1000,
  reason: "",
};

type Cb = (ev: unknown) => void;

class MockWebSocket {
  binaryType = "blob";
  private listeners: Record<string, Cb[]> = {};
  readonly sent: unknown[] = [];

  constructor(readonly url: string) {
    queueMicrotask(() => {
      this.fire("open", {});
      for (const data of wsScript.frames) this.fire("message", { data });
      this.fire("close", { code: wsScript.code, reason: wsScript.reason });
    });
  }

  addEventListener(ev: string, cb: Cb): void {
    (this.listeners[ev] ??= []).push(cb);
  }
  removeEventListener(): void {}
  send(data: unknown): void {
    this.sent.push(data);
  }
  close(): void {
    this.fire("close", { code: 1000, reason: "" });
  }
  private fire(ev: string, payload: unknown): void {
    for (const cb of this.listeners[ev] ?? []) cb(payload);
  }
}

// Keep the real WebSocket for the live smoke (ORCHARD_SMOKE=1); mock otherwise.
if (process.env.ORCHARD_SMOKE !== "1") {
  (globalThis as unknown as { WebSocket: unknown }).WebSocket = MockWebSocket;
}
