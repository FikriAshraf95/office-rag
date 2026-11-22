# Eval nemo-super-m07-run3 — 2026-11-21

- **Score: 27.5 / 32 (86%)** — 27 correct, 1 partial, 4 wrong
- Answer model `nemo-super`, judge `nemo-super`, provider `ilmu`, user `ben`
- Latency p50 366 ms, p95 709 ms; first token p50 292 ms
- Tokens per question: 2117 in, 24 out; cost per question: n/a (plan-quota model)

## By category

| Category | Score | % |
|---|---|---|
| multi-hop | 2 / 2 | 100% |
| multi-hop / guardrail | 1 / 1 | 100% |
| multi-hop / vision | 1 / 1 | 100% |
| multilingual (Malay question) | 1 / 1 | 100% |
| multilingual doc | 1 / 1 | 100% |
| not found | 2 / 2 | 100% |
| override / OCR | 1 / 2 | 50% |
| policy | 4.5 / 6 | 75% |
| policy (negative) | 1 / 1 | 100% |
| reasoning | 2 / 2 | 100% |
| table aggregation | 1 / 1 | 100% |
| table lookup | 4 / 6 | 67% |
| version | 4 / 4 | 100% |
| vision | 2 / 2 | 100% |

## All questions

| Id | Verdict | Found | Sources | Latency | Reason |
|---|---|---|---|---|---|
| Q01 | wrong | True | ok | 481 ms | The answer incorrectly states 'immediate supervisor approval' is required, whereas the reference answer specifies that up to 10 days can be taken without HOD approval (implying supervisor approval may be sufficient or not the gatekeeper), and the core condition is misrepresented. |
| Q02 | wrong | False | miss | 322 ms | The reference answer states that a Grade M2 manager with 6 years of service gets 22 days of annual leave, but the system answer claims it could not find this information, which is incorrect given that the reference provides the correct value. |
| Q03 | correct | True | ok | 690 ms | The answer correctly states that a new Executive (E1) with 1 year of service gets 14 annual leave days per year, matching the reference. |
| Q04 | correct | True | ok | 514 ms | The answer correctly states the maximum carry-forward days and the deadline for using 2026 leave, matching the reference answer and avoiding the outdated Handbook 2024 trap. |
| Q05 | wrong | True | ok | 331 ms | The answer incorrectly states '3 working days' instead of the required 'at least 14 calendar days in advance' for leave of more than 3 working days. |
| Q06 | correct | True | ok | 366 ms | The answer matches the reference exactly, stating the correct minimum of 3 days and the specific days: Tuesday, Wednesday, and Thursday. |
| Q07 | correct | True | ok | 399 ms | The answer correctly states the core working hours as 10:00 to 16:00, matching the reference answer. |
| Q08 | correct | True | ok | 351 ms | The answer states the correct yearly limit for outpatient medical claims as RM 1,500 per calendar year, which matches the reference answer and avoids the 2024 trap of RM 1,000. |
| Q09 | correct | True | ok | 288 ms | The answer correctly states the notice period for a manager (M grade) who resigns is 2 months, matching the reference answer and avoiding the outdated 2024 trap. |
| Q10 | correct | True | ok | 775 ms | The answer correctly states the 20‑day limit with HOD and HR approval and notes the Bank Teratai system restriction, matching the reference. |
| Q11 | correct | True | ok | 340 ms | The system answer correctly states 7 consecutive days, matching the reference answer. |
| Q12 | partial | True | ok | 351 ms | The core fact (RM 0.70 per km) is correct, but the answer omits the condition that toll and parking are reimbursable with receipts. |
| Q13 | correct | True | ok | 349 ms | The answer correctly states the hotel limit per night for a business trip to Penang as RM 350 per night, matching the reference exactly. |
| Q14 | correct | True | ok | 603 ms | The answer correctly states that S2 engineers are not eligible for business class, matching the reference that business class is only for flights over 6 hours and M grades and above, and S2 is below M1. |
| Q15 | correct | True | ok | 493 ms | The system answer accurately states the 30-day submission deadline and the 60-day rejection rule, matching the reference answer. |
| Q16 | correct | True | ok | 557 ms | The answer correctly states that both HOD and Finance must approve claims over RM 2,000, which includes RM 2,500. |
| Q17 | correct | True | ok | 275 ms | The answer states the correct minimum password length of 14 characters as specified in the reference. |
| Q18 | correct | True | ok | 519 ms | The answer correctly states that personal AI accounts like ChatGPT are not approved for client data, matching the reference. |
| Q19 | correct | True | ok | 470 ms | The answer correctly states both the email recipient and the required timeframe (within 1 hour), and includes the after-hours IT on-call contact with the correct extension, matching the reference exactly. |
| Q20 | correct | True | ok | 268 ms | The system answer correctly states that Bank Teratai must be notified of a security incident within 2 hours, which matches the reference answer. |
| Q21 | correct | True | ok | 709 ms | The system answer includes all required facts: booking 3 working days ahead via Arjun Pillai, safety induction, wearing safety boots and high-visibility vest, and prohibiting USB drives on the OT network. |
| Q22 | correct | True | ok | 366 ms | The answer correctly states that Gemilang Capital data must be hosted in Malaysia or Singapore, matching the reference answer exactly. |
| Q23 | correct | True | ok | 472 ms | The answer correctly states the account manager for Gemilang Capital is Zainab Yusof and that she reports to Nurul Huda, Client Delivery Director. |
| Q24 | correct | True | ok | 347 ms | The answer correctly states that the Finance team reports to Hafiz Osman, the CFO, which matches the reference answer. |
| Q25 | correct | True | ok | 370 ms | The answer correctly states Jason Wong as Head of Security and that he reports to Daniel Lim, CTO, matching the reference. |
| Q26 | correct | True | ok | 360 ms | The answer correctly states that 15 people are working on Bank Teratai projects, matching the reference answer. |
| Q27 | wrong | False | miss | 431 ms | The system answer states it could not find the information, but the reference answer provides a specific end date of 31 December 2026, indicating the information is available in the documents. |
| Q28 | correct | True | ok | 536 ms | The answer correctly states that annual leave is not required on 29 Disember 2026 because it is a company holiday, matching the reference answer and notes. |
| Q29 | correct | True | ok | 330 ms | The answer correctly states the days during the year-end closure that require annual leave: 28 and 31 December 2026, with the option to work from home if agreed with HOD, matching the reference. |
| Q30 | correct | False | ok | 169 ms | The answer correctly states that the information is not found in the documents and directs the user to contact HR as instructed. |
| Q31 | correct | False | ok | 115 ms | The answer correctly states the information is not found and suggests contacting HR, which matches the reference. |
| Q32 | correct | True | ok | 319 ms | The answer correctly states that office parking is not reimbursed as per the Travel and Claims SOP. |

