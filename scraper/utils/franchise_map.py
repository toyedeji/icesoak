"""Franchise brand → modality map (shared, dependency-free).

Two consumers:
  * crawlers/franchise.py looks up modalities by an EXACT franchise brand name
    (``BRAND_MODALITIES.get(brand.lower())``) for the location pages it scrapes.
  * processors/merger.py backfills modalities by SUBSTRING match on a studio's
    name (``modalities_for_name``) when a scrape returned an empty list. This is
    what makes known franchises get tagged automatically on every future run,
    instead of relying on a one-off enrichment pass over studios.json.

Tokens are canonical (match utils/schema.VALID_MODALITIES and the frontend):
cold_plunge, sauna, sauna_traditional, sauna_infrared, contrast, cryo,
red_light, compression, iv.
"""

# The five brands the franchise crawler visits directly, keyed by exact
# brand.lower(). Preserved verbatim so crawler behaviour is unchanged.
_EXISTING_BRAND_MODALITIES = {
    "sweathouz": ["sauna_infrared", "cold_plunge"],
    "perspire sauna studio": ["sauna_infrared"],
    "restore hyper wellness": ["cryo", "red_light", "compression", "iv"],
    "pause": ["sauna_infrared", "cold_plunge", "contrast"],
    "contrast studio": ["sauna_infrared", "cold_plunge", "contrast"],
}

