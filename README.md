# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

Provenance Guard is a local backend service that evaluates writing using two
different signals. Its scores describe patterns in the writing, not proof of
who wrote it.

A submission follows these steps:

1. A writer sends `text` and `creator_id` to `POST /submit`.
2. The service checks the input and creates a unique `content_id`. Text must
   contain between 50 and 10,000 characters after surrounding whitespace is
   removed. The creator ID must be a nonempty string.
3. A local GPT-2 model measures how predictable the writing is.
4. The style signal measures sentence length variation, vocabulary repetition,
   and selected punctuation density.
5. The combining function averages the two signal scores.
6. The label function maps the combined score to a human, AI, or unsure label.
7. The service records the decision in the audit log and returns the ID,
   scores, guess, and label.

Writers can send their `content_id` and reasoning to `POST /appeal`.
The explanation must contain at least 25 whitespace-separated words.
The service checks that the submission exists, records the appeal, and
marks it `under_review`. It does not automatically rescore the writing.

Repeating the same explanation for the same submission does not add another
appeal entry. Duplicate checking ignores capitalization and extra whitespace.
A different explanation meeting the minimum length is saved.

The audit log preserves the original decision. An appeal adds a later entry
with the `under_review` status rather than overwriting the decision.

---

## Signals and Scoring

### Signal one — the model signal

**What it measures:**

`detector.model_signal(text)` uses the local GPT-2 model to measure how
predictable the text is. It converts that measurement into a score from
0 to 1. Higher scores mean more AI-like according to this signal.

**Why that might differ between human and AI writing:**

AI-generated writing can contain common phrases and predictable word
sequences. A language model may find those patterns easier to predict.

**What it can't see:**

Predictability does not establish authorship. Human writing can also use
common phrases, simple vocabulary, or repeated sentence patterns. Unusual
AI-generated writing can receive a lower score.

The model processes up to the configured limit of 400 tokens, so it does not
necessarily evaluate the entire passage.

### Signal two — the style signal

**What it measures:**

`stylometry.style_signal(text)` combines three measurements:

- Sentence length spread: the sample standard deviation of sentence word
  counts divided by their mean.
- Type-token ratio: unique lowercase words divided by total words.
- Punctuation density: selected punctuation marks divided by non-whitespace
  characters.

The component calculations are:

```text
sentence component = 1 - min(sentence_length_spread, 1)
repetition component = 1 - type_token_ratio
punctuation component = 1 - min(punctuation_density / 0.05, 1)

style_score = (0.50 × sentence component)
            + (0.30 × repetition component)
            + (0.20 × punctuation component)
```

Selected punctuation includes commas, semicolons, colons, question marks,
exclamation marks, dashes, parentheses, and square brackets. Full stops and
apostrophes are excluded.

The score is rounded to four decimal places. Text with fewer than 20 words
or fewer than two nonempty sentences receives a neutral score of 0.5.

These weights and the punctuation scale are experimental choices rather
than values established through validation.

**Why that might differ between human and AI writing:**

Generated writing may have consistent sentence lengths and repeated wording.
The style signal treats those patterns as more AI-like. These are assumptions
that need testing rather than reliable rules about authorship.

**What it can't see:**

This signal cannot understand meaning or verify who wrote the text. Changing
punctuation, splitting sentences, or adding typos can affect its score without
changing the main content.

Vocabulary repetition also increases with passage length, so passages of
different lengths are not directly comparable. Human writing can have all
the patterns this signal treats as AI-like.

### The combining rule

**The rule:**

I kept the starter's equally weighted average. Both signals point in the
same direction, so higher combined scores mean more AI-like writing.

When the signals disagree, the combined score falls between them.
Disagreement does not guarantee an unsure label because the average can
still fall outside the unsure range.

The response calls this combined score `confidence`. It is not a calibrated
probability of AI authorship.

**The numbers:**

```text
combined_score = (0.50 × model_score) + (0.50 × style_score)
```

The label thresholds are:

- Human: combined score at or below 0.35.
- Unsure: combined score above 0.35 and below 0.65.
- AI: combined score at or above 0.65.

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:**

I ran both signals separately on four calibration passages:

