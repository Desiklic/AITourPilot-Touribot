# Outreach Infrastructure Blueprint

*Source: 20260318-outreach-infrastructure-blueprint.html*
*Priority: P2*

## Executive Summary

This document defines the complete email and domain infrastructure for AITourPilot's B2B museum outreach operation. It is the operational foundation for the Precision Partner Acquisition Engine -- the system that will deliver 1-2 pilot museum partnerships within 60 days.

**Key decisions:**

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Outreach domain | **aitourpilot.co** | Complete reputation isolation from main domain; clean inbox appearance |
| Defensive domains | **aitourpilot.eu + 7 country TLDs** | Reserved to prevent squatting; European market coverage |
| Domain registrars | **Cloudflare** (.co, .co.uk) + **INWX** (all European ccTLDs) | Cloudflare for outreach domain DNS; INWX covers TLDs Cloudflare cannot register (.at, .dk) at wholesale pricing |
| DNS management | **Cloudflare** (all domains point nameservers here) | Single DNS dashboard regardless of where domains are registered |
| Email provider | **Google Workspace** (new instance on .co) | Isolated from Zoho on .com; excellent deliverability |
| Sender identity | **hermann@aitourpilot.co** | Real founder name; matches LinkedIn profile; builds trust |
| Display name | **Hermann Kudlich** or **Hermann Kudlich \\| AITourPilot** | Human-first, brand-second |
| Email warm-up | **Instantly.ai** | Handles warm-up + cold email sequencing in one tool |
| Website hosting | **Vercel** (Next.js) | Free tier, deploy from GitHub, optimized for Next.js |
| .com domain transfer | **Edis.at to Cloudflare** (before May 24, 2026) | Consolidate DNS management; avoid Edis renewal; prepare for campaign traffic |
| Domain ownership | **Hermann Kudlich Consulting** (temporary) | AITourPilot ApS bank account pending; transfer/assign to ApS within weeks |

> This infrastructure is designed for a founder-led, high-trust, low-volume outreach operation targeting conservative institutional buyers. Every choice prioritizes trust over scale.

---

## Strategic Context

### Why This Infrastructure Matters

The Precision Partner Acquisition Engine defines *what* to send and *who* to send it to. This document defines *how* to send it safely and credibly.

Museums are conservative, board-governed institutions. A Head of Digital at the Rijksmuseum or V&A who receives an outreach email will:

1. **Scan the subject line** (2 seconds) -- if it reads like automation, it's deleted
2. **Check the sender name and domain** (1 second) -- does this look real?
3. **Read the first 2-3 lines** (5 seconds) -- is this personalized to my museum?
4. **Check the sender's LinkedIn profile** -- is this a credible person?
5. **Google the company** -- does the website match what they claim?
6. **Possibly check the sending domain** -- does it resolve to a real site?

The infrastructure must pass every one of these checks without friction. A separate outreach domain that redirects to the main site, sends from a real founder identity, and has proper email authentication handles all of them.

### Relationship to Other Documents

| Document | What It Covers | How This Connects |
|----------|---------------|-------------------|
| [Precision Partner Acquisition Engine](../strategy/20260314-precision-partner-acquisition-engine.html) | The 6-module outreach system, messaging, targeting | This document is **Module 0** -- the infrastructure that Module 5 (Automation Layer) runs on |
| [TouriBot Marketing Platform](../marketing/20260317-touribot-marketing-platform-architecture.html) | AI operations platform with 11-stage museum pipeline | TouriBot sends outreach from hermann@aitourpilot.co using this infrastructure; manages research, personalization, response scoring, and pipeline tracking |
| LinkedIn Campaign Spring 2025 Analysis | Campaign performance data, audience segmentation | Consumer demand data feeds into outreach messaging as leverage |
| LinkedIn Campaign 2.0 (within the Engine) | 8-week content calendar, ad strategy | Runs in parallel on LinkedIn; email infrastructure is separate |

> **Timeline alignment:** The 6-week email warm-up protocol runs in parallel with the [TouriBot platform build](../marketing/20260317-touribot-marketing-platform-architecture.html) (~4 weeks). Domain registration and warm-up begin immediately (Week 1); TouriBot development runs in parallel. Real B2B outreach starts Week 4-5, when both the platform and email reputation are ready.

---

## The Domain Strategy

