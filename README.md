# Finance Recruiting Terminal

A $0, single-user finance internship discovery + application tracking PWA designed around official employer career sources.

## What is genuinely implemented

- Responsive static web app for Mac/iPhone/desktop browsers.
- PWA manifest + service worker; can be added to iPhone Home Screen after HTTPS deployment.
- Private local persistence using IndexedDB for candidate profile, resume PDF, saved jobs, manually-added employers and application records.
- JSON backup/export and restore, including the locally stored resume PDF.
- Opportunity dashboard, filters/sorting, NYC/Seattle/Boston ranking bonuses, location × career matrix, action-required view, recruiting calendar, applications tracker and monitoring-health view.
- Transparent heuristic Fit / Career Value / Priority scores. Full scores are calculated locally from the user's profile, so resume/profile data does not need to be published.
- Explicit GPA parsing with `hard`, `preferred`, `none`, and `unknown`. A low GPA does not suppress a posting.
- Modular **Greenhouse** and **Lever** monitoring adapters.
- Deduplication with stable IDs using employer + ATS ID + title + location + application URL.
- Historical retention: removed jobs remain in `data/jobs.json` with `status=Removed` and `removed_at` rather than being deleted.
- Monitoring failures are written to `data/monitor_health.json`; failures are not interpreted as "no jobs".
- Scheduled GitHub Actions workflow and GitHub Issue alerts. Issue notifications can be delivered by GitHub's own free email/web notification system.
- GitHub Pages deployment workflow.

## Deliberately NOT faked

- `data/jobs.json` ships empty. The dashboard is populated only after a monitor actually retrieves official postings.
- No employer is labeled healthy until a real monitoring run succeeds.
- Workday/SuccessFactors/iCIMS/Taleo are **not** represented as universal adapters. Their public implementations vary enough that employer-specific configuration is normally required.
- Historical opening predictions are not generated until enough real historical observations exist. A prediction from no data would be fake.
- The automated alert score is intentionally "server-lite" unless you choose to expose more profile inputs to GitHub Actions. The richer profile-aware score is calculated locally in the browser.

## $0 architecture

```text
Official ATS/public career endpoints
        |
        v
GitHub Actions (hourly scheduler, public repo)
        |
        +--> monitor/adapters/*
        +--> data/jobs.json
        +--> data/monitor_health.json
        +--> data/monitor_state.json
        +--> GitHub Issue alert when server-lite priority >= threshold
        |
        v
GitHub Pages static PWA
        |
        +--> public job/health feed
        +--> local browser scoring
        +--> IndexedDB: profile, resume, applications, notes, local employers
        +--> JSON backup/export
```

### Why this split

A public repository keeps GitHub Pages and standard GitHub-hosted Actions at $0, while personal information remains only in the browser. The repo contains public job data and monitor state, not your resume or application notes.

## Monitoring frequency

The scheduler runs once per hour. Each employer has its own `check_interval_minutes`, so a tier-1 source can be checked hourly while lower-priority sources can be checked every 3–12 hours. This prevents unnecessary requests and scales better than checking every employer every few minutes.

GitHub supports scheduled workflows as frequently as every five minutes, but that does **not** mean five-minute scraping is appropriate. The provided default is intentionally conservative.

## Initial configured adapters

### Greenhouse

Endpoint pattern:

```text
https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
```

`Point72` is seeded with board token `point72`.

### Lever

Endpoint pattern:

```text
https://api.lever.co/v0/postings/{site}?mode=json
```

`HCVT` is seeded with site slug `hcvt` because its official public jobs site uses Lever and currently exposes internship postings.

## Running locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r monitor/requirements.txt
python monitor/run.py --force
python -m http.server 8000
```

Open `http://localhost:8000`.

The monitor requires normal Internet access. If your network blocks a source, the source will appear as failing in Monitoring Health and existing job records remain intact.

## Tests

```bash
python -m pytest -q
node --check src/app.js
```

The checked-in Greenhouse fixture is a deterministic adapter/parser test only. It is not loaded into the production dashboard.

## Free deployment: exact steps

