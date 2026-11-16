# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1. No false accusations on my human-written samples

Of 10 pieces I wrote myself, 0 should be labeled high-confidence AI in each of the three trials.

**Why this target:**

I chose zero because incorrectly labeling my writing as AI-generated could cause problems later and affect how people view my work. I want the system to leave room for uncertainty instead of making a false accusation.


---

## 2. Appeals require detailed reasoning and avoid duplicates

Across five appeal test cases in each of the three trials, the service should correctly handle all five. An appeal with at least 25 words of reasoning should be saved and change an existing submission’s status to under_review. Reasoning with fewer than 25 words should be rejected with a clear message. An identical explanation submitted again for the same content_id should not create another appeal entry, but a different explanation meeting the word minimum should be saved.

**Why this target:**

I want writers to explain why they disagree and describe supporting evidence, such as drafts or notes. Requiring at least 25 words encourages a fuller explanation, although length alone does not prove the evidence is convincing. Saving different explanations lets writers add information while avoiding repeated copies of the same appeal.

---

## 3. Invalid submissions return clear errors

In each of the three trials, all five invalid inputs—missing text, blank text, text with an incorrect data type, text shorter than 50 characters, and text longer than 10,000 characters—should return a clear JSON error without crashing the service. Input errors should return HTTP 400, except text over the maximum, which should return HTTP 413.

**Why this target:**

The system needs enough writing to evaluate, so I chose a minimum of 50 characters. The 10,000-character maximum limits how much text the service processes per request. Missing or invalid text should produce a message explaining what the writer needs to fix.

---

## 4. All three labels are reachable

Using the same set of six writing samples in each of the three trials, the results should include at least one high-confidence human label, one high-confidence AI label, and one unsure label in every trial.

**Why this target:**

All three labels should appear in actual submissions so I know the system can use each one. The unsure label matters because the system should be able to admit when it cannot confidently judge the writing.

---

## 5. Human and AI samples have separated average scores

Using five known human-written samples and five known AI-generated samples, the average combined score for AI-generated samples should be at least 0.25 higher than the average for human-written samples in each of the three trials.

**Why this target:**

I chose a gap of 0.25 because the scores should show a noticeable difference between the two groups. This checks whether the signals distinguish the groups on average, while my false-positive criterion separately checks for wrong accusations.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
