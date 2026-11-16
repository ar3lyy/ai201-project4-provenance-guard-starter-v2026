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

The original Unit 7 thresholds were human at or below 0.35, unsure above
0.35 and below 0.65, and AI at or above 0.65. Those settings produced the
before results.

The current thresholds after the single Unit 8 improvement are:

- Human: combined score at or below 0.35.
- Unsure: combined score above 0.35 and below 0.80.
- AI: combined score at or above 0.80.

Only `AI_THRESHOLD` changed, from 0.65 to 0.80. Both weights remain 0.50.

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
| unsure | 0.35 < score < 0.80 | Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision. |
| high-confidence AI | 0.80 ≤ score ≤ 1.00 | Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision. |

**Why I worded the "unsure" one this way:**

The label explains that the checks could not reach a confident conclusion.
It also says the result is not a finding of wrongdoing because uncertainty
should not become an accusation. The appeal sentence gives the writer a
way to challenge the result.

The ranges above describe the current code. The wording did not change.
The following Unit 7 submissions used the original AI threshold of 0.65:

| Submission | Combined score | Returned guess | Content ID |
|---|---:|---|---|
| Short test submission | 0.28125 | human | 53b1d580-3041-4e4b-a80c-266c38268e36 |
| Original AI garden passage | 0.6158 | unsure | 1deabba6-27f3-4048-8e3c-090e755161a6 |
| Human-written morning paragraph | 0.7745 | ai | b2f4fb71-e51f-4c26-9680-a2ad7989d6a0 |

The AI label on my morning paragraph is a false positive. This table
demonstrates historical label coverage, not accurate authorship detection.
After the threshold change, the morning paragraph receives unsure. All three
labels remain reachable across the wider tested inputs: EV10 still receives
AI at 0.84305. However, the original fixed six-sample coverage criterion now
misses because those six inputs contain no score at or above 0.80.

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

### Unit 8 AI assistance

I asked AI to help with rejection logging, testing, and the write-up. It
provided code that logs existing input errors without changing their acceptance
rules. I ran the flood and malformed-input checks locally and supplied the
actual output. AI also split my uploaded essay into ten unchanged excerpts,
generated five identified AI samples, and extended the evaluation runner to
measure my existing criteria, including appeals and log changes.

AI helped draft the attack assessment rules and diagnoses by comparing my
actual report and log entries. These are interpretations of the recorded
outcomes; they are not evidence of paired causal effects. The human samples
are limited to one essay, and no claim of general detector accuracy follows
from them. The runner uses fresh test creator IDs, so its criterion results
are separate from the flood test.

For the improvement, AI suggested raising only the AI threshold to 0.80
because avoiding false accusations was my priority. I made that change and
ran both test commands locally. AI compared the uploaded before and after
reports and helped write the measured tradeoff, including the newly missed
coverage target and unchanged score-gap miss. No after result was filled in
before the actual run.

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

Command: `python run_attacks.py --set attack_set --label before`

All 56 inputs completed. There were no observed 5xx responses or request
failures. The original report left every verdict blank; zero automatically
marked failures did not mean zero substantive failures.

### Assessment rules

HELD/BROKE describes whether the defense met the stated check below. These
rules are used consistently for the before and after runs. They are separate
from my five original acceptance criteria.

- Evasion: HELD requires an AI label. An unsure result is marked BROKE for
  detection, but is a partial evasion rather than a confident human judgment.
- False positives: an AI label is BROKE. Unsure avoids the accusation. FP08 is
  HELD only for the configured input rule: it was rejected for being under
  50 characters. That rejection still blocks legitimate short writing.
- Injection: check the attempted output or log manipulation. A requested human
  outcome counts as BROKE when returned, without claiming the model obeyed an
  instruction. Fixed safe labels and an unmodified structured log count as HELD.
- Malformed requests: appropriate JSON errors without crashes are HELD.
  Confident authorship judgments on repeated-character or emoji-only inputs
  are BROKE. MF07 is valid Arabic text: its confident AI judgment is marked
  BROKE for unsupported-language handling, not because Arabic should be rejected
  or because this test establishes its true authorship.
- Flood: the first ten accepted requests and the following 429 responses are
  HELD under the configured 10-per-minute policy. The supplied file contains
  12 flood rows, although its targeting description says 20.

