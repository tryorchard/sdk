import { afterEach, describe, expect, it, vi } from "vitest";

import { Orchard } from "../src/index.js";

const UUID = "a31eba21-953b-4184-8ed7-5cf3bd062615";

function run(call: (o: Orchard) => Promise<unknown>) {
  const seen: { method?: string; path?: string } = {};
  globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const req = new Request(input, init);
    seen.method = req.method;
    seen.path = new URL(req.url).pathname;
    return new Response(JSON.stringify({ instances: [], uuid: UUID, url: "/api/x" }), { status: 200 });
  }) as typeof fetch;
  const o = new Orchard({ url: "https://orchard.test", token: "orc_test" });
  return call(o).then(() => seen);
}

afterEach(() => vi.restoreAllMocks());

const cases: Array<[string, (o: Orchard) => Promise<unknown>, string, string]> = [
  ["sandboxes.list", (o) => o.sandboxes.list(), "GET", "/api/instances"],
  ["sandboxes.create", (o) => o.sandboxes.create({ name: "x" }), "POST", "/api/instances/create"],
  ["sandbox.start", (o) => o.sandboxes.get(UUID).start(), "POST", `/api/sandboxes/${UUID}/start`],
  ["sandbox.get", (o) => o.sandboxes.get(UUID).get(), "GET", `/api/sandboxes/${UUID}`],
  ["sandbox.tag", (o) => o.sandboxes.get(UUID).tag("t", "#112233"), "PATCH", `/api/sandboxes/${UUID}`],
  ["apps.uninstall", (o) => o.sandboxes.get(UUID).apps.uninstall("com.x"), "POST", `/api/sandboxes/${UUID}/apps/uninstall`],
  ["snapshots.restore", (o) => o.sandboxes.get(UUID).snapshots.restore("s1"), "POST", `/api/sandboxes/${UUID}/snapshots/s1`],
  ["keys.list", (o) => o.keys.list(), "GET", "/api/tokens"],
  ["templates.list", (o) => o.templates.list(), "GET", "/api/templates"],
  ["catalog.android", (o) => o.catalog.android(), "GET", "/api/android/catalog"],
  ["jobs.list", (o) => o.jobs.list(), "GET", "/api/jobs"],
  ["team.members.list", (o) => o.team.members.list(), "GET", "/api/org/members"],
  ["remote.catalog", (o) => o.remote.catalog(), "GET", "/api/remote/catalog"],
  // input wrappers all POST the unified /control endpoint
  ["sandbox.tap", (o) => o.sandboxes.get(UUID).tap(1, 2), "POST", `/api/sandboxes/${UUID}/control`],
  ["sandbox.swipe", (o) => o.sandboxes.get(UUID).swipe(1, 2, 3, 4), "POST", `/api/sandboxes/${UUID}/control`],
  ["sandbox.key", (o) => o.sandboxes.get(UUID).key("home"), "POST", `/api/sandboxes/${UUID}/control`],
  ["sandbox.text", (o) => o.sandboxes.get(UUID).text("hi"), "POST", `/api/sandboxes/${UUID}/control`],
  ["sandbox.tapText", (o) => o.sandboxes.get(UUID).tapText("Login"), "POST", `/api/sandboxes/${UUID}/control`],
  ["sandbox.launch", (o) => o.sandboxes.get(UUID).launch("com.x"), "POST", `/api/sandboxes/${UUID}/control`],
  ["sandbox.launchIntent", (o) => o.sandboxes.get(UUID).launchIntent("com.x", ".Main"), "POST", `/api/sandboxes/${UUID}/control`],
  // frida: status is a GET, everything else POSTs the same /frida endpoint
  ["frida.status", (o) => o.sandboxes.get(UUID).frida.status(), "GET", `/api/sandboxes/${UUID}/frida`],
  ["frida.install", (o) => o.sandboxes.get(UUID).frida.install(), "POST", `/api/sandboxes/${UUID}/frida`],
  ["frida.start", (o) => o.sandboxes.get(UUID).frida.start(), "POST", `/api/sandboxes/${UUID}/frida`],
  ["frida.stop", (o) => o.sandboxes.get(UUID).frida.stop(), "POST", `/api/sandboxes/${UUID}/frida`],
  ["frida.verify", (o) => o.sandboxes.get(UUID).frida.verify("com.x"), "POST", `/api/sandboxes/${UUID}/frida`],
  ["frida.inject", (o) => o.sandboxes.get(UUID).frida.inject("x", "com.x"), "POST", `/api/sandboxes/${UUID}/frida`],
  // debugger (lldb): status is a GET, install/start POST the same /debugger endpoint
  ["debugger.status", (o) => o.sandboxes.get(UUID).debugger.status(), "GET", `/api/sandboxes/${UUID}/debugger`],
  ["debugger.install", (o) => o.sandboxes.get(UUID).debugger.install(), "POST", `/api/sandboxes/${UUID}/debugger`],
  ["debugger.start", (o) => o.sandboxes.get(UUID).debugger.start("com.x"), "POST", `/api/sandboxes/${UUID}/debugger`],
];

