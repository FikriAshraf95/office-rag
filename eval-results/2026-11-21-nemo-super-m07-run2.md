# Eval nemo-super-m07-run2 — 2026-11-21

- **Score: 25.5 / 32 (80%)** — 24 correct, 3 partial, 5 wrong
- Answer model `nemo-super`, judge `nemo-super`, provider `ilmu`, user `ben`
- Latency p50 371 ms, p95 601 ms; first token p50 292 ms
- Tokens per question: 2105 in, 22 out; cost per question: n/a (plan-quota model)

## By category

| Category | Score | % |
|---|---|---|
| multi-hop | 1.5 / 2 | 75% |
| multi-hop / guardrail | 1 / 1 | 100% |
| multi-hop / vision | 1 / 1 | 100% |
| multilingual (Malay question) | 1 / 1 | 100% |
| multilingual doc | 1 / 1 | 100% |
| not found | 2 / 2 | 100% |
| override / OCR | 1.5 / 2 | 75% |
| policy | 4.5 / 6 | 75% |
| policy (negative) | 1 / 1 | 100% |
| reasoning | 2 / 2 | 100% |
| table aggregation | 1 / 1 | 100% |
| table lookup | 3 / 6 | 50% |
| version | 4 / 4 | 100% |
| vision | 1 / 2 | 50% |

## All questions

| Id | Verdict | Found | Sources | Latency | Reason |
|---|---|---|---|---|---|
| Q01 | partial | True | ok | 486 ms | The core fact (10 working days) is correct, but the condition is incorrect—it requires no HOD approval, not immediate supervisor approval. |
| Q02 | wrong | False | miss | 385 ms | The answer states it could not find the information, but the reference answer provides a specific value (22 days) that should be stated directly. |
| Q03 | wrong | True | ok | 529 ms | The answer incorrectly pro-rates the leave to 7 days for 1 year of service, but the reference states a new Executive (E1) with 1 year of service gets 14 days per year. |
| Q04 | correct | True | ok | 593 ms | The answer correctly states that up to 5 days can be carried forward from 2026 and must be used by 30 April 2027, matching the reference answer. |
| Q05 | wrong | True | ok | 355 ms | The system answer incorrectly states "3 working days" while the reference requires "at least 14 calendar days in advance" for leave of more than 3 working days. |
| Q06 | correct | True | ok | 566 ms | The answer correctly states the minimum of 3 days and specifies Tuesday, Wednesday, and Thursday, matching the reference answer. |
| Q07 | correct | True | ok | 417 ms | The answer correctly states the core working hours as 10:00 to 16:00, matching the reference answer. |
| Q08 | correct | True | ok | 357 ms | The answer correctly states the yearly limit for outpatient medical claims as RM 1,500 per calendar year, matching the reference and avoiding the outdated 2024 value. |
| Q09 | correct | True | ok | 344 ms | The answer correctly states the notice period for a manager (M grade) who resigns as 2 months, matching the reference answer and avoiding the outdated 2024 trap. |
| Q10 | correct | True | ok | 587 ms | The system answer correctly states the 20-working-day limit with HOD and HR approval and appropriately notes that system access may be restricted, aligning with the reference and notes. |
| Q11 | correct | True | ok | 333 ms | The answer correctly states that employees get 7 consecutive days of paternity leave, matching the reference answer exactly. |
| Q12 | partial | True | ok | 338 ms | The answer correctly states the mileage rate but omits the condition that toll and parking are reimbursable with receipts. |
| Q13 | correct | True | ok | 286 ms | The answer matches the reference value exactly. |
| Q14 | correct | True | ok | 516 ms | The system answer correctly states that business class requires flights over 6 hours and M grades or above, and that S2 is below M grade, so S2 flies economy. |
| Q15 | correct | True | ok | 557 ms | The system answer accurately states the deadline as within 30 days and mentions that claims older than 60 days are rejected, matching the reference answer exactly. |
| Q16 | correct | True | ok | 367 ms | The answer correctly states that both the HOD and Finance must approve a claim over RM 2,000, which includes RM 2,500, matching the reference answer exactly. |
| Q17 | correct | True | ok | 321 ms | The answer correctly states the minimum password length as 14 characters, matching the reference. |
| Q18 | correct | True | ok | 601 ms | The answer correctly states that client data is restricted and must not be entered into personal AI accounts like ChatGPT, and specifies the approved tools, matching the reference answer. |
| Q19 | correct | True | ok | 483 ms | Matches the reference exactly: reports to security@serimaju.example within 1 hour and calls IT on-call at ext. 2222 outside office hours. |
| Q20 | correct | True | ok | 335 ms | The answer correctly states that Bank Teratai must be notified within 2 hours after internal reporting to Security within 1 hour, matching the reference. |
| Q21 | partial | True | ok | 468 ms | The answer correctly mentions safety induction and required PPE but omits the requirement to book at least 3 working days ahead through the account manager and the prohibition on USB drives on the OT network. |
| Q22 | correct | True | ok | 563 ms | The answer matches the reference answer exactly, stating the correct hosting locations. |
| Q23 | correct | True | ok | 420 ms | The answer correctly states that Zainab Yusof is the account manager for Gemilang Capital and reports to Nurul Huda, matching the reference answer. |
| Q24 | wrong | True | ok | 356 ms | The system answer reverses the reporting relationship and states that Hafiz Osman reports to Aisyah Rahman, which contradicts the reference answer that Finance Manager Kumar Selvam reports to CFO Hafiz Osman. |
| Q25 | correct | True | ok | 371 ms | The answer correctly states Jason Wong is Head of Security and reports to Daniel Lim, who is identified as the CTO. |
| Q26 | correct | True | ok | 328 ms | The system answer states the correct total number of people working on Bank Teratai projects as 15, matching the reference answer. |
| Q27 | wrong | False | miss | 317 ms | The reference states a specific end date (31 December 2026), but the system answer claims it could not find the information and invents a suggestion to contact HR, which contradicts the known answer. |
| Q28 | correct | True | ok | 713 ms | Jawapan betul menyatakan bahawa 29 Disember 2026 adalah cuti syarikat dan tidak perlu diambil daripada cuti tahunan, sesuai dengan rujukan. |
| Q29 | correct | True | ok | 356 ms | The answer correctly identifies the days requiring annual leave during the year-end closure as 28 and 31 December 2026, matching the reference answer exactly. |
| Q30 | correct | False | ok | 137 ms | The system answer correctly states it couldn't find the information and advises contacting HR, matching the reference. |
| Q31 | correct | False | ok | 95 ms | The system answer correctly states that the information is not found in the documents and suggests contacting HR, which matches the reference answer and avoids guessing. |
| Q32 | correct | True | ok | 406 ms | The answer correctly states that office parking is not reimbursed, matching the reference answer from the Travel and Claims SOP. |

## Failures and triage

Cause hint is automatic; confirm by hand as parsing, chunking, retrieval or answering.

| Id | Verdict | Question | Expected | Got | Cited | Reason | Cause hint |
|---|---|---|---|---|---|---|---|
| Q01 | partial | What is the maximum number of consecutive working days I can take in one leave application without HOD approval? | 10 consecutive working days (effective 1 Oct 2026). Longer needs HOD + HR approval. | 10 working days (with immediate supervisor approval) [3] | Memo_HR_2026-09_Leave_Policy_Amendment_scan.png | The core fact (10 working days) is correct, but the condition is incorrect—it requires no HOD approval, not immediate supervisor approval. | answering (right source, wrong or incomplete answer) |
| Q02 | wrong | How many days of annual leave does a Grade M2 manager with 6 years of service get? | 22 days per year. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The answer states it could not find the information, but the reference answer provides a specific value (22 days) that should be stated directly. | retrieval (gate or ranking) or answering (refused) |
| Q03 | wrong | How many annual leave days does a new Executive (E1) with 1 year of service get? | 14 days per year. | 14 days (pro-rated to 7 days for 1 year of service) [1][3] | HR_Employee_Handbook_2026.pdf, Leave_Entitlement_by_Grade_2026.xlsx | The answer incorrectly pro-rates the leave to 7 days for 1 year of service, but the reference states a new Executive (E1) with 1 year of service gets 14 days per year. | answering (right source, wrong or incomplete answer) |
| Q05 | wrong | How far in advance must I apply for 5 days of annual leave? | At least 14 calendar days in advance (leave of more than 3 working days). | At least 3 working days in advance. [1] | HR_Employee_Handbook_2026.pdf | The system answer incorrectly states "3 working days" while the reference requires "at least 14 calendar days in advance" for leave of more than 3 working days. | answering (right source, wrong or incomplete answer) |
| Q12 | partial | What is the mileage claim rate for using my own car? | RM 0.70 per km, plus toll and parking with receipts. | RM 0.70 per km [1] | Travel_and_Claims_SOP.md | The answer correctly states the mileage rate but omits the condition that toll and parking are reimbursable with receipts. | answering (right source, wrong or incomplete answer) |
| Q21 | partial | What do I need before visiting the Pelita Precision factory? | Book at least 3 working days ahead through the account manager (Arjun Pillai), complete a safety induction, and wear safety boots and a high-visibility vest. No USB drives on the OT network. | You need a safety induction before the first visit and must wear personal protective equipment (safety boots and a high-visibility vest) on the factory floor. [1] | Client_Engagement_and_Data_Handling_Policy.docx | The answer correctly mentions safety induction and required PPE but omits the requirement to book at least 3 working days ahead through the account manager and the prohibition on USB drives on the OT network. | answering (right source, wrong or incomplete answer) |
| Q24 | wrong | Who does the Finance team report to? | Finance Manager Kumar Selvam, who reports to CFO Hafiz Osman. | Hafiz Osman, Chief Financial Officer, reports to: Aisyah Rahman [2] | Org_Chart_2026.jpg | The system answer reverses the reporting relationship and states that Hafiz Osman reports to Aisyah Rahman, which contradicts the reference answer that Finance Manager Kumar Selvam reports to CFO Hafiz Osman. | answering (right source, wrong or incomplete answer) |
| Q27 | wrong | When does the Gemilang Capital contract end? | 31 December 2026. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The reference states a specific end date (31 December 2026), but the system answer claims it could not find the information and invents a suggestion to contact HR, which contradicts the known answer. | retrieval (gate or ranking) or answering (refused) |
