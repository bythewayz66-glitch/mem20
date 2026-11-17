# mem20-naration — narrative chronicle archive

This directory holds a static copy of the **mem20-naration** chronicle, a serialized
narrative history of the mem20 project, for browsing inside the repository.

## What is here

- `index.html` — the serial index: every published post in order, with week, date
  window, word count, title, standfirst and link.
- `post-NN-*.html` — the posts themselves, one self-contained page each.
- `timeline.html` — a searchable timeline of the commits the series covers.
- `sources-and-method.html` — the corpus the series draws on, and the secrets policy.
- `corrections.html` — every correction made to an earlier post, in the open.
- `comic/index.html` and `comic/issue-01-the-gate-that-would-not-open.html` — the
  companion comic, Issue 01.

## Post numbers present

Posts **01–16** and **19–30** are present. Posts **17** and **18** are **not** in this
archive: their source bytes are unreachable (the directories that held them return
403, and the copies that are reachable are 2,979-byte placeholder shells). The index
marks them text-unavailable rather than linking to nothing.

## Self-contained

Every page is a single HTML file with no external CSS, JavaScript, fonts or images.
They render identically offline and with no network access.

## Canonical copies

The canonical live copies are published on the static host. This directory is a
repository-side mirror for browsing and for the record.

## Corrections

The series is written to a corrections standard: when a published figure is found to
be wrong, the correction is logged in `corrections.html` and marked in place in the
post, rather than silently edited.
