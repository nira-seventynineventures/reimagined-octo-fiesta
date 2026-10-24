#!/usr/bin/env python3
"""Build the native journal using only Python's standard library.

Run from this checkout; output defaults to dist, or to the repository root on
the GitHub Pages copy. Published content is supplied in content/journal.json.
"""
from pathlib import Path
from datetime import date, datetime, timezone
from email.utils import format_datetime
from html import escape
from urllib.parse import urlparse
import argparse
import json
import re
import unicodedata
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ARROW = '<svg class="site-icon" viewBox="0 0 14 16" aria-hidden="true" focusable="false"><path d="M1 13.5 12.5 2M7.5 2h5v5"/></svg>'
STAR = '<svg class="site-icon" viewBox="0 0 40 47" aria-hidden="true" focusable="false"><path d="M20 6v35M2.5 23.5h35M7.6 11.1l24.8 24.8M7.6 35.9l24.8-24.8"/></svg>'
SOCIAL_HOSTS = {'www.linkedin.com', 'linkedin.com', 'www.instagram.com', 'instagram.com', 'www.threads.com', 'threads.com', 'www.threads.net', 'threads.net'}


def clean(value):
    """Keep the site's no-emoji presentation for imported social excerpts."""
    return ''.join(c for c in str(value) if unicodedata.category(c) != 'So' and c not in '\ufe0f\ufe0e\u200d\u20e3' and not 0x2194 <= ord(c) <= 0x2199)


def safe_social_url(value):
    parsed = urlparse(value)
    if parsed.scheme != 'https' or parsed.hostname not in SOCIAL_HOSTS or parsed.username or parsed.password:
        raise ValueError('Social links must use an approved HTTPS platform hostname')
    return escape(value, quote=True)


def pretty_date(value):
    return date.fromisoformat(value).strftime('%B %d, %Y').replace(' 0', ' ')


def meta(post):
    parts = [escape(clean(post['category']))]
    if post.get('date'):
        parts.append(f'<time datetime="{escape(post["date"])}">{pretty_date(post["date"])}</time>')
    return '<div class="journal-meta">' + ''.join(f'<span>{part}</span>' for part in parts) + '</div>'


def entry(post):
    path = '/notes/' + post['slug'] + '/'
    return f'<li class="journal-entry">{meta(post)}<h3><a href="{path}"><span>{escape(clean(post["title"]))}</span>{ARROW}</a></h3><p>{escape(clean(post["excerpt"]))}</p></li>'


def social_section(data):
    channels, cards = data['channels'], []
    for post in sorted(data['posts'], key=lambda p: p.get('date') or '', reverse=True)[:6]:
        key = post['platform']
        if key not in channels:
            raise ValueError('Unknown social channel')
        label = channels[key]['label']
        dated = f'<time datetime="{post["date"]}">{pretty_date(post["date"])}</time>' if post.get('date') else ''
        url = safe_social_url(post['url'])
        cards.append(f'<article class="social-post" data-post-channel="{key}"><div class="journal-meta"><span>{escape(label)}</span>{dated}</div><h4><a href="{url}" target="_blank" rel="noopener noreferrer">{escape(clean(post["title"]))}</a></h4><p>{escape(clean(post["excerpt"]))}</p><a class="social-original" href="{url}" target="_blank" rel="noopener noreferrer">View on {escape(label)} {ARROW}</a></article>')
    filters = '<button type="button" data-channel="all" aria-pressed="true">All</button>' + ''.join(f'<button type="button" data-channel="{key}" aria-pressed="false">{escape(ch["label"])}</button>' for key, ch in channels.items())
    fallbacks = ''.join(f'<p class="social-fallback" data-fallback-channel="{key}" hidden>Find more on <a href="{safe_social_url(ch["url"])}" target="_blank" rel="noopener noreferrer">{escape(ch["label"])}</a>.</p>' for key, ch in channels.items())
    profiles = ''.join(f'<a href="{safe_social_url(ch["url"])}" target="_blank" rel="noopener noreferrer">{escape(ch["label"])}</a>' for ch in channels.values())
    return f'<div class="elsewhere" id="elsewhere" data-social-feed><div class="elsewhere-heading"><h3>Elsewhere.</h3><span class="journal-label">Across my channels</span></div><p class="feed-intro">Notes, conversations, and things worth sharing.</p><div class="feed-filters" data-feed-filters role="group" aria-label="Filter posts by channel" hidden>{filters}</div><p class="journal-sr-only" aria-live="polite" aria-atomic="true" data-feed-count>{len(cards)} selected posts</p><div class="social-post-list">{"".join(cards)}</div>{fallbacks}<div class="social-profile-links" aria-label="Social profiles">{profiles}</div><p class="feed-caption">Selected public posts. Visit each channel for the latest.</p></div>'


def document(title, description, path, body, site_url):
    title, description = escape(title), escape(description, quote=True)
    return f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} — Nira Minniefield</title><meta name="description" content="{description}"><link rel="canonical" href="{site_url}{path}"><link rel="alternate" type="application/rss+xml" title="Nira Minniefield — Notes &amp; ideas" href="/notes/feed.xml"><link rel="stylesheet" href="/assets/journal.css"></head><body class="journal-page"><a class="skip-link" href="#main">Skip to content</a><header class="journal-header"><a class="wordmark" href="/" aria-label="Nira home"><span class="star" aria-hidden="true">{STAR}</span> nira</a><nav class="journal-nav" aria-label="Journal navigation"><a href="/notes/">Notes &amp; ideas</a><a href="/#connect">Let’s talk {ARROW}</a></nav></header><main class="journal-main" id="main">{body}</main><footer><span>©︎ {date.today().year} Nira Minniefield</span><span>Always building something.</span><a href="/">Back to home</a></footer></body></html>\n'


