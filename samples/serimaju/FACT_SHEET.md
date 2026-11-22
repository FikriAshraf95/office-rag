# Serimaju Technologies Sdn Bhd: Fact Sheet (answer key source)

> **Entirely fictional.** Company, people, clients, emails and figures are invented for testing a RAG system.
> This file is the ground truth the documents were generated from. **Do not ingest this file** into the RAG system (it would make every question trivially answerable). Use it to check answers.

## Company
- Serimaju Technologies Sdn Bhd: tech startup (software delivery, data platforms, cloud), Kuala Lumpur (Level 18, Menara Fiktif, Jalan Contoh, 50450 KL). ~180 staff. Founded 12 June 2019 (Foundation Day = company holiday).
- Email domain: `serimaju.example`.

## Leadership (Org Chart 2026)
- CEO: **Aisyah Rahman**
- CTO: **Daniel Lim** (reports to CEO). Under CTO: Head of Engineering **Farid Ismail**; Head of Security **Jason Wong**.
- COO: **Priya Nair** (reports to CEO). Under COO: Head of HR **Tan Mei Ling**; Client Delivery Director **Nurul Huda**.
- CFO: **Hafiz Osman** (reports to CEO). Under CFO: Finance Manager **Kumar Selvam** (leads the Finance team).
- Account managers (report to Client Delivery Director Nurul Huda): Bank Teratai, **Sarah Chong**; Pelita Precision, **Arjun Pillai**; Gemilang Capital, **Zainab Yusof**.

## Clients
| Client | Industry | Code | Data residency | Incident SLA to client | Special requirements |
|---|---|---|---|---|---|
| Bank Teratai Berhad | Banking | BTB | Malaysia only | **2 hours** | Background screening before access; escorted access at Menara Teratai; no personal devices in client server rooms |
| Pelita Precision Manufacturing Sdn Bhd | Manufacturing (factory in Senai, Johor) | PPM | No restriction (Malaysia preferred) | 8 hours | Safety induction + PPE (safety boots, hi-vis vest) on factory floor; no USB drives on OT network; site visits booked **3 working days** ahead |
| Gemilang Capital Berhad | Finance / asset management | GCB | Malaysia or Singapore | **4 hours** | Signed NDA per person; trading data = Restricted; quarterly access review; information barrier ("Chinese wall") between GCB team and other client teams |

- Delivery leads: BTB **Farid Ismail**, PPM **Lee Wei Jie**, GCB **Siti Aminah**.
- Contracts: BTB 2024-03-01 → 2027-02-28; PPM 2025-07-01 → 2027-06-30; GCB 2025-01-15 → **2026-12-31**.
- BTB screening takes ~10 working days. BTB visitor passes are arranged 1 working day ahead. BTB systems cannot be accessed from abroad, even with approved remote work abroad.
- Staff counts on org chart: Engineering ~120, Finance team 6.

## Active projects (Client_Accounts_Q4_2026.xlsx)
| Code | Client | Project | Status | Team | Go-live |
|---|---|---|---|---|---|
| BTB-0142 | BTB | Core banking API gateway modernisation | In progress | 9 | 2027-01-18 |
| BTB-0157 | BTB | Fraud analytics data pipeline | In progress | 6 | 2027-03-31 |
| PPM-0031 | PPM | Factory IoT telemetry platform (Senai plant) | In progress | 7 | 2026-12-14 |
| PPM-0034 | PPM | Predictive maintenance dashboard | Planning | 3 | 2027-05-04 |
| GCB-0019 | GCB | Portfolio reporting portal | UAT | 5 | 2026-12-07 |
Totals: 30 people overall; BTB 15.

## HR policy: HR Handbook 2026 (effective 1 Jan 2026), with memo overrides
- Working hours 9:00–18:00 Mon–Fri; flexible core hours **10:00–16:00**. Hybrid: **minimum 3 office days per week (Tue, Wed, Thu)**.
- Probation **3 months**. Notice period: E grades 1 month, S grades 1 month, M grades **2 months**, D **3 months**.
- Annual leave (days/year) by grade and completed service (detail in XLSX):