### Decision: Separate Domain (.co), Not Subdomain

Three approaches were evaluated through multi-expert analysis:

| Approach | Example | Verdict |
|----------|---------|---------|
| Main domain | hermann@aitourpilot.com | Maximum trust, but zero isolation -- one spam complaint affects all business email |
| Subdomain | hermann@mail.aitourpilot.com | Brand continuity, but partial reputation bleed-through to parent domain; complex DNS when parent uses Zoho |
| **Separate domain** | **hermann@aitourpilot.co** | **Complete isolation + clean inbox appearance** |

**Why .co wins for AITourPilot's specific situation:**

1. **Complete reputation isolation.** The .co domain has zero connection to aitourpilot.com's email reputation. If outreach generates spam complaints, Zoho business email on .com is unaffected.

2. **Clean inbox appearance.** Recipients see `hermann@aitourpilot.co` -- short, professional, indistinguishable from a normal business email. No subdomain prefix that might signal "marketing system." This matches industry practice observed in real B2B outreach (e.g., Danilo Abreu Ott sending from analyticsmade.co while the main site is at analyticsma.de).

3. **No DNS conflicts with Zoho.** The .com domain currently runs Zoho for email. Adding Google Workspace on a subdomain of .com would require careful SPF/DKIM/DMARC management across two email providers on the same domain tree. A separate domain avoids this entirely.

4. **Disposable if needed.** If a domain's reputation is ever damaged (unlikely at our volume, but possible if scaling), registering a replacement is trivial. You cannot replace a subdomain of your primary domain.

5. **Simple redirect solves the "two websites" problem.** A 301 redirect from aitourpilot.co to aitourpilot.com means anyone who checks the domain lands on the real site. No mirror needed, no content duplication.

### Domain Portfolio

| Domain | Purpose | Registrar | Renewal/yr | Status |
|--------|---------|-----------|-----------|--------|
| **aitourpilot.com** | Main website, Zoho email, core business identity | Edis.at (transferring to Cloudflare) | ~EUR 10-12 | Active |
| **aitourpilot.co** | Outreach email (Google Workspace), future website during rebuild | **Cloudflare** | ~EUR 22 | To register |
| **aitourpilot.eu** | Reserved / defensive; European market signal | **INWX** | EUR 10.00 | To register |
| **aitourpilot.de** | Germany / DACH market | **INWX** | EUR 5.02 | To register |
| **aitourpilot.co.uk** | United Kingdom market | **Cloudflare** | ~EUR 4.50 | To register |
| **aitourpilot.fr** | France market | **INWX** | EUR 11.00 | To register |
| **aitourpilot.nl** | Netherlands market | **INWX** | EUR 10.50 | To register |
| **aitourpilot.es** | Spain / Barcelona cluster | **INWX** | EUR 12.52 | To register |
| **aitourpilot.at** | Austria (home market) | **INWX** | EUR 13.00 | To register |
| **aitourpilot.dk** | Denmark (company domicile) | **INWX** | EUR 25.00 | To register |

### Why Two Registrars

**Cloudflare Registrar does not support most European country-code TLDs.** It cannot register .eu, .de, .fr, .nl, .es, .at, or .dk. This is because each country-code registry (e.g., DK Hostmaster for .dk, nic.at for .at) requires separate accreditation, and Cloudflare has only pursued accreditation for a limited set of TLDs.

**INWX** (inwx.de) is a Berlin-based wholesale domain registrar that supports 2,200+ TLDs including all European ccTLDs. They operate on a near-wholesale pricing model with minimal markup -- similar in philosophy to Cloudflare but with broader TLD coverage.

| | Cloudflare | INWX |
|---|---|---|
| **Domains** | .co, .co.uk, .com (transfer) | .eu, .de, .fr, .nl, .es, .at, .dk |
| **Pricing** | At-cost (zero markup) | Near-wholesale (minimal markup) |
| **DNS** | Best-in-class (used for all domains) | Good, but we point nameservers to Cloudflare instead |
| **TLD coverage** | Limited European ccTLDs | Comprehensive |
| **Redirects** | Free page rules | Header redirect available |
| **Country** | USA | Germany |

All INWX-registered domains point their nameservers to Cloudflare, giving a **single DNS dashboard** for all 10 domains regardless of where they are registered. The registrar holds the domain title; Cloudflare handles all DNS resolution, redirects, and record management.

