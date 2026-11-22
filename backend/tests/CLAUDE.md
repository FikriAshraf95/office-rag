# Test rules (`backend/tests/`)

Host and conventions: [SPEC-10 §1–3](../../docs/specs/SPEC-10-testing-and-eval.md).

- **Name tests after spec checks:** `test_spec04_ac02_superseded_never_retrieved`. One test per numbered check (more if needed, same prefix). Plain names for extra tests.
- Files by spec: `tests/spec03/test_ingestion_*.py`, `tests/spec04/…`; invariants in `tests/invariants/`.
- `AI_PROVIDER=fake` always. The network guard (`pytest-socket`) is on: a test that needs ILMU is wrong. Script fakes with `fake_chat.script([...])` or make them raise `ProviderError(...)`.
- Real Postgres (`rag_test`, port 5433). Each test runs in a rolled-back transaction; worker and concurrency tests use the `committed_db` fixture, which truncates afterwards.
- Run the worker step with `await process_one_job(session)`; never start the loop in tests.
- Docling-heavy tests carry `@pytest.mark.docling`. Keep fixtures tiny; Serimaju copies live in `tests/fixtures/serimaju/`.
- Use the `client` fixture (`X-Demo-User: ben`) and `client_as("aisyah")` for other users.
- The private-marker document is `tests/fixtures/private_salary_bands.md` (`access_groups = {hr-restricted}`). Any new read path gets an invariant test that asserts `ZQX-PRIVATE-7` is absent for `ben`.
- Assert on error `code`, never on `detail` text.
- Don't mock the database or `ingestion/service.py`; mock only at the provider boundary (fakes) and HTTP transport (for provider client tests).
