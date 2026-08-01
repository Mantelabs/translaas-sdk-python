# Live API integration tests

Optional tests against a real Translaas delivery API. They are **excluded from default CI** and skip automatically when `TRANSLAAS_API_KEY` is unset.

## Fixtures

Aligned with [translaas-sdk-examples](https://github.com/Mantelabs/translaas-sdk-examples) (`translaas_sdk_samples_strings.csv`):

| Field | Value |
|-------|-------|
| Project | `translaas-sdk-samples` |
| Groups | `common`, `messages` |
| Entries | `welcome.message`, `item` (plural) |
| Language | `en` (+ `fr`, `es`, `de` for locale checks) |

## Environment

| Variable | Required | Default |
|----------|----------|---------|
| `TRANSLAAS_API_KEY` | Yes (to run) | — |
| `TRANSLAAS_BASE_URL` | No | `https://api.translaas.local` |
| `TRANSLAAS_DEFAULT_PROJECT` | No | `translaas-sdk-samples` |

Local Docker (`platform/translaas`, profile `core`) serves the sample project at `https://api.translaas.local`. The SDK disables TLS verification for these tests (`verify=False`) to support self-signed certificates.

## Run locally

```bash
# PowerShell
$env:TRANSLAAS_API_KEY = "your-key"
$env:TRANSLAAS_BASE_URL = "https://api.translaas.local"
make test-integration

# Or directly
pytest -m live --no-cov -v
```

Without `TRANSLAAS_API_KEY`, live tests are **skipped** (exit code 0).

## Test matrix

- `get_entry` — existing, plural, not-found, invalid key
- `get_group` — existing, format, missing group/project
- `get_project` — existing, format, not-found, multi-group walk (metadata keys excluded)
- `get_project_locales` — existing, common locales, not-found
- `validate_api_key` — valid key, resolved default project
- Error scenarios — invalid key, bad URL, timeout, not-found
- `TranslaasService.t()` — explicit language

## Platform notes

- Mantelabs returns **HTTP 404** for missing SDK resources (not 204). Tests soft-skip on 404 when fixtures are not seeded.
- When the API is unreachable, tests skip with a hint to start Docker or adjust `TRANSLAAS_BASE_URL`.

## GitHub Actions

Run manually via **Integration Tests** workflow (`workflow_dispatch`) after configuring repository secrets `TRANSLAAS_API_KEY` and `TRANSLAAS_BASE_URL`.
