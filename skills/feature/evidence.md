# Evidence at the test stage

Proof a person can look at for each acceptance line: screenshots and a short video of the app doing what the line says, on the job's own Try it server, signed in as the dev bypass user, against the local database copy. The tester writes one Playwright spec per line; the Feature Workshop dashboard runs them, keeps the pictures and the video in the job folder and shows them on the gate card. A person pastes the gate card's link on the ticket.

## When

The job's `evidence` option (job-options.md): `"auto"` is on at L2 and L3 and off at L1, `"always"` is on at L1 too, `"off"` is never. Never at L0, whatever the option says. When it is off, write no specs and leave the Evidence section out of the report.

## Names

- A criterion's id is `AC-<n>`, numbered in the order of the spec's acceptance list: the first line is `AC-1`. The same numbers as `acceptance.md` and the per-line results in `test-report.md`.
- Its spec is `<private folder>/evidence/specs/AC-<n>.spec.mjs`, one file per criterion, one test per file, the test's title starting with the id: `AC-3: Managers see the Hours column`.

## Which criteria get a spec

A line a person could see in the app gets one: a page, a button, a message, a list that changes. A line with nothing to see (an API-only rule, a permission the server enforces with no screen of its own, a background job, an email, a migration) gets none, and the report says why in one line (below). Don't invent a screen to have something to record.

## How a spec reads

Plain steps from the app's home address to the thing the criterion names, a screenshot at each step a person would want to see, and one `expect` at the end:

```js
import { test, expect } from '@playwright/test';

test('AC-3: Managers see the Hours column', async ({ page }, testInfo) => {
  let n = 0;
  const shot = async (what) => {
    const file = testInfo.outputPath(`${String(++n).padStart(2, '0')}.png`);
    await page.screenshot({ path: file, fullPage: true });
    await testInfo.attach(what, { path: file, contentType: 'image/png' });
  };

  await page.goto('/');
  await shot('The home page, signed in as the dev user');
  await page.getByRole('link', { name: 'Team' }).click();
  await shot('The Team page, with the Hours column next to Name');
  await expect(page.getByRole('columnheader', { name: 'Hours' })).toBeVisible();
});
```

- `shot('…')` names what a person sees in that picture, in plain words. It becomes the picture's text description on the gate card, so say what is on the screen, not what the code does.
- Find things the way a person does: `getByRole`, `getByLabel`, `getByText`. No fixed waits (`waitForTimeout`); Playwright waits for what you ask about. Each spec finishes in well under 60 seconds.
- Import only `@playwright/test`. No other files, no `fs`, no `process.env`, no helpers shared between specs.

## What a spec never does

- **Never signs in with a password.** No password, token or cookie is typed or set. Try it turns on the dev sign-in skip (`DEV_BYPASS_AUTH`, from the repository's profile), so the app opens as the dev bypass user.
- **Never reads `.env` files** or any other settings file, and never prints a setting.
- **Never changes data outside the local database copy.** The app on the Try it port only uses the local copy. Prefer looking over changing; when a criterion is about saving something, save clearly invented values ("Evidence check 1"). Nothing that sends email, texts or calls another service.
- **Never visits anything but this computer.** Start with `page.goto('/')` and use paths, never a full address: the dashboard sets the address to the job's Try it server on `127.0.0.1`, and stops any page that tries to go elsewhere.

## Who runs them

Not the tester, and not you. The dashboard runs them once `test-report.md` names the commit under test: it starts the job's Try it server on its own port, checks the local database copy is up, runs the specs in Chromium, keeps the pictures and the video, and stops the server again. So recording needs no extra yes for a server, and the tester never starts the app for evidence. When the dashboard can't record (the database copy isn't running, Chromium isn't installed) it says so on the gate card, and the person presses Record again; don't work around it.

The results are the dashboard's: `evidence/evidence.json` and the folder `evidence/<commit>/AC-<n>/`. Read `evidence.json` if it is there when you brief; a criterion whose evidence failed is a reason to look, like a FAIL in the report, but the report's own checks stay the result.

## The report's Evidence section

Write the specs first and `test-report.md` last: the dashboard starts recording when the report names its commit. The report ends with one line per acceptance criterion, in this form (the dashboard reads it for the titles and the reasons):

```
## Evidence

- AC-1: Managers see the Hours column. Spec: evidence/specs/AC-1.spec.mjs
- AC-2: Only managers can export. No spec: the server refuses the export (API only); covered by the route test.
```

## Where they go

Nowhere. The specs, the pictures and the video stay in the job's private folder. They are never copied into the repository, committed, put in a PR or pasted on a ticket; the ticket gets the link the gate card's "Copy link" gives.
