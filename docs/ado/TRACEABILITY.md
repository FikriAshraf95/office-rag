# Traceability — ADO stories → specs → milestones

Which spec sections implement each story, and which milestones build it. Keep this in step when a spec or milestone changes; reference the story in commits and PRs (`AB#1101` from GitHub, `#1101` in Azure Repos) so ADO links the work.

| Story | Title | Spec sections | Milestones |
|---|---|---|---|
| **F1100** | **Document library** | | |
| 1101 | Upload documents | [SPEC-03 §2](../specs/SPEC-03-ingestion.md) · [SPEC-09 §2](../specs/SPEC-09-security-and-access.md) · [SPEC-08 §4.1](../specs/SPEC-08-api-contract.md) · [SPEC-07 §6.1](../specs/SPEC-07-frontend.md) | [M01](../milestones/done/M01-upload-and-documents.md), [M05](../milestones/M05-frontend.md) |
| 1102 | See all documents and their processing status | [SPEC-07 §6.2](../specs/SPEC-07-frontend.md) · [SPEC-08 §4.2](../specs/SPEC-08-api-contract.md) | [M01](../milestones/done/M01-upload-and-documents.md), [M05](../milestones/M05-frontend.md) |
| 1103 | Correct document details and mark old versions | [SPEC-03 §1, §6.1](../specs/SPEC-03-ingestion.md) · [SPEC-08 §4.3](../specs/SPEC-08-api-contract.md) · [SPEC-07 §6.2](../specs/SPEC-07-frontend.md) | [M01](../milestones/done/M01-upload-and-documents.md) |
| 1104 | Delete a document | [SPEC-03 §7](../specs/SPEC-03-ingestion.md) · [SPEC-08 §4.4](../specs/SPEC-08-api-contract.md) | [M01](../milestones/done/M01-upload-and-documents.md) |
| 1105 | Open a document and see what the system read from it | [SPEC-07 §6.3](../specs/SPEC-07-frontend.md) · [SPEC-08 §4.5, §4.7](../specs/SPEC-08-api-contract.md) | [M01](../milestones/done/M01-upload-and-documents.md), [M02](../milestones/done/M02-ingestion.md) |
| **F1200** | **Document processing** | | |
| 1201 | Process documents in the background | [SPEC-03 §3](../specs/SPEC-03-ingestion.md) · [SPEC-06 §4–5](../specs/SPEC-06-ai-providers.md) · [SPEC-01 §3](../specs/SPEC-01-architecture.md) | [M02](../milestones/done/M02-ingestion.md) |
| 1202 | Read PDF and Word documents with their structure | [SPEC-03 §4, §5.1](../specs/SPEC-03-ingestion.md) | [M02](../milestones/done/M02-ingestion.md) |
| 1203 | Read Excel spreadsheets correctly | [SPEC-03 §5.2](../specs/SPEC-03-ingestion.md) | [M02](../milestones/done/M02-ingestion.md) |
| 1204 | Read scanned documents and images | [SPEC-03 §4](../specs/SPEC-03-ingestion.md) | [M02](../milestones/done/M02-ingestion.md) |
| 1205 | Understand diagrams such as org charts | [SPEC-03 §8](../specs/SPEC-03-ingestion.md) | [M07](../milestones/done/M07-vision-and-summaries.md) |
| 1206 | Detect old versions automatically | [SPEC-03 §6.1](../specs/SPEC-03-ingestion.md) | [M02](../milestones/done/M02-ingestion.md) |
| 1207 | Fill in document details automatically | [SPEC-03 §6, §8](../specs/SPEC-03-ingestion.md) | [M02](../milestones/done/M02-ingestion.md), [M07](../milestones/done/M07-vision-and-summaries.md) |
| 1208 | Replace a document with a new version of the file | [SPEC-03 §7](../specs/SPEC-03-ingestion.md) | [M08](../milestones/done/M08-reranker-and-reingest.md) |
| **F1300** | **Ask questions** | | |
| 1301 | Ask a question and see the answer appear as it is written | [SPEC-05 §1, §6](../specs/SPEC-05-answering.md) · [SPEC-07 §5.1–5.2, §5.6](../specs/SPEC-07-frontend.md) · [SPEC-00 §7](../specs/SPEC-00-overview.md) | [M04](../milestones/done/M04-answering.md), [M05](../milestones/M05-frontend.md) |
| 1302 | See where each answer comes from | [SPEC-05 §4](../specs/SPEC-05-answering.md) · [SPEC-07 §5.3–5.4](../specs/SPEC-07-frontend.md) | [M04](../milestones/done/M04-answering.md), [M05](../milestones/M05-frontend.md) |
| 1303 | Say so when the answer isn't in the documents | [SPEC-05 §5](../specs/SPEC-05-answering.md) · [SPEC-04 §4](../specs/SPEC-04-retrieval.md) | [M03](../milestones/done/M03-retrieval.md), [M04](../milestones/done/M04-answering.md) |
| 1304 | Use the latest rule when documents disagree | [SPEC-04 §1](../specs/SPEC-04-retrieval.md) · [SPEC-05 §2](../specs/SPEC-05-answering.md) | [M03](../milestones/done/M03-retrieval.md), [M04](../milestones/done/M04-answering.md) |
| 1305 | Ask in Bahasa Malaysia | [SPEC-05 §2, §5](../specs/SPEC-05-answering.md) · [SPEC-03 §6](../specs/SPEC-03-ingestion.md) · [SPEC-02 §3](../specs/SPEC-02-database-schema.md) | [M02](../milestones/done/M02-ingestion.md), [M04](../milestones/done/M04-answering.md) |
| 1306 | Ask follow-up questions | [SPEC-05 §1](../specs/SPEC-05-answering.md) · [SPEC-07 §5.6](../specs/SPEC-07-frontend.md) | [M04](../milestones/done/M04-answering.md), [M05](../milestones/M05-frontend.md) |
| 1307 | Clear messages when the AI service has a problem | [SPEC-06 §5](../specs/SPEC-06-ai-providers.md) · [SPEC-07 §5.5](../specs/SPEC-07-frontend.md) | [M04](../milestones/done/M04-answering.md), [M05](../milestones/M05-frontend.md) |
| **F1400** | **Access and security** | | |
| 1401 | Restrict documents to groups | [SPEC-09 §3–4](../specs/SPEC-09-security-and-access.md) · [SPEC-04 §1](../specs/SPEC-04-retrieval.md) · [SPEC-08 §2](../specs/SPEC-08-api-contract.md) · [SPEC-07 §8](../specs/SPEC-07-frontend.md) | [M00](../milestones/done/M00-foundation.md), [M01](../milestones/done/M01-upload-and-documents.md), [M02](../milestones/done/M02-ingestion.md), [M03](../milestones/done/M03-retrieval.md), [M04](../milestones/done/M04-answering.md) |
| 1402 | Only accept safe uploads | [SPEC-09 §2](../specs/SPEC-09-security-and-access.md) | [M01](../milestones/done/M01-upload-and-documents.md) |
| 1403 | Protect keys and data | [SPEC-09 §1, §5–6](../specs/SPEC-09-security-and-access.md) | [M00](../milestones/done/M00-foundation.md), [M99](../milestones/done/M99-release-and-demo.md) |
| 1404 | Ignore instructions hidden inside documents | [SPEC-09 §7](../specs/SPEC-09-security-and-access.md) · [SPEC-05 §2](../specs/SPEC-05-answering.md) | [M04](../milestones/done/M04-answering.md), [M05](../milestones/M05-frontend.md) |
| **F1500** | **Answer quality, usage and cost** | | |
| 1501 | Measure answer accuracy on a test set | [SPEC-10 §5](../specs/SPEC-10-testing-and-eval.md) | [M06](../milestones/done/M06-evaluation.md), [M99](../milestones/done/M99-release-and-demo.md) |
| 1502 | Track AI usage and cost | [SPEC-06 §6](../specs/SPEC-06-ai-providers.md) · [SPEC-07 §7](../specs/SPEC-07-frontend.md) · [SPEC-08 §7](../specs/SPEC-08-api-contract.md) | [M04](../milestones/done/M04-answering.md), [M05](../milestones/M05-frontend.md) |
| 1503 | Improve result ranking | [SPEC-04 §6](../specs/SPEC-04-retrieval.md) | [M08](../milestones/done/M08-reranker-and-reingest.md) |
| **F1600** | **Platform and operations** | | |
| 1601 | Run the whole system with one command | [SPEC-11 §1–4](../specs/SPEC-11-deployment.md) | [M99](../milestones/done/M99-release-and-demo.md) |
| 1602 | Switch AI provider without code changes | [SPEC-06 §1, §7](../specs/SPEC-06-ai-providers.md) | [M00](../milestones/done/M00-foundation.md), [M99](../milestones/done/M99-release-and-demo.md) |
| 1603 | Public preview over the internet | [SPEC-11 §5](../specs/SPEC-11-deployment.md) | [M100](../milestones/M100-public-preview.md) |
