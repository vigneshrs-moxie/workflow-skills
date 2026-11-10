"""build.py in job mode and outside it, on the skill's own examples in a throwaway HOME. Run: python3 -m unittest test_build -v"""
import json, os, shutil, subprocess, sys, tempfile, unittest

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "build.py")
PROTOTYPE_SECTIONS = os.path.join(HERE, "example", "prototype-sections.html")
REVIEW_SECTIONS = os.path.join(HERE, "example", "sections.html")
SLUG = "orbit-900-made-up-job"
REFUSED = "A job's screens are always the prototype page. Drop --fidelity, or build outside a job."


class Build(unittest.TestCase):
    def setUp(self):
        # HOME is a temporary folder, so ~/.claude/wireframes and ~/.claude/feature-work are both inside it.
        self.home = tempfile.mkdtemp(prefix="build-test-")
        self.addCleanup(shutil.rmtree, self.home)
        self.job = os.path.join(self.home, ".claude", "feature-work", SLUG)
        os.makedirs(self.job)
        self.cwd = os.path.join(self.home, "work")  # not a git repository: the page is "ideas"
        os.makedirs(self.cwd)

    def run_it(self, *args):
        env = {**os.environ, "HOME": self.home, "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("STARBASE_FEATURES_DIR", None)
        env.pop("WORKSHOP_FEATURES_DIR", None)
        return subprocess.run([sys.executable, SCRIPT, "--title", "Download invoices", *args],
                              capture_output=True, text=True, env=env, cwd=self.cwd, timeout=30)

    def read(self, *parts):
        with open(os.path.join(*parts), encoding="utf-8") as f:
            return f.read()

    def test_a_job_page_is_a_prototype(self):
        """a job page is a prototype"""
        r = self.run_it("--sections", PROTOTYPE_SECTIONS, "--preset", "mono", "--job", SLUG)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('id="pt-', self.read(self.job, "wireframes.html"))
        self.assertEqual(json.loads(self.read(self.job, "wireframes.json"))["fidelity"], "high")

    def test_a_job_with_fidelity_lo_is_refused(self):
        """a job with --fidelity lo is refused"""
        r = self.run_it("--sections", REVIEW_SECTIONS, "--fidelity", "lo", "--job", SLUG)
        self.assertEqual(r.returncode, 2)
        self.assertIn(REFUSED, r.stderr)
        self.assertEqual(os.listdir(self.job), [])

    def test_a_job_with_no_theme_uses_the_bundled_preset(self):
        """a job with no theme uses the bundled preset"""
        r = self.run_it("--sections", PROTOTYPE_SECTIONS, "--job", SLUG)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("preset", r.stdout)
        self.assertIn('id="pt-', self.read(self.job, "wireframes.html"))
        self.assertEqual(json.loads(self.read(self.job, "wireframes.json"))["tier"], "preset")

    def test_outside_a_job_lo_fi_still_builds_the_review_page(self):
        """outside a job lo-fi still builds the review page"""
        r = self.run_it("--sections", REVIEW_SECTIONS, "--fidelity", "lo")
        self.assertEqual(r.returncode, 0, r.stderr)
        page = self.read(self.home, ".claude", "wireframes", "ideas", "download-invoices.html")
        self.assertNotIn('id="pt-', page)
        self.assertEqual(os.listdir(self.job), [])


if __name__ == "__main__":
    unittest.main()