### Registrar Pricing Comparison

The alternative of using a single registrar (Gandi) was evaluated and rejected due to cost:

| Approach | Year 1 | Year 2+ (annual) |
|----------|--------|------------------|
| **Cloudflare + INWX** (chosen) | ~EUR 86 | **~EUR 124/yr** |
| Gandi (single registrar) | ~EUR 87 | ~EUR 272/yr |
| INWX only | ~EUR 103 | ~EUR 135/yr |

The Cloudflare + INWX split saves approximately EUR 148/year compared to Gandi and EUR 11/year compared to INWX-only, while keeping the outreach domain (.co) on Cloudflare where DNS and redirect management is most convenient.

### Domain Ownership

All domains are initially registered under **Hermann Kudlich Consulting** (existing Cloudflare account: hermann@kudlich.at). AITourPilot ApS (Danish company) does not yet have a bank account -- expected within 1-2 weeks.

Once AITourPilot ApS is financially operational:

- **Option A:** Transfer domains to a new Cloudflare/INWX account under AITourPilot ApS
- **Option B:** Update WHOIS registrant to AITourPilot ApS on existing accounts
- **Option C:** Write a simple internal lease/assignment agreement (recommended for clean paper trail)

This is standard practice for early-stage companies. The domain registrant has no impact on email deliverability, DNS, or recipient trust.

### Future Country Domains (Priority Timing)

> Register all domains before the LinkedIn Campaign 2.0 launches. Once "paintings come alive" videos go viral again, domain squatters will notice. Domain age also starts accumulating from registration date -- earlier registration means better email reputation foundation if any domain is later used for regional outreach.

---

## Email Infrastructure

### Google Workspace Setup

A **new Google Workspace instance** on aitourpilot.co, completely separate from the Zoho setup on .com.

| Setting | Value |
|---------|-------|
| **Plan** | Business Starter |
| **Cost** | EUR 7.20/user/month (~EUR 86/year) |
| **Primary user** | hermann@aitourpilot.co |
| **Display name** | Hermann Kudlich |
| **Additional addresses** (later, if needed) | hello@aitourpilot.co, info@aitourpilot.co |

**Why a new Workspace instance (not adding .co to the Zoho account or an existing Workspace):**

- Zoho cannot manage a secondary domain on Google -- these are different providers
- Complete isolation: if the .co Workspace is ever compromised or restricted, .com business email is unaffected
- Separate admin, separate billing, separate reputation pool
- Clean architecture: one domain = one email provider, no confusion

### DNS Authentication Records

All records configured in **Cloudflare DNS** for aitourpilot.co (Cloudflare serves as both registrar and DNS for this domain):

**SPF Record:**
```
Type: TXT
Name: @
Value: v=spf1 include:_spf.google.com ~all
```

**DKIM Record:**
```
Type: TXT
Name: google._domainkey
Value: (generated by Google Workspace Admin > Apps > Gmail > Authenticate email)
```

**DMARC Record (initial -- permissive monitoring):**
```
Type: TXT
Name: _dmarc
Value: v=DMARC1; p=none; rua=mailto:dmarc-reports@aitourpilot.co; pct=100
```

**DMARC Record (after 2-4 weeks of clean sending -- tightened):**
```
Type: TXT
Name: _dmarc
Value: v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@aitourpilot.co; pct=100
```

### Sender Identity Rules

| Element | Value | Why |
|---------|-------|-----|
| **From address** | hermann@aitourpilot.co | Real founder = maximum trust for institutional buyers |
| **Display name** | Hermann Kudlich | Human name first; recipients see this before the email address |
| **Email signature** | Full name, "Co-Founder, AITourPilot", website link (aitourpilot.com) | The .com in the signature reinforces the main brand |
| **Reply-to** | hermann@aitourpilot.co (same as From) | No reply-to tricks; replies land in the outreach inbox |

**What to never use:**

- hans@, maria@, or any alias/persona -- museums will Google the sender; only Hermann's real identity passes the LinkedIn verification step
- sales@, info@, noreply@ -- signals automation, not founder-led outreach
- Any display name with emojis, brackets, or marketing language

---

## DNS and Hosting Architecture

### Current State (Before Changes)

