# Pearson Press

An automated, black-and-white personal newspaper that collects trusted data,
creates original editorial coverage, lays out daily and Sunday editions, renders
print-ready PDFs, and submits approved editions for duplex printing.

Pearson Press is profile-driven. A publication profile selects sports, providers,
sections, teams, priorities, schedules, edition sizes, and delivery settings.
The planned Streamlit control panel edits those profiles; it does not contain
publishing logic. This keeps the core engine usable from the CLI, scheduler,
future web clients, and hosted multi-user deployments.

## Publication profiles

- Daily: 6 pages / 3 duplex sheets
- Sunday: 10-12 pages / 5-6 duplex sheets
- Special editions: event-driven and always an even page count

## Project map

- `config/` publication, source, sport, editorial, fantasy, and printer settings
- `src/pearson_press/` application code
- `src/pearson_press/dashboard/` optional Streamlit control panel
- `src/pearson_press/profiles/` portable, versioned personalization profiles
- `src/pearson_press/providers/` discoverable provider plug-ins and capabilities
- `templates/` reusable newspaper pages and components
- `assets/` brand, icon, font, and placeholder assets
- `data/` local runtime data, generated editions, archives, and print queue
- `tests/` unit, integration, fixture, and visual snapshot tests
- `scripts/` operator entry points and scheduler installers
- `docs/` architecture, policies, source notes, and operating runbooks

Implementation begins with the contracts in `domain/`, one end-to-end sport
adapter, the daily edition profile, PDF preflight, and manual printing.
