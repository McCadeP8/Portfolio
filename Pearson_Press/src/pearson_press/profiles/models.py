"""Profile identity, coverage, providers, editions, schedule, and delivery models."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PublicationProfile:
    """A versioned description of one personalized newspaper."""

    profile_id: str
    name: str
    revision: int
    timezone: str
    enabled_sports: frozenset[str] = field(default_factory=frozenset)
    enabled_sections: frozenset[str] = field(default_factory=frozenset)
    enabled_providers: frozenset[str] = field(default_factory=frozenset)
    favorite_teams: tuple[str, ...] = ()
    favorite_topics: tuple[str, ...] = ()
