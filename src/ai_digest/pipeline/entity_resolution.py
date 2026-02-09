"""Entity resolution — map items to company/product/categories using rules."""

from __future__ import annotations

import logging
import re

from ai_digest.models.source import Source
from ai_digest.models.update_event import UpdateEvent
from ai_digest.taxonomy import CATEGORY_NAMES

logger = logging.getLogger(__name__)

# Keyword → category mappings for rule-based classification
_KEYWORD_CATEGORIES: list[tuple[list[str], str]] = [
    # 1. New foundation model release
    (["new model", "launches model", "releases model", "foundation model", "introduces model"],
     "New foundation model release"),
    # 2. Model upgrade
    (["model upgrade", "improved model", "faster model", "context window", "quality improvement"],
     "Model upgrade (quality/latency/context)"),
    # 3. New modality
    (["vision", "audio", "video", "multimodal", "image generation", "speech", "3d"],
     "New modality (vision/audio/video/3D)"),
    # 4. Fine-tuning
    (["fine-tune", "fine-tuning", "finetune", "custom model", "training"],
     "Fine-tuning/customization updates"),
    # 5. Inference
    (["inference", "latency", "throughput", "runtime", "speed", "faster"],
     "Inference & serving (speed/runtimes)"),
    # 6. Pricing
    (["pricing", "price", "cost", "billing", "free tier", "rate change"],
     "Pricing & billing changes"),
    # 7. Rate limits
    (["rate limit", "quota", "throttle", "tier", "usage limit"],
     "Rate limits/quotas/tiers"),
    # 8. Deprecations
    (["deprecat", "breaking change", "end of life", "eol", "sunset", "removal", "removed"],
     "Deprecations/breaking changes"),
    # 9. SDK
    (["sdk", "library", "package", "pip install", "npm install", "client library"],
     "SDK releases/updates"),
    # 10. API
    (["api", "endpoint", "rest api", "graphql", "authentication", "schema change"],
     "API changes (endpoints/auth/schemas)"),
    # 11. Agents
    (["agent", "orchestrat", "workflow", "multi-agent", "crew", "autogen"],
     "Agents frameworks/orchestration"),
    # 12. Tool use
    (["function calling", "tool use", "tools", "integration", "plugin", "mcp"],
     "Tool-use/function calling/integrations"),
    # 13. RAG
    (["rag", "retrieval", "search", "vector search", "knowledge base"],
     "RAG/retrieval tooling"),
    # 14. Embeddings
    (["embedding", "rerank", "reranking", "similarity"],
     "Embeddings & reranking"),
    # 15. Evals
    (["benchmark", "eval", "evaluation", "leaderboard", "score"],
     "Evaluation/benchmarks/evals"),
    # 16. Datasets
    (["dataset", "data release", "training data", "corpus"],
     "Datasets (new/updated/licensing)"),
    # 17. Safety
    (["safety", "alignment", "guardrail", "content filter", "responsible ai"],
     "Safety/alignment features"),
    # 18. Policy
    (["policy", "compliance", "governance", "regulation", "gdpr", "terms of service"],
     "Policy/compliance/governance"),
    # 19. Security
    (["security", "vulnerability", "cve", "breach", "exploit", "patch"],
     "Security incidents/vuln disclosures"),
    # 20. Privacy
    (["privacy", "data protection", "opt out", "data retention"],
     "Privacy changes"),
    # 21. Open source
    (["open source", "open-source", "apache license", "mit license", "weights released"],
     "Open-source model/tool releases"),
    # 22. Dev products
    (["dashboard", "playground", "console", "developer portal", "studio"],
     "New developer products (dashboards/playgrounds)"),
    # 23. Enterprise
    (["enterprise", "sso", "rbac", "audit log", "sla"],
     "Enterprise features (SSO/RBAC/audit logs)"),
    # 24. Edge
    (["edge", "on-device", "mobile ai", "onnx", "tflite", "local"],
     "Edge/on-device AI"),
    # 25. Hardware
    (["gpu", "tpu", "chip", "accelerator", "driver", "cuda", "hardware"],
     "Hardware accelerators/drivers"),
    # 26. Training infra
    (["distributed training", "cluster", "infrastructure", "scaling"],
     "Training infrastructure/distributed systems"),
    # 27. LLMOps
    (["monitoring", "tracing", "observability", "logging", "llmops", "langsmith", "weave"],
     "LLMOps/monitoring/tracing"),
    # 28. App launches
    (["app launch", "consumer", "chatbot", "assistant", "copilot"],
     "App launches (consumer/prosumer)"),
    # 29. Funding
    (["funding", "acquisition", "merger", "partnership", "series", "investment", "ipo"],
     "Funding/M&A/partnerships"),
    # 30. Reliability
    (["outage", "incident", "downtime", "status", "degraded", "maintenance"],
     "Reliability/outages/status updates"),
]


async def resolve_entities(
    events: list[UpdateEvent],
    source: Source,
) -> list[UpdateEvent]:
    """Tag each event with company, product_line, and categories.

    Uses a two-pass approach:
    1. Inherit company/product from source registry (rule-based, high confidence).
    2. Keyword-match title + content to assign categories.
    """
    for event in events:
        # Pass 1: Source-level entity resolution
        if not event.company_slug or event.company_slug == "":
            event.company_slug = source.company_slug
        if not event.company_name:
            event.company_name = source.company_name
        if not event.product_line:
            event.product_line = source.product_line

        # Pass 2: Keyword-based category assignment
        text = f"{event.title} {event.why_it_matters or ''}".lower()
        matched_categories: list[str] = []

        for keywords, category in _KEYWORD_CATEGORIES:
            for kw in keywords:
                if kw in text:
                    if category not in matched_categories:
                        matched_categories.append(category)
                    break

        # Default category based on source fetch_method if nothing matched
        if not matched_categories:
            if source.fetch_method == "github_releases":
                matched_categories = ["SDK releases/updates"]
            elif "status" in source.source_name.lower():
                matched_categories = ["Reliability/outages/status updates"]
            else:
                matched_categories = ["API changes (endpoints/auth/schemas)"]

        event.categories = matched_categories

        # Detect breaking changes from keywords
        breaking_keywords = ["breaking", "deprecat", "removal", "removed", "end of life", "eol"]
        if any(kw in text for kw in breaking_keywords):
            event.breaking_change = True

    logger.info("Entity-resolved %d events from %s", len(events), source.source_name)
    return events
