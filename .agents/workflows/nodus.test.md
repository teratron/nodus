---
description: Run @test blocks in a .nodus workflow and explain the results.
---

# /nodus.test

Execute inline tests from a NODUS workflow and provide clear results.

## Steps

1. **Identify the target.** If user has a `.nodus` file open, use it. Otherwise ask. Optionally accept a `--tag` filter (e.g. `smoke`).

// turbo
2. **Validate first** — run `nodus validate <file>`. If errors exist, report them and stop. Tests require a valid workflow.

// turbo
3. **Run tests** — execute `nodus test <file>` (or `nodus test <file> --tag=<tag>` if filtered).

4. **Parse and present results.** For each test:
   - ✅ **PASS** — test name, tags, what was tested
   - ❌ **FAIL** — test name, expected vs actual, likely cause
   - ⚠️ **ERROR** — test name, exception details

5. **For failed tests**, provide actionable guidance:
   - What the test expected (`@expect:`)
   - What the workflow actually produced
   - Which step likely caused the failure
   - Suggested fix

6. **Show summary:**
   ```
   Tests: 3 passed, 1 failed, 0 errors
   Tags:  smoke (2), happy_path (1), edge_case (1)
   ```

7. **Offer next actions:**
   - "Fix the failing test?" → identify the issue and suggest a code change
   - "Add more tests?" → scaffold a new `@test:` block
   - "Run with real data?" → suggest `nodus run <file>`