def build(output):
    journal = json.loads((ROOT / 'content/journal.json').read_text())
    social = json.loads((ROOT / 'content/social.json').read_text())
    site_url = journal['site_url'].rstrip('/')
    posts = sorted((p for p in journal['posts'] if p.get('status') == 'published'), key=lambda p: p['date'], reverse=True)
    for post in posts:
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', post['slug']):
            raise ValueError('Invalid article slug')
        date.fromisoformat(post['date'])
    home = output / 'index.html'
    html = home.read_text()
    section = re.search(r'<section id="notes".*?</section>', html, re.S)
    if not section:
        raise ValueError('Notes section is missing')
    old = section.group()
    prefix, content = old.split('<div>', 1)
    intro = content.split('<!-- JOURNAL:CONTENT -->', 1)[0] if '<!-- JOURNAL:CONTENT -->' in content else content.rsplit('<a href=', 1)[0]
    if 'class="journal-about"' not in intro:
        about = re.findall(r'<p class="bodycopy"[^>]*>.*?</p>', intro, re.S)
        if about:
            about_html = ''.join(about)
            intro = intro.replace(about_html, '<details class="journal-about"><summary>About these notes</summary>' + about_html + '</details>', 1)
    writing = '<div class="journal-writing"><div class="journal-label">Notes &amp; essays</div><ol class="journal-post-list">' + ''.join(entry(p) for p in posts[:3]) + '</ol><div class="journal-actions"><a class="underlink" href="/notes/">All notes &amp; essays <span aria-hidden="true">' + ARROW + '</span></a><a class="journal-rss" href="/notes/feed.xml">Subscribe by RSS</a></div></div>'
    replacement = prefix + '<div>' + intro + '<!-- JOURNAL:CONTENT -->' + writing + social_section(social) + '</div></section>'
    html = html[:section.start()] + replacement + html[section.end():]
    head_links = '<link rel="stylesheet" href="/assets/journal.css"><link rel="alternate" type="application/rss+xml" title="Nira Minniefield — Notes &amp; ideas" href="/notes/feed.xml">'
    if head_links not in html:
        html = html.replace('</head>', head_links + '</head>', 1)
    script = '<script src="/assets/journal.js" defer></script>'
    if script not in html:
        html = html.replace('</body>', script + '</body>', 1)
    home.write_text(html)
    notes_dir = output / 'notes'
    notes_dir.mkdir(parents=True, exist_ok=True)
    archive = '<div class="journal-label">Notes &amp; ideas</div><h1>What I’m thinking about.</h1><p class="archive-intro">Human agency, the political economy of technology, and the institutions we build around both.</p><ol class="journal-post-list">' + ''.join(entry(p) for p in posts) + '</ol><div class="article-footer"><a href="/#notes">Back to the main page</a><a href="/notes/feed.xml">Subscribe by RSS</a></div>'
    (notes_dir / 'index.html').write_text(document('Notes & ideas', 'Notes and essays by Nira Minniefield.', '/notes/', archive, site_url))
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    for tag, value in [('title', 'Nira Minniefield — Notes & ideas'), ('link', site_url + '/notes/'), ('description', 'Notes and essays on human agency, technology, and institutions.'), ('language', 'en-us')]:
        ET.SubElement(channel, tag).text = value
    for post in posts:
        body_path = (ROOT / 'content' / post['body']).resolve()
        if not body_path.is_relative_to((ROOT / 'content/posts').resolve()):
            raise ValueError('Article body must be in content/posts')
        body = body_path.read_text()
        if re.search(r'<(?:script|iframe)\b', body, re.I):
            raise ValueError('Article content must not contain scripts or embeds')
        article = f'<article><header class="article-header">{meta(post)}<h1>{escape(clean(post["title"]))}</h1><p class="article-byline">Nira Minniefield</p></header><div class="article-body">{body}</div><div class="article-footer"><a href="/notes/">All notes &amp; essays</a><a href="/#connect">Connect about the work</a></div></article>'
        dest = notes_dir / post['slug']
        dest.mkdir(exist_ok=True)
        path = '/notes/' + post['slug'] + '/'
        (dest / 'index.html').write_text(document(post['title'], post['excerpt'], path, article, site_url))
        item = ET.SubElement(channel, 'item')
        for tag, value in [('title', post['title']), ('link', site_url + path), ('guid', site_url + path), ('description', post['excerpt']), ('pubDate', format_datetime(datetime.combine(date.fromisoformat(post['date']), datetime.min.time(), timezone.utc)))]:
            ET.SubElement(item, tag).text = value
    ET.indent(rss)
    (notes_dir / 'feed.xml').write_bytes(ET.tostring(rss, encoding='utf-8', xml_declaration=True))
    print(json.dumps({'published_articles': len(posts), 'selected_social_posts': len(social['posts']), 'output': str(output)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'dist' if (ROOT / 'dist/index.html').is_file() else ROOT)
    build(parser.parse_args().output.resolve())
