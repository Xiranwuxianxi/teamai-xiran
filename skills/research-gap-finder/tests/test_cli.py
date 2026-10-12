#!/usr/bin/env python3
"""Offline tests for the research-gap CLI (stdlib only)."""
import subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "research_gap_cli.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(CLI), *args], text=True,
                          capture_output=True, check=False)


class ResearchGapCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="rgf-test-")
        self.proj = Path(self.tmp) / "proj"

    def test_selftest_pipeline(self) -> None:
        proc = run_cli("selftest", "--dir", self.proj)
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)

    def test_init_and_status(self) -> None:
        proc = run_cli("init", "--dir", str(self.proj), "--topic", "Test topic",
                       "--pico", '{"population":"X"}')
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertTrue((self.proj / "config.json").is_file())
        self.assertTrue((self.proj / "evidence.json").is_file())
        status = run_cli("status", "--dir", str(self.proj))
        self.assertEqual(status.returncode, 0, msg=status.stdout + status.stderr)
        self.assertIn("Test topic", status.stdout)

    def test_taxonomy_classifier(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        import research_gap_cli as rgc  # noqa: E402
        # a population/theoretical gap should classify to 'population' or 'theoretical'
        t, sec = rgc.classify_type("No studies exist in elderly rural populations; the mechanism remains unclear.")
        self.assertIn(t, {"population", "theoretical", "evidence"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