```
aitourpilot.com (Edis.at)
\├\─\─ DNS: Edis.at nameservers
\├\─\─ Website: Squarespace
\├\─\─ Email: Zoho
\└\─\─ Renewal: May 24, 2026 (EUR 0.00 bundled with vHost)
```

### Target State (After All Migrations)

```
aitourpilot.com (registered: Cloudflare, DNS: Cloudflare)
\├\─\─ Website: Vercel (Next.js -- rebuilt site)
\├\─\─ Email: Zoho (unchanged)
\└\─\─ Status: Canonical domain, Google-indexed

aitourpilot.co (registered: Cloudflare, DNS: Cloudflare)
\├\─\─ Website: 301 redirect to aitourpilot.com
\├\─\─ Email: Google Workspace (outreach)
\└\─\─ Status: Outreach domain, not indexed

aitourpilot.eu, .de, .fr, .nl, .es, .at, .dk (registered: INWX, DNS: Cloudflare)
\├\─\─ Website: 301 redirect to aitourpilot.com
\└\─\─ Status: Reserved / defensive (all redirect via Cloudflare page rules)

aitourpilot.co.uk (registered: Cloudflare, DNS: Cloudflare)
\├\─\─ Website: 301 redirect to aitourpilot.com
\└\─\─ Status: Reserved / defensive
```

### Why Cloudflare for DNS (Even When Not the Registrar)

Cloudflare is used as the **DNS provider for all domains**, including those registered at INWX. This is done by setting nameservers at INWX to point to Cloudflare. The registrar holds the domain title; Cloudflare handles all DNS queries, redirects, and record management.

| Cloudflare DNS | Registrar DNS (INWX/Edis) |
|----------------|--------------------------|
| Global anycast network (~10ms worldwide) | Basic DNS, slower propagation |
| Free page rules (301 redirects without a server) | Redirect available but less flexible |
| Single dashboard for ALL domains | Only manages domains registered there |
| DDoS protection included | Not included |
| Free WHOIS privacy (for Cloudflare-registered domains) | Varies |

### About 301 Redirects

A 301 redirect is an HTTP standard (RFC 7231). **It works identically regardless of who serves it** -- Cloudflare, Vercel, INWX, or any other provider. Browsers, search engines, and email security scanners (Barracuda, Proofpoint, Mimecast) all handle 301s the same way. There is no "better" 301 -- choose whichever provider is most convenient for management.

### Cloudflare DNS Records for aitourpilot.co

```
# Website redirect (via Cloudflare Page Rule)
# Rule: aitourpilot.co/* -> 301 -> https://aitourpilot.com/$1

# Email -> Google Workspace
Type: MX   Name: @   Value: aspmx.l.google.com          Priority: 1
Type: MX   Name: @   Value: alt1.aspmx.l.google.com     Priority: 5
Type: MX   Name: @   Value: alt2.aspmx.l.google.com     Priority: 5
Type: MX   Name: @   Value: alt3.aspmx.l.google.com     Priority: 10
Type: MX   Name: @   Value: alt4.aspmx.l.google.com     Priority: 10

# Authentication (SPF, DKIM, DMARC as specified above)
```

**MX records (email) and A/CNAME records (website) are independent.** The 301 redirect handles web traffic; MX records handle email. They do not conflict. Millions of domains operate this way.

---

## Website Rebuild Plan

### Why Rebuild

The current aitourpilot.com is on Squarespace -- expensive, limited, and not suitable for the campaign landing pages and demo booking flows needed for the Precision Partner Acquisition Engine.

### Rebuild Strategy

| Phase | Domain | What Happens |
|-------|--------|-------------|
| **Phase 1: Build** | aitourpilot.co | Build the new Next.js site, deploy on Vercel, test on .co while .com stays on Squarespace |
| **Phase 2: Switch** | aitourpilot.com | Point .com to Vercel (the new site). Transfer .com from Edis to Cloudflare in the same move. |
| **Phase 3: Redirect** | aitourpilot.co | .co becomes a 301 redirect to .com. Email on .co continues to work independently. |
| **Phase 4: Cancel** | Squarespace | Cancel the Squarespace subscription |

### Vercel Hosting

Vercel is not traditional webspace. There is no server to rent or manage.

| Traditional Hosting (Edis, Hostinger) | Vercel |
|---------------------------------------|--------|
| Rent a server (VPS) or folder on shared hosting | Push code to GitHub; Vercel auto-builds and serves globally |
| Monthly fee regardless of usage | **Free tier** covers most sites; Pro is EUR 20/month if needed |
| You manage the server, updates, security | Fully managed; automatic SSL, CDN, edge network |
| Good for PHP, custom server software | Optimized for Next.js, React, static sites |

**For the immediate need:** No Vercel setup required. Cloudflare handles the .co redirect via a free Page Rule. Vercel enters the picture only when the website rebuild begins.

**Cost:**

| Tier | Price | What You Get |
|------|-------|-------------|
| **Hobby (Free)** | EUR 0/month | 1 project, sufficient for the landing page and initial rebuild |
| **Pro** | EUR 20/month | Multiple projects, analytics, more bandwidth -- use when .com migrates |

---

## Google Indexing and Legitimacy

### Will aitourpilot.co be indexed by Google?

**No -- and that's correct behavior.** A 301-redirected domain tells Google "this domain permanently points to aitourpilot.com." Google follows the redirect and indexes only the destination. You do not want two versions of your site competing in search results.

### Does non-indexing affect email deliverability?

**No.** Email providers (Gmail, Outlook, Apple Mail) do not cross-reference Google Search index for spam filtering. What they check:

| Check | How .co Passes |
|-------|---------------|
| DNS authentication (SPF/DKIM/DMARC) | Configured in Cloudflare |
| Domain age | Starts accumulating from registration date -- register now |
| Sending patterns | Low volume, consistent cadence via Instantly.ai |
| Website resolves | 301 redirect lands on a real site (aitourpilot.com) |
| Spam complaints | Highly personalized outreach to researched contacts = very low risk |

### At 100+ emails/day (future scaling)

The domain will have 2+ months of age and warm-up history by the time volume scales. At that point:

- Use **2-3 mailboxes** rotating (hermann@, hello@, info@aitourpilot.co) -- Instantly.ai handles rotation
- Monitor deliverability via Google Postmaster Tools
- The 301 redirect continues to satisfy website checks -- email security tools (Barracuda, Proofpoint) follow redirects

> Domain age matters more than indexing. Register now, even before sending a single email, so the clock starts ticking.

---

## Email Warm-Up Protocol

A new domain sending cold email will land in spam without proper warm-up. This is the most critical step.

### Pre-Send Setup (Day 0)

Before sending any email:

1. Configure all DNS records (SPF, DKIM, DMARC) in Cloudflare
2. Create the Google Workspace account
3. Set up a professional email signature (name, title, company, aitourpilot.com website link)
4. Connect to Instantly.ai for automated warm-up
5. Send a test email to mail-tester.com -- verify score is 9/10 or higher

### Warm-Up Timeline

| Week | Daily Volume | Activity |
|------|-------------|----------|
| **Week 1-2** | 5-10 emails/day | Send to known contacts: friends, colleagues, existing warm contacts from the 74-person list. Have real conversations -- **replies are the strongest reputation signal.** Subscribe to a few newsletters to generate inbound mail. Instantly.ai auto warm-up runs in parallel. |
| **Week 3** | 10-20 emails/day | Mix known contacts with light outreach to best-fit prospects. Keep reply rate high. |
| **Week 4** | 20-30 emails/day | Begin real B2B outreach. Highly personalized only. Monitor bounce rate (must stay under 2%). |
| **Week 5-6** | 30-50 emails/day | Gradual scale-up. If engagement is healthy, this is steady-state for a single mailbox. |
| **Week 7+** | 50-80 emails/day | Full capacity. Add second mailbox if needed. Never exceed ~100/day from one address. |

### Critical Rules During Warm-Up

1. **No bulk email in weeks 1-2.** Only real conversations with real people.
2. **Replies are gold.** Each reply boosts domain reputation. Ask questions that invite responses.
3. **No attachments or heavy HTML** in early emails. Plain text only.
4. **Verify email addresses before sending** using ZeroBounce or NeverBounce. Bounce rate must stay under 2%.
5. **Don't send on weekends** during warm-up. Business hours only (Tue-Fri, 9:00-16:00 CET).
6. **Don't send from the outreach domain for personal email.** Keep it exclusively for professional outreach.

### Warm-Up Tool

| Tool | Cost | Why |
|------|------|-----|
| **Instantly.ai** (Growth plan) | ~EUR 30/month | All-in-one: automated warm-up + cold email sequencing + analytics. Connects directly to Google Workspace. Handles mailbox rotation when scaling. |

