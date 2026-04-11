# OpenClaw in StockMonkey — Technical Overview

## What OpenClaw Is

OpenClaw is an **autonomous agent framework**. Think of it as a runtime that sits between an LLM (in our case GPT-5.4) and the outside world — messaging platforms, shell commands, scheduled tasks. It's the infrastructure that turns a language model from something you query in a browser into something that **runs on your machine, takes actions, and communicates with you through real channels** like Telegram, Discord, or Slack.

The three core pieces of OpenClaw's architecture that we use are:

---

## 1. The Gateway (Local Process Manager)

```
gateway.mode: "local"
gateway.port: 18789
gateway.bind: "loopback"
```

The gateway is a **persistent local daemon** running as a macOS LaunchAgent. It's a WebSocket server bound to `127.0.0.1:18789`. It's responsible for:

- **Session management** — maintaining conversation state across interactions
- **Channel multiplexing** — routing inbound messages from Telegram (or any connected channel) to the agent, and routing the agent's responses back out
- **Cron scheduling** — executing timed jobs and delivering results
- **Skill loading** — reading SKILL.md files at session start so the agent knows its capabilities

It runs continuously in the background. When your laptop is open, the gateway is alive. When you restart, macOS relaunches it automatically via the LaunchAgent.

---

## 2. Channels (Telegram Integration)

```json
"telegram": {
  "enabled": true,
  "botToken": "...",
  "dmPolicy": "open"
}
```

A **channel** is OpenClaw's abstraction for any messaging platform. We registered a Telegram bot token with the gateway using `openclaw channels add --channel telegram --token <token>`. The gateway then runs a **long-polling loop** against the Telegram Bot API — the exact same mechanism our custom `telegram_bot.py` used to use, but now managed by the framework.

Here's what's technically happening when you send "how are my stocks doing?" to the bot:

1. The gateway's Telegram provider **polls** `getUpdates` from Telegram's API
2. Your message arrives as an update object with your `chat_id` and text
3. The gateway checks the `dmPolicy` — since it's `"open"`, your message is accepted
4. The gateway creates an **agent session** (or resumes an existing one) and passes your message to the LLM
5. The LLM has the `stock-daily-brief` SKILL.md loaded in its context, so it **recognizes your intent** and knows which shell commands to execute
6. The agent runs the commands (activates the venv, executes the Python pipeline)
7. The agent captures stdout and **composes a response** — not just a raw dump, but an intelligent summary
8. The gateway sends that response back through the Telegram Bot API's `sendMessage`

The key difference from what we had before: the old `telegram_bot.py` did rigid keyword matching (`if "stonks" in cmd`). Now the LLM interprets intent. "How are my stocks doing?", "run my brief", "stonks please" — they all work because the agent understands natural language.

---

## 3. Skills (Teaching the Agent What It Can Do)

This is the most architecturally interesting part. A **skill** is just a Markdown file with YAML frontmatter:

```yaml
---
name: stock-daily-brief
description: Generate daily stock watchlist briefs and manage a personal ticker watchlist...
---
```

The body of the Markdown contains **instructions for the agent** — not code the agent executes directly, but documentation it reads to understand what tools are available and how to use them. It's essentially **prompt engineering stored as a file**.

When a session starts, OpenClaw reads every SKILL.md from its skill directories and injects them into the LLM's system context. The agent then has a "menu" of capabilities. Our skill tells the agent:

- The project path and how to activate the venv
- The exact shell commands for running the pipeline, showing the watchlist, adding/removing tickers
- What the output format looks like
- What it should NOT do (no financial advice, no trade execution)
- How errors are handled

The skill lives at `~/.openclaw/workspace/skills/stock-daily-brief/SKILL.md`. OpenClaw discovers it through a **precedence chain**: workspace skills override shared skills, which override bundled skills. We also keep a copy in our project repo at `stockmonkey/openclaw/skills/stock_daily_brief/` for version control.

---

## 4. Cron (Scheduled Agent Execution)

```json
{
  "schedule": { "kind": "cron", "expr": "0 7 * * 1-5", "tz": "America/Los_Angeles" },
  "payload": {
    "kind": "agentTurn",
    "message": "Run my daily stock brief. Use the stock-daily-brief skill..."
  },
  "delivery": { "mode": "announce", "channel": "telegram", "to": "8715564698" }
}
```

The cron system is baked into the gateway. At 7:00 AM Pacific every weekday, the gateway:

1. Creates an **isolated session** (separate from your main chat context)
2. Sends the `message` payload to the agent as if a human typed it
3. The agent reads the skill, runs the pipeline, gets the output
4. The `"announce"` delivery mode tells the gateway to take the agent's final response and push it through the Telegram channel to your `chat_id`

This replaced our old approach, which was a **macOS LaunchAgent** that triggered a Python gate script (`wake_trigger.py`) on login/wake. That script had hardcoded logic — check if it's a weekday, check if it's after 9:30 AM ET, check if today's digest exists. Now the agent handles all of that intelligently, and if something fails, it can retry or tell you what went wrong in natural language instead of silently logging to a file.

---

## The Data Flow (End-to-End)

If someone asks you to trace a request through the system:

```
You (Telegram) → Telegram API → Gateway (polling) → Agent Session
    → Agent reads SKILL.md → Agent shells out to Python pipeline
        → Playwright scrapes Yahoo Finance (headless Chromium)
        → OpenAI Responses API summarizes each ticker
        → SQLite stores snapshots for day-over-day comparison
        → Digest builder aggregates + LLM summarizes the whole watchlist
        → Markdown output to stdout
    → Agent captures output → Agent composes response
→ Gateway → Telegram API → You (Telegram)
```

For the cron path, it's the same flow but the trigger is the gateway's internal scheduler instead of an inbound Telegram message.

---

## Why This Architecture Matters (Interview Talking Points)

**Separation of concerns**: The Python pipeline (`app/`) is pure data processing — extract, summarize, persist, compare. It knows nothing about messaging. OpenClaw handles all the I/O with the outside world. You could swap Telegram for Discord by adding a channel; the pipeline doesn't change.

**Agent-as-orchestrator**: Instead of writing imperative glue code (if this command, call this function), you write declarative instructions (here's what you can do, here are the commands). The LLM handles intent parsing, error messaging, and response composition. This is a fundamentally different software architecture pattern — closer to how you'd brief a human assistant than how you'd write a switch statement.

**Infrastructure-as-config**: The entire integration — which LLM to use, which channels are connected, what the DM policy is, what skills are available, what cron jobs run — is declarative JSON in `~/.openclaw/openclaw.json`. Nothing is hardcoded in application code.

**Graceful degradation**: The pipeline is designed so that if one ticker fails, the rest still process. If the whole pipeline fails, an error artifact is still saved. The agent can communicate failures to you in plain language rather than you having to check log files.
