"""Machine-readable standard conformance; all refs resolve offline."""
import copy
import importlib.util
import json
import re
import unittest
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from openapi_spec_validator import validate

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {p.name.replace(".schema.json", ""): json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "contracts").glob("*.schema.json")}
REGISTRY = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in SCHEMAS.values())


def validator(name):
    return Draft202012Validator(SCHEMAS[name], registry=REGISTRY, format_checker=FormatChecker())


class Contracts(unittest.TestCase):
    def test_metaschemas_and_all_positive_fixtures(self):
        for name, schema in SCHEMAS.items():
            with self.subTest(schema=name):
                Draft202012Validator.check_schema(schema)
                fixture = ROOT / "examples/fixtures" / (name + ".json")
                if fixture.exists():
                    validator(name).validate(json.loads(fixture.read_text(encoding="utf-8")))
                else:
                    self.assertEqual(name, "agent-manifest")
        for path in (ROOT / "examples/manifests").glob("*.json"):
            with self.subTest(manifest=path.name):
                validator("agent-manifest").validate(json.loads(path.read_text(encoding="utf-8")))
        self.assertEqual(len(list((ROOT / "examples/manifests").glob("*.json"))), 4)

    def test_negative_manifest_fixtures(self):
        cases = json.loads((ROOT / "examples/negative/index.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(cases), 6)
        for case in cases:
            with self.subTest(case=case["name"]):
                self.assertTrue(list(validator(case["schema"]).iter_errors(json.loads((ROOT / case["file"]).read_text(encoding="utf-8")))))

    def test_identity_delegation_conditions(self):
        f = json.loads((ROOT / "examples/fixtures/identity.json").read_text(encoding="utf-8"))
        f["delegation"] = []
        self.assertTrue(list(validator("identity").iter_errors(f)))
        f["mode"] = "independent"
        self.assertTrue(list(validator("identity").iter_errors(f)))
        del f["principalId"]
        validator("identity").validate(f)

    def test_openapi_documents_security_and_examples(self):
        ids = set()
        for path in (ROOT / "contracts").glob("*.openapi.json"):
            api = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(api=path.name):
                self.assertEqual(api["openapi"], "3.1.2")
                validate(api)
            reg = REGISTRY.with_resource("https://oas.example.invalid/root", Resource.from_contents(api, default_specification=__import__("referencing.jsonschema", fromlist=["DRAFT202012"]).DRAFT202012))
            for route, methods in api["paths"].items():
                for method, operation in methods.items():
                    with self.subTest(api=path.name, route=route, method=method):
                        self.assertNotIn(operation["operationId"], ids)
                        ids.add(operation["operationId"])
                        if not route.startswith("/health/"):
                            self.assertTrue(operation.get("security", api.get("security")))
                            self.assertIn("401", operation["responses"])
                            self.assertIn("403", operation["responses"])
                        content_nodes = [operation.get("requestBody", {})] + list(operation["responses"].values())
                        for node in content_nodes:
                            for media in node.get("content", {}).values():
                                if "example" in media:
                                    schema = copy.deepcopy(media["schema"])
                                    schema["components"] = api["components"]
                                    Draft202012Validator(schema, registry=reg, format_checker=FormatChecker()).validate(media["example"])

    def test_frozen_contract_release(self):
        actual = {"schemas": SCHEMAS, "apis": {p.name.replace(".openapi.json", ""): json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "contracts").glob("*.openapi.json")}}
        snapshots = sorted((ROOT / "contracts/released").glob("*.json"),
                           key=lambda p: tuple(int(x) for x in p.stem.split(".")))
        frozen = json.loads(snapshots[-1].read_text(encoding="utf-8"))
        self.assertEqual(actual, frozen, "Contract changed: reviewed migration and new release snapshot required")

    def test_baseline_adr_traceability(self):
        baseline = (ROOT / "docs/requirements/baseline-v0.1.md").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"^\| Q\d+ \|", baseline, re.M)), 37)
        for n in range(1, 38):
            text = (ROOT / f"adr/ADR-{n:03}.md").read_text(encoding="utf-8")
            for section in ["Context", "Decision", "Alternatives considered", "Consequences", "Constraints", "Related contracts", "Security impact", "Supersession / migration"]:
                self.assertIn(section, text)
            self.assertIn("Status: Decided", text)
        self.assertIn("명시적으로", (ROOT / "adr/ADR-030.md").read_text(encoding="utf-8"))

    def test_markdown_local_links(self):
        for p in [ROOT / "README.md", *list((ROOT / "docs").rglob("*.md")), *list((ROOT / "adr").glob("*.md"))]:
            for target in re.findall(r"\]\(([^)]+)\)", p.read_text(encoding="utf-8")):
                parts = urlsplit(target)
                if not parts.scheme and not target.startswith("#"):
                    with self.subTest(file=p.name, target=target):
                        self.assertTrue((p.parent / unquote(parts.path)).resolve().exists())

    def test_offline_portal_assets_and_links(self):
        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links = []
            def handle_starttag(self, tag, attrs):
                a = dict(attrs)
                for k in ["src", "href"]:
                    if k in a:
                        self.links.append((tag, k, a[k]))
        pages = list((ROOT / "portal").glob("*.html"))
        self.assertGreater(len(pages), 30)
        for p in pages:
            parser = Links()
            parser.feed(p.read_text(encoding="utf-8"))
            for tag, attr, target in parser.links:
                parts = urlsplit(target)
                if parts.scheme in ("http", "https"):
                    self.assertEqual((tag, attr), ("a", "href"), "No network-loaded asset allowed")
                elif parts.path:
                    self.assertTrue((p.parent / unquote(parts.path)).resolve().exists(), str((p, target)))
        scripts = (ROOT / "portal/app.js").read_text(encoding="utf-8")
        self.assertNotRegex(scripts, r"\bfetch\s*\(|XMLHttpRequest|https?://")
        index = (ROOT / "portal/search-index.js").read_text(encoding="utf-8")
        entries = json.loads(index.removeprefix("window.PLATFORM_SEARCH = ").strip().removesuffix(";"))
        self.assertGreater(len(entries), 30)
        self.assertTrue(all((ROOT / "portal" / e["href"]).exists() for e in entries))


class PackagingTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("release", ROOT / "scripts/release.py")
        self.release = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.release)

    def test_sensitive_files_fail_packaging(self):
        for bad in [".env", "config/.env.local", "keys/service.pem", "deploy/private.key", "certs/client.p12", "home/id_rsa"]:
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                self.release.select_package_files(["README.md", bad])

    def test_generated_and_junk_files_are_excluded_and_order_is_stable(self):
        names = ["docs/b.md", "README.md", "checksums.sha256", "dist/x.zip", "verification/archive-verification.json",
                 "verification/archive-verification-v0.1.1.json", "docs/.DS_Store", "docs/a.md", "scripts/x.pyc",
                 "verification/results.json", "impl/gateway/model_route.py", "Makefile"]
        self.assertEqual(self.release.select_package_files(names),
                         ["README.md", "docs/a.md", "docs/b.md", "verification/results.json"])

    def test_release_name_follows_package_version(self):
        version = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]
        self.assertEqual(self.release.package_version(), version)
        self.assertEqual(self.release.release_name("0.1.1"), "enterprise-ai-agent-platform-v0.1.1")
        # The 0.1.0 archive keeps its own path; a newer version never writes over it.
        self.assertNotEqual(self.release.release_name(version) + ".zip", "enterprise-ai-agent-platform-v0.1.zip")

    def test_release_refuses_changed_source_but_not_earlier_outputs(self):
        changed = ["verification/results.json", "dist/a.zip", "checksums.sha256", "docs/guide.md"]
        self.assertEqual(self.release.source_changes(changed), ["docs/guide.md"])
        self.assertEqual(self.release.unexpected_changes([], ["portal/index.html", "verification/results.json"]),
                         ["portal/index.html"])
        self.assertEqual(self.release.unexpected_changes(["docs/guide.md"], ["docs/guide.md"]), [])

    def test_tracked_files_include_current_guide(self):
        names = self.release.select_package_files(self.release.tracked_files())
        for required in ["docs/core-systems.md", "docs/onboarding/01-why.md", "portal/index.html"]:
            self.assertIn(required, names)
        self.assertFalse(any("\\" in n for n in names))

