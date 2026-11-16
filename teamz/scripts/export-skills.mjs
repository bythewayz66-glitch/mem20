/**
 * Export the frontend skill catalogue to a JSON file the orchestrator serves to
 * agents, so they can discover and learn every skill in the catalogue.
 *
 * The catalogue lives in TypeScript (`src/data/templates/skills.ts`), so this
 * script transpiles that module with the esbuild that already ships with Vite
 * and evaluates it — no second source of truth, no hand-copied list.
 *
 * Run: node scripts/export-skills.mjs
 */
import { build } from 'esbuild';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, '..');
const outFile = join(repoRoot, 'server', 'app', 'skill_catalogue.json');

const tmp = mkdtempSync(join(tmpdir(), 'teamz-skills-'));
try {
  const bundle = join(tmp, 'skills.mjs');
  await build({
    entryPoints: [join(repoRoot, 'src', 'data', 'templates', 'skills.ts')],
    outfile: bundle,
    bundle: true,
    format: 'esm',
    platform: 'node',
    logLevel: 'silent',
  });
  const mod = await import(bundle);
  const skills = Object.entries(mod.SKILLS).map(([id, s]) => ({
    id,
    key: s.id,
    label: s.name,
    description: s.description,
    category: s.category,
  }));
  skills.sort((a, b) => a.category.localeCompare(b.category) || a.label.localeCompare(b.label));
  writeFileSync(outFile, JSON.stringify(skills, null, 2) + '\n', 'utf8');
  console.log(`wrote ${skills.length} skills -> ${outFile}`);
} finally {
  rmSync(tmp, { recursive: true, force: true });
}
