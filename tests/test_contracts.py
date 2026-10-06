"""Contract tests for request validation and triage scale consistency."""

import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from pydantic import ValidationError

from backend.main import (
    DISCHARGE_QUESTIONS,
    EXAMPLES_DIR,
    PRIORITY_QUESTIONS,
    DecisionRequest,
    discharge,
    get_example_file,
    health,
    priority,
    search_examples,
)
from scripts import generate_examples


class RequestContractTests(unittest.TestCase):
    def test_report_is_trimmed_and_bounded(self):
        self.assertEqual(DecisionRequest(report="  fictional case  ").report, "fictional case")
        with self.assertRaises(ValidationError):
            DecisionRequest(report="   ")
        with self.assertRaises(ValidationError):
            DecisionRequest(report="x" * 40_001)

    def test_triage_scale_orders_esi_one_as_most_urgent(self):
        criteria = PRIORITY_QUESTIONS["priority"]["criteria"]
        instructions = PRIORITY_QUESTIONS["priority"]["instructions"]
        self.assertIn("1 - ESI-1", criteria[0])
        self.assertIn("5 - ESI-5", criteria[-1])
        self.assertIn("most urgent", instructions)
        self.assertIn("least urgent", instructions)

    def test_health_response_identifies_service(self):
        self.assertEqual(health()["status"], "ok")


class QuestionPayloadContractTests(unittest.TestCase):
    REQUIRED_FIELDS_BY_TYPE = {
        "noul": ("instructions",),
        "score": ("instructions", "criteria"),
        "choice": ("instructions", "criteria"),
    }

    def test_every_question_carries_required_fields(self):
        for name, questions in (("discharge", DISCHARGE_QUESTIONS), ("priority", PRIORITY_QUESTIONS)):
            for key, question in questions.items():
                with self.subTest(endpoint=name, question=key):
                    self.assertIn("type", question, "question must declare a type")
                    required = self.REQUIRED_FIELDS_BY_TYPE[question["type"]]
                    for field in required:
                        self.assertIn(field, question, f"{question['type']} questions require '{field}'")
                    self.assertTrue(question["instructions"].strip())

    def test_score_criteria_are_non_empty_lists(self):
        for questions in (DISCHARGE_QUESTIONS, PRIORITY_QUESTIONS):
            for key, question in questions.items():
                if question["type"] == "score":
                    with self.subTest(question=key):
                        self.assertIsInstance(question["criteria"], list)
                        self.assertGreater(len(question["criteria"]), 0)

    def test_choice_criteria_are_non_empty_dicts(self):
        for questions in (DISCHARGE_QUESTIONS, PRIORITY_QUESTIONS):
            for key, question in questions.items():
                if question["type"] == "choice":
                    with self.subTest(question=key):
                        self.assertIsInstance(question["criteria"], dict)
                        self.assertGreater(len(question["criteria"]), 0)


class RouteDelegationTests(unittest.IsolatedAsyncioTestCase):
    async def test_discharge_route_uses_discharge_questions(self):
        expected = {"answers": {"discharge": {"noul": 0.1}}}
        with patch("backend.main.call_systemone", new_callable=AsyncMock) as call:
            call.return_value = expected
            response = await discharge(DecisionRequest(report="fictional case"))
        self.assertEqual(response, expected)
        call.assert_awaited_once_with(DISCHARGE_QUESTIONS, "fictional case")

    async def test_priority_route_uses_priority_questions(self):
        expected = {"answers": {"priority": {"score": 1}}}
        with patch("backend.main.call_systemone", new_callable=AsyncMock) as call:
            call.return_value = expected
            response = await priority(DecisionRequest(report="fictional case"))
        self.assertEqual(response, expected)
        call.assert_awaited_once_with(PRIORITY_QUESTIONS, "fictional case")

    async def test_discharge_simple_mode_sends_single_question(self):
        with patch("backend.main.call_systemone", new_callable=AsyncMock) as call:
            call.return_value = {"answers": {"discharge": {"noul": 0.1}}}
            await discharge(DecisionRequest(report="fictional case"), simple=True)
        call.assert_awaited_once_with({"discharge": DISCHARGE_QUESTIONS["discharge"]}, "fictional case")

    async def test_priority_simple_mode_sends_single_question(self):
        with patch("backend.main.call_systemone", new_callable=AsyncMock) as call:
            call.return_value = {"answers": {"priority": {"score": 1}}}
            await priority(DecisionRequest(report="fictional case"), simple=True)
        call.assert_awaited_once_with({"priority": PRIORITY_QUESTIONS["priority"]}, "fictional case")


class ExamplesEndpointsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.examples_dir = Path(self._tmp.name).resolve()
        nested = self.examples_dir / "cases"
        nested.mkdir()
        (nested / "case_a.txt").write_text("Patient reports chest pain and shortness of breath.", encoding="utf-8")
        (nested / "case_b.txt").write_text("Patient has a minor laceration on the left hand.", encoding="utf-8")
        (self.examples_dir / "case_c.txt").write_text("No relevant findings here.", encoding="utf-8")

    async def test_search_is_case_insensitive_and_recursive(self):
        with patch("backend.main.EXAMPLES_DIR", self.examples_dir):
            response = await search_examples(q="CHEST")
        files = [result["file"] for result in response["results"]]
        self.assertIn(str(Path("cases") / "case_a.txt"), files)
        self.assertNotIn(str(Path("cases") / "case_b.txt"), files)

    async def test_search_context_contains_keyword(self):
        with patch("backend.main.EXAMPLES_DIR", self.examples_dir):
            response = await search_examples(q="laceration")
        self.assertEqual(len(response["results"]), 1)
        self.assertIn("laceration", response["results"][0]["context"].lower())

    async def test_file_endpoint_returns_content(self):
        with patch("backend.main.EXAMPLES_DIR", self.examples_dir):
            response = await get_example_file(path=str(Path("cases") / "case_a.txt"))
        self.assertIn("chest pain", response["content"])

    async def test_file_endpoint_rejects_path_traversal(self):
        with patch("backend.main.EXAMPLES_DIR", self.examples_dir):
            with self.assertRaises(HTTPException) as ctx:
                await get_example_file(path="../secrets.txt")
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_file_endpoint_rejects_missing_file(self):
        with patch("backend.main.EXAMPLES_DIR", self.examples_dir):
            with self.assertRaises(HTTPException) as ctx:
                await get_example_file(path="cases/missing.txt")
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_examples_dir_uses_resolved_path(self):
        self.assertTrue(EXAMPLES_DIR.is_absolute())
        self.assertEqual(EXAMPLES_DIR, EXAMPLES_DIR.resolve())


class ExampleGeneratorTests(unittest.TestCase):
    def test_generation_is_reproducible_and_preserves_other_files(self):
        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            sentinel = output_dir / "keep-this.txt"
            sentinel.write_text("unrelated fixture", encoding="utf-8")

            with patch.object(
                sys,
                "argv",
                ["generate_examples.py", "--count", "4", "--seed", "7", "--output-dir", directory],
            ), redirect_stdout(StringIO()):
                generate_examples.main()
            first_run = {
                path.name: path.read_text(encoding="utf-8")
                for path in output_dir.glob("case_*.txt")
            }

            with patch.object(
                sys,
                "argv",
                ["generate_examples.py", "--count", "4", "--seed", "7", "--output-dir", directory],
            ), redirect_stdout(StringIO()):
                generate_examples.main()
            second_run = {
                path.name: path.read_text(encoding="utf-8")
                for path in output_dir.glob("case_*.txt")
            }

            self.assertEqual(first_run, second_run)
            self.assertEqual(len(first_run), 4)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "unrelated fixture")


if __name__ == "__main__":
    unittest.main()
