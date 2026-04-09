# 20260323-domain-operations-guide

*Source: Business Wiki / technical/20260323-domain-operations-guide.html*

## Overview

This is a step-by-step operations guide for managing AITourPilot's domain portfolio. Use this document when registering new domains, configuring DNS, or troubleshooting issues.

### Current Domain Portfolio (as of March 2026)

| Domain | Registrar | DNS Provider | Cloudflare Status | Purpose |
|--------|-----------|-------------|-------------------|---------|
| aitourpilot.com | Edis.at (transferring to Cloudflare) | Edis.at | Not yet onboarded | Main website + Zoho email |
| **aitourpilot.co** | **Cloudflare** | Cloudflare | Active | Outreach email (Google Workspace) |
| aitourpilot.org | INWX | Cloudflare | Active | Defensive |
| aitourpilot.eu | INWX | Cloudflare | Active | Defensive / European |
| aitourpilot.de | INWX | Cloudflare | Active | Defensive / DACH |
| aitourpilot.fr | INWX | Cloudflare | Active | Defensive / France |
| aitourpilot.nl | INWX | Cloudflare | Active | Defensive / Netherlands |
| aitourpilot.es | INWX | Cloudflare | Active | Defensive / Spain |
| aitourpilot.at | INWX | Cloudflare | Active | Defensive / Austria |
| aitourpilot.ch | INWX | Cloudflare | Active | Defensive / Switzerland |
| aitourpilot.co.uk | INWX | Cloudflare | Active | Defensive / UK |
| aitourpilot.dk | INWX | **INWX** (not Cloudflare) | N/A -- managed at INWX | Defensive / Denmark |

### Account Credentials

| Service | Account | Used For |
|---------|---------|----------|
| **Cloudflare** | hermann@kudlich.at | DNS management for all domains; registrar for .co |
| **INWX** | hermann@kudlich.at | Registrar for all European ccTLDs |
| **Edis.at** | Customer #13445 | Current registrar for aitourpilot.com (pending transfer) |

### Registrant Information

All domains registered under:
- **Name:** Hermann Kudlich
- **Organization:** AITourPilot ApS
- **Email:** contact@aitourpilot.com
- **Danish CVR:** DK46307836

---

## Procedure: Register a New Domain at INWX

Use this when adding a new country domain (e.g., aitourpilot.se, aitourpilot.no, aitourpilot.pl).

### Step 1: Search and Add to Cart

1. Log in to **inwx.de**
2. Go to **Domain** > **Domainsuche** (Domain Search)
3. Search for `aitourpilot.XX` (replace XX with the TLD)
4. Click **Registrierung** (Registration) to add to cart
5. Select **12 Monate** (12 months)

### Step 2: Configure Domain Owner

For each domain in the cart:

1. Click **"Click to complete"** or **"Edit"**
2. Go to the **Domain owner** tab
3. Verify registrant info matches: Hermann Kudlich / AITourPilot ApS / contact@aitourpilot.com

### Step 3: Handle TLD-Specific Requirements

Some TLDs require additional data:

| TLD | Extra Requirement | What to Enter |
|-----|-------------------|---------------|
| **.dk** | VAT number | `DK46307836` (Danish CVR) |
| **.dk** | Accept registrar management | Check the box (allows INWX to manage at DK Hostmaster) |
| **.dk** | Accept Punktum dk terms | Check the box |
| **.es** | Registrant ID (NIF/NIE/VAT/Passport) | `DK46307836` (Danish CVR) or Austrian passport number |
| **.es** | Admin ID | Same as Registrant ID |
| **.at** | No extra requirements | -- |
| **.ch** | No extra requirements | -- |
| **.fr** | No extra requirements | -- |
| **.de** | No extra requirements | -- |
| **.eu** | No extra requirements | -- |
| **.nl** | No extra requirements | -- |
| **.co.uk** | No extra requirements | -- |
| **.org** | No extra requirements | -- |

### Step 4: Skip Upsells

- **Trust Provider DV SSL (EUR 19/year):** Skip. Cloudflare provides free SSL for all domains using its DNS.

### Step 5: Complete Purchase

Click **Nachster Schritt** (Next Step) > confirm > pay.

---

## Procedure: Add Domain to Cloudflare DNS

After registering a domain at INWX, you must add it to Cloudflare for DNS management.

