# Organisation logos

Files dropped here appear in the organisation strip on `/projects/`.

Expected filenames — these are already wired up in `build.py` (`ORGS`):

| File | Organisation |
|---|---|
| `ura.png` | Uganda Revenue Authority |
| `finca.jpg` | FINCA |
| `wfp.png` | UN World Food Programme |
| `gtbank.png` | Guaranty Trust Bank |

Add the file, then run `python3 build.py`. The tile switches from placeholder
initials to the image on its own. If a file is missing the tile simply shows the wordmark —
the page never displays a broken image, so you can add them one at a time.

**Format:** SVG if you have it (rename the extension in `ORGS` to match),
otherwise PNG with a transparent background, around 400px on the long edge.
Tiles render each logo at 64px inside a white plate, in full brand colour. The
plate is what keeps free-standing marks and solid-colour blocks lining up, and
keeps transparent marks legible in dark mode.

**Permission:** these are third-party trademarks. Use them only with the
owner's written permission — the UN emblem in particular is restricted.
