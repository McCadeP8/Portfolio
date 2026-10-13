# Architecture

The system is divided into ingestion, normalization, storage, editorial
selection, original writing, graphics, publication layout, PDF preflight,
printing, archiving, and monitoring. Sources and sports are adapters behind
shared contracts so they can fail, change, and be tested independently.

## Product boundary

The publishing engine is independent of Streamlit. User interfaces call
application services, which validate and save versioned publication profiles.
The nightly pipeline receives a profile snapshot and builds deterministically
from that snapshot. A saved edition therefore remains reproducible even when a
user later changes dashboard settings.

## Extensibility

Sport desks, news publishers, data feeds, fantasy platforms, renderers, and
delivery targets expose capability manifests and register through stable
interfaces. Dashboard controls are generated from those manifests rather than
hard-coded provider names. A new provider can therefore appear as an available
checkbox without requiring edits to the dashboard.

## Growth path

The first deployment uses a local profile and SQLite. Repository, secret,
authentication, scheduling, and object-storage interfaces keep the domain and
publishing pipeline independent of those choices. A hosted version may use
PostgreSQL, object storage, isolated secrets, per-user time zones, and workers
without replacing editorial or layout code.