describe("resource routing", () => {
  for (const [name, call, method, path] of cases) {
    it(name, async () => {
      const seen = await run(call);
      expect([seen.method, seen.path]).toEqual([method, path]);
    });
  }
});

describe("input bodies", () => {
  async function body(call: (o: Orchard) => Promise<unknown>): Promise<unknown> {
    let captured: unknown;
    globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      captured = JSON.parse((await new Request(input, init).text()) || "{}");
      return new Response("{}", { status: 200 });
    }) as typeof fetch;
    await call(new Orchard({ url: "https://orchard.test", token: "orc_test" }));
    return captured;
  }
  it("tap", async () => expect(await body((o) => o.sandboxes.get(UUID).tap(540, 1200)))
    .toEqual({ action: "tap", x: 540, y: 1200 }));
  it("swipe", async () => expect(await body((o) => o.sandboxes.get(UUID).swipe(1, 2, 3, 4, 120)))
    .toEqual({ action: "swipe", x1: 1, y1: 2, x2: 3, y2: 4, ms: 120 }));
  it("key", async () => expect(await body((o) => o.sandboxes.get(UUID).key("back")))
    .toEqual({ action: "key", name: "back" }));
  it("text", async () => expect(await body((o) => o.sandboxes.get(UUID).text("hello")))
    .toEqual({ action: "text", text: "hello" }));
  it("tapText", async () => expect(await body((o) => o.sandboxes.get(UUID).tapText("OK")))
    .toEqual({ action: "tap_text", text: "OK" }));
  it("launch", async () => expect(await body((o) => o.sandboxes.get(UUID).launch("com.x")))
    .toEqual({ action: "launch", app: "com.x" }));
  it("launchIntent", async () => expect(await body((o) =>
    o.sandboxes.get(UUID).launchIntent("com.x", ".Main", { action: "A", data: "u://x", extras: { k: "v" } })))
    .toEqual({ action: "launch_intent", package: "com.x", component: ".Main",
               intent_action: "A", data: "u://x", extras: { k: "v" } }));
  it("frida.install", async () => expect(await body((o) => o.sandboxes.get(UUID).frida.install()))
    .toEqual({ action: "install" }));
  it("frida.verify", async () => expect(await body((o) => o.sandboxes.get(UUID).frida.verify("SpringBoard")))
    .toEqual({ action: "verify", process: "SpringBoard" }));
  it("frida.inject", async () => expect(await body((o) => o.sandboxes.get(UUID).frida.inject("console.log(1)", "com.x", 10)))
    .toEqual({ action: "inject", script: "console.log(1)", process: "com.x", timeout: 10 }));
  it("debugger.start", async () => expect(await body((o) => o.sandboxes.get(UUID).debugger.start("com.x")))
    .toEqual({ action: "start", process: "com.x" }));
});
