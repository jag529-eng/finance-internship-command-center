# Architecture decisions

## Decision 1 — static PWA + scheduled collector
A static PWA is sufficient for the user interface; monitoring must run independently of whether the user opens the app. GitHub Actions provides that scheduler. This avoids paid servers and paid databases.

## Decision 2 — public feed / private personal state
Public official job data is safe to publish. Resume/application data is not. IndexedDB separates those concerns without a paid backend.

## Decision 3 — adapters, not per-company scrapers
Adapters normalize ATS output. Employer records contain the ATS token/site slug. One Greenhouse adapter can monitor many employers.

## Decision 4 — evidence-based GPA handling
The parser only marks a hard/preferred numeric GPA rule when the posting text supports it. Otherwise it returns `none` or `unknown`.

## Decision 5 — failures are first-class data
A fetch exception records a failing source. Existing jobs stay intact. A failing check never becomes an empty successful result.

## Decision 6 — hourly top-level scheduler
Hourly is fast enough for a single-student recruiting monitor while remaining respectful. Employer-specific intervals allow slower checks where appropriate.

## Decision 7 — GitHub Issue alerts
Issue creation uses the built-in `GITHUB_TOKEN`, so no paid SMS/email vendor is required. GitHub can deliver issue notifications by email/web depending on the user's notification settings.
