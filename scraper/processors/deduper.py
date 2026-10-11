import logging
import re
from typing import Optional

from processors.identity import all_identity_keys

log = logging.getLogger(__name__)


def deduplicate(studios: list) -> list:
    """Collapse records that refer to the same business.

    Groups by any shared identity key — place_id, (metro, street-first-line),
    or (metro, name) — using union-find over `all_identity_keys()`. The old
    place-id-then-name+address pipeline missed the case the 2026-10-11 run
    exposed: a franchise crawler record (addr only) and a Google-Maps record
    (place_id + addr) for the same studio ended up in different indexes, and
    the reconciliation step only dropped the name+addr duplicate when its
    key exactly matched the place-indexed record's name+addr. With slight
    formatting differences (whitespace, suite number punctuation) both
    survived; the merger then handed both the same slug and retention aborted.
    """
    # Union-find over records keyed by their identity keys.
    parent: dict = {}  # key -> representative record (dict object)

    def find_root(record: dict) -> dict:
        """Follow the chain to the current root record for this one."""
        root = record
        while root.get("_dedup_merged_into") is not None:
            root = root["_dedup_merged_into"]
        return root

    for studio in studios:
        keys = all_identity_keys(studio)
        matched_root = None
        for k in keys:
            if k in parent:
                candidate = find_root(parent[k])
                if matched_root is None:
                    matched_root = candidate
                elif candidate is not matched_root:
                    # Two previously-independent groups bridged by this record;
                    # unify them.
                    _merge_into(matched_root, candidate)
                    candidate["_dedup_merged_into"] = matched_root
        if matched_root is None:
            # New business; the record is its own root.
            matched_root = studio
        else:
            _merge_into(matched_root, studio)
        for k in keys:
            parent[k] = matched_root

    # Collect unique roots and strip the internal marker.
    seen_ids = set()
    result = []
    for root in parent.values():
        actual_root = find_root(root)
        rid = id(actual_root)
        if rid not in seen_ids:
            seen_ids.add(rid)
            actual_root.pop("_dedup_merged_into", None)
            result.append(actual_root)

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