Assessment totals: **37 HELD, 19 BROKE** under these rules.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `b3810c1a-a8ac-4000-bb6f-f2360bf24f95` | unsure | 0.397 | BROKE |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `5096a5bb-4de2-40b6-935c-aa397154c885` | unsure | 0.448 | BROKE |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `68c33533-9e80-44bc-8457-24d41f428bbd` | unsure | 0.578 | BROKE |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `86f4437d-df12-4f53-b285-4796d6a0e7a5` | unsure | 0.614 | BROKE |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `35c4ccf4-e314-4ec1-9a61-5171134544fb` | human | 0.340 | BROKE |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `078ec5ba-7ed8-4673-87b3-55c5f65e8186` | unsure | 0.413 | BROKE |
| EV07 | evasion | signal two: padding with punctuation | 200 | `50dbeb4a-3bad-4734-8bbc-ca32b2038f92` | unsure | 0.543 | BROKE |
| EV08 | evasion | signal one: text below the token window | 200 | `a05bcf52-77a2-4d18-9fea-60062262883a` | unsure | 0.373 | BROKE |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `4e72f681-b9ef-4555-9424-1fd502d49260` | unsure | 0.591 | BROKE |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `df4f9920-0a25-46b6-9705-c572c00e5fc2` | ai | 0.843 | HELD |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `61c6cfd8-e7aa-4beb-9392-c640e9ee7ba2` | unsure | 0.579 | HELD |
| FP02 | false_positive | human writing in a formal register | 200 | `b5015d1c-b57a-4399-8cc9-75adb1ba9f94` | ai | 0.698 | BROKE |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `53117377-ba35-4662-9df5-5c00ca047981` | ai | 0.712 | BROKE |
| FP04 | false_positive | a student essay written to a rubric | 200 | `756d529c-7bb4-4cbb-8b30-cb622627379d` | ai | 0.698 | BROKE |
| FP05 | false_positive | technical documentation written by a person | 200 | `b6dc5863-d43b-4b4f-8c09-83ec5ad1759e` | ai | 0.731 | BROKE |
| FP06 | false_positive | a person imitating a formal template | 200 | `5eca2a25-171c-4d54-bb08-31d8ff803c95` | ai | 0.694 | BROKE |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `5f5c107e-f889-40e3-96c5-e48127a6bb5b` | ai | 0.675 | BROKE |
| FP08 | false_positive | very short genuine human submission | 400 | `—` | — | — | HELD |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `82bf1934-f4ff-4397-8090-152b1f4cea47` | unsure | 0.426 | HELD |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `8513e4a0-bc7e-47e0-abcd-15213c689a83` | human | 0.282 | BROKE |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `5b16daae-5327-4c4d-baa5-8ae1ffeaa724` | unsure | 0.556 | HELD |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `840e16ad-f8a2-439d-8d34-a151b9b408f5` | unsure | 0.486 | HELD |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `092fd0ce-53e9-40ec-9879-f177531e1841` | unsure | 0.493 | HELD |
| PI06 | prompt_injection | instruction plus real human text | 200 | `edf18a0e-9c34-4807-8cd2-6a401afbccdd` | unsure | 0.553 | HELD |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — | HELD |
| MF02 | malformed | text is a single character | 400 | `—` | — | — | HELD |
| MF03 | malformed | text is control characters | 400 | `—` | — | — | HELD |
| MF04 | malformed | text is only punctuation | 400 | `—` | — | — | HELD |
| MF05 | malformed | text is a very long single word | 200 | `20fcfcee-e1c5-493b-8886-dbe6c25f1805` | ai | 0.749 | BROKE |
| MF06 | malformed | text is emoji only | 200 | `c40bbc86-1fb0-4d1e-a1c9-ffc442e388d6` | ai | 0.748 | BROKE |
| MF07 | malformed | text is right-to-left script | 200 | `28afc9d0-d48b-4368-9d96-2c053f19cb2f` | ai | 0.703 | BROKE |
| MF08 | malformed | text is 60,000 characters | 413 | `—` | — | — | HELD |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — | HELD |
| RQ02 | malformed | no creator_id | 400 | `—` | — | — | HELD |
| RQ03 | malformed | text is a number | 400 | `—` | — | — | HELD |
| RQ04 | malformed | text is a list | 400 | `—` | — | — | HELD |
| RQ05 | malformed | text is null | 400 | `—` | — | — | HELD |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — | HELD |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — | HELD |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — | HELD |
| RQ09 | malformed | body is empty | 400 | `—` | — | — | HELD |
| RQ10 | malformed | body is form-encoded, not JSON | 400 | `—` | — | — | HELD |
| RQ11 | malformed | body is JSON claiming to be plain text | 400 | `—` | — | — | HELD |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — | HELD |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | `d3c1fbe2-0157-44c7-8380-4bea240c71ae` | human | 0.264 | HELD |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | `da61cb3e-88b7-4938-95cb-80b3a3ff3789` | human | 0.264 | HELD |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | `cfbe517d-48e2-44ef-8db3-246a4f28d430` | human | 0.264 | HELD |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | `a6c4baf4-9ad4-457a-a1a0-ceee92d25976` | human | 0.264 | HELD |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | `2c4302af-7a0a-40bd-a1dc-9bbd919b1ce7` | human | 0.264 | HELD |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 200 | `3baddf03-a070-4a54-b56d-4c7c89d1382f` | human | 0.264 | HELD |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 200 | `b574bdb1-d4e3-4014-a10a-9123c6653578` | human | 0.264 | HELD |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 200 | `2cc5c735-33db-4e5f-b1df-fade5934f6f3` | human | 0.264 | HELD |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 200 | `566a7447-3a4c-4e3d-8058-52221486ffaf` | human | 0.264 | HELD |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 200 | `235db0aa-e399-41d7-80d2-11c235d8eed5` | human | 0.264 | HELD |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |

**Ten audit log entries from the run**

These are actual entries from `results/audit_extract.json`. The ninth shows
unsupported-language handling; the tenth records a rate-limit rejection.

