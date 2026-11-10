import { describe, expect, it } from "vitest";

import { SelectorError } from "../src/errors.js";
import type { Instance } from "../src/models.js";
import { resolve, resolveAll } from "../src/selector.js";

const I = [
  { uuid: "a31eba21-953b-4184-8ed7-5cf3bd062615", name: "cuttlefish", display_name: "cuttlefish", tag: "pay" },
  { uuid: "2609ff67-aaaa", name: "pixel", display_name: "pixel", tag: "pay" },
  { uuid: "6acc3ef4", name: "spare", tag: "" },
  { uuid: null, name: "remote-x", tag: "" },
] as unknown as Instance[];

describe("selector", () => {
  it("exact uuid, prefix, name", () => {
    expect(resolve(I, "a31eba21-953b-4184-8ed7-5cf3bd062615").name).toBe("cuttlefish");
    expect(resolve(I, "2609ff67").name).toBe("pixel");
    expect(resolve(I, "spare").uuid).toBe("6acc3ef4");
  });
  it("tag matches many -> resolve throws, resolveAll returns all", () => {
    expect(() => resolve(I, "pay")).toThrow(SelectorError);
    expect(resolveAll(I, "pay")).toHaveLength(2);
  });
  it("rows without uuid are excluded; no match throws", () => {
    expect(resolveAll(I, "remote-x")).toHaveLength(0);
    expect(() => resolve(I, "nope")).toThrow(SelectorError);
  });
});
