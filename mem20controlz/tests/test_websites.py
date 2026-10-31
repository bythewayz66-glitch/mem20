"""Websites manager: reads are free, writes are explicit, nothing touches the net."""

import subprocess

import pytest
from mem20ops import audit, runtime

from mem20controlz import websites


class FakeCloudflare:
    def __init__(self, records=(), zone_id="zone-1", raises=None, projects=()):
        self.records = [dict(r) for r in records]
        self.zone_id = zone_id
        self.raises = raises
        self.projects = list(projects)
        self.zone_lookups = []
        self.record_lookups = []
        self.created = []
        self.deleted = []

    def _maybe_raise(self, where):
        if self.raises == where:
            raise RuntimeError(f"cloudflare {where} exploded")

    def get_zone_id(self, zone_name):
        self.zone_lookups.append(zone_name)
        self._maybe_raise("get_zone_id")
        return self.zone_id

    def dns_records(self, zone_id, per_page=200):
        self.record_lookups.append((zone_id, per_page))
        self._maybe_raise("dns_records")
        return [dict(r) for r in self.records]

    def create_dns_record(self, zone_id, payload):
        self.created.append((zone_id, payload))
        self._maybe_raise("create_dns_record")
        return {
            "id": "rec-new",
            "type": payload.get("type"),
            "name": payload.get("name"),
            "content": payload.get("content"),
            "proxied": payload.get("proxied"),
        }

    def delete_dns_record(self, zone_id, record_id):
        self.deleted.append((zone_id, record_id))
        self._maybe_raise("delete_dns_record")
        return {"id": record_id}


def record(name, content="10.0.0.1", rtype="A"):
    return {"name": name, "type": rtype, "content": content}


def no_network_client(monkeypatch):
    """Any accidental real client construction is a test failure, not a slow test."""

    def boom(*a, **k):
        raise AssertionError("a real Cloudflare client was constructed")

    monkeypatch.setattr(audit, "build_client", boom)


def test_site_inventory_reports_the_zone_and_sites(monkeypatch):
    client = FakeCloudflare(records=[record("mem20.com")])
    monkeypatch.setattr(audit, "build_client", lambda *a, **k: client)

    result = websites.site_inventory()

    assert result["zone"] == websites.DEFAULT_ZONE
    assert result["api_error"] is None
    assert result["record_count"] == 1
    assert result["sites"] == websites.FLEET_SITES


def test_manifest_lists_write_and_read_capabilities():
    caps = " ".join(websites.manifest()["capabilities"])
    assert "DNS read" in caps
    assert "DNS write" in caps
    assert "journal tail" in caps
    assert "Cloudflare Pages" in caps


def test_dns_create_sends_the_exact_payload(monkeypatch):
    no_network_client(monkeypatch)
    client = FakeCloudflare()

    result = websites.dns_create(
        "mem20.com",
        "A",
        "shop.mem20.com",
        "10.0.0.7",
        proxied=True,
        ttl=300,
        client=client,
    )

    assert client.zone_lookups == ["mem20.com"]
    assert client.created == [
        (
            "zone-1",
            {
                "type": "A",
                "name": "shop.mem20.com",
                "content": "10.0.0.7",
                "proxied": True,
                "ttl": 300,
            },
        )
    ]
    assert result["created"] is True
    assert result["record"] == {
        "id": "rec-new",
        "type": "A",
        "name": "shop.mem20.com",
        "content": "10.0.0.7",
        "proxied": True,
    }


def test_dns_create_defaults_are_dns_but_valid(monkeypatch):
    no_network_client(monkeypatch)
    client = FakeCloudflare()

    websites.dns_create("z.example", "A", "z.example", "1.1.1.1", client=client)

    assert client.created[0][1]["proxied"] is False
    assert client.created[0][1]["ttl"] == 1


def test_dns_create_propagates_client_failure(monkeypatch):
    no_network_client(monkeypatch)
    client = FakeCloudflare(raises="create_dns_record")

    with pytest.raises(RuntimeError, match="create_dns_record exploded"):
        websites.dns_create("z.example", "A", "z.example", "1.1.1.1", client=client)


