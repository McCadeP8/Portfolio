"""Provider metadata used for discovery, validation, and dashboard controls."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ProviderManifest:
    """Public, non-secret description of a provider plug-in."""

    provider_id: str
    display_name: str
    kind: str
    capabilities: frozenset[str] = field(default_factory=frozenset)
    authentication: str = "none"
    attribution_required: bool = False
    licensing_review_required: bool = False
