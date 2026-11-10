import { describe, expect, it } from "vitest";

import { ChannelClosedError } from "../src/errors.js";
import { Channel, decodeBytes, decodeText } from "../src/ws.js";
import { wsScript } from "./setup.js";

async function collect<T>(ch: Channel<T>): Promise<T[]> {
  const out: T[] = [];
  for await (const f of ch) out.push(f);
  return out;
}

describe("Channel", () => {
  it("yields decoded text frames then ends on clean close", async () => {
    wsScript.frames = ["a", "b", "c"];
    wsScript.code = 1000;
    expect(await collect(new Channel("ws://x/logs", decodeText))).toEqual(["a", "b", "c"]);
  });

  it("decodes binary frames to Uint8Array", async () => {
    wsScript.frames = [new TextEncoder().encode("hi").buffer];
    wsScript.code = 1000;
    const out = await collect(new Channel("ws://x/screen", decodeBytes));
    expect(Array.from(out[0])).toEqual([104, 105]);
  });

  it("fires .on('message') and .on('open')", async () => {
    wsScript.frames = ["x"];
    wsScript.code = 1000;
    const seen: string[] = [];
    const ch = new Channel<string>("ws://x/logs", decodeText);
    ch.on("open", () => seen.push("open"));
    ch.on("message", (m) => seen.push(`msg:${m}`));
    await collect(ch);
    expect(seen).toContain("open");
    expect(seen).toContain("msg:x");
  });

  it("rejects with ChannelClosedError on an error close code", async () => {
    wsScript.frames = [];
    wsScript.code = 4403;
    wsScript.reason = "forbidden";
    await expect(collect(new Channel("ws://x/logs", decodeText))).rejects.toBeInstanceOf(
      ChannelClosedError,
    );
  });
});
