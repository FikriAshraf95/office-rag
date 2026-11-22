# Eval nemo-super-m08-norerank — 2026-11-21

- **Score: 26 / 32 (81%)** — 24 correct, 4 partial, 4 wrong
- Answer model `nemo-super`, judge `nemo-super`, provider `ilmu`, user `ben`
- Latency p50 404 ms, p95 630 ms; first token p50 296 ms
- Tokens per question: 2117 in, 22 out; cost per question: n/a (plan-quota model)

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
| vision | 1.5 / 2 | 75% |

## All questions

| Id | Verdict | Found | Sources | Latency | Reason |
|---|---|---|---|---|---|
| Q01 | partial | True | ok | 468 ms | The core fact of 10 consecutive working days is correct, but the answer incorrectly states 'with immediate supervisor approval' whereas the reference indicates that no HOD approval is needed for up to 10 days, implying supervisor approval may not be required or is insufficiently specified. |
| Q02 | wrong | False | miss | 334 ms | The answer claims the information is not found, but the reference states that 22 days per year is correct, so inventing unavailability is incorrect. |
| Q03 | wrong | False | miss | 285 ms | The reference answer states 14 days per year, but the system answer claims it could not find the information and invents a referral instead of stating the correct fact. |
| Q04 | correct | True | ok | 529 ms | The answer correctly states that up to 5 days can be carried forward and must be used by 30 April 2027, matching the reference and avoiding the outdated Handbook 2024 trap. |
| Q05 | wrong | True | ok | 404 ms | The system answer states 3 working days, but the reference requires at least 14 calendar days for leave of more than 3 working days. |
| Q06 | correct | True | ok | 532 ms | The answer correctly states the minimum of 3 days and specifies Tuesday, Wednesday, and Thursday as required office days, matching the reference answer. |
| Q07 | correct | True | ok | 400 ms | The answer states the correct core working hours as 10:00 to 16:00, matching the reference answer and avoiding the outdated 2024 trap. |
| Q08 | correct | True | ok | 322 ms | The answer states the correct yearly limit for outpatient medical claims as RM 1,500 per calendar year, matching the reference answer. |
| Q09 | correct | True | ok | 358 ms | The answer correctly states the notice period for a manager (M grade) who resigns as 2 months, matching the reference answer and avoiding the outdated 2024 trap. |
| Q10 | partial | True | ok | 572 ms | The answer correctly states the 20 working days limit with HOD and HR approval but omits the restriction that Bank Teratai systems may not be accessed from outside Malaysia, instead mentioning a vague client contract prohibition. |
| Q11 | correct | True | ok | 343 ms | The answer states the exact number of days and specifies they are consecutive, matching the reference. |
| Q12 | partial | True | ok | 354 ms | The core fact is correct, but the answer omits the condition about toll and parking with receipts. |
| Q13 | correct | True | ok | 443 ms | The answer correctly states the hotel limit per night for a business trip to Penang as RM 350, matching the reference answer exactly. |
| Q14 | correct | True | ok | 611 ms | The answer correctly states that business class requires flights over 6 hours and M grades or above, and that S2 (Senior) is below M1 and thus not eligible. |
| Q15 | correct | True | ok | 462 ms | The answer accurately states the 30-day submission deadline and the 60-day rejection rule, matching the reference exactly. |
| Q16 | correct | True | ok | 419 ms | The answer correctly states that both HOD and Finance must approve claims over RM 2,000, which includes RM 2,500. |
| Q17 | correct | True | ok | 384 ms | The answer states the correct minimum password length of 14 characters as per the reference. |
| Q18 | correct | True | ok | 638 ms | The answer accurately reflects the policy that Bank Teratai customer data is restricted and may not be entered into personal AI accounts like ChatGPT, and that only approved tools (Claude workspace and GitHub Copilot) are permitted. |
| Q19 | correct | True | ok | 537 ms | The answer matches the reference exactly in both the reporting channel and the required timeframe, including the after-hours procedure. |
| Q20 | correct | True | ok | 326 ms | The answer correctly states that Bank Teratai must be notified within 2 hours of a security incident, matching the reference. |
| Q21 | correct | True | ok | 630 ms | The answer includes all required conditions: booking at least 3 working days ahead through the account manager, completing a safety induction, and wearing safety boots and a high-visibility vest. |
| Q22 | correct | True | ok | 370 ms | The answer correctly states that Gemilang Capital data must be hosted in Malaysia or Singapore, matching the reference answer. |
| Q23 | correct | True | ok | 520 ms | The answer correctly states that Zainab Yusof is the account manager for Gemilang Capital and reports to Nurul Huda, Client Delivery Director. |
| Q24 | partial | True | ok | 474 ms | The system answer correctly identifies Hafiz Osman as the CFO but omits that the Finance team reports to Finance Manager Kumar Selvam, who in turn reports to Hafiz Osman. |
| Q25 | correct | True | ok | 406 ms | The answer correctly states Jason Wong as Head of Security reporting to Daniel Lim, who is identified as the Chief Technology Officer, matching the reference answer. |
| Q26 | correct | True | ok | 458 ms | The answer states the correct total number of people working on Bank Teratai projects as 15, matching the reference. |
| Q27 | wrong | False | miss | 383 ms | The answer invents that the information is not found, but the reference clearly states the contract ends on 31 December 2026, which should have been retrievable from the documents. |
| Q28 | correct | True | ok | 487 ms | System answer correctly states that no annual leave is needed on 29 Disember 2026 as it is a company holiday, matching the reference answer and its conditions. |
| Q29 | correct | True | ok | 343 ms | The system answer correctly states that annual leave is required on 28 and 31 December 2026, matching the reference answer. |
| Q30 | correct | False | ok | 99 ms | The answer correctly states that the information is not found in the documents and directs to HR, matching the reference answer. |
| Q31 | correct | False | ok | 124 ms | The answer correctly states that the information is not found in the documents and suggests contacting HR, as required by the reference. |
| Q32 | correct | True | ok | 332 ms | The answer correctly states that office parking is not reimbursed, matching the reference. |

