"""AgmClient, `agm mem/handoff/connect` CLI and agent-key creation against a real HTTP server."""
from __future__ import annotations

import json
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn

from agm.agent_keys import add_agent_key
from agm.api import create_app
from agm.bootstrap import bootstrap_owner
from agm.cli import main
from agm.client import AgmClient, AgmError
from agm.config import load_key_registry


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Server:
    def __init__(self, keys: Path, db: Path) -> None:
        self.port = _free_port()
        config = uvicorn.Config(create_app(db_path=str(db), key_registry=load_key_registry(keys)),
                                host="127.0.0.1", port=self.port, log_level="error")
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def __enter__(self) -> "Server":
        self.thread.start()
        for _ in range(100):
            if self.server.started:
                return self
            time.sleep(0.05)
        raise RuntimeError("server did not start")

    def __exit__(self, *exc: object) -> None:
        self.server.should_exit = True
        self.thread.join(timeout=10)


@pytest.fixture()
def env(tmp_path):
    keys = tmp_path / "keys.json"
    bootstrap_owner(keys, tenant_id="t1")
    rw = add_agent_key(keys, name="agent-rw")
    ro = add_agent_key(keys, name="agent-ro", scopes=("memory:read",))
    with Server(keys, tmp_path / "m.db") as server:
        yield {"url": server.url, "rw": rw, "ro": ro, "keys": keys}


def test_write_retrieve_history_supersede_delete(env):
    c = AgmClient(env["url"], env["rw"])
    assert c.health()["status"] == "ok"
    first = c.write({"kind": "fact", "text": "Service alpha owner is team-red", "entity": "alpha",
                     "attribute": "owner", "value": "team-red"})
    assert first["status"] == "added"
    result = c.retrieve("who owns alpha", entity="alpha")
    assert result["items"] and "untrusted" in result["notice"]
    second = c.supersede(first["item_id"], {"kind": "fact", "text": "Service alpha owner is team-blue",
                                            "entity": "alpha", "attribute": "owner", "value": "team-blue"}, "reorg")
    assert second["status"] == "superseded" and second["superseded_id"] == first["item_id"]
    texts = [n["text"] for n in c.retrieve("alpha owner", entity="alpha")["items"]]
    assert any("team-blue" in t for t in texts) and not any("team-red" in t for t in texts)
    assert len(c.history("alpha", "owner")) >= 2
    assert c.delete(second["item_id"])["deleted"] is True


def test_handoff_roundtrip(env):
    c = AgmClient(env["url"], env["rw"])
    packet = c.handoff_save("s1", {"goal": "ship R1", "decisions": [{"text": "use urllib", "rationale": "no deps"}],
                                   "open_questions": ["windows ok?"]})
    packet_id = packet.get("packet_id") or packet.get("id")
    assert packet_id
    resumed = c.handoff_resume(packet_id, "any-model", 2000)
    assert "ship R1" in json.dumps(resumed)


def test_errors_and_scopes(env):
    with pytest.raises(AgmError) as bad:
        AgmClient(env["url"], "wrong-key").write({"kind": "fact", "text": "x"})
    assert bad.value.status == 401
    ro = AgmClient(env["url"], env["ro"])
    assert ro.retrieve("anything")["items"] == []  # read scope allowed
    with pytest.raises(AgmError) as denied:
        ro.write({"kind": "fact", "text": "x"})
    assert denied.value.status == 403
    rw = AgmClient(env["url"], env["rw"])
    with pytest.raises(AgmError) as missing:
        rw.supersede("n_does_not_exist", {"kind": "fact", "text": "y", "entity": "e", "attribute": "a"}, "r")
    assert missing.value.status == 404
    assert rw.delete("n_does_not_exist")["deleted"] is False  # delete is idempotent
    with pytest.raises(AgmError) as invalid:
        AgmClient(env["url"], env["rw"]).write({"kind": "bogus", "text": "x"})
    assert invalid.value.status == 422


def test_guard_still_redacts_through_client(env):
    c = AgmClient(env["url"], env["rw"])
    secret = "ghp_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    result = c.write({"kind": "fact", "text": f"token is {secret}", "entity": "ci", "attribute": "token"})
    assert result["redactions"] >= 1
    assert secret not in json.dumps(c.retrieve("token", entity="ci"))


def test_client_safety(env):
    with pytest.raises(AgmError):
        AgmClient("http://example.com", "k")  # plain http to non-loopback
    AgmClient("http://example.com", "k", allow_insecure_http=True)
    with pytest.raises(AgmError):
        AgmClient(env["url"], "")
    assert "agm_" not in repr(AgmClient(env["url"], env["rw"]))
    with pytest.raises(AgmError) as unreachable:
        AgmClient("http://127.0.0.1:1", "k", timeout=1).health()
    assert unreachable.value.status is None


