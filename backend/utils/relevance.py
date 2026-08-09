"""Candidate answer relevance and gibberish detection utility."""

import re

_VOWELS = frozenset("aeiouyAEIOUY")

# Common phrases, evasions, greetings, or non-technical noise that do not address technical interview questions
_EXPLICIT_EVASIONS = (
    "don't know",
    "dont know",
    "no idea",
    "not sure",
    "idk",
    "pass",
    "skip",
    "whatever",
    "who cares",
    "i don't care",
    "i dont care",
    "nothing",
    "none",
    "n/a",
    "no",
    "nah",
    "bye",
    "goodbye",
    "exit",
    "quit",
    "hello",
    "hi",
    "hey",
    "how are you",
    "who are you",
    "what is your name",
    "tell me a joke",
    "foo",
    "bar",
    "baz",
    "test",
    "123",
    "abc",
    "xyz",
)


def is_irrelevant_or_gibberish(
    answer: str, question: str = "", competency: str = ""
) -> tuple[bool, str]:
    """Determine if a candidate answer is irrelevant, off-topic, evasive, or gibberish.

    Returns:
        tuple[bool, str]: (is_irrelevant, reason_type)
        where reason_type is 'empty', 'evasion', 'gibberish', or 'off_topic'.
    """
    text = (answer or "").strip()
    if not text:
        return True, "empty"

    lowered = text.lower()
    clean_words = [w for w in re.findall(r"[a-z0-9']+", lowered)]

    if not clean_words:
        return True, "gibberish"

    # 1. Check for gibberish FIRST (words > 3 chars with no vowels, or repeated keyboard patterns)
    gibberish_count = 0
    keyboard_patterns = {
        "asdf",
        "asdfgh",
        "asdfghjkl",
        "qwerty",
        "qwertyuiop",
        "zxcvbnm",
        "jgfjhgjfh",
    }

    for w in clean_words:
        if len(w) > 3 and not any(char in _VOWELS for char in w):
            gibberish_count += 1
        elif any(pat in w for pat in keyboard_patterns):
            gibberish_count += 1

    if gibberish_count > 0 and gibberish_count >= (len(clean_words) / 2):
        return True, "gibberish"

    # Check overall vowel ratio for non-whitespace text
    non_space = re.sub(r"[^a-z]", "", lowered)
    if non_space and len(non_space) > 4:
        vowel_count = sum(1 for c in non_space if c in _VOWELS)
        if vowel_count / len(non_space) < 0.15:  # English text normally has ~35-40% vowels
            return True, "gibberish"

    # 2. Check for explicit evasions / off-topic phrases
    for evasion in _EXPLICIT_EVASIONS:
        if (
            lowered == evasion
            or lowered.startswith(evasion + " ")
            or lowered.endswith(" " + evasion)
        ):
            return True, "evasion"

    # Short evasive phrases (< 4 words) containing evasions/noise
    if len(clean_words) <= 4:
        if any(w in _EXPLICIT_EVASIONS for w in clean_words):
            return True, "evasion"

    return False, ""
