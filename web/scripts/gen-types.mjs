#!/usr/bin/env node
import { readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { compile } from "json-schema-to-typescript";

const here = dirname(fileURLToPath(import.meta.url));
const schemaPath = resolve(here, "../../schemas/textile-dpp.v1.json");
const outPath = resolve(here, "../lib/generated/textile-dpp.ts");

const schema = JSON.parse(await readFile(schemaPath, "utf8"));
const ts = await compile(schema, "TextileDPP", {
  bannerComment:
    "/* Auto-generated from schemas/textile-dpp.v1.json. Do not edit by hand. */",
  additionalProperties: false,
  style: { singleQuote: false, trailingComma: "all", printWidth: 100 },
});

await writeFile(outPath, ts, "utf8");
console.log(`wrote ${outPath}`);