def test_cli_mem_commands(env, monkeypatch, capsys):
    monkeypatch.setenv("AGM_BASE_URL", env["url"])
    monkeypatch.setenv("AGM_API_KEY", env["rw"])
    assert main(["mem", "write", "--text", "Beta runs on port 9000", "--entity", "beta",
                 "--attribute", "port", "--value", "9000"]) == 0
    written = json.loads(capsys.readouterr().out)
    assert written["status"] == "added"
    assert main(["mem", "retrieve", "beta port", "--entity", "beta", "--brief"]) == 0
    brief = capsys.readouterr().out
    assert brief.startswith("NOTICE:") and "Beta runs on port 9000" in brief
    assert main(["mem", "history", "--entity", "beta"]) == 0
    assert json.loads(capsys.readouterr().out)
    assert main(["mem", "supersede", written["item_id"], "--text", "Beta runs on port 9001", "--entity", "beta",
                 "--attribute", "port", "--value", "9001", "--reason", "moved"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "superseded"
    assert main(["mem", "supersede", "n_nope", "--text", "t", "--entity", "e", "--attribute", "a", "--reason", "r"]) == 1
    assert "HTTP 404" in capsys.readouterr().out
    assert main(["mem", "delete", "n_nope"]) == 0
    assert json.loads(capsys.readouterr().out)["deleted"] is False


def test_cli_bad_key_and_handoff(env, monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("AGM_BASE_URL", env["url"])
    monkeypatch.setenv("AGM_API_KEY", "wrong")
    assert main(["mem", "retrieve", "x"]) == 1
    assert "HTTP 401" in capsys.readouterr().out
    monkeypatch.setenv("AGM_API_KEY", env["rw"])
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"goal": "cli handoff"}), encoding="utf-8")
    assert main(["handoff", "save", "--session", "s2", "--file", str(state)]) == 0
    saved = json.loads(capsys.readouterr().out)
    packet_id = saved.get("packet_id") or saved.get("id")
    assert main(["handoff", "resume", packet_id, "--model", "m", "--budget", "1000"]) == 0
    assert "cli handoff" in capsys.readouterr().out
    assert main(["handoff", "save", "--session", "s3", "--file", str(tmp_path / "missing.json")]) == 1


def test_connect_creates_working_scoped_key(tmp_path, capsys, monkeypatch):
    keys = tmp_path / "k.json"
    bootstrap_owner(keys, tenant_id="acme", project="p9")
    assert main(["connect", "--name", "claude-code", "--keys", str(keys)]) == 0
    out = capsys.readouterr().out
    assert "AGM_API_KEY" in out and "untrusted data" in out and "agm mem retrieve" in out
    records = json.loads(keys.read_text(encoding="utf-8"))["keys"]
    agent = records[-1]
    assert (agent["tenant_id"], agent["project"], agent["writer_id"]) == ("acme", "p9", "claude-code")
    assert agent["trust_tier"] == "trusted_agent" and "admin" not in agent["scopes"]
    assert agent["api_key"] in out
    with Server(keys, tmp_path / "d.db") as server:
        c = AgmClient(server.url, agent["api_key"])
        assert c.write({"kind": "episode", "text": "connect works"})["status"] == "added"


def test_connect_rejects_bad_input(tmp_path):
    with pytest.raises(ValueError):
        add_agent_key(tmp_path / "nope.json", name="a")
    keys = tmp_path / "k.json"
    bootstrap_owner(keys, tenant_id="t")
    for kwargs in ({"name": " "}, {"name": "a", "scopes": ("admin",)}, {"name": "a", "tier": "god"}):
        with pytest.raises(ValueError):
            add_agent_key(keys, **kwargs)
    assert len(json.loads(keys.read_text(encoding="utf-8"))["keys"]) == 1  # file untouched


def test_openapi_documents_every_route(env):
    from agm.api import create_app as make
    paths = make(db_path=":memory:", key_registry=load_key_registry(env["keys"])).openapi()["paths"]
    for route in ("/v1/memory", "/v1/memory/retrieve", "/v1/memory/{item_id}/supersede", "/v1/memory/history",
                  "/v1/memory/{item_id}", "/v1/handoff", "/v1/handoff/{packet_id}/resume",
                  "/v1/handoff/{packet_id}/readback", "/v1/admin/revoke", "/healthz"):
        assert route in paths
