# Notes & ideas

This is a static blog and a small, curated social feed. There is no database,
visitor login, third-party embed, or client-side platform credential.

## Publish an article

1. Add its HTML body in `content/posts/`.
2. Add its title, slug, date, category, excerpt, body path, and `published`
   status in `content/journal.json`. Use `draft` to keep an item unpublished.
3. Run `python3 scripts/build-journal.py`.
4. Publish the generated index, article/archive pages, RSS, and journal assets.

The builder preserves every home-page section outside Notes & ideas. On the
GitHub Pages repository it defaults to the root; on the Sites source it uses
`dist`. Python's standard library is the only build requirement.

## Social feed

Edit `content/social.json` and rebuild. Include only verified public posts,
their original URLs, and publication dates when known. Excerpts are displayed
as selected posts, not as a live or comprehensive account history. No date is
invented when the original publication date is unavailable.

Instagram and LinkedIn currently link to the owner's profiles. Their filters
have useful profile fallbacks until post access is authorized. Threads entries
were selected from public search results for the owner's exact handle.

Automatic cross-channel collection is **not enabled**. It requires a supported,
authorized source connection and an independently verified unattended updater.
Never put API tokens, private drafts, or account credentials in these public
files. Only the resulting public post metadata belongs in the site.

The first native project note reuses the existing approved public book and
research copy; it does not introduce new research findings or private writing.