## Failures and triage

Cause hint is automatic; confirm by hand as parsing, chunking, retrieval or answering.

| Id | Verdict | Question | Expected | Got | Cited | Reason | Cause hint |
|---|---|---|---|---|---|---|---|
| Q01 | wrong | What is the maximum number of consecutive working days I can take in one leave application without HOD approval? | 10 consecutive working days (effective 1 Oct 2026). Longer needs HOD + HR approval. | 10 working days (with immediate supervisor approval) [3] | Memo_HR_2026-09_Leave_Policy_Amendment_scan.png | The answer incorrectly states 'immediate supervisor approval' is required, whereas the reference answer specifies that up to 10 days can be taken without HOD approval (implying supervisor approval may be sufficient or not the gatekeeper), and the core condition is misrepresented. | answering (right source, wrong or incomplete answer) |
| Q02 | wrong | How many days of annual leave does a Grade M2 manager with 6 years of service get? | 22 days per year. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The reference answer states that a Grade M2 manager with 6 years of service gets 22 days of annual leave, but the system answer claims it could not find this information, which is incorrect given that the reference provides the correct value. | retrieval (gate or ranking) or answering (refused) |
| Q05 | wrong | How far in advance must I apply for 5 days of annual leave? | At least 14 calendar days in advance (leave of more than 3 working days). | At least 3 working days in advance. [1] | HR_Employee_Handbook_2026.pdf | The answer incorrectly states '3 working days' instead of the required 'at least 14 calendar days in advance' for leave of more than 3 working days. | answering (right source, wrong or incomplete answer) |
| Q12 | partial | What is the mileage claim rate for using my own car? | RM 0.70 per km, plus toll and parking with receipts. | RM 0.70 per km [1] | Travel_and_Claims_SOP.md | The core fact (RM 0.70 per km) is correct, but the answer omits the condition that toll and parking are reimbursable with receipts. | answering (right source, wrong or incomplete answer) |
| Q27 | wrong | When does the Gemilang Capital contract end? | 31 December 2026. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The system answer states it could not find the information, but the reference answer provides a specific end date of 31 December 2026, indicating the information is available in the documents. | retrieval (gate or ranking) or answering (refused) |