---

## Domain Transfer: aitourpilot.com from Edis.at to Cloudflare

### Why Transfer

| Reason | Detail |
|--------|--------|
| **Consolidate DNS** | All domains (.com, .co, .eu) managed in one Cloudflare dashboard |
| **Avoid Edis renewal** | Current .com billed at EUR 0.00 (bundled with vHost) but renewal is May 24 -- verify what the vHost itself costs |
| **Campaign readiness** | DNS changes for Vercel migration are simpler when already on Cloudflare |
| **Better tools** | Cloudflare page rules, analytics, and edge caching support the campaign landing pages |

### Pre-Transfer Checklist

Before initiating the transfer, **document every DNS record currently at Edis.at:**

| Record Type | Name | Value | Purpose |
|-------------|------|-------|---------|
| MX | @ | (Zoho MX servers) | Zoho email |
| TXT | @ | v=spf1 include:zoho... | SPF for Zoho |
| TXT | zmail._domainkey | (Zoho DKIM key) | DKIM for Zoho |
| TXT | _dmarc | (DMARC policy) | DMARC |
| CNAME or A | @ | (Squarespace IP/CNAME) | Website |
| CNAME | www | (Squarespace) | Website |
| TXT | @ | (Squarespace verification) | Domain verification |

**Replicate ALL of these in Cloudflare before the transfer completes.** This ensures zero downtime for email and website.

### Transfer Steps

1. **At Edis.at:** Go to Domain > Domaininhaber, ensure WHOIS contact email is accessible
2. **At Edis.at:** Disable domain lock ("Verriegelung" -- currently set to "ja", change to "nein")
3. **At Edis.at:** Request the EPP/Auth-Code (Transfer-Code/Autorisierungscode)
4. **At Cloudflare:** Add aitourpilot.com as a site first (free plan). This lets you pre-configure all DNS records.
5. **At Cloudflare:** Go to Registrar > Transfer Domain > enter aitourpilot.com > paste auth code > pay (~EUR 10-12 for 1 year extension from current expiry)
6. **Approve transfer:** Edis will send a confirmation email. Approve it to speed things up (otherwise it auto-completes in 5 days).
7. **Verify:** Once transfer completes, check that email (Zoho) and website (Squarespace) still work.

### Timeline

| Step | When |
|------|------|
| Pre-configure DNS records in Cloudflare | Week of March 24 |
| Initiate transfer at Cloudflare | Week of March 24 |
| Transfer completes | Late March / Early April |
| Verify email + website | Immediately after transfer |
| Switch .com to Vercel | When new site is ready (April-May) |
| Cancel Squarespace | After .com points to Vercel |

> **Important:** When transferring a domain to Cloudflare, registration is automatically extended by 1 year from the current expiry. So transferring now means .com is paid through approximately May 2027 at Cloudflare's at-cost rate.

---

## Budget Summary

### Domain Costs (Annual)

| Domain | Registrar | 1st Year | Renewal/yr |
|--------|-----------|----------|-----------|
| aitourpilot.co | Cloudflare | ~EUR 22 | ~EUR 22 |
| aitourpilot.co.uk | Cloudflare | ~EUR 4.50 | ~EUR 4.50 |
| aitourpilot.eu | INWX | EUR 5.00 | EUR 10.00 |
| aitourpilot.de | INWX | EUR 5.02 | EUR 5.02 |
| aitourpilot.fr | INWX | EUR 11.00 | EUR 11.00 |
| aitourpilot.nl | INWX | EUR 10.50 | EUR 10.50 |
| aitourpilot.es | INWX | EUR 12.52 | EUR 12.52 |
| aitourpilot.at | INWX | EUR 13.00 | EUR 13.00 |
| aitourpilot.dk | INWX | EUR 25.00 | EUR 25.00 |
| aitourpilot.com transfer | Cloudflare | ~EUR 10-12 | ~EUR 10-12 |
| **Domain total** | | **~EUR 119** | **~EUR 124/yr** |

### Service Costs (Annual)

| Item | Cost | Frequency |
|------|------|-----------|
| Google Workspace Business Starter (1 user) | ~EUR 86 | Annual |
| **Total services** | **~EUR 86/year** | |

