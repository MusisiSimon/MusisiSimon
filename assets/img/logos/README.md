# Organisation logos

Files dropped here appear in the organisation strip on `/projects/`.

Expected filenames — these are already wired up in `build.py` (`ORGS`):

| File | Organisation |
|---|---|
| `ura.png` | Uganda Revenue Authority |
| `finca.png` | FINCA |
| `wfp.png` | UN World Food Programme |
| `gtbank.png` | Guaranty Trust Bank |

Add the file, then run `python3 build.py`. The tile switches from a wordmark to
the image on its own. If a file is missing the tile simply shows the wordmark —
the page never displays a broken image, so you can add them one at a time.

**Format:** SVG if you have it (rename the extension in `ORGS` to match),
otherwise PNG with a transparent background, around 400px on the long edge.
Tiles render the logo at 44px tall, greyscale, turning full colour on hover.

**Permission:** these are third-party trademarks. Use them only with the
owner's written permission — the UN emblem in particular is restricted.
