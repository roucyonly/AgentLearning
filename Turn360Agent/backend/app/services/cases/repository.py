import json
from functools import cached_property
from pathlib import Path
from typing import Any


class CaseRepository:
    def __init__(self, case_file: Path | None = None) -> None:
        root = Path(__file__).resolve().parents[4]
        self.case_file = case_file or root / "docs" / "seed-cases-yongge-mvp.json"

    @cached_property
    def _cases(self) -> list[dict[str, Any]]:
        with self.case_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("seed case file must contain a JSON array")
        return data

    def list_cases(self) -> list[dict[str, Any]]:
        return self._cases

    def get_case(self, case_id: str) -> dict[str, Any] | None:
        return next((case for case in self._cases if case.get("case_id") == case_id), None)

    def list_case_summaries(self) -> list[dict[str, Any]]:
        summaries: list[dict[str, Any]] = []
        for case in self._cases:
            finance = case.get("finance_indicators", {})
            summaries.append(
                {
                    "case_id": case.get("case_id"),
                    "title": case.get("title"),
                    "business_stage": case.get("business_stage"),
                    "case_usage": case.get("case_usage"),
                    "finance_mode": finance.get("mode"),
                    "risk_flags": case.get("risk_flags", []),
                }
            )
        return summaries

