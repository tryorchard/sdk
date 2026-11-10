import { describe, expect, it } from "vitest";

import { Orchard } from "../src/index.js";

const live = process.env.ORCHARD_SMOKE === "1";

describe.skipIf(!live)("live smoke", () => {
  it("lists, tags and streams logs", async () => {
    const sel = process.env.ORCHARD_SMOKE_UUID ?? "cuttlefish";
    const orchard = Orchard.fromEnv();
    const { instances } = await orchard.sandboxes.list();
    expect(Array.isArray(instances)).toBe(true);
    const sb = await orchard.sandbox(sel);
    await sb.tag("smoke");
    expect((await sb.get()).tag).toBe("smoke");
    if ((await sb.get()).state === "running") {
      const lines: string[] = [];
      for await (const line of sb.logs()) {
        lines.push(line);
        if (lines.length >= 3) break;
      }
      expect(lines.length).toBeGreaterThan(0);
    }
  }, 30000);
});
