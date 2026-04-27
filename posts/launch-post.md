# Launch post — copy/paste ready

Three flavours below: long (LinkedIn / blog), medium (Mastodon / Bluesky), short (X). Plus a standalone code snippet for the install instructions.

---

## Long — LinkedIn / blog (~250 words)

I gave up trying to keep up with AI and ML news on social media.

The signal-to-noise ratio just wasn't working. Too many takes, not enough substance, and an algorithm picking what I see based on what makes me angry rather than what makes me smarter. So I went back to RSS — the boring, beautiful, decentralised technology that actually works.

The folks at **foorilla** had already done the hard part: a public, curated catalogue of 270+ AI / ML / Big Data feeds — labs, journals, podcasts, YouTube channels, the lot. (https://github.com/foorilla/allainews_sources — go give them a star.)

I spent an evening with Claude turning that list into a clean little reader. Single HTML file. No accounts. No tracking. No ads. No "for you" algorithm. Just a unified timeline, a video grid, a podcast tab, search, filters, light/dark theme. Add your own feeds if you want.

It's live and free for anyone to use:

👉 **https://news.saorsalabs.com/**

Bookmark it and you've got a quiet corner of the internet for actual research and news.

The source list refreshes from upstream every 30 minutes, so new sources appear automatically — even on a downloaded copy.

Want full control? **Fork it and host your own** in five minutes. The whole thing is one HTML file plus a tiny Python build script — MIT licensed, no servers, no databases, no ongoing cost. Run it as your personal reader, customise the source list, never depend on anyone else's infrastructure.

Repo: https://github.com/saorsa-labs/news

Less noise. More signal. That's it.

---

## Medium — Mastodon / Bluesky (~500 chars)

Got fed up with AI/ML news on socials — too much noise, not enough signal. So I took foorilla's curated catalogue of 270+ AI feeds and built a wee reader with Claude.

Single page, no accounts, no tracking, no ads. Timeline / videos / podcasts / search / filters. Auto-updates every 30 mins.

Free for anyone:
👉 https://news.saorsalabs.com/

Or fork & self-host in 5 mins:
🛠️ https://github.com/saorsa-labs/news

Less noise. More signal.

---

## Short — X / Twitter (≤280 chars)

I gave up on AI news on socials — too much noise. Built a wee RSS reader with Claude over foorilla's curated catalogue of 270+ AI feeds. No accounts, no tracking, free.

👉 https://news.saorsalabs.com/
🛠️ https://github.com/saorsa-labs/news (MIT, fork & self-host)

---

## Standalone install / self-host snippet

Use this as a paragraph or pinned reply.

> **Install it on your own machine — three options, easiest first:**
>
> **1. Just open the URL.** Bookmark <https://news.saorsalabs.com/> — that's it. Your settings live in your browser only.
>
> **2. Local copy.** One terminal command:
> ```
> curl -L -o ~/Desktop/news.html https://raw.githubusercontent.com/saorsa-labs/news/main/index.html && open ~/Desktop/news.html
> ```
> Double-click the file anytime. It auto-pulls fresh sources every time you open it.
>
> **3. Run your own copy under your control.** Fork the repo, turn on GitHub Pages, you've got `https://<you>.github.io/news/` in five minutes:
> ```
> gh repo fork saorsa-labs/news --clone=false
> gh api -X POST repos/<your-username>/news/pages \
>   -f 'source[branch]=main' -f 'source[path]=/'
> ```
> The fork inherits the rebuild Action so it keeps itself in sync with the upstream catalogue. Or rip out the auto-update and curate your own list — `sources.json` is a plain flat array, easy to edit by hand.
