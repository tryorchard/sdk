/** Live WebSocket channels. @packageDocumentation
 *
 * A {@link Channel} is one of Orchard's per-sandbox streams (logs, shell, screen,
 * adb, vnc, mitm…). It is both an `AsyncIterable` (use `for await`) and a small
 * event emitter (`.on("message"|"open"|"close"|"error")`), and you can `.send()`
 * upstream (shell keystrokes) and `.close()` it.
 */
import { wsBase, type ResolvedConfig } from "./config.js";
import { ChannelClosedError } from "./errors.js";
import { getWebSocket } from "./_ws-impl.js";

const ERR_CODES = new Set([4401, 4403, 4404, 4502]);

export type Decoder<T> = (data: string | ArrayBuffer) => T;

export const decodeText: Decoder<string> = (d) =>
  typeof d === "string" ? d : new TextDecoder().decode(new Uint8Array(d));
export const decodeJson: Decoder<unknown> = (d) => JSON.parse(decodeText(d));
export const decodeBytes: Decoder<Uint8Array> = (d) =>
  typeof d === "string" ? new TextEncoder().encode(d) : new Uint8Array(d);

/** Build `wss?://host/ws/sandboxes/<uuid>/<suffix>?token=…` with auth + extras. */
export function channelUrl(
  cfg: ResolvedConfig,
  uuid: string,
  suffix: string,
  extra: Record<string, string | undefined> = {},
): string {
  return rawChannelUrl(cfg, `ws/sandboxes/${uuid}/${suffix}`, extra);
}

/** Build a WS URL for a non-sandbox path (ws/jobs/…, ws/remote/…). */
export function rawChannelUrl(
  cfg: ResolvedConfig,
  path: string,
  extra: Record<string, string | undefined> = {},
): string {
  const u = new URL(`${wsBase(cfg)}/${path.replace(/^\/+/, "")}`);
  u.searchParams.set("token", cfg.token);
  if (cfg.org) u.searchParams.set("org", cfg.org);
  if (cfg.ws) u.searchParams.set("ws", cfg.ws);
  for (const [k, v] of Object.entries(extra)) if (v !== undefined) u.searchParams.set(k, v);
  return u.toString();
}

type Listener = (payload?: unknown) => void;

/** Synchronous normalization for string / ArrayBuffer / Node Buffer frames.
 * (Browser `Blob` frames are handled separately, async, in the listener.) */
function toData(data: unknown): string | ArrayBuffer {
  if (typeof data === "string") return data;
  if (data instanceof ArrayBuffer) return data;
  const u8 = data as Uint8Array;
  if (u8?.buffer) return u8.buffer.slice(u8.byteOffset, u8.byteOffset + u8.byteLength) as ArrayBuffer;
  return String(data);
}

/** A live, decoded WebSocket stream. Opens eagerly; await {@link ready} or just
 * start iterating. */
export class Channel<T> implements AsyncIterable<T> {
  private socket?: WebSocket;
  private readonly queue: T[] = [];
  private readonly waiters: Array<(r: IteratorResult<T>) => void> = [];
  private readonly listeners = new Map<string, Listener[]>();
  private done = false;
  private error?: Error;
  /** Resolves once the socket is open (rejects if it fails to open). */
  readonly ready: Promise<void>;

  constructor(
    private readonly url: string,
    private readonly decode: Decoder<T>,
  ) {
    this.ready = this.open();
  }

  private emit(event: string, payload?: unknown): void {
    for (const cb of this.listeners.get(event) ?? []) cb(payload);
  }

  /** Subscribe to `message` | `open` | `close` | `error`. */
  on(event: "message" | "open" | "close" | "error", cb: Listener): this {
    const arr = this.listeners.get(event) ?? [];
    arr.push(cb);
    this.listeners.set(event, arr);
    return this;
  }

  private push(item: T): void {
    this.emit("message", item);
    const w = this.waiters.shift();
    if (w) w({ value: item, done: false });
    else this.queue.push(item);
  }

  private finish(err?: Error): void {
    if (this.done) return;
    this.done = true;
    this.error = err;
    this.emit("close");
    while (this.waiters.length) {
      const w = this.waiters.shift()!;
      if (err) w(Promise.reject(err) as never);
      else w({ value: undefined as never, done: true });
    }
  }

  private async open(): Promise<void> {
    const WS = await getWebSocket();
    const socket = new WS(this.url);
    socket.binaryType = "arraybuffer";
    this.socket = socket;
    socket.addEventListener("message", (ev: MessageEvent) => {
      const d = ev.data;
      if (typeof Blob !== "undefined" && d instanceof Blob) {
        void d.arrayBuffer().then((b) => this.push(this.decode(b)));
      } else {
        this.push(this.decode(toData(d)));
      }
    });
    socket.addEventListener("close", (ev: CloseEvent) => {
      this.finish(ERR_CODES.has(ev.code) ? new ChannelClosedError(ev.code, ev.reason) : undefined);
    });
    socket.addEventListener("error", () => this.emit("error", new Error("websocket error")));
    await new Promise<void>((resolve, reject) => {
      socket.addEventListener("open", () => {
        this.emit("open");
        resolve();
      });
      socket.addEventListener("error", () => reject(new Error("failed to open channel")));
    });
  }

  /** Send a frame upstream (e.g. a shell keystroke). Waits for the socket to open. */
  async send(data: string | ArrayBufferView): Promise<void> {
    await this.ready;
    this.socket!.send(data as never);
  }

  /** Close the channel. */
  close(): void {
    try {
      this.socket?.close();
    } catch {
      /* already closed */
    }
    this.finish();
  }

  [Symbol.asyncIterator](): AsyncIterator<T> {
    return {
      next: (): Promise<IteratorResult<T>> => {
        if (this.queue.length) return Promise.resolve({ value: this.queue.shift()!, done: false });
        if (this.error) return Promise.reject(this.error);
        if (this.done) return Promise.resolve({ value: undefined as never, done: true });
        return new Promise((resolve) => this.waiters.push(resolve));
      },
      return: (): Promise<IteratorResult<T>> => {
        this.close();
        return Promise.resolve({ value: undefined as never, done: true });
      },
    };
  }
}
