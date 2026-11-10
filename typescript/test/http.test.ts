import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../src/errors.js";
import { Orchard } from "../src/index.js";

function orchard(): Orchard {
  return new Orchard({ url: "https://orchard.test", token: "orc_test", org: "acme", ws: "default" });
}

function mockFetch(status: number, body: unknown, capture?: (req: Request) => void) {
  globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    capture?.(new Request(input, init));
    const text = typeof body === "string" ? body : JSON.stringify(body);
    return new Response(status === 204 ? null : text, { status });
  }) as typeof fetch;
}

afterEach(() => vi.restoreAllMocks());

describe("Http", () => {
  it("sends bearer + tenancy headers and hits /api/me", async () => {
    let seen: Request | undefined;
    mockFetch(200, { username: "admin" }, (r) => (seen = r));
    const me = await orchard().me();
    expect(me).toEqual({ username: "admin" });
    expect(seen!.headers.get("Authorization")).toBe("Bearer orc_test");
    expect(seen!.headers.get("X-Orchard-Org")).toBe("acme");
    expect(seen!.url).toMatch(/\/api\/me$/);
  });

  it("maps 401 and 404 to actionable ApiError messages", async () => {
    mockFetch(401, "");
    await expect(orchard().me()).rejects.toThrow(/invalid or expired/);
    mockFetch(404, "");
    await expect(orchard().me()).rejects.toBeInstanceOf(ApiError);
  });

  it("returns undefined for 204", async () => {
    mockFetch(204, "");
    await expect(orchard().keys.delete(5)).resolves.toBeUndefined();
  });

  it("key.create sends the scope fields", async () => {
    let seen: Request | undefined;
    mockFetch(201, { id: 1, token: "orc_new" }, (r) => (seen = r));
    await orchard().keys.create("ci", { sandboxUuids: ["u1"], tag: "pay", allowedFeatures: ["logs"] });
    const body = JSON.parse(await seen!.text());
    expect(body).toMatchObject({ name: "ci", sandbox_uuids: ["u1"], tag: "pay", capabilities: ["logs"] });
  });
});
