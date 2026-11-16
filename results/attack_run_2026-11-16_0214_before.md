# Attack run — before

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-16 02:14
- Auto-marked BROKE (5xx, crash, no response): **0**
- Left for you to judge: **56**

The Verdict column is blank where a script can't honestly decide. Whether
an evasion worked depends on where you put your thresholds — read the
`targets` column, look at what came back, and write HELD or BROKE yourself.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `b3810c1a-a8ac-4000-bb6f-f2360bf24f95` | unsure | 0.397 |  |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `5096a5bb-4de2-40b6-935c-aa397154c885` | unsure | 0.448 |  |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `68c33533-9e80-44bc-8457-24d41f428bbd` | unsure | 0.578 |  |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `86f4437d-df12-4f53-b285-4796d6a0e7a5` | unsure | 0.614 |  |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `35c4ccf4-e314-4ec1-9a61-5171134544fb` | human | 0.340 |  |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `078ec5ba-7ed8-4673-87b3-55c5f65e8186` | unsure | 0.413 |  |
| EV07 | evasion | signal two: padding with punctuation | 200 | `50dbeb4a-3bad-4734-8bbc-ca32b2038f92` | unsure | 0.543 |  |
| EV08 | evasion | signal one: text below the token window | 200 | `a05bcf52-77a2-4d18-9fea-60062262883a` | unsure | 0.373 |  |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `4e72f681-b9ef-4555-9424-1fd502d49260` | unsure | 0.591 |  |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `df4f9920-0a25-46b6-9705-c572c00e5fc2` | ai | 0.843 |  |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `61c6cfd8-e7aa-4beb-9392-c640e9ee7ba2` | unsure | 0.579 |  |
| FP02 | false_positive | human writing in a formal register | 200 | `b5015d1c-b57a-4399-8cc9-75adb1ba9f94` | ai | 0.698 |  |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `53117377-ba35-4662-9df5-5c00ca047981` | ai | 0.712 |  |
| FP04 | false_positive | a student essay written to a rubric | 200 | `756d529c-7bb4-4cbb-8b30-cb622627379d` | ai | 0.698 |  |
| FP05 | false_positive | technical documentation written by a person | 200 | `b6dc5863-d43b-4b4f-8c09-83ec5ad1759e` | ai | 0.731 |  |
| FP06 | false_positive | a person imitating a formal template | 200 | `5eca2a25-171c-4d54-bb08-31d8ff803c95` | ai | 0.694 |  |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `5f5c107e-f889-40e3-96c5-e48127a6bb5b` | ai | 0.675 |  |
| FP08 | false_positive | very short genuine human submission | 400 | `—` | — | — |  |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `82bf1934-f4ff-4397-8090-152b1f4cea47` | unsure | 0.426 |  |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `8513e4a0-bc7e-47e0-abcd-15213c689a83` | human | 0.282 |  |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `5b16daae-5327-4c4d-baa5-8ae1ffeaa724` | unsure | 0.556 |  |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `840e16ad-f8a2-439d-8d34-a151b9b408f5` | unsure | 0.486 |  |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `092fd0ce-53e9-40ec-9879-f177531e1841` | unsure | 0.493 |  |
| PI06 | prompt_injection | instruction plus real human text | 200 | `edf18a0e-9c34-4807-8cd2-6a401afbccdd` | unsure | 0.553 |  |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — |  |
| MF02 | malformed | text is a single character | 400 | `—` | — | — |  |
| MF03 | malformed | text is control characters | 400 | `—` | — | — |  |
| MF04 | malformed | text is only punctuation | 400 | `—` | — | — |  |
| MF05 | malformed | text is a very long single word | 200 | `20fcfcee-e1c5-493b-8886-dbe6c25f1805` | ai | 0.749 |  |
| MF06 | malformed | text is emoji only | 200 | `c40bbc86-1fb0-4d1e-a1c9-ffc442e388d6` | ai | 0.748 |  |
| MF07 | malformed | text is right-to-left script | 200 | `28afc9d0-d48b-4368-9d96-2c053f19cb2f` | ai | 0.703 |  |
| MF08 | malformed | text is 60,000 characters | 413 | `—` | — | — |  |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — |  |
| RQ02 | malformed | no creator_id | 400 | `—` | — | — |  |
| RQ03 | malformed | text is a number | 400 | `—` | — | — |  |
| RQ04 | malformed | text is a list | 400 | `—` | — | — |  |
| RQ05 | malformed | text is null | 400 | `—` | — | — |  |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — |  |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — |  |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — |  |
| RQ09 | malformed | body is empty | 400 | `—` | — | — |  |
| RQ10 | malformed | body is form-encoded, not JSON | 400 | `—` | — | — |  |
| RQ11 | malformed | body is JSON claiming to be plain text | 400 | `—` | — | — |  |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — |  |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | `d3c1fbe2-0157-44c7-8380-4bea240c71ae` | human | 0.264 |  |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | `da61cb3e-88b7-4938-95cb-80b3a3ff3789` | human | 0.264 |  |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | `cfbe517d-48e2-44ef-8db3-246a4f28d430` | human | 0.264 |  |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | `a6c4baf4-9ad4-457a-a1a0-ceee92d25976` | human | 0.264 |  |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | `2c4302af-7a0a-40bd-a1dc-9bbd919b1ce7` | human | 0.264 |  |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 200 | `3baddf03-a070-4a54-b56d-4c7c89d1382f` | human | 0.264 |  |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 200 | `b574bdb1-d4e3-4014-a10a-9123c6653578` | human | 0.264 |  |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 200 | `2cc5c735-33db-4e5f-b1df-fade5934f6f3` | human | 0.264 |  |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 200 | `566a7447-3a4c-4e3d-8058-52221486ffaf` | human | 0.264 |  |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 200 | `235db0aa-e399-41d7-80d2-11c235d8eed5` | human | 0.264 |  |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `evasion` | 10 | 0 | 10 |
| `false_positive` | 8 | 0 | 8 |
| `flood_same_creator` | 12 | 0 | 12 |
| `malformed` | 20 | 0 | 20 |
| `prompt_injection` | 6 | 0 | 6 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### EV01 — `evasion`

