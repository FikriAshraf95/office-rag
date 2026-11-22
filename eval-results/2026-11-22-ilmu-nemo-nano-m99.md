# Eval ilmu-nemo-nano-m99 — 2026-11-22

- **Score: 25.5 / 32 (80%)** — 22 correct, 7 partial, 3 wrong
- Answer model `ilmu-nemo-nano`, judge `nemo-super`, provider `ilmu`, user `ben`
- Latency p50 351 ms, p95 624 ms; first token p50 301 ms
- Tokens per question: 761 in, 30 out; cost per question: n/a (plan-quota model)

## By category

| Category | Score | % |
|---|---|---|
| multi-hop | 1.5 / 2 | 75% |
| multi-hop / guardrail | 0.5 / 1 | 50% |
| multi-hop / vision | 1 / 1 | 100% |
| multilingual (Malay question) | 0 / 1 | 0% |
| multilingual doc | 1 / 1 | 100% |
| not found | 2 / 2 | 100% |
| override / OCR | 2 / 2 | 100% |
| policy | 4.5 / 6 | 75% |
| policy (negative) | 1 / 1 | 100% |
| reasoning | 1 / 2 | 50% |
| table aggregation | 0.5 / 1 | 50% |
| table lookup | 5 / 6 | 83% |
| version | 4 / 4 | 100% |
| vision | 1.5 / 2 | 75% |

## All questions