| Grade | < 2 yrs | 2–5 yrs | > 5 yrs |
|---|---|---|---|
| E1–E3 (Executive) | 14 | 16 | 18 |
| S1–S2 (Senior) | 16 | 18 | 20 |
| M1–M3 (Manager) | 18 | 20 | **22** |
| D (Director) | 22 | 24 | 26 |

- **Max consecutive working days per leave application without HOD approval:** Handbook 2026 says **7** → **overridden by memo of 15 Sep 2026: 10, effective 1 Oct 2026.** (Old Handbook 2024 said 5.) Above the limit: HOD + HR approval.
- Leave notice: ≤ 3 days → apply **3 working days** ahead; > 3 days → **14 calendar days** ahead.
- Carry forward: max **5 days**; Handbook says use by **31 March** → **memo: for 2026 balances only, extended to 30 April 2027.** (Handbook 2024: 8 days, by 30 June.)
- Medical leave: 14 / 18 / 22 days (< 2 / 2–5 / > 5 yrs). Hospitalisation 60 days (inclusive of medical leave).
- Maternity 98 days; paternity 7 days; compassionate 3 days (immediate family); marriage 3 days (once).
- Outpatient medical claim cap **RM 1,500/year**; dental **RM 500/year**. (Handbook 2024: RM 1,000 outpatient.)
- Working remotely from abroad: max **20 working days/year**, HOD + HR approval.

### What the superseded Handbook 2024 says differently (trap values)
Core hours 10:00–15:00; 2 office days/week; probation 6 months; M-grade notice 1 month; annual leave 2 days lower per cell (e.g. M >5 yrs = 20); max consecutive 5 days; carry forward 8 days by 30 June; outpatient RM 1,000; dental RM 300; remote work abroad not permitted.

## Travel & Claims SOP (Markdown)
- Submit claims in the **Kakitangan portal** (HRIS) within **30 days**; claims older than **60 days rejected**.
- Mileage **RM 0.70/km**; toll and parking with receipts.
- Meal allowance (overnight outstation): **RM 80/day** domestic; **USD 60/day** overseas.
- Hotel cap: **RM 350/night** in KL, Penang, Johor Bahru; **RM 250/night** elsewhere in Malaysia; **USD 180/night** overseas.
- Flights economy; **business class allowed for flights over 6 hours for M grades and above**.
- Client-billable expenses tagged with client project code prefix (BTB-, PPM-, GCB-).
- Claims over **RM 2,000** need HOD + Finance approval.

## IT Security Policy v3 (DOCX, effective 1 Mar 2026)
- Passwords min **14 characters**; MFA mandatory; company password manager **Bitwarden**.
- Full-disk encryption; screen lock after **5 minutes**.
- Data classification: Public, Internal, Confidential, **Restricted** (client production data, credentials, personal data, client trading data).
- Restricted data: never in personal email/cloud; never in unapproved AI tools. Approved AI tools: company Claude workspace, company GitHub Copilot org.
- Incident reporting: email **security@serimaju.example** within **1 hour**, IT on-call ext **2222**.
- USB mass storage disabled by default (exception via IT ticket).
- Access reviews quarterly; offboarding access revoked within **24 hours**.

## Year-end office closure notice (bilingual PDF, Malay + English)
- Office closed **24 Dec 2026 – 1 Jan 2027**.
- **24, 29, 30 Dec 2026** = company-granted days (no leave deducted). **25 Dec** and **1 Jan** = public holidays. **28 and 31 Dec** = staff must apply annual leave (or arrange work with HOD).
- Support on-call for Bank Teratai and Gemilang continues (rota by Client Delivery).
- Foundation Day **12 June** = company holiday each year.

## Deliberately absent (system should say "not found")
- Stock options / ESOS, pet policy, parking allowance for office, gym membership.