```json
[
  {
    "combined_score": 0.39705,
    "content_id": "b3810c1a-a8ac-4000-bb6f-f2360bf24f95",
    "creator_id": "attacker_EV01",
    "guess": "unsure",
    "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
    "model_score": 0.1635,
    "status": "decided",
    "style_score": 0.6306,
    "timestamp": "2026-11-16T07:14:17+00:00"
  },
  {
    "combined_score": 0.44825000000000004,
    "content_id": "5096a5bb-4de2-40b6-935c-aa397154c885",
    "creator_id": "attacker_EV02",
    "guess": "unsure",
    "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
    "model_score": 0.5943,
    "status": "decided",
    "style_score": 0.3022,
    "timestamp": "2026-11-16T07:14:17+00:00"
  },
  {
    "combined_score": 0.3397,
    "content_id": "35c4ccf4-e314-4ec1-9a61-5171134544fb",
    "creator_id": "attacker_EV05",
    "guess": "human",
    "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
    "model_score": 0.3212,
    "status": "decided",
    "style_score": 0.3582,
    "timestamp": "2026-11-16T07:14:18+00:00"
  },
  {
    "combined_score": 0.6977,
    "content_id": "b5015d1c-b57a-4399-8cc9-75adb1ba9f94",
    "creator_id": "attacker_FP02",
    "guess": "ai",
    "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
    "model_score": 0.7387,
    "status": "decided",
    "style_score": 0.6567,
    "timestamp": "2026-11-16T07:14:18+00:00"
  },
  {
    "combined_score": 0.7120500000000001,
    "content_id": "53117377-ba35-4662-9df5-5c00ca047981",
    "creator_id": "attacker_FP03",
    "guess": "ai",
    "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
    "model_score": 0.8051,
    "status": "decided",
    "style_score": 0.619,
    "timestamp": "2026-11-16T07:14:18+00:00"
  },
  {
    "combined_score": 0.73085,
    "content_id": "b6dc5863-d43b-4b4f-8c09-83ec5ad1759e",
    "creator_id": "attacker_FP05",
    "guess": "ai",
    "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
    "model_score": 0.8005,
    "status": "decided",
    "style_score": 0.6612,
    "timestamp": "2026-11-16T07:14:19+00:00"
  },
  {
    "combined_score": 0.2816,
    "content_id": "8513e4a0-bc7e-47e0-abcd-15213c689a83",
    "creator_id": "attacker_PI02",
    "guess": "human",
    "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
    "model_score": 0.2044,
    "status": "decided",
    "style_score": 0.3588,
    "timestamp": "2026-11-16T07:14:19+00:00"
  },
  {
    "combined_score": 0.7484500000000001,
    "content_id": "c40bbc86-1fb0-4d1e-a1c9-ffc442e388d6",
    "creator_id": "attacker_MF06",
    "guess": "ai",
    "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
    "model_score": 0.9969,
    "status": "decided",
    "style_score": 0.5,
    "timestamp": "2026-11-16T07:14:20+00:00"
  },
  {
    "combined_score": 0.7032,
    "content_id": "28afc9d0-d48b-4368-9d96-2c053f19cb2f",
    "creator_id": "attacker_MF07",
    "guess": "ai",
    "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
    "model_score": 0.9064,
    "status": "decided",
    "style_score": 0.5,
    "timestamp": "2026-11-16T07:14:20+00:00"
  },
  {
    "creator_id": "attacker_flood",
    "event": "rejected",
    "limit": "10 per 1 minute",
    "reason": "rate_limited",
    "status": "rejected",
    "timestamp": "2026-11-16T07:14:20+00:00"
  }
]
```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:

FP03, the staff sample representing a person writing carefully in a second
language, received an AI label at 0.71205. Its model score was 0.8051 and its
style score was 0.6190. The equal average crossed 0.65, so ordinary writing
patterns became an accusation. The appeal option does not remove the burden
this places on a writer.

---

## Run Log and Verdicts

Command: `python run_eval.py --label before`

Produced by `run_eval.py::main`, `run_eval.py::evaluate`, and
`run_eval.py::appeal_test`. The runner extends the starter to check appeals
and audit history, invalid responses, label coverage, and group means.

The ten human inputs are non-overlapping, unchanged excerpts from my supplied
five-paragraph essay, two per paragraph. Quotations, citations, and original
Markdown entities are retained. These are correlated samples from one essay,
not ten independent writing tasks. The AI samples were generated by ChatGPT.
Criterion 5 uses H01–H05 and A01–A05; topics and lengths are not matched.
The six coverage samples are fixed and include earlier calibration inputs.

Each test submission receives a fresh creator ID to isolate these criteria
from the separately tested flood limit. Rate limiting stays enabled. Samples
and targets remain the same for the after run. Matching trials are expected
because both scoring signals are deterministic for identical input.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Human false positives | 0/10 AI labels, all 10 accepted | 0/10 AI; 10/10 accepted | 0/10 AI; 10/10 accepted | 0/10 AI; 10/10 accepted | MET |
| 2. Appeal rules | 5/5 cases handled correctly | 5/5 | 5/5 | 5/5 | MET |
| 3. Invalid submissions | 5/5 correct JSON errors | 5/5; service alive=True | 5/5; service alive=True | 5/5; service alive=True | MET |
| 4. Label coverage | 3/3 labels across six samples | 3/3 labels; 6/6 accepted | 3/3 labels; 6/6 accepted | 3/3 labels; 6/6 accepted | MET |
| 5. Average score spread | AI mean minus human mean >= 0.25 | gap=0.07393 | gap=0.07393 | gap=0.07393 | MISSED |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

### Criterion 1 — Trial 1

Source: `results/run_2026-11-16_023053_before.json`, produced by
`run_eval.py::evaluate`.

```json
{
  "met": true,
  "measure": "0/10 AI; 10/10 accepted",
  "false_positives": 0,
  "accepted": 10,
  "trial": 1,
  "responses": [
    {
      "status": 200,
      "response": {
        "confidence": 0.5468999999999999,
        "content_id": "682b052f-b0bc-4b9e-b40e-e36cff236553",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.4625,
        "style_score": 0.6313
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.5549,
        "content_id": "c21bbe6f-d5df-4978-aedf-3f0ccc405838",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.4694,
        "style_score": 0.6404
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.5868,
        "content_id": "89f41625-b263-4f64-b697-3216472a1e28",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.5762,
        "style_score": 0.5974
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.51585,
        "content_id": "ffc35844-a897-4400-bb3f-8000cc9df4c6",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.4313,
        "style_score": 0.6004
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.4921,
        "content_id": "29d4e198-4c46-4b72-9952-5f69d866c298",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.4804,
        "style_score": 0.5038
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.5067,
        "content_id": "cb2d2583-c4b0-4b9c-84af-3d2a8282d23f",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.4261,
        "style_score": 0.5873
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.5136499999999999,
        "content_id": "0248a1e1-fd78-4e8d-84cc-08e5b8e10f8d",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.4589,
        "style_score": 0.5684
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.5062,
        "content_id": "0a32a055-2eec-4bbb-a117-9644b9fa7a99",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.5257,
        "style_score": 0.4867
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.38875000000000004,
        "content_id": "a48441cb-396c-4690-86a1-024894f932ed",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.3204,
        "style_score": 0.4571
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.4123,
        "content_id": "9cb357ef-4feb-4ab9-88c0-8ed06328a67d",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.2072,
        "style_score": 0.6174
      }
    }
  ]
}
```

