from __future__ import annotations

import html
import os
import sys
from datetime import date
from typing import Any

import requests

from selector import (
    current_kst_date,
    load_history,
    load_sentences,
    record_sent_sentences,
    select_daily_sentences,
)


TELEGRAM_API_BASE = "https://api.telegram.org/bot"


class TelegramError(RuntimeError):
    pass


def build_daily_message(sentences: list[dict[str, Any]], *, message_date: date | None = None) -> str:
    message_date = message_date or current_kst_date()
    circled_numbers = ["①", "②", "③", "④", "⑤"]
    lines = [f"🇭🇰 <b>Cantonese Daily — {message_date.isoformat()}</b>", ""]

    for index, sentence in enumerate(sentences):
        number = circled_numbers[index] if index < len(circled_numbers) else f"{index + 1}."
        lines.extend(
            [
                f"{number} {html.escape(str(sentence['cantonese']))}",
                html.escape(str(sentence["jyutping"])),
                html.escape(str(sentence["english"])),
                html.escape(str(sentence["korean"])),
                "",
            ]
        )

    lines.append("✍️ Write these down and review them today.")
    return "\n".join(lines)


def send_telegram_message(text: str) -> None:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token:
        raise TelegramError("Missing TELEGRAM_BOT_TOKEN environment variable.")
    if not chat_id:
        raise TelegramError("Missing TELEGRAM_CHAT_ID environment variable.")

    url = f"{TELEGRAM_API_BASE}{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, data=payload, timeout=20)
    except requests.RequestException as error:
        raise TelegramError(f"Telegram request failed: {error}") from error

    if response.status_code != 200:
        raise TelegramError(
            f"Telegram API returned HTTP {response.status_code}: {_safe_response_text(response)}"
        )

    try:
        response_data = response.json()
    except ValueError as error:
        raise TelegramError("Telegram API returned a non-JSON response.") from error

    if not response_data.get("ok"):
        description = response_data.get("description", "No description provided.")
        raise TelegramError(f"Telegram API rejected the message: {description}")


def _safe_response_text(response: requests.Response) -> str:
    text = response.text.strip()
    if len(text) > 500:
        return text[:500] + "..."
    return text or "<empty response>"


def main() -> int:
    try:
        sentences = load_sentences()
        history = load_history()
        selected = select_daily_sentences(sentences, history)
        message = build_daily_message(selected)

        send_telegram_message(message)
        record_sent_sentences([sentence["id"] for sentence in selected])
    except (TelegramError, OSError, ValueError, KeyError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print("Sent today's Cantonese message and updated history.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
