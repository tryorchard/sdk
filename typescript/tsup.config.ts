import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm", "cjs"],
  dts: true,
  sourcemap: true,
  clean: true,
  treeshake: true,
  target: "node18",
  external: ["ws"], // optional peer — never bundled; browser build stays clean
  outExtension: ({ format }) => ({ js: format === "cjs" ? ".cjs" : ".js" }),
});
