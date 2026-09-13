# Cantonese Daily

A small personal automation that sends 5 beginner-friendly Cantonese sentences to Telegram every morning at 7:00 AM Korea Standard Time.

The learning flow is intentionally simple:

```text
GitHub Actions
  -> Telegram
  -> your phone
  -> physical notebook
```

No web app, database server, or always-on Mac is required.

## File Structure

```text
cantonese-daily/
├── data/
│   ├── sentences.json
│   ├── history.json
│   └── vocabulary.json
├── src/
│   ├── send_daily.py
│   └── selector.py
├── .github/
│   └── workflows/
│       └── daily.yml
├── .gitignore
├── requirements.txt
└── README.md
```

## How It Works

Every day, GitHub Actions runs `python src/send_daily.py`.

The script:

1. Reads `data/sentences.json`.
2. Reads `data/history.json`.
3. Selects exactly 5 sentences, preferring `A1` and `A2` sentences.
4. Avoids sentences sent in the last 30 days when possible.
5. Sends the message through the Telegram Bot API.
6. Updates `data/history.json` only after Telegram confirms success.
7. Commits and pushes the updated history file back to GitHub.

If Telegram fails, the script exits with a non-zero status code and does not update history.

Dates are calculated with the `Asia/Seoul` time zone so the message date matches the 7:00 AM KST delivery time.

## Create a Telegram Bot

1. Open Telegram.
2. Search for `@BotFather`.
3. Start a chat with BotFather.
4. Send:

   ```text
   /newbot
   ```

5. Follow the prompts:
   - Choose a display name, such as `Cantonese Daily`.
   - Choose a username ending in `bot`, such as `my_cantonese_daily_bot`.
6. BotFather will give you a bot token.

Keep the token private. It will look something like this:

```text
123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
```

Do not commit this token to GitHub.

## Get Your Telegram Chat ID

1. Open Telegram and send any message to your new bot, such as:

   ```text
   hello
   ```

2. In your browser, open this URL after replacing `<BOT_TOKEN>` with your real bot token:

   ```text
   https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
   ```

3. Look for a `chat` object in the response. The `id` value is your chat ID.

It will look similar to:

```json
"chat": {
  "id": 123456789,
  "first_name": "Jake",
  "type": "private"
}
```

Use the number from `id` as `TELEGRAM_CHAT_ID`.

If `getUpdates` returns an empty result, send another message to your bot and refresh the URL.

## GitHub Secrets

In your GitHub repository:

1. Go to `Settings`.
2. Go to `Secrets and variables`.
3. Choose `Actions`.
4. Click `New repository secret`.
5. Add these two secrets:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

The workflow reads these secrets at runtime. They are not stored in the code.

## Add or Edit Sentences

Edit `data/sentences.json`.

Each sentence must have these fields:

```json
{
  "id": 1,
  "cantonese": "你食咗飯未呀？",
  "jyutping": "nei5 sik6 zo2 faan6 mei6 aa3?",
  "english": "Have you eaten yet?",
  "korean": "밥 먹었어?",
  "level": "A1",
  "tags": ["daily", "conversation"]
}
```

Rules:

- Keep each `id` unique.
- Use `A1` or `A2` for beginner sentences.
- Add any useful tags you want, such as `food`, `travel`, `daily`, or `conversation`.
- The Python code automatically works with more sentences as long as the JSON remains valid.

## Local Setup

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Preview sentence selection without sending anything:

```bash
python src/selector.py
```

Temporarily set Telegram credentials locally:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Then send a real test message:

```bash
python src/send_daily.py
```

After a successful send, `data/history.json` will be updated.

## Manual GitHub Actions Test

After pushing this project to GitHub:

1. Open the repository on GitHub.
2. Click the `Actions` tab.
3. Select `Daily Cantonese Telegram`.
4. Click `Run workflow`.
5. Confirm that the run succeeds.
6. Confirm that Telegram received the message.
7. Confirm that `data/history.json` was committed back to the repository.

## Daily Schedule

The workflow uses this cron schedule:

```yaml
cron: "0 22 * * *"
```

GitHub Actions cron schedules use UTC.

Korea Standard Time is UTC+9, so:

```text
22:00 UTC = 07:00 KST on the next calendar day
```

That means the workflow sends your message at 7:00 AM KST.

GitHub scheduled workflows can sometimes run a few minutes late depending on GitHub's queue. This is normal.

## History and Repetition

`data/history.json` stores the dates and sentence IDs that were successfully sent.

The selector avoids sentences sent in the last 30 days when possible. If your sentence database is too small to provide 5 unused sentences, it allows older sentences to repeat so the daily message still works.

With the initial 15 sample sentences, repetition will happen quickly. Add more sentences over time for better variety.

## Future Ideas

The project is structured so these can be added later:

- Spaced repetition with new and review sentences.
- Native Cantonese audio links or attachments.
- Vocabulary extraction into `data/vocabulary.json`.
- Weekly review messages.
- Multiple-choice quizzes.

For now, the project stays focused on one reliable job: sending 5 useful Cantonese sentences to your phone every morning.
