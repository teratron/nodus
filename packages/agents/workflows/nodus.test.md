---
description: Run @test blocks in a .nodus workflow and explain the results.
---

# /nodus.test

Execute inline tests from a NODUS workflow and provide clear results.

## Steps

// turbo

1. **Check CLI availability** — run `nodus --version`. If the command is not found, stop and tell the user: "The `nodus` CLI is not installed. Run `pip install nodus` and try again."

2. **Identify the target.** If user has a `.nodus` file open, use it. Otherwise ask. Optionally accept a `--tag` filter (e.g. `smoke`).

// turbo
3. **Validate first** — run `nodus validate <file>`. If errors exist, report them and stop. Tests require a valid workflow.

// turbo
4. **Run tests** — execute `nodus test <file>` (or `nodus test <file> --tag=<tag>` if filtered).

5. **Parse and present results.** For each test:

   - ✅ **PASS** — test name, tags, what was tested
   - ❌ **FAIL** — test name, expected vs actual, likely cause
   - ⚠️ **ERROR** — test name, exception details

6. **For failed tests**, provide actionable guidance:

   - What the test expected (`@expect:`)
   - What the workflow actually produced
   - Which step likely caused the failure
   - Suggested fix

7. **Show summary:**

   ```
   Tests: 3 passed, 1 failed, 0 errors
   Tags:  smoke (2), happy_path (1), edge_case (1)
   ```

8. **Offer next actions:**
   - "Fix the failing test?" → identify the issue and suggest a code change
   - "Add more tests?" → scaffold a new `@test:` block
   - "Run with real data?" → suggest `nodus run <file>`