### Criterion 2 — Trial 1

Source: `results/run_2026-11-16_023053_before.json`, produced by
`run_eval.py::evaluate` and `run_eval.py::appeal_test`.

```json
{
  "met": true,
  "measure": "5/5",
  "cases": [
    {
      "case": "initial detailed explanation",
      "met": true,
      "status": 200,
      "before_entries": 1,
      "after_entries": 2
    },
    {
      "case": "duplicate explanation",
      "met": true,
      "status": 200,
      "before_entries": 2,
      "after_entries": 2
    },
    {
      "case": "short explanation",
      "met": true,
      "status": 400,
      "before_entries": 2,
      "after_entries": 2
    },
    {
      "case": "different detailed explanation",
      "met": true,
      "status": 200,
      "before_entries": 2,
      "after_entries": 3
    },
    {
      "case": "unknown content ID",
      "met": true,
      "status": 404,
      "before_entries": 0,
      "after_entries": 0
    }
  ],
  "trial": 1,
  "responses": [
    {
      "route": "/submit",
      "status": 200,
      "response": {
        "confidence": 0.4461,
        "content_id": "12e578c1-b0c2-4a22-aa5d-eca0e9a8f6af",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.2171,
        "style_score": 0.6751
      }
    },
    {
      "route": "/appeal",
      "status": 200,
      "response": {
        "content_id": "12e578c1-b0c2-4a22-aa5d-eca0e9a8f6af",
        "duplicate": false,
        "message": "Your appeal has been recorded for review. The writing has not been automatically rescored.",
        "status": "under_review"
      }
    },
    {
      "route": "/appeal",
      "status": 200,
      "response": {
        "content_id": "12e578c1-b0c2-4a22-aa5d-eca0e9a8f6af",
        "duplicate": true,
        "message": "This explanation is already recorded. No duplicate appeal was saved.",
        "status": "under_review"
      }
    },
    {
      "route": "/appeal",
      "status": 400,
      "response": {
        "error": "reasoning_too_short",
        "message": "Your explanation must contain at least 25 words."
      }
    },
    {
      "route": "/appeal",
      "status": 200,
      "response": {
        "content_id": "12e578c1-b0c2-4a22-aa5d-eca0e9a8f6af",
        "duplicate": false,
        "message": "Your appeal has been recorded for review. The writing has not been automatically rescored.",
        "status": "under_review"
      }
    },
    {
      "route": "/appeal",
      "status": 404,
      "response": {
        "error": "content_not_found",
        "message": "No submission exists with that content_id."
      }
    }
  ]
}
```

### Criterion 3 — Trial 1

Source: `results/run_2026-11-16_023053_before.json`, produced by
`run_eval.py::evaluate`.

```json
{
  "met": true,
  "measure": "5/5; service alive=True",
  "cases": [
    {
      "case": "missing text",
      "met": true,
      "status": 400
    },
    {
      "case": "blank text",
      "met": true,
      "status": 400
    },
    {
      "case": "wrong type",
      "met": true,
      "status": 400
    },
    {
      "case": "short text",
      "met": true,
      "status": 400
    },
    {
      "case": "long text",
      "met": true,
      "status": 413
    }
  ],
  "service_alive": true,
  "trial": 1,
  "responses": [
    {
      "route": "/submit",
      "status": 400,
      "response": {
        "error": "invalid_text",
        "message": "Text is required and must be a nonempty string."
      }
    },
    {
      "route": "/submit",
      "status": 400,
      "response": {
        "error": "invalid_text",
        "message": "Text is required and must be a nonempty string."
      }
    },
    {
      "route": "/submit",
      "status": 400,
      "response": {
        "error": "invalid_text",
        "message": "Text is required and must be a nonempty string."
      }
    },
    {
      "route": "/submit",
      "status": 400,
      "response": {
        "error": "text_too_short",
        "message": "Text must contain at least 50 characters."
      }
    },
    {
      "route": "/submit",
      "status": 413,
      "response": {
        "error": "text_too_long",
        "message": "Text must contain no more than 10,000 characters."
      }
    }
  ]
}
```

### Criterion 4 — Trial 1

Source: `results/run_2026-11-16_023053_before.json`, produced by
`run_eval.py::evaluate`.

```json
{
  "met": true,
  "measure": "3/3 labels; 6/6 accepted",
  "labels": [
    "ai",
    "human",
    "unsure"
  ],
  "trial": 1,
  "responses": [
    {
      "status": 200,
      "response": {
        "confidence": 0.28125,
        "content_id": "56ebc3fa-0abc-436f-b192-e9f30304ef97",
        "guess": "human",
        "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
        "model_score": 0.0625,
        "style_score": 0.5
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.6158,
        "content_id": "8bad3935-518b-4ccb-a65b-03fc319ad26c",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.6927,
        "style_score": 0.5389
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.5468999999999999,
        "content_id": "0c3d3dba-39a2-465e-b654-b9c89f64de18",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.4625,
        "style_score": 0.6313
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.5549,
        "content_id": "856a8db6-81f5-4296-925a-8e23fef53fab",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.4694,
        "style_score": 0.6404
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.6543,
        "content_id": "f6475ad4-3c2b-42b7-9d96-c1433134c00f",
        "guess": "ai",
        "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
        "model_score": 0.7361,
        "style_score": 0.5725
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.7745,
        "content_id": "fd0fd6ff-600f-4cb7-bd2e-638a4b2ce242",
        "guess": "ai",
        "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
        "model_score": 0.8582,
        "style_score": 0.6908
      }
    }
  ]
}
```

