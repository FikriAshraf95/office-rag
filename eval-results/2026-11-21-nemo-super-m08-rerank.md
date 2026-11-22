# Eval nemo-super-m08-rerank — 2026-11-21

- **Score: 28 / 32 (88%)** — 26 correct, 4 partial, 2 wrong
- Answer model `nemo-super`, judge `nemo-super`, provider `ilmu`, user `ben`
- Latency p50 502 ms, p95 2632 ms; first token p50 406 ms
- Tokens per question: 734 in, 52 out; cost per question: n/a (plan-quota model)

## By category

| Category | Score | % |
|---|---|---|
| multi-hop | 1.5 / 2 | 75% |
| multi-hop / guardrail | 0 / 1 | 0% |
| multi-hop / vision | 1 / 1 | 100% |
| multilingual (Malay question) | 1 / 1 | 100% |
| multilingual doc | 1 / 1 | 100% |
| not found | 2 / 2 | 100% |
| override / OCR | 2 / 2 | 100% |
| policy | 5.5 / 6 | 92% |
| policy (negative) | 1 / 1 | 100% |
| reasoning | 1 / 2 | 50% |
| table aggregation | 1 / 1 | 100% |
| table lookup | 5.5 / 6 | 92% |
| version | 4 / 4 | 100% |
| vision | 1.5 / 2 | 75% |

## All questions

| Id | Verdict | Found | Sources | Latency | Reason |
|---|---|---|---|---|---|
| Q01 | correct | True | ok | 2632 ms | The answer correctly states the maximum of 10 consecutive working days as per the memo, without omitting conditions or falling for outdated handbook values. |
| Q02 | correct | True | ok | 882 ms | The answer correctly states 22 days and references the current 2026 entitlement table, avoiding the outdated 2024 handbook trap. |
| Q03 | partial | True | ok | 6336 ms | The core fact is correct (14 days), but the answer includes unnecessary confusion about pro-rating and rounded-down rules that are not needed for exactly 12 months of service, making the reasoning weak and vague. |
| Q04 | correct | True | ok | 1097 ms | The system answer correctly states that up to 5 days can be carried forward and must be used by 30 April 2027, matching the reference answer and avoiding the trap in Handbook 2024. |
| Q05 | correct | True | ok | 492 ms | The answer correctly states that at least 14 calendar days in advance is required for leave of more than 3 working days, which applies to 5 days of annual leave. |
| Q06 | correct | True | ok | 605 ms | The answer correctly states the minimum of 3 office days per week and specifies Tuesday, Wednesday, and Thursday as required, matching the reference answer exactly. |
| Q07 | correct | True | ok | 468 ms | The answer correctly states the core working hours as 10:00 to 16:00, matching the reference answer and avoiding the outdated 2024 trap. |
| Q08 | correct | True | ok | 421 ms | The answer correctly states the yearly limit for outpatient medical claims as RM 1,500 per calendar year, matching the reference and avoiding the outdated RM 1,000 trap. |
| Q09 | correct | True | ok | 417 ms | The system answer correctly states the notice period for a manager (M grade) who resigns as 2 months, matching the reference answer and avoiding the outdated 2024 trap. |
| Q10 | correct | True | ok | 867 ms | The answer correctly states the 20-working-day limit with HOD and HR approval and notes the restriction on accessing Bank Teratai systems from outside Malaysia, matching the reference answer and notes. |
| Q11 | correct | True | ok | 544 ms | The answer correctly states 7 consecutive days of paternity leave, matching the reference exactly. |
| Q12 | partial | True | ok | 593 ms | The core fact is correct, but the answer omits the condition 'plus toll and parking with receipts'. |
| Q13 | correct | True | ok | 432 ms | The system answer correctly states the hotel limit per night for a business trip to Penang as RM 350, matching the reference answer. |
| Q14 | wrong | False | miss | 299 ms | The answer claims inability to find the information, but the reference clearly states the policy and trip details, so inventing uncertainty is incorrect. |
| Q15 | correct | True | ok | 563 ms | The system answer correctly states both the 30-day submission deadline and the 60-day rejection rule, matching the reference exactly. |
| Q16 | correct | True | ok | 506 ms | The answer correctly states that both HOD and Finance must approve a claim of RM 2,500, matching the reference answer for claims over RM 2,000. |
| Q17 | correct | True | ok | 502 ms | The answer correctly states the minimum password length as 14 characters, which matches the reference answer. |
| Q18 | wrong | False | miss | 250 ms | The answer incorrectly claims the information is not in the documents and invents a suggestion to contact HR, while the reference clearly states that personal AI accounts are never approved for client data. |
| Q19 | correct | True | ok | 561 ms | The answer matches the reference exactly: email security@serimaju.example within 1 hour and call IT on-call at ext. 2222 outside office hours. |
| Q20 | correct | True | ok | 437 ms | The system answer correctly states that Bank Teratai must be notified within 2 hours of a security incident, matching the reference answer. |
| Q21 | partial | True | ok | 656 ms | The answer includes safety induction and PPE requirements but omits the need to book at least 3 working days ahead through Arjun Pillai and the prohibition on USB drives on the OT network. |
| Q22 | correct | True | ok | 469 ms | The answer correctly states that Gemilang Capital data must be hosted in Malaysia or Singapore, matching the reference answer. |
| Q23 | correct | True | ok | 580 ms | The answer correctly states the account manager and her reporting line as per the reference. |
| Q24 | partial | True | ok | 502 ms | The answer correctly identifies Kumar Selvam as the Finance Manager to whom the team reports, but omits that he reports to CFO Hafiz Osman, which is a key condition in the reference. |
| Q25 | correct | True | ok | 459 ms | The answer correctly identifies Jason Wong as the Head of Security and states he reports to Daniel Lim, who is the Chief Technology Officer, matching the reference. |
| Q26 | correct | True | ok | 465 ms | The answer correctly states the total number of people working on Bank Teratai projects as 15, which matches the reference answer. |
| Q27 | correct | True | ok | 465 ms | The answer provides the correct end date for the Gemilang Capital contract as 31 December 2026, which matches the reference answer. |
| Q28 | correct | True | ok | 646 ms | The answer correctly states that no annual leave is required on 29 December 2026 as it is a company holiday not deducted from annual leave, matching the reference answer. |
| Q29 | correct | True | ok | 597 ms | The answer correctly states the days requiring annual leave application during the year-end closure as 28 and 31 December 2026, matching the reference answer. |
| Q30 | correct | False | ok | 269 ms | The answer correctly states that the information is not found and suggests contacting HR as instructed. |
| Q31 | correct | False | ok | 368 ms | The answer correctly states that the information is not found in the documents and appropriately suggests contacting HR without guessing. |
| Q32 | correct | True | ok | 404 ms | The answer matches the reference answer by stating that office parking is not reimbursed, which is a fact from the policy. |

