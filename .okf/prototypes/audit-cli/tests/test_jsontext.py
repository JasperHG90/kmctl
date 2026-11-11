"""Tests for reading a list a model sent as JSON text."""

import json
from typing import Any

import pytest

from audit_cli.claims.models import Verdicts
from audit_cli.jsontext import read_list

SENTENCE = {"n": 1, "how_to_check": "", "reason": "a choice", "kind": "none", "claims": []}


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ('[{"n": 1}]', [{"n": 1}]),
        ('[{"n": 1}]}', [{"n": 1}]),
        ('  [{"n": 1}] ]} \n', [{"n": 1}]),
        ([{"n": 1}], [{"n": 1}]),
    ],
    ids=["text", "a stray brace after it", "stray brackets and spaces", "already a list"],
)
def test_a_list_is_read_from_text(value: Any, expected: list[Any]) -> None:
    """A list sent as text is read up to its own end, with stray closing brackets after it ignored."""
    assert read_list(value) == expected


@pytest.mark.parametrize(
    "value",
    ['[{"n": 1}] and more', '[{"n": 1', '{"n": 1}', "not json"],
    ids=["words after it", "cut off", "not a list", "not json"],
)
def test_text_that_is_not_one_list_is_left_for_validation(value: str) -> None:
    """Text with anything but closing brackets after the list, or no whole list, is passed on unchanged."""
    assert read_list(value) == value


def test_the_extractor_reads_sentences_sent_as_text_with_a_stray_brace() -> None:
    """The answer DeepSeek gave for decision 0020: a sentences list as text, closed with an extra brace."""
    raw = json.dumps([SENTENCE, SENTENCE | {"n": 2}]) + "}"
    assert [s.n for s in Verdicts.model_validate({"sentences": raw}).sentences] == [1, 2]


def test_sentence_labels_sent_as_numbers_are_read_as_text() -> None:
    """The answer DeepSeek gave for a correction of decision 0020: refers_to as [2.7] without quotes or brackets."""
    claim = {"claim": "x", "quantifier": "exists", "refers_to": [2.7, 3, "[1.2]"]}
    verdicts = Verdicts.model_validate({"sentences": [SENTENCE | {"claims": [claim]}]})
    assert verdicts.sentences[0].claims[0].refers_to == ["2.7", "3", "[1.2]"]
