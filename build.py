#!/usr/bin/env python3
"""
Build sources.json and index.html for the AI News Hub.

Pulls the latest list of RSS sources from foorilla/allainews_sources,
parses them, and writes both files into the same directory as this script.

Usage:  python3 build.py

Requires: Python 3.9+, no third-party packages.
"""
from __future__ import annotations

import html as html_lib
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

REPO_README_URL = (
    "https://raw.githubusercontent.com/foorilla/allainews_sources/main/README.md"
)
ROOT = Path(__file__).resolve().parent

# ---------- Fetch & parse the source list ----------
def fetch_readme() -> str:
    print(f"Fetching {REPO_README_URL} …")
    req = urllib.request.Request(
        REPO_README_URL,
        headers={"User-Agent": "saorsa-labs-news/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")

_SECTION_RE = re.compile(r"^##\s+AI, ML, Big Data\s+(\w+)\s*$", re.MULTILINE)
_ENTRY_RE = re.compile(
    r"^-\s+\[(?P<title>[^\]]+)\]\((?P<home>[^)]+)\)"
    r"(?:\s*-\s*(?P<desc>.*?))?"
    r"\s*\(RSS feed:\s*\[?(?P<feed>https?://[^\s\]\)]+)\]?",
    re.MULTILINE,
)
_CAT = {"news": "News", "podcasts": "Podcasts", "videos": "Videos", "jobs": "Jobs"}
_LAB_HOSTS = (
    "openai.com", "deepmind.com", "huggingface.co", "ai.googleblog.com",
    "anthropic.com", "meta.com", "ainowinstitute.org", "bair.berkeley.edu",
    "blog.eleuther.ai", "stability.ai", "mila.quebec", "blog.ml.cmu.edu",
    "microsoft.com", "developer.nvidia.com", "blog.tensorflow.org",
    "blog.langchain.dev",
)

def parse_sources(text: str) -> list[dict]:
    sections = [(m.group(1).lower(), m.start()) for m in _SECTION_RE.finditer(text)]
    sections.append(("__end__", len(text)))
    out: list[dict] = []
    seen: set[str] = set()
    for i in range(len(sections) - 1):
        cat, start = sections[i]
        end = sections[i + 1][1]
        chunk = text[start:end]
        for m in _ENTRY_RE.finditer(chunk):
            title = html_lib.unescape(m.group("title")).strip()
            home = m.group("home").strip()
            desc = (m.group("desc") or "").strip()
            desc = html_lib.unescape(desc).rstrip("…").strip()
            feed = m.group("feed").strip().rstrip("]").rstrip(")")
            cat_norm = _CAT.get(cat, cat.title())
            try:
                host = urlparse(home).netloc.lower()
                host_feed = urlparse(feed).netloc.lower()
            except Exception:
                host, host_feed = "", ""
            tags: list[str] = []
            if "reddit.com" in host: tags.append("Reddit")
            if "arxiv.org" in host_feed or "arxiv.org" in host: tags.append("Research")
            if "substack.com" in host_feed or "substack.com" in host: tags.append("Newsletter")
            if "medium.com" in host_feed or "medium.com" in host: tags.append("Medium")
            if "youtube.com" in host or "youtube.com" in host_feed: tags.append("YouTube")
            if any(s in host for s in _LAB_HOSTS): tags.append("Lab/Vendor")
            yt = None
            if "youtube.com/feeds/videos.xml?channel_id=" in feed:
                yt = feed.split("channel_id=", 1)[1].strip()
            if feed in seen:
                continue
            seen.add(feed)
            out.append({
                "title": title, "homepage": home, "feed": feed,
                "description": desc, "category": cat_norm,
                "tags": tags, "youtube_channel_id": yt,
            })
    cat_order = {"News": 0, "Podcasts": 1, "Videos": 2, "Jobs": 3}
    out.sort(key=lambda s: (cat_order.get(s["category"], 99), s["title"].lower()))
    return out

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI News Hub — allainews aggregator</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🤖</text></svg>">
<style>
:root {
  --bg: #0b0d10;
  --bg-1: #11151a;
  --bg-2: #181d24;
  --bg-3: #232932;
  --border: #262d36;
  --text: #e6edf3;
  --text-2: #9aa6b2;
  --text-3: #6b7785;
  --accent: #7c5cff;
  --accent-2: #00d4ff;
  --news: #4ea3ff;
  --podcasts: #ff9f43;
  --videos: #ff5c8a;
  --jobs: #2ecc71;
  --shadow: 0 8px 24px rgba(0,0,0,.35);
  --radius: 14px;
  --radius-sm: 10px;
}
[data-theme="light"] {
  --bg: #f7f8fa;
  --bg-1: #ffffff;
  --bg-2: #f1f3f6;
  --bg-3: #e6e9ef;
  --border: #dde1e7;
  --text: #1a1f26;
  --text-2: #50596a;
  --text-3: #8893a0;
  --accent: #6243ff;
  --accent-2: #0094c2;
  --shadow: 0 6px 18px rgba(20,30,50,.08);
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  font-size: 15px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}
a { color: var(--accent-2); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ---------- Header ---------- */
.app-header {
  position: sticky;
  top: 0;
  z-index: 50;
  background: color-mix(in srgb, var(--bg-1) 92%, transparent);
  backdrop-filter: saturate(140%) blur(10px);
  -webkit-backdrop-filter: saturate(140%) blur(10px);
  border-bottom: 1px solid var(--border);
}
.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 12px 20px;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 16px;
  align-items: center;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  letter-spacing: -.01em;
  font-size: 18px;
}
.brand .logo {
  width: 34px; height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  display: grid; place-items: center;
  color: white; font-size: 18px;
  box-shadow: var(--shadow);
}
.brand .sub {
  font-size: 12px;
  color: var(--text-2);
  font-weight: 500;
  margin-top: 2px;
}
.search-wrap {
  position: relative;
  max-width: 560px;
  margin: 0 auto;
  width: 100%;
}
.search-wrap input {
  width: 100%;
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 10px 16px 10px 38px;
  color: var(--text);
  font-size: 14px;
  outline: none;
  transition: border-color .2s, box-shadow .2s;
}
.search-wrap input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 18%, transparent);
}
.search-wrap .icon {
  position: absolute;
  left: 12px; top: 50%;
  transform: translateY(-50%);
  color: var(--text-3);
  pointer-events: none;
}
.actions { display: flex; gap: 8px; align-items: center; }
.btn {
  appearance: none;
  background: var(--bg-2);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 8px 14px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: background .15s, border-color .15s, transform .05s;
}
.btn:hover { background: var(--bg-3); }
.btn:active { transform: translateY(1px); }
.btn.primary {
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  border-color: transparent;
  color: white;
}
.btn.icon-only { padding: 8px 10px; }

