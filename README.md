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

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->

Provenance Guard is a local backend service that evaluates writing using two
different signals. Its scores describe patterns in the writing, not proof of
who wrote it.

The submission path is:

1. A writer sends `text` and `creator_id` to `POST /submit`.
2. The service checks the input and creates a unique `content_id`. Text must
   contain between 50 and 10,000 characters after surrounding whitespace is
   removed. The creator ID must be a nonempty string.
3. The local model measures how predictable the writing is.
4. The style signal measures sentence length variation, vocabulary repetition,
   and selected punctuation density.
5. The combining function averages the two signal scores.
6. The planned label function maps the combined score to a human, AI, or
   unsure label.
7. The service records the submission in the audit log and returns the ID,
   scores, guess, and label.

A writer will be able to appeal using the `content_id` and an explanation.
The planned appeal path records the explanation and changes the status to
`under_review`. It does not automatically decide whether the writer's evidence
is convincing.

**Current progress:** The submission route validates input, runs both signals,
combines their scores using equal weights, and records all three scores in
the audit log. Final labels and appeals are still in progress.

---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:**

`detector.model_signal(text)` uses the local GPT-2 model to measure how
predictable the text is. It converts that measurement into a score from 0 to 1.
Higher scores mean more AI-like according to this signal.

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

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

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

The starter thresholds are:

- Human: combined score at or below 0.35.
- Unsure: combined score above 0.35 and below 0.65.
- AI: combined score at or above 0.65.

The combined score is connected to the submission route. The final label
mapping is not connected yet, so the route still returns a temporary
`unsure` guess and a placeholder label.

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
They are not final labeled responses from the endpoint.

The model ranked the original AI passage above my human film paragraph,
while the style signal ranked them in the opposite order. My film paragraph
had low sentence length variation and repeated vocabulary, which increased
its style score.

With equal weights and the starter thresholds, my human film paragraph
would receive an AI label. The original AI passage would receive an unsure
label. This shows how the style signal can push a human submission above
the AI threshold.

My plain human-written morning paragraph also scored above the planned AI
threshold. The model found its wording predictable, while the style signal
measured very similar sentence lengths. Both signals leaned toward AI, so
averaging them did not prevent a false positive.

The edited garden passage received a higher model score than the original.
Editing does not necessarily reduce predictability. The passages also differ
in length, so these examples do not isolate editing as the cause.

These calibration examples show a risk to my zero-false-positive target.
They are not the full acceptance test results.

---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

Final label wording has not been implemented yet. The ranges below are the
planned starter settings.

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 ≤ score ≤ 0.35 | Not implemented yet. |
| unsure | 0.35 < score < 0.65 | Not implemented yet. |
| high-confidence AI | 0.65 ≤ score ≤ 1.00 | Not implemented yet. |

**Why I worded the "unsure" one this way:**

<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->

To be completed when I write and test the final labels.

---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

This is a real Milestone 4 submission with both signals connected.
The confidence field contains their average. The guess and label are
still placeholders.

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

```bash
$ curl -i --max-time 120 -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test submission to check that both signals return scores and the service combines them correctly.", "creator_id": "arely"}'
```

HTTP status: `200 OK`

```json
{
  "confidence": 0.28125,
  "content_id": "d9097043-f26a-4641-9967-3551dda7dee3",
  "guess": "unsure",
  "label": "Both signals are connected. Final labels are not connected yet.",
  "model_score": 0.0625,
  "style_score": 0.5
}
```

The average is `(0.0625 + 0.5) / 2 = 0.28125`. This sample has only one
sentence, so the style signal returns its neutral fallback of 0.5.

**An appeal**

Not implemented or tested yet. The request, response, and resulting log
entry will be added in Milestone 5.

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "...", "reasoning": "..."}'
```

```json

```

**What the log shows afterwards**

This is the actual log after the two-signal submission above, before any
appeal.

```bash
$ curl -i "http://127.0.0.1:5000/log?limit=1"
```

HTTP status: `200 OK`

```json
{
  "count": 1,
  "entries": [
    {
      "combined_score": 0.28125,
      "content_id": "d9097043-f26a-4641-9967-3551dda7dee3",
      "creator_id": "arely",
      "guess": "unsure",
      "label": "Both signals are connected. Final labels are not connected yet.",
      "model_score": 0.0625,
      "status": "pending_scoring",
      "style_score": 0.5,
      "timestamp": "2026-11-16T06:34:36+00:00"
    }
  ]
}
```

---

## How I Used AI

**Moment 1**

- **What I asked for:** Help getting the submission endpoint running and
  connecting the first signal to the audit log.
- **What came back:** A fixed JSON response to test the route first, followed
  by code for input validation, unique content IDs, the detector call, and
  audit logging.
- **What I changed:** I replaced the starter's 501 response, tested the fixed
  response, and then connected the real model signal. I checked that the
  returned content ID matched the audit log entry.

**Moment 2**

- **What I asked for:** A complete version of `stylometry.py` that kept the
  starter's layout and function names, followed by help connecting both
  signals.
- **What came back:** Implementations for sentence length spread, type-token
  ratio, punctuation density, and a weighted style score. AI also provided
  instructions for connecting the style score to the combining function and
  audit log.
- **What I changed:** I replaced the stub functions, tested four calibration
  passages, and connected both signals to `/submit`. I verified that the
  response and log contained both scores and their average. The calibration
  results showed false-positive risks that I recorded in this README.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**

<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```text

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