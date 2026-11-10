/** Resolve a human-friendly sandbox selector to a concrete instance.
 * Precedence: exact uuid, uuid prefix, exact name/display_name, then tag.
 * @packageDocumentation */
import { SelectorError } from "./errors.js";
import type { Instance } from "./models.js";

function candidates(instances: Instance[]): Instance[] {
  return instances.filter((i) => i.uuid);
}

/** Every instance a selector matches, by the first precedence tier that hits. */
export function resolveAll(instances: Instance[], selector: string): Instance[] {
  const cands = candidates(instances);
  const tiers: Array<(i: Instance) => boolean> = [
    (i) => i.uuid === selector,
    (i) => String(i.uuid).startsWith(selector),
    (i) => i.name === selector || i.display_name === selector,
    (i) => !!selector && i.tag === selector,
  ];
  for (const pred of tiers) {
    const hit = cands.filter(pred);
    if (hit.length) return hit;
  }
  return [];
}

/** Exactly one instance, or throw {@link SelectorError} (zero or ambiguous). */
export function resolve(instances: Instance[], selector: string): Instance {
  const matches = resolveAll(instances, selector);
  if (matches.length === 0) throw new SelectorError(`no sandbox matches ${JSON.stringify(selector)}`);
  if (matches.length > 1) {
    const lines = matches
      .map((i) => `  ${i.name ?? "?"}  ${i.uuid}  tag=${i.tag || "-"}  node=${i.node || "-"}`)
      .join("\n");
    throw new SelectorError(
      `${JSON.stringify(selector)} matches ${matches.length} sandboxes — be more specific:\n${lines}`,
    );
  }
  return matches[0];
}