## Failures and triage

Cause hint is automatic; confirm by hand as parsing, chunking, retrieval or answering.

| Id | Verdict | Question | Expected | Got | Cited | Reason | Cause hint |
|---|---|---|---|---|---|---|---|
| Q01 | partial | What is the maximum number of consecutive working days I can take in one leave application without HOD approval? | 10 consecutive working days (effective 1 Oct 2026). Longer needs HOD + HR approval. | 10 working days (with immediate supervisor approval) [3] | Memo_HR_2026-09_Leave_Policy_Amendment_scan.png | The core fact of 10 consecutive working days is correct, but the answer incorrectly states 'with immediate supervisor approval' whereas the reference indicates that no HOD approval is needed for up to 10 days, implying supervisor approval may not be required or is insufficiently specified. | answering (right source, wrong or incomplete answer) |
| Q02 | wrong | How many days of annual leave does a Grade M2 manager with 6 years of service get? | 22 days per year. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The answer claims the information is not found, but the reference states that 22 days per year is correct, so inventing unavailability is incorrect. | retrieval (gate or ranking) or answering (refused) |
| Q03 | wrong | How many annual leave days does a new Executive (E1) with 1 year of service get? | 14 days per year. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The reference answer states 14 days per year, but the system answer claims it could not find the information and invents a referral instead of stating the correct fact. | retrieval (gate or ranking) or answering (refused) |
| Q05 | wrong | How far in advance must I apply for 5 days of annual leave? | At least 14 calendar days in advance (leave of more than 3 working days). | At least 3 working days in advance. [1] | HR_Employee_Handbook_2026.pdf | The system answer states 3 working days, but the reference requires at least 14 calendar days for leave of more than 3 working days. | answering (right source, wrong or incomplete answer) |
| Q10 | partial | Can I work remotely from overseas, and for how long? | Yes, up to 20 working days per calendar year with HOD and HR approval. But Bank Teratai systems may not be accessed from outside Malaysia. | Employees may work remotely from outside Malaysia for a maximum of 20 working days per calendar year, subject to prior approval from the HOD and HR. However, client contracts may prohibit remote access from abroad (see the Client Engagement policy). [1] | HR_Employee_Handbook_2026.pdf | The answer correctly states the 20 working days limit with HOD and HR approval but omits the restriction that Bank Teratai systems may not be accessed from outside Malaysia, instead mentioning a vague client contract prohibition. | answering (right source, wrong or incomplete answer) |
| Q12 | partial | What is the mileage claim rate for using my own car? | RM 0.70 per km, plus toll and parking with receipts. | RM 0.70 per km [1] | Travel_and_Claims_SOP.md | The core fact is correct, but the answer omits the condition about toll and parking with receipts. | answering (right source, wrong or incomplete answer) |
| Q24 | partial | Who does the Finance team report to? | Finance Manager Kumar Selvam, who reports to CFO Hafiz Osman. | Hafiz Osman, Chief Financial Officer [1] | Org_Chart_2026.jpg | The system answer correctly identifies Hafiz Osman as the CFO but omits that the Finance team reports to Finance Manager Kumar Selvam, who in turn reports to Hafiz Osman. | answering (right source, wrong or incomplete answer) |
| Q27 | wrong | When does the Gemilang Capital contract end? | 31 December 2026. | I couldn't find this in the documents I have access to. Please contact HR, hr@serimaju.example. | - | The answer invents that the information is not found, but the reference clearly states the contract ends on 31 December 2026, which should have been retrievable from the documents. | retrieval (gate or ranking) or answering (refused) |
