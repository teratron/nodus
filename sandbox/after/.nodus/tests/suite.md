# SDD Cognitive Test Suite
;; Format:  T{N} — {Title} (H3), required fields: Input, Expected, Mock, Tags
;; Runtime: sdd.simulate test
;; Note:    T01–T162 from sandbox/before/tests/suite.md are not yet ported.
;;          This stub satisfies FILE_EXISTS() in sdd.simulate.test_suite.
;;          Port remaining tests before relying on this suite for full regression coverage.

---

### T001 — Analyze ventilate with empty arg routes to Mode C

**Input:** `sdd analyze` (no args, workspace = null)
**Expected:** status = SUCCESS, out.mode = "C", Advisory Report appended
**Mock:**
- ENGINE_PREFLIGHT: { ok: true }
- RESOLVE_WORKSPACE: "main"
- ANALYZE: { mode: "ventilate" }
- SCAN_DIR (depth=1): [{ name: "src" }, { name: "tests" }] — count = 2
- CHECK_PREREQS: { ok: true }
- PARSE_INDEX: { specs: [{ name: "core", file: "core.md", status: "Stable" }] }
**Tags:** smoke, analyze, mode_c

---

### T002 — Analyze depth control halts on >500 files

**Input:** `sdd analyze` (no args)
**Expected:** status = ABORTED, flags CONTAINS "DEPTH_LIMIT"
**Mock:**
- ENGINE_PREFLIGHT: { ok: true }
- RESOLVE_WORKSPACE: "main"
- ANALYZE: { mode: "ventilate" }
- SCAN_DIR (depth=1): { count: 601 }
**Tags:** guard, analyze, depth_control

---

### T003 — Analyze depth control 50–500: awaits user choice

**Input:** `sdd analyze` (no args), user responds "focused"
**Expected:** status = SUCCESS, out.mode = "D"
**Mock:**
- ENGINE_PREFLIGHT: { ok: true }
- RESOLVE_WORKSPACE: "main"
- ANALYZE: { mode: "ventilate" }
- SCAN_DIR (depth=1): { count: 120 }
- AWAIT: "focused"
**Tags:** guard, analyze, depth_control, await

---

### T004 — Simulate pre-flight integrity halts all modes

**Input:** `sdd simulate test`
**Expected:** status = ABORTED, errors CONTAINS "SDD:ENGINE_INTEGRITY"
**Mock:**
- CHECK_PREREQS: { ok: false, warnings: ["ENGINE_INTEGRITY"] }
**Tags:** guard, simulate, preflight

---

### T005 — Simulate test mode falls back to improv when suite missing

**Input:** `sdd simulate test`
**Expected:** status = SUCCESS, out.mode = "improv"
**Mock:**
- CHECK_PREREQS: { ok: true }
- RESOLVE_WORKSPACE: "main"
- ANALYZE: { mode: "test" }
- FILE_EXISTS(".nodus/tests/suite.md"): false
**Tags:** smoke, simulate, fallback

---

;; TODO: Port T006–T162 from sandbox/before/tests/suite.md
;; Priority areas: T4-queuing, C12 recursive depth, cross-workspace parity
