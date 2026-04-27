# 🤖 AI News Hub

A beautiful, single-page reader for **270+ AI / ML / Big-Data news, podcast and YouTube sources** — sourced from the excellent [foorilla/allainews_sources](https://github.com/foorilla/allainews_sources) catalogue and kept fresh automatically.

No accounts. No tracking. No ads. Open it and read.

---

## Just open it

**The easy way — works for everyone, no install:**

👉 **<https://saorsa-labs.github.io/news/>**

Bookmark that URL. That's the whole thing. It runs entirely in your browser and remembers your preferences locally.

### One-liners

If you'd rather launch from the terminal:

```bash
# macOS
open https://saorsa-labs.github.io/news/

# Linux
xdg-open https://saorsa-labs.github.io/news/

# Windows (PowerShell)
start https://saorsa-labs.github.io/news/
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

### Privacy

Everything runs client-side. The page fetches RSS/Atom feeds through public CORS proxies (`api.codetabs.com`, `api.allorigins.win`, `corsproxy.io`, `thingproxy.freeboard.io`) — those proxies see which feeds you're loading, but no personal data is sent to anyone, and your settings, custom feeds and cache live only in your browser's `localStorage`.

---

## How it stays current

A scheduled GitHub Action runs every Sunday and:

1. Pulls the latest README from [foorilla/allainews_sources](https://github.com/foorilla/allainews_sources)
2. Re-runs `build.py` to regenerate `sources.json` and `index.html`
3. Commits if anything changed

Because the page also fetches `sources.json` from this repo on every load, **your downloaded copy auto-updates** without you doing anything.

---

## For maintainers / contributors

You only need this section if you want to regenerate the build locally or work on the code.

### Requirements

- Python 3.9+ (no third-party packages — uses only the standard library)

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