## Failures and triage

Cause hint is automatic; confirm by hand as parsing, chunking, retrieval or answering.

| Id | Verdict | Question | Expected | Got | Cited | Reason | Cause hint |
|---|---|---|---|---|---|---|---|
| Q03 | partial | How many annual leave days does a new Executive (E1) with 1 year of service get? | 14 days per year. | 7 days. New joiners: entitlement is pro-rated by completed months of service in the first year (entitlement × months ÷ 12), rounded down to the nearest half day. Executive (E1-E3) with less than 2 years gets 14 days. 14 × 12 ÷ 12 = 14 days for full year, but for 1 year (12 months) service: 14 × 12 ÷ | Leave_Entitlement_by_Grade_2026.xlsx | The core fact is correct (14 days), but the answer includes unnecessary confusion about pro-rating and rounded-down rules that are not needed for exactly 12 months of service, making the reasoning weak and vague. | answering (right source, wrong or incomplete answer) |
| Q12 | partial | What is the mileage claim rate for using my own car? | RM 0.70 per km, plus toll and parking with receipts. | RM 0.70 per km [1] | Travel_and_Claims_SOP.md | The core fact is correct, but the answer omits the condition 'plus toll and parking with receipts'. | answering (right source, wrong or incomplete answer) |
| Q14 | wrong | Can a Senior (S2) engineer fly business class to London? | No. Business class is only for flights over 6 hours AND for M grades and above; S2 flies economy. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The answer claims inability to find the information, but the reference clearly states the policy and trip details, so inventing uncertainty is incorrect. | retrieval (gate or ranking) or answering (refused) |
| Q18 | wrong | Can I paste Bank Teratai customer data into ChatGPT on my personal account to summarise it? | No. Client production data is Restricted and may only be used with approved AI tools (company Claude workspace, company GitHub Copilot); personal AI accounts are never approved for client data. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The answer incorrectly claims the information is not in the documents and invents a suggestion to contact HR, while the reference clearly states that personal AI accounts are never approved for client data. | retrieval (gate or ranking) or answering (refused) |
| Q21 | partial | What do I need before visiting the Pelita Precision factory? | Book at least 3 working days ahead through the account manager (Arjun Pillai), complete a safety induction, and wear safety boots and a high-visibility vest. No USB drives on the OT network. | You need a safety induction before the first visit and must wear personal protective equipment (safety boots and a high-visibility vest) on the factory floor. [1] | Client_Engagement_and_Data_Handling_Policy.docx | The answer includes safety induction and PPE requirements but omits the need to book at least 3 working days ahead through Arjun Pillai and the prohibition on USB drives on the OT network. | answering (right source, wrong or incomplete answer) |
| Q24 | partial | Who does the Finance team report to? | Finance Manager Kumar Selvam, who reports to CFO Hafiz Osman. | The Finance team reports to Kumar Selvam, Finance Manager. [1] | Org_Chart_2026.jpg | The answer correctly identifies Kumar Selvam as the Finance Manager to whom the team reports, but omits that he reports to CFO Hafiz Osman, which is a key condition in the reference. | answering (right source, wrong or incomplete answer) |
