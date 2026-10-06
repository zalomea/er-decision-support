"""Frontend logic tests executed via Node when available."""

import shutil
import subprocess
import unittest

REPO_ROOT = __file__.rsplit("/tests/", 1)[0]
FRONTEND_TEST = f"{REPO_ROOT}/tests/frontend_logic.test.js"


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class FrontendLogicTests(unittest.TestCase):
    def test_frontend_logic_suite_passes(self):
        result = subprocess.run(
            ["node", "--test", FRONTEND_TEST],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"node --test failed:\n{result.stdout}\n{result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