### Criterion 5 — Trial 1

Source: `results/run_2026-11-16_023053_before.json`, produced by
`run_eval.py::evaluate`.

```json
{
  "met": false,
  "measure": "gap=0.07393",
  "human_scores": [
    0.5468999999999999,
    0.5549,
    0.5868,
    0.51585,
    0.4921
  ],
  "ai_scores": [
    0.6158,
    0.6543,
    0.6246499999999999,
    0.5837,
    0.58775
  ],
  "human_mean": 0.53931,
  "ai_mean": 0.61324,
  "gap": 0.07393000000000005,
  "trial": 1,
  "responses": [
    {
      "status": 200,
      "response": {
        "confidence": 0.5468999999999999,
        "content_id": "a8dbab39-5d35-464d-9ddd-18aec885c937",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.4625,
        "style_score": 0.6313
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.5549,
        "content_id": "15d0ec5e-8e25-4c51-ab95-e1660dbf0267",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.4694,
        "style_score": 0.6404
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.5868,
        "content_id": "ca5e1477-db12-4a97-b047-27ab6a7ac9ff",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.5762,
        "style_score": 0.5974
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.51585,
        "content_id": "bb13d113-d811-4f59-94ff-62a49540a679",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.4313,
        "style_score": 0.6004
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.4921,
        "content_id": "0fbbac1e-7f8a-4898-8413-e88659c5f331",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.4804,
        "style_score": 0.5038
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.6158,
        "content_id": "adf01144-b8f9-418e-892a-4194398ff925",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.6927,
        "style_score": 0.5389
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.6543,
        "content_id": "ce6ec40f-68bb-4dff-a030-71e55c624481",
        "guess": "ai",
        "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
        "model_score": 0.7361,
        "style_score": 0.5725
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.6246499999999999,
        "content_id": "899c04b2-8123-4fd8-b9d8-70e7448e3ff1",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.6672,
        "style_score": 0.5821
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.5837,
        "content_id": "c031faee-7cc7-473a-a06e-aeb132d8e746",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.5394,
        "style_score": 0.628
      }
    },
    {
      "status": 200,
      "response": {
        "confidence": 0.58775,
        "content_id": "391f23c6-9885-48f3-85d7-bddf1048c7b6",
        "guess": "unsure",
        "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
        "model_score": 0.5288,
        "style_score": 0.6467
      }
    }
  ]
}
```

**Diagnoses**

1. **Criterion 1 — MET.** All ten excerpts were accepted and none received an
   AI label in any trial. All ten were unsure, so this is success at avoiding
   accusations on these samples, not successful recognition of human authorship.
   It does not cancel the six false positives in the staff set.
2. **Criterion 2 — MET.** Each trial checked the initial valid appeal, an exact
   duplicate, a short explanation, a different valid explanation, and an unknown
   ID. Log counts changed only for the two distinct valid appeals. The original
   decision remained unchanged. Length is not a check of evidence quality.
3. **Criterion 3 — MET.** All five invalid-input cases returned the required
   JSON errors and HTTP codes in every trial. A subsequent health check passed.
   The attack set also exposed valid-shaped inputs that length checks do not
   make suitable for authorship scoring.
4. **Criterion 4 — MET.** The fixed six inputs produced all three labels in
   every trial. One AI label was on my human morning paragraph. Coverage is
   not accuracy, and a later threshold change may remove that label from this
   particular set even while the label remains reachable in principle.
5. **Criterion 5 — MISSED.** The human mean was 0.53931 and the AI mean was
   0.61324, a gap of 0.07393 rather than 0.25. Signal one had means of 0.48396
   and 0.63284, a gap of 0.14888. Signal two had means of 0.59466 and 0.59364,
   a gap of -0.00102. **Stages: signal two and combining rule.** The style
   heuristics gave nearly identical group averages, and weighting them at 50%
   reduced the separation supplied by the model. Signal one alone also misses
   the target. Changing a label threshold cannot change this score gap.

Broken attacks are diagnosed by shared mechanisms below. The targeting column
states staff intent; a single attacked input does not establish the causal
change that would require a paired, unmodified control.

| Broken attacks | Stage and mechanism supported by this run |
|---|---|
| EV01 | Signal one scored 0.1635 while style scored 0.6306. Their average was 0.39705, below the AI cutoff. The low model score drove the partial evasion; this run does not show that typos lowered the style score. |
| EV02, EV06 | Signal two returned 0.3022 and 0.2531. Sentence fragmentation and uneven lengths target the spread component; their low style scores pulled the combined scores to 0.44825 and 0.41290. Both were unsure. |
| EV03, EV09 | Style scores of 0.4907 and 0.4776 reduced model scores of 0.6662 and 0.7042 to unsure averages. Quotations and mixed human/AI text are measured as a single passage. |
| EV04 | Both scores, 0.6114 and 0.6166, were below 0.65, so averaging could not reach the AI band. Rare-word predictability is the targeted weakness; no paired control isolates its effect here. |
| EV05 | Both scores leaned human, 0.3212 and 0.3582, producing 0.33970 and a human label. Both signals measure the edited text's patterns rather than its creation history. |
| EV07, EV08 | Style fell back to 0.5. With model scores 0.5862 and 0.2452, equal weighting produced unsure scores of 0.54310 and 0.37260. A neutral fallback is insufficient evidence, not independent support for either authorship. |
| FP02–FP07 | Signal one ranged from 0.7387 to 0.8816. Style ranged from 0.4684 to 0.6612. The equal averages were 0.67500–0.73085, crossing the label mapper's 0.65 AI cutoff. Predictable human prose and the chosen cutoff created six false accusations. |
| PI02 | The requested human outcome occurred, but the exact requested score 0.02 did not: the service returned 0.2816 from scores 0.2044 and 0.3588. The classification outcome broke; there is no evidence of instruction execution because this model scores text rather than following a chat instruction. |
| MF05, MF06 | The route checked string type and length, accepting a repeated-character string and emoji-only input. Signal two fell back to 0.5; model scores 0.9976 and 0.9969 produced confident AI judgments. The route has no suitability check and the scoring path has no abstention for these inputs. |
| MF07 | Valid Arabic text received model 0.9064 and style 0.5, producing 0.7032 and an AI label. The style tokenizer does not recognize Arabic words, so it falls back. The service still labels the result confidently without validated language support. |