| Passage | Model score | Style score | 50/50 combined score |
|---|---:|---:|---:|
| My human-written film paragraph | 0.6155 | 0.7230 | 0.66925 |
| Original AI garden passage | 0.6927 | 0.5389 | 0.61580 |
| Edited AI garden passage | 0.8587 | 0.6319 | 0.74530 |
| Plain human-written morning paragraph | 0.8582 | 0.6908 | 0.77450 |

The combined scores in this table are calculated from the standalone results.
I later confirmed the original garden and morning paragraph scores through
the completed endpoint.

The model ranked the original AI passage above my human film paragraph,
while the style signal ranked them in the opposite order. My film paragraph
had low sentence length variation and repeated vocabulary, which increased
its style score.

With equal weights and the starter thresholds, my human film paragraph
would receive an AI label. The original AI passage receives an unsure label.
This shows how the style signal can push a human submission above the AI
threshold.

My plain human-written morning paragraph also received an AI label when
submitted through the endpoint. The model found its wording predictable,
while the style signal measured very similar sentence lengths. Both signals
leaned toward AI, so averaging them did not prevent a false positive.

The edited garden passage received a higher model score than the original.
Editing does not necessarily reduce predictability. The passages also differ
in length, so these examples do not isolate editing as the cause.

These calibration examples show a risk to my zero-false-positive target.
They are not the full acceptance test results.

---

## Label Variants

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 ≤ score ≤ 0.35 | Our automated checks suggest this writing was written by a person. These checks cannot verify authorship. |
| unsure | 0.35 < score < 0.65 | Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision. |
| high-confidence AI | 0.65 ≤ score ≤ 1.00 | Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision. |

**Why I worded the "unsure" one this way:**

The label explains that the checks could not reach a confident conclusion.
It also says the result is not a finding of wrongdoing because uncertainty
should not become an accusation. The appeal sentence gives the writer a
way to challenge the result.

All three labels were reached through actual submissions:

| Submission | Combined score | Returned guess | Content ID |
|---|---:|---|---|
| Short test submission | 0.28125 | human | 53b1d580-3041-4e4b-a80c-266c38268e36 |
| Original AI garden passage | 0.6158 | unsure | 1deabba6-27f3-4048-8e3c-090e755161a6 |
| Human-written morning paragraph | 0.7745 | ai | b2f4fb71-e51f-4c26-9680-a2ad7989d6a0 |

The AI label on my morning paragraph is a false positive. This table
demonstrates label coverage, not accurate authorship detection.

---

## Sample Run

**A submission**

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test submission to check that both signals return scores and the service combines them correctly.", "creator_id": "arely"}'
```

```json
{
  "confidence": 0.28125,
  "content_id": "53b1d580-3041-4e4b-a80c-266c38268e36",
  "guess": "human",
  "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
  "model_score": 0.0625,
  "style_score": 0.5
}
```

The average is `(0.0625 + 0.5) / 2 = 0.28125`. This sample has only one
sentence, so the style signal returns its neutral fallback of 0.5.

**An appeal**

This appeal tests the endpoint behavior. The original submission received a
human label; the appeal is not an example of correcting an AI accusation.

```bash
$ curl -i -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "53b1d580-3041-4e4b-a80c-266c38268e36", "reasoning": "This is a test appeal to verify that the service records a detailed explanation, links it to my submission, and marks the item for review without automatically rescoring it."}'
```

HTTP status: `200 OK`

```json
{
  "content_id": "53b1d580-3041-4e4b-a80c-266c38268e36",
  "duplicate": false,
  "message": "Your appeal has been recorded for review. The writing has not been automatically rescored.",
  "status": "under_review"
}
```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log?limit=2"
```

```json
{
  "count": 2,
  "entries": [
    {
      "combined_score": 0.28125,
      "content_id": "53b1d580-3041-4e4b-a80c-266c38268e36",
      "creator_id": "arely",
      "guess": "human",
      "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
      "model_score": 0.0625,
      "status": "decided",
      "style_score": 0.5,
      "timestamp": "2026-11-16T06:42:59+00:00"
    },
    {
      "content_id": "53b1d580-3041-4e4b-a80c-266c38268e36",
      "creator_id": "arely",
      "event": "appeal",
      "reasoning": "This is a test appeal to verify that the service records a detailed explanation, links it to my submission, and marks the item for review without automatically rescoring it.",
      "status": "under_review",
      "timestamp": "2026-11-16T06:44:19+00:00"
    }
  ]
}
```

