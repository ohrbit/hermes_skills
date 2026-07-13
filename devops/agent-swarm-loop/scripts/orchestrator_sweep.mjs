// Orchestrator-sweep harness — reusable fitness sweep for a swarm project.
// Combines the REAL feature branches, runs the GA/metric harness locally (seconds),
// and prints the fitness metric across a parameter sweep to find a BINARY CLIFF
// or the true passable window. Run with: node orchestrator_sweep.mjs
//
// Tunnel-Derby proven shape:
//   - assemble real branches into ./assembled (see ASSEMBLE recipe below)
//   - physics.mjs exports GENE_COUNT, decodeGenome, class Ship, simulate()
//   - tunnel.mjs exports generateTunnel(rng,length)->{length,sample,minRadius,...}
//   - ga.mjs exports GENE_COUNT, randomGenome, breed(ranked)
// Edit the SWEEP arrays + metric extraction to fit your project.

import { createRequire } from "module";
const require = createRequire(import.meta.url);

const tunnel = await import("./tunnel.mjs");
const physics = await import("./physics.mjs");
const ga = await import("./ga.mjs");

function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const POP = 20, GENS = 40;
const rngSeed = 12345;

// ---- EDIT: the metric under test -------------------------------------------
// Here: sweep a physics constant by importing per-constant variants written by
// the Orchestrator (phys_cf30.mjs, phys_cf50.mjs, ...). Replace with your own
// parameter-import loop.
const physicsVariants = {
  30: await import("./phys_cf30.mjs"),
  50: await import("./phys_cf50.mjs"),
  80: await import("./phys_cf80.mjs"),
};

for (const CF of Object.keys(physicsVariants)) {
  const phys = physicsVariants[CF];
  const rng = mulberry32(rngSeed);
  const T = tunnel.generateTunnel(rng, 4000);
  let genomes = [];
  for (let i = 0; i < POP; i++) genomes.push(ga.randomGenome(rng));
  let reach = [], surv = [];
  for (let g = 0; g < GENS; g++) {
    let ranked = [];
    for (const gen of genomes) {
      const ship = new phys.Ship(gen, 0, "x", 0.8);
      const res = phys.simulate(ship, T, 2000);
      ranked.push({ genome: gen, dist: res.dist, crashed: res.crashed });
    }
    ranked.sort((a, b) => b.dist - a.dist);
    reach.push(ranked[0].dist);
    surv.push(ranked.filter((r) => !r.crashed && r.dist > T.length * 0.5).length / POP);
    genomes = ga.breed(ranked);
  }
  const sFinal = (surv.at(-1) * 100).toFixed(0);
  const sFirst = (surv[0] * 100).toFixed(0);
  const gain = ((reach.at(-1) - reach[0]) / (GENS - 1)).toFixed(2);
  console.log(
    `CF=${CF} -> survival_first=${sFirst}% survival_final=${sFinal}% ` +
    `reach=${reach.at(-1).toFixed(0)} convergence_gain/gen=${gain}`
  );
}
// INTERPRET: if every row is 0% or every row is 100%, you hit a BINARY CLIFF.
// Look for the CF where survival jumps — that's the cliff edge. No 40-70% band
// there => the metric has no gradient; apply a design fix (see fitness-tuning.md).

// ---- ASSEMBLE recipe (run once, before this script) ------------------------
// cd /tmp/sweep && git clone git@github.com:owner/repo.git && cd repo
// git fetch origin
// for f in physics.mjs:origin/feat/r3-flight-physicist \
//          tunnel.mjs:origin/feat/r4-tunnel-architect \
//          ga.mjs:origin/feat/r1-ga-breeder \
//          render.mjs:origin/feat/r1-renderer ; do
//   file=${f%:*}; br=${f#*:}
//   git checkout "$br" -- "tunnel-derby/$file"
//   cp "tunnel-derby/$file" assembled/
// done
// # then write phys_cfNN.mjs = physics.mjs with the constant patched, one per CF.