.tabs {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--border);
  overflow-x: auto;
  scrollbar-width: none;
}
.tabs::-webkit-scrollbar { display: none; }
.tab {
  background: none;
  border: none;
  color: var(--text-2);
  padding: 12px 16px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  border-bottom: 2px solid transparent;
  white-space: nowrap;
  transition: color .15s, border-color .15s;
}
.tab:hover { color: var(--text); }
.tab.active {
  color: var(--text);
  border-bottom-color: var(--accent);
}
.tab .count {
  background: var(--bg-3);
  color: var(--text-2);
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 999px;
  margin-left: 6px;
}
.tab.active .count { background: color-mix(in srgb, var(--accent) 25%, transparent); color: var(--text); }

/* ---------- Layout ---------- */
.app {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 24px;
  align-items: start;
}
.sidebar {
  position: sticky;
  top: 110px;
  background: var(--bg-1);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  max-height: calc(100vh - 130px);
  overflow-y: auto;
}
.sidebar h3 {
  font-size: 11px;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--text-3);
  margin: 16px 0 8px;
  font-weight: 700;
}
.sidebar h3:first-child { margin-top: 0; }
.filter-list { display: flex; flex-direction: column; gap: 4px; }
.filter-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-2);
  user-select: none;
  border: 1px solid transparent;
}
.filter-item:hover { background: var(--bg-2); color: var(--text); }
.filter-item.active {
  background: color-mix(in srgb, var(--accent) 18%, transparent);
  color: var(--text);
  border-color: color-mix(in srgb, var(--accent) 40%, transparent);
}
.filter-item .dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  margin-right: 8px;
  flex-shrink: 0;
}
.dot.News { background: var(--news); }
.dot.Podcasts { background: var(--podcasts); }
.dot.Videos { background: var(--videos); }
.dot.Jobs { background: var(--jobs); }
.filter-item .label-wrap { display: flex; align-items: center; flex: 1; min-width: 0; }
.filter-item .label-wrap > span:last-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.filter-item .num { color: var(--text-3); font-size: 11px; font-variant-numeric: tabular-nums; }

.progress-card {
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 12px;
  margin-bottom: 12px;
}
.progress-card .row { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-2); margin-bottom: 6px; }
.progress-bar {
  height: 6px; background: var(--bg-3); border-radius: 999px; overflow: hidden;
}
.progress-fill {
  height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-2));
  width: 0%; transition: width .3s ease;
}
.progress-card .controls { display: flex; gap: 6px; margin-top: 10px; }
.progress-card .btn { padding: 6px 10px; font-size: 12px; flex: 1; justify-content: center; }

/* ---------- Main ---------- */
.main { min-width: 0; }
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 12px;
  flex-wrap: wrap;
}
.toolbar .info { color: var(--text-2); font-size: 13px; }
.toolbar .info b { color: var(--text); }
.toolbar .sort { display: flex; gap: 6px; }
.chip {
  background: var(--bg-2);
  border: 1px solid var(--border);
  color: var(--text-2);
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  cursor: pointer;
  transition: all .15s;
}
.chip:hover { color: var(--text); }
.chip.active {
  background: color-mix(in srgb, var(--accent) 20%, transparent);
  color: var(--text);
  border-color: color-mix(in srgb, var(--accent) 50%, transparent);
}

