# ADR 0001: Provider Boundary

Use provider classes to isolate mock, Airplanes.live, and future receiver behavior. Provider-specific payloads must be normalized into domain models before selection, persistence, or public serialization.
