# Telegram Bot

Build Telegram bots with aiogram and the factory pattern.

## Overview

The Telegram bot uses [aiogram](https://docs.aiogram.dev/) for async bot development with handlers and commands.

## Architecture

```
Telegram API
     │
     ▼
┌─────────────┐
│    Bot      │
│  (aiogram)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Dispatcher  │
│  (Router)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Handlers   │
│ (Commands)  │
└─────────────┘
```

## Topics

<div class="grid cards" markdown>

-   **Bot & Dispatcher Factories**

    ---

    How the bot and dispatcher are created and configured.

    [:octicons-arrow-right-24: Learn More](factories.md)

-   **Handlers**

    ---

    Command handlers and message processing.

    [:octicons-arrow-right-24: Learn More](handlers.md)

</div>

## Quick Start

### 1. Get a Bot Token

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy the token

### 2. Configure Environment

Add to `.env`:

```bash
TELEGRAM_BOT_TOKEN=your-bot-token
```

### 3. Start the Bot

```bash
make bot-dev
```

### 4. Test It

Message your bot with `/start` or `/id`.

## Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | `SecretStr` | **Required** | Bot token from BotFather |
| `TELEGRAM_BOT_PARSE_MODE` | `str` | `HTML` | Default message parse mode |

## Entry Point

The bot is started via `delivery/bot/__main__.py`:

```python
from aiogram import Bot, Dispatcher

from core.configs.infrastructure import configure_infrastructure
from ioc.container import get_container


def main() -> None:
    configure_infrastructure(service_name="bot")
    container = get_container()

    bot = container.resolve(Bot)
    dispatcher = container.resolve(Dispatcher)
    dispatcher.run_polling(bot)


if __name__ == "__main__":
    main()
```

## Available Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/id` | Get user and chat IDs |

## Related Topics

- [Your First Bot Command](../tutorials/first-bot-command.md) — Tutorial
- [aiogram Documentation](https://docs.aiogram.dev/) — Official docs