### Combined Annual Fixed Costs

| | Year 1 | Year 2+ |
|---|---|---|
| Domains (all 10) | ~EUR 119 | ~EUR 124 |
| Google Workspace | ~EUR 86 | ~EUR 86 |
| **Total fixed** | **~EUR 205** | **~EUR 210/yr** |

### Monthly Operational Costs

| Item | Cost | Duration |
|------|------|----------|
| Instantly.ai (warm-up + sending) | ~EUR 30/month | Active outreach months |
| Email verification (ZeroBounce) | ~EUR 15-20/month | Active outreach months |
| Vercel Hobby tier | EUR 0 | Ongoing |
| **Total monthly** | **~EUR 45-50/month** | |

### Cost Savings

| Removed | Saved |
|---------|-------|
| Squarespace subscription (after migration) | ~EUR 15-30/month |
| Edis.at vHost (if no longer needed after .com transfer) | Check current rate |

---

## Complete Execution Timeline

### Week 1 (March 20-28): Foundation

| Day | Action |
|-----|--------|
| Day 1 | Register aitourpilot.co + aitourpilot.co.uk at **Cloudflare** |
| Day 1 | Register aitourpilot.eu, .de, .fr, .nl, .es, .at, .dk at **INWX** |
| Day 1 | Point all INWX domains' nameservers to Cloudflare |
| Day 1 | Set up 301 redirects for all domains to aitourpilot.com via Cloudflare Page Rules |
| Day 1 | Sign up for Google Workspace Business Starter on .co |
| Day 1 | Configure DNS for .co: MX records, SPF, DKIM, DMARC in Cloudflare |
| Day 2 | Send test email to mail-tester.com, verify 9+/10 score |
| Day 2 | Sign up for Instantly.ai, connect Google Workspace, start auto warm-up |
| Day 3-7 | Send 5-10 manual emails/day to known contacts |

### Week 2-3 (March 25 - April 7): Warm-Up + Domain Transfer

| Action | Detail |
|--------|--------|
| Continue warm-up | 10-20 emails/day, mix of known contacts and light outreach |
| Initiate .com transfer | Unlock at Edis, get auth code, start transfer at Cloudflare |
| Pre-configure .com DNS in Cloudflare | Replicate all Edis DNS records before transfer completes |
| Prepare lead list | Module 2 of the Precision Partner Acquisition Engine |
| Write outreach sequences | Module 4 of the Engine |
| Begin LinkedIn authority content | Week 1-2 of the Engine's content calendar |

### Week 4-5 (April 8-21): Launch Outreach

| Action | Detail |
|--------|--------|
| Begin real B2B outreach | 5-10 emails/day, highly personalized (Module 3-4) |
| .com transfer completes | Verify Zoho email + Squarespace website still work |
| Send reactivation emails | 74 warm contacts from Spring 2025 campaign |
| Post LinkedIn award announcement | The trigger for the entire Engine |
| Scale to 15-20 emails/day | If engagement metrics are healthy |

### Week 6-8 (April 22 - May 12): Scale + Convert

| Action | Detail |
|--------|--------|
| Conduct demo calls | Score 4-5 responses from Module 6 |
| Scale to 30-50 emails/day | Add second mailbox if needed |
| Launch LinkedIn Lead Gen ads | Week 6-8 of Engine content calendar |
| Prepare pilot proposals | Museum-specific, based on demo conversations |
| Begin website rebuild | Next.js on Vercel, build on .co, test alongside Squarespace |

### Week 9+ (May 13+): Migrate + Close

| Action | Detail |
|--------|--------|
| Switch .com to Vercel | New website goes live on the main domain |
| Redirect .co to .com | .co email continues working independently |
| Cancel Squarespace | No longer needed |
| Close pilot deal(s) | Push for agreement with strongest prospects |
| Transfer domain ownership to AITourPilot ApS | When ApS bank account is active |

---

## Risk Mitigation

### What If the .co Domain Gets Flagged?

At 5-15 personalized emails/day to verified, researched contacts, this is extremely unlikely. But if it happens:

1. Register a replacement domain (aitourpilot.io, aitourpilot.xyz, etc.)
2. Set up a new Google Workspace instance
3. Warm up for 2 weeks
4. Resume outreach

The .com domain and Zoho email are completely unaffected.

### What If a Museum Checks .co and Finds a Redirect?

