# Mock Scenarios

Set `MOCK_SCENARIO` to one of these deterministic scenarios while Phase 1 uses the mock provider:

| Scenario | Purpose |
| --- | --- |
| `no_flights` | Empty/waiting UI state. |
| `one_commercial` | Simple primary-card review with one eligible commercial aircraft. |
| `multiple_competing` | Default selection and nearby-list review with commercial and private aircraft. |
| `missing_route` | Aircraft with valid telemetry and limited enrichment. |
| `private_aircraft` | Default commercial filter excludes registration-like traffic. |
| `stale_provider` | Provider returns only stale aircraft so the UI shows waiting/stale context. |
| `provider_recovery` | First poll is stale; later polls recover to normal traffic. |