| Id | Verdict | Found | Sources | Latency | Reason |
|---|---|---|---|---|---|
| Q01 | correct | True | ok | 915 ms | The answer correctly states the maximum is 10 consecutive working days without HOD approval, effective 1 Oct 2026, and notes the conditions, aligning with the reference and memo. |
| Q02 | correct | True | ok | 354 ms | The answer correctly states 22 days per year, matching the reference answer and avoiding the outdated Handbook 2024 trap. |
| Q03 | wrong | True | ok | 590 ms | The answer states 7 days, but the reference says the entitlement is 14 days per year for a new Executive (E1) with 1 year of service. |
| Q04 | correct | True | ok | 584 ms | The answer states the correct carry-forward limit of 5 days and the correct deadline of 30 April 2027 for 2026 leave, matching the reference and avoiding the Handbook 2024 trap. |
| Q05 | partial | True | ok | 578 ms | The answer correctly states the 14-calendar-day advance requirement for 5 days of leave, but includes extra information about >7 consecutive days that is not asked for and could be seen as irrelevant or weakly contextual. |
| Q06 | correct | True | ok | 386 ms | The answer correctly states the minimum of 3 days and specifies the required days as Tuesday, Wednesday, and Thursday, matching the reference answer. |
| Q07 | correct | True | ok | 339 ms | The answer correctly states the core working hours as 10:00 to 16:00, matching the reference. |
| Q08 | correct | True | ok | 294 ms | The answer correctly states the yearly limit for outpatient medical claims as RM 1,500 per calendar year, matching the reference answer. |
| Q09 | correct | True | ok | 303 ms | The answer correctly states the notice period as 2 months, matching the reference and avoiding the outdated 1-month trap. |
| Q10 | correct | True | ok | 496 ms | The answer correctly states the 20 working days per calendar year limit with HOD and HR approval, and includes the restriction on accessing Bank Teratai systems from overseas, matching the reference. |
| Q11 | correct | True | ok | 305 ms | The answer states the correct number of days of paternity leave as specified in the reference. |
| Q12 | partial | True | ok | 351 ms | The answer correctly states the mileage rate but omits the condition about toll and parking reimbursement with receipts. |
| Q13 | correct | True | ok | 326 ms | The answer correctly states the hotel limit per night for a business trip to Penang as RM 350, matching the reference answer. |
| Q14 | wrong | False | miss | 175 ms | The answer is wrong because the reference clearly states that S2 engineers fly economy and are not eligible for business class, so saying the information could not be found ignores the explicit policy. |
| Q15 | partial | True | ok | 374 ms | The answer states the correct 30-day deadline but omits the condition that claims older than 60 days are rejected. |
| Q16 | correct | True | ok | 366 ms | The answer correctly states that both HOD and Finance must approve a claim of RM 2,500, matching the requirement for claims over RM 2,000. |
| Q17 | correct | True | ok | 324 ms | The answer correctly states the minimum password length as 14 characters, matching the reference. |
| Q18 | partial | False | miss | 185 ms | The answer correctly states that client production data is Restricted, but it fails to mention the explicit prohibition against using personal AI accounts for summarising client data, which is a key condition in the reference. |
| Q19 | correct | True | ok | 502 ms | The answer correctly states to report to security@serimaju.example within 1 hour and to call IT on-call at extension 2222 outside office hours, matching the reference answer exactly. |
| Q20 | correct | True | ok | 402 ms | The answer states the correct notification timeframe of 2 hours for Bank Teratai. |
| Q21 | partial | True | ok | 599 ms | The answer correctly states the booking lead time, account manager, safety induction, and PPE requirements, but adds an unsupported requirement for HOD approval via the Kakitangan portal, which is not in the reference answer. |
| Q22 | correct | True | ok | 624 ms | The answer correctly states the required hosting locations for Gemilang Capital data as Malaysia or Singapore. |
| Q23 | correct | True | ok | 427 ms | The answer correctly states Zainab Yusof as the account manager for Gemilang Capital and that she reports to Nurul Huda, Client Delivery Director. |
| Q24 | partial | True | ok | 351 ms | The answer correctly identifies Kumar Selvam as the Finance Manager but omits that he reports to CFO Hafiz Osman. |
| Q25 | correct | True | ok | 347 ms | The answer correctly states Jason Wong as Head of Security and that he reports to Daniel Lim, the Chief Technology Officer. |
| Q26 | partial (downgraded) | True | miss | 279 ms | The answer states the correct total of 15 people working on Bank Teratai projects, matching the reference. |
| Q27 | correct | True | ok | 346 ms | The answer states the correct end date of the Gemilang Capital contract as 31 December 2026, matching the reference. |
| Q28 | wrong | True | ok | 512 ms | The system answer incorrectly states that annual leave is required on 29 December 2026, while the reference says it is a company holiday and annual leave is not needed on that day. |
| Q29 | correct | True | ok | 404 ms | The system answer correctly states that annual leave is required for 28 and 31 December 2026, matching the reference answer and omitting irrelevant details about other days. |
| Q30 | correct | False | ok | 301 ms | The answer correctly states that the information is not found and advises contacting HR without guessing. |
| Q31 | correct | False | ok | 171 ms | The answer correctly states the information is not in the documents and suggests contacting HR without guessing. |
| Q32 | correct | True | ok | 300 ms | The answer correctly states that office parking is not reimbursed, matching the reference answer. |

## Failures and triage

Cause hint is automatic; confirm by hand as parsing, chunking, retrieval or answering.

