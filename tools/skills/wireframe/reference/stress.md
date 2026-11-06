# Stress test

`stress.py` clicks through a prototype page at random, from a seed, and checks the page after every step. Python 3, no dependencies, headless Chrome.

## Run it

```bash
python3 stress.py <page.html> --seeds 1-8 --mode all --device both      # before publishing a revision
python3 stress.py <page.html> --seeds 1-24 --steps 200 --mode all --device both --timing both   # the full run
python3 stress.py <page.html> --seed 7 --steps 200 --mode framed --device phone --timing settled   # replay one failure
```

Add `--expect-restore`: the page keeps its place on reload and has browser history. Without it, reload is expected to land on the first screen, and browser Back leaving the page is counted, not failed. With it, Back leaving the page fails unless the page is on its first place.

On `file://` with many Chromes running, Chrome itself can lose `localStorage` across a reload, even on an empty page. A plain run then shows `pin-count` at a reload. Check whether storage was already empty before the page's scripts ran before blaming the page. On a busy machine a phone tap can also be lost, which shows as `landed-elsewhere` with the next same tap working. Replay the seed alone to tell.

| Option | Choices |
|---|---|
| `--mode` | `plain`: the page as a file. `framed`: inside a sandboxed iframe, with `stress-frame.html` playing the site's side of the bridge. `hosted`: with a stand-in for the artifact runtime whose database answers late. `all` runs the three. |
| `--device` | The window: `laptop` is 1400 × 950, `phone` is 390 × 844 with a phone user agent and touch. The page's own Phone/Laptop switch is used inside both. |
| `--timing` | `burst`: no wait between steps, clicks sent straight to the element. `settled`: waits for animations and two frames, and uses real mouse and touch input, so a covered control can't be clicked. |
| `--jobs` | Chromes at once. Each has its own storage. |
| `--out` | Where the JSON files go. Default: a new folder under the system temp folder. |

## Reading the result

There is one line per run. The code in square brackets is a hash of the action log: replaying a seed gives the same code. Exit code 1 means a failure, or a run the rig couldn't finish ("not finished", which is a problem with the test, not the page).

| Failure | What a person would see |
|---|---|
| `back-did-nothing` | A Back control does nothing: there's nowhere to go back to, or the screen didn't change. |
| `back-landed-elsewhere`, `landed-elsewhere`, `device-landed-elsewhere`, `reload-landed-elsewhere` | The page ended up on a different screen or overlay from the one it should be on. |
| `content-changed-after-back`, `content-changed-after-close` | Same screen, but it reads differently from when they left it. |
| `scroll-not-restored` | Coming back lost their place in a list. |
| `scroll-jump-under-overlay` | Opening a sheet or dialog sent the screen behind it back to the top. |
| `start-over-kept-old-state` | Start over didn't really start over: a tab or an open section stayed changed. |
| `overlay-stuck` | Close or Escape left the overlay open. |
| `to-target-missing`, `to-did-nothing` | A link points at nothing, or at nothing on this device or for this role. |
| `blank-canvas`, `two-screens-on`, `two-overlays-on`, `screen-is-empty`, `screen-has-no-size`, `overlay-has-no-size` | A broken screen. |
| `left-the-prototype` | A step dropped them out of the Prototype tab. |
| `page-error` | An uncaught error or rejection in the page. |
| `page-wider-than-phone` | The page is wider than the phone, so a real phone zooms everything out to fit. The failure lists what's too wide. |
| `pin-count`, `pin-on-wrong-layer`, `pin-outside-screen` | Pins don't match the notes left on this screen, or sit in the wrong place. |
| `bridge-reports-wrong-screen`, `bridge-no-feedback-reply` | The parent page gets the wrong screen, or no answer to a feedback request. |
| `status-by-colour-alone` | Something shows a state with no words, labelled icon or title. |
| `reload-lost-the-place`, `browser-back-left-the-page` | With `--expect-restore`: the page didn't keep its place. |

A run stops after 8 different failures. The same failure on the same screen counts once.

**Skipped actions** are listed at the end and are not failures: a control covered at that moment, or something the page doesn't have yet (right-click and press-and-hold pins, dragging, editing).

## What it can't tell you

Chrome only, headless. No Safari and no real phone. Phone runs use a true 390 width with real touch taps. Press-and-hold and drag on a phone are sent as pointer events, and Escape is sent from the page. The page's CDN files load over the network, so run it online.
