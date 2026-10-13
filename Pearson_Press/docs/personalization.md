# Personalization

A publication profile is the complete, portable description of one newspaper.
It controls enabled sports, providers, teams, leagues, sections, priorities,
edition sizes, time zone, data cutoffs, schedule, printer, and delivery targets.

The dashboard must never mutate global configuration when a user changes a
checkbox. It creates a validated profile revision. Each pipeline run stores the
exact profile revision used to build the edition.

Provider settings and credentials are separate. Profiles store provider IDs and
non-secret preferences; secrets remain in a secret backend. Provider availability
is distinct from provider enablement so a missing credential can be explained
without silently changing a user's choices.