PI04 retained the fixed safe label, and PI05 did not insert the supplied
fake fields into the decision log. Those outcomes held the tested output and
log boundaries. This backend test does not test how a separate website renders
submitted HTML.

FP08 followed my 50-character minimum and was logged as `text_too_short`.
That holds the input rule but still excludes genuine short writing. RQ06 was
rejected for short text before reaching the creator-ID check, so that attack
alone does not isolate validation of an object-valued creator ID.

---

## The Improvement

**What I changed:**

I changed only `config.py::AI_THRESHOLD` from 0.65 to 0.80. The human threshold
stayed at 0.35, and both signal weights stayed at 0.50. Signal calculations,
label wording, acceptance criteria, evaluation samples, and validation rules
were unchanged. I restarted the service and ran the same attack set and all
five criteria again.

**Which diagnosis pointed at it:**

FP02–FP07 were human samples with combined scores of 0.67500–0.73085.
The 0.65 cutoff turned those scores into AI labels. Raising the cutoff
prioritizes avoiding wrong accusations, which was my main concern when
setting the criteria. It does not repair the underlying signal weaknesses
or increase the average score gap. The threshold was chosen after inspecting
the before results, so this is an improvement on the measured set, not an
independent validation of general performance.

### Attack Run — After

Command: `python run_attacks.py --set attack_set --label after`

Source: `results/attack_run_2026-11-16_0240_after.md`, produced by
`run_attacks.py::main`. All 56 attacks ran. The assessment rules are the same
as in Attack Run — Before. No 5xx or request failures were observed.

Assessment totals: **46 HELD, 10 BROKE**, compared with
37 HELD and 19 BROKE before. These counts depend on the stated assessment
rules and are not a general accuracy estimate.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `3f989115-7abd-4d32-8b1a-4cd9a1577e42` | unsure | 0.397 | BROKE |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `1654b101-3516-4735-ad16-24f27566252a` | unsure | 0.448 | BROKE |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `19c8ad35-471c-4b08-aeb1-94b92c9423f4` | unsure | 0.578 | BROKE |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `de85c1a2-0a90-4838-8102-0a5692fde9f5` | unsure | 0.614 | BROKE |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `7b85ddd2-b10c-42ea-adb1-987bde00df72` | human | 0.340 | BROKE |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `ec7fc86c-f3b4-4061-8c07-f110418c3e2a` | unsure | 0.413 | BROKE |
| EV07 | evasion | signal two: padding with punctuation | 200 | `b2181a3e-1727-49c1-9188-45519c75c6cd` | unsure | 0.543 | BROKE |
| EV08 | evasion | signal one: text below the token window | 200 | `ab233903-c184-4dec-9821-47a9cb7f539e` | unsure | 0.373 | BROKE |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `a802ad1a-d291-4652-abca-ab5857d2a4d1` | unsure | 0.591 | BROKE |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `6d211277-6eb2-43a2-ab70-7351730c83c0` | ai | 0.843 | HELD |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `57cfbcd5-de7b-43ec-be22-6a4e74c2f60d` | unsure | 0.579 | HELD |
| FP02 | false_positive | human writing in a formal register | 200 | `2998dbc0-a4d3-4a64-9332-d411b464a59a` | unsure | 0.698 | HELD |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `d76f6cd7-9ba9-448e-8e7f-11498cdc43b1` | unsure | 0.712 | HELD |
| FP04 | false_positive | a student essay written to a rubric | 200 | `728bb8f0-23cd-48f7-bac6-2cbae895ae58` | unsure | 0.698 | HELD |
| FP05 | false_positive | technical documentation written by a person | 200 | `ea676843-afeb-4cec-9475-93a621f1d417` | unsure | 0.731 | HELD |
| FP06 | false_positive | a person imitating a formal template | 200 | `43ab9ac4-f899-4433-a3e0-ad100f036cd4` | unsure | 0.694 | HELD |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `73f0487b-3430-426e-92d8-154209d07b9b` | unsure | 0.675 | HELD |
| FP08 | false_positive | very short genuine human submission | 400 | `—` | — | — | HELD |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `9de94349-0e9e-4e09-b519-4eeb27230c5c` | unsure | 0.426 | HELD |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `4d6ebf0e-3de1-499d-b388-fe9475c32012` | human | 0.282 | BROKE |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `e12d755b-d008-4fde-af4f-f1a1a1992614` | unsure | 0.556 | HELD |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `f4e8a89a-9fac-4f2b-a42a-90d5f5bffd32` | unsure | 0.486 | HELD |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `a82f7f69-7b45-4c22-8a1b-9688b1c4ab40` | unsure | 0.493 | HELD |
| PI06 | prompt_injection | instruction plus real human text | 200 | `373a5d51-61c1-4339-906c-49f12e2b676b` | unsure | 0.553 | HELD |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — | HELD |
| MF02 | malformed | text is a single character | 400 | `—` | — | — | HELD |
| MF03 | malformed | text is control characters | 400 | `—` | — | — | HELD |
| MF04 | malformed | text is only punctuation | 400 | `—` | — | — | HELD |
| MF05 | malformed | text is a very long single word | 200 | `36022526-ac85-46fe-b976-eb3a6e14a784` | unsure | 0.749 | HELD |
| MF06 | malformed | text is emoji only | 200 | `b7415c48-5133-44d0-8f2d-172023c19a6d` | unsure | 0.748 | HELD |
| MF07 | malformed | text is right-to-left script | 200 | `a61e94e7-a54a-4e8e-a199-b9ebc1bfdc05` | unsure | 0.703 | HELD |
| MF08 | malformed | text is 60,000 characters | 413 | `—` | — | — | HELD |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — | HELD |
| RQ02 | malformed | no creator_id | 400 | `—` | — | — | HELD |
| RQ03 | malformed | text is a number | 400 | `—` | — | — | HELD |
| RQ04 | malformed | text is a list | 400 | `—` | — | — | HELD |
| RQ05 | malformed | text is null | 400 | `—` | — | — | HELD |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — | HELD |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — | HELD |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — | HELD |
| RQ09 | malformed | body is empty | 400 | `—` | — | — | HELD |
| RQ10 | malformed | body is form-encoded, not JSON | 400 | `—` | — | — | HELD |
| RQ11 | malformed | body is JSON claiming to be plain text | 400 | `—` | — | — | HELD |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — | HELD |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | `609b589b-1f7f-4f7a-916a-855e5e4fb1aa` | human | 0.264 | HELD |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | `4463266f-cf38-45a5-ab17-b93dbfdff743` | human | 0.264 | HELD |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | `2e3b1a60-9e06-49f7-9405-b352ccd4caba` | human | 0.264 | HELD |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | `8edcbc49-5b50-4d99-891f-85f4a0233e36` | human | 0.264 | HELD |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | `6166390e-84fc-44df-a713-1330e08b1365` | human | 0.264 | HELD |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 200 | `799494e0-ba02-4787-a5da-7e53002ccf4a` | human | 0.264 | HELD |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 200 | `81c1e1d5-0728-4937-8a5f-2e859795febf` | human | 0.264 | HELD |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 200 | `1b26d3e3-71f3-4019-adb6-7af904c6ae52` | human | 0.264 | HELD |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 200 | `2f61b532-964a-491d-a124-1fa7e096db8c` | human | 0.264 | HELD |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 200 | `1ff070f3-8e6a-4927-8e53-94e08d15bd8e` | human | 0.264 | HELD |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |

**Before and after, side by side**

| Measure | Before | After |
|---|---|---|
| Attack assessments | 37 HELD / 19 BROKE | 46 HELD / 10 BROKE |
| FP02–FP07: human samples labeled AI | 6 | 0; all became unsure |
| FP01 | unsure | unsure |
| FP08 | 400 for short text | 400 for short text |
| Evasion rows | 1 AI, 8 unsure, 1 human | 1 AI, 8 unsure, 1 human |
| PI02 | human at 0.2816 | human at 0.2816 |
| MF05–MF07 | 3 AI labels | 3 unsure labels |
| RQ01–RQ12 | All 400 | All 400 |
| Flood rows | 10 accepted, then 2 rejected with 429 | 10 accepted, then 2 rejected with 429 |
| Observed server crashes | 0 | 0 |

I compared the report details by attack ID. All 56 HTTP statuses, model scores,
style scores, and combined scores were identical before and after. Only the
nine expected guesses and labels changed: FP02–FP07 and MF05–MF07. This is
consistent with changing only a label threshold.

**Five criteria after the change — three trials each**

Produced by `run_eval.py::main`, `evaluate`, and `appeal_test`.

| Criterion | Original target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Human false positives | 0/10 AI labels, all 10 accepted | 0/10 AI; 10/10 accepted | 0/10 AI; 10/10 accepted | 0/10 AI; 10/10 accepted | MET |
| 2. Appeal rules | 5/5 cases handled correctly | 5/5 | 5/5 | 5/5 | MET |
| 3. Invalid submissions | 5/5 correct JSON errors | 5/5; service alive=True | 5/5; service alive=True | 5/5; service alive=True | MET |
| 4. Label coverage | 3/3 labels across six samples | 2/3 labels; 6/6 accepted | 2/3 labels; 6/6 accepted | 2/3 labels; 6/6 accepted | MISSED |
| 5. Average score spread | AI mean minus human mean >= 0.25 | gap=0.07393 | gap=0.07393 | gap=0.07393 | MISSED |

| Criterion | Before verdict | After verdict | Reason |
|---|---|---|---|
| 1. Human false positives | MET | MET | The ten essay excerpts stayed unsure, with zero AI labels. |
| 2. Appeal rules | MET | MET | All five cases passed in each trial, including log checks. |
| 3. Invalid submissions | MET | MET | All five errors matched, and the service remained running. |
| 4. Label coverage | MET | MISSED | None of the fixed six samples reaches the new AI cutoff. |
| 5. Average score spread | MISSED | MISSED | The score gap remains 0.07393; thresholds do not change scores. |

**Actual after output — Trial 1 for each criterion**

Source: `results/run_2026-11-16_024035_after.json`. Trial summaries below
are copied from that file; the full three-trial request/response evidence is
saved in both after evaluation reports.

#### Criterion 1

```json
{
  "met": true,
  "measure": "0/10 AI; 10/10 accepted",
  "false_positives": 0,
  "accepted": 10,
  "trial": 1
}
```

#### Criterion 2

