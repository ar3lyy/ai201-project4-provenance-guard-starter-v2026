"""
Signal two: the style signal.

Signal one measures how predictable text is to a local language model.
This one measures it *as text* — the shape of it, without understanding a word.

Three measures are implemented below:

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much selected punctuation appears?

These are experimental heuristics, not proof of authorship. Both human and
AI writing can have consistent sentences, repeated vocabulary, or sparse
punctuation.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures ──────────────────────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    How much sentence length varies.

    Returns:
        The sample standard deviation of sentence word counts divided by
        their mean. Higher means more variation. This can exceed 1.

    A one-sentence submission has no measurable spread, so this function
    returns 0.0 when fewer than two nonempty sentences are available.
    The style signal handles that case by returning a neutral score.
    """
    lengths = [
        len(words(sentence))
        for sentence in sentences(text)
        if words(sentence)
    ]

    if len(lengths) < 2:
        return 0.0

    return statistics.stdev(lengths) / statistics.mean(lengths)


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words.

    Returns:
        A float between 0 and 1. Higher means more varied vocabulary.
        Empty text returns 0.0.

    Worth knowing before you rely on it: this measure falls as text gets
    longer, because common words repeat. Two texts of different lengths aren't
    directly comparable on it, and if your test inputs vary a lot in length,
    that alone can look like a signal.
    """
    tokens = words(text)

    if not tokens:
        return 0.0

    return len(set(tokens)) / len(tokens)


def punctuation_density(text: str) -> float:
    """
    How much selected punctuation appears, relative to length.

    Returns:
        The number of selected punctuation marks divided by the number of
        non-whitespace characters. Empty text returns 0.0.

    Counts commas, semicolons, colons, question marks, exclamation marks,
    dashes, parentheses, and square brackets. Full stops and apostrophes
    are excluded.
    """
    characters = [
        character for character in text
        if not character.isspace()
    ]

    if not characters:
        return 0.0

    punctuation = sum(
        character in ",;:!?—–-()[]"
        for character in characters
    )

    return punctuation / len(characters)


# ── Combining them ───────────────────────────────────────────────────────────

def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. Higher means more AI-like.

    Each component is converted to a value between 0 and 1:

      1. Sentence spread: 1 minus spread, with spread capped at 1.
         Less sentence variation produces a higher component score.
      2. Vocabulary: 1 minus the type-token ratio.
         More repeated vocabulary produces a higher component score.
      3. Punctuation: 1 minus density divided by 0.05, capped at 1.
         Less selected punctuation produces a higher component score.

    The components receive weights of 0.50, 0.30, and 0.20 respectively.
    These weights and the 0.05 punctuation scale are heuristic choices,
    not values established by validation.

    Text with fewer than 20 words or two nonempty sentences receives 0.5
    because there is too little evidence for these measurements.

    Test it on the four calibration inputs from Milestone 4 — clearly AI,
    clearly human, plain conventional human writing, lightly-edited AI —
    before you trust it.
    """
    tokens = words(text)
    sentence_count = sum(
        bool(words(sentence))
        for sentence in sentences(text)
    )

    if len(tokens) < 20 or sentence_count < 2:
        return 0.5

    spread = sentence_length_spread(text)
    variety = type_token_ratio(text)
    density = punctuation_density(text)

    spread_score = 1.0 - min(spread, 1.0)
    repetition_score = 1.0 - variety
    punctuation_score = 1.0 - min(density / 0.05, 1.0)

    score = (
        0.50 * spread_score
        + 0.30 * repetition_score
        + 0.20 * punctuation_score
    )

    return round(max(0.0, min(score, 1.0)), 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
    print("\nStyle measurements are heuristics, not proof of authorship.")