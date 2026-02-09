"""Tests for dedup pipeline stage."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from ai_digest.models.update_event import UpdateEvent
from ai_digest.pipeline.dedupe import _title_similarity


def test_title_similarity_identical():
    assert _title_similarity("Hello World", "Hello World") == 1.0


def test_title_similarity_case_insensitive():
    assert _title_similarity("Hello World", "hello world") == 1.0


def test_title_similarity_different():
    sim = _title_similarity("OpenAI releases GPT-5", "Anthropic launches Claude 4")
    assert sim < 0.5


def test_title_similarity_very_similar():
    sim = _title_similarity(
        "OpenAI releases GPT-5 model",
        "OpenAI releases GPT-5 foundation model",
    )
    assert sim > 0.8


def test_title_similarity_empty():
    assert _title_similarity("", "hello") == 0.0
    assert _title_similarity("hello", "") == 0.0