This is expected and normal behavior. The recipient types aitourpilot.co into their browser, it immediately redirects to aitourpilot.com, and they see the full website. The verification loop closes cleanly. This is identical to how Danilo Abreu Ott operates: sending from analyticsmade.co, with the main site at analyticsma.de.

### What If Google Workspace Has Deliverability Issues?

Monitor via:

- **Google Postmaster Tools** -- tracks domain reputation, spam rate, authentication
- **Instantly.ai analytics** -- tracks open rates (directional only due to Apple Mail inflation), reply rates, bounce rates
- **mail-tester.com** -- periodic checks of email score

If issues arise, the first fix is always: reduce volume, increase personalization quality, verify email addresses more aggressively.

### What If the Edis Transfer Fails or Stalls?

Domain transfers occasionally get delayed by the losing registrar. If Edis does not release the domain within 7 days:

1. Contact Edis support directly
2. Ensure the domain is fully unlocked and the auth code is correct
3. Check that WHOIS contact email is accessible (transfer approval emails go there)

The transfer does not affect current website or email service -- DNS continues resolving throughout the process.

---

## Decisions Log

All infrastructure decisions made in this planning phase, with rationale:

| # | Decision | Options Considered | Chosen | Why |
|---|----------|-------------------|--------|-----|
| 1 | Outreach domain type | Main domain, subdomain, separate domain | Separate domain (.co) | Complete isolation; clean appearance; no Zoho DNS conflict |
| 2 | TLD for outreach | .co, .eu, .io | .co (+ 8 defensive domains) | .co is universally recognized business TLD; country TLDs for market coverage |
| 3 | Domain registrars | Cloudflare only, INWX only, Gandi only, Cloudflare + INWX | **Cloudflare + INWX** | Cloudflare cannot register .at, .dk, .eu, .de, .fr, .nl, .es; INWX covers all European ccTLDs at wholesale pricing; Gandi renewals 3x more expensive (~EUR 272/yr vs ~EUR 124/yr) |
| 4 | DNS management | Per-registrar DNS, Cloudflare for all | **Cloudflare for all** | Single dashboard; all INWX domains point nameservers to Cloudflare |
| 5 | Email provider for outreach | Google Workspace (same instance), Google Workspace (new), Zoho secondary | Google Workspace (new instance) | Complete isolation from business email; separate admin/billing/reputation |
| 6 | Sender identity | hermann@, hans@, hello@, sales@ | hermann@ | Real founder identity; passes LinkedIn verification; maximum trust |
| 7 | Website hosting | Edis VPS, Hostinger, Cloudflare Pages, Vercel | Vercel | Optimized for Next.js; free tier; auto-deploy from GitHub |
| 8 | .com transfer timing | Now, after site rebuild, never | Before May 24 renewal | Consolidate DNS; avoid Edis billing; prepare for campaign traffic |
| 9 | Warm-up tool | Instantly.ai, Lemlist, Warmbox, manual only | Instantly.ai | All-in-one warm-up + sequencing; best integration with Google Workspace |
| 10 | Initial .co website | Full mirror, landing page, 301 redirect | 301 redirect to .com | Zero maintenance; 301 works identically across all providers (RFC 7231 standard); real site on .com satisfies trust checks |
| 11 | Google indexing of .co | Index both, noindex .co, 301 redirect | 301 redirect (auto noindex) | Correct SEO practice; one canonical domain; no duplicate content |
| 12 | Domain ownership | AITourPilot ApS, Hermann Kudlich Consulting | **Consulting (temporary)** | ApS bank account pending; assign/transfer to ApS within weeks via simple internal agreement |

---

*Based on: Multi-expert analysis (email deliverability, museum buyer psychology, infrastructure architecture), Precision Partner Acquisition Engine strategic framework, Spring 2025 LinkedIn campaign data, Edis.at account review, and registrar pricing research (Cloudflare, INWX, Gandi, Porkbun, Simply.com, OVHcloud).*

*Sources consulted: Lemlist Help Center, Woodpecker Blog, Instantly.ai Blog, LeadsMonky, Allegrow, GlockApps, Mailreach, Hunter.io, Google Workspace documentation, Cloudflare documentation, INWX.de pricing and TLD support.*

*Compiled: March 2026 (updated March 20 with registrar strategy and pricing research)*