def test_dns_delete_calls_through_with_zone_and_id(monkeypatch):
    no_network_client(monkeypatch)
    client = FakeCloudflare()

    result = websites.dns_delete("mem20.com", "rec-42", client=client)

    assert client.zone_lookups == ["mem20.com"]
    assert client.deleted == [("zone-1", "rec-42")]
    assert result == {
        "deleted": True,
        "record_id": "rec-42",
        "zone": "mem20.com",
    }


def test_dns_delete_propagates_client_failure(monkeypatch):
    no_network_client(monkeypatch)
    client = FakeCloudflare(raises="delete_dns_record")

    with pytest.raises(RuntimeError, match="delete_dns_record exploded"):
        websites.dns_delete("mem20.com", "rec-42", client=client)


def test_dns_records_forwards_the_pattern(monkeypatch):
    seen = {}

    def fake_audit_dns(zone_name, pattern=None, client=None):
        seen["zone"] = zone_name
        seen["pattern"] = pattern
        seen["client"] = client
        return {
            "zone": zone_name,
            "zone_id": "zone-1",
            "total_records": 2,
            "matched_records": 1,
            "type_counts": {"A": 2},
            "records": [{"name": "a.example", "type": "A"}],
            "findings": {"wildcards": []},
        }

    monkeypatch.setattr(audit, "audit_dns", fake_audit_dns)

    result = websites.dns_records("mem20.com", pattern="^shop\\.")

    assert seen == {"zone": "mem20.com", "pattern": "^shop\\.", "client": None}
    assert set(result) == {
        "zone",
        "total_records",
        "matched_records",
        "type_counts",
        "records",
        "findings",
    }


def test_dns_records_defaults_to_the_managed_zone(monkeypatch):
    seen = {}

    def fake_audit_dns(zone_name, pattern=None, client=None):
        seen["zone"] = zone_name
        seen["pattern"] = pattern
        return {
            "zone": zone_name,
            "total_records": 0,
            "matched_records": 0,
            "type_counts": {},
            "records": [],
            "findings": {"wildcards": []},
        }

    monkeypatch.setattr(audit, "audit_dns", fake_audit_dns)

    websites.dns_records()
    assert seen == {"zone": websites.DEFAULT_ZONE, "pattern": None}


def test_dns_records_actually_filters_through_a_fake_client(monkeypatch):
    client = FakeCloudflare(
        records=[
            record("shop.mem20.com"),
            record("docs.mem20.com", content="10.0.0.2"),
            record("mem20.com", rtype="MX", content="mx.provider.com"),
        ]
    )
    monkeypatch.setattr(audit, "build_client", lambda *a, **k: client)

    result = websites.dns_records("mem20.com", pattern="^shop")

    assert result["total_records"] == 3
    assert result["matched_records"] == 1
    assert [r["name"] for r in result["records"]] == ["shop.mem20.com"]
    assert result["type_counts"] == {"A": 2, "MX": 1}
    assert client.zone_lookups == ["mem20.com"]


def test_logs_bounds_the_line_count(monkeypatch):
    calls = {}

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        calls["kwargs"] = kwargs

        class P:
            stdout = "\n".join(f"line {i}" for i in range(50))
            returncode = 0

        return P()

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = websites.logs("mcp-server.service", lines=5)

    assert calls["cmd"] == [
        "journalctl",
        "-u",
        "mcp-server.service",
        "-n",
        "5",
        "--no-pager",
    ]
    assert result["lines"] == [f"line {i}" for i in range(45, 50)]
    assert result["exit_code"] == 0


def test_logs_clamps_a_zero_line_request(monkeypatch):
    """A zero would slice from the front and return the whole buffer."""

    def fake_run(cmd, **kwargs):
        class P:
            stdout = "a\nb\nc"
            returncode = 0

        return P()

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = websites.logs("mcp-server.service", lines=0)

    assert result["lines"] == ["c"]


def test_health_marks_active_only_when_the_unit_exists(monkeypatch):
    monkeypatch.setattr(
        runtime,
        "service_status",
        lambda unit, user=False: {
            "unit": unit,
            "exists": True,
            "active_state": "active",
        },
    )

    assert websites.health("mcp-server.service")["active"] is True


