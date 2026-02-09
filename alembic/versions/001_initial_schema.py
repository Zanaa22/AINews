"""001 — Initial schema: sources, raw_items, snapshots, clusters, update_events, digests.

Revision ID: 001
Revises:
Create Date: 2026-02-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- sources ---
    op.create_table(
        "sources",
        sa.Column("source_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_slug", sa.String(128), nullable=False),
        sa.Column("company_name", sa.String(256), nullable=False),
        sa.Column("product_line", sa.String(256), nullable=True),
        sa.Column("source_name", sa.String(256), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False, unique=True),
        sa.Column("fetch_method", sa.String(32), nullable=False),
        sa.Column("poll_frequency_min", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("trust_tier", sa.SmallInteger(), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False, server_default="normal"),
        sa.Column("parse_rules", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("health_status", sa.String(16), nullable=False, server_default="healthy"),
        sa.Column("last_fetched_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_item_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_sources_company", "sources", ["company_slug"])
    op.create_index("idx_sources_enabled", "sources", ["enabled", "health_status"])
    op.create_index("idx_sources_next_fetch", "sources",
                    ["enabled", "last_fetched_at", "poll_frequency_min"])

    # --- raw_items ---
    op.create_table(
        "raw_items",
        sa.Column("raw_item_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sources.source_id"), nullable=False),
        sa.Column("external_id", sa.String(512), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("content_html", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("snapshot_s3_key", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_duplicate", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("idx_raw_items_source", "raw_items", ["source_id", "fetched_at"])
    op.create_index("idx_raw_items_hash", "raw_items", ["content_hash"])
    op.create_index("idx_raw_items_url", "raw_items", ["url"])
    op.create_index("idx_raw_items_published", "raw_items", ["published_at"])
    op.create_unique_constraint("uq_raw_items_source_ext", "raw_items",
                                ["source_id", "external_id"])

    # --- snapshots ---
    op.create_table(
        "snapshots",
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sources.source_id"), nullable=False),
        sa.Column("s3_key", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("diff_from_prev", sa.Text(), nullable=True),
        sa.Column("has_changes", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("idx_snapshots_source", "snapshots", ["source_id", "fetched_at"])

    # --- clusters ---
    op.create_table(
        "clusters",
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("canonical_title", sa.Text(), nullable=False),
        sa.Column("company_slug", sa.String(128), nullable=True),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_seen_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("merged_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_clusters_company", "clusters", ["company_slug", "last_seen_at"])

    # --- digests ---
    op.create_table(
        "digests",
        sa.Column("digest_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("digest_date", sa.Date(), nullable=False, unique=True),
        sa.Column("overview_text", sa.Text(), nullable=True),
        sa.Column("sections", postgresql.JSONB(), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("delivery_channels", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("html_s3_key", sa.Text(), nullable=True),
        sa.Column("web_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_digests_date", "digests", ["digest_date"])

    # --- update_events ---
    op.create_table(
        "update_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("clusters.cluster_id"), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sources.source_id"), nullable=False),
        sa.Column("raw_item_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("raw_items.raw_item_id"), nullable=False),
        sa.Column("company_slug", sa.String(128), nullable=False),
        sa.Column("company_name", sa.String(256), nullable=False),
        sa.Column("product_line", sa.String(256), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("categories", postgresql.ARRAY(sa.Text()), nullable=False,
                  server_default="{}"),
        sa.Column("trust_tier", sa.SmallInteger(), nullable=False),
        sa.Column("severity", sa.String(8), nullable=False, server_default="LOW"),
        sa.Column("breaking_change", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("impact_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.String(16), nullable=False, server_default="confirmed"),
        sa.Column("what_changed", postgresql.JSONB(), nullable=True),
        sa.Column("why_it_matters", sa.Text(), nullable=True),
        sa.Column("action_items", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("citations", postgresql.ARRAY(sa.Text()), nullable=False,
                  server_default="{}"),
        sa.Column("evidence_snippets", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("summary_short", sa.Text(), nullable=True),
        sa.Column("summary_medium", sa.Text(), nullable=True),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("digest_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("digests.digest_id"), nullable=True),
        sa.Column("digest_section", sa.String(32), nullable=True),
    )
    op.create_index("idx_events_company", "update_events", ["company_slug", "created_at"])
    op.create_index("idx_events_score", "update_events", ["impact_score"])
    op.create_index("idx_events_created", "update_events", ["created_at"])
    op.create_index("idx_events_digest", "update_events", ["digest_id"])
    op.create_index("idx_events_severity", "update_events", ["severity", "created_at"])


def downgrade() -> None:
    op.drop_table("update_events")
    op.drop_table("digests")
    op.drop_table("clusters")
    op.drop_table("snapshots")
    op.drop_table("raw_items")
    op.drop_table("sources")
