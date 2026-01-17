# Getting Started

Welcome to Fast Django. This section will help you get up and running quickly.

## What You Will Learn

This guide covers everything you need to start developing with the template:

| Guide | Description | Time |
|-------|-------------|------|
| [Quick Start](quick-start.md) | Get the project running in 5 minutes | 5 min |
| [Project Structure](project-structure.md) | Understand the codebase organization | 10 min |
| [Development Environment](development-environment.md) | Configure your IDE and tooling | 15 min |

## Prerequisites

Before you begin, ensure you have:

- **Python 3.14+** - The template uses modern Python features
- **Docker & Docker Compose** - For running infrastructure services
- **uv** - Fast Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))

!!! tip "New to uv?"
    uv is a fast Python package installer and resolver written in Rust. It replaces pip, pip-tools, and virtualenv with a single, fast tool. Install it with:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

## Quick Overview

The template provides a production-ready foundation for building APIs with:

- **FastAPI** - Fast, async-ready HTTP API framework
- **Celery** - Distributed task queue for background jobs
- **punq** - Lightweight dependency injection container
- **PostgreSQL + Redis + MinIO** - Battle-tested infrastructure stack

## Next Steps

Ready to dive in? Start with the [Quick Start](quick-start.md) guide to get the project running locally.
