# NODUS Workflow Patterns

Reusable patterns for common workflow architectures.

## Pattern 1: Fetch → Analyze → Gate → Generate → Validate → Publish

The standard content-response pipeline. Used for social media replies, customer support, etc.

```nodus
§wf:social_reply v1.0
§runtime: { core: .nodus/core/schema.nodus, mode: production }

@ON: new_mention
@in: { post_url: url, tone?: str = neutral }
@ctx: [brand_voice]
@out: $reply
@err: ESCALATE(human)

!!NEVER: publish WITHOUT validate
!PREF: tone = brand_voice OVER tone = $in.tone

@steps:
  1. FETCH($in.post_url) +timeout=10          → $raw
  2. ANALYZE($raw) ~sentiment ~intent ~toxicity → $meta

  ;; — Gate: filter unwanted content —
  3. ?IF $meta.intent = spam     → !BREAK
     ?IF $meta.toxicity > 0.7   → ESCALATE(human) !BREAK

  ;; — Generate and validate —
  4. GEN(reply) +tone=$in.tone +ctx=$meta      → $draft
  5. VALIDATE($draft) ^brand_voice ^no_toxic ^len:280
  6. PUBLISH($draft)
  7. LOG($draft)
```

## Pattern 2: Quality Refinement Loop

Iteratively improve output until a quality threshold is met.

```nodus
§wf:polished_article v1.0
§runtime: { core: .nodus/core/schema.nodus, mode: production }

@ON: article_request
@in: { topic: str, max_words?: int = 500 }
@out: $article
@err: ESCALATE(human)

!!ALWAYS: log($out)

@steps:
  1. GEN(article) +topic=$in.topic +max_len=$in.max_words → $draft
  2. SCORE($draft) → $quality

  ~UNTIL $quality > 0.85 | MAX:3:
    3. REFINE($draft) +focus=clarity → $draft
    4. SCORE($draft) → $quality
  ~END

  5. VALIDATE($draft) ^brand_voice ^no_pii
  6. LOG($draft)
```

## Pattern 3: Parallel Analysis → Merge → Route

Run multiple analysis tasks concurrently, then make a routing decision.

```nodus
§wf:smart_triage v1.0
§runtime: { core: .nodus/core/schema.nodus, mode: production }

@ON: incoming_ticket
@in: { ticket_text: str }
@out: $result
@err: ESCALATE(human)

@steps:
  ~PARALLEL:
    1. ANALYZE($in.ticket_text) ~sentiment  → $sentiment
    2. ANALYZE($in.ticket_text) ~intent     → $intent
    3. ANALYZE($in.ticket_text) ~urgency    → $urgency
  ~JOIN → $signals

  4. ?IF $signals.urgency > 0.9:
       ROUTE(wf:urgent_handler) !BREAK
     ?ELIF $signals.sentiment < -0.5:
       ROUTE(wf:escalation) !BREAK
     ?ELSE:
       GEN(reply) +tone=neutral +ctx=$signals → $result

  5. LOG($result)
```

## Pattern 4: Batch Processing

Iterate over a collection, process each item, collect results.

```nodus
§wf:batch_translate v1.0
§runtime: { core: .nodus/core/schema.nodus, mode: production }

@ON: translate_batch
@in: { items: list, target_lang: str }
@out: $results
@err: ESCALATE(human)

!!ALWAYS: log($out)

@steps:
  ~FOR $item IN $in.items:
    1. TRANSLATE($item.text) +lang=$in.target_lang → $translated
    2. VALIDATE($translated) ^len:500
    3. APPEND($translated → $results)
  ~END

  4. LOG($results)
```

## Pattern 5: Context-Enriched Decision Chain

Load context, enrich input data, then make a multi-step decision.

```nodus
§wf:review_handler v1.0
§runtime: {
  core:    .nodus/core/schema.nodus
  extends: [.nodus/schema/brand_voice.nodus]
  mode:    production
}

@ON: new_review
@in: { review_url: url }
@ctx: [brand_voice, response_guidelines]
@out: $response
@err: ESCALATE(human)

!!NEVER: publish WITHOUT validate
!!NEVER: respond to review IF toxicity > 0.8
!PREF: empathetic OVER neutral IF sentiment < 0

@steps:
  1. FETCH($in.review_url) → $raw
  2. ANALYZE($raw) ~sentiment ~intent ~entities → $meta
  3. QUERY_KB($meta.entities) → $kb

  4. ?IF $meta.sentiment > 0.5:
       TONE(warm)
       GEN(thank_you) +ctx=$kb → $response
     ?ELIF $meta.sentiment > 0:
       TONE(neutral)
       GEN(acknowledgement) +ctx=$kb → $response
     ?ELSE:
       TONE(empathetic)
       GEN(apology) +ctx=$kb +ctx=$meta → $response

  5. VALIDATE($response) ^brand_voice ^no_pii ^len:500
  6. REMEMBER("last_review", $meta)
  7. PUBLISH($response)
  8. LOG($response)
```

## Pattern 6: Macro-Based Composition

Extract reusable logic into macros for DRY workflows.

```nodus
§wf:multi_channel v1.0
§runtime: { core: .nodus/core/schema.nodus, mode: production }

@ON: content_ready
@in: { content: str }
@out: $published
@err: ESCALATE(human)

@macro:FORMAT_AND_VALIDATE
  1. REFINE($draft) +focus=clarity → $draft
  2. VALIDATE($draft) ^brand_voice ^no_toxic → $validated
@end

@steps:
  ;; — Twitter version —
  1. SUMMARIZE($in.content) +max_len=280 → $draft
  2. RUN(@macro:FORMAT_AND_VALIDATE) → $tweet
  3. PUBLISH($tweet) +channel=twitter

  ;; — LinkedIn version —
  4. REFINE($in.content) +focus=professional +max_len=1500 → $draft
  5. RUN(@macro:FORMAT_AND_VALIDATE) → $post
  6. PUBLISH($post) +channel=linkedin

  7. LOG($published)
```

## Anti-Patterns to Avoid

| ❌ Don't | ✅ Do |
| :--- | :--- |
| `PUBLISH()` without `VALIDATE()` | Always validate before publish |
| `~UNTIL` without `MAX:n` | Always set a maximum iteration count |
| `~FOR` / `~UNTIL` without `~END` | Always close loop blocks |
| `~PARALLEL` without `~JOIN` | Always join parallel branches |
| Variables used before assignment | Assign via `→` before referencing |
| `§wf:name` doesn't match filename | Keep them in sync (E012) |
| `!!` rules after `@steps:` | Place rules before steps (E003) |
