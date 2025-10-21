<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Git Commit Message Conventions

This project uses a hybrid of Conventional Commits and classic best practices (Chris Beams). The goal is clear, searchable history that explains what and why, not just how.

## TL;DR
- Use Conventional Commits: `type(scope)!: subject`
- Subject in imperative mood, ≤ 50 chars; no period
- Blank line after subject; wrap body at ~72 chars
- Explain motivation, user impact, risks; reference epics/tasks/chunks
- List key files affected for searchability
- Footer for breaking changes and issue refs

## Format
```
<type>(<scope>)!: <subject>

<body>

<footer>
```
- **type**: one of `feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert`
- **scope**: optional, small area like `backend`, `chat-ui`, `config`, `docs`, `infra`
- **!**: optional; indicate breaking change
- **subject**: imperative, concise (≤ 50 chars), no trailing period
- **body**: details (what/why), wrapped at 72 cols; bullets ok
- **footer**: `BREAKING CHANGE:` and/or issue refs `Refs: #123`, `Closes #123`

## Best practices
- Subject: imperative mood ("Add", not "Added"/"Adds")
- Separate subject and body with a blank line
- Focus body on rationale and impact; avoid code diffs
- Reference planning IDs (EPIC/FEATURE/TASK/CHUNK) when relevant
- Add a short “Files affected” list to aid future search

## Types (Conventional Commits)
- **feat**: new user-facing capability
- **fix**: bug fix
- **docs**: documentation only
- **style**: formatting, no code change
- **refactor**: code change without new feature/fix
- **perf**: performance improvement
- **test**: tests only
- **build**: build system/deps
- **ci**: CI config/scripts
- **chore**: maintenance tasks
- **revert**: revert a previous commit

## Examples (this repo)

Short, single-file docs change:
```
docs(architecture): add salesbot integration approaches

Explain recommended Shadow DOM widget, alternatives, and cross-cutting concerns.
Files affected:
- memorybank/architecture/salesbot-integration.md
```

Feature chunk completion with planning link:
```
feat(backend): implement 0002-001-001-01 base page (GET /)

Baseline Jinja2 page with HTMX CDN, message textarea, Send and Clear buttons,
and append-only chat pane. Supports Ctrl+Enter send, Enter newline.
Refs: 0002-001-001-01
Files affected:
- backend/app/main.py
- backend/templates/index.html
```

Planning status update:
```
docs(plan): mark 0002-001-001-01 as Completed

Update baseline connectivity plan to reflect implemented base page.
Files affected:
- memorybank/project-management/0002-baseline-connectivity.md
```

Breaking change:
```
refactor(api)!: rename SSE route to /events/stream

Aligns with design docs; updates all references.
BREAKING CHANGE: clients must call GET /events/stream instead of /sse.
```

## Referencing issues and PRs
- Use `Refs: #123` to link context; `Closes #123` to auto-close
- Link external PRs/issues with full URLs when helpful

## Co-authors (optional)
Add lines to the footer:
```
Co-authored-by: Name <email@example.com>
```

## Searchability checklist
- Include planning ID(s): `0002-001-001-01` where applicable
- Mention key file paths under “Files affected”
- Prefer descriptive scopes: `backend`, `chat-ui`, `architecture`, `config`

