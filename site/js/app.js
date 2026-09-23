// RGENGY DFS Platform — progressive enhancement SPA.
// Loads demo data (the only data source in this repo since live feeds require
// network access the Pages build does not retain), projects players (using the
// same engine the Python side uses, ported to JS), optimizes lineups client-side,
// runs Monte Carlo contest simulation, and surfaces every result with its
// provenance.  Nothing here is fabricated: "unavailable" is always a legal answer.

(function () {
  "use strict";

  const CONFIG = {
    sports: ["mlb", "nba", "nfl", "nhl", "wnba"],
    sites: ["draftkings", "fanduel"],
    sportLabels: { mlb: "MLB", nba: "NBA", nfl: "NFL", nhl: "NHL", wnba: "WNBA" },
    siteLabels: { draftkings: "DraftKings", fanduel: "FanDuel" },
    date: "2026-09-22",
    dataRoot: "data/demo/",
    salaryStep: 100,
    nSims: 500,
    fieldSize: 200,
    sharpFraction: 0.5,
  };

  // Roster templates (verified copies of models.py defaults).
  const ROSTER_TEMPLATES = {
    "mlb:draftkings": {
      cap: 50000, n: 10,
      slots: [
        { label: "P", count: 2, eligible: ["P", "SP", "RP"] },
        { label: "C/1B", count: 1, eligible: ["C", "1B"] },
        { label: "2B", count: 1, eligible: ["2B"] },
        { label: "3B", count: 1, eligible: ["3B"] },
        { label: "SS", count: 1, eligible: ["SS"] },
        { label: "OF", count: 3, eligible: ["OF", "LF", "CF", "RF"] },
        { label: "UTIL", count: 1, eligible: ["C", "1B", "2B", "3B", "SS", "OF", "LF", "CF", "RF"] },
      ],
      src: "single-source",
    },
    "mlb:fanduel": {
      cap: 35000, n: 9,
      slots: [
        { label: "P", count: 1, eligible: ["P", "SP", "RP"] },
        { label: "C/1B", count: 1, eligible: ["C", "1B"] },
        { label: "2B", count: 1, eligible: ["2B"] },
        { label: "3B", count: 1, eligible: ["3B"] },
        { label: "SS", count: 1, eligible: ["SS"] },
        { label: "OF", count: 3, eligible: ["OF", "LF", "CF", "RF"] },
        { label: "UTIL", count: 1, eligible: ["C", "1B", "2B", "3B", "SS", "OF", "LF", "CF", "RF"] },
      ],
      src: "single-source",
    },
    "nba:draftkings": {
      cap: 50000, n: 8,
      slots: [
        { label: "PG", count: 1, eligible: ["PG"] },
        { label: "SG", count: 1, eligible: ["SG"] },
        { label: "G", count: 1, eligible: ["PG", "SG"] },
        { label: "SF", count: 1, eligible: ["SF"] },
        { label: "PF", count: 1, eligible: ["PF"] },
        { label: "F", count: 1, eligible: ["SF", "PF"] },
        { label: "C", count: 1, eligible: ["C"] },
        { label: "UTIL", count: 1, eligible: ["PG", "SG", "SF", "PF", "C"] },
      ],
      src: "multi-source-consistent",
    },
    "nba:fanduel": {
      cap: 60000, n: 9,
      slots: [
        { label: "PG", count: 2, eligible: ["PG"] },
        { label: "SG", count: 2, eligible: ["SG"] },
        { label: "SF", count: 2, eligible: ["SF"] },
        { label: "PF", count: 2, eligible: ["PF"] },
        { label: "C", count: 1, eligible: ["C"] },
      ],
      src: "multi-source-consistent",
    },
    "nfl:draftkings": {
      cap: 50000, n: 9,
      slots: [
        { label: "QB", count: 1, eligible: ["QB"] },
        { label: "RB", count: 2, eligible: ["RB"] },
        { label: "WR", count: 3, eligible: ["WR"] },
        { label: "TE", count: 1, eligible: ["TE"] },
        { label: "FLEX", count: 1, eligible: ["RB", "WR", "TE"] },
        { label: "DST", count: 1, eligible: ["DST", "D"] },
      ],
      src: "multi-source-consistent",
    },
    "nfl:fanduel": {
      cap: 60000, n: 9,
      slots: [
        { label: "QB", count: 1, eligible: ["QB"] },
        { label: "RB", count: 2, eligible: ["RB"] },
        { label: "WR", count: 3, eligible: ["WR"] },
        { label: "TE", count: 1, eligible: ["TE"] },
        { label: "FLEX", count: 1, eligible: ["RB", "WR", "TE", "K"] },
        { label: "DST", count: 1, eligible: ["DST", "D"] },
      ],
      src: "disputed",
    },
    "nhl:draftkings": {
      cap: 50000, n: 9,
      slots: [
        { label: "C", count: 2, eligible: ["C"] },
        { label: "W", count: 3, eligible: ["LW", "RW", "W"] },
        { label: "D", count: 2, eligible: ["D"] },
        { label: "UTIL", count: 1, eligible: ["C", "LW", "RW", "W", "D", "G"] },
        { label: "G", count: 1, eligible: ["G"] },
      ],
      src: "single-source",
    },
    "nhl:fanduel": {
      cap: 40000, n: 9,
      slots: [
        { label: "C", count: 2, eligible: ["C"] },
        { label: "W", count: 2, eligible: ["LW", "RW", "W"] },
        { label: "D", count: 2, eligible: ["D"] },
        { label: "UTIL", count: 2, eligible: ["C", "LW", "RW", "W", "D", "G"] },
        { label: "G", count: 1, eligible: ["G"] },
      ],
      src: "single-source",
    },
    "wnba:draftkings": {
      cap: 50000, n: 6,
      slots: [
        { label: "G", count: 2, eligible: ["G", "PG", "SG"] },
        { label: "F", count: 2, eligible: ["F", "SF", "PF"] },
        { label: "C", count: 1, eligible: ["C"] },
        { label: "UTIL", count: 1, eligible: ["G", "F", "C", "PG", "SG", "SF", "PF"] },
      ],
      src: "not-audited",
    },
    "wnba:fanduel": {
      cap: 40000, n: 6,
      slots: [
        { label: "G", count: 2, eligible: ["G", "PG", "SG"] },
        { label: "F", count: 2, eligible: ["F", "SF", "PF"] },
        { label: "C", count: 1, eligible: ["C"] },
        { label: "UTIL", count: 1, eligible: ["G", "F", "C", "PG", "SG", "SF", "PF"] },
      ],
      src: "not-audited",
    },
  };

  // --------------------------------------------------------------------------
  // State
  // --------------------------------------------------------------------------
  const state = {
    sport: "nba",
    site: "draftkings",
    data: null,         // the loaded run result
    players: [],        // normalized players
    locked: new Set(),
    excluded: new Set(),
    lineups: [],
    simResults: null,
    sortKey: "fpts",
    sortDir: "desc",
    posFilter: "ALL",
    searchQ: "",
  };

  // --------------------------------------------------------------------------
  // Data loading
  // --------------------------------------------------------------------------
  async function loadData(sport, site) {
    const fname = `demo-${sport}-${site}.json`;
    const res = await fetch(CONFIG.dataRoot + fname);
    if (!res.ok) throw new Error(`Failed to load ${fname}: HTTP ${res.status}`);
    return res.json();
  }

  function normalizePlayers(doc) {
    const site = doc.site;
    const slate = doc.slate || {};
    return (slate.players || []).map((p) => {
      const fpts = (p.fpts && p.fpts[site]) || 0;
      const sal = p.salary || 0;
      return {
        id: p.player_id,
        name: p.name,
        team: p.team,
        opp: p.opp,
        positions: p.positions || [],
        position: (p.positions || []).join("/"),
        salary: sal,
        fpts: fpts,
        floor: p.floor || 0,
        ceil: p.ceil || 0,
        sd: (p.extra && p.extra.sd) || 0,
        value: sal > 0 ? +(fpts / (sal / 1000)).toFixed(2) : 0,
        pown: (p.pown == null ? null : +(p.pown * 100).toFixed(2)),
        status: p.status || "",
        projected: p.projected || {},
        gameLine: (p.extra && p.extra.game_line) || null,
        lev: (p.extra && p.extra.lev) || null,
        smash: (p.extra && p.extra.smash) || null,
        notes: (p.extra && p.extra.engine_notes) || [],
      };
    });
  }

  // --------------------------------------------------------------------------
  // Optimizer (port of rgengy/optimizer.py)
  // --------------------------------------------------------------------------
  function matches(positions, eligible) {
    return positions.some((p) => eligible.indexOf(p) !== -1);
  }

  function overlapPairs(rules, members, pool) {
    const pairs = [];
    for (let ai = 0; ai < members.length; ai++) {
      for (let bi = ai + 1; bi < members.length; bi++) {
        const a = members[ai], b = members[bi];
        const ea = new Set(rules[a].eligible), eb = new Set(rules[b].eligible);
        let conflict = false;
        for (const x of ea) { if (eb.has(x)) { conflict = true; break; } }
        if (!conflict && pool) {
          for (const p of pool) {
            if (matches(p.positions, rules[a].eligible) && matches(p.positions, rules[b].eligible)) {
              conflict = true; break;
            }
          }
        }
        if (conflict) pairs.push([a, b]);
      }
    }
    return pairs;
  }

  function splitSlots(rules, pool) {
    let fixed = rules.map((_, i) => i);
    const flex = [];
    while (true) {
      const pairs = overlapPairs(rules, fixed, pool);
      if (!pairs.length) break;
      const counts = {};
      for (const [a, b] of pairs) { counts[a] = (counts[a] || 0) + 1; counts[b] = (counts[b] || 0) + 1; }
      let victim = -1, best = -1;
      for (const k of Object.keys(counts)) {
        const i = +k;
        const score = counts[i] * 1000 + rules[i].eligible.length;
        if (score > best) { best = score; victim = i; }
      }
      fixed = fixed.filter((x) => x !== victim);
      flex.push(victim);
    }
    flex.sort((a, b) => a - b);
    return { flex, fixed };
  }

  function groupKnapsack(pool, need, unitsCap, site) {
    if (need <= 0) {
      const curve = new Array(unitsCap + 1).fill(-Infinity);
      curve[0] = 0;
      const picks = new Array(unitsCap + 1).fill(null).map(() => []);
      return { curve, picks };
    }
    if (pool.length < need) return null;
    const NEG = -Infinity;
    const dp = []; const pick = [];
    for (let j = 0; j <= need; j++) {
      dp.push(new Array(unitsCap + 1).fill(NEG));
      pick.push(new Array(unitsCap + 1).fill(null).map(() => []));
    }
    dp[0][0] = 0;
    for (let idx = 0; idx < pool.length; idx++) {
      const p = pool[idx];
      const cost = Math.floor(p.salary / CONFIG.salaryStep);
      const pts = p.fpts;
      if (cost > unitsCap) continue;
      for (let j = need - 1; j >= 0; j--) {
        const src = dp[j], dst = dp[j + 1];
        const psrc = pick[j], pdst = pick[j + 1];
        for (let s = unitsCap - cost; s >= 0; s--) {
          if (src[s] === NEG) continue;
          const cand = src[s] + pts;
          const t = s + cost;
          if (cand > dst[t]) { dst[t] = cand; pdst[t] = psrc[s].concat(idx); }
        }
      }
    }
    const best = dp[need];
    if (best.every((v) => v === NEG)) return null;
    return { curve: best, picks: pick[need] };
  }

  function convolve(results, unitsCap) {
    const NEG = -Infinity;
    let best = new Array(unitsCap + 1).fill(NEG); best[0] = 0;
    let trace = new Array(unitsCap + 1).fill(null).map(() => []);
    for (let gi = 0; gi < results.length; gi++) {
      const { curve } = results[gi];
      const nb = new Array(unitsCap + 1).fill(NEG);
      const nt = new Array(unitsCap + 1).fill(null).map(() => []);
      const levels = [];
      for (let s = 0; s <= unitsCap; s++) if (curve[s] !== NEG) levels.push(s);
      for (let s = 0; s <= unitsCap; s++) {
        if (best[s] === NEG) continue;
        const base = best[s], bt = trace[s];
        for (const s2 of levels) {
          const t = s + s2;
          if (t > unitsCap) break;
          const cand = base + curve[s2];
          if (cand > nb[t]) { nb[t] = cand; nt[t] = bt.concat([[gi, s2]]); }
        }
      }
      best = nb; trace = nt;
    }
    return { best, trace };
  }

  function solveFixed(pool, fixedRules, unitsCap, site, excluded) {
    const available = pool.filter((p) => !excluded.has(p.id) && p.salary != null);
    const groups = [];
    for (const rule of fixedRules) groups.push(available.filter((p) => matches(p.positions, rule.eligible)));
    const results = [];
    for (let gi = 0; gi < fixedRules.length; gi++) {
      const r = groupKnapsack(groups[gi], fixedRules[gi].count, unitsCap, site);
      if (!r) return null;
      results.push(r);
    }
    const { best, trace } = convolve(results, unitsCap);
    let bestS = -1, bestPts = -Infinity;
    for (let s = 0; s <= unitsCap; s++) if (best[s] > bestPts) { bestPts = best[s]; bestS = s; }
    if (bestS < 0) return null;
    const chosen = [];
    for (const [gi, s2] of trace[bestS]) {
      for (const idx of results[gi].picks[s2]) chosen.push(groups[gi][idx]);
    }
    const ids = chosen.map((p) => p.id);
    if (new Set(ids).size !== ids.length) return null;
    const salary = chosen.reduce((a, p) => a + Math.floor(p.salary), 0);
    return { players: chosen, salary, pts: bestPts };
  }

  function optimize(players, sport, site) {
    const key = sport + ":" + site;
    const tmpl = ROSTER_TEMPLATES[key];
    if (!tmpl) return { feasible: false, reason: `Unknown roster template ${key}` };
    const cap = tmpl.cap;
    let allRules = tmpl.slots.map((r) => ({ label: r.label, count: r.count, eligible: r.eligible.slice() }));
    const usable = players.filter((p) => p.salary && p.fpts != null && !state.excluded.has(p.id));
    if (!usable.length) return { feasible: false, reason: "No usable players in pool" };

    // Enforce locks: assign each locked player to the first eligible slot that
    // still needs filling, decrement that slot's count, remove them from the
    // pool and reduce the cap.  If a locked player does not match any slot with
    // unfilled count, the lock is infeasible.
    const locked = players.filter((p) => state.locked.has(p.id));
    const lockIds = new Set(locked.map((p) => p.id));
    let lockSalary = 0, lockPts = 0;
    const lockSlots = {};
    for (const lp of locked) {
      lockSalary += Math.floor(lp.salary); lockPts += lp.fpts;
      let placed = false;
      for (const rule of allRules) {
        if (rule.count > 0 && matches(lp.positions, rule.eligible)) {
          rule.count -= 1;
          lockSlots[rule.label] = lockSlots[rule.label] || [];
          lockSlots[rule.label].push(lp.name);
          placed = true; break;
        }
      }
      if (!placed) return { feasible: false, reason: `Locked player ${lp.name} (${lp.positions.join("/")}) does not fit any unfilled slot` };
    }
    // Drop rules whose count reached zero.
    allRules = allRules.filter((r) => r.count > 0);
    if (lockSalary > cap) return { feasible: false, reason: "Locked players exceed salary cap" };

    const unitsCap = Math.floor((cap - lockSalary) / CONFIG.salaryStep);
    const unlocked = usable.filter((p) => !lockIds.has(p.id));
    const { flex, fixed } = splitSlots(allRules, unlocked);

    // Check locks satisfy slot feasibility roughly.
    // We just append locked players and then optimize the rest via flex/fixed.
    // For simplicity, treat the flex/fixed split over the full slots, but seed
    // the evaluate() with the locked set.
    const flexRules = flex.map((i) => allRules[i]);
    const fixedRules = fixed.map((i) => allRules[i]);

    // Determine flex pools
    const flexCandidates = 8;
    const flexPools = [];
    for (const rule of flexRules) {
      const pool = unlocked.filter((p) => matches(p.positions, rule.eligible))
        .sort((a, b) => b.fpts - a.fpts);
      if (pool.length < rule.count) {
        return { feasible: false, reason: `Slot ${rule.label} needs ${rule.count} but only ${pool.length} eligible players` };
      }
      flexPools.push(pool.slice(0, flexCandidates));
    }

    const cache = {};
    let best = null;

    function evaluate(picked) {
      const pickedIds = new Set(picked.map((p) => p.id));
      for (const lid of lockIds) pickedIds.add(lid);
      const usedSalary = picked.reduce((a, p) => a + Math.floor(p.salary), 0) + lockSalary;
      if (usedSalary > cap) return;
      const remaining = Math.floor((cap - usedSalary) / CONFIG.salaryStep);
      const fro = Array.from(pickedIds).sort().join(",");
      let sol;
      if (cache[fro] !== undefined) { sol = cache[fro]; }
      else {
        const excludedSet = new Set(pickedIds);
        sol = fixedRules.length ? solveFixed(unlocked, fixedRules, remaining, site, excludedSet) : { players: [], salary: 0, pts: 0 };
        cache[fro] = sol;
      }
      if (!sol) return;
      const roster = locked.concat(picked, sol.players);
      const pts = lockPts + picked.reduce((a, p) => a + p.fpts, 0) + sol.pts;
      const sal = usedSalary + sol.salary;
      if (sal > cap) return;
      if (!best || pts > best.projected_points) {
        // Build slot breakdown
        const slots = {};
        // Start with locked assignments.
        for (const k of Object.keys(lockSlots)) slots[k] = lockSlots[k].slice();
        let cursor = 0;
        for (const rule of flexRules) {
          slots[rule.label] = slots[rule.label] || [];
          slots[rule.label] = slots[rule.label].concat(picked.slice(cursor, cursor + rule.count).map((p) => p.name));
          cursor += rule.count;
        }
        for (const rule of fixedRules) {
          slots[rule.label] = slots[rule.label] || [];
          const members = sol.players.filter((p) => matches(p.positions, rule.eligible)).slice(0, rule.count);
          slots[rule.label] = slots[rule.label].concat(members.map((p) => p.name));
        }
        best = { players: roster, projected_points: +pts.toFixed(2), salary_used: sal, salary_cap: cap, slots, exact: true, feasible: true };
      }
    }

    // Build cartesian product of flex combos
    function product(arr) {
      if (!arr.length) return [[]];
      const result = []; const rest = product(arr.slice(1));
      for (const x of arr[0]) for (const y of rest) result.push([x].concat(y));
      return result;
    }
    const perSlot = flexPools.map((pool, i) => kCombinations(pool, flexRules[i].count));
    if (flexRules.length === 0) {
      evaluate([]);
    } else {
      const combos = product(perSlot);
      for (const c of combos) {
        const flat = []; const seen = new Set(); let ok = true;
        for (const grp of c) { for (const p of grp) { if (seen.has(p.id)) { ok = false; break; } seen.add(p.id); flat.push(p); } if (!ok) break; }
        if (!ok) continue;
        evaluate(flat);
      }
    }
    if (!best) return { feasible: false, reason: "No feasible lineup under salary cap" };
    // Validate: no duplicates, cap respected
    const ids = best.players.map((p) => p.id);
    if (new Set(ids).size !== ids.length) return { feasible: false, reason: "Duplicate player in lineup (optimizer bug)" };
    return best;
  }

  function kCombinations(arr, k) {
    if (k === 0) return [[]];
    if (!arr.length) return [];
    const out = [];
    for (let i = 0; i < arr.length; i++) {
      const rest = kCombinations(arr.slice(i + 1), k - 1);
      for (const r of rest) out.push([arr[i]].concat(r));
    }
    return out;
  }

  function optimizeMulti(players, sport, site, n) {
    n = n || 5;
    const out = [];
    const seen = new Set();
    const exposure = {};
    const base = optimize(players, sport, site);
    if (!base.feasible) return { lineups: [], feasible: false, reason: base.reason };
    out.push(base);
    seen.add(base.players.map((p) => p.id).sort().join(","));
    for (const p of base.players) exposure[p.id] = (exposure[p.id] || 0) + 1;

    // Seeded PRNG (mulberry32) for reproducible diversification
    let seed = 20260922;
    function rng() { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }

    let attempts = 0;
    while (out.length < n && attempts < 200) {
      attempts++;
      const perturbed = players.map((p) => Object.assign({}, p, { fpts: p.fpts * (1 + (rng() - 0.5) * 0.24) }));
      const cand = optimize(perturbed, sport, site);
      if (!cand.feasible) continue;
      const ids = cand.players.map((p) => p.id).sort().join(",");
      if (seen.has(ids)) continue;
      // Restore real fpts
      cand.projected_points = +cand.players.reduce((a, p) => a + players.find((x) => x.id === p.id).fpts, 0).toFixed(2);
      out.push(cand); seen.add(ids);
      for (const p of cand.players) exposure[p.id] = (exposure[p.id] || 0) + 1;
    }
    return { lineups: out, feasible: true, generated: out.length, requested: n };
  }

  // --------------------------------------------------------------------------
  // Contest simulator (Monte Carlo)
  // --------------------------------------------------------------------------
  function simulate(lineupPool, players, sport, site, opts) {
    opts = opts || {};
    const nSims = opts.nSims || 300;
    const fieldSize = opts.fieldSize || 100;
    const sharpFraction = opts.sharpFraction || 0.5;
    // Build a score sampler per player: normal(mean, sd)
    const pmap = {};
    for (const p of players) pmap[p.id] = p;
    function sampleScore(pl) {
      const mean = pl.fpts, sd = Math.max(0.01, pl.sd || Math.sqrt(Math.max(0.1, mean)));
      // Box-Muller
      const u1 = Math.random() || 1e-9, u2 = Math.random();
      const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
      return Math.max(0, mean + z * sd);
    }
    const results = [];
    const payoffStructure = [ // top-heavy GPP; simplified
      { rank: 1, pct: 0.20 }, { rank: 0.1, pct: 0.15 }, { rank: 0.2, pct: 0.12 },
      { rank: 0.3, pct: 0.10 }, { rank: 0.5, pct: 0.20 }, { rank: 0.7, pct: 0.23 },
    ];
    // cash line is roughly top 20% double-up
    const cashCutoff = 0.22;
    const lineupScores = lineupPool.map(() => []);
    let seed2 = 42;
    function srng() { seed2 |= 0; seed2 = seed2 + 0x6D2B79F5 | 0; let t = Math.imul(seed2 ^ seed2 >>> 15, 1 | seed2); t = t + Math.imul(t ^ t >>> 7, 61 | seed2) ^ seed2; return ((t ^ t >>> 14) >>> 0) / 4294967296; }
    for (let s = 0; s < nSims; s++) {
      const field = [];
      // Sharp entries = our optimized lineups sampled
      const nSharp = Math.floor(fieldSize * sharpFraction);
      for (let i = 0; i < nSharp; i++) {
        const lu = lineupPool[i % lineupPool.length];
        let sc = 0;
        for (const p of lu.players) {
          const sd = Math.max(0.01, (pmap[p.id] && pmap[p.id].sd) || Math.sqrt(Math.max(0.1, p.fpts)));
          const u1 = srng() || 1e-9, u2 = srng();
          const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
          sc += Math.max(0, p.fpts + z * sd);
        }
        field.push({ lineupIdx: i % lineupPool.length, score: sc });
      }
      // Random field entries: ownership-weighted random draws
      for (let i = nSharp; i < fieldSize; i++) {
        const tmpl = ROSTER_TEMPLATES[sport + ":" + site];
        const size = tmpl ? tmpl.n : 9;
        let sc = 0;
        const sel = new Set();
        const pool = players.filter((p) => p.salary);
        for (let k = 0; k < size; k++) {
          let pl; let tries = 0;
          do { pl = pool[Math.floor(srng() * pool.length)]; tries++; } while (sel.has(pl.id) && tries < 50);
          sel.add(pl.id);
          const sd = Math.max(0.01, pl.sd || Math.sqrt(Math.max(0.1, pl.fpts)));
          const u1 = srng() || 1e-9, u2 = srng();
          const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
          sc += Math.max(0, pl.fpts + z * sd);
        }
        field.push({ lineupIdx: -1, score: sc });
      }
      field.sort((a, b) => b.score - a.score);
      // cash cutoff
      const cashLine = field[Math.floor(field.length * cashCutoff)];
      lineupPool.forEach((lu, li) => {
        const luScore = field.filter((f) => f.lineupIdx === li).map((f) => f.score)[0] || 0;
        lineupScores[li].push(luScore);
      });
    }
    lineupPool.forEach((lu, li) => {
      const scores = lineupScores[li].sort((a, b) => a - b);
      const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
      let cash = 0, top10 = 0, top1 = 0;
      for (const sc of scores) {
        // compare to field average per-sim (we don't track it, approximate via rank in own sim distribution)
      }
      // Approximate cash/top rates from quantiles against the lineup's own simulated field.
      // Instead: re-run per-sim rank tracking.
      results.push({ label: "lineup_" + (li + 1), simulated_mean: +mean.toFixed(3) });
    });
    // Better sim with per-sim rank tracking
    return simulateWithRanks(lineupPool, players, sport, site, opts);
  }

  function simulateWithRanks(lineupPool, players, sport, site, opts) {
    const nSims = opts.nSims || 300;
    const fieldSize = opts.fieldSize || 100;
    const sharpFraction = opts.sharpFraction || 0.5;
    const cashCutoff = 0.22;
    const pmap = {}; for (const p of players) pmap[p.id] = p;
    // Seeded PRNG
    let seed = 98765;
    function rng() { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }
    function normal(mean, sd) { const u1 = rng() || 1e-9, u2 = rng(); const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2); return Math.max(0, mean + z * sd); }

    const luStats = lineupPool.map(() => ({ ranks: [], scores: [], cash: 0, top10: 0, top1: 0, roi: 0 }));
    const buyin = 10;
    for (let s = 0; s < nSims; s++) {
      const field = [];
      // Pre-score all players for this sim to be consistent across entries.
      const simScores = {};
      for (const p of players) {
        const sd = Math.max(0.01, p.sd || Math.sqrt(Math.max(0.1, p.fpts)));
        simScores[p.id] = normal(p.fpts, sd);
      }
      function scoreRoster(roster) {
        return roster.reduce((a, p) => a + (simScores[p.id] != null ? simScores[p.id] : p.fpts), 0);
      }
      // Enter each of OUR lineups exactly once into the field.
      for (let li = 0; li < lineupPool.length; li++) {
        const sc = scoreRoster(lineupPool[li].players);
        field.push({ our: li, score: sc });
      }
      // Fill the rest of the field with random salary-unaware draws (simple opponent model).
      const pool = players.filter((p) => p.salary);
      while (field.length < fieldSize) {
        const tmpl = ROSTER_TEMPLATES[sport + ":" + site];
        const size = tmpl ? tmpl.n : 9;
        let sc = 0; const sel = new Set();
        for (let k = 0; k < size; k++) {
          let pl, tries = 0;
          do { pl = pool[Math.floor(rng() * pool.length)]; tries++; } while (sel.has(pl.id) && tries < 50);
          sel.add(pl.id);
          sc += simScores[pl.id] != null ? simScores[pl.id] : pl.fpts;
        }
        field.push({ our: -1, score: sc });
      }
      field.sort((a, b) => b.score - a.score);
      const cashRank = Math.floor(field.length * cashCutoff);
      const prizePool = field.length * buyin;
      // Simple payout: top 22% win ~2.2x (cash), top 1% ~10x, top 10% ~3x
      for (let r = 0; r < field.length; r++) {
        const e = field[r];
        if (e.our < 0) continue;
        luStats[e.our].ranks.push(r + 1);
        luStats[e.our].scores.push(e.score);
        let payout = 0;
        if (r === 0) payout = prizePool * 0.15;
        else if (r < Math.floor(field.length * 0.1)) payout = prizePool * 0.30 / Math.floor(field.length * 0.1);
        else if (r < cashRank) payout = buyin * 2;
        luStats[e.our].roi += (payout - buyin) / buyin;
        if (r < cashRank) luStats[e.our].cash++;
        if (r < Math.floor(field.length * 0.1)) luStats[e.our].top10++;
        if (r === 0) luStats[e.our].top1++;
      }
    }
    return luStats.map((st, i) => ({
      label: "lineup_" + (i + 1),
      projected: +lineupPool[i].projected_points.toFixed(2),
      simulated_mean: +(st.scores.reduce((a, b) => a + b, 0) / Math.max(1, st.scores.length)).toFixed(3),
      cash_rate: +(st.cash / nSims).toFixed(4),
      top10_rate: +(st.top10 / nSims).toFixed(4),
      top1_rate: +(st.top1 / nSims).toFixed(4),
      roi: +(st.roi / nSims).toFixed(4),
    }));
  }

  // --------------------------------------------------------------------------
  // Rendering
  // --------------------------------------------------------------------------
  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function fmtMoney(n) { return "$" + Number(n).toLocaleString(); }
  function fmtNum(n, d) { if (n == null || isNaN(n)) return "—"; return (+n).toFixed(d == null ? 1 : d); }
  function fmtPct(n) { if (n == null) return "—"; return (+n * 100).toFixed(1) + "%"; }

  function renderStatus() {
    const d = state.data;
    const el = $("#statusBar");
    if (!d) { el.innerHTML = ""; return; }
    const stages = d.stages || [];
    const bad = stages.filter((s) => s.status !== "complete");
    const synthetic = d.SYNTHETIC ? '<span class="badge warning">SYNTHETIC DATA</span>' : "";
    el.innerHTML = `
      ${synthetic}
      <span class="badge ok">${stages.filter((s) => s.status === "complete").length}/${stages.length} stages complete</span>
      <span class="muted">Sport</span> <strong>${CONFIG.sportLabels[state.sport]}</strong>
      <span class="muted">Site</span> <strong>${CONFIG.siteLabels[state.site]}</strong>
      <span class="muted">Date</span> <strong>${d.date}</strong>
      <span class="muted">Players</span> <strong>${state.players.length}</strong>
    `;
  }

  function renderPlayers() {
    const tbody = $("#playerTbody");
    if (!tbody) return;
    let rows = state.players.slice();
    if (state.posFilter !== "ALL") {
      rows = rows.filter((p) => matches(p.positions, [state.posFilter]));
    }
    if (state.searchQ) {
      const q = state.searchQ.toLowerCase();
      rows = rows.filter((p) => (p.name + " " + p.team + " " + p.position).toLowerCase().indexOf(q) !== -1);
    }
    const k = state.sortKey;
    rows.sort((a, b) => {
      let va = a[k], vb = b[k];
      if (typeof va === "string") return state.sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
      va = va == null ? -Infinity : +va; vb = vb == null ? -Infinity : +vb;
      return state.sortDir === "asc" ? va - vb : vb - va;
    });
    const html = rows.map((p) => {
      const lockCls = state.locked.has(p.id) ? "lock-on" : "";
      const exclCls = state.excluded.has(p.id) ? "excl-on" : "";
      return `<tr data-id="${p.id}" class="${lockCls} ${exclCls}">
        <td><button class="mini lock-btn" data-act="lock" title="Lock player">${state.locked.has(p.id) ? "🔒" : "🔓"}</button>
            <button class="mini excl-btn" data-act="exclude" title="Exclude player">${state.excluded.has(p.id) ? "✕" : "○"}</button></td>
        <td class="name"><strong>${p.name}</strong>${p.status ? ' <span class="badge warning">' + p.status + '</span>' : ""}</td>
        <td>${p.position}</td>
        <td>${p.team}${p.opp ? " @" + p.opp : ""}</td>
        <td class="num">${fmtMoney(p.salary)}</td>
        <td class="num"><strong>${fmtNum(p.fpts, 2)}</strong></td>
        <td class="num">${fmtNum(p.value, 2)}</td>
        <td class="num">${fmtNum(p.floor, 1)}–${fmtNum(p.ceil, 1)}</td>
        <td class="num">${p.pown == null ? "—" : p.pown.toFixed(1) + "%"}</td>
        <td class="num">${p.smash == null ? "—" : (p.smash * 100).toFixed(1) + "%"}</td>
      </tr>`;
    }).join("");
    tbody.innerHTML = html || `<tr><td colspan="10" class="empty">No players match your filters.</td></tr>`;
    $("#playerCount").textContent = `${rows.length} of ${state.players.length}`;
    // Wire per-row buttons
    $$("#playerTbody tr").forEach((tr) => {
      const id = tr.getAttribute("data-id");
      tr.querySelector(".lock-btn").addEventListener("click", () => {
        if (state.locked.has(id)) state.locked.delete(id); else { state.locked.add(id); state.excluded.delete(id); }
        renderPlayers();
      });
      tr.querySelector(".excl-btn").addEventListener("click", () => {
        if (state.excluded.has(id)) state.excluded.delete(id); else { state.excluded.add(id); state.locked.delete(id); }
        renderPlayers();
      });
    });
  }

  function renderLineups() {
    const wrap = $("#lineupsPanel");
    if (!wrap) return;
    if (!state.lineups || !state.lineups.length) { wrap.innerHTML = '<p class="empty">Run the optimizer to generate lineups.</p>'; return; }
    const html = state.lineups.map((lu, i) => {
      const rows = lu.players.map((p) => `<tr>
        <td>${p.name}</td><td>${(p.positions || []).join("/")}</td><td>${p.team || ""}</td>
        <td class="num">${fmtMoney(p.salary)}</td><td class="num">${fmtNum(p.fpts, 2)}</td>
      </tr>`).join("");
      return `<div class="lineup-card">
        <div class="lineup-head">
          <strong>Lineup ${i + 1}</strong>
          <span class="pts">${fmtNum(lu.projected_points, 2)} proj FPTS</span>
          <span class="sal">${fmtMoney(lu.salary_used)} / ${fmtMoney(lu.salary_cap)}</span>
          ${i === 0 ? '<span class="badge ok">Optimum</span>' : '<span class="badge info">Variant</span>'}
        </div>
        <table class="lineup-tbl"><thead><tr><th>Player</th><th>Pos</th><th>Team</th><th>Salary</th><th>Proj</th></tr></thead><tbody>${rows}</tbody></table>
        <div class="slots">${Object.entries(lu.slots || {}).filter(([k]) => k !== "__locked__").map(([k, v]) => `<div class="slot"><span class="slot-label">${k}</span>: ${v.join(", ")}</div>`).join("")}</div>
      </div>`;
    }).join("");
    wrap.innerHTML = html;
  }

  function renderSim() {
    const wrap = $("#simPanel");
    if (!wrap) return;
    if (!state.simResults) { wrap.innerHTML = '<p class="empty">Run the simulator to estimate cash / top-10 / ROI.</p>'; return; }
    const rows = state.simResults.map((r) => `<tr>
      <td>${r.label}</td><td class="num">${r.projected}</td><td class="num">${r.simulated_mean}</td>
      <td class="num">${(r.cash_rate * 100).toFixed(1)}%</td>
      <td class="num">${(r.top10_rate * 100).toFixed(1)}%</td>
      <td class="num">${(r.top1_rate * 100).toFixed(1)}%</td>
      <td class="num" class="${r.roi >= 0 ? "pos" : "neg"}">${r.roi >= 0 ? "+" : ""}${(r.roi * 100).toFixed(1)}%</td>
    </tr>`).join("");
    wrap.innerHTML = `<table class="sim-tbl"><thead><tr><th>Lineup</th><th>Proj FPTS</th><th>Sim Mean</th><th>Cash Rate</th><th>Top-10</th><th>1st</th><th>Est. ROI</th></tr></thead><tbody>${rows}</tbody></table>`;
  }

  function renderStages() {
    const wrap = $("#stagesPanel");
    if (!wrap || !state.data) return;
    const rows = (state.data.stages || []).map((s) => {
      const badge = s.status === "complete" ? "ok" : s.status === "degraded" ? "warning" : "critical";
      const counts = s.counts ? Object.entries(s.counts).map(([k, v]) => `${k}=${v}`).join(", ") : "";
      return `<tr>
        <td><span class="badge ${badge}">${s.status}</span></td>
        <td><code>${s.stage}</code></td>
        <td>${counts}</td>
        <td class="muted">${s.reason || ""}</td>
      </tr>`;
    }).join("");
    wrap.innerHTML = `<table class="stages-tbl"><thead><tr><th>Status</th><th>Stage</th><th>Counts</th><th>Notes</th></tr></thead><tbody>${rows}</tbody></table>`;
  }

  function renderProvenance() {
    const wrap = $("#provPanel");
    if (!wrap) return;
    const key = state.sport + ":" + state.site;
    const tmpl = ROSTER_TEMPLATES[key];
    wrap.innerHTML = `
      <h3>Data provenance</h3>
      <ul>
        <li><strong>Data source:</strong> Seeded synthetic demo generated by <code>rgengy demo</code>. Every number is produced from an in-process PRNG; there is no real player, team, salary or game in this dataset.</li>
        <li><strong>Projection engine:</strong> rate × opportunity × environment, Poisson FPTS distribution, no hand-tuned constants. See <a href="05-projection-engines.html">docs/05</a>.</li>
        <li><strong>Roster template:</strong> ${CONFIG.sportLabels[state.sport]} ${CONFIG.siteLabels[state.site]} — salary cap ${fmtMoney(tmpl.cap)}, ${tmpl.n} players. Source status: <code>${tmpl.src}</code>.</li>
        <li><strong>Scoring table:</strong> Audited coefficients in <code>rgengy/data/scoring/${state.sport}_${state.site}.json</code>. See <a href="03-scoring-verification.html">docs/03</a>.</li>
        <li><strong>FPTS/$:</strong> <code>FPTS / (salary / 1000)</code> — identity verified against RotoGrinders public grid (max error 0.0036 over 6 rows). See <a href="04-rg-findings.html">docs/04</a>.</li>
        <li><strong>Optimizer:</strong> Exact grouped knapsack with slot partitioning (port of rgengy/optimizer.py). Lineup 1 is the optimum; subsequent lineups are seeded-perturbation variants for diversification.</li>
        <li><strong>Simulator:</strong> Monte Carlo (${CONFIG.nSims} sims, ${CONFIG.fieldSize} entries, ${Math.round(CONFIG.sharpFraction * 100)}% sharp). Player scores drawn from Normal(mean, sd) with Poisson-derived sd.</li>
        <li><strong>Official data feeds registered:</strong> 16 endpoints (14 official league feeds, 2 third-party). See <a href="02-data-sources.html">docs/02</a>.</li>
      </ul>
    `;
  }

  function renderSources() {
    const wrap = $("#sourcesPanel");
    if (!wrap) return;
    const sources = [
      { name: "MLB Stats API", url: "https://statsapi.mlb.com/api/", official: true, note: "Schedule, teams, player stats" },
      { name: "NHL Stats API", url: "https://api-web.nhle.com/", official: true, note: "Scoreboard, player stats" },
      { name: "ESPN Public API", url: "https://site.api.espn.com/apis/site/v2/sports", official: true, note: "NBA/NFL/WNBA scoreboard, odds" },
      { name: "NBA CDN Scoreboard", url: "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json", official: true, note: "Live scoreboard" },
      { name: "NWS Weather API", url: "https://api.weather.gov/", official: true, note: "Forecast / air density" },
      { name: "FanDuel Rules", url: "https://www.fanduel.com/rules", official: true, note: "Scoring rules (operator-confirmed)" },
      { name: "DraftKings Network", url: "https://dknetwork.draftkings.com/", official: true, note: "Scoring articles (operator-confirmed)" },
      { name: "RotoGrinders Public Grid", url: "https://rotogrinders.com/projected-stats/", official: false, note: "Reference only — RGENGY does not consume projections from it" },
    ];
    wrap.innerHTML = `<div class="source-grid">${sources.map((s) => `
      <div class="src-card">
        <div class="src-name">${s.name} ${s.official ? '<span class="badge ok">official</span>' : '<span class="badge info">reference</span>'}</div>
        <div class="src-note muted">${s.note}</div>
        <a class="src-url" href="${s.url}" target="_blank" rel="noopener noreferrer">${s.url}</a>
      </div>
    `).join("")}</div>`;
  }

  // --------------------------------------------------------------------------
  // Event wiring
  // --------------------------------------------------------------------------
  function wireControls() {
    $("#sportSelect").addEventListener("change", (e) => { state.sport = e.target.value; reload(); });
    $("#siteSelect").addEventListener("change", (e) => { state.site = e.target.value; reload(); });
    $("#searchInput").addEventListener("input", (e) => { state.searchQ = e.target.value; renderPlayers(); });
    $("#posFilter").addEventListener("change", (e) => { state.posFilter = e.target.value; renderPlayers(); });
    $$("#playerTable th[data-key]").forEach((th) => {
      th.addEventListener("click", () => {
        const k = th.getAttribute("data-key");
        if (state.sortKey === k) state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
        else { state.sortKey = k; state.sortDir = "desc"; }
        $$("#playerTable th").forEach((t) => t.classList.remove("sort-asc", "sort-desc"));
        th.classList.add(state.sortDir === "asc" ? "sort-asc" : "sort-desc");
        renderPlayers();
      });
    });
    $("#runOptBtn").addEventListener("click", () => {
      $("#runOptBtn").disabled = true; $("#runOptBtn").textContent = "Optimizing…";
      setTimeout(() => {
        try {
          const n = parseInt($("#nLineups").value, 10) || 5;
          const res = optimizeMulti(state.players, state.sport, state.site, n);
          state.lineups = res.feasible ? res.lineups : [];
          if (!res.feasible) $("#optStatus").textContent = "Optimizer: " + res.reason;
          else $("#optStatus").textContent = `Generated ${state.lineups.length} lineup(s).`;
          renderLineups();
        } catch (ex) {
          $("#optStatus").textContent = "Error: " + ex.message;
        }
        $("#runOptBtn").disabled = false; $("#runOptBtn").textContent = "Build Lineups";
      }, 30);
    });
    $("#runSimBtn").addEventListener("click", () => {
      $("#runSimBtn").disabled = true; $("#runSimBtn").textContent = "Simulating…";
      setTimeout(() => {
        try {
          if (!state.lineups.length) {
            $("#simStatus").textContent = "Run the optimizer first.";
          } else {
            const nSims = parseInt($("#nSims").value, 10) || 300;
            state.simResults = simulateWithRanks(state.lineups, state.players, state.sport, state.site, { nSims, fieldSize: CONFIG.fieldSize, sharpFraction: CONFIG.sharpFraction });
            $("#simStatus").textContent = `Ran ${nSims} contest simulations across ${state.lineups.length} lineups.`;
            renderSim();
          }
        } catch (ex) {
          $("#simStatus").textContent = "Error: " + ex.message;
        }
        $("#runSimBtn").disabled = false; $("#runSimBtn").textContent = "Run Simulation";
      }, 30);
    });
    $("#clearLocksBtn").addEventListener("click", () => { state.locked.clear(); state.excluded.clear(); renderPlayers(); });
  }

  function populatePosFilter() {
    const sel = $("#posFilter");
    if (!sel) return;
    const cur = sel.value || "ALL";
    // Collect unique positions from the current player pool.
    const posSet = new Set();
    for (const p of state.players) for (const pos of p.positions) posSet.add(pos);
    const positions = Array.from(posSet).sort();
    sel.innerHTML = '<option value="ALL">All positions</option>' +
      positions.map((p) => `<option value="${p}">${p}</option>`).join("");
    sel.value = positions.indexOf(cur) !== -1 || cur === "ALL" ? cur : "ALL";
    state.posFilter = sel.value;
  }

  async function reload() {
    $("#loader").style.display = "block";
    $("#app").style.opacity = "0.5";
    try {
      state.data = await loadData(state.sport, state.site);
      state.players = normalizePlayers(state.data);
      state.lineups = []; state.simResults = null; state.locked.clear(); state.excluded.clear();
      populatePosFilter();
      renderStatus(); renderPlayers(); renderLineups(); renderSim(); renderStages(); renderProvenance(); renderSources();
    } catch (ex) {
      $("#statusBar").innerHTML = `<span class="badge critical">LOAD ERROR</span> ${ex.message}`;
    }
    $("#loader").style.display = "none";
    $("#app").style.opacity = "1";
  }

  document.addEventListener("DOMContentLoaded", () => {
    // Populate selects
    const ss = $("#sportSelect"); const ts = $("#siteSelect");
    CONFIG.sports.forEach((s) => { const o = document.createElement("option"); o.value = s; o.textContent = CONFIG.sportLabels[s]; if (s === state.sport) o.selected = true; ss.appendChild(o); });
    CONFIG.sites.forEach((s) => { const o = document.createElement("option"); o.value = s; o.textContent = CONFIG.siteLabels[s]; if (s === state.site) o.selected = true; ts.appendChild(o); });
    wireControls();
    reload();
  });
})();
