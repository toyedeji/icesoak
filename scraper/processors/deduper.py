import logging
import re
from typing import Optional

log = logging.getLogger(__name__)


def deduplicate(studios: list) -> list:
    """Deduplicate by google_place_id first, then by normalised name+address."""
    by_place_id: dict = {}
    by_name_addr: dict = {}
    orphans: list = []

    for studio in studios:
        place_id = studio.get("google_place_id")
        name_key = _name_addr_key(studio)

        if place_id:
            if place_id in by_place_id:
                _merge_into(by_place_id[place_id], studio)
            else:
                by_place_id[place_id] = studio
        elif name_key:
            if name_key in by_name_addr:
                _merge_into(by_name_addr[name_key], studio)
            else:
                by_name_addr[name_key] = studio
        else:
            orphans.append(studio)

    # Prevent double-counting records that appear in both indexes
    place_id_name_keys = {_name_addr_key(s) for s in by_place_id.values()}
    result = list(by_place_id.values())
    for key, studio in by_name_addr.items():
        if key not in place_id_name_keys:
            result.append(studio)
    result.extend(orphans)

    log.info("Deduplication: %d → %d records", len(studios), len(result))
    return result


def _name_addr_key(studio: dict) -> Optional[str]:
    name = re.sub(r"[^\w\s]", "", studio.get("name", "").lower()).strip()
    name = re.sub(r"\s+", " ", name)
    addr = studio.get("address") or ""
    addr_line = addr.split(",")[0].lower().strip()
    addr_line = re.sub(r"\s+", " ", addr_line)
    return f"{name}|{addr_line}" if name else None


def _merge_into(target: dict, source: dict) -> None:
    """Merge non-null fields from source into target; prefer target values."""
    for key, val in source.items():
        if key.startswith("_"):
            continue
        if not target.get(key) and val is not None:
            target[key] = val
        elif isinstance(val, list) and isinstance(target.get(key), list):
            for item in val:
                if item not in target[key]:
                    target[key].append(item)

    # Prefer the rating backed by more reviews
    s_reviews = source.get("google_reviews_count") or 0
    t_reviews = target.get("google_reviews_count") or 0
    if s_reviews > t_reviews:
        target["google_rating"] = source.get("google_rating")
        target["google_reviews_count"] = s_reviews
