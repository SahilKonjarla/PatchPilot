

```
# 🧠 PatchPilot

**PatchPilot** is an autonomous, AI-powered code review assistant that integrates directly with GitHub pull requests.
It listens to repository webhooks, fetches code changes, analyzes diffs with an LLM, and posts actionable, structured feedback --- automatically.

---

## 🚀 Features

- **Real-time PR Reviews:** Automatically triggered on `opened`, `synchronize`, or `reopened` pull request events.
- **LLM-powered Analysis:** Uses large language models to generate structured and concise code reviews.
- **GitHub App Integration:** Authenticates securely as a GitHub App to access PRs and post comments.
- **Celery Queues:** Asynchronous task processing with retries, backoff, and timeout guards.
- **Observability:** Exposes Prometheus metrics for HTTP and Celery performance.
- **Resilient Design:** Built with full fault-tolerance --- auto-retries on transient network or LLM failures.
- **Extensible:** Modular architecture supporting pluggable AI models and GitHub integrations.

---

```
## 🧩 Architecture Overview

```

PatchPilot/
├── adapters/ # Interfaces for GitHub API (auth, comments, client)\
├── core/ # Webhook and HTTP routes (Django views)\
├── observability/ # Metrics, middleware, Celery hooks\
├── project/ # Django project configuration\
├── reviews/ # Review logic and AI agents\
├── services/\
│ ├── queue/ # Celery tasks, reliability guards, retries\
│ └── review/ # ReviewAgent (LLM interface)\
└── manage.py # Django entrypoint

```

---

## 🧰 Technology Stack

| Component | Technology |
|------------|-------------|
| **Framework** | Django |
| **Queue Engine** | Celery |
| **Message Broker / Backend** | Redis |
| **Monitoring** | Prometheus |
| **Deployment** | Makefile |

---

## ⚙️ Setup Guide

### 1. Prerequisites

Ensure you have:

- Python 3.12+
- Redis Server (local or cloud)
- GitHub App credentials:
  - `GITHUB_APP_ID`
  - `GITHUB_PRIVATE_KEY_PEM`
  - `GITHUB_WEBHOOK_SECRET`

---

### 2. Clone and Initialize

```bash
git clone https://github.com/<your-username>/PatchPilot.git
cd PatchPilot
python3 -m venv .PatchPilot
source .PatchPilot/bin/activate
pip install -r requirements.txt

```

* * * * *

### 3\. Environment Variables

Copy `.env.example` to `.env` and fill in your secrets:

```
cp .env.example .env

```

**Example:**

```
DJANGO_SECRET_KEY=your-django-secret
DJANGO_DEBUG=True
REDIS_URL=redis://localhost:6379/0
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY_PEM="-----BEGIN PRIVATE KEY-----\n....\n-----END PRIVATE KEY-----"
GITHUB_WEBHOOK_SECRET=your-webhook-secret

```

* * * * *

### 4\. Database and Django Setup

```
python manage.py migrate
python manage.py createsuperuser

```

* * * * *

### 5\. Running the Application

You can use the `Makefile` for quick management of all services.

#### Start the web server and Celery worker:

```
make run

```

#### Stop all running services:

```
make stop

```


Once running:

-   **Django Web Server:** `http://127.0.0.1:8000`

-   **Celery Worker:** Processes background review tasks

-   **Prometheus Metrics:** `http://127.0.0.1:8000/metrics`

* * * * *

🔗 GitHub Webhook Configuration
-------------------------------

1.  Create a **GitHub App** at:\
    <https://github.com/settings/apps/new>

2.  Under **Permissions**, enable:

    -   **Pull requests:** Read & Write

    -   **Contents:** Read

    -   **Metadata:** Read

    -   **Issues:** Read & Write

3.  Under **Webhook**:

    -   **URL:** `https://<your-domain>/webhook/`

    -   **Secret:** same as `GITHUB_WEBHOOK_SECRET`

    -   **Events:** `Pull Request` and `Installation`

4.  Install the App on your test repository.

* * * * *

🧠 How It Works
---------------

1.  GitHub sends a `pull_request` event → Django webhook (`/webhook/`) receives it.

2.  Webhook enqueues a Celery task: `review_pull_request`.

3.  Celery worker fetches changed files → sends them to `ReviewAgent`.

4.  `ReviewAgent` builds a structured LangChain prompt → calls LLM.

5.  The generated review is posted back to the PR via GitHub API.

6.  Observability hooks record request and task metrics in Prometheus.

* * * * *

📊 Observability and Metrics
----------------------------

PatchPilot exposes Prometheus metrics at `/metrics`.

**Available Metrics:**

| Metric | Description |
| --- | --- |
| `patchpilot_http_requests_total` | HTTP requests by method/endpoint |
| `patchpilot_request_latency_seconds` | Latency histogram per route |
| `patchpilot_tasks_total` | Celery tasks executed (by name/status) |
| `patchpilot_task_duration_seconds` | Task execution durations |

* * * * *

🩹 Reliability and Retries
--------------------------

-   Automatic **retries** on:

    -   GitHub rate limits (403/429)

    -   Network or API errors

-   **Exponential backoff** and **jitter** to avoid retry storms.

-   **Timeout guards** for every Celery task.

-   **Worker shutdown hooks** ensure in-flight tasks are gracefully drained.

* * * * *

📁 Project Modules Summary
--------------------------

| Module | Purpose |
| --- | --- |
| `adapters/github/auth.py` | Handles App JWT and installation token exchange |
| `adapters/github/client.py` | Fetches PR files from GitHub |
| `adapters/github/comments.py` | Posts PR review comments |
| `core/views.py` | Webhook + metrics + health routes |
| `services/review/review_agent.py` | LLM interface for PR reviews |
| `services/queue/tasks.py` | Celery task orchestration with retries and timeouts |
| `observability/metrics.py` | Prometheus metric definitions |
| `observability/celery_hooks.py` | Hooks for Celery instrumentation |

* * * * *

🏁 License
----------

MIT License © 2025 [Sahil Konjarla](https://github.com/SahilKonjarla)