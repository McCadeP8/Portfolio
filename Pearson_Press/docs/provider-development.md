# Provider Development

Every provider supplies a manifest with a stable ID, display name, provider
kind, supported capabilities, supported regions or leagues, authentication
requirements, attribution text, licensing notes, and health-check behavior.

Adapters implement shared contracts and return canonical domain objects with
provenance. They must not write directly to layouts or user profiles. Contract
tests ensure adapters remain interchangeable.