/* Cards */
.timeline { display: grid; gap: 12px; }
.card {
  background: var(--bg-1);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 18px;
  transition: border-color .15s, transform .05s;
}
.card:hover { border-color: color-mix(in srgb, var(--accent) 35%, var(--border)); }
.card .meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--text-2);
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.card .src-pill {
  font-weight: 600;
  font-size: 12px;
  padding: 3px 9px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--bg-2);
  color: var(--text);
}
.card .src-pill.News { color: var(--news); border-color: color-mix(in srgb, var(--news) 35%, var(--border)); }
.card .src-pill.Podcasts { color: var(--podcasts); border-color: color-mix(in srgb, var(--podcasts) 35%, var(--border)); }
.card .src-pill.Videos { color: var(--videos); border-color: color-mix(in srgb, var(--videos) 35%, var(--border)); }
.card .src-pill.Jobs { color: var(--jobs); border-color: color-mix(in srgb, var(--jobs) 35%, var(--border)); }
.card h2 {
  margin: 0 0 6px;
  font-size: 17px;
  font-weight: 600;
  line-height: 1.35;
  letter-spacing: -.005em;
}
.card h2 a { color: var(--text); }
.card h2 a:hover { color: var(--accent-2); text-decoration: none; }
.card .summary {
  color: var(--text-2);
  font-size: 14px;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.card.has-thumb { display: grid; grid-template-columns: 200px 1fr; gap: 16px; }
.card.has-thumb .thumb {
  width: 200px; height: 112px;
  border-radius: 10px;
  background: var(--bg-2) center/cover no-repeat;
  flex-shrink: 0;
}
.card .tag-row { margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap; }
.card .tag {
  font-size: 11px;
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 2px 8px;
  color: var(--text-2);
}

/* Video grid */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.video-card {
  background: var(--bg-1);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  transition: transform .15s, border-color .15s;
}
.video-card:hover {
  border-color: color-mix(in srgb, var(--accent) 35%, var(--border));
  transform: translateY(-2px);
}
.video-card .thumb {
  aspect-ratio: 16/9;
  background: var(--bg-2) center/cover no-repeat;
  position: relative;
}
.video-card .thumb::after {
  content: "";
  position: absolute; inset: 0;
  background: linear-gradient(180deg, transparent 50%, rgba(0,0,0,.6));
  pointer-events: none;
}
.video-card .play {
  position: absolute;
  inset: 0;
  display: grid; place-items: center;
  color: white; font-size: 36px;
  opacity: 0;
  transition: opacity .2s;
}
.video-card:hover .play { opacity: 1; }
.video-card .body { padding: 12px 14px; }
.video-card h3 {
  margin: 0 0 6px;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.video-card h3 a { color: var(--text); }
.video-card .meta { font-size: 12px; color: var(--text-2); display: flex; justify-content: space-between; }

/* Sources tab */
.sources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}
.source-card {
  background: var(--bg-1);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 14px;
  transition: border-color .15s;
}
.source-card:hover { border-color: color-mix(in srgb, var(--accent) 35%, var(--border)); }
.source-card h4 {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.source-card h4 a { color: var(--text); }
.source-card .desc {
  font-size: 12px;
  color: var(--text-2);
  margin: 4px 0 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.source-card .footer { display: flex; justify-content: space-between; font-size: 11px; color: var(--text-3); }

/* States */
.state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-2);
}
.state .icon { font-size: 40px; margin-bottom: 12px; }
.spinner {
  display: inline-block;
  width: 14px; height: 14px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.error-banner {
  background: color-mix(in srgb, #ff4d6d 15%, transparent);
  border: 1px solid color-mix(in srgb, #ff4d6d 40%, transparent);
  color: var(--text);
  padding: 10px 14px;
  border-radius: 10px;
  margin-bottom: 12px;
  font-size: 13px;
}

/* Custom feed badge + remove button */
.source-card.is-custom { border-color: color-mix(in srgb, var(--accent) 35%, var(--border)); }
.custom-badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .04em;
  text-transform: uppercase;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  color: white;
  padding: 2px 7px;
  border-radius: 4px;
}
.remove-btn {
  background: none;
  border: 1px solid var(--border);
  color: var(--text-3);
  border-radius: 6px;
  padding: 2px 7px;
  font-size: 11px;
  cursor: pointer;
}
.remove-btn:hover { background: color-mix(in srgb, #ff4d6d 15%, transparent); border-color: #ff4d6d; color: var(--text); }

/* Sources tab toolbar */
.sources-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  padding: 14px 16px;
  background: var(--bg-1);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  gap: 12px;
  flex-wrap: wrap;
}
.sources-toolbar .stats { color: var(--text-2); font-size: 13px; }
.sources-toolbar .stats b { color: var(--text); }

/* Modal */
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(8, 10, 14, .65);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  display: grid; place-items: center;
  z-index: 1000;
  padding: 20px;
  animation: fade .15s ease;
}
@keyframes fade { from { opacity: 0; } to { opacity: 1; } }
.modal {
  background: var(--bg-1);
  border: 1px solid var(--border);
  border-radius: 16px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 20px 50px rgba(0,0,0,.5);
  overflow: hidden;
  animation: pop .2s cubic-bezier(.2,.8,.3,1.2);
}
@keyframes pop { from { transform: scale(.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }
.modal header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  display: flex; justify-content: space-between; align-items: center;
}
.modal header h3 { margin: 0; font-size: 16px; font-weight: 600; }
.modal header .close {
  background: none; border: none; color: var(--text-2);
  font-size: 22px; cursor: pointer; line-height: 1; padding: 4px 8px;
  border-radius: 6px;
}
.modal header .close:hover { background: var(--bg-2); color: var(--text); }
.modal .body { padding: 18px 20px; }
.modal .field { margin-bottom: 14px; }
.modal .field label {
  display: block; margin-bottom: 6px;
  font-size: 12px; color: var(--text-2); font-weight: 500;
}
.modal .field input, .modal .field select {
  width: 100%;
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 9px 12px;
  color: var(--text);
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: border-color .15s, box-shadow .15s;
}
.modal .field input:focus, .modal .field select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 18%, transparent);
}
.modal .field .help { font-size: 11px; color: var(--text-3); margin-top: 4px; }
.modal .feedback {
  font-size: 13px;
  padding: 8px 10px;
  border-radius: 8px;
  margin-bottom: 12px;
}
.modal .feedback.error { background: color-mix(in srgb, #ff4d6d 18%, transparent); color: var(--text); }
.modal .feedback.info { background: var(--bg-2); color: var(--text-2); display: flex; align-items: center; gap: 8px; }
.modal footer {
  padding: 14px 20px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  background: var(--bg-2);
}

/* Auto-update toast */
.toast {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  background: var(--bg-1); border: 1px solid var(--border);
  padding: 10px 18px; border-radius: 999px;
  box-shadow: var(--shadow); z-index: 2000; font-size: 13px; color: var(--text);
  animation: toast-in .25s, toast-out .35s 4.6s forwards;
  white-space: nowrap;
}
@keyframes toast-in { from { opacity: 0; transform: translateX(-50%) translateY(10px); } }
@keyframes toast-out { to { opacity: 0; transform: translateX(-50%) translateY(10px); } }

/* Mobile */
@media (max-width: 900px) {
  .app { grid-template-columns: 1fr; }
  .sidebar { position: static; max-height: none; }
  .header-inner { grid-template-columns: 1fr auto; }
  .search-wrap { grid-column: 1 / -1; order: 3; max-width: none; }
  .card.has-thumb { grid-template-columns: 1fr; }
  .card.has-thumb .thumb { width: 100%; height: 180px; }
}
.hidden { display: none !important; }
</style>
</head>
<body data-theme="dark">

<header class="app-header">
  <div class="header-inner">
    <div class="brand">
      <div class="logo">🤖</div>
      <div>
        <div>AI News Hub</div>
        <div class="sub">__SOURCE_COUNT__ sources · foorilla/allainews</div>
      </div>
    </div>
    <div class="search-wrap">
      <span class="icon">🔍</span>
      <input id="search" type="text" placeholder="Search titles, sources, descriptions…" autocomplete="off">
    </div>
    <div class="actions">
      <button class="btn icon-only" id="theme-toggle" title="Toggle theme">🌗</button>
      <button class="btn" id="add-feed-btn" title="Add a custom feed">+ Feed</button>
      <button class="btn" id="refresh-btn" title="Force refresh all feeds (ignores cache)">↻ Refresh</button>
    </div>
  </div>
  <nav class="tabs" id="tabs">
    <button class="tab active" data-view="timeline">📰 Timeline <span class="count" id="cnt-timeline">0</span></button>
    <button class="tab" data-view="videos">🎬 Videos <span class="count" id="cnt-videos">0</span></button>
    <button class="tab" data-view="podcasts">🎙️ Podcasts <span class="count" id="cnt-podcasts">0</span></button>
    <button class="tab" data-view="sources">📚 Sources <span class="count" id="cnt-sources">0</span></button>
  </nav>
</header>

<div class="app">
  <aside class="sidebar">
    <div class="progress-card">
      <div class="row"><span id="prog-label">Loading feeds…</span><span id="prog-num">0/0</span></div>
      <div class="progress-bar"><div class="progress-fill" id="prog-fill"></div></div>
      <div class="controls">
        <button class="btn" id="pause-btn">⏸ Pause</button>
        <button class="btn" id="loadall-btn">Load all</button>
      </div>
    </div>
    <h3>Categories</h3>
    <div class="filter-list" id="cat-list"></div>
    <h3>Tags</h3>
    <div class="filter-list" id="tag-list"></div>
    <h3>Time</h3>
    <div class="filter-list" id="time-list">
      <div class="filter-item active" data-time="all"><div class="label-wrap"><span>Any time</span></div></div>
      <div class="filter-item" data-time="24h"><div class="label-wrap"><span>Last 24 hours</span></div></div>
      <div class="filter-item" data-time="week"><div class="label-wrap"><span>Last 7 days</span></div></div>
      <div class="filter-item" data-time="month"><div class="label-wrap"><span>Last 30 days</span></div></div>
    </div>
  </aside>
  <main class="main">
    <div class="toolbar">
      <div class="info" id="info">Initializing…</div>
      <div class="sort">
        <button class="chip active" data-sort="newest">↓ Newest</button>
        <button class="chip" data-sort="oldest">↑ Oldest</button>
      </div>
    </div>
    <div id="error-banner"></div>
    <div id="view-timeline" class="timeline"></div>
    <div id="view-videos" class="video-grid hidden"></div>
    <div id="view-podcasts" class="timeline hidden"></div>
    <div id="view-sources" class="sources-grid hidden"></div>
    <div id="empty-state" class="state hidden">
      <div class="icon">📭</div>
      <div>No items match your filters yet.</div>
    </div>
  </main>
</div>

<div id="modal-root"></div>

<template id="add-feed-modal-tpl">
  <div class="modal-backdrop">
    <div class="modal" role="dialog" aria-labelledby="add-feed-title">
      <header>
        <h3 id="add-feed-title">Add a custom feed</h3>
        <button class="close" data-close="1">×</button>
      </header>
      <div class="body">
        <div class="feedback" id="modal-feedback" style="display:none"></div>
        <div class="field">
          <label>RSS / Atom feed URL <span style="color:#ff8da3">*</span></label>
          <input type="url" id="feed-url" placeholder="https://example.com/feed.xml" autocomplete="off">
          <div class="help">Paste any RSS or Atom URL — including YouTube channel feeds.</div>
        </div>
        <div class="field">
          <label>Title (optional — auto-detected if empty)</label>
          <input type="text" id="feed-title" placeholder="">
        </div>
        <div class="field">
          <label>Category</label>
          <select id="feed-category">
            <option value="News">News</option>
            <option value="Podcasts">Podcasts</option>
            <option value="Videos">Videos</option>
            <option value="Jobs">Jobs</option>
          </select>
        </div>
        <div class="field">
          <label>Tags (comma-separated, optional)</label>
          <input type="text" id="feed-tags" placeholder="Newsletter, Lab/Vendor, …">
        </div>
      </div>
      <footer>
        <button class="btn" data-close="1">Cancel</button>
        <button class="btn primary" id="feed-submit">Add feed</button>
      </footer>
    </div>
  </div>
</template>

<script id="sources-data" type="application/json">__SOURCES_JSON__</script>
<script>
"use strict";

let BUILTIN_SOURCES = JSON.parse(document.getElementById('sources-data').textContent);
const REMOTE_SOURCES_URL = 'https://raw.githubusercontent.com/saorsa-labs/news/main/sources.json';
let CUSTOM_FEEDS = [];
try {
  const raw = localStorage.getItem('ainewshub:custom_feeds:v1');
  if (raw) CUSTOM_FEEDS = JSON.parse(raw) || [];
} catch {}
let SOURCES = [...BUILTIN_SOURCES, ...CUSTOM_FEEDS];
function persistCustomFeeds() {
  try { localStorage.setItem('ainewshub:custom_feeds:v1', JSON.stringify(CUSTOM_FEEDS)); } catch {}
}
function rebuildSources() {
  SOURCES = [...BUILTIN_SOURCES, ...CUSTOM_FEEDS];
}

// ---------- State ----------
const state = {
  view: 'timeline',
  query: '',
  sort: 'newest',
  catFilter: new Set(),       // empty = all
  tagFilter: new Set(),       // empty = all
  timeFilter: 'all',
  items: [],                  // { source, title, link, date, summary, image, video, category, tags }
  itemKeys: new Set(),
  loadedSources: new Set(),
  failedSources: new Set(),
  paused: false,
  loadAll: false,
  startedAt: Date.now(),
};

const PROXIES = [
  url => 'https://api.codetabs.com/v1/proxy?quest=' + encodeURIComponent(url),
  url => 'https://api.allorigins.win/raw?url=' + encodeURIComponent(url),
  url => 'https://corsproxy.io/?' + encodeURIComponent(url),
  url => 'https://thingproxy.freeboard.io/fetch/' + url,
];
function shuffledProxies() {
  // Rotate first index over time to spread load across proxies
  const k = Math.floor(Date.now() / 120000) % PROXIES.length;
  return [...PROXIES.slice(k), ...PROXIES.slice(0, k)];
}

const CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000;  // 7 days
const CACHE_KEY = 'ainewshub:cache:v2';
const CUSTOM_FEEDS_KEY = 'ainewshub:custom_feeds:v1';

// ---------- Cache ----------
function loadCache() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch { return {}; }
}
function saveCache(cache) {
  try {
    // Cap cache size to avoid quota errors
    const entries = Object.entries(cache);
    if (entries.length > 400) {
      entries.sort((a, b) => (b[1].ts || 0) - (a[1].ts || 0));
      cache = Object.fromEntries(entries.slice(0, 400));
    }
    localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
  } catch (e) {
    // Quota? wipe and retry once
    try { localStorage.removeItem(CACHE_KEY); } catch {}
  }
}
let cache = loadCache();

// ---------- Helpers ----------
function normalizeFeedUrl(url) {
  // Reddit blocks the regular RSS for many user agents — use old.reddit.com which is friendlier
  if (/(?:^|\/\/)(www\.)?reddit\.com\//.test(url)) {
    url = url.replace(/^https?:\/\/(www\.)?reddit\.com/i, 'https://old.reddit.com');
    if (!/\.rss(\?|$)/.test(url) && !/\.json/.test(url)) {
      url = url.replace(/\/?$/, '/.rss');
    }
  }
  return url;
}
function timeAgo(date) {
  if (!date) return '';
  const d = new Date(date);
  if (isNaN(d)) return '';
  const sec = Math.floor((Date.now() - d.getTime()) / 1000);
  if (sec < 0) return 'just now';
  if (sec < 60) return sec + 's ago';
  const min = Math.floor(sec / 60);
  if (min < 60) return min + 'm ago';
  const hr = Math.floor(min / 60);
  if (hr < 24) return hr + 'h ago';
  const day = Math.floor(hr / 24);
  if (day < 30) return day + 'd ago';
  const mo = Math.floor(day / 30);
  if (mo < 12) return mo + 'mo ago';
  return Math.floor(mo / 12) + 'y ago';
}
function stripHtml(s) {
  if (!s) return '';
  const tmp = document.createElement('div');
  tmp.innerHTML = s;
  let txt = tmp.textContent || tmp.innerText || '';
  return txt.replace(/\s+/g, ' ').trim();
}
function escAttr(s) { return String(s || '').replace(/"/g, '&quot;'); }
function escText(s) { const d = document.createElement('div'); d.textContent = s == null ? '' : s; return d.innerHTML; }

function timeWindowMs(filter) {
  switch (filter) {
    case '24h': return 24 * 3600 * 1000;
    case 'week': return 7 * 24 * 3600 * 1000;
    case 'month': return 30 * 24 * 3600 * 1000;
    default: return Infinity;
  }
}

// ---------- Fetch + parse ----------
async function fetchWithProxies(url) {
  let lastErr;
  for (const p of shuffledProxies()) {
    try {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), 18000);
      const r = await fetch(p(url), { signal: ctrl.signal, redirect: 'follow' });
      clearTimeout(t);
      if (!r.ok) { lastErr = new Error('HTTP ' + r.status); continue; }
      const text = await r.text();
      if (!text || text.length < 60) { lastErr = new Error('empty'); continue; }
      return text;
    } catch (e) { lastErr = e; continue; }
  }
  throw lastErr || new Error('all proxies failed');
}

function parseFeed(xmlText, source) {
  const doc = new DOMParser().parseFromString(xmlText, 'application/xml');
  if (doc.querySelector('parsererror')) {
    // Try as HTML — some proxies wrap content
    return [];
  }
  const out = [];
  // RSS 2.0 / RSS 1.0
  const items = doc.querySelectorAll('item');
  if (items.length) {
    items.forEach(it => {
      const title = stripHtml(it.querySelector('title')?.textContent);
      const link = it.querySelector('link')?.textContent?.trim() || '';
      const pub = it.querySelector('pubDate, dc\\:date, date')?.textContent?.trim();
      const desc = it.querySelector('description, content\\:encoded, summary')?.textContent || '';
      // Find image
      let img = it.querySelector('media\\:thumbnail, media\\:content')?.getAttribute('url')
            || it.querySelector('enclosure[type^="image"]')?.getAttribute('url') || '';
      if (!img) {
        const m = desc.match(/<img[^>]+src=['"]([^'"]+)['"]/i);
        if (m) img = m[1];
      }
      out.push({
        source: source.title,
        sourceCategory: source.category,
        sourceTags: source.tags,
        sourceFeed: source.feed,
        title: title || '(no title)',
        link, date: pub, image: img,
        summary: stripHtml(desc).slice(0, 400),
      });
    });
    return out;
  }
  // Atom (YouTube, Atom feeds)
  const entries = doc.querySelectorAll('entry');
  entries.forEach(en => {
    const title = stripHtml(en.querySelector('title')?.textContent);
    let link = '';
    en.querySelectorAll('link').forEach(l => {
      const rel = l.getAttribute('rel') || 'alternate';
      if (rel === 'alternate' && !link) link = l.getAttribute('href') || '';
    });
    if (!link) link = en.querySelector('link')?.getAttribute('href') || en.querySelector('link')?.textContent || '';
    const pub = en.querySelector('published, updated')?.textContent?.trim();
    const summary = en.querySelector('summary, content, media\\:description')?.textContent || '';
    const img = en.querySelector('media\\:thumbnail')?.getAttribute('url') || '';
    out.push({
      source: source.title,
      sourceCategory: source.category,
      sourceTags: source.tags,
      sourceFeed: source.feed,
      title: title || '(no title)',
      link, date: pub, image: img,
      summary: stripHtml(summary).slice(0, 400),
      isVideo: !!source.youtube_channel_id,
    });
  });
  return out;
}

async function loadSource(source) {
  const key = source.feed;
  // Try cache
  const cached = cache[key];
  if (cached && (Date.now() - (cached.ts || 0)) < CACHE_TTL_MS) {
    return cached.items || [];
  }
  const url = normalizeFeedUrl(source.feed);
  const xml = await fetchWithProxies(url);
  const items = parseFeed(xml, source);
  cache[key] = { ts: Date.now(), items: items.slice(0, 25) };
  return cache[key].items;
}

// ---------- Render ----------
const els = {
  timeline: document.getElementById('view-timeline'),
  videos: document.getElementById('view-videos'),
  podcasts: document.getElementById('view-podcasts'),
  sources: document.getElementById('view-sources'),
  empty: document.getElementById('empty-state'),
  info: document.getElementById('info'),
  catList: document.getElementById('cat-list'),
  tagList: document.getElementById('tag-list'),
  cntTimeline: document.getElementById('cnt-timeline'),
  cntVideos: document.getElementById('cnt-videos'),
  cntPodcasts: document.getElementById('cnt-podcasts'),
  cntSources: document.getElementById('cnt-sources'),
  progLabel: document.getElementById('prog-label'),
  progNum: document.getElementById('prog-num'),
  progFill: document.getElementById('prog-fill'),
  pauseBtn: document.getElementById('pause-btn'),
  loadAllBtn: document.getElementById('loadall-btn'),
  errBanner: document.getElementById('error-banner'),
};

function buildSidebar() {
  const cats = {};
  const tags = {};
  SOURCES.forEach(s => {
    cats[s.category] = (cats[s.category] || 0) + 1;
    (s.tags || []).forEach(t => tags[t] = (tags[t] || 0) + 1);
  });
  const catOrder = ['News', 'Podcasts', 'Videos', 'Jobs'];
  els.catList.innerHTML = catOrder.filter(c => cats[c]).map(c =>
    `<div class="filter-item" data-cat="${c}"><div class="label-wrap"><span class="dot ${c}"></span><span>${c}</span></div><span class="num">${cats[c]}</span></div>`
  ).join('');
  els.tagList.innerHTML = Object.entries(tags).sort((a,b)=>b[1]-a[1]).map(([t, n]) =>
    `<div class="filter-item" data-tag="${escAttr(t)}"><div class="label-wrap"><span>${escText(t)}</span></div><span class="num">${n}</span></div>`
  ).join('');
  els.cntSources.textContent = SOURCES.length;
}

function applyFilters(items) {
  const q = state.query.toLowerCase();
  const win = timeWindowMs(state.timeFilter);
  const now = Date.now();
  return items.filter(it => {
    if (state.catFilter.size && !state.catFilter.has(it.sourceCategory)) return false;
    if (state.tagFilter.size) {
      const has = (it.sourceTags || []).some(t => state.tagFilter.has(t));
      if (!has) return false;
    }
    if (q) {
      const hay = (it.title + ' ' + it.source + ' ' + (it.summary || '')).toLowerCase();
      if (!hay.includes(q)) return false;
    }
    if (win !== Infinity) {
      const d = it.date ? new Date(it.date).getTime() : 0;
      if (!d || (now - d) > win) return false;
    }
    return true;
  });
}

function sortItems(items) {
  const dir = state.sort === 'oldest' ? 1 : -1;
  return items.slice().sort((a, b) => {
    const da = a.date ? new Date(a.date).getTime() : 0;
    const db = b.date ? new Date(b.date).getTime() : 0;
    return (da - db) * dir;
  });
}

function renderTimeline() {
  const items = sortItems(applyFilters(state.items.filter(i => i.sourceCategory !== 'Videos')));
  els.cntTimeline.textContent = items.length;
  if (!items.length) {
    els.timeline.innerHTML = '';
    if (state.view === 'timeline') els.empty.classList.remove('hidden');
    return;
  }
  els.empty.classList.add('hidden');
  // Cap render to 200 for perf
  const render = items.slice(0, 200);
  els.timeline.innerHTML = render.map(cardHtml).join('');
}

function renderPodcasts() {
  const items = sortItems(applyFilters(state.items.filter(i => i.sourceCategory === 'Podcasts')));
  els.cntPodcasts.textContent = items.length;
  if (!items.length) {
    els.podcasts.innerHTML = '<div class="state"><div class="icon">🎙️</div><div>No podcast episodes loaded yet.</div></div>';
    return;
  }
  els.podcasts.innerHTML = items.slice(0, 200).map(cardHtml).join('');
}

function renderVideos() {
  const items = sortItems(applyFilters(state.items.filter(i => i.sourceCategory === 'Videos')));
  els.cntVideos.textContent = items.length;
  if (!items.length) {
    els.videos.innerHTML = '<div class="state"><div class="icon">🎬</div><div>No videos loaded yet. Loading…</div></div>';
    return;
  }
  els.videos.innerHTML = items.slice(0, 120).map(it => {
    let thumb = it.image;
    // Derive YouTube thumbnail from video URL if missing
    if (!thumb && it.link) {
      const m = it.link.match(/[?&]v=([\w-]{6,})/) || it.link.match(/\/watch\?v=([\w-]{6,})/);
      if (m) thumb = `https://i.ytimg.com/vi/${m[1]}/hqdefault.jpg`;
    }
    return `
      <a class="video-card" href="${escAttr(it.link)}" target="_blank" rel="noopener">
        <div class="thumb" style="${thumb ? `background-image:url('${escAttr(thumb)}')` : ''}">
          <div class="play">▶</div>
        </div>
        <div class="body">
          <h3>${escText(it.title)}</h3>
          <div class="meta"><span>${escText(it.source)}</span><span>${escText(timeAgo(it.date))}</span></div>
        </div>
      </a>
    `;
  }).join('');
}

function renderSources() {
  const q = state.query.toLowerCase();
  const filtered = SOURCES.filter(s => {
    if (state.catFilter.size && !state.catFilter.has(s.category)) return false;
    if (state.tagFilter.size && !(s.tags || []).some(t => state.tagFilter.has(t))) return false;
    if (q) {
      const hay = (s.title + ' ' + (s.description || '') + ' ' + s.feed).toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
  // Sort custom first
  filtered.sort((a, b) => Number(!!b.isCustom) - Number(!!a.isCustom));
  const customCount = CUSTOM_FEEDS.length;
  const toolbar = `
    <div class="sources-toolbar">
      <div class="stats">
        <b>${SOURCES.length}</b> total · <b>${customCount}</b> custom · <b>${BUILTIN_SOURCES.length}</b> built-in
      </div>
      <button class="btn primary" id="sources-add-btn">+ Add custom feed</button>
    </div>
  `;
  const cards = filtered.map(s => {
    const customMarker = s.isCustom
      ? `<span class="custom-badge">custom</span>`
      : '';
    const removeBtn = s.isCustom
      ? `<button class="remove-btn" data-remove="${escAttr(s.feed)}" title="Remove this feed">remove</button>`
      : '';
    return `
    <div class="source-card${s.isCustom ? ' is-custom' : ''}">
      <div class="meta" style="margin-bottom:6px;justify-content:space-between">
        <div style="display:flex;align-items:center;gap:6px">
          <span class="src-pill ${s.category}">${escText(s.category)}</span>
          ${customMarker}
        </div>
        ${state.loadedSources.has(s.feed) ? '<span style="color:var(--text-3);font-size:11px">✓ loaded</span>' :
          state.failedSources.has(s.feed) ? '<span style="color:#ff6b8a;font-size:11px">✕ failed</span>' :
          '<span style="color:var(--text-3);font-size:11px">·</span>'}
      </div>
      <h4><a href="${escAttr(s.homepage || s.feed)}" target="_blank" rel="noopener">${escText(s.title)}</a></h4>
      <div class="desc">${escText(s.description || '')}</div>
      <div class="footer">
        <span>${(s.tags || []).map(t => escText(t)).join(' · ') || '—'}</span>
        <span style="display:flex;gap:6px;align-items:center">
          ${removeBtn}
          <a href="${escAttr(s.feed)}" target="_blank" rel="noopener" title="${escAttr(s.feed)}">RSS</a>
        </span>
      </div>
    </div>
  `;
  }).join('');
  els.sources.innerHTML = toolbar + `<div class="sources-grid" style="display:grid;grid-template-columns:repeat(auto-fill, minmax(260px, 1fr));gap:12px">${cards}</div>`;
  // Wire up the in-tab buttons
  document.getElementById('sources-add-btn')?.addEventListener('click', openAddFeedModal);
  els.sources.querySelectorAll('[data-remove]').forEach(btn => {
    btn.addEventListener('click', () => removeCustomFeed(btn.getAttribute('data-remove')));
  });
}

function cardHtml(it) {
  const ago = timeAgo(it.date);
  const dotCat = it.sourceCategory || 'News';
  const tags = (it.sourceTags || []).slice(0, 3);
  const hasThumb = !!it.image;
  return `
    <article class="card${hasThumb ? ' has-thumb' : ''}">
      ${hasThumb ? `<div class="thumb" style="background-image:url('${escAttr(it.image)}')"></div>` : ''}
      <div>
        <div class="meta">
          <span class="src-pill ${dotCat}">${escText(it.source)}</span>
          ${ago ? `<span>${escText(ago)}</span>` : ''}
        </div>
        <h2><a href="${escAttr(it.link)}" target="_blank" rel="noopener">${escText(it.title)}</a></h2>
        ${it.summary ? `<p class="summary">${escText(it.summary)}</p>` : ''}
        ${tags.length ? `<div class="tag-row">${tags.map(t => `<span class="tag">${escText(t)}</span>`).join('')}</div>` : ''}
      </div>
    </article>
  `;
}

function setView(v) {
  state.view = v;
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.view === v));
  ['timeline','videos','podcasts','sources'].forEach(k => {
    els[k].classList.toggle('hidden', k !== v);
  });
  els.empty.classList.add('hidden');
  if (v === 'timeline') renderTimeline();
  if (v === 'videos') renderVideos();
  if (v === 'podcasts') renderPodcasts();
  if (v === 'sources') renderSources();
}

function renderAll() {
  renderTimeline();
  renderVideos();
  renderPodcasts();
  renderSources();
}

function updateInfo() {
  const total = state.loadedSources.size + state.failedSources.size;
  els.progNum.textContent = `${total}/${SOURCES.length}`;
  els.progFill.style.width = (total / SOURCES.length * 100).toFixed(1) + '%';
  if (state.paused) {
    els.progLabel.innerHTML = `Paused`;
  } else if (total >= SOURCES.length) {
    els.progLabel.innerHTML = `Done · ${state.failedSources.size} failed`;
  } else {
    els.progLabel.innerHTML = `<span class="spinner"></span> Loading…`;
  }
  els.info.innerHTML = `<b>${state.items.length}</b> items · <b>${state.loadedSources.size}</b> sources loaded${state.failedSources.size ? ` · <span style="color:#ff8da3">${state.failedSources.size} failed</span>` : ''}`;
}

// ---------- Loader pipeline ----------
function pickInitialBatch() {
  // Prioritize: News (especially well-known), Videos, Podcasts. Skip Reddit (often blocked) until "Load all".
  const priority = (s) => {
    let p = 0;
    if (s.category === 'News') p += 0;
    else if (s.category === 'Videos') p += 1;
    else if (s.category === 'Podcasts') p += 2;
    else p += 3;
    if ((s.tags || []).includes('Reddit')) p += 10;
    if ((s.tags || []).includes('Lab/Vendor')) p -= 1;
    return p;
  };
  const sorted = SOURCES.slice().sort((a,b) => priority(a) - priority(b));
  return sorted.slice(0, 60);  // initial batch
}

async function runLoader(sources) {
  const concurrency = 6;
  let idx = 0;
  let active = 0;
  return new Promise(resolve => {
    const tick = () => {
      if (state.paused) {
        if (active === 0) return;  // resume will retick
      }
      while (!state.paused && active < concurrency && idx < sources.length) {
        const s = sources[idx++];
        active++;
        loadSource(s).then(items => {
          state.loadedSources.add(s.feed);
          for (const it of items) {
            const k = (it.link || it.title) + '|' + s.feed;
            if (state.itemKeys.has(k)) continue;
            state.itemKeys.add(k);
            state.items.push(it);
          }
          if (state.loadedSources.size % 4 === 0) {
            saveCache(cache);
            renderAll();
          }
        }).catch(() => {
          state.failedSources.add(s.feed);
        }).finally(() => {
          active--;
          updateInfo();
          if (idx >= sources.length && active === 0) {
            saveCache(cache);
            renderAll();
            resolve();
          } else {
            setTimeout(tick, 0);
          }
        });
      }
      if (idx >= sources.length && active === 0) resolve();
    };
    tick();
    state.resumeTick = tick;  // for pause/resume
  });
}

async function loadAll() {
  const remaining = SOURCES.filter(s => !state.loadedSources.has(s.feed) && !state.failedSources.has(s.feed));
  if (!remaining.length) return;
  els.loadAllBtn.disabled = true;
  els.loadAllBtn.textContent = 'Loading…';
  await runLoader(remaining);
  els.loadAllBtn.textContent = '✓ All loaded';
}

// ---------- Auto-update from saorsa-labs/news ----------
function showToast(msg) {
  const el = document.createElement('div');
  el.className = 'toast';
  el.innerHTML = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 5200);
}

async function autoUpdateSources() {
  let text = null;
  try {
    const r = await fetch(REMOTE_SOURCES_URL, { cache: 'no-cache' });
    if (r.ok) text = await r.text();
  } catch {}
  if (!text) {
    try { text = await fetchWithProxies(REMOTE_SOURCES_URL); } catch { return; }
  }
  let remote;
  try { remote = JSON.parse(text); } catch { return; }
  if (!Array.isArray(remote) || remote.length < 50) return;
  const localKeys = new Set(BUILTIN_SOURCES.map(s => s.feed));
  const remoteKeys = new Set(remote.map(s => s.feed));
  const added = remote.filter(s => !localKeys.has(s.feed));
  const removed = BUILTIN_SOURCES.filter(s => !remoteKeys.has(s.feed));
  if (!added.length && !removed.length && remote.length === BUILTIN_SOURCES.length) return;
  BUILTIN_SOURCES = remote;
  rebuildSources();
  buildSidebar();
  renderAll();
  const sub = document.querySelector('.brand .sub');
  if (sub) sub.textContent = `${BUILTIN_SOURCES.length} sources · foorilla/allainews`;
  let msg = '✓ Source list updated';
  if (added.length || removed.length) {
    msg += ` · +${added.length} added · −${removed.length} removed`;
  }
  showToast(msg);
}

async function refreshAll() {
  cache = {};
  saveCache(cache);
  state.items = [];
  state.itemKeys.clear();
  state.loadedSources.clear();
  state.failedSources.clear();
  renderAll();
  updateInfo();
  await runLoader(pickInitialBatch());
  if (state.loadAll) await loadAll();
}

// ---------- Custom feeds ----------
function openAddFeedModal() {
  const tpl = document.getElementById('add-feed-modal-tpl');
  const root = document.getElementById('modal-root');
  root.innerHTML = '';
  root.appendChild(tpl.content.cloneNode(true));
  const backdrop = root.querySelector('.modal-backdrop');
  const closeAll = () => { root.innerHTML = ''; };
  backdrop.addEventListener('click', e => { if (e.target === backdrop) closeAll(); });
  root.querySelectorAll('[data-close]').forEach(b => b.addEventListener('click', closeAll));
  document.addEventListener('keydown', function esc(e) {
    if (e.key === 'Escape') { closeAll(); document.removeEventListener('keydown', esc); }
  });
  const urlInput = root.querySelector('#feed-url');
  setTimeout(() => urlInput.focus(), 50);
  const fb = root.querySelector('#modal-feedback');
  const submit = root.querySelector('#feed-submit');

  async function doSubmit() {
    const url = urlInput.value.trim();
    if (!url) { showFb('error', 'Please enter a feed URL.'); return; }
    if (!/^https?:\/\//i.test(url)) { showFb('error', 'URL must start with http:// or https://'); return; }
    if (SOURCES.some(s => s.feed === url)) { showFb('error', 'That feed is already in your list.'); return; }
    submit.disabled = true;
    submit.innerHTML = '<span class="spinner"></span> Validating…';
    showFb('info', '<span class="spinner"></span> Fetching feed and checking format…');
    try {
      const result = await addCustomFeed({
        feed: url,
        title: root.querySelector('#feed-title').value.trim(),
        category: root.querySelector('#feed-category').value,
        tags: root.querySelector('#feed-tags').value.split(',').map(s => s.trim()).filter(Boolean),
      });
      showFb('info', `✓ Added <b>${escText(result.title)}</b> (${result.itemCount} items). Closing…`);
      setTimeout(closeAll, 700);
    } catch (e) {
      showFb('error', '✕ ' + (e.message || 'Could not add feed'));
      submit.disabled = false;
      submit.textContent = 'Add feed';
    }
  }
  function showFb(kind, html) {
    fb.style.display = '';
    fb.className = 'feedback ' + kind;
    fb.innerHTML = html;
  }
  submit.addEventListener('click', doSubmit);
  urlInput.addEventListener('keydown', e => { if (e.key === 'Enter') doSubmit(); });
}

async function addCustomFeed({ feed, title, category, tags }) {
  // Validate by fetching + parsing
  const xml = await fetchWithProxies(normalizeFeedUrl(feed));
  if (!xml) throw new Error('No data from any proxy');
  const probe = { title: title || 'Custom', category: category || 'News', tags: tags || [], feed };
  const items = parseFeed(xml, probe);
  if (!items.length) throw new Error('No items found in feed (is the URL correct?)');
  // Auto-detect title/description from XML if missing
  let autoTitle = title;
  let autoDesc = '';
  let autoHomepage = '';
  try {
    const doc = new DOMParser().parseFromString(xml, 'application/xml');
    if (!autoTitle) {
      const t = doc.querySelector('channel > title') || doc.querySelector('feed > title');
      if (t) autoTitle = t.textContent.trim();
    }
    const d = doc.querySelector('channel > description') || doc.querySelector('feed > subtitle');
    if (d) autoDesc = d.textContent.trim().slice(0, 200);
    const home = doc.querySelector('channel > link');
    if (home && home.textContent) autoHomepage = home.textContent.trim();
    if (!autoHomepage) {
      const linkAlt = doc.querySelector('feed > link[rel="alternate"]');
      if (linkAlt) autoHomepage = linkAlt.getAttribute('href') || '';
    }
  } catch {}
  if (!autoTitle) autoTitle = new URL(feed).hostname.replace(/^www\./,'');
  if (!autoHomepage) {
    try { const u = new URL(feed); autoHomepage = u.origin; } catch { autoHomepage = feed; }
  }
  // Auto-detect YouTube channel feed
  let yt = null;
  if (/youtube\.com\/feeds\/videos\.xml\?channel_id=/.test(feed)) {
    yt = feed.split('channel_id=', 2)[1].trim();
    if (!category || category === 'News') category = 'Videos';
  }
  const newSrc = {
    title: autoTitle,
    homepage: autoHomepage,
    feed,
    description: autoDesc,
    category: category || 'News',
    tags: Array.from(new Set([...(tags || []), 'Custom'])),
    youtube_channel_id: yt,
    isCustom: true,
  };
  CUSTOM_FEEDS.push(newSrc);
  persistCustomFeeds();
  rebuildSources();
  // Cache items + add to current view
  cache[feed] = { ts: Date.now(), items: items.slice(0, 25) };
  saveCache(cache);
  state.loadedSources.add(feed);
  for (const it of items) {
    const k = (it.link || it.title) + '|' + feed;
    if (state.itemKeys.has(k)) continue;
    state.itemKeys.add(k);
    state.items.push({
      ...it,
      source: newSrc.title,
      sourceCategory: newSrc.category,
      sourceTags: newSrc.tags,
      sourceFeed: feed,
    });
  }
  buildSidebar();
  renderAll();
  updateInfo();
  return { title: newSrc.title, itemCount: items.length };
}

function removeCustomFeed(feedUrl) {
  const idx = CUSTOM_FEEDS.findIndex(f => f.feed === feedUrl);
  if (idx === -1) return;
  if (!confirm(`Remove "${CUSTOM_FEEDS[idx].title}" from your list?`)) return;
  CUSTOM_FEEDS.splice(idx, 1);
  persistCustomFeeds();
  rebuildSources();
  state.items = state.items.filter(it => it.sourceFeed !== feedUrl);
  state.itemKeys = new Set([...state.itemKeys].filter(k => !k.endsWith('|' + feedUrl)));
  state.loadedSources.delete(feedUrl);
  state.failedSources.delete(feedUrl);
  delete cache[feedUrl];
  saveCache(cache);
  buildSidebar();
  renderAll();
  updateInfo();
}

// ---------- Wiring ----------
function bindUI() {
  // Tabs
  document.getElementById('tabs').addEventListener('click', e => {
    const btn = e.target.closest('.tab');
    if (btn) setView(btn.dataset.view);
  });
  // Search
  let searchT;
  document.getElementById('search').addEventListener('input', e => {
    clearTimeout(searchT);
    searchT = setTimeout(() => {
      state.query = e.target.value.trim();
      renderAll();
    }, 150);
  });
  // Sort
  document.querySelectorAll('.chip[data-sort]').forEach(b => {
    b.addEventListener('click', () => {
      document.querySelectorAll('.chip[data-sort]').forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      state.sort = b.dataset.sort;
      renderAll();
    });
  });
  // Cat filter
  els.catList.addEventListener('click', e => {
    const item = e.target.closest('.filter-item');
    if (!item) return;
    const cat = item.dataset.cat;
    if (state.catFilter.has(cat)) state.catFilter.delete(cat);
    else state.catFilter.add(cat);
    item.classList.toggle('active');
    renderAll();
  });
  // Tag filter
  els.tagList.addEventListener('click', e => {
    const item = e.target.closest('.filter-item');
    if (!item) return;
    const tag = item.dataset.tag;
    if (state.tagFilter.has(tag)) state.tagFilter.delete(tag);
    else state.tagFilter.add(tag);
    item.classList.toggle('active');
    renderAll();
  });
  // Time filter
  document.getElementById('time-list').addEventListener('click', e => {
    const item = e.target.closest('.filter-item');
    if (!item) return;
    document.querySelectorAll('#time-list .filter-item').forEach(x => x.classList.remove('active'));
    item.classList.add('active');
    state.timeFilter = item.dataset.time;
    renderAll();
  });
  // Theme toggle
  document.getElementById('theme-toggle').addEventListener('click', () => {
    const cur = document.body.dataset.theme || 'dark';
    const next = cur === 'dark' ? 'light' : 'dark';
    document.body.dataset.theme = next;
    try { localStorage.setItem('ainewshub:theme', next); } catch {}
  });
  try {
    const t = localStorage.getItem('ainewshub:theme');
    if (t) document.body.dataset.theme = t;
  } catch {}
  // Pause / resume
  els.pauseBtn.addEventListener('click', () => {
    state.paused = !state.paused;
    els.pauseBtn.textContent = state.paused ? '▶ Resume' : '⏸ Pause';
    if (!state.paused && state.resumeTick) state.resumeTick();
    updateInfo();
  });
  // Load all
  els.loadAllBtn.addEventListener('click', () => {
    state.loadAll = true;
    loadAll();
  });
  // Refresh
  document.getElementById('refresh-btn').addEventListener('click', refreshAll);
  // Add custom feed (header)
  document.getElementById('add-feed-btn').addEventListener('click', openAddFeedModal);
}

async function init() {
  buildSidebar();
  bindUI();
  renderAll();
  updateInfo();
  // Hydrate from cache first for instant UX
  let hydratedCount = 0;
  for (const s of SOURCES) {
    const c = cache[s.feed];
    if (c && (Date.now() - (c.ts || 0)) < CACHE_TTL_MS && Array.isArray(c.items)) {
      state.loadedSources.add(s.feed);
      for (const it of c.items) {
        const fixed = { ...it, source: s.title, sourceCategory: s.category, sourceTags: s.tags, sourceFeed: s.feed };
        const k = (fixed.link || fixed.title) + '|' + s.feed;
        if (state.itemKeys.has(k)) continue;
        state.itemKeys.add(k);
        state.items.push(fixed);
      }
      hydratedCount++;
    }
  }
  if (hydratedCount) renderAll();
  updateInfo();
  // Kick off network loader for the initial batch
  await runLoader(pickInitialBatch().filter(s => !state.loadedSources.has(s.feed)));
  saveCache(cache);
  renderAll();
  // Background: pull the latest source list from saorsa-labs/news so
  // even downloaded copies stay current as the upstream catalogue grows.
  autoUpdateSources();
}

init().catch(e => {
  els.errBanner.innerHTML = `<div class="error-banner">Init error: ${escText(e.message || e)}</div>`;
});
</script>
</body>
</html>
"""

def main() -> int:
    text = fetch_readme()
    sources = parse_sources(text)
    if len(sources) < 50:
        print(f"ERROR: only parsed {len(sources)} sources — README format may have changed",
              file=sys.stderr)
        return 1
    by_cat: dict[str, int] = {}
    for s in sources:
        by_cat[s["category"]] = by_cat.get(s["category"], 0) + 1
    print(f"Parsed {len(sources)} sources: {by_cat}")

    sources_json = json.dumps(sources, ensure_ascii=False, separators=(",", ":"))
    html_out = (
        HTML.replace("__SOURCES_JSON__", sources_json)
            .replace("__SOURCE_COUNT__", str(len(sources)))
    )

    sources_path = ROOT / "sources.json"
    index_path = ROOT / "index.html"
    sources_path.write_text(json.dumps(sources, indent=2, ensure_ascii=False))
    index_path.write_text(html_out, encoding="utf-8")
    print(f"Wrote {sources_path.name}")
    print(f"Wrote {index_path.name} ({len(html_out):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
