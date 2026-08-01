"""Subject-relevance filter for harvested questions.

Why this exists
---------------
Two guides shipped that had nothing to do with the directory: "What are some
hidden free gems in Dallas?" and "Where to walk indoors in Dallas?" They were
not authored by mistake. Google's People Also Ask box, queried for "cold plunge
Dallas", returns questions about Dallas — the city, not the practice — and the
harvester accepted every one of them. Every metro seeds the same local queries,
so this is not a Dallas problem and deleting the Dallas seed would only have
moved it to whichever metro drifted next.

So the filter is on SUBJECT, not on geography: a harvested question has to be
about cold plunge, sauna, contrast therapy, or recovery to be kept.

Direction of failure
--------------------
Deliberately strict. A rejected question costs a stub that nobody had written
yet and that the next harvest can surface again. An accepted off-topic question
costs a published page — travel content sitting in a health directory under a
byline, with an affiliate block underneath it. The asymmetry is not close.

Kept dependency-free (no bs4, no crawl4ai) so the tests can import it directly.
"""
import re
import unicodedata

# Substring matches against the normalized question. Substrings rather than
# whole words so "saunas", "plunges" and "plunging" all land without a stemmer.
_SUBJECT_TERMS = (
    # cold
    "cold plunge", "coldplunge", "cold-plunge", "cold water", "cold-water",
    "cold immersion", "cold exposure", "cold therapy", "cold tub",
    "ice bath", "icebath", "ice-bath", "plunge", "plunging",
    "cryotherapy", "cryo", "wim hof", "chill tub",
    # heat
    "sauna", "steam room", "steam bath", "banya", "sweat lodge", "infrared",
    "heat therapy", "heat exposure", "hot tub", "thermotherapy", "sweat",
    # combined + adjacent practice
    "contrast therapy", "contrast bath", "contrast shower", "hot and cold",
    "hot-cold", "recovery", "doms", "sore muscle", "muscle soreness",
    "thermoregulation", "hormesis", "hormetic",
)


def _normalize(text: str) -> str:
    """Lowercase, strip accents, collapse punctuation to spaces."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_on_topic(question: str) -> bool:
    """True if the question is about what this directory covers.

    >>> is_on_topic("How cold is a cold plunge in Denver?")
    True
    >>> is_on_topic("What are some hidden free gems in Dallas?")
    False
    """
    if not question or not question.strip():
        return False
    norm = _normalize(question)
    # Terms are already lowercase and punctuation-free except for spaces and
    # hyphens; normalize them the same way so "cold-plunge" matches "cold plunge".
    return any(_normalize(term) in norm for term in _SUBJECT_TERMS)


def filter_on_topic(questions: list) -> tuple:
    """Split harvested records into (kept, rejected) on subject relevance."""
    kept, rejected = [], []
    for q in questions:
        text = q.get("question", "") if isinstance(q, dict) else str(q)
        (kept if is_on_topic(text) else rejected).append(q)
    return kept, rejected
