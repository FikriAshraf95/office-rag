# Eval nemo-super-m08-rerank-min0005 — 2026-11-21

- **Score: 27 / 32 (84%)** — 24 correct, 6 partial, 2 wrong
- Answer model `nemo-super`, judge `nemo-super`, provider `ilmu`, user `ben`
- Latency p50 899 ms, p95 3852 ms; first token p50 600 ms
- Tokens per question: 1467 in, 55 out; cost per question: n/a (plan-quota model)

## By category

| Category | Score | % |
|---|---|---|
| multi-hop | 1 / 2 | 50% |
| multi-hop / guardrail | 0.5 / 1 | 50% |
| multi-hop / vision | 1 / 1 | 100% |
| multilingual (Malay question) | 1 / 1 | 100% |
| multilingual doc | 1 / 1 | 100% |
| not found | 2 / 2 | 100% |
| override / OCR | 1.5 / 2 | 75% |
| policy | 4.5 / 6 | 75% |
| policy (negative) | 1 / 1 | 100% |
| reasoning | 2 / 2 | 100% |
| table aggregation | 1 / 1 | 100% |
| table lookup | 5 / 6 | 83% |
| version | 4 / 4 | 100% |
| vision | 1.5 / 2 | 75% |

## All questions

| Id | Verdict | Found | Sources | Latency | Reason |
|---|---|---|---|---|---|
| Q01 | partial | True | ok | 3852 ms | The answer correctly states the 10-day maximum but incorrectly adds 'with immediate supervisor approval' instead of noting that HOD + HR approval is required for longer leave. |
| Q02 | correct | True | ok | 1234 ms | The answer correctly states 22 days per year, matching the reference answer, and explains the condition of being in Manager grade band M1-M3 with over 5 years of service. |
| Q03 | wrong | False | miss | 6474 ms | The reference answer states that a new Executive (E1) with 1 year of service gets 14 days of annual leave per year, but the system answer claims it could not find this information and suggests contacting HR, which is incorrect as the information is present in the documents. |
| Q04 | correct | True | ok | 1059 ms | The answer correctly states that up to 5 days can be carried forward and must be used by 30 April 2027, matching the reference answer and avoiding the outdated Handbook 2024 trap. |
| Q05 | wrong | True | ok | 1094 ms | The answer states 3 working days in advance, but the reference requires at least 14 calendar days in advance for leave of more than 3 working days. |
| Q06 | correct | True | ok | 772 ms | The answer correctly states the minimum of 3 days and specifies Tuesday, Wednesday, and Thursday as required office days, matching the reference answer. |
| Q07 | correct | True | ok | 997 ms | The answer correctly states the core working hours as 10:00 to 16:00, matching the reference answer. |
| Q08 | correct | True | ok | 550 ms | The answer correctly states the yearly limit for outpatient medical claims as RM 1,500 per calendar year, which matches the reference answer. |
| Q09 | correct | True | ok | 548 ms | The answer correctly states the notice period as 2 months, matching the reference answer and avoiding the outdated 2024 trap. |
| Q10 | partial | True | ok | 851 ms | The answer correctly states the 20-day limit and approval requirement but omits the restriction that Bank Teratai systems may not be accessed from outside Malaysia, which is a key condition from the reference. |
| Q11 | correct | True | ok | 940 ms | The answer states the right fact from the policy: 7 consecutive days of paternity leave. |
| Q12 | partial | True | ok | 1481 ms | The answer correctly states the mileage rate but omits the condition that toll and parking costs are claimable with receipts. |
| Q13 | correct | True | ok | 469 ms | The answer correctly states the hotel limit per night for a business trip to Penang as RM 350 per night. |
| Q14 | correct | True | ok | 899 ms | The system answer correctly states that business class is only for flights over 6 hours and for M grades and above, and that S2 (Senior) is below M1, so not eligible, matching the reference. |
| Q15 | correct | True | ok | 946 ms | The answer matches the reference exactly, stating the 30-day submission deadline and the 60-day rejection rule. |
| Q16 | correct | True | ok | 981 ms | The answer correctly states that both HOD and Finance must approve claims over RM 2,000, which includes RM 2,500, matching the reference. |
| Q17 | correct | True | ok | 445 ms | The system answer correctly states the minimum password length is 14 characters, matching the reference answer. |
| Q18 | partial | True | ok | 918 ms | The system answer correctly states that pasting Bank Teratai customer data into ChatGPT on a personal account is not allowed, but it introduces unrelated policies about personal devices in server rooms and data residency in Malaysia, which are not in the reference answer and make the response vague and off-focus. |
| Q19 | correct | True | ok | 623 ms | The answer matches the reference exactly in both the reporting channel and the required timeframe, including the after-hours procedure. |
| Q20 | correct | True | ok | 482 ms | The answer states the correct 2-hour notification timeframe, matching the reference answer exactly. |
| Q21 | partial | True | ok | 988 ms | The answer correctly mentions the safety induction and required PPE but omits the requirement to book at least 3 working days ahead through the account manager and the prohibition on USB drives on the OT network. |
| Q22 | correct | True | ok | 1048 ms | The answer correctly states that Gemilang Capital data must be hosted in Malaysia or Singapore, matching the reference. |
| Q23 | correct | True | ok | 1147 ms | The answer states the correct facts from the reference answer: Zainab Yusof is the account manager for Gemilang Capital and she reports to Nurul Huda, Client Delivery Director. |
| Q24 | partial | True | ok | 753 ms | The answer correctly states that Kumar Selvam is the Finance Manager, but omits that he reports to CFO Hafiz Osman, which is a key condition in the reference. |
| Q25 | correct | True | ok | 607 ms | The answer correctly states Jason Wong is Head of Security and reports to Daniel Lim, CTO, matching the reference. |
| Q26 | correct | True | ok | 907 ms | The answer correctly states the total number of people working on Bank Teratai projects as 15, matching the reference answer. |
| Q27 | correct | True | ok | 510 ms | The answer states the correct end date of the Gemilang Capital contract as 31 December 2026, matching the reference. |
| Q28 | correct | True | ok | 719 ms | Jawapan menyatakan dengan betul bahawa 29 Disember 2026 adalah cuti syarikat dan cuti tahunan tidak diperlukan, sesuai dengan rujukan. |
| Q29 | correct | True | ok | 1109 ms | The answer correctly states that 28 and 31 December 2026 require annual leave application, matching the reference answer exactly. |
| Q30 | correct | False | ok | 463 ms | The system answer correctly states it could not find the information and advises contacting HR, matching the reference answer. |
| Q31 | correct | False | ok | 833 ms | The answer correctly states the information is not in the documents and appropriately suggests contacting HR without guessing. |
| Q32 | correct | True | ok | 566 ms | The answer correctly states that office parking is not reimbursed, matching the reference answer. |

