"""Tests for the structured log."""

import json
import pathlib as plb

import structlog
from typer.testing import CliRunner

from audit_cli.cli import app
from audit_cli.logs import configure_logging, get_logger


def test_events_are_json_lines_at_or_above_the_level(tmp_path: plb.Path) -> None:
    """Each kept event is one JSON object with its level, time and fields; lower levels are dropped."""
    path = tmp_path / "x" / "audit.log"
    configure_logging(path, "info")
    log = get_logger("test")
    log.debug("hidden")
    log.info("shown", chunk="c#one")
    (line,) = path.read_text().splitlines()
    event = json.loads(line)
    assert event["event"] == "shown" and event["level"] == "info" and event["chunk"] == "c#one"
    assert event["component"] == "test" and "timestamp" in event
    structlog.reset_defaults()


def test_a_diff_logs_to_the_projects_file_in_the_log_folder(repo: plb.Path, tmp_path: plb.Path) -> None:
    """Without logging.path, the CLI appends to <log dir>/<project key>.log and prints nothing extra."""
    CliRunner().invoke(app, ["claims", "diff", str(repo)])
    (log_file,) = (tmp_path / "logs").glob("repo-*.log")
    events = [json.loads(line)["event"] for line in log_file.read_text().splitlines()]
    assert events == ["start", "diff_done"]


def test_debug_adds_detail_and_info_is_the_default(repo: plb.Path, tmp_path: plb.Path) -> None:
    """The default log keeps info events; --debug adds the settings and other detail."""
    CliRunner().invoke(app, ["claims", "diff", str(repo)])
    CliRunner().invoke(app, ["claims", "diff", str(repo), "--debug"])
    (log_file,) = (tmp_path / "logs").glob("repo-*.log")
    events = [json.loads(line) for line in log_file.read_text().splitlines()]
    assert [e["event"] for e in events] == ["start", "diff_done", "start", "settings", "diff_done"]
    start = events[0]
    assert start["config"].endswith("audit.toml") and start["sections"] == 3
    assert start["runs"] == {"extractor": "test-model", "extractor@2": "test-model"}
