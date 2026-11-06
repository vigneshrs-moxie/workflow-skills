"""publish.py against a stub site: no network, no model calls. Run: python3 -m unittest test_publish -v"""
import json, os, re, shutil, stat, subprocess, sys, tempfile, threading, unittest
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.dont_write_bytecode = True
SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "publish.py")
TOKEN = "ptp_made-up-token-for-tests"
PAGE = b'<!doctype html><html><body><div id="pt-root">made up</div></body></html>'
# The grammar both homes of these lines write: the page's feedbackText() and the Starbase tests' "Pick A for c-entry".
PICK_LINE = re.compile(r"^Pick \w+ for [\w-]+$")
NOTE_LINE = re.compile(r'^(s-[\w-]+|overview)( \([^()]*\))?: (needs change|question|idea|note): .*$')


class Stub(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def answer(self, code, body, headers=()):
        raw = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        for k, v in headers:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(raw)

    def handle_any(self):
        n = int(self.headers.get("Content-Length") or 0)
        srv = self.server
        srv.requests.append({"method": self.command, "path": self.path, "headers": dict(self.headers), "body": self.rfile.read(n)})
        if srv.force:
            code, body, headers = srv.force
            return self.answer(code, body, headers)
        if self.path == "/api/publish":
            srv.revision += 1
            return self.answer(200, {"key": "k", "revision": srv.revision, "url": f"https://example.test/f/k", "created": srv.revision == 1})
        if self.command == "POST":
            sent = json.loads(srv.requests[-1]["body"])
            return self.answer(200, {"notes": len(sent["notes"]), "choices": len(sent["choices"])})
        return self.answer(200, srv.notes_reply)

    do_GET = do_POST = handle_any


def parts(request):
    """{name: bytes} from a recorded multipart request."""
    msg = BytesParser().parsebytes(b"Content-Type: " + request["headers"]["Content-Type"].encode() + b"\r\n\r\n" + request["body"])
    return {p.get_param("name", header="content-disposition"): p.get_payload(decode=True) for p in msg.get_payload()}


class Base(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="publish-test-")
        self.addCleanup(shutil.rmtree, self.home)
        self.claude = os.path.join(self.home, ".claude")
        self.jobs = os.path.join(self.claude, "feature-work")
        self.pages = os.path.join(self.claude, "wireframes", "repo")
        os.makedirs(self.jobs)
        os.makedirs(self.pages)
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
        self.srv.requests, self.srv.revision, self.srv.force = [], 0, None
        self.srv.notes_reply = {"feature": {"key": "k", "title": "T", "latest_revision": 3}, "notes": [], "choices": []}
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.site = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.config()

    def config(self, mode=0o600, body=None):
        path = os.path.join(self.claude, "prototypes.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"site": self.site, "token": TOKEN}) if body is None else body)
        os.chmod(path, mode)
        return path

    def run_it(self, *args):
        env = {**os.environ, "HOME": self.home, "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("STARBASE_FEATURES_DIR", None)
        env.pop("WORKSHOP_FEATURES_DIR", None)
        r = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True, env=env, timeout=30)
        self.assertNotIn(TOKEN, r.stdout + r.stderr)
        return r

    def load(self, path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def write(self, path, data):
        with open(path, "wb" if isinstance(data, bytes) else "w") as f:
            f.write(data)
        return path

    def job(self, slug="orbit-296-freeze-row", status=None, spec=None, decisions=None, pdf=True):
        folder = os.path.join(self.jobs, slug)
        os.makedirs(folder)
        source = os.path.join(self.pages, "freeze.html")
        os.makedirs(source[:-5] + ".revisions", exist_ok=True)
        self.write(source[:-5] + ".revisions/history.json", json.dumps([{"rev": 2, "note": "Header frozen.", "changed": [], "added": [], "removed": []}]))
        self.write(os.path.join(folder, "wireframes.html"), PAGE)
        self.write(os.path.join(folder, "wireframes.json"), json.dumps({"version": 2, "title": "Page title", "tier": "hi", "source": source, "repo": "/Users/someone/repo",
                                                                       "screens": [{"key": "s-a"}], "choices": [], "questions": []}))
        self.write(os.path.join(folder, "status.json"), json.dumps(status or {"slug": slug, "title": "ORBIT-296: Freeze the header row on scroll please",
                                                                             "ticket": {"key": "ORBIT-296", "url": "https://orbit.example/t/296"}}))
        if spec:
            self.write(os.path.join(folder, "spec.md"), spec)
        if decisions:
            self.write(os.path.join(folder, "decisions.md"), decisions)
        if pdf:
            self.write(os.path.join(folder, "wireframes.pack.pdf"), b"%PDF-made-up")
        return folder

    def page(self, name="field", revision=4, sections=None):
        path = self.write(os.path.join(self.pages, f"{name}.html"), PAGE)
        self.write(os.path.join(self.pages, f"{name}.json"), json.dumps({"title": "Field Team Mobile Test", "revision": revision, "tier": "hi", "file": "repo/field.html"}))
        if sections:
            os.makedirs(os.path.join(self.pages, f"{name}.revisions"), exist_ok=True)
            self.write(os.path.join(self.pages, f"{name}.revisions", f"{revision}.html"), sections)
        return path


class JobMode(Base):
    SPEC = ("# Spec\n\n## 6. Functional requirements\n| ID | Requirement | Source |\n|---|---|---|\n| FR-001 | Header stays. | Confirmed |\n| ~~FR-002~~ | Dropped. | Removed (v0.2): no |\n\n"
            "## 7. Acceptance criteria\n| ID | Covers | Criterion |\n|---|---|---|\n| AC-001 | FR-001 | Given it |\n")

    def test_sends_everything_and_remembers(self):
        folder = self.job(spec=self.SPEC, decisions="| id |\n")
        r = self.run_it("--job", "orbit-296-freeze-row")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Published revision 1: https://example.test/f/k", r.stdout)
        req = self.srv.requests[0]
        self.assertEqual((req["method"], req["path"]), ("POST", "/api/publish"))
        self.assertEqual(req["headers"]["Authorization"], f"Bearer {TOKEN}")
        p = parts(req)
        self.assertEqual(p["key"], b"orbit-296-freeze-the-header-row")
        self.assertEqual(p["ticket_key"], b"ORBIT-296")
        self.assertEqual(p["ticket_url"], b"https://orbit.example/t/296")
        self.assertEqual(p["job_slug"], b"orbit-296-freeze-row")
        self.assertEqual(p["page_version"], b"2")
        self.assertEqual(p["changes"], b"Header frozen.")
        self.assertEqual(p["page"], PAGE)
        self.assertEqual(p["pdf"], b"%PDF-made-up")
        self.assertEqual(p["decisions"], b"| id |\n")
        self.assertEqual(p["requirements"].decode().splitlines(), ["| ID | Requirement | Source |", "|---|---|---|", "| FR-001 | Header stays. | Confirmed |", "| ~~FR-002~~ | Dropped. | Removed (v0.2): no |"])
        manifest = json.loads(p["manifest"])
        self.assertEqual(manifest["history"][0]["rev"], 2)
        self.assertEqual(manifest["screens"], [{"key": "s-a"}])
        self.assertNotIn("source", manifest)
        self.assertNotIn("/Users/", p["manifest"].decode())
        state = self.load(os.path.join(folder, "prototype.json"))
        self.assertEqual({k: state[k] for k in ("key", "url", "revision")}, {"key": "orbit-296-freeze-the-header-row", "url": "https://example.test/f/k", "revision": 1})
        self.assertTrue(state["published_at"])

    def test_no_spec_no_decisions_no_pdf_are_left_out(self):
        self.job(pdf=False)
        self.assertEqual(self.run_it("--job", "orbit-296-freeze-row").returncode, 0)
        p = parts(self.srv.requests[0])
        self.assertFalse({"requirements", "decisions", "pdf"} & set(p))

    def test_spec_named_by_status(self):
        spec = self.write(os.path.join(self.home, "named-spec.md"), self.SPEC)
        self.job(status={"title": "A title", "spec": {"path": spec}})
        self.run_it("--job", "orbit-296-freeze-row")
        self.assertIn(b"FR-001", parts(self.srv.requests[0])["requirements"])

    def test_bold_fr_cells_are_found(self):
        self.job(spec="| ID | Confirmed requirement | Testable |\n| --- | --- | --- |\n| **FR-001 — Compose** | Admins can. | Yes |\n")
        self.run_it("--job", "orbit-296-freeze-row")
        self.assertIn(b"**FR-001", parts(self.srv.requests[0])["requirements"])

    def test_json(self):
        self.job()
        r = self.run_it("--job", "orbit-296-freeze-row", "--json")
        self.assertEqual(json.loads(r.stdout)["revision"], 1)

    def test_job_without_a_page(self):
        os.makedirs(os.path.join(self.jobs, "empty"))
        r = self.run_it("--job", "empty")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(len(r.stderr.strip().splitlines()), 1)

    def test_slug_cant_leave_the_folder(self):
        self.assertEqual(self.run_it("--job", "../wireframes").returncode, 1)


class PageMode(Base):
    def test_sends_page_with_flags(self):
        page = self.page()
        reqs = self.write(os.path.join(self.home, "r.md"), "# R\n")
        r = self.run_it("--page", page, "--title", "Field team mobile", "--ticket", "orbit-12", "--ticket-url", "https://o/12", "--requirements", reqs, "--changes", "First.")
        self.assertEqual(r.returncode, 0, r.stderr)
        p = parts(self.srv.requests[0])
        self.assertEqual(p["key"], b"orbit-12-field-team-mobile")
        self.assertEqual(p["ticket_key"], b"ORBIT-12")
        self.assertEqual(p["requirements"], b"# R\n")
        self.assertEqual(p["changes"], b"First.")
        self.assertEqual(p["page_version"], b"4")
        self.assertNotIn("job_slug", p)
        self.assertTrue(os.path.exists(os.path.join(self.pages, "field.prototype.json")))

    def test_two_pages_in_one_folder_keep_their_own_records(self):
        one, two = self.page("one"), self.page("two")
        self.run_it("--page", one, "--title", "One")
        self.run_it("--page", two, "--title", "Two")
        self.assertEqual(self.load(os.path.join(self.pages, "one.prototype.json"))["key"], "one")
        self.assertEqual(self.load(os.path.join(self.pages, "two.prototype.json"))["key"], "two")

    def test_pdf_beside_the_page_is_found(self):
        page = self.page()
        self.write(page[:-5] + ".pack.pdf", b"%PDF-beside")
        self.run_it("--page", page)
        self.assertEqual(parts(self.srv.requests[0])["pdf"], b"%PDF-beside")

    def test_manifest_gets_screens_from_the_saved_revision(self):
        sections = '<div class="screen" data-id="team" data-device="phone" data-name="Team" data-pack></div>'
        page = self.page(sections=sections)
        self.assertEqual(self.run_it("--page", page).returncode, 0)
        manifest = json.loads(parts(self.srv.requests[0])["manifest"])
        self.assertEqual([s["key"] for s in manifest["screens"]], ["s-team"])
        self.assertNotIn("file", manifest)

    def test_only_the_complete_page(self):
        page = self.page()
        for name, note in (("field.artifact.html", "body-only"), ("field.draft.html", "draft")):
            r = self.run_it("--page", self.write(os.path.join(self.pages, name), PAGE))
            self.assertEqual(r.returncode, 1)
            self.assertIn(note, r.stderr)
        self.write(page, b"<div>no doctype</div>")
        self.assertEqual(self.run_it("--page", page).returncode, 1)
        self.assertEqual(self.srv.requests, [])

    def test_review_page_is_warned_about(self):
        page = self.page()
        self.write(page, b"<!doctype html><section data-key='s-a'></section>")
        r = self.run_it("--page", page)
        self.assertEqual(r.returncode, 0)
        self.assertIn("review page", r.stderr)

    def test_needs_the_builds_record(self):
        path = self.write(os.path.join(self.pages, "loose.html"), PAGE)
        self.assertEqual(self.run_it("--page", path).returncode, 1)


class KeyRule(Base):
    def key_of(self, *args):
        self.srv.requests.clear()
        r = self.run_it(*args)
        self.assertEqual(r.returncode, 0, r.stderr)
        return parts(self.srv.requests[0])["key"].decode()

    def test_ticket_in_the_title_isnt_doubled(self):
        self.job(status={"title": "ORBIT-296 · Freeze header", "ticket": {"key": "ORBIT-296"}})
        self.assertEqual(self.key_of("--job", "orbit-296-freeze-row"), "orbit-296-freeze-header")

    def test_ticket_from_the_slug_when_status_has_none(self):
        self.job(slug="orbit-465-we-want", status={"title": "ORBIT-465: Freeze/finalize team talent ratings", "ticket": None})
        self.assertEqual(self.key_of("--job", "orbit-465-we-want"), "orbit-465-freeze-finalize-team-talent")

    def test_no_ticket_is_the_title_slug(self):
        self.job(slug="some-job", status={"title": "Copy Ticket ID"})
        self.assertEqual(self.key_of("--job", "some-job"), "copy-ticket-id")

    def test_written_once_and_kept_when_the_title_changes(self):
        page = self.page()
        self.assertEqual(self.key_of("--page", page, "--title", "First title"), "first-title")
        self.assertEqual(self.key_of("--page", page, "--title", "A new title"), "first-title")

    def test_given_key_is_used_once_then_cant_change(self):
        page = self.page()
        self.assertEqual(self.key_of("--page", page, "--key", "field-team-mobile"), "field-team-mobile")
        r = self.run_it("--page", page, "--key", "another")
        self.assertEqual(r.returncode, 1)
        self.assertIn("never changes", r.stderr)

    def test_bad_key_and_bad_ticket(self):
        page = self.page()
        self.assertEqual(self.run_it("--page", page, "--key", "../Bad").returncode, 1)
        self.assertEqual(self.run_it("--page", page, "--ticket", "not a ticket").returncode, 1)
        self.assertEqual(self.srv.requests, [])

    def test_title_with_nothing_to_slug(self):
        self.assertEqual(self.run_it("--page", self.page(), "--title", "×××").returncode, 1)


class Notes(Base):
    def reply(self, notes=(), choices=(), latest=3):
        self.srv.notes_reply = {"feature": {"key": "k", "title": "T", "ticket_key": None, "ticket_url": None, "latest_revision": latest}, "notes": list(notes), "choices": list(choices)}

    def note(self, **kw):
        return {"id": "1", "revision": 3, "screen": "s-needs", "device": "phone", "kind": "change", "text": "Too tight", "pin": None, "by": {"name": "A", "email": "a@example.test"},
                "at": "2026-11-05T10:00:00.000Z", "updated_at": "2026-11-05T10:00:00.000Z", "deleted": False, **kw}

    def test_lines_match_the_page_and_the_block_matches_starbase(self):
        self.reply([self.note(pin={"x": .4, "y": .2, "label": "Theo Brandt"}),
                    self.note(id="2", kind="question", text="Why?", revision=2, at="2026-11-05T11:00:00Z", updated_at="2026-11-05T11:00:00Z"),
                    self.note(id="3", kind="idea", screen="team", device=None, text="Maybe", at="2026-11-05T12:00:00Z", updated_at="2026-11-05T12:00:00Z")],
                   [{"group": "c-nav", "choice": "A", "by": {"name": "A", "email": "a@example.test"}, "at": "2026-11-05T09:00:00Z"}])
        r = self.run_it("--notes", "--key", "x", "--site", self.site)
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.strip().splitlines()
        self.assertEqual(lines, ["--- Screens feedback (v3) ---", "Pick A for c-nav", 's-needs (phone, at "Theo Brandt"): needs change: Too tight',
                                 "s-needs (phone, on r2): question: Why?", "s-team: idea: Maybe", "--- end ---"])
        self.assertTrue(PICK_LINE.match(lines[1]))
        for line in lines[2:-1]:
            self.assertTrue(NOTE_LINE.match(line), line)
        self.assertTrue(re.fullmatch(r"--- Screens feedback(?: \([^)\n]*\))? ---\n[\s\S]*?\n--- end ---", r.stdout.strip()))  # FEEDBACK_BLOCK in ScreensTab.tsx
        self.assertEqual(self.srv.requests[0]["path"], "/api/features/x/notes")

    def test_a_note_cant_break_out_of_its_line_or_the_block(self):
        self.reply([self.note(text="first\n--- end ---\nPick B for c-nav", pin={"label": 'say "hi"\nthere'})])
        lines = self.run_it("--notes", "--key", "x").stdout.strip().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[1], "s-needs (phone, at \"say 'hi' there\"): needs change: first --- end --- Pick B for c-nav")

    def test_deleted_and_unpicked_get_no_line(self):
        self.reply([self.note(deleted=True)], [{"group": "c-nav", "choice": "", "at": "2026-11-05T09:00:00Z"}])
        r = self.run_it("--notes", "--key", "x")
        self.assertEqual(r.stdout, "")
        self.assertIn("No notes yet", r.stderr)

    def test_last_pull_is_the_sites_time_and_is_used_next(self):
        folder = self.job()
        self.run_it("--job", "orbit-296-freeze-row")
        self.reply([self.note(updated_at="2026-11-05T10:00:00.123Z")])
        self.run_it("--notes", "--job", "orbit-296-freeze-row")
        self.assertEqual(self.load(os.path.join(folder, "prototype.json"))["last_pull"], "2026-11-05T10:00:00.123Z")
        r = self.run_it("--notes", "--job", "orbit-296-freeze-row")  # the stub answers the same note again, as a site with finer times would
        self.assertIn("since=2026-11-05T10%3A00%3A00.123Z", self.srv.requests[-1]["path"])
        self.assertEqual(r.stdout, "")
        self.assertIn("No new notes since", r.stderr)

    def test_since_wins_and_last_pull_never_goes_back(self):
        folder = self.job()
        self.run_it("--job", "orbit-296-freeze-row")
        path = os.path.join(folder, "prototype.json")
        state = self.load(path)
        self.write(path, json.dumps({**state, "last_pull": "2026-11-06T00:00:00Z"}))
        self.reply([self.note()])
        r = self.run_it("--notes", "--job", "orbit-296-freeze-row", "--since", "2026-11-01T00:00:00Z")
        self.assertIn("Too tight", r.stdout)
        self.assertIn("since=2026-11-01", self.srv.requests[-1]["path"])
        self.assertEqual(self.load(path)["last_pull"], "2026-11-06T00:00:00Z")

    def test_key_alone_finds_its_record(self):
        page = self.page()
        self.run_it("--page", page, "--key", "field-team-mobile")
        self.reply([self.note()])
        self.run_it("--notes", "--key", "field-team-mobile")
        self.assertEqual(self.load(page[:-5] + ".prototype.json")["last_pull"], "2026-11-05T10:00:00.000Z")

    def test_another_site_doesnt_touch_the_record(self):
        folder = self.job()
        self.run_it("--job", "orbit-296-freeze-row")
        path = os.path.join(folder, "prototype.json")
        state = {**self.load(path), "site": "https://prototypes.example.test", "last_pull": "2026-11-06T00:00:00Z"}
        self.write(path, json.dumps(state))
        self.reply([self.note()])
        r = self.run_it("--notes", "--job", "orbit-296-freeze-row", "--site", self.site)
        self.assertNotIn("since=", self.srv.requests[-1]["path"])
        self.assertIn("wasn't remembered", r.stderr)
        self.assertEqual(self.load(path), state)

    def test_json_is_the_reply_plus_the_lines(self):
        self.reply([self.note()])
        out = json.loads(self.run_it("--notes", "--key", "x", "--json").stdout)
        self.assertEqual(out["notes"][0]["id"], "1")
        self.assertEqual(out["feature"]["latest_revision"], 3)
        self.assertEqual(out["lines"], ["s-needs (phone): needs change: Too tight"])

    def test_different_picks_are_all_listed_and_warned_about(self):
        self.reply([], [{"group": "c-nav", "choice": "A", "at": "2026-11-05T09:00:00Z"}, {"group": "c-nav", "choice": "B", "at": "2026-11-05T10:00:00Z"}])
        r = self.run_it("--notes", "--key", "x")
        self.assertIn("Pick A for c-nav\nPick B for c-nav", r.stdout)
        self.assertIn("picked differently on c-nav", r.stderr)

    def test_not_published_yet(self):
        self.job()
        self.assertEqual(self.run_it("--notes", "--job", "orbit-296-freeze-row").returncode, 1)

    def test_bad_since(self):
        self.assertEqual(self.run_it("--notes", "--key", "x", "--since", "yesterday").returncode, 1)


class Token(Base):
    def test_group_or_world_readable_is_refused(self):
        page = self.page()
        for mode in (0o640, 0o604, 0o644):
            path = self.config(mode=mode)
            r = self.run_it("--page", page)
            self.assertEqual(r.returncode, 3, oct(mode))
            self.assertIn(f"chmod 600 {path}", r.stderr)
        self.assertEqual(self.srv.requests, [])

    def test_missing_and_broken_files(self):
        page = self.page()
        self.config(body="{ not json " + TOKEN)
        self.assertEqual(self.run_it("--page", page).returncode, 3)
        self.config(body="{}")
        self.assertEqual(self.run_it("--page", page).returncode, 3)
        os.remove(os.path.join(self.claude, "prototypes.json"))
        r = self.run_it("--page", page, "--site", self.site)
        self.assertEqual(r.returncode, 3)
        self.assertIn("isn't set up", r.stderr)
        self.assertEqual(self.srv.requests, [])

    def test_no_plain_http_to_anywhere_else(self):
        r = self.run_it("--page", self.page(), "--site", "http://prototypes.moxieorbit.com")
        self.assertEqual(r.returncode, 1)
        self.assertIn("https", r.stderr)

    def test_a_redirect_is_not_followed(self):
        self.srv.force = (302, {}, [("Location", f"{self.site}/elsewhere")])
        r = self.run_it("--page", self.page())
        self.assertEqual(r.returncode, 4)
        self.assertIn("redirect", r.stderr)
        self.assertEqual(len(self.srv.requests), 1)


class SiteAnswers(Base):
    def test_refusals_are_one_line_and_record_nothing(self):
        page = self.page()
        for code, word in ((401, "refused the publish token"), (403, "can't do that"), (413, "too big"), (429, "Too many"), (500, "answered 500")):
            self.srv.force = (code, {"error": "said\nso"}, [])
            r = self.run_it("--page", page)
            self.assertEqual(r.returncode, 4, code)
            self.assertIn(word, r.stderr)
            self.assertIn("said so", r.stderr)
            self.assertEqual(len(r.stderr.strip().splitlines()), 1)
        self.assertFalse(os.path.exists(page[:-5] + ".prototype.json"))

    def test_unknown_key(self):
        self.srv.force = (404, {}, [])
        r = self.run_it("--notes", "--key", "nope")
        self.assertEqual(r.returncode, 4)
        self.assertIn("no feature called nope", r.stderr)

    def test_a_reply_without_a_revision(self):
        self.srv.force = (200, {"ok": True}, [])
        self.assertEqual(self.run_it("--page", self.page()).returncode, 4)

    def test_nothing_listening(self):
        r = self.run_it("--notes", "--key", "x", "--site", "http://127.0.0.1:9")
        self.assertEqual(r.returncode, 4)
        self.assertIn("Couldn't reach", r.stderr)


class DryRun(Base):
    def test_job_says_what_and_sends_nothing(self):
        folder = self.job(spec=JobMode.SPEC)
        r = self.run_it("--job", "orbit-296-freeze-row", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        for word in ("orbit-296-freeze-the-header-row (new)", "ORBIT-296", "wireframes.html", "wireframes.pack.pdf", "2 FR rows", "total:", "found, not shown"):
            self.assertIn(word, r.stdout)
        self.assertEqual(self.srv.requests, [])
        self.assertFalse(os.path.exists(os.path.join(folder, "prototype.json")))

    def test_works_with_no_token_file(self):
        os.remove(os.path.join(self.claude, "prototypes.json"))
        r = self.run_it("--page", self.page(), "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("isn't set up", r.stdout)

    def test_notes_and_import(self):
        r = self.run_it("--notes", "--key", "x", "--dry-run")
        self.assertIn("GET", r.stdout)
        f = self.write(os.path.join(self.home, "e.json"), json.dumps({"feedback": []}))
        self.assertIn("0 notes", self.run_it("--import-notes", f, "--key", "x", "--dry-run").stdout)
        self.assertEqual(self.srv.requests, [])

    def test_too_big_for_one_request_is_refused_before_sending(self):
        page = self.page()
        self.write(page[:-5] + ".pack.pdf", b"%PDF" + b"0" * 5000000)
        r = self.run_it("--page", page, "--dry-run", "--site", "https://prototypes.example.test")
        self.assertEqual(r.returncode, 1)
        self.assertIn("in one request", r.stderr)
        self.assertEqual(self.run_it("--page", page, "--site", self.site).returncode, 0)  # a local server has no such limit

    def test_over_the_sites_file_limits(self):
        page = self.page()
        self.write(page, b"<!doctype html>" + b"0" * 5000001)
        r = self.run_it("--page", page)
        self.assertEqual(r.returncode, 1)
        self.assertIn("page is", r.stderr)


class ImportNotes(Base):
    EXPORT = {"feedback": [
        {"id": "a1", "data": {"at": "2026-11-04T23:23:52.536Z", "author": "u_one", "device": "laptop", "kind": "question", "name": "Team Overview", "options": {"c-nav": "B"},
                              "path": ["team"], "pin": {"label": "Collection", "s": 1, "x": 442, "y": 272}, "rev": 4, "role": "admin", "screen": "team", "text": "what is this"}, "version": 1, "updatedAt": "2026-11-04T23:23:52.7Z"},
        {"id": "a2", "data": {"at": "2026-11-04T23:24:02.569Z", "author": "u_two", "device": "phone", "kind": "idea", "screen": "needs", "text": "hmm", "pin": None}, "version": 1}],
        "notes": [{"id": "c-nav", "data": {"section": "c-nav", "choice": "A", "updatedAt": "2026-11-04T23:25:00Z"}}, {"id": "c-off", "data": {"section": "c-off", "choice": ""}}, {"id": "_meta", "data": {"intent": "refine"}}],
        "names": {"u_one": "Made-up Person"}}

    def export(self, data=None):
        return self.write(os.path.join(self.home, "export.json"), json.dumps(data or self.EXPORT))

    def test_posts_notes_and_choices_with_author_labels(self):
        r = self.run_it("--import-notes", self.export(), "--key", "k")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Imported 2 notes and 1 choices", r.stdout)
        self.assertIn("Someone on the artifact", r.stderr)
        req = self.srv.requests[-1]
        self.assertEqual((req["method"], req["path"]), ("POST", "/api/features/k/notes"))
        sent = json.loads(req["body"])
        first = sent["notes"][0]
        self.assertEqual(first, {"screen": "s-team", "device": "laptop", "kind": "question", "text": "what is this", "pin": {"label": "Collection", "px": {"x": 442, "y": 272, "s": 1}},
                                 "at": "2026-11-04T23:23:52.536Z", "by_label": "Made-up Person"})
        self.assertEqual(sent["notes"][1]["by_label"], "Someone on the artifact")
        self.assertEqual(sent["choices"], [{"group": "c-nav", "choice": "A", "at": "2026-11-04T23:25:00Z", "by_label": "Someone on the artifact"}])

    def test_flat_documents_work_too(self):
        data = {"feedback": [{"id": "a", "at": "2026-11-04T23:23:52Z", "kind": "idea", "screen": "s-team", "text": "x"}]}
        self.assertEqual(self.run_it("--import-notes", self.export(data), "--key", "k").returncode, 0)
        self.assertEqual(json.loads(self.srv.requests[-1]["body"])["notes"][0]["screen"], "s-team")

    def test_a_second_run_adds_nothing(self):
        self.srv.notes_reply["notes"] = [{"at": "2026-11-04T23:23:52.536Z", "text": "what is this"}, {"at": "2026-11-04T23:24:02.569+00:00", "text": "hmm"}]
        self.srv.notes_reply["choices"] = [{"group": "c-nav", "choice": "A"}]
        r = self.run_it("--import-notes", self.export(), "--key", "k")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Nothing new", r.stderr)
        self.assertEqual([q["method"] for q in self.srv.requests], ["GET"])

    def test_unusable_notes_are_named_and_left_out(self):
        data = {"feedback": [{"id": "bad", "data": {"kind": "idea", "text": ""}}, *self.EXPORT["feedback"]]}
        r = self.run_it("--import-notes", self.export(data), "--key", "k")
        self.assertIn("left out note bad", r.stderr)
        self.assertEqual(len(json.loads(self.srv.requests[-1]["body"])["notes"]), 2)

    def test_the_site_taking_fewer_is_a_failure(self):
        f = self.export()
        srv = self.srv

        class Short(Stub):
            def handle_any(self):
                n = int(self.headers.get("Content-Length") or 0)
                self.rfile.read(n)
                self.answer(200, {"notes": 1, "choices": 0} if self.command == "POST" else srv.notes_reply)
            do_GET = do_POST = handle_any
        srv.RequestHandlerClass = Short
        r = self.run_it("--import-notes", f, "--key", "k")
        self.assertEqual(r.returncode, 4)
        self.assertIn("says it took 1", r.stderr)

    def test_feature_must_exist(self):
        self.srv.force = (404, {}, [])
        r = self.run_it("--import-notes", self.export(), "--key", "k")
        self.assertEqual(r.returncode, 4)
        self.assertIn("Publish the page first", r.stderr)

    def test_wrong_shape(self):
        r = self.run_it("--import-notes", self.write(os.path.join(self.home, "e.json"), "[]"), "--key", "k")
        self.assertEqual(r.returncode, 1)


class Flags(Base):
    def test_wrong_combinations(self):
        for args in ([], ["--job", "a", "--page", "b"], ["--notes"], ["--notes", "--import-notes", "f", "--key", "k"], ["--since", "2026-11-05T00:00:00Z", "--job", "a"], ["--import-notes", "f"]):
            self.assertEqual(self.run_it(*args).returncode, 2, args)


if __name__ == "__main__":
    unittest.main()