# Substring-matchable brand fragments → modalities. Grown from the studios.json
# enrichment pass. A studio name that contains one of these keys is tagged with
# its modalities when the crawl couldn't derive any itself.
_NAME_MODALITIES = {
    "sweathouz":          ["sauna_infrared", "cold_plunge", "contrast"],
    "swthz":              ["sauna_infrared", "cold_plunge", "contrast"],
    "perspire sauna":     ["sauna_infrared"],
    "pure sweat":         ["sauna_infrared", "cold_plunge"],
    "urban sweat":        ["sauna_infrared", "cold_plunge"],
    "glow sauna":         ["sauna_infrared"],
    "pause studio":       ["sauna_infrared", "cold_plunge", "contrast"],
    "pause venice":       ["sauna_infrared", "cold_plunge"],
    "city sweats":        ["sauna_infrared", "cold_plunge", "contrast"],
    "sauna house":        ["sauna_traditional", "cold_plunge"],
    "bywater sauna":      ["sauna_traditional"],
    "hothouse spa":       ["sauna_traditional", "cold_plunge"],
    "naosu":              ["sauna_infrared"],
    "ritual community":   ["sauna_traditional"],
    "seek sauna":         ["sauna_infrared"],
    "sek sauna":          ["sauna_infrared"],
    "contrast studio":    ["sauna_infrared", "cold_plunge", "contrast"],
    "formation sauna":    ["sauna_infrared", "cold_plunge"],
    "surge sauna":        ["sauna_infrared", "cold_plunge", "contrast"],
    "dtxfy":              ["sauna_infrared"],
    "elev8 infrared":     ["sauna_infrared"],
    "sweatheory":         ["sauna_infrared"],
    "r3 experience":      ["cold_plunge", "cryo"],
    "r3 spa":             ["cold_plunge", "sauna_infrared"],
    "r3 cryo":            ["cryo", "cold_plunge"],
    "icebox cryo":        ["cryo", "cold_plunge"],
    "icebox":             ["cryo", "cold_plunge"],
    "cryobar":            ["cryo"],
    "cryohealthcare":     ["cryo", "cold_plunge"],
    "cryo tempe":         ["cryo"],
    "cryo miami":         ["cryo"],
    "cryo boost":         ["cryo"],
    "icryo":              ["cryo"],
    "orange cryo":        ["cryo"],
    "restore hyper":      ["cold_plunge", "cryo", "contrast"],
    "restore hy":         ["cold_plunge", "cryo"],
    "beem light":         ["sauna_infrared"],
    "campfire sauna":     ["sauna_traditional"],
    "oak st. sauna":      ["sauna_traditional"],
    "riverwalk sauna":    ["sauna_traditional"],
    "vihta sauna":        ["sauna_traditional"],
    "von sauna":          ["sauna_traditional"],
    "salt & cedar":       ["sauna_traditional"],
    "sauna hut":          ["sauna_traditional"],
    "sauna sanctuary":    ["sauna_traditional"],
    "sunsauna":           ["sauna_infrared"],
    "fyre sauna":         ["sauna_infrared"],
    "wild haus":          ["sauna_traditional"],
    "icepass":            ["cold_plunge", "sauna"],
    "westside sweat":     ["sauna_infrared", "cold_plunge"],
    "melt well":          ["sauna_infrared", "cold_plunge"],
    "optimal health":     ["sauna_infrared"],
    "eleos float":        ["sauna_infrared", "cold_plunge"],
    "flow state cryo":    ["cryo", "cold_plunge"],
    "livecolder":         ["cold_plunge"],
    "subzero plunge":     ["cold_plunge"],
    "cold plunge austin": ["cold_plunge"],
    "cold plunge philly": ["cold_plunge"],
    "ocean lab":          ["cold_plunge", "contrast"],
    "ulu recovery":       ["cold_plunge", "sauna"],
    "pure recovery":      ["cold_plunge", "cryo"],
    "king spa":           ["sauna_traditional", "cold_plunge"],
    "polar star":         ["sauna_traditional", "cold_plunge"],
    "chicago sweatlodge": ["sauna_traditional"],
    "contrast hot":       ["cold_plunge", "sauna", "contrast"],
    "fire and ice":       ["sauna", "cold_plunge", "contrast"],
    "warriors garden":    ["cold_plunge", "sauna"],
    "warrior garden":     ["cold_plunge", "sauna"],
    "aura sauna":         ["sauna_infrared"],
    "sauna phl":          ["sauna_infrared"],
    "sauna moon":         ["sauna_traditional"],
    "crockpot sauna":     ["sauna_traditional"],
    "halsa nordic":       ["sauna_traditional"],
    "portal":             ["sauna_traditional", "cold_plunge", "contrast"],
    "therma haus":        ["sauna", "cold_plunge", "contrast"],
    "havana sauna":       ["sauna_traditional"],
    "simply sauna":       ["sauna_infrared"],
    "apres sauna":        ["sauna_infrared"],
    "dear sauna":         ["sauna_traditional"],
    "sauna room":         ["sauna_infrared"],
    "sauna to-go":        ["sauna_traditional"],
    "nomadic fire":       ["sauna_traditional"],
    "peak recovery":      ["cold_plunge", "sauna"],
    "urban unwind":       ["sauna_infrared"],
    "sweat shack":        ["sauna_infrared", "cold_plunge"],
    "contrast club":      ["sauna", "cold_plunge", "contrast"],
    "sweat plunge":       ["sauna", "cold_plunge", "contrast"],
    "rok spas":           ["sauna", "cold_plunge"],
    "naos":               ["cold_plunge"],
    "blue recovery":      ["cold_plunge", "sauna"],
    "ice room":           ["cold_plunge"],
    "recovery lounge":    ["cold_plunge", "sauna"],
    "recovery space":     ["cold_plunge"],
    "recovery studio":    ["cold_plunge", "sauna"],
    "nexus recovery lab": ["cold_plunge", "cryo"],
    "helix performance":  ["cold_plunge", "cryo"],
    "electric ice":       ["cryo", "cold_plunge"],
    "rivera performance": ["cold_plunge"],
    "royal standard":     ["sauna"],
    "five star sauna":    ["sauna_infrared"],
    "infrared sauna store": ["sauna_infrared"],
    "miami infrared":     ["sauna_infrared"],
    "cloud nine":         ["sauna_infrared", "cold_plunge"],
    "polar star spa":     ["sauna_traditional", "cold_plunge"],
    "hothouse":           ["sauna_traditional", "cold_plunge"],
    "seattle sauna":      ["sauna_traditional"],
    "dtxfy infrared":     ["sauna_infrared"],
}

# Merged lookup: the substring map wins on overlapping keys (it carries the more
# complete, canonical modality set), while every existing brand key is preserved.
BRAND_MODALITIES = {**_EXISTING_BRAND_MODALITIES, **_NAME_MODALITIES}

# Keys long enough to substring-match without false positives, longest first so
# the most specific brand wins.
_MIN_KEY_LEN = 5
_KEYS_BY_LENGTH = sorted(
    (k for k in _NAME_MODALITIES if len(k) >= _MIN_KEY_LEN),
    key=len,
    reverse=True,
)


def modalities_for_name(name: str) -> list:
    """Return canonical modalities for a studio whose name contains a known
    franchise fragment, or [] if none match. Longest match wins."""
    if not name:
        return []
    low = name.lower()
    for key in _KEYS_BY_LENGTH:
        if key in low:
            return list(_NAME_MODALITIES[key])
    return []
