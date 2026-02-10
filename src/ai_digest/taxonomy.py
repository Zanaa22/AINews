"""30-category taxonomy and severity rubric constants."""

from __future__ import annotations

from enum import IntEnum

# ---------------------------------------------------------------------------
# 30-category taxonomy
# ---------------------------------------------------------------------------

CATEGORIES: dict[int, str] = {
    1: "New foundation model release",
    2: "Model upgrade (quality/latency/context)",
    3: "New modality (vision/audio/video/3D)",
    4: "Fine-tuning/customization updates",
    5: "Inference & serving (speed/runtimes)",
    6: "Pricing & billing changes",
    7: "Rate limits/quotas/tiers",
    8: "Deprecations/breaking changes",
    9: "SDK releases/updates",
    10: "API changes (endpoints/auth/schemas)",
    11: "Agents frameworks/orchestration",
    12: "Tool-use/function calling/integrations",
    13: "RAG/retrieval tooling",
    14: "Embeddings & reranking",
    15: "Evaluation/benchmarks/evals",
    16: "Datasets (new/updated/licensing)",
    17: "Safety/alignment features",
    18: "Policy/compliance/governance",
    19: "Security incidents/vuln disclosures",
    20: "Privacy changes",
    21: "Open-source model/tool releases",
    22: "New developer products (dashboards/playgrounds)",
    23: "Enterprise features (SSO/RBAC/audit logs)",
    24: "Edge/on-device AI",
    25: "Hardware accelerators/drivers",
    26: "Training infrastructure/distributed systems",
    27: "LLMOps/monitoring/tracing",
    28: "App launches (consumer/prosumer)",
    29: "Funding/M&A/partnerships",
    30: "Reliability/outages/status updates",
}

CATEGORY_NAMES: list[str] = list(CATEGORIES.values())
CATEGORY_NAME_SET: set[str] = set(CATEGORY_NAMES)

# ---------------------------------------------------------------------------
# Section routing: category name → digest section
# ---------------------------------------------------------------------------

SECTION_DEVELOPER: set[str] = {
    "Deprecations/breaking changes",
    "SDK releases/updates",
    "API changes (endpoints/auth/schemas)",
    "Agents frameworks/orchestration",
    "Tool-use/function calling/integrations",
}

SECTION_MODELS: set[str] = {
    "New foundation model release",
    "Model upgrade (quality/latency/context)",
    "New modality (vision/audio/video/3D)",
    "Fine-tuning/customization updates",
    "Inference & serving (speed/runtimes)",
    "Embeddings & reranking",
    "Evaluation/benchmarks/evals",
    "Open-source model/tool releases",
}

SECTION_PRICING: set[str] = {
    "Pricing & billing changes",
    "Rate limits/quotas/tiers",
}

SECTION_INCIDENTS: set[str] = {
    "Security incidents/vuln disclosures",
    "Reliability/outages/status updates",
}

# ---------------------------------------------------------------------------
# Severity enum
# ---------------------------------------------------------------------------


class Severity(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


SEVERITY_LABELS: dict[int, str] = {
    Severity.HIGH: "HIGH",
    Severity.MEDIUM: "MEDIUM",
    Severity.LOW: "LOW",
}

# ---------------------------------------------------------------------------
# ImpactScore weights  (sum of positive weights ≈ 0.95, penalty 0.05)
# ---------------------------------------------------------------------------

IMPACT_WEIGHTS = {
    "trust": 0.20,
    "severity": 0.25,
    "user_match": 0.15,
    "recency": 0.15,
    "breadth": 0.10,
    "novelty": 0.10,
    "spam_dupe_penalty": 0.05,
}

# Trust tier → normalised score
TRUST_SCORES: dict[int, float] = {
    1: 1.0,
    2: 0.7,
    3: 0.4,
    4: 0.2,
}

# Severity → normalised score
SEVERITY_SCORES: dict[str, float] = {
    "HIGH": 1.0,
    "MEDIUM": 0.5,
    "LOW": 0.15,
}

# Recency decay parameter  (exp(-lambda * hours_old))
RECENCY_LAMBDA: float = 0.03

# Section quotas (max items per section, 0 = unlimited)
SECTION_QUOTAS: dict[str, int] = {
    "top5": 5,
    "developer": 8,
    "models": 8,
    "pricing": 5,
    "incidents": 5,
    "radar": 3,
    "everything_else": 0,
}

# Severity rules: mapping category id → default severity keyword hints
# Used by the rule-based severity assigner as fallback.
ALWAYS_HIGH_CATEGORIES: set[int] = {1}  # "New foundation model release"