*Targeting:* signal two: typos raise word variety

```json
{
  "id": "EV01",
  "status": 200,
  "content_id": "b3810c1a-a8ac-4000-bb6f-f2360bf24f95",
  "creator_id": "attacker_EV01",
  "guess": "unsure",
  "confidence": 0.39705,
  "model_score": 0.1635,
  "style_score": 0.6306,
  "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### EV02 — `evasion`

*Targeting:* signal two: broken-up sentences raise length spread

```json
{
  "id": "EV02",
  "status": 200,
  "content_id": "5096a5bb-4de2-40b6-935c-aa397154c885",
  "creator_id": "attacker_EV02",
  "guess": "unsure",
  "confidence": 0.44825000000000004,
  "model_score": 0.5943,
  "style_score": 0.3022,
  "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### EV03 — `evasion`

*Targeting:* signal two: a pasted quotation changes the shape

```json
{
  "id": "EV03",
  "status": 200,
  "content_id": "68c33533-9e80-44bc-8457-24d41f428bbd",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "confidence": 0.57845,
  "model_score": 0.6662,
  "style_score": 0.4907,
  "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### EV04 — `evasion`

*Targeting:* signal one: unusual words raise perplexity

```json
{
  "id": "EV04",
  "status": 200,
  "content_id": "86f4437d-df12-4f53-b285-4796d6a0e7a5",
  "creator_id": "attacker_EV04",
  "guess": "unsure",
  "confidence": 0.6140000000000001,
  "model_score": 0.6114,
  "style_score": 0.6166,
  "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### EV05 — `evasion`

*Targeting:* both signals: heavy human editing pass

```json
{
  "id": "EV05",
  "status": 200,
  "content_id": "35c4ccf4-e314-4ec1-9a61-5171134544fb",
  "creator_id": "attacker_EV05",
  "guess": "human",
  "confidence": 0.3397,
  "model_score": 0.3212,
  "style_score": 0.3582,
  "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
  "error": null,
  "verdict": ""
}
```

### EV06 — `evasion`

*Targeting:* signal two: one very long sentence and one very short

```json
{
  "id": "EV06",
  "status": 200,
  "content_id": "078ec5ba-7ed8-4673-87b3-55c5f65e8186",
  "creator_id": "attacker_EV06",
  "guess": "unsure",
  "confidence": 0.4129,
  "model_score": 0.5727,
  "style_score": 0.2531,
  "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### EV07 — `evasion`

*Targeting:* signal two: padding with punctuation

```json
{
  "id": "EV07",
  "status": 200,
  "content_id": "50dbeb4a-3bad-4734-8bbc-ca32b2038f92",
  "creator_id": "attacker_EV07",
  "guess": "unsure",
  "confidence": 0.5431,
  "model_score": 0.5862,
  "style_score": 0.5,
  "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### EV08 — `evasion`

*Targeting:* signal one: text below the token window

```json
{
  "id": "EV08",
  "status": 200,
  "content_id": "a05bcf52-77a2-4d18-9fea-60062262883a",
  "creator_id": "attacker_EV08",
  "guess": "unsure",
  "confidence": 0.3726,
  "model_score": 0.2452,
  "style_score": 0.5,
  "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### EV09 — `evasion`

*Targeting:* both: AI text with a human opening paragraph bolted on

```json
{
  "id": "EV09",
  "status": 200,
  "content_id": "4e72f681-b9ef-4555-9424-1fd502d49260",
  "creator_id": "attacker_EV09",
  "guess": "unsure",
  "confidence": 0.5909,
  "model_score": 0.7042,
  "style_score": 0.4776,
  "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### EV10 — `evasion`

*Targeting:* signal two: repeated stanza structure

```json
{
  "id": "EV10",
  "status": 200,
  "content_id": "df4f9920-0a25-46b6-9705-c572c00e5fc2",
  "creator_id": "attacker_EV10",
  "guess": "ai",
  "confidence": 0.84305,
  "model_score": 0.9792,
  "style_score": 0.7069,
  "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "61c6cfd8-e7aa-4beb-9392-c640e9ee7ba2",
  "creator_id": "attacker_FP01",
  "guess": "unsure",
  "confidence": 0.57855,
  "model_score": 0.6175,
  "style_score": 0.5396,
  "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### FP02 — `false_positive`

*Targeting:* human writing in a formal register

```json
{
  "id": "FP02",
  "status": 200,
  "content_id": "b5015d1c-b57a-4399-8cc9-75adb1ba9f94",
  "creator_id": "attacker_FP02",
  "guess": "ai",
  "confidence": 0.6977,
  "model_score": 0.7387,
  "style_score": 0.6567,
  "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### FP03 — `false_positive`

*Targeting:* a non-native English speaker writing carefully

```json
{
  "id": "FP03",
  "status": 200,
  "content_id": "53117377-ba35-4662-9df5-5c00ca047981",
  "creator_id": "attacker_FP03",
  "guess": "ai",
  "confidence": 0.7120500000000001,
  "model_score": 0.8051,
  "style_score": 0.619,
  "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### FP04 — `false_positive`

*Targeting:* a student essay written to a rubric

```json
{
  "id": "FP04",
  "status": 200,
  "content_id": "756d529c-7bb4-4cbb-8b30-cb622627379d",
  "creator_id": "attacker_FP04",
  "guess": "ai",
  "confidence": 0.69815,
  "model_score": 0.8329,
  "style_score": 0.5634,
  "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### FP05 — `false_positive`

*Targeting:* technical documentation written by a person

```json
{
  "id": "FP05",
  "status": 200,
  "content_id": "b6dc5863-d43b-4b4f-8c09-83ec5ad1759e",
  "creator_id": "attacker_FP05",
  "guess": "ai",
  "confidence": 0.73085,
  "model_score": 0.8005,
  "style_score": 0.6612,
  "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### FP06 — `false_positive`

*Targeting:* a person imitating a formal template

```json
{
  "id": "FP06",
  "status": 200,
  "content_id": "5eca2a25-171c-4d54-bb08-31d8ff803c95",
  "creator_id": "attacker_FP06",
  "guess": "ai",
  "confidence": 0.69385,
  "model_score": 0.8814,
  "style_score": 0.5063,
  "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### FP07 — `false_positive`

*Targeting:* human writing that repeats a phrase deliberately

```json
{
  "id": "FP07",
  "status": 200,
  "content_id": "5f5c107e-f889-40e3-96c5-e48127a6bb5b",
  "creator_id": "attacker_FP07",
  "guess": "ai",
  "confidence": 0.675,
  "model_score": 0.8816,
  "style_score": 0.4684,
  "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### FP08 — `false_positive`

*Targeting:* very short genuine human submission

```json
{
  "id": "FP08",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_FP08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### PI01 — `prompt_injection`

*Targeting:* instruction to ignore the check

```json
{
  "id": "PI01",
  "status": 200,
  "content_id": "82bf1934-f4ff-4397-8090-152b1f4cea47",
  "creator_id": "attacker_PI01",
  "guess": "unsure",
  "confidence": 0.4256,
  "model_score": 0.4625,
  "style_score": 0.3887,
  "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### PI02 — `prompt_injection`

*Targeting:* instruction disguised as a system message

```json
{
  "id": "PI02",
  "status": 200,
  "content_id": "8513e4a0-bc7e-47e0-abcd-15213c689a83",
  "creator_id": "attacker_PI02",
  "guess": "human",
  "confidence": 0.2816,
  "model_score": 0.2044,
  "style_score": 0.3588,
  "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
  "error": null,
  "verdict": ""
}
```

### PI03 — `prompt_injection`

*Targeting:* instruction wrapped in the writer's voice

```json
{
  "id": "PI03",
  "status": 200,
  "content_id": "5b16daae-5327-4c4d-baa5-8ae1ffeaa724",
  "creator_id": "attacker_PI03",
  "guess": "unsure",
  "confidence": 0.5564,
  "model_score": 0.5943,
  "style_score": 0.5185,
  "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### PI04 — `prompt_injection`

*Targeting:* attempt to make the label text hostile

```json
{
  "id": "PI04",
  "status": 200,
  "content_id": "840e16ad-f8a2-439d-8d34-a151b9b408f5",
  "creator_id": "attacker_PI04",
  "guess": "unsure",
  "confidence": 0.4864,
  "model_score": 0.4998,
  "style_score": 0.473,
  "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### PI05 — `prompt_injection`

*Targeting:* attempt to inject into the audit log

```json
{
  "id": "PI05",
  "status": 200,
  "content_id": "092fd0ce-53e9-40ec-9879-f177531e1841",
  "creator_id": "attacker_PI05",
  "guess": "unsure",
  "confidence": 0.4927,
  "model_score": 0.6401,
  "style_score": 0.3453,
  "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### PI06 — `prompt_injection`

*Targeting:* instruction plus real human text

```json
{
  "id": "PI06",
  "status": 200,
  "content_id": "edf18a0e-9c34-4807-8cd2-6a401afbccdd",
  "creator_id": "attacker_PI06",
  "guess": "unsure",
  "confidence": 0.55325,
  "model_score": 0.5583,
  "style_score": 0.5482,
  "label": "Our automated checks cannot confidently determine how this writing was created. This result is not a finding of wrongdoing. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### MF01 — `malformed`

*Targeting:* text is only whitespace

```json
{
  "id": "MF01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF02 — `malformed`

*Targeting:* text is a single character

```json
{
  "id": "MF02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF02",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF03 — `malformed`

*Targeting:* text is control characters

```json
{
  "id": "MF03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF05 — `malformed`

*Targeting:* text is a very long single word

```json
{
  "id": "MF05",
  "status": 200,
  "content_id": "20fcfcee-e1c5-493b-8886-dbe6c25f1805",
  "creator_id": "attacker_MF05",
  "guess": "ai",
  "confidence": 0.7488,
  "model_score": 0.9976,
  "style_score": 0.5,
  "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### MF06 — `malformed`

*Targeting:* text is emoji only

```json
{
  "id": "MF06",
  "status": 200,
  "content_id": "c40bbc86-1fb0-4d1e-a1c9-ffc442e388d6",
  "creator_id": "attacker_MF06",
  "guess": "ai",
  "confidence": 0.7484500000000001,
  "model_score": 0.9969,
  "style_score": 0.5,
  "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### MF07 — `malformed`

*Targeting:* text is right-to-left script

```json
{
  "id": "MF07",
  "status": 200,
  "content_id": "28afc9d0-d48b-4368-9d96-2c053f19cb2f",
  "creator_id": "attacker_MF07",
  "guess": "ai",
  "confidence": 0.7032,
  "model_score": 0.9064,
  "style_score": 0.5,
  "label": "Our automated checks suggest this writing may be AI-generated. These checks can be wrong. You can appeal this decision.",
  "error": null,
  "verdict": ""
}
```

### MF08 — `malformed`

*Targeting:* text is 60,000 characters

```json
{
  "id": "MF08",
  "status": 413,
  "content_id": null,
  "creator_id": "attacker_MF08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ01 — `malformed`

*Targeting:* no text field at all

```json
{
  "id": "RQ01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ02 — `malformed`

*Targeting:* no creator_id

```json
{
  "id": "RQ02",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ03 — `malformed`

*Targeting:* text is a number

```json
{
  "id": "RQ03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ04 — `malformed`

*Targeting:* text is a list

```json
{
  "id": "RQ04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ05 — `malformed`

*Targeting:* text is null

```json
{
  "id": "RQ05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ06 — `malformed`

*Targeting:* creator_id is an object

```json
{
  "id": "RQ06",
  "status": 400,
  "content_id": null,
  "creator_id": {
    "id": "x"
  },
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ07 — `malformed`

*Targeting:* body is a JSON array, not an object

```json
{
  "id": "RQ07",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ08 — `malformed`

*Targeting:* body is unparseable JSON

```json
{
  "id": "RQ08",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ09 — `malformed`

*Targeting:* body is empty

```json
{
  "id": "RQ09",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ10 — `malformed`

*Targeting:* body is form-encoded, not JSON

```json
{
  "id": "RQ10",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ11 — `malformed`

*Targeting:* body is JSON claiming to be plain text

```json
{
  "id": "RQ11",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ12 — `malformed`

*Targeting:* deeply nested JSON

```json
{
  "id": "RQ12",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ12",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_01 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_01",
  "status": 200,
  "content_id": "d3c1fbe2-0157-44c7-8380-4bea240c71ae",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.26435,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
  "error": null,
  "verdict": ""
}
```

### FL01_02 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_02",
  "status": 200,
  "content_id": "da61cb3e-88b7-4938-95cb-80b3a3ff3789",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.26435,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
  "error": null,
  "verdict": ""
}
```

### FL01_03 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_03",
  "status": 200,
  "content_id": "cfbe517d-48e2-44ef-8db3-246a4f28d430",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.26435,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
  "error": null,
  "verdict": ""
}
```

### FL01_04 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_04",
  "status": 200,
  "content_id": "a6c4baf4-9ad4-457a-a1a0-ceee92d25976",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.26435,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
  "error": null,
  "verdict": ""
}
```

### FL01_05 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_05",
  "status": 200,
  "content_id": "2c4302af-7a0a-40bd-a1dc-9bbd919b1ce7",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.26435,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
  "error": null,
  "verdict": ""
}
```

### FL01_06 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_06",
  "status": 200,
  "content_id": "3baddf03-a070-4a54-b56d-4c7c89d1382f",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.26435,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
  "error": null,
  "verdict": ""
}
```

### FL01_07 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_07",
  "status": 200,
  "content_id": "b574bdb1-d4e3-4014-a10a-9123c6653578",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.26435,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
  "error": null,
  "verdict": ""
}
```

### FL01_08 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_08",
  "status": 200,
  "content_id": "2cc5c735-33db-4e5f-b1df-fade5934f6f3",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.26435,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
  "error": null,
  "verdict": ""
}
```

### FL01_09 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_09",
  "status": 200,
  "content_id": "566a7447-3a4c-4e3d-8058-52221486ffaf",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.26435,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
  "error": null,
  "verdict": ""
}
```

### FL01_10 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_10",
  "status": 200,
  "content_id": "235db0aa-e399-41d7-80d2-11c235d8eed5",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.26435,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "Our automated checks suggest this writing was written by a person. These checks cannot verify authorship.",
  "error": null,
  "verdict": ""
}
```

### FL01_11 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_11",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_12 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_12",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```