## Failures and triage

Cause hint is automatic; confirm by hand as parsing, chunking, retrieval or answering.

| Id | Verdict | Question | Expected | Got | Cited | Reason | Cause hint |
|---|---|---|---|---|---|---|---|
| Q01 | partial | What is the maximum number of consecutive working days I can take in one leave application without HOD approval? | 10 consecutive working days (effective 1 Oct 2026). Longer needs HOD + HR approval. | 10 working days (with immediate supervisor approval) [2] | Memo_HR_2026-09_Leave_Policy_Amendment_scan.png | The answer correctly states the 10-day maximum but incorrectly adds 'with immediate supervisor approval' instead of noting that HOD + HR approval is required for longer leave. | answering (right source, wrong or incomplete answer) |
| Q03 | wrong | How many annual leave days does a new Executive (E1) with 1 year of service get? | 14 days per year. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The reference answer states that a new Executive (E1) with 1 year of service gets 14 days of annual leave per year, but the system answer claims it could not find this information and suggests contacting HR, which is incorrect as the information is present in the documents. | retrieval (gate or ranking) or answering (refused) |
| Q05 | wrong | How far in advance must I apply for 5 days of annual leave? | At least 14 calendar days in advance (leave of more than 3 working days). | At least 3 working days in advance. [1] | HR_Employee_Handbook_2026.pdf | The answer states 3 working days in advance, but the reference requires at least 14 calendar days in advance for leave of more than 3 working days. | answering (right source, wrong or incomplete answer) |
| Q10 | partial | Can I work remotely from overseas, and for how long? | Yes, up to 20 working days per calendar year with HOD and HR approval. But Bank Teratai systems may not be accessed from outside Malaysia. | Yes, you may work remotely from outside Malaysia for a maximum of 20 working days per calendar year, subject to prior approval from your HOD and HR. [1] | HR_Employee_Handbook_2026.pdf | The answer correctly states the 20-day limit and approval requirement but omits the restriction that Bank Teratai systems may not be accessed from outside Malaysia, which is a key condition from the reference. | answering (right source, wrong or incomplete answer) |
| Q12 | partial | What is the mileage claim rate for using my own car? | RM 0.70 per km, plus toll and parking with receipts. | RM 0.70 per km [1] | Travel_and_Claims_SOP.md | The answer correctly states the mileage rate but omits the condition that toll and parking costs are claimable with receipts. | answering (right source, wrong or incomplete answer) |
| Q18 | partial | Can I paste Bank Teratai customer data into ChatGPT on my personal account to summarise it? | No. Client production data is Restricted and may only be used with approved AI tools (company Claude workspace, company GitHub Copilot); personal AI accounts are never approved for client data. | No. Personal devices (including personal phones) are not allowed in BTB server rooms, and data residency requires client data to remain in Malaysia only. Pasting Bank Teratai customer data into ChatGPT on a personal account would violate these policies, as it involves transferring data outside appro | Client_Engagement_and_Data_Handling_Policy.docx | The system answer correctly states that pasting Bank Teratai customer data into ChatGPT on a personal account is not allowed, but it introduces unrelated policies about personal devices in server rooms and data residency in Malaysia, which are not in the reference answer and make the response vague and off-focus. | answering (right source, wrong or incomplete answer) |
| Q21 | partial | What do I need before visiting the Pelita Precision factory? | Book at least 3 working days ahead through the account manager (Arjun Pillai), complete a safety induction, and wear safety boots and a high-visibility vest. No USB drives on the OT network. | You need a safety induction before the first visit and must wear personal protective equipment (safety boots and a high-visibility vest) on the factory floor. [1] | Client_Engagement_and_Data_Handling_Policy.docx | The answer correctly mentions the safety induction and required PPE but omits the requirement to book at least 3 working days ahead through the account manager and the prohibition on USB drives on the OT network. | answering (right source, wrong or incomplete answer) |
| Q24 | partial | Who does the Finance team report to? | Finance Manager Kumar Selvam, who reports to CFO Hafiz Osman. | The Finance team reports to Kumar Selvam, Finance Manager. [1] | Org_Chart_2026.jpg | The answer correctly states that Kumar Selvam is the Finance Manager, but omits that he reports to CFO Hafiz Osman, which is a key condition in the reference. | answering (right source, wrong or incomplete answer) |
