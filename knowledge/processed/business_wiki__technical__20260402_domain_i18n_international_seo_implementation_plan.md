# 20260402-domain-i18n-international-seo-implementation-plan

*Source: Business Wiki / technical/20260402-domain-i18n-international-seo-implementation-plan.html*

# Domain, i18n & International SEO Strategy for AITourPilot

**Date:** 2 April 2026
**Author:** Senior Web Marketing & International SEO Strategy Analysis
**Status:** Strategic recommendation -- pending decision
**Audience:** Founders, marketing, development

---

## Table of Contents

1. [Current State Assessment](#1-current-state-assessment)
2. [Domain Strategy: Four Options Compared](#2-domain-strategy-four-options-compared)
3. [Vercel Cost Analysis](#3-vercel-cost-analysis)
4. [Google Crawling & SEO Implementation](#4-google-crawling--seo-implementation)
5. [User Experience Considerations](#5-user-experience-considerations)
6. [Marketing Platform Integration](#6-marketing-platform-integration)
7. [Final Recommendation](#7-final-recommendation)
8. [Implementation Plan](#8-implementation-plan)
9. [Risk Register](#9-risk-register)

---

## 1. Current State Assessment

### What Exists Today

| Component | Current State |
|-----------|--------------|
| **Main site** | `aitourpilot.com` -- Next.js on Vercel (Hobby tier), English + German |
| **Engage site** | `engage.aitourpilot.com` -- campaign landing pages, separate Vercel project |
| **i18n library** | `next-intl` with `localePrefix: "as-needed"` |
| **URL structure** | English at `/`, German at `/de` |
| **Locales configured** | `en`, `de` only |
| **Sitemap** | Static, 4 URLs (homepage + privacy in both languages) |
| **robots.txt** | Simple allow-all with `/api/` disallowed |
| **hreflang** | Not implemented |
| **Middleware** | No custom middleware (next-intl handles routing internally) |
| **DNS** | All domains on Cloudflare DNS (registrars: Cloudflare + INWX) |
| **Outreach domain** | `aitourpilot.co` -- isolated for B2B email via Google Workspace |

### Domain Portfolio

| Domain | Registrar | Current Use | Annual Cost |
|--------|-----------|-------------|-------------|
| aitourpilot.com | Cloudflare | Main site (Vercel) + Zoho email | ~EUR 10-12 |
| aitourpilot.co | Cloudflare | Outreach email (Google Workspace), 301 to .com | ~EUR 22 |
| aitourpilot.co.uk | Cloudflare | Reserved -- 301 redirect | ~EUR 4.50 |
| aitourpilot.de | INWX | Reserved -- 301 redirect | EUR 5.02 |
| aitourpilot.at | INWX | Reserved -- 301 redirect | EUR 13.00 |
| aitourpilot.ch | (assumed owned) | Reserved -- 301 redirect | ~EUR 10-15 |
| aitourpilot.dk | INWX | Reserved -- 301 redirect | EUR 25.00 |
| aitourpilot.fr | INWX | Reserved -- 301 redirect | EUR 11.00 |
| aitourpilot.nl | INWX | Reserved -- 301 redirect | EUR 10.50 |
| aitourpilot.es | INWX | Reserved -- 301 redirect | EUR 12.52 |
| aitourpilot.eu | INWX | Reserved -- 301 redirect | EUR 10.00 |
| aitourpilot.org | (assumed owned) | Reserved -- 301 redirect | ~EUR 10-12 |

**Total domain cost:** ~EUR 144-154/year (already committed regardless of strategy chosen)

### Target Markets (Priority Order)

| Market | Language | ccTLD | Strategic Importance |
|--------|----------|-------|---------------------|
| Germany | German | .de | DACH anchor, largest museum market in Europe |
| Austria | German | .at | Home market of founder |
| Switzerland | German/French | .ch | High-value museum market (DACH) |
| Denmark | Danish/English | .dk | Company domicile, registered office |
| Spain | Spanish | .es | Barcelona HQ origin, La Pedrera connection |
| Netherlands | Dutch/English | .nl | Progressive museum market (Rijksmuseum, Van Gogh) |
| France | French | .fr | Major museum market (Louvre, Orsay) |
| UK | English | .co.uk | Large English-speaking museum market |
| EU-wide | Multiple | .eu | Pan-European signal |

### Languages Needed (Phased)

| Phase | Languages | Markets Served |
|-------|-----------|---------------|
| **Phase 1 (now)** | English, German | UK, DE, AT, CH, NL, DK, global |
| **Phase 2 (Q3 2026)** | + French, Spanish | FR, ES, CH (French), Latin America |
| **Phase 3 (Q4 2026+)** | + Danish, Dutch | DK, NL (native experience) |

Note: Museums in the Netherlands, Denmark, and Scandinavia generally operate in English at decision-maker level. Native-language sites for these markets are a "nice to have" rather than a conversion necessity.

---

## 2. Domain Strategy: Four Options Compared

### Option A: Single Domain with Subdirectories

**Structure:** `aitourpilot.com/de`, `aitourpilot.com/fr`, `aitourpilot.com/es`, etc.

| Aspect | Assessment |
|--------|-----------|
| **Pros** | |
| Domain authority | 100% consolidated -- all backlinks, all content authority flows to one domain |
| Management | Single Vercel project, single deployment pipeline, single analytics property |
| SEO simplicity | One Google Search Console property (with hreflang for language targeting) |
| Cost | Zero incremental cost -- already running |
| Speed to market | Adding a language = adding translation files + routes, no infrastructure work |
| **Cons** | |
| Local trust signal | No ccTLD trust indicator in SERPs (mitigated by hreflang + GSC geo-targeting) |
| Perceived locality | A German museum director sees `.com/de` rather than `.de` -- slightly less local feel |
| ccTLD waste | Owned ccTLDs are purely defensive (redirect-only) |

### Option B: ccTLDs Redirecting to Subdirectories

**Structure:** `aitourpilot.de` 301-redirects to `aitourpilot.com/de`, `aitourpilot.fr` 301-redirects to `aitourpilot.com/fr`, etc.

| Aspect | Assessment |
|--------|-----------|
| **Pros** | |
| Local trust for typed URLs | If someone types `aitourpilot.de` directly, they land on German content |
| Email credibility | Outreach from `.co` linking to "aitourpilot.de" looks locally relevant |
| Defensive value preserved | Prevents squatting, redirects to correct language version |
| Vanity URLs in print | Business cards for German market can show `aitourpilot.de` |
| **Cons** | |
| SEO: zero value from ccTLDs | 301 redirects pass authority to the destination; the ccTLD itself is not indexed. Google sees only `.com/de`. |
| User confusion potential | Visitor types `aitourpilot.de`, URL bar changes to `aitourpilot.com/de` -- slight disconnect |
| Redirect maintenance | Must keep Cloudflare page rules correct for all 8+ domains |
| False sense of local presence | The redirect provides no actual ranking benefit in local SERPs |

### Option C: ccTLDs Serving Localized Content Directly

**Structure:** `aitourpilot.de` serves German content directly, `aitourpilot.fr` serves French content, etc.

| Aspect | Assessment |
|--------|-----------|
| **Pros** | |
| Strongest local SEO signal | ccTLD is the single most powerful geo-targeting signal for Google |
| Maximum local trust | German museums see `.de` throughout their experience |
| Clean URLs | `aitourpilot.de/museen` feels native |
| **Cons** | |
| Split domain authority | Each domain starts at zero authority. Backlinks are fragmented across 8+ domains. For a startup with no existing backlink profile, this is devastating. |
| Multiple deployments | 8+ Vercel projects or complex multi-domain routing |
| Vercel cost | Pro plan required (EUR 20/month minimum); potentially one per project |
| Content synchronization | Every page change must deploy to all domains |
| Analytics fragmentation | Separate GA4 properties or complex cross-domain tracking |
| GSC complexity | 8+ Search Console properties to monitor |
| Development burden | Multiplied testing, staging, QA across domains |
| Canonical confusion | Must carefully set canonical URLs to avoid duplicate content penalties |
| Startup-inappropriate scale | This is a Fortune 500 strategy (e.g., IKEA, BMW). For a pre-revenue startup targeting 50-150 museum contacts, it is massive over-engineering. |

### Option D: Hybrid -- Subdirectories + ccTLD Redirects to Language Versions

**Structure:** Content lives at `aitourpilot.com/de`, `aitourpilot.com/fr`, etc. ccTLDs redirect intelligently: `aitourpilot.de` redirects to `aitourpilot.com/de`, `aitourpilot.fr` redirects to `aitourpilot.com/fr`, `aitourpilot.co.uk` redirects to `aitourpilot.com` (English).

| Aspect | Assessment |
|--------|-----------|
| **Pros** | |
| All advantages of Option A | Consolidated authority, single deployment, simple management |
| ccTLD vanity utility | Local domains usable in print materials, email signatures, QR codes |
| Smart entry point | Visitor typing a ccTLD lands on the right language |
| Future-proof | If you ever want to move to Option C, the redirects can be changed to serve content |
| Zero incremental infrastructure | Cloudflare page rules handle all redirects (free) |
| **Cons** | |
| Same as Option B | URL bar changes on redirect; no SEO ranking benefit from ccTLDs themselves |
| Redirect mapping maintenance | Must update Cloudflare rules when adding new language paths |

---

### Side-by-Side Comparison Matrix

| Criterion | Weight | A: Subdirs Only | B: ccTLD -> subdir | C: ccTLD direct | D: Hybrid |
|-----------|--------|-----------------|-------------------|-----------------|-----------|
| Domain authority consolidation | 25% | 10 | 10 | 2 | 10 |
| Local SEO ranking signal | 15% | 5 | 5 | 10 | 5 |
| Management complexity | 20% | 10 | 8 | 2 | 8 |
| Vercel cost | 10% | 10 | 10 | 3 | 10 |
| Local trust perception | 10% | 4 | 6 | 10 | 7 |
| Future flexibility | 10% | 7 | 7 | 8 | 9 |
| Marketing integration | 10% | 8 | 8 | 6 | 9 |
| **Weighted Score** | **100%** | **8.0** | **7.8** | **4.9** | **8.2** |

**Option D wins.** It captures 97% of the benefit of a pure subdirectory approach while using the ccTLD portfolio for practical marketing value.

---

## 3. Vercel Cost Analysis

### Projects Required Per Option

| Option | Vercel Projects | Plan Required | Monthly Cost |
|--------|----------------|---------------|-------------|
| **A: Subdirectories only** | 1 (main site) + 1 (engage) = **2** | Hobby (free) or Pro | EUR 0-20 |
| **B: ccTLDs redirect** | Same as A: **2** (redirects are Cloudflare, not Vercel) | Hobby or Pro | EUR 0-20 |
| **C: ccTLDs direct** | 1 per ccTLD + 1 engage = **9-10** | Pro required | EUR 180-200 |
| **D: Hybrid** | Same as A: **2** | Hobby or Pro | EUR 0-20 |

### Can One Vercel Project Serve Multiple Domains?

**Yes.** Vercel Pro allows adding multiple custom domains to a single project. You could add `aitourpilot.de`, `aitourpilot.fr`, etc. as domains to the main project. However, this alone does not solve the routing problem -- the Next.js app still needs to know which language to serve based on the incoming domain.

There are two sub-approaches for multi-domain on one project:

1. **Domains as aliases (redirect):** Add ccTLDs to Vercel project settings with "redirect to primary domain" enabled. Vercel handles the 301 automatically. This is equivalent to Option D but Vercel does the redirect instead of Cloudflare.

2. **Domains with middleware routing:** Add ccTLDs to Vercel project, then use Next.js middleware to detect the incoming hostname and rewrite to the appropriate locale. This achieves Option C behavior with a single project.

**Recommended for Option D:** Use Cloudflare Page Rules for the redirects (already configured), not Vercel. Reasons:
- Cloudflare redirects resolve at the edge before hitting Vercel, saving serverless function invocations
- No changes needed to the Next.js codebase
- Already the established pattern per the Outreach Infrastructure Blueprint
- One fewer point of failure

### Cost Summary (Recommended: Option D)

| Item | Monthly | Annual |
|------|---------|--------|
| Vercel Hobby (main site) | EUR 0 | EUR 0 |
| Vercel Hobby (engage site) | EUR 0 | EUR 0 |
| Upgrade to Pro (when needed) | EUR 20 | EUR 240 |
| Cloudflare (DNS + redirects) | EUR 0 | EUR 0 |
| **Total Vercel infrastructure** | **EUR 0-20** | **EUR 0-240** |

The Pro upgrade becomes necessary when:
- You need analytics (Vercel Analytics)
- You exceed Hobby bandwidth (100 GB/month)
- You need password-protected preview deployments
- You need team collaboration features

For a B2B marketing site targeting 50-150 museum contacts, the Hobby tier will be sufficient for months.

---

## 4. Google Crawling & SEO Implementation

### 4.1 hreflang Implementation

hreflang is the single most critical technical SEO element for a multilingual site. It tells Google which page serves which language/region combination, preventing duplicate content issues and ensuring users see the correct language version in search results.

#### Implementation Strategy: HTML `<link>` Tags in `<head>`

For a Next.js site with `next-intl`, the recommended approach is adding hreflang link tags via the layout metadata.

**For every page, include all language alternates plus an x-default:**

```
English page (aitourpilot.com/):
  <link rel="alternate" hreflang="en" href="https://www.aitourpilot.com/" />
  <link rel="alternate" hreflang="de" href="https://www.aitourpilot.com/de/" />
  <link rel="alternate" hreflang="fr" href="https://www.aitourpilot.com/fr/" />
  <link rel="alternate" hreflang="es" href="https://www.aitourpilot.com/es/" />
  <link rel="alternate" hreflang="x-default" href="https://www.aitourpilot.com/" />

German page (aitourpilot.com/de/):
  <link rel="alternate" hreflang="en" href="https://www.aitourpilot.com/" />
  <link rel="alternate" hreflang="de" href="https://www.aitourpilot.com/de/" />
  <link rel="alternate" hreflang="fr" href="https://www.aitourpilot.com/fr/" />
  <link rel="alternate" hreflang="es" href="https://www.aitourpilot.com/es/" />
  <link rel="alternate" hreflang="x-default" href="https://www.aitourpilot.com/" />
```

**Key rules:**
- `x-default` should point to the English version (the "catch-all" for unmatched locales)
- Every page must reference ALL alternate versions, including itself
- hreflang must be bidirectional (EN points to DE, DE points to EN)
- Use full absolute URLs, never relative
- Use bare language codes (`de`, `fr`) unless you need region-specific targeting (`de-AT`, `de-CH`)

#### When to Use Region-Specific hreflang

For AITourPilot's B2B use case, bare language codes are sufficient:

| Approach | When to Use |
|----------|-------------|
| `hreflang="de"` | One German version serves all German-speaking markets (DE, AT, CH) -- **recommended for now** |
| `hreflang="de-DE"` + `hreflang="de-AT"` + `hreflang="de-CH"` | Only if you create separate pages with different pricing, legal terms, or culturally distinct content per country |

Since AITourPilot's German content is uniform across DACH, use `hreflang="de"`. If you later create Austria-specific or Switzerland-specific landing pages (e.g., different museum references, local pricing), you can add region-specific variants.

### 4.2 Sitemap Strategy

The current sitemap is static and incomplete. It must become dynamic and language-aware.

#### Recommended: One Sitemap with Language Alternates

Replace the static `sitemap.ts` with a dynamic version:

```
Sitemap structure (sitemap.xml):

<url>
  <loc>https://www.aitourpilot.com/</loc>
  <xhtml:link rel="alternate" hreflang="en" href="https://www.aitourpilot.com/" />
  <xhtml:link rel="alternate" hreflang="de" href="https://www.aitourpilot.com/de/" />
  <xhtml:link rel="alternate" hreflang="x-default" href="https://www.aitourpilot.com/" />
  <lastmod>2026-04-02</lastmod>
  <changefreq>weekly</changefreq>
  <priority>1.0</priority>
</url>

<url>
  <loc>https://www.aitourpilot.com/de/</loc>
  <xhtml:link rel="alternate" hreflang="en" href="https://www.aitourpilot.com/" />
  <xhtml:link rel="alternate" hreflang="de" href="https://www.aitourpilot.com/de/" />
  <xhtml:link rel="alternate" hreflang="x-default" href="https://www.aitourpilot.com/" />
  <lastmod>2026-04-02</lastmod>
  <changefreq>weekly</changefreq>
  <priority>0.9</priority>
</url>

... (repeat for every page in every language)
```

**Why one sitemap (not per-language sitemaps):**
- Google recommends including hreflang annotations within the sitemap itself
- Easier to maintain and verify completeness
- A single sitemap index is all that is needed until the site exceeds 50,000 URLs

**When to split into per-language sitemaps:**
Only if the site grows to thousands of pages (unlikely for a B2B marketing site). At that point, use a sitemap index:
```
sitemap-index.xml
  -> sitemap-en.xml
  -> sitemap-de.xml
  -> sitemap-fr.xml
```

### 4.3 robots.txt Strategy

The current `robots.ts` is adequate but should be extended:

```
User-agent: *
Allow: /
Disallow: /api/
Disallow: /_next/

Sitemap: https://www.aitourpilot.com/sitemap.xml
```

**For the ccTLD domains (aitourpilot.de, .fr, etc.):** Since they are 301-redirecting via Cloudflare (not serving content), they do not need a robots.txt. Googlebot follows the 301 and respects the destination's robots.txt.

**For engage.aitourpilot.com:** Consider whether campaign landing pages should be indexed. If they are meant for paid traffic only:

```
User-agent: *
Disallow: /
```

If some pages (like `/museums`) should be indexable:

```
User-agent: *
Allow: /museums
Disallow: /
```

### 4.4 Canonical URLs

Every page must declare a canonical URL to prevent duplicate content issues.

**Rules:**
- The canonical URL for English pages is the version without locale prefix: `https://www.aitourpilot.com/privacy-policy`
- The canonical URL for German pages includes the prefix: `https://www.aitourpilot.com/de/privacy-policy`
- Each language version is canonical to itself (not cross-language canonical)
- Always use `https://www.` (consistent protocol + www/non-www)

**Common mistake to avoid:** Do NOT set the canonical of `aitourpilot.com/de/` to `aitourpilot.com/`. Each language version should be its own canonical. The hreflang tags handle the relationship between versions.

### 4.5 Google Search Console Strategy

**Recommended: One property with international targeting**

| Approach | Properties | When to Use |
|----------|-----------|-------------|
| **Single domain property** | `https://www.aitourpilot.com` (1 property) | Small multilingual sites with subdirectory structure -- **recommended** |
| Multiple properties | 1 per ccTLD | Only if ccTLDs serve content directly (Option C) |

**Setup steps:**
1. Add `https://www.aitourpilot.com` as a property (URL prefix type)
2. Also verify via Domain property (`aitourpilot.com`) for a complete view including non-www
3. Use the "International Targeting" section to monitor hreflang errors
4. Check the "Coverage" report per language by filtering URL paths (`/de/`, `/fr/`, etc.)

**No need for separate properties for ccTLDs** because they 301-redirect. Google will show the redirect destination (`.com/de`) in Search Console, not the ccTLD.

**Google does NOT use the International Targeting tool for subdirectory structures.** The geo-targeting setting in GSC only applies to ccTLDs or subdomains. For subdirectories, Google relies entirely on hreflang and on-page language signals. This is another reason subdirectories are simpler.

---

## 5. User Experience Considerations

### 5.1 Geo-Detection and Auto-Redirect

**Recommendation: Do NOT auto-redirect based on IP geolocation.**

| Factor | Analysis |
|--------|----------|
| **Google's guidance** | Google explicitly discourages IP-based redirects. Googlebot crawls from the US; if you redirect US IPs to English, Google may never discover your German pages. |
| **User annoyance** | A German museum director traveling in Spain gets redirected to Spanish content. VPN users get wrong content. |
| **B2B context** | Museum professionals often research in English regardless of location. Forcing a language based on IP overrides their intent. |
| **Legal considerations** | Some European privacy regulators consider IP-based geolocation as processing personal data without consent. |

**Instead, use these approaches:**

1. **Browser language detection (Accept-Language header):** Use `next-intl` middleware to detect the browser's preferred language and suggest (not force) a language switch. Display a non-intrusive banner: "This page is also available in German. Switch?"

2. **Cookie/preference persistence:** Once a user selects a language, store the preference and respect it on return visits.

3. **ccTLD entry points:** If someone types `aitourpilot.de`, the Cloudflare redirect sends them to `/de`. This is user-initiated geo-selection, not forced.

### 5.2 Language Switcher

**Current approach:** next-intl with `localePrefix: "as-needed"` -- English at `/`, German at `/de`.

**Recommended improvements:**

| Element | Current | Recommended |
|---------|---------|-------------|
| **Switcher UI** | (Not assessed from code) | Dropdown or flag-free toggle in header, showing language names in their own language ("Deutsch", not "German") |
| **URL behavior** | Locale prefix as-needed | Keep this -- it is the industry standard pattern |
| **Flag icons** | Unknown | Do NOT use flags. Flags represent countries, not languages. A Swiss user should not have to click a German flag. Use language names only. |
| **Position** | Unknown | Top-right corner of header, consistent across all pages |
| **Mobile** | Unknown | Accessible from hamburger menu, not hidden |

**Language name display best practice:**

```
EN | Deutsch | Francais | Espanol
```

Each language name is written in that language. This is the standard used by the EU, United Nations, and major international organizations.

### 5.3 URL Structure Users Expect

For a B2B audience (museum professionals), URL expectations vary by market:

| Market | What They Expect | What We Provide (Option D) |
|--------|-----------------|---------------------------|
| Germany/Austria | `.de` domain or `/de/` path | `aitourpilot.de` redirects to `aitourpilot.com/de/` -- acceptable |
| France | `.fr` domain or `/fr/` path | `aitourpilot.fr` redirects to `aitourpilot.com/fr/` -- acceptable |
| Netherlands | `.com` with English content | `aitourpilot.com` -- natural |
| UK | `.com` or `.co.uk` | `aitourpilot.co.uk` redirects to `aitourpilot.com` -- natural |
| Denmark | `.com` with English content | `aitourpilot.com` -- natural |
| Spain | `.com` or `.es` | `aitourpilot.es` redirects to `aitourpilot.com/es/` -- acceptable |

**Key insight:** For B2B, the primary URL discovery path is clicking a link from an email, LinkedIn message, or Google search -- not typing a domain. The URL structure matters less than the content quality and language match.

---

## 6. Marketing Platform Integration

### 6.1 TouriBot Outreach Campaign Support

Based on the Outreach Infrastructure Blueprint and Precision Partner Acquisition Engine, here is how the domain strategy supports each outreach component:

#### Email Campaigns (via hermann@aitourpilot.co)

| Campaign Element | Domain Strategy Support |
|-----------------|----------------------|
| **Email links to main site** | Link to `aitourpilot.com` (English) or `aitourpilot.com/de` (German) based on prospect language |
| **Email signature website** | Use `aitourpilot.com` -- the canonical brand domain |
| **Demo booking link** | Link to `engage.aitourpilot.com/museums` or directly to Google Calendar -- language-neutral |
| **One-pager PDF link** | Host at `aitourpilot.com/resources/[language]/one-pager.pdf` or use Cloudflare R2 |

**Language routing in outreach emails:**

TouriBot's personalization engine (Module 3) determines the prospect's language. The email templates should include language-appropriate links:

```
German prospect: "Besuchen Sie aitourpilot.com/de fuer mehr Informationen"
French prospect: "Visitez aitourpilot.com/fr pour en savoir plus"
English prospect: "Visit aitourpilot.com to learn more"
```

Alternatively, for print materials and business cards targeting specific markets, use the ccTLD as a vanity URL:

```
German business card: "aitourpilot.de" (redirects to .com/de)
French business card: "aitourpilot.fr" (redirects to .com/fr)
```

#### Personalized Museum Landing Pages

The Precision Partner Acquisition Engine envisions personalized landing pages per museum prospect. These should live under the engage subdomain:

```
engage.aitourpilot.com/museums/rijksmuseum
engage.aitourpilot.com/museums/moesgaard
engage.aitourpilot.com/museums/la-pedrera
```

**Why engage subdomain, not main site:**
- Keeps the main site clean for organic SEO
- Campaign pages can be noindexed without affecting main site
- Separate analytics tracking for conversion attribution
- Can be spun up/down without affecting main site deployments

### 6.2 Partner Acquisition Engine Integration

| Engine Module | Domain/URL Touchpoint | Implementation |
|--------------|----------------------|----------------|
| **Module 1: ICP Definition** | No URL touchpoint | Internal tool |
| **Module 2: Lead Research** | Prospect visits `aitourpilot.com` to verify company | Main site must look professional in all target languages |
| **Module 3: Personalization** | Links in email point to relevant language | TouriBot generates language-tagged URLs |
| **Module 4: Message Sequences** | Email CTAs link to demo booking or landing pages | `engage.aitourpilot.com/museums` for campaign; `aitourpilot.com` for credibility |
| **Module 5: Automation** | Instantly.ai click tracking | All tracked links should use consistent UTM parameters |
| **Module 6: Response Handling** | Follow-up links match original language | Maintain language consistency through the entire funnel |

### 6.3 UTM and Tracking Strategy

With a single domain, tracking is straightforward:

```
Source: email      -> utm_source=email&utm_medium=outreach&utm_campaign=spring2026
Source: LinkedIn   -> utm_source=linkedin&utm_medium=organic&utm_campaign=spring2026
Source: LinkedIn ad -> utm_source=linkedin&utm_medium=paid&utm_campaign=awareness_q2
```

All traffic lands on `aitourpilot.com` (with language path), keeping analytics consolidated in one GA4 property. No cross-domain tracking needed.

### 6.4 The engage.aitourpilot.com Question

The engage subdomain is currently a separate Vercel project. Two strategic options:

| Option | Description | Recommendation |
|--------|-------------|---------------|
| **Keep separate** | engage stays as its own project with campaign-specific pages | Recommended for now -- clean separation of concerns |
| **Merge into main** | Campaign pages become routes on the main site (e.g., `/campaigns/museums`) | Consider later if the separation creates content management overhead |

If keeping separate, ensure `engage.aitourpilot.com` also supports the same languages as the main site, at least for the primary campaign pages (`/museums`).

---

## 7. Final Recommendation

### The Strategy: Option D -- Hybrid (Subdirectories + Smart ccTLD Redirects)

**One sentence summary:** Serve all content from `aitourpilot.com` with locale subdirectories (`/de`, `/fr`, `/es`, `/dk`, `/nl`), and configure all ccTLD domains to redirect to their corresponding language version.

### What to Do with Each Domain

| Domain | Action | Cloudflare Page Rule | Notes |
|--------|--------|---------------------|-------|
| **aitourpilot.com** | Primary website | N/A -- Vercel serves content | Canonical domain for all SEO |
| **aitourpilot.co** | Outreach email only | `aitourpilot.co/*` -> 301 -> `https://www.aitourpilot.com/$1` | Keep isolated for email reputation |
| **aitourpilot.de** | Redirect to German content | `aitourpilot.de/*` -> 301 -> `https://www.aitourpilot.com/de/$1` | Use as vanity URL on German materials |
| **aitourpilot.at** | Redirect to German content | `aitourpilot.at/*` -> 301 -> `https://www.aitourpilot.com/de/$1` | Austrian market shares German content |
| **aitourpilot.ch** | Redirect to German content | `aitourpilot.ch/*` -> 301 -> `https://www.aitourpilot.com/de/$1` | Swiss market; could later redirect to `/de-CH` if needed |
| **aitourpilot.fr** | Redirect to French content | `aitourpilot.fr/*` -> 301 -> `https://www.aitourpilot.com/fr/$1` | Available when French content launches |
| **aitourpilot.es** | Redirect to Spanish content | `aitourpilot.es/*` -> 301 -> `https://www.aitourpilot.com/es/$1` | Available when Spanish content launches |
| **aitourpilot.nl** | Redirect to Dutch or English | `aitourpilot.nl/*` -> 301 -> `https://www.aitourpilot.com/$1` | English until Dutch content exists |
| **aitourpilot.dk** | Redirect to English | `aitourpilot.dk/*` -> 301 -> `https://www.aitourpilot.com/$1` | English until Danish content exists |
| **aitourpilot.co.uk** | Redirect to English | `aitourpilot.co.uk/*` -> 301 -> `https://www.aitourpilot.com/$1` | UK market, English content |
| **aitourpilot.eu** | Redirect to English | `aitourpilot.eu/*` -> 301 -> `https://www.aitourpilot.com/$1` | Pan-European, defaults to English |
| **aitourpilot.org** | Redirect to English | `aitourpilot.org/*` -> 301 -> `https://www.aitourpilot.com/$1` | Defensive only |

### Why This is the Right Choice for AITourPilot Specifically

1. **Pre-revenue startup reality.** You are building domain authority from scratch. Splitting it across 8+ domains would mean 8+ domains with near-zero authority competing against established competitors. A single domain accumulates authority faster.

2. **B2B sales cycle.** Your prospects discover you through personalized email outreach, LinkedIn, and conference meetings -- not through organic Google search for "museum audio guide" (where competitors like Smartify dominate). URL structure is secondary to content quality and personalization.

3. **50-150 contacts, not 50,000.** At this volume, micro-optimization of local SEO signals has negligible ROI. One well-optimized page in German on `.com/de` will serve the DACH market just as effectively as a `.de` domain.

4. **Speed of execution.** The Precision Partner Acquisition Engine runs on a 60-day timeline. Every hour spent managing multi-domain infrastructure is an hour not spent on outreach. Option D requires zero additional infrastructure work.

5. **The ccTLDs still provide value.** They serve as vanity URLs for offline materials, prevent competitor squatting, and provide a local-feeling entry point that redirects to the right language. This is practical value without engineering cost.

6. **Easy to escalate later.** If AITourPilot grows to 50+ museum partnerships and SEO becomes a primary acquisition channel, migrating from subdirectories to ccTLDs is a well-documented process. Going the other direction (consolidating fragmented ccTLDs) is much harder.

---

## 8. Implementation Plan

### Phase 1: Foundation (Week 1 -- April 2026)

**Goal:** Correct i18n foundation for current EN + DE site.

| Task | Effort | Owner |
|------|--------|-------|
| Add `next-intl` middleware for Accept-Language detection and language suggestion banner | 2-3h | Dev |
| Implement hreflang `<link>` tags in root layout (EN + DE) | 1-2h | Dev |
| Rewrite `sitemap.ts` to be dynamic with hreflang annotations per URL | 2h | Dev |
| Add canonical URL meta tags to all pages | 1h | Dev |
| Update `robots.ts` to disallow `/_next/` | 15min | Dev |
| Verify Google Search Console property and submit new sitemap | 30min | Dev |
| Configure Cloudflare 301 redirects for all ccTLDs (point to current EN or DE) | 1-2h | DevOps |
| **Total** | **~8-10h** | |

**Deliverables:**
- hreflang on all pages
- Dynamic sitemap with language alternates
- All ccTLDs redirecting to correct language versions
- GSC verified and sitemap submitted

### Phase 2: French + Spanish Expansion (Q3 2026)

**Goal:** Add French and Spanish content for Module 4 outreach to FR and ES markets.

| Task | Effort | Owner |
|------|--------|-------|
| Add `fr` and `es` to `locales` array in `config.ts` | 15min | Dev |
| Create `messages/fr.json` and `messages/es.json` translation files | 4-8h | Translation |
| Translate key pages: homepage, museum partner page, privacy policy | 8-16h | Translation |
| Update hreflang tags to include `fr` and `es` | 30min | Dev |
| Update sitemap to include `/fr/` and `/es/` pages | 30min | Dev |
| Update Cloudflare redirects: `.fr` -> `/fr/`, `.es` -> `/es/` | 30min | DevOps |
| Test all language versions end-to-end | 2h | QA |
| **Total** | **~16-28h** (mostly translation) | |

### Phase 3: Dutch + Danish (Q4 2026+)

**Goal:** Native-language experience for NL and DK markets.

Same pattern as Phase 2. Only pursue if:
- There are active museum negotiations in NL or DK requiring native-language presence
- Organic traffic from these markets warrants localized content
- Translation resources are available

### Phase 4: SEO Maturity (2027+)

**Goal:** Advanced SEO for organic acquisition.

| Task | Description |
|------|-------------|
| Structured data (JSON-LD) | Add Organization, WebSite, and Service schema markup in each language |
| Blog / case studies | Language-specific content marketing (e.g., `aitourpilot.com/de/blog/rijksmuseum-fallstudie`) |
| Link building | Regional PR and museum industry backlinks pointing to language-specific pages |
| Evaluate ccTLD migration | If organic search becomes a primary channel and local rankings are insufficient, revisit Option C |

### Estimated Costs

| Phase | Development | Translation | Infrastructure |
|-------|------------|-------------|---------------|
| Phase 1 | EUR 0 (internal) | EUR 0 | EUR 0 |
| Phase 2 | EUR 0 (internal) | EUR 400-800 (professional translation of ~5,000 words x 2 languages) | EUR 0 |
| Phase 3 | EUR 0 (internal) | EUR 400-800 (2 more languages) | EUR 0 |
| Phase 4 | EUR 0 (internal) | Ongoing content | EUR 0-240/yr (Vercel Pro if needed) |

**Note on translation costs:** For B2B marketing copy targeting museum professionals, machine translation is NOT acceptable. The language must be polished, industry-specific, and culturally appropriate. Budget for professional translation or native-speaker review.

---

## 9. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Competitor registers similar ccTLD** | Low (you own all key TLDs) | Medium | Already mitigated by owning the portfolio |
| **Google fails to discover language versions** | Low | High | hreflang + sitemap + GSC monitoring catches this early |
| **Translation quality issues** | Medium | High | Use professional translators with museum industry context; have native speakers review |
| **ccTLD redirect chains** | Low | Medium | Keep redirects simple (single 301, no chains); test quarterly |
| **Vercel Hobby tier limits exceeded** | Low (for B2B traffic) | Low | Upgrade to Pro when needed (simple, instant) |
| **User expects `.de` to stay in URL bar** | Medium | Low | Minimal impact on B2B users; most arrive via direct links not typed URLs |
| **Future need to migrate to ccTLDs** | Low (2+ years) | High | Subdirectory structure makes migration possible; plan redirect map in advance |
| **hreflang implementation errors** | Medium | Medium | Use Google's hreflang testing tool; monitor GSC International Targeting report monthly |

---

## Appendix A: Technical Implementation Notes for next-intl

### Adding Locales

In `src/i18n/config.ts`, expand the locales array:

```typescript
// Phase 1 (current)
export const locales = ["en", "de"] as const;

// Phase 2
export const locales = ["en", "de", "fr", "es"] as const;

// Phase 3
export const locales = ["en", "de", "fr", "es", "nl", "da"] as const;
```

### hreflang in Layout

In the root layout or via `generateMetadata`, add alternateLinks:

```typescript
// In layout.tsx or page.tsx generateMetadata
export function generateMetadata({ params }: Props): Metadata {
  return {
    alternates: {
      canonical: `https://www.aitourpilot.com/${params.locale === 'en' ? '' : params.locale + '/'}`,
      languages: {
        'en': 'https://www.aitourpilot.com/',
        'de': 'https://www.aitourpilot.com/de/',
        'x-default': 'https://www.aitourpilot.com/',
      },
    },
  };
}
```

### Dynamic Sitemap with hreflang

Next.js 14+ supports hreflang in sitemaps via the `alternates` field:

```typescript
export default function sitemap(): MetadataRoute.Sitemap {
  const pages = ['', '/privacy-policy'];
  const locales = ['en', 'de'];
  const baseUrl = 'https://www.aitourpilot.com';

  return pages.flatMap((page) =>
    locales.map((locale) => ({
      url: `${baseUrl}${locale === 'en' ? '' : '/' + locale}${page}`,
      lastModified: new Date(),
      alternates: {
        languages: Object.fromEntries(
          locales.map((l) => [
            l,
            `${baseUrl}${l === 'en' ? '' : '/' + l}${page}`,
          ])
        ),
      },
    }))
  );
}
```

---

## Appendix B: Cloudflare Page Rule Templates

For each ccTLD, create one page rule in Cloudflare:

```
Domain: aitourpilot.de
Rule: aitourpilot.de/*
Setting: Forwarding URL (301 Permanent Redirect)
Destination: https://www.aitourpilot.com/de/$1

Domain: aitourpilot.at
Rule: aitourpilot.at/*
Setting: Forwarding URL (301 Permanent Redirect)
Destination: https://www.aitourpilot.com/de/$1

Domain: aitourpilot.ch
Rule: aitourpilot.ch/*
Setting: Forwarding URL (301 Permanent Redirect)
Destination: https://www.aitourpilot.com/de/$1

Domain: aitourpilot.fr
Rule: aitourpilot.fr/*
Setting: Forwarding URL (301 Permanent Redirect)
Destination: https://www.aitourpilot.com/fr/$1

Domain: aitourpilot.es
Rule: aitourpilot.es/*
Setting: Forwarding URL (301 Permanent Redirect)
Destination: https://www.aitourpilot.com/es/$1

Domain: aitourpilot.nl
Rule: aitourpilot.nl/*
Setting: Forwarding URL (301 Permanent Redirect)
Destination: https://www.aitourpilot.com/$1
(English until Dutch content exists)

Domain: aitourpilot.dk
Rule: aitourpilot.dk/*
Setting: Forwarding URL (301 Permanent Redirect)
Destination: https://www.aitourpilot.com/$1
(English until Danish content exists)

Domain: aitourpilot.co.uk
Rule: aitourpilot.co.uk/*
Setting: Forwarding URL (301 Permanent Redirect)
Destination: https://www.aitourpilot.com/$1

Domain: aitourpilot.eu
Rule: aitourpilot.eu/*
Setting: Forwarding URL (301 Permanent Redirect)
Destination: https://www.aitourpilot.com/$1

Domain: aitourpilot.org
Rule: aitourpilot.org/*
Setting: Forwarding URL (301 Permanent Redirect)
Destination: https://www.aitourpilot.com/$1
```

Note: Each domain in Cloudflare gets 3 free page rules. One rule per domain is sufficient for this setup.

---

## Appendix C: Comparison with Competitor Approaches

| Company | Domain Strategy | Revenue Stage | Why It Works for Them |
|---------|----------------|---------------|----------------------|
| **Smartify** | smartify.org (single domain, English) | Series A, 700+ museums | Single product language; museums integrate the SDK |
| **izi.TRAVEL** | izi.travel (single domain, 40+ languages via subdirs) | Established, 25K+ tours | User-generated content; subdirectories per language |
| **Cuseum** | cuseum.com (single domain, English) | Funded, US-focused | English-only market |
| **GetYourGuide** | getyourguide.com + ccTLDs (getyourguide.de, .fr, etc.) | Public company, $2B+ | Consumer marketplace with massive organic traffic; justifies multi-domain SEO investment |
| **Musement** | musement.com (single domain, subdirs) | Acquired by TUI | B2C marketplace; subdirectories for 8 languages |

**Pattern:** B2B SaaS companies in the museum/culture space use single-domain strategies. Only large B2C marketplaces (GetYourGuide) with millions of organic visits invest in ccTLD strategies.

AITourPilot is B2B at the current stage. The subdirectory approach is the industry standard for this phase.

---

## Summary Decision Table

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Domain strategy | **Option D: Hybrid** | Consolidated authority + ccTLD marketing utility |
| Primary domain | **aitourpilot.com** | Canonical domain for all content and SEO |
| Locale structure | **Subdirectories** (`/de`, `/fr`, `/es`) | Industry standard, simplest to maintain |
| ccTLD purpose | **301 redirects to language versions** | Marketing vanity URLs, defensive registration |
| Vercel projects | **2** (main + engage) | Minimal cost, maximum simplicity |
| hreflang | **HTML link tags + sitemap annotations** | Belt-and-suspenders approach for Google |
| Geo-detection | **No auto-redirect; language suggestion banner** | Google-safe, user-respecting |
| GSC | **1 property** (domain-level) | Single source of truth for search performance |
| Phase 1 languages | **EN + DE** (current) | Already built; serves primary DACH + UK + NL + DK markets |
| Phase 2 languages | **+ FR + ES** (Q3 2026) | Unlocks France and Spain outreach with native content |
| Estimated cost | **EUR 0 incremental infrastructure** | All within existing free tier; translation is the only cost |