def test_health_does_not_call_a_missing_unit_active(monkeypatch):
    monkeypatch.setattr(
        runtime,
        "service_status",
        lambda unit, user=False: {
            "unit": unit,
            "exists": False,
            "active_state": "inactive",
        },
    )

    assert websites.health("nope.service")["active"] is False


def test_fleet_health_reports_each_unit_and_counts_healthy(monkeypatch):
    def fake_status(unit, user=False):
        return {
            "unit": unit,
            "exists": True,
            "active_state": "active" if unit == "mcp-server.service" else "inactive",
        }

    monkeypatch.setattr(runtime, "service_status", fake_status)

    result = websites.fleet_health()

    assert result["count"] == len(websites.UNIT_CANDIDATES)
    assert result["healthy"] == 1


def test_fleet_health_survives_a_unit_that_raises(monkeypatch):
    def fake_status(unit, user=False):
        if unit == "mem20controlz.service":
            raise RuntimeError("systemd exploded")
        return {"unit": unit, "exists": True, "active_state": "active"}

    monkeypatch.setattr(runtime, "service_status", fake_status)

    result = websites.fleet_health()

    errored = [u for u in result["units"] if "error" in u]
    assert len(errored) == 1
    assert "systemd exploded" in errored[0]["error"]


def test_pages_reports_an_account_resolution_failure(monkeypatch):
    def boom():
        raise RuntimeError("no account")

    monkeypatch.setattr(websites, "resolve_account_id", boom)

    result = websites.pages()

    assert result["projects"] == []
    assert "no account" in result["error"]


def test_pages_returns_projects(monkeypatch):
    monkeypatch.setattr(websites, "resolve_account_id", lambda: "acct-1")
    monkeypatch.setattr(
        audit,
        "inspect_pages",
        lambda account_id=None, fetch_live=False: {
            "projects": [{"name": "mem20"}],
            "total": 1,
        },
    )

    result = websites.pages()

    assert result["account_id"] == "acct-1"
    assert result["total"] == 1


def test_site_inventory_reports_api_error_instead_of_raising(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("cloudflare down")

    monkeypatch.setattr(audit, "build_client", boom)

    result = websites.site_inventory()

    assert "cloudflare down" in result["api_error"]
    assert result["zone"] == websites.DEFAULT_ZONE
    assert len(result["sites"]) == len(websites.FLEET_SITES)


def test_site_inventory_survives_a_client_that_cannot_be_built(monkeypatch):
    monkeypatch.setattr(audit, "build_client", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no creds")))

    result = websites.site_inventory()

    assert result["record_count"] == 0
    assert [s["host"] for s in result["sites"]] == [
        s["host"] for s in websites.FLEET_SITES
    ]


def test_site_inventory_marks_present_and_missing_hosts(monkeypatch):
    live = next(s for s in websites.FLEET_SITES if s["state"] == "live")["host"]
    client = FakeCloudflare(records=[record(live)])
    monkeypatch.setattr(audit, "build_client", lambda *a, **k: client)

    result = websites.site_inventory()

    by_host = {s["host"]: s for s in result["sites"]}
    assert by_host[live]["dns_present"] is True
    assert client.zone_lookups == [websites.DEFAULT_ZONE]


def test_site_inventory_host_matching_is_case_insensitive(monkeypatch):
    host = websites.FLEET_SITES[1]["host"]
    client = FakeCloudflare(records=[record(host.upper())])
    monkeypatch.setattr(audit, "build_client", lambda *a, **k: client)

    result = websites.site_inventory()

    assert {s["host"]: s for s in result["sites"]}[host]["dns_present"] is True


def test_site_inventory_reads_are_non_mutating(monkeypatch):
    client = FakeCloudflare(records=[record(websites.FLEET_SITES[1]["host"])])
    monkeypatch.setattr(audit, "build_client", lambda *a, **k: client)

    websites.site_inventory()

    assert client.created == []
    assert client.deleted == []
