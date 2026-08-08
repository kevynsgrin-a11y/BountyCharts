# Deploying BountyCharts to bountycharts.com (Cloudflare)

Runbook for taking `site/` live on the apex domain via **Cloudflare Pages**.

**What is automated:** the build/deploy pipeline (`.github/workflows/deploy.yml`) — once secrets exist, every push to `main` that touches `site/**` deploys to production, and every PR gets a preview URL.

**What only you can do:** anything requiring the Cloudflare account — buying the domain, creating the Pages project, minting an API token, attaching the custom domain. Those steps are marked **[you]**.

---

## 0. Prerequisites

| Item | Status | Notes |
|---|---|---|
| Cloudflare account | **[you]** | Free tier is sufficient for this stage |
| `bountycharts.com` registered | **[you]** | See step 1 |
| Repo pushed to GitHub | ✅ | `kevynsgrin-a11y/BountyCharts` |
| Static site to deploy | ✅ | `site/` — index, 404, robots, sitemap, headers |
| CI workflow | ✅ | `.github/workflows/deploy.yml` |

---

## 1. Register the domain **[you]**

Cloudflare Dashboard → **Domain Registration → Register Domain** → search `bountycharts.com` → purchase.

Cloudflare Registrar sells at wholesale cost with no markup and includes WHOIS privacy free. Buying it here also means the domain lands in your Cloudflare account with nameservers already pointed correctly — no DNS migration step, which is the main reason to prefer it over an external registrar.

> If the domain is already registered elsewhere, instead add the site to Cloudflare (**Add a site**) and repoint the nameservers at your current registrar. Propagation is usually under an hour but allow 24.

**Verify:** the zone appears under your account with status **Active**.

---

## 2. Create the Pages project **[you]**

Dashboard → **Workers & Pages → Create → Pages → Connect to Git** → select `kevynsgrin-a11y/BountyCharts`.

Configure exactly:

| Setting | Value |
|---|---|
| Project name | `bountycharts` |
| Production branch | `main` |
| Framework preset | **None** |
| Build command | *(leave empty)* |
| Build output directory | `site` |

The site is hand-written static HTML with no build step, so there is nothing to compile. An empty build command is correct, not an oversight.

> The project name must be exactly `bountycharts` — the CI workflow passes `--project-name=bountycharts`. If you name it differently, update `.github/workflows/deploy.yml` to match.

**Verify:** first deploy succeeds and `https://bountycharts.pages.dev` serves the landing page.

---

## 3. Mint an API token **[you]**

Dashboard → **My Profile → API Tokens → Create Token → Custom token**.

| Field | Value |
|---|---|
| Permissions | `Account` → `Cloudflare Pages` → **Edit** |
| Account Resources | Include → your account |
| TTL | Set an expiry and calendar a rotation |

Copy the token immediately — it is shown once.

Also grab your **Account ID** from the right-hand sidebar of any account page (or the dashboard URL: `dash.cloudflare.com/<account-id>`).

> Scope the token to Pages:Edit only. A global API key in CI is a standing compromise of the whole account.

---

## 4. Add the secrets to GitHub **[you]**

Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Name | Value |
|---|---|
| `CLOUDFLARE_API_TOKEN` | the token from step 3 |
| `CLOUDFLARE_ACCOUNT_ID` | your account ID |

**Verify:** Actions → **Deploy site** → *Run workflow* completes green.

---

## 5. Attach the custom domain **[you]**

Pages project → **Custom domains → Set up a custom domain** → `bountycharts.com` → **Activate**.

Because the zone is already in the same Cloudflare account, the required `CNAME` is created for you and TLS is provisioned automatically. Certificate issuance is typically a few minutes.

Repeat for `www.bountycharts.com` — you need www *routed* before you can redirect it in step 6.

**Verify:**
```bash
curl -sSI https://bountycharts.com | head -1        # expect: HTTP/2 200
curl -sS https://bountycharts.com/robots.txt        # expect: sitemap line
```

---

## 6. Canonicalise www → apex **[you]**

Pick one canonical host or you split ranking signals between two URLs that serve identical content.

Dashboard → your zone → **Rules → Redirect Rules → Create rule**:

| Field | Value |
|---|---|
| Rule name | `www to apex` |
| When incoming requests match | `Hostname` **equals** `www.bountycharts.com` |
| Then | **Dynamic** redirect |
| Expression | `concat("https://bountycharts.com", http.request.uri.path)` |
| Status code | `301` |
| Preserve query string | ✅ |

This is deliberately not in `site/_redirects` — that file is only consulted after a request already reaches the Pages project, which makes it the wrong layer for host canonicalisation.

**Verify:**
```bash
curl -sSI https://www.bountycharts.com | head -3    # expect: 301 → https://bountycharts.com/
```

---

## 7. Post-launch checks

```bash
# Security headers are live
curl -sSI https://bountycharts.com | grep -iE 'strict-transport|content-security|x-content-type'

# 404 returns the right status, not a soft 200
curl -sSI https://bountycharts.com/nope | head -1   # expect: HTTP/2 404

# Sitemap is reachable and valid XML
curl -sS https://bountycharts.com/sitemap.xml | head -3
```

Then:

- **Google Search Console** — add `bountycharts.com` as a Domain property (DNS TXT verification is one click when the zone is in Cloudflare), submit the sitemap.
- **Bing Webmaster Tools** — import from Search Console.
- **Cloudflare Web Analytics** — Dashboard → Web Analytics → add site. Free, cookieless, no consent banner needed, which keeps the privacy surface at zero until a real analytics decision is made.

---

## Known follow-ups

These are deliberate deferrals, not omissions:

1. ~~**CSP allows `'unsafe-inline'` for scripts.**~~ **Resolved.** The stated reason — that some browsers evaluate JSON-LD against `script-src` — did not reproduce. Serving the real page under three policies in Chromium produced zero CSP violations in every case, and the JSON-LD stayed parseable even under `script-src 'none'`, because `application/ld+json` is a data block rather than an executable script. `'unsafe-inline'` has been dropped from `script-src`; `style-src` keeps it, because the page genuinely does use inline `<style>`. When real JavaScript ships it must come from a same-origin file, or move to nonces/hashes. Not verified in Safari or Firefox.
2. **No email capture.** Deliberate — a pre-launch capture form needs an email service provider, which is a recurring spend and therefore a decision reserved to the owner under the agency protocol (`GT` escalation rules). Do not add a form that posts nowhere.
3. **No affiliate links yet.** When they land, an affiliate disclosure becomes legally required before the first link ships, not after. See the `legal-compliance` agent brief in `prompts/agency-handoff-prompt.md`.
4. **Apex A/AAAA records.** Not needed — Pages custom domains use a managed CNAME with CNAME flattening at the apex. Do not add manual A records; they will conflict.

---

## Rollback

Pages keeps every deployment. Dashboard → Pages project → **Deployments** → pick the last good one → **Rollback**. It is instant and does not require a git revert.

For a bad commit on `main`, revert the commit and let CI redeploy — the rollback button is for emergencies where you need the old build serving *now*.