1. Create a **public** GitHub repository. Public is required for GitHub Pages on GitHub Free.
2. Upload/push this entire folder to the repository's `main` branch.
3. In **Settings → Pages**, choose **GitHub Actions** as the source.
4. In **Settings → Actions → General**, make sure Actions are enabled.
5. In **Settings → Secrets and variables → Actions → Variables**, create `ALERT_THRESHOLD` with `75` (or another number).
6. Optional: create repository secret `PROFILE_GPA` with your current GPA. If omitted, the script defaults to 2.81. A secret is preferable to putting GPA in a public config file.
7. Run **Actions → Monitor official internship sources → Run workflow** once manually.
8. Inspect `data/monitor_health.json` or the Monitoring Health page. Only sources that actually succeeded will count as healthy.
9. Watch the repository / configure GitHub email notifications so new `internship-alert` issues produce notifications.
10. Open the GitHub Pages URL on your iPhone in Safari → Share → **Add to Home Screen**.

No credit card or paid API is required for this architecture.

## Privacy/security model

### Public in the repository

- Employer source configuration
- Official public job postings retrieved by the monitor
- Monitor timestamps / errors / health

### Private to the browser

- GPA/profile edits (unless you optionally add GPA as an Actions secret)
- Resume PDF
- Applications
- Recruiter/contact details
- Interview notes
- Referrals/networking notes
- Offer data

GitHub Actions secrets are not placed in frontend JavaScript.

### Important tradeoff

IndexedDB is device/browser-specific. Your Mac's application tracker does not automatically sync to your iPhone. Use **Export** on one device and **Import** on the other for a $0, no-backend privacy-first workflow. Automatic private cross-device sync without operating a backend is the main feature intentionally sacrificed by this architecture.

## Scoring formulas

### Local Fit score

Starts at 58, then applies explicit evidence only:

- hard GPA met: +8
- hard GPA missed: -42
- preferred GPA met: +4
- preferred GPA missed: -8
- no GPA listed: +8
- stated graduation year matches: +15
- stated graduation year misses: -45
- explicit work authorization conflict: -50
- finance relevance: +7
- profile/resume-keyword overlap: up to +10

Clamped to 0–100.

Classification defaults:

- 78–100: High Probability
- 58–77: Realistic
- 25–57: Reach
- 0–24: Not Eligible

`Not Eligible` is meant for explicit conflicts, not prestige-based guesswork.

### Career Value

Starts from category-specific seed values and increases for explicit modeling, valuation, transaction, underwriting, investment-research, and client-exposure language. It is a heuristic career-value measure, not an acceptance probability.

### Priority

Default local formula:

```text
Priority = 0.46 × Fit
         + 0.36 × Career Value
         + Location Bonus
         + Recency Bonus
         + Deadline Urgency
```

Default location bonuses:

- NYC +12
- Seattle +8
- Boston +5
- Other +0

These weights and bonuses are editable in Profile.

## What remains employer-specific

The next coverage phase is adding and validating employers one by one while reusing adapters wherever possible. Greenhouse and Lever should scale cleanly. Workday/custom sites require source-specific endpoint discovery and testing. If a site blocks automation, requires authentication/CAPTCHA, or disallows automated access, keep it `Manual Monitoring` with its official careers link.

## Acceptance-test status

The codebase currently passes deterministic adapter/parser tests and JavaScript syntax validation. A current Point72 internship is independently verifiable on Point72's official Greenhouse-backed careers system, which establishes that the seeded employer/source is real.

The final production acceptance test — **scheduled GitHub Action retrieves the live posting, commits it, renders it on your deployed Pages site, and emits a GitHub notification** — cannot be truthfully claimed until the repository is pushed to your GitHub account and that workflow actually runs there. The repository contains everything needed for that test; the GitHub-account setup is the external action you must perform.

## File structure

```text
.
├── index.html
├── manifest.webmanifest
├── service-worker.js
├── assets/
│   └── styles.css
├── src/
│   └── app.js
├── data/
│   ├── employers.json
│   ├── jobs.json
│   ├── monitor_health.json
│   ├── monitor_state.json
│   └── pending_alerts.json
├── monitor/
│   ├── run.py
│   ├── classify.py
│   ├── requirements.txt
│   └── adapters/
│       ├── base.py
│       ├── greenhouse.py
│       └── lever.py
├── tests/
│   ├── test_monitor.py
│   └── fixtures/
└── .github/workflows/
    ├── monitor.yml
    └── pages.yml
```
