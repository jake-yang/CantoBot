from __future__ import annotations

import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SENTENCES_PATH = DATA_DIR / "sentences.json"
TOPICS_PATH = DATA_DIR / "topics.json"
HISTORY_PATH = DATA_DIR / "history.json"
APP_TIME_ZONE = ZoneInfo("Asia/Seoul")

REQUIRED_SENTENCE_FIELDS = {
    "id",
    "cantonese",
    "jyutping",
    "english",
    "korean",
    "level",
    "tags",
}


def load_sentences(path: Path = SENTENCES_PATH) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        sentences = json.load(file)

    if not isinstance(sentences, list):
        raise ValueError(f"{path} must contain a JSON list of sentences.")

    seen_ids: set[int] = set()
    for index, sentence in enumerate(sentences, start=1):
        if not isinstance(sentence, dict):
            raise ValueError(f"Sentence #{index} must be a JSON object.")

        missing = REQUIRED_SENTENCE_FIELDS - sentence.keys()
        if missing:
            missing_fields = ", ".join(sorted(missing))
            raise ValueError(f"Sentence #{index} is missing: {missing_fields}")

        sentence_id = sentence["id"]
        if not isinstance(sentence_id, int):
            raise ValueError(f"Sentence #{index} has a non-integer id.")
        if sentence_id in seen_ids:
            raise ValueError(f"Duplicate sentence id found: {sentence_id}")
        seen_ids.add(sentence_id)

    return sentences


def load_topics(path: Path = TOPICS_PATH) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        topics = json.load(file)

    if not isinstance(topics, list) or len(topics) != 50:
        raise ValueError(f"{path} must contain exactly 50 topics.")

    for index, topic in enumerate(topics, start=1):
        if not isinstance(topic, dict) or not {"id", "title", "korean", "tags"} <= topic.keys():
            raise ValueError(f"Topic #{index} is missing a required field.")
        if not isinstance(topic["tags"], list) or not topic["tags"]:
            raise ValueError(f"Topic #{index} must include at least one tag.")
    return topics


def select_daily_topic(topics: list[dict[str, Any]]) -> dict[str, Any]:
    return random.choice(topics)


def load_history(path: Path = HISTORY_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"sent_history": []}

    with path.open("r", encoding="utf-8") as file:
        history = json.load(file)

    if not isinstance(history, dict):
        raise ValueError(f"{path} must contain a JSON object.")

    sent_history = history.setdefault("sent_history", [])
    if not isinstance(sent_history, list):
        raise ValueError(f"{path} field 'sent_history' must be a list.")

    return history


def get_recent_sentence_ids(
    history: dict[str, Any],
    *,
    today: date | None = None,
    recent_days: int = 30,
) -> set[int]:
    today = today or current_kst_date()
    cutoff = today - timedelta(days=recent_days)
    recent_ids: set[int] = set()

    for entry in history.get("sent_history", []):
        if not isinstance(entry, dict):
            continue

        entry_date = _parse_date(entry.get("date"))
        if entry_date is None or entry_date < cutoff:
            continue

        sentence_ids = entry.get("sentence_ids", [])
        if isinstance(sentence_ids, list):
            recent_ids.update(item for item in sentence_ids if isinstance(item, int))

    return recent_ids


def select_daily_sentences(
    sentences: list[dict[str, Any]],
    history: dict[str, Any],
    *,
    count: int = 5,
    preferred_levels: tuple[str, ...] = ("A1", "A2"),
    recent_days: int = 30,
) -> list[dict[str, Any]]:
    if len(sentences) < count:
        raise ValueError(f"Need at least {count} sentences, but only found {len(sentences)}.")

    recent_ids = get_recent_sentence_ids(history, recent_days=recent_days)
    preferred = [s for s in sentences if s.get("level") in preferred_levels]
    other = [s for s in sentences if s.get("level") not in preferred_levels]

    pools = [
        [s for s in preferred if s["id"] not in recent_ids],
        [s for s in other if s["id"] not in recent_ids],
        [s for s in preferred if s["id"] in recent_ids],
        [s for s in other if s["id"] in recent_ids],
    ]

    selected: list[dict[str, Any]] = []
    selected_ids: set[int] = set()

    for pool in pools:
        shuffled_pool = pool[:]
        random.shuffle(shuffled_pool)
        for sentence in shuffled_pool:
            if sentence["id"] in selected_ids:
                continue
            selected.append(sentence)
            selected_ids.add(sentence["id"])
            if len(selected) == count:
                random.shuffle(selected)
    return selected


def select_topic_sentences(
    sentences: list[dict[str, Any]],
    history: dict[str, Any],
    topic: dict[str, Any],
    *,
    count: int = 5,
) -> list[dict[str, Any]]:
    """Prefer sentences related to the chosen topic, then complete the set safely."""
    eligible_sentences = [
        sentence for sentence in sentences if len(str(sentence["cantonese"])) >= 10
    ]
    if len(eligible_sentences) < count:
        raise ValueError(f"Need at least {count} sentences with 10 or more characters.")

    topic_tags = set(topic["tags"])
    recent_ids = get_recent_sentence_ids(history)
    related = [
        sentence for sentence in eligible_sentences if topic_tags.intersection(sentence.get("tags", []))
    ]
    unrelated = [sentence for sentence in eligible_sentences if sentence not in related]
    pools = [
        [sentence for sentence in related if sentence["id"] not in recent_ids],
        [sentence for sentence in related if sentence["id"] in recent_ids],
        [sentence for sentence in unrelated if sentence["id"] not in recent_ids],
        [sentence for sentence in unrelated if sentence["id"] in recent_ids],
    ]

    selected: list[dict[str, Any]] = []
    for pool in pools:
        random.shuffle(pool)
        for sentence in pool:
            if sentence not in selected:
                selected.append(sentence)
            if len(selected) == count:
                return selected
    raise ValueError(f"Could not select {count} unique sentences.")

    raise ValueError(f"Could not select {count} unique sentences.")


def save_history(history: dict[str, Any], path: Path = HISTORY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".json.tmp")
    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)
        file.write("\n")
    temp_path.replace(path)


def record_sent_sentences(
    sentence_ids: list[int],
    *,
    sent_date: date | None = None,
    history_path: Path = HISTORY_PATH,
) -> None:
    history = load_history(history_path)
    history["sent_history"].append(
        {
            "date": (sent_date or current_kst_date()).isoformat(),
            "sentence_ids": sentence_ids,
        }
    )
    save_history(history, history_path)


def current_kst_date() -> date:
    return datetime.now(APP_TIME_ZONE).date()


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _print_selection_preview() -> None:
    sentences = load_sentences()
    history = load_history()
    selected = select_daily_sentences(sentences, history)

    for number, sentence in enumerate(selected, start=1):
        print(f"{number}. {sentence['cantonese']}")
        print(f"   {sentence['jyutping']}")
        print(f"   {sentence['english']}")
        print(f"   {sentence['korean']}")
        print()


if __name__ == "__main__":
    _print_selection_preview()