Additional appeal checks produced these results:

| Check | Observed result |
|---|---|
| Repeat the same explanation for the same content ID | HTTP 200, `duplicate: true`; no additional appeal entry in the checked history |
| Submit an explanation shorter than 25 words | HTTP 400, `reasoning_too_short` |
| Submit a different explanation of at least 25 words for the same content ID | HTTP 200, `duplicate: false`; another appeal entry saved |

The short explanation was:

```json
{
  "content_id": "53b1d580-3041-4e4b-a80c-266c38268e36",
  "reasoning": "I wrote this myself."
}
```

The response was:

```json
{
  "error": "reasoning_too_short",
  "message": "Your explanation must contain at least 25 words."
}
```

The second distinct explanation was:

```text
This is a second test explanation with different wording to confirm that
additional information can be saved for the same submission while keeping
the original appeal in the audit history.
```

Its saved log entry was:

```json
{
  "content_id": "53b1d580-3041-4e4b-a80c-266c38268e36",
  "creator_id": "arely",
  "event": "appeal",
  "reasoning": "This is a second test explanation with different wording to confirm that additional information can be saved for the same submission while keeping the original appeal in the audit history.",
  "status": "under_review",
  "timestamp": "2026-11-16T06:46:19+00:00"
}
```

After these checks, the filtered history contained three entries: the
original decision and two distinct appeals.

The word minimum checks explanation length, not evidence quality. A person
would still need to assess any drafts, notes, or other evidence described
by the writer.

---

## How I Used AI

**Moment 1**

- **What I asked for:** Help getting the submission endpoint running and
  connecting the signals to scoring, labels, and the audit log.
- **What came back:** A fixed JSON response to test the route first, followed
  by code for input validation, unique content IDs, the detector call,
  stylometry measurements, scoring, and label mapping.
- **What I changed:** I replaced the starter stubs in stages and ran terminal
  checks after each stage. I tested four calibration passages and verified
  that the endpoint returned both signal scores and their average. I recorded
  the false-positive results instead of describing the detector as accurate.

**Moment 2**

- **What I asked for:** Help implementing my appeal rules: at least 25 words,
  saving different explanations, and avoiding duplicate explanations for the
  same submission.
- **What came back:** An appeal function that validates the request, checks
  for an existing submission, compares explanations, and records valid appeals.
  AI also suggested wording for the reader-facing labels and helped draft
  this README from my actual terminal output.
- **What I changed:** I replaced the appeal stub and tested an initial appeal,
  an identical repeat, a short explanation, and a different explanation.
  I checked the audit history to confirm that the original decision and both
  distinct appeals remained recorded.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 10 per minute, 200 per day

**Why those numbers and not others:**

Ten submissions per minute allows a writer to submit work and make a few
revisions while slowing repeated automated requests. The daily limit of
200 allows regular use while limiting sustained requests from one caller.

**What a caller counts as:**

The service uses creator_id when it is a nonempty string. Otherwise, it
falls back to the caller's IP address. Different creators sharing an
address can have separate limits, but a script can bypass the per-creator
limit by changing its creator_id because these IDs are not authenticated.

The counters are stored in memory, so restarting the service resets them.

**The run of status codes when I pushed past it:**

Command:

```bash
python run_attacks.py --flood 15
```

Actual output:

```text
200 200 200 200 200 200 200 200 200 200 429 429 429 429 429
```

Ten requests succeeded and five were rate limited. The report was saved
to results/flood_2026-11-16_0206.md.

GET /log showed all five rate-limit rejections. I also submitted a request
with no text, which returned HTTP 400 and recorded this rejection:

```json
{
  "creator_id": "validation_tester",
  "event": "rejected",
  "reason": "invalid_text",
  "route": "/submit",
  "status": "rejected",
  "status_code": 400,
  "timestamp": "2026-11-16T07:09:57+00:00"
}
```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->

**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:

---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. | | | | | |
| 2. | | | | | |
| 3. | | | | | |
| 4. | | | | | |
| 5. | | | | | |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->

---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->

**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->

---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->

**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**