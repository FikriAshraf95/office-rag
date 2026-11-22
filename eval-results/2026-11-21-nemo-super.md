# Eval nemo-super — 2026-11-21

- **Score: 25 / 32 (78%)** — 24 correct, 2 partial, 6 wrong
- Answer model `nemo-super`, judge `nemo-super`, provider `ilmu`, user `ben`
- Latency p50 442 ms, p95 692 ms; first token p50 320 ms
- Tokens per question: 1952 in, 22 out; cost per question: n/a (plan-quota model)

## By category

| Category | Score | % |
|---|---|---|
| multi-hop | 2 / 2 | 100% |
| multi-hop / guardrail | 1 / 1 | 100% |
| multi-hop / vision | 0 / 1 | 0% |
| multilingual (Malay question) | 1 / 1 | 100% |
| multilingual doc | 1 / 1 | 100% |
| not found | 2 / 2 | 100% |
| override / OCR | 1.5 / 2 | 75% |
| policy | 4.5 / 6 | 75% |
| policy (negative) | 1 / 1 | 100% |
| reasoning | 2 / 2 | 100% |
| table aggregation | 1 / 1 | 100% |
| table lookup | 4 / 6 | 67% |
| version | 4 / 4 | 100% |
| vision | 0 / 2 | 0% |

## All questions

| Id | Verdict | Found | Sources | Latency | Reason |
|---|---|---|---|---|---|
| Q01 | partial | True | ok | 425 ms | The answer correctly states 10 working days but incorrectly adds 'with immediate supervisor approval', when the reference indicates HOD + HR approval is required for longer leaves, and the 10-day limit applies without HOD approval. |
| Q02 | wrong | False | miss | 471 ms | The answer invents a statement about not finding the information, but the reference clearly states the correct value is 22 days per year. |
| Q03 | correct | True | ok | 564 ms | The answer correctly states 14 days per year for a new Executive (E1) with 1 year of service, matching the reference answer. |
| Q04 | correct | True | ok | 682 ms | The answer correctly states that up to 5 days can be carried forward and that 2026 balances must be used by 30 April 2027, matching the reference answer. |
| Q05 | wrong | True | ok | 462 ms | The answer states 3 working days, but the reference requires at least 14 calendar days for more than 3 working days of leave. |
| Q06 | correct | True | ok | 489 ms | The answer correctly states the required office days and matches the reference answer exactly. |
| Q07 | correct | True | ok | 455 ms | The answer correctly states the core working hours as 10:00 to 16:00, matching the reference answer and avoiding the outdated 2024 trap. |
| Q08 | correct | True | ok | 335 ms | The answer correctly states the yearly limit for outpatient medical claims as RM 1,500 per calendar year, matching the reference. |
| Q09 | correct | True | ok | 329 ms | The answer correctly states the notice period for a manager (M grade) who resigns as 2 months, matching the reference and avoiding the outdated 2024 trap. |
| Q10 | correct | True | ok | 587 ms | The answer correctly states the 20-day limit and HOD/HR approval requirement, and adds a relevant note about client contracts, which aligns with the reference and notes about combining documents. |
| Q11 | correct | True | ok | 321 ms | The answer states the correct fact of 7 consecutive days, matching the reference. |
| Q12 | partial | True | ok | 395 ms | The system answer correctly states the mileage rate of RM 0.70 per km but omits the additional reimbursement for toll and parking with receipts, which is part of the complete reference answer. |
| Q13 | correct | True | ok | 478 ms | The answer matches the reference exactly, stating the correct hotel limit of RM 350 per night. |
| Q14 | correct | True | ok | 717 ms | The answer correctly states the policy conditions and applies them to the S2 grade. |
| Q15 | correct | True | ok | 472 ms | The system answer correctly states the 30-day submission deadline and the 60-day rejection rule, matching the reference answer. |
| Q16 | correct | True | ok | 442 ms | The answer correctly states that both the HOD and Finance must approve claims over RM 2,000, which includes RM 2,500. |
| Q17 | correct | True | ok | 293 ms | The answer states the correct minimum password length of 14 characters as per the reference. |
| Q18 | correct | True | ok | 673 ms | The system answer correctly states that Bank Teratai customer data must not be entered into unapproved AI tools, including personal ChatGPT accounts, which aligns with the reference answer. |
| Q19 | correct | True | ok | 461 ms | The answer accurately states the correct reporting channel and timeframe as specified in the reference. |
| Q20 | correct | True | ok | 406 ms | The answer correctly states the required 2-hour notification window for Bank Teratai after internal reporting, matching the reference. |
| Q21 | correct | True | ok | 692 ms | The answer includes all required elements: booking 3 working days ahead via the account manager, safety induction, safety boots and high-visibility vest, and the prohibition on USB drives on the OT network. |
| Q22 | correct | True | ok | 370 ms | The answer correctly states that Gemilang Capital data must be hosted in Malaysia or Singapore, matching the reference answer. |
| Q23 | wrong | True | ok | 487 ms | The system answer incorrectly states that Zainab Yusof reports to Siti Aminah, while the reference answer specifies she reports to Nurul Huda, Client Delivery Director. |
| Q24 | wrong | False | miss | 190 ms | The answer claims the information is not in the documents, but the reference answer states that Finance Manager Kumar Selvam reports to CFO Hafiz Osman, so the correct information is present. |
| Q25 | wrong | False | miss | 94 ms | The answer claims the information is not in the documents, but the reference answer provides the Head of Security as Jason Wong reporting to CTO Daniel Lim, so the answer is incorrect. |
| Q26 | correct | True | ok | 428 ms | The answer correctly states the total number of people working on Bank Teratai projects as 15, matching the reference answer. |
| Q27 | wrong | False | miss | 379 ms | The reference answer provides a specific end date, but the system answer claims it could not find the information, which contradicts the reference and invents an inability to answer where the documents do contain the answer. |
| Q28 | correct | True | ok | 478 ms | Jawapan menyatakan betul bahawa 29 Disember 2026 adalah cuti syarikat dan tidak perlu mengambil cuti tahunan, seperti yang dinyatakan dalam rujukan. |
| Q29 | correct | True | ok | 417 ms | The system answer correctly states the days requiring annual leave (28 and 31 December 2026) without adding incorrect details or omitting key conditions. |
| Q30 | correct | False | ok | 174 ms | The answer correctly states that the information is not found and suggests contacting HR as instructed. |
| Q31 | correct | False | ok | 207 ms | The answer correctly states that the information is not found in the documents and suggests contacting HR, which aligns with the reference and avoids guessing. |
| Q32 | correct | True | ok | 568 ms | The answer correctly states that office parking is not reimbursed, matching the reference answer and preserving the condition. |

## Failures and triage

Cause hint is automatic; confirm by hand as parsing, chunking, retrieval or answering.

| Id | Verdict | Question | Expected | Got | Cited | Reason | Cause hint |
|---|---|---|---|---|---|---|---|
| Q01 | partial | What is the maximum number of consecutive working days I can take in one leave application without HOD approval? | 10 consecutive working days (effective 1 Oct 2026). Longer needs HOD + HR approval. | 10 working days (with immediate supervisor approval) [3] | Memo_HR_2026-09_Leave_Policy_Amendment_scan.png | The answer correctly states 10 working days but incorrectly adds 'with immediate supervisor approval', when the reference indicates HOD + HR approval is required for longer leaves, and the 10-day limit applies without HOD approval. | answering (right source, wrong or incomplete answer) |
| Q02 | wrong | How many days of annual leave does a Grade M2 manager with 6 years of service get? | 22 days per year. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The answer invents a statement about not finding the information, but the reference clearly states the correct value is 22 days per year. | retrieval (gate or ranking) or answering (refused) |
| Q05 | wrong | How far in advance must I apply for 5 days of annual leave? | At least 14 calendar days in advance (leave of more than 3 working days). | At least 3 working days in advance. [1] | HR_Employee_Handbook_2026.pdf | The answer states 3 working days, but the reference requires at least 14 calendar days for more than 3 working days of leave. | answering (right source, wrong or incomplete answer) |
| Q12 | partial | What is the mileage claim rate for using my own car? | RM 0.70 per km, plus toll and parking with receipts. | RM 0.70 per km [3] | Travel_and_Claims_SOP.md | The system answer correctly states the mileage rate of RM 0.70 per km but omits the additional reimbursement for toll and parking with receipts, which is part of the complete reference answer. | answering (right source, wrong or incomplete answer) |
| Q23 | wrong | Who is the account manager for Gemilang Capital, and who does she report to? | Zainab Yusof; she reports to Nurul Huda, Client Delivery Director. | Zainab Yusof is the account manager for Gemilang Capital Berhad. She reports to the Delivery lead, Siti Aminah. [1][2] | Client_Accounts_Q4_2026.xlsx, Client_Engagement_and_Data_Handling_Policy.docx | The system answer incorrectly states that Zainab Yusof reports to Siti Aminah, while the reference answer specifies she reports to Nurul Huda, Client Delivery Director. | answering (right source, wrong or incomplete answer) |
| Q24 | wrong | Who does the Finance team report to? | Finance Manager Kumar Selvam, who reports to CFO Hafiz Osman. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The answer claims the information is not in the documents, but the reference answer states that Finance Manager Kumar Selvam reports to CFO Hafiz Osman, so the correct information is present. | retrieval (gate or ranking) or answering (refused) |
| Q25 | wrong | Who is the Head of Security and which executive do they report to? | Jason Wong; reports to CTO Daniel Lim. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The answer claims the information is not in the documents, but the reference answer provides the Head of Security as Jason Wong reporting to CTO Daniel Lim, so the answer is incorrect. | retrieval (gate or ranking) or answering (refused) |
| Q27 | wrong | When does the Gemilang Capital contract end? | 31 December 2026. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The reference answer provides a specific end date, but the system answer claims it could not find the information, which contradicts the reference and invents an inability to answer where the documents do contain the answer. | retrieval (gate or ranking) or answering (refused) |

## Triage (confirmed by hand)

Retrieval was checked with `python -m app.eval.inspect_search`. Score 25 / 32 is one short of the 26 target; five of the seven misses are not cheap fixes and go to M07/M08.

| Id | Cause | Evidence | Next |
|---|---|---|---|
| Q24, Q25 | **parsing** (image has no text yet) | `Org_Chart_2026.jpg` is never retrieved; best vec_sim 0.502 fails the gate | M07 vision descriptions |
| Q23 | **parsing** (same chart) | Answer built from the spreadsheet; the chart's reporting line is missing | M07 |
| Q02 | **answering** | Top hit is the right `Annual Leave 2026` table chunk, yet the model refused | Prompt/model check, M08 compare |
| Q27 | **answering** | The `Accounts` table chunk is rank 2, but the wide row loses its column headers for the model, which refused | M08 (reranker, then row-wise table chunks if still failing) |
| Q05 | **answering** | The right §4.2 chunk is rank 1; the model quoted "3 working days" (the threshold), not 14 days' notice | Model/prompt check |
| Q01 | **answering** | Correct 10 days from the memo, plus an invented "immediate supervisor approval" (partial) | Model/prompt check |
| Q12 | **answering** | Right rate RM 0.70/km, omits a condition (partial) | Model/prompt check |
