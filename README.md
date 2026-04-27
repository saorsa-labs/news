# 🤖 AI News Hub

A beautiful, single-page reader for **270+ AI / ML / Big-Data news, podcast and YouTube sources** — sourced from the excellent [foorilla/allainews_sources](https://github.com/foorilla/allainews_sources) catalogue and kept fresh automatically.

No accounts. No tracking. No ads. Open it and read.

---

## Just open it

**The easy way — works for everyone, no install:**

👉 **<https://news.saorsalabs.com/>**

Bookmark that URL. That's the whole thing. It runs entirely in your browser and remembers your preferences locally.

### One-liners

If you'd rather launch from the terminal:

```bash
# macOS
open https://news.saorsalabs.com/

# Linux
xdg-open https://news.saorsalabs.com/

# Windows (PowerShell)
start https://news.saorsalabs.com/
```

### Want a local copy that works offline-friendly?

Download the single HTML file and double-click it:

```bash
# macOS / Linux
curl -L -o ~/Desktop/news.html https://raw.githubusercontent.com/saorsa-labs/news/main/index.html && \
  ( open ~/Desktop/news.html 2>/dev/null || xdg-open ~/Desktop/news.html )
```

The page **auto-updates its source list from this repo every time you open it**, so even an old downloaded copy keeps getting new feeds as we add them. You'll see a small "Sources updated" toast at the bottom when that happens.

---

## What it does

- **Timeline** — newest items from every source in one chronological feed
- **Videos** — grid of recent YouTube uploads from 60+ channels with thumbnails
- **Podcasts** — latest episodes from 35+ shows
- **Sources** — browse the full catalogue, see which loaded successfully, click through to RSS or homepage
- **Custom feeds** — add any RSS/Atom URL via the **+ Feed** button. Auto-detects title and YouTube channels. Persists in your browser.
- **Filters** — by category (News / Podcasts / Videos / Jobs), by tag (Reddit / Newsletter / Research / Lab/Vendor / YouTube / Medium), by time window (24h / 7 days / 30 days)
- **Search** — across titles, sources and descriptions
- **Light & dark themes** — toggle in the header, persisted
- **7-day cache** — items stay visible even if a feed is briefly down; saves bandwidth
- **Instant first load** — every 30 min the GitHub Action pre-fetches all 269 feeds server-side and ships an `items.json` (~400 KB gzipped). The page hydrates from that one file instead of fetching 269 feeds individually through CORS proxies, so a fresh visitor sees ~4,000 items in seconds rather than tens of minutes

### Privacy

Everything runs client-side. The page fetches RSS/Atom feeds through public CORS proxies (`api.codetabs.com`, `api.allorigins.win`, `corsproxy.io`, `thingproxy.freeboard.io`) — those proxies see which feeds you're loading, but no personal data is sent to anyone, and your settings, custom feeds and cache live only in your browser's `localStorage`.

---

## How it stays current

A scheduled GitHub Action runs **every 30 minutes** and:

1. Pulls the latest README from [foorilla/allainews_sources](https://github.com/foorilla/allainews_sources)
2. Re-runs `build.py` to regenerate `sources.json` and `index.html`
3. Fetches every RSS/Atom feed in parallel (24 workers) and writes `items.json` — a pre-parsed bundle of the most recent 15 items per source
4. Commits if anything changed

Because the page also fetches `sources.json` from this repo on every load, **your downloaded copy auto-updates** without you doing anything. Open the page anytime, get the latest sources.

---

## Run your own copy (full control, no dependency on us)

If you'd rather not rely on `saorsa-labs/news`, host your own. Three flavours, easiest first:

### 1. Fork & GitHub Pages (zero install, free, automatic)

```bash
gh repo fork saorsa-labs/news --clone=false                # or click Fork on GitHub
gh api -X POST repos/<your-username>/news/pages \
  -f 'source[branch]=main' -f 'source[path]=/'
```

You now have your own URL: `https://<your-username>.github.io/news/`. The forked repo also has the rebuild Action, so it'll keep itself in sync with upstream foorilla automatically — no maintenance from you.

### 2. Local web server (works fully offline once first cached)

Clone the repo and serve the folder. Any static-file server works:

```bash
git clone https://github.com/saorsa-labs/news.git
cd news

# Python (almost certainly already installed)
python3 -m http.server 8000

# …or Node, …or Caddy, …or whatever you like
# npx serve .
```

Then open `http://localhost:8000/`. It still fetches feeds via public CORS proxies (your network → proxy → feed), so it needs internet, but the page itself is served from your machine.

### 3. Just the file (truly portable)

Drop `index.html` into Dropbox / iCloud / a USB stick. It works from `file://` too. Bookmark it, sync it, do whatever. The only limitation: a few feeds (Reddit notably) refuse `null` origin requests — those'll just show as "failed" in the Sources tab.

### Customising your fork

Edit `build.py` to add/remove sources, change tags or categories, then run `python3 build.py`. Or just hand-edit `sources.json` — it's a flat array of `{title, homepage, feed, description, category, tags, youtube_channel_id}`.

If you want your fork to **stop** auto-updating its source list from `saorsa-labs/news` (so you fully own the catalogue), open `index.html` and either change `REMOTE_SOURCES_URL` to point to your fork's raw URL, or delete the call to `autoUpdateSources()` in `init()`.

---

## For maintainers / contributors

You only need this section if you want to regenerate the build locally or work on the code.

### Requirements

- Python 3.9+
- `feedparser` (`pip install feedparser`) — only needed if you want `build.py` to also fetch feed items into `items.json`. Without it the build still produces `sources.json` and `index.html`; you just lose the instant-first-load hydration.

### Rebuild

```bash
git clone https://github.com/saorsa-labs/news.git
cd news
python3 build.py
```

This pulls the latest upstream README, regenerates `sources.json` and `index.html` in place, and prints a summary by category.

### Project structure

```
.
├── index.html                 # The single-file app (generated)
├── sources.json               # Structured source list (generated)
├── build.py                   # Builds the two files above from upstream
├── .github/workflows/
│   └── rebuild.yml            # Weekly auto-rebuild
├── LICENSE                    # MIT
└── README.md
```

Both `index.html` and `sources.json` are checked in so GitHub Pages can serve them directly with no build step.

### Customising the build

Edit `build.py` to change:

- **Tag detection** — `_LAB_HOSTS` and the `tags.append(...)` rules in `parse_sources`
- **Categories** — `_CAT` mapping
- **Initial load batch size and concurrency** — see `pickInitialBatch` and `runLoader` inside the inline HTML/JS template
- **Cache TTL** — search for `CACHE_TTL_MS` in the template

After editing, run `python3 build.py` and commit the regenerated files.

### Why a single file?

`index.html` is a self-contained ~120 KB page with all CSS, JS and the embedded source catalogue. That makes it trivial to host (GitHub Pages, any static server, even file://) and trivial to share (a single download).

---

## Credits

The source catalogue is curated by [foorilla](https://foorilla.com/) — see [foorilla/allainews_sources](https://github.com/foorilla/allainews_sources). This project simply turns it into a browseable reader.

## License

[MIT](LICENSE) © Saorsa Labs
