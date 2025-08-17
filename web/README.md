# Web (Astro host app)

This directory contains an optional Astro site used to host or link to the backend chat UI.

## Project Structure

Inside of your Astro project, you'll see the following folders and files:

```text
/
├── public/
│   └── favicon.svg
├── src
│   ├── assets
│   │   └── astro.svg
│   ├── components
│   │   └── Welcome.astro
│   ├── layouts
│   │   └── Layout.astro
│   └── pages
│       └── index.astro
└── package.json
```

Tailwind v4 is configured via `@tailwindcss/vite` in `astro.config.mjs`. Basecoat CSS is imported after Tailwind in `src/styles/global.css`. Ensure `global.css` is imported from your layout.

## Commands

All commands are run from the root of the project, from a terminal:

| Command                   | Action                                           |
| :------------------------ | :----------------------------------------------- |
| `pnpm install`           | Installs dependencies                            |
| `pnpm dev`               | Starts local dev server at `localhost:4321`      |
| `pnpm build`           | Build your production site to `./dist/`          |
| `pnpm preview`         | Preview your build locally, before deploying     |
| `pnpm astro ...`       | Run CLI commands like `astro add`, `astro check` |
| `pnpm astro -- --help` | Get help using the Astro CLI                     |

## Notes
- Baseline does not host the chat pane here; it’s served by the backend at `http://localhost:8000/`.
- For quick demos you can link to the backend chat page; long-term we will provide a site-wide floating button widget.

## Widget (Shadow-DOM) Integration

To show a site-wide floating chat button on every page:

1) Enable via env (recommended)
- Set `PUBLIC_ENABLE_WIDGET=true` for the demo environment (default false in prod).

2) Include the loader once in your shared layout
- In `src/layouts/Layout.astro`, add the script just before `</body>`:

```astro
{import.meta.env.PUBLIC_ENABLE_WIDGET === 'true' && (
  <script src="/widget/chat-widget.js" is:inline data-chat-path="/chat"></script>
)}
```

3) Same-origin in dev and prod
- Dev: `astro.config.mjs` proxies `/chat`, `/events`, `/health` to the backend (default `http://localhost:8000`). This makes widget fetches same-origin:
  - Set `BACKEND_ORIGIN=http://localhost:8000` if your backend origin differs.
- Prod: serve the backend via the same domain (reverse proxy) and keep `data-allow-cross` OFF.

4) Optional configuration via data attributes
- `data-chat-path` (default `/chat`)
- `data-backend` (override the origin for special dev cases only)
- `data-allow-cross="1"` (dev-only; do not use in production)

5) Notes
- The widget uses a Shadow DOM to isolate styles; it won’t interfere with your site CSS.
- Accessibility: ESC closes, overlay click closes, focus returns to trigger.
- Keep `ui.expose_backend_chat: false` in production; the widget posts to `/chat` and does not need to expose GET `/`.
