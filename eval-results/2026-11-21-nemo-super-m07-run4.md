# Eval nemo-super-m07-run4 — 2026-11-21

- **Score: 26.5 / 32 (83%)** — 24 correct, 5 partial, 3 wrong
- Answer model `nemo-super`, judge `nemo-super`, provider `ilmu`, user `ben`
- Latency p50 445 ms, p95 668 ms; first token p50 329 ms
- Tokens per question: 2117 in, 23 out; cost per question: n/a (plan-quota model)

## By category

| Category | Score | % |
|---|---|---|
| multi-hop | 2 / 2 | 100% |
| multi-hop / guardrail | 1 / 1 | 100% |
| multi-hop / vision | 1 / 1 | 100% |
| multilingual (Malay question) | 1 / 1 | 100% |
| multilingual doc | 0.5 / 1 | 50% |
| not found | 2 / 2 | 100% |
| override / OCR | 1.5 / 2 | 75% |
| policy | 4.5 / 6 | 75% |
| policy (negative) | 1 / 1 | 100% |
| reasoning | 2 / 2 | 100% |
| table aggregation | 1 / 1 | 100% |
| table lookup | 3.5 / 6 | 58% |
| version | 4 / 4 | 100% |
| vision | 1.5 / 2 | 75% |

## All questions

| Id | Verdict | Found | Sources | Latency | Reason |
|---|---|---|---|---|---|
| Q01 | partial | True | ok | 450 ms | The core fact of 10 consecutive working days is correct, but the answer incorrectly adds 'with immediate supervisor approval' instead of stating that HOD approval is required for longer leaves, omitting the key condition from the reference. |
| Q02 | wrong | False | miss | 371 ms | The reference answer states 22 days per year, but the system answer claims it could not find the information, which contradicts the known correct value. |
| Q03 | partial | True | ok | 471 ms | The reference states 14 days per year for an Executive with 1 year of service, but the answer incorrectly states it is pro-rated to 7 days, which contradicts the reference. |
| Q04 | correct | True | ok | 583 ms | The answer correctly states the current policy: up to 5 days can be carried forward and must be used by 30 April 2027, matching the reference and avoiding the outdated Handbook 2024 trap. |
| Q05 | wrong | True | ok | 469 ms | The system answer incorrectly states 3 working days, while the reference specifies at least 14 calendar days for leave exceeding 3 working days. |
| Q06 | correct | True | ok | 644 ms | The answer correctly states the minimum of 3 days and specifies Tuesday, Wednesday, and Thursday, matching the reference answer despite extra contextual details. |
| Q07 | correct | True | ok | 394 ms | The answer correctly states the core working hours as 10:00 to 16:00, matching the reference answer without falling into the outdated 2024 trap. |
| Q08 | correct | True | ok | 384 ms | The system answer correctly states the yearly limit for outpatient medical claims as RM 1,500 per calendar year, matching the reference answer and avoiding the outdated 2024 value of RM 1,000. |
| Q09 | correct | True | ok | 364 ms | The answer correctly states the notice period for a manager (M grade) who resigns as 2 months, matching the reference. |
| Q10 | correct | True | ok | 600 ms | The answer correctly states that overseas remote work is allowed up to 20 working days per year with HOD and HR approval, and includes the relevant restriction about system access and client contracts, aligning with the reference. |
| Q11 | correct | True | ok | 486 ms | The answer matches the reference exactly, stating 7 consecutive days of paternity leave. |
| Q12 | partial | True | ok | 427 ms | The core fact is correct, but the answer omits the condition that toll and parking costs are also claimable with receipts. |
| Q13 | correct | True | ok | 339 ms | The answer states the correct hotel limit of RM 350 per night for a business trip to Penang as per the reference. |
| Q14 | correct | True | ok | 668 ms | The answer correctly states that S2 engineers cannot fly business class because it requires flights over 6 hours and M grade or above, and S2 is below M1. |
| Q15 | correct | True | ok | 445 ms | The system answer matches the reference answer exactly, stating the 30-day submission deadline and the 60-day rejection rule. |
| Q16 | correct | True | ok | 464 ms | The answer correctly states that both HOD and Finance must approve a claim of RM 2,500, which exceeds the RM 2,000 threshold requiring dual approval. |
| Q17 | correct | True | ok | 352 ms | The answer states the correct minimum password length of 14 characters as specified in the reference. |
| Q18 | correct | True | ok | 635 ms | The system answer correctly states that client data cannot be pasted into personal AI accounts and lists the approved tools, matching the reference. |
| Q19 | correct | True | ok | 491 ms | The answer matches the reference exactly in terms of recipient, timeframe, and escalation procedure. |
| Q20 | correct | True | ok | 455 ms | The answer correctly states the 2-hour notification requirement as per the reference. |
| Q21 | correct | True | ok | 787 ms | The system answer accurately states all required pre-visit conditions: booking at least 3 working days ahead through the account manager, completing a safety induction, wearing safety boots and a high-visibility vest, and prohibiting USB drives on the OT network. |
| Q22 | correct | True | ok | 405 ms | The answer correctly states that Gemilang Capital data must be hosted in Malaysia or Singapore, matching the reference answer exactly. |
| Q23 | correct | True | ok | 551 ms | The answer provides the correct account manager and reporting line as stated in the reference. |
| Q24 | partial | True | ok | 351 ms | The core fact that the Finance team reports to the CFO Hafiz Osman is correct, but the answer does not mention the Finance Manager Kumar Selvam as the immediate reporting line, omitting a condition. |
| Q25 | correct | True | ok | 400 ms | The answer correctly states that Jason Wong is the Head of Security and reports to Daniel Lim, the CTO, matching the reference. |
| Q26 | correct | True | ok | 466 ms | The answer states the correct total number of people (15) working on Bank Teratai projects as per the reference. |
| Q27 | wrong | False | miss | 318 ms | The answer claims the information is not in the documents, but the reference provides a definite end date, so inventing that it cannot be found is incorrect. |
| Q28 | correct | True | ok | 536 ms | Jawapan menyatakan dengan betul bahawa 29 Disember 2026 adalah cuti syarikat dan tidak perlu diambil daripada cuti tahunan, sesuai dengan jawapan rujukan. |
| Q29 | partial | True | ok | 445 ms | The answer correctly states the days requiring annual leave but omits the alternative option of working from home with HOD agreement. |
| Q30 | correct | False | ok | 108 ms | The answer correctly states that the information is not found in the documents and advises contacting HR as suggested in the reference answer. |
| Q31 | correct | False | ok | 101 ms | The answer correctly states the information is not found and suggests contacting HR without guessing. |
| Q32 | correct | True | ok | 425 ms | The answer correctly states that office parking is not reimbursed, matching the reference answer from the Travel and Claims SOP. |

## Failures and triage

Cause hint is automatic; confirm by hand as parsing, chunking, retrieval or answering.

| Id | Verdict | Question | Expected | Got | Cited | Reason | Cause hint |
|---|---|---|---|---|---|---|---|
| Q01 | partial | What is the maximum number of consecutive working days I can take in one leave application without HOD approval? | 10 consecutive working days (effective 1 Oct 2026). Longer needs HOD + HR approval. | 10 working days (with immediate supervisor approval) [3] | Memo_HR_2026-09_Leave_Policy_Amendment_scan.png | The core fact of 10 consecutive working days is correct, but the answer incorrectly adds 'with immediate supervisor approval' instead of stating that HOD approval is required for longer leaves, omitting the key condition from the reference. | answering (right source, wrong or incomplete answer) |
| Q02 | wrong | How many days of annual leave does a Grade M2 manager with 6 years of service get? | 22 days per year. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The reference answer states 22 days per year, but the system answer claims it could not find the information, which contradicts the known correct value. | retrieval (gate or ranking) or answering (refused) |
| Q03 | partial | How many annual leave days does a new Executive (E1) with 1 year of service get? | 14 days per year. | 14 days (pro-rated to 7 days for 1 year of service) [1][3] | HR_Employee_Handbook_2026.pdf, Leave_Entitlement_by_Grade_2026.xlsx | The reference states 14 days per year for an Executive with 1 year of service, but the answer incorrectly states it is pro-rated to 7 days, which contradicts the reference. | answering (right source, wrong or incomplete answer) |
| Q05 | wrong | How far in advance must I apply for 5 days of annual leave? | At least 14 calendar days in advance (leave of more than 3 working days). | At least 3 working days in advance. [1] | HR_Employee_Handbook_2026.pdf | The system answer incorrectly states 3 working days, while the reference specifies at least 14 calendar days for leave exceeding 3 working days. | answering (right source, wrong or incomplete answer) |
| Q12 | partial | What is the mileage claim rate for using my own car? | RM 0.70 per km, plus toll and parking with receipts. | RM 0.70 per km [1] | Travel_and_Claims_SOP.md | The core fact is correct, but the answer omits the condition that toll and parking costs are also claimable with receipts. | answering (right source, wrong or incomplete answer) |
| Q24 | partial | Who does the Finance team report to? | Finance Manager Kumar Selvam, who reports to CFO Hafiz Osman. | Hafiz Osman, Chief Financial Officer [1] | Org_Chart_2026.jpg | The core fact that the Finance team reports to the CFO Hafiz Osman is correct, but the answer does not mention the Finance Manager Kumar Selvam as the immediate reporting line, omitting a condition. | answering (right source, wrong or incomplete answer) |
| Q27 | wrong | When does the Gemilang Capital contract end? | 31 December 2026. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The answer claims the information is not in the documents, but the reference provides a definite end date, so inventing that it cannot be found is incorrect. | retrieval (gate or ranking) or answering (refused) |
| Q29 | partial | Which days during the year-end closure do I need to apply annual leave for? | 28 and 31 December 2026 (or work from home with HOD agreement). 24, 29, 30 Dec are company leave; 25 Dec and 1 Jan are public holidays. | 28 and 31 December 2026 [2] | Notis_Penutupan_Akhir_Tahun_2026_Year_End_Closure.pdf | The answer correctly states the days requiring annual leave but omits the alternative option of working from home with HOD agreement. | answering (right source, wrong or incomplete answer) |