### Step 1: Onboard Domain in Cloudflare

1. Log in to **Cloudflare** (hermann@kudlich.at)
2. Click **"Onboard domain"** (top right) or **"Add a site"**
3. Enter the bare domain name (e.g., `aitourpilot.se`) -- no http://, no www, no trailing slash
4. Select **"Import DNS records automatically"** (recommended)
5. Under "Block AI training bots" select **"Do not block (allow crawlers)"**
6. Turn **off** the "Instruct AI bot traffic with robots.txt" toggle
7. Click **Continue**
8. Select the **Free** plan

### Step 2: Review DNS Records

Cloudflare will scan for existing DNS records. For new domains, it typically finds INWX parking records:

- **Delete all A records** pointing to INWX IP addresses (e.g., `185.181.104.242`)
- The domain should have **zero DNS records** at this point
- Click **"Continue to activation"**

### Step 3: Note the Assigned Nameservers

Cloudflare will show two nameservers, for example:
```
elliot.ns.cloudflare.com
etta.ns.cloudflare.com
```

> **IMPORTANT:** Cloudflare may assign DIFFERENT nameservers for different domains. Always check what Cloudflare shows for the specific domain you are onboarding. Do not assume all domains use the same pair.

**Known assignments for AITourPilot domains:**

| Domains | Nameserver 1 | Nameserver 2 |
|---------|-------------|-------------|
| Most domains (.at, .ch, .de, .eu, .fr, .nl, .org, .es) | `elliot.ns.cloudflare.com` | `etta.ns.cloudflare.com` |
| **.co.uk** | `alexandra.ns.cloudflare.com` | `kirk.ns.cloudflare.com` |
| **.dk** | **N/A -- managed at INWX, not Cloudflare** | (DK Hostmaster rejects external NS) |

---

## Procedure: Point INWX Nameservers to Cloudflare

This is the critical step that connects INWX-registered domains to Cloudflare DNS.

### Step 1: Open INWX Forwarding

1. Log in to **inwx.de**
2. Go to **Domain** overview
3. Click the **gear icon** next to the domain
4. Select **"External Nameservers"** from the dropdown menu

### Step 2: Switch to External Nameservers

1. You will see a dialog with tabs: **Web | Mail | Hosting | Nameserver**
2. Make sure you're on the **Nameserver** tab
3. Click **"External nameserver"** (right side -- it may show "INWX nameserver" as currently selected on the left)

### Step 3: Enter Cloudflare Nameservers

1. In **Nameserver 1**: enter the first Cloudflare nameserver (e.g., `elliot.ns.cloudflare.com`)
2. In **Nameserver 2**: enter the second Cloudflare nameserver (e.g., `etta.ns.cloudflare.com`)
3. **Nameserver 3, 4, 5:** Leave empty. The grey placeholder text (`ns3.your domain.de` etc.) is just placeholder -- it is NOT submitted. Do not try to delete it; it cannot be removed and does not affect anything.
4. Click **Save**

### Step 4: Confirm in Cloudflare

1. Go back to Cloudflare
2. Click **"I updated my nameservers"** (or "Check nameservers" if already past the setup wizard)
3. Wait for propagation -- typically 5 minutes to a few hours
4. The domain status in Cloudflare will change from "Pending" to **"Active"**

### Propagation Times Observed

| TLD | Time to Active |
|-----|---------------|
| .at, .ch, .de, .eu, .fr, .nl, .org, .es | Minutes to a few hours |
| .co.uk | Up to 72 hours (Nominet registry is slower; also check that Cloudflare assigned different nameservers) |
| .dk | **Not possible** -- DK Hostmaster rejects Cloudflare nameservers. Use INWX DNS directly (see Troubleshooting). |

---

## Procedure: Set Up 301 Redirects

All defensive domains should redirect to `aitourpilot.com`. This is done via Cloudflare Redirect Rules (free, unlimited).

### For Each Domain in Cloudflare

1. Click on the domain in the Cloudflare dashboard
2. Go to **Rules** > **Redirect Rules** (or legacy: **Page Rules**)
3. Create a new rule:

**Using Redirect Rules (newer, recommended):**
- **When:** Hostname equals `aitourpilot.XX` (the domain)
- **Then:** Dynamic redirect
- **URL:** `https://aitourpilot.com`
- **Status code:** 301 (permanent)
- **Preserve query string:** Yes
- **Preserve path:** Yes (so `aitourpilot.de/something` redirects to `aitourpilot.com/something`)