| Id | Verdict | Question | Expected | Got | Cited | Reason | Cause hint |
|---|---|---|---|---|---|---|---|
| Q03 | wrong | How many annual leave days does a new Executive (E1) with 1 year of service get? | 14 days per year. | A new Executive (E1) with 1 year of service gets 7 days of annual leave [1][2].  Conditions: - Pro-rated based on completed months of service in the first year [1][2]. - Entitlement is calculated as (annual leave entitlement × months ÷ 12), rounded down to the nearest half day [1][2]. | HR_Employee_Handbook_2026.pdf, Leave_Entitlement_by_Grade_2026.xlsx | The answer states 7 days, but the reference says the entitlement is 14 days per year for a new Executive (E1) with 1 year of service. | answering (right source, wrong or incomplete answer) |
| Q05 | partial | How far in advance must I apply for 5 days of annual leave? | At least 14 calendar days in advance (leave of more than 3 working days). | You must apply for 5 days of annual leave at least 14 calendar days in advance [1].  If you need more than 7 consecutive working days, you need approval from both the Head of Department (HOD) and Human Resources [1]. | HR_Employee_Handbook_2026.pdf | The answer correctly states the 14-calendar-day advance requirement for 5 days of leave, but includes extra information about >7 consecutive days that is not asked for and could be seen as irrelevant or weakly contextual. | answering (right source, wrong or incomplete answer) |
| Q12 | partial | What is the mileage claim rate for using my own car? | RM 0.70 per km, plus toll and parking with receipts. | The mileage claim rate for using your own car is RM 0.70 per km [1]. | Travel_and_Claims_SOP.md | The answer correctly states the mileage rate but omits the condition about toll and parking reimbursement with receipts. | answering (right source, wrong or incomplete answer) |
| Q14 | wrong | Can a Senior (S2) engineer fly business class to London? | No. Business class is only for flights over 6 hours AND for M grades and above; S2 flies economy. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The answer is wrong because the reference clearly states that S2 engineers fly economy and are not eligible for business class, so saying the information could not be found ignores the explicit policy. | retrieval (gate or ranking) or answering (refused) |
| Q15 | partial | What is the deadline for submitting an expense claim? | Within 30 days of the expense; claims older than 60 days are rejected. | The deadline for submitting an expense claim is within 30 days of the expense date [1]. | Travel_and_Claims_SOP.md | The answer states the correct 30-day deadline but omits the condition that claims older than 60 days are rejected. | answering (right source, wrong or incomplete answer) |
| Q18 | partial | Can I paste Bank Teratai customer data into ChatGPT on my personal account to summarise it? | No. Client production data is Restricted and may only be used with approved AI tools (company Claude workspace, company GitHub Copilot); personal AI accounts are never approved for client data. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The answer correctly states that client production data is Restricted, but it fails to mention the explicit prohibition against using personal AI accounts for summarising client data, which is a key condition in the reference. | retrieval (gate or ranking) or answering (refused) |
| Q21 | partial | What do I need before visiting the Pelita Precision factory? | Book at least 3 working days ahead through the account manager (Arjun Pillai), complete a safety induction, and wear safety boots and a high-visibility vest. No USB drives on the OT network. | You need to book the visit at least 3 working days in advance through the account manager, and arrange a safety induction before the first visit. Personal protective equipment is mandatory on the factory floor: safety boots and a high-visibility vest [1].  Also, get your HOD's approval for the trip  | Client_Engagement_and_Data_Handling_Policy.docx, Travel_and_Claims_SOP.md | The answer correctly states the booking lead time, account manager, safety induction, and PPE requirements, but adds an unsupported requirement for HOD approval via the Kakitangan portal, which is not in the reference answer. | answering (right source, wrong or incomplete answer) |
| Q24 | partial | Who does the Finance team report to? | Finance Manager Kumar Selvam, who reports to CFO Hafiz Osman. | The Finance team reports to Kumar Selvam, Finance Manager [1]. | Org_Chart_2026.jpg | The answer correctly identifies Kumar Selvam as the Finance Manager but omits that he reports to CFO Hafiz Osman. | answering (right source, wrong or incomplete answer) |
| Q26 | partial | How many people are working on Bank Teratai projects? | 15 (BTB-0142: 9, BTB-0157: 6). | 15 [2] | Org_Chart_2026.jpg | The answer states the correct total of 15 people working on Bank Teratai projects, matching the reference. | retrieval (expected source not cited) |
| Q28 | wrong | Adakah saya perlu mengambil cuti tahunan pada 29 Disember 2026? | Tidak. 29 Disember 2026 ialah cuti syarikat (tidak ditolak daripada cuti tahunan). Cuti tahunan hanya diperlukan pada 28 dan 31 Disember. | Ya, anda perlu mengambil cuti tahunan pada 29 Disember 2026 kecuali jika anda diberi cuti syarikat oleh syarikat. [1] | Notis_Penutupan_Akhir_Tahun_2026_Year_End_Closure.pdf | The system answer incorrectly states that annual leave is required on 29 December 2026, while the reference says it is a company holiday and annual leave is not needed on that day. | answering (right source, wrong or incomplete answer) |