```json
{
  "met": true,
  "measure": "5/5",
  "cases": [
    {
      "case": "initial detailed explanation",
      "met": true,
      "status": 200,
      "before_entries": 1,
      "after_entries": 2
    },
    {
      "case": "duplicate explanation",
      "met": true,
      "status": 200,
      "before_entries": 2,
      "after_entries": 2
    },
    {
      "case": "short explanation",
      "met": true,
      "status": 400,
      "before_entries": 2,
      "after_entries": 2
    },
    {
      "case": "different detailed explanation",
      "met": true,
      "status": 200,
      "before_entries": 2,
      "after_entries": 3
    },
    {
      "case": "unknown content ID",
      "met": true,
      "status": 404,
      "before_entries": 0,
      "after_entries": 0
    }
  ],
  "trial": 1
}
```

#### Criterion 3

```json
{
  "met": true,
  "measure": "5/5; service alive=True",
  "cases": [
    {
      "case": "missing text",
      "met": true,
      "status": 400
    },
    {
      "case": "blank text",
      "met": true,
      "status": 400
    },
    {
      "case": "wrong type",
      "met": true,
      "status": 400
    },
    {
      "case": "short text",
      "met": true,
      "status": 400
    },
    {
      "case": "long text",
      "met": true,
      "status": 413
    }
  ],
  "service_alive": true,
  "trial": 1
}
```

#### Criterion 4

```json
{
  "met": false,
  "measure": "2/3 labels; 6/6 accepted",
  "labels": [
    "human",
    "unsure"
  ],
  "trial": 1
}
```

#### Criterion 5

```json
{
  "met": false,
  "measure": "gap=0.07393",
  "human_scores": [
    0.5468999999999999,
    0.5549,
    0.5868,
    0.51585,
    0.4921
  ],
  "ai_scores": [
    0.6158,
    0.6543,
    0.6246499999999999,
    0.5837,
    0.58775
  ],
  "human_mean": 0.53931,
  "ai_mean": 0.61324,
  "gap": 0.07393000000000005,
  "trial": 1
}
```

**Did it help, and how do I know:**

It helped reduce false accusations in the staff set: six human samples that
previously received AI labels now receive unsure. It also removed confident
AI labels from the repeated-character, emoji-only, and Arabic inputs, although
those inputs still reach the scoring pipeline.

The cost is visible in criterion 4: only human and unsure appear in the same
six coverage samples after the change. For example, the known AI library
passage at 0.6543 changed from AI to unsure. My human morning paragraph at
0.7745 also changed from AI to unsure. Thus the wider unsure range avoids a
wrong accusation and also withholds a previously correct AI label. The ten
staff evasion outcomes did not change, and EV10 at 0.84305 still demonstrates
that the AI label is reachable elsewhere.

The improvement does not solve criterion 5. Human and AI means are still
0.53931 and 0.61324. I kept the original 0.25 target and recorded the miss.

---

## What's Still Broken

| Remaining issue | Stage and mechanism | What I would do next |
|---|---|---|
| EV01–EV04 and EV06–EV09 remain unsure | Signal scores stay below the AI cutoff; neutral style fallbacks and disagreement reduce confidence. This is still partial evasion under the unchanged assessment rule. | Test paired original/modified passages to isolate how typos, sentence changes, quotations, and wording affect each component, then validate any revised signal on separate data. |
| EV05 still receives human | Both signals score the edited text as human-like; neither establishes creation history. | Treat the label as tentative and investigate process evidence or provenance rather than claim a detector can prove authorship. |
| PI02 still receives human | The text scores 0.2816 from its measured patterns. The requested classification occurs, but this does not demonstrate execution of its fake system instruction. | Add paired controls with and without the instruction to distinguish a scoring weakness from instruction-following claims. |
| Criterion 4 now misses | Label mapping requires at least 0.80, above every score in the original six-sample set. | Keep the MISSED verdict. Use a separate exploratory coverage set later without replacing or retroactively passing the original fixed test. |
| Criterion 5 still misses | Style averages barely separate the two groups; equal weighting reduces the model's limited separation. Threshold changes cannot alter the gap. | Examine the style features and weights using more diverse, length-matched data and a separate held-out set. A model-only gap of 0.14888 still misses 0.25 here. |
| MF05 and MF06 still return scored judgments, now unsure | Type and length validation do not establish that the input contains usable prose. The style fallback is 0.5. | Add explicit insufficient-evidence handling and test repeated-character and emoji-only inputs. |
| MF07 now receives unsure, but language support is unresolved | Arabic words are not recognized by the style tokenizer; the model has not been validated here for this language. | Test language-appropriate tokenization and evaluation, and abstain from unsupported authorship judgments. Arabic itself is not invalid input. |
| FP08 is still rejected | The 50-character minimum excludes a genuine short human submission. | Consider accepting short work with an insufficient-evidence message instead of applying an authorship label. |
| Rate limits can be bypassed or reset | Creator IDs are caller-supplied and counters are in memory. | Use authenticated identities and persistent counters if deployed. |
| Appeal detail is only approximated by word count | Twenty-five words can still contain weak or repetitive claims. | Provide a real human review workflow and assess the evidence itself. |
| Evaluation generalization is limited | Human excerpts share one essay and include quotations; AI and human lengths/topics are unmatched. Coverage includes calibration examples. | Add writing from different tasks and topics with recorded provenance and a separately held-out evaluation set. |

I stopped after the one threshold change so that the before and after remain
comparable and the effect of that change can be identified. The other possible
fixes above were not implemented during this measurement.

**The trade I'd make if this ran for real:**

I would favor fewer wrong accusations and allow more writing to remain unsure,
with a meaningful appeal and human review process. The site would bear more
review work and miss some AI-generated writing, rather than making real writers
bear the cost of an automated accusation.

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