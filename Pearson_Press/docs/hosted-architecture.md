# Hosted Architecture

The local-first build should preserve clear seams for authentication, tenant
isolation, profile repositories, secret storage, databases, object storage,
job queues, rate limiting, observability, billing, and multiple delivery targets.

These are interfaces and boundaries, not immediate infrastructure requirements.
The personal edition should stay simple while avoiding assumptions that make a
future hosted service unsafe or require rewriting the publishing engine.