**Using Page Rules (legacy, also works):**
- **URL pattern:** `*aitourpilot.XX/*`
- **Setting:** Forwarding URL -- 301 Permanent Redirect
- **Destination:** `https://aitourpilot.com/$1`

> **Note:** For redirect rules to work, Cloudflare needs a DNS record to "activate" the domain's HTTP handling. Add a dummy A record: Type A, Name `@`, Content `192.0.2.1`, Proxy status: **Proxied** (orange cloud). This is a standard placeholder -- the redirect fires before any traffic reaches this IP.

Also add for www:
- Type A, Name `www`, Content `192.0.2.1`, Proxy status: **Proxied**

### Redirect for aitourpilot.co (Special Case)

The .co domain also redirects web traffic to .com, but it has **MX records for Google Workspace email**. The redirect only affects HTTP/HTTPS traffic -- email routing (MX records) is completely independent and unaffected.

---

## Troubleshooting

### "Invalid nameservers" on Cloudflare (persists for days)

**Cause:** Usually a mismatch between nameservers entered in INWX and what Cloudflare expects.

**Fix:**
1. In Cloudflare, click on the affected domain
2. Go to **DNS** > **Overview** or look for the activation page
3. Check the **exact** nameservers Cloudflare expects -- they may differ from other domains
4. Go to INWX and verify the nameservers match **exactly**
5. Save in INWX, then in Cloudflare click **"Check nameservers"**

**Known case -- .co.uk (RESOLVED):**
Cloudflare assigned `alexandra.ns.cloudflare.com` and `kirk.ns.cloudflare.com` for aitourpilot.co.uk, but the original setup used `elliot` and `etta` (which were correct for the other domains). After correcting to `alexandra` and `kirk`, it took ~72 hours for Nominet (UK registry) to propagate. Now Active.

### .dk -- Cannot Use Cloudflare DNS (DK Hostmaster Limitation)

**Problem:** DK Hostmaster (Punktum dk) rejected the external nameserver change with error "No NS info on host." This is a known .dk registry limitation -- DK Hostmaster requires external nameservers to be pre-registered in their system before they can be assigned to a domain. Cloudflare nameservers are not pre-registered at DK Hostmaster, and INWX cannot force this.

**Resolution:** Manage .dk DNS directly at INWX instead of Cloudflare. Since .dk is a purely defensive redirect domain, this is the pragmatic choice.

**How to set up the .dk redirect at INWX:**

1. In INWX, go to the gear icon for aitourpilot.dk
2. Select **"Forwarding"** (or click the gear > choose from the dropdown)
3. Switch nameservers back to **INWX nameservers** (if they were changed to external)
4. Go to the **"Web"** tab
5. Set:
   - **URL:** `https://aitourpilot.com`
   - **Redirect type:** Header-Redirect (301)
   - **Append path to URL:** Checked (so `aitourpilot.dk/about` redirects to `aitourpilot.com/about`)
6. Click **Save**

> **Important for future .dk domains:** Do NOT attempt to use Cloudflare DNS for .dk domains. Manage them directly at INWX. This is a DK Hostmaster registry limitation, not an INWX or Cloudflare issue.

### .es stuck on "REG INITIATED"

The Spanish registry (Red.es) validates the identification number. EU VAT numbers are accepted. Check email for any verification requirements from Red.es.

### INWX placeholder text in nameserver fields

The grey text `ns3.your domain.de`, `ns4.your domain.de`, `ns5.your domain.de` in INWX nameserver fields 3-5 is **placeholder text only**. It is NOT submitted as actual nameserver values. It cannot be deleted. It does not affect the configuration. Only Nameserver 1 and 2 values matter.

### Cloudflare shows "Moved" status

If a domain is removed from Cloudflare and re-added, it may show "Moved." Delete the domain from Cloudflare and re-add it fresh using the onboarding procedure above.

---

## Procedure: Transfer aitourpilot.com from Edis.at to Cloudflare

This is planned for before May 24, 2026 (Edis renewal date).

### Pre-Transfer Checklist

Before initiating, document **all** current DNS records at Edis.at:

| Record Type | Name | Value | Purpose |
|-------------|------|-------|---------|
| MX | @ | (Zoho MX servers) | Zoho email |
| TXT | @ | v=spf1 include:zoho... | SPF for Zoho |
| TXT | zmail._domainkey | (Zoho DKIM key) | DKIM for Zoho |
| TXT | _dmarc | (DMARC policy) | DMARC |
| CNAME or A | @ | (Squarespace IP/CNAME) | Website |
| CNAME | www | (Squarespace) | Website |
| TXT | @ | (Squarespace verification) | Domain verification |

### Transfer Steps

1. **At Cloudflare:** Add `aitourpilot.com` as a site (free plan). Recreate ALL DNS records from the list above.
2. **At Edis.at:** Go to Domain > Domaininhaber, ensure WHOIS contact email is accessible
3. **At Edis.at:** Disable domain lock (Verriegelung: change "ja" to "nein")
4. **At Edis.at:** Request the EPP/Auth-Code (Transfer-Code / Autorisierungscode)
5. **At Cloudflare:** Go to Domain Registration > Transfer Domain > enter `aitourpilot.com` > paste auth code > pay (~EUR 10-12)
6. **Approve:** Edis will send a confirmation email to the WHOIS contact. Approve it to speed things up (otherwise auto-completes in 5 days).
7. **Verify:** Once complete, check that Zoho email and Squarespace website still work.

> Cloudflare automatically extends registration by 1 year from current expiry. Transferring before May 24 means .com is paid through ~May 2027.

---

## Reference: TLD Registry Requirements

| TLD | Registry | Country ID Required | WHOIS Privacy | Notes |
|-----|----------|-------------------|---------------|-------|
| .com | Verisign | No | Cloudflare redacts | -- |
| .co | CO Internet SAS | No | Cloudflare redacts | -- |
| .org | PIR | No | Cloudflare redacts | -- |
| .eu | EURid | No | GDPR redacted | Must have EU connection (company or residency) |
| .de | DENIC | No | Partially redacted | -- |
| .fr | AFNIC | No | Redacted for individuals | -- |
| .nl | SIDN | No | GDPR redacted | -- |
| .co.uk | Nominet | No | Opt-out available | Slower propagation for NS changes |
| .es | Red.es | **Yes** (NIF/NIE/VAT/Passport) | Not redacted | Spanish registry requires ID for all registrants |
| .at | nic.at | No | GDPR redacted | Not available at Cloudflare -- use INWX |
| .ch | SWITCH | No | Not redacted for orgs | Not available at Cloudflare -- use INWX |
| .dk | DK Hostmaster | **Yes** (CVR for companies) | Published for orgs | Requires user agreement with Punktum dk A/S |

---

## Reference: Cost Summary

### INWX Domains (Annual)

| Domain | Registration | Renewal/yr |
|--------|-------------|-----------|
| aitourpilot.org | EUR 7.20 | EUR 7.20 |
| aitourpilot.eu | EUR 6.00 | EUR 10.00 |
| aitourpilot.de | EUR 6.02 | EUR 6.02 |
| aitourpilot.co.uk | EUR 12.00 | EUR 12.00 |
| aitourpilot.fr | EUR 13.20 | EUR 13.20 |
| aitourpilot.nl | EUR 12.60 | EUR 12.60 |
| aitourpilot.es | EUR 15.02 | EUR 15.02 |
| aitourpilot.at | EUR 15.60 | EUR 15.60 |
| aitourpilot.ch | EUR 16.20 | EUR 16.20 |
| aitourpilot.dk | EUR 30.00 | EUR 30.00 |
| **INWX Total** | **EUR 133.84** | **~EUR 138/yr** |

### Cloudflare Domains (Annual)

| Domain | Registration | Renewal/yr |
|--------|-------------|-----------|
| aitourpilot.co | ~EUR 22 | ~EUR 22 |
| aitourpilot.com (transfer) | ~EUR 10-12 | ~EUR 10-12 |
| **Cloudflare Total** | **~EUR 32-34** | **~EUR 32-34/yr** |

### Grand Total

| | Year 1 | Year 2+ |
|---|---|---|
| All 12 domains | **~EUR 166-168** | **~EUR 170/yr** |

---

*Operations guide for AITourPilot domain infrastructure. Companion to the [Outreach Infrastructure Blueprint](20260318-outreach-infrastructure-blueprint.html).*

*Last updated: March 2026*
