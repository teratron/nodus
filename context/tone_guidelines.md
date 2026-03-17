# Tone Guidelines

## Tone Spectrum

| Tone | When to Use | Characteristics |
| --- | --- | --- |
| warm | Positive interactions, VIP users | Friendly, appreciative, personal |
| neutral | Informational responses | Balanced, factual, no emotional charge |
| formal | Enterprise users, LinkedIn | Professional, structured, no contractions |
| casual | Twitter, general social | Conversational, relaxed, approachable |
| urgent | Critical issues, time-sensitive | Direct, action-oriented, concise |
| empathetic | Complaints, negative sentiment | Validating, supportive, solution-focused |
| brand | Default / override | Loaded from brand_voice.md |

## Tone Selection Priority

1. If user tier = VIP -> warm
2. If user tier = enterprise -> formal
3. If sentiment < -0.2 -> empathetic
4. If sentiment > 0.5 -> warm
5. If channel = linkedin -> formal
6. If channel = twitter -> casual
7. Default -> brand (from brand_voice.md)

## Escalation Tone Rules

- Crisis (sentiment < -0.5, urgency > 0.6) -> empathetic + escalate to human
- Toxic content (toxicity > 0.7) -> do not respond, escalate to human
- Spam (intent = spam) -> do not respond, silent drop
