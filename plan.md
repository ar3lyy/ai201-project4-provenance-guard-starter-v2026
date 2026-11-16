# Provenance Guard Plan

This is my planned design before implementation. The scores and labels below are examples, not actual test results.

## Submission Path

1. A writer sends their writing and creator ID to POST /submit.
2. The service checks that the JSON contains nonempty strings for text and creator_id. It creates a unique content_id for a valid submission.
3. detector.model_signal(text) measures how predictable the text is and returns a score from 0 to 1.
4. stylometry.style_signal(text) measures sentence length variation, word variety, and punctuation density. It returns another score from 0 to 1.
5. scoring.combine_signals combines the two scores. Higher combined scores mean the text looks more AI-like.
6. scoring.score_to_label turns the combined score into an AI, human, or unsure label written in plain language.
7. The service records the decision and scores in the audit log, then returns the content_id, guess, confidence, label, and both signal scores.

The writer can use the content_id to appeal the decision.

## Signal One: Local Model

The first signal is detector.model_signal(text). It uses a local language model to measure how predictable the writing is. AI-generated writing may use common patterns that the model finds easy to predict.

Its blind spot is that predictable writing can also be written by a person. Someone using simple vocabulary, writing formally, or writing in a second language could receive a high AI score. Unusual AI-generated writing could also receive a low score. This signal cannot prove who wrote something.

## Signal Two: Stylometry

The second signal is stylometry.style_signal(text). I plan to measure sentence length variation, the ratio of unique words to total words, and punctuation density.

These patterns might differ between human and AI writing because some generated writing has repeated words or consistently structured sentences. However, human writing can have those patterns too.

This signal cannot understand what the writing means. Typos, punctuation changes, quotations, or splitting sentences can change its score without changing the main content. Short passages may also provide too little text for reliable measurements.

## False-Positive Scenario

A writer submits a paragraph they wrote themselves. Their writing uses simple words and similar sentence lengths. For this planned example, the combined score is 0.82 and the system gives it an AI label.

A possible label is: "Our automated checks suggest this writing may be AI-generated, but they can be wrong. If you wrote it yourself, you can appeal this decision."

The writer sends the submission's content_id and an explanation to POST /appeal. For example, they could explain their writing process and mention that they have earlier drafts.

The service checks that the content_id exists, records the explanation, and changes the item's status to under_review. It confirms that the appeal was recorded. It does not automatically score the writing again or claim that a person has already reviewed it.

Because a wrong accusation can affect a real writer, I want the unsure range to give the system room to admit uncertainty. I will decide and document the final thresholds before testing the completed scoring system.

## Endpoint Contracts

### POST /submit

The request must be a JSON object containing:

- text: a nonempty string containing the writing.
- creator_id: a nonempty string identifying the writer.

Example request:

{
  "text": "This is a paragraph I wrote.",
  "creator_id": "arely"
}

A successful response will use HTTP 200 and contain:

- content_id: a unique string identifying the submission.
- guess: "ai", "human", or "unsure".
- confidence: the combined score from 0 to 1, where higher means more AI-like.
- label: the full message shown to the reader.
- model_score: the first signal's score from 0 to 1.
- style_score: the second signal's score from 0 to 1.

The confidence field represents the combined AI-likeness score. It is not a proven probability that AI wrote the text.

Malformed JSON, missing fields, incorrect field types, and blank required fields will return HTTP 400 with an error and a readable message. I plan to limit text to 10,000 characters; longer text will return HTTP 413.

### POST /appeal

The request must be a JSON object containing:

- content_id: the ID returned by a successful submission.
- reasoning: a nonempty string explaining why the writer disputes the decision.

Example request:

{
  "content_id": "<ID returned by /submit>",
  "reasoning": "I wrote this myself and have earlier drafts."
}

A successful response will use HTTP 200 and contain:

- content_id: the ID of the appealed submission.
- status: "under_review".
- message: confirmation that the appeal was recorded.

Missing, blank, or incorrectly typed fields will return HTTP 400. A content_id that does not exist will return HTTP 404.

## Audit Log

Each submission will be recorded in logs/audit.jsonl with a timestamp, content_id, creator_id, guess, both signal scores, combined confidence score, and status.

An appeal will add a linked entry containing the content_id, the writer's reasoning, a timestamp, and the under_review status. The original decision will remain in the log so the history can be checked.