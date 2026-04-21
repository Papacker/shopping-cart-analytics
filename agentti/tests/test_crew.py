"""
test_crew.py — Yksikkotest crew.py:lle.
Kattaa: _TESTI_AVAINSANAT-reitityslogiikka, build_tester_crew, build_crew rakenne.
LLM-yhteyksia ei testata — testataan vain Python-logiikka.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

AGENTTI_DIR = Path(__file__).resolve().parent.parent
if str(AGENTTI_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTTI_DIR))

import pytest


# ── _TESTI_AVAINSANAT reititys (puhdas Python-logiikka) ──────────

class TestTestiAvainsanat:
    @pytest.fixture(autouse=True)
    def import_crew(self):
        import crew as crew_module
        self.crew = crew_module

    def test_testaa_triggers_test_route(self):
        kw = self.crew._TESTI_AVAINSANAT
        assert any("testaa agentti/crew.py".lower().startswith(k) for k in kw)

    def test_testa_triggers_test_route(self):
        kw = self.crew._TESTI_AVAINSANAT
        assert any("testa src/app.py".lower().startswith(k) for k in kw)

    def test_analysoi_goes_to_analysis(self):
        kw = self.crew._TESTI_AVAINSANAT
        assert not any("analysoi tietokanta".lower().startswith(k) for k in kw)

    def test_pytest_keyword(self):
        kw = self.crew._TESTI_AVAINSANAT
        assert any("pytest src/app.py".lower().startswith(k) for k in kw)

    def test_pylint_keyword(self):
        kw = self.crew._TESTI_AVAINSANAT
        assert any("pylint agentti/crew.py".lower().startswith(k) for k in kw)

    def test_coverage_keyword(self):
        kw = self.crew._TESTI_AVAINSANAT
        assert any("coverage agentti/".lower().startswith(k) for k in kw)

    def test_hae_does_not_trigger(self):
        kw = self.crew._TESTI_AVAINSANAT
        assert not any("hae tiedot".lower().startswith(k) for k in kw)

    def test_empty_string_does_not_trigger(self):
        kw = self.crew._TESTI_AVAINSANAT
        assert not any("".startswith(k) for k in kw)


# ── File path extraction from task string ────────────────────────

class TestFilePathExtraction:
    """Testaa tiedostopolun poimimista tehtavakuvauksesta."""

    def _extract(self, task: str, keywords) -> str:
        file_path = task.strip()
        for kw in keywords:
            if file_path.lower().startswith(kw):
                file_path = file_path[len(kw):].strip()
                break
        return file_path

    def test_extract_from_testaa(self):
        import crew as m
        result = self._extract("testaa agentti/crew.py", m._TESTI_AVAINSANAT)
        assert result == "agentti/crew.py"

    def test_extract_from_pytest(self):
        import crew as m
        result = self._extract("pytest src/app.py", m._TESTI_AVAINSANAT)
        assert result == "src/app.py"

    def test_extract_preserves_full_path(self):
        import crew as m
        result = self._extract("testaa agentti/tools/tester_agent.py", m._TESTI_AVAINSANAT)
        assert result == "agentti/tools/tester_agent.py"


# ── build_tester_crew rakenne ─────────────────────────────────────

class TestBuildTesterCrew:
    def test_has_one_agent(self):
        import crew as m
        c = m.build_tester_crew("agentti/crew.py")
        assert len(c.agents) == 1

    def test_has_one_task(self):
        import crew as m
        c = m.build_tester_crew("agentti/crew.py")
        assert len(c.tasks) == 1

    def test_task_description_contains_filepath(self):
        import crew as m
        c = m.build_tester_crew("src/app.py")
        assert "src/app.py" in c.tasks[0].description


# ── build_crew rakenne ────────────────────────────────────────────

class TestBuildCrew:
    def test_has_four_agents(self):
        import crew as m
        c = m.build_crew("analysoi tietokanta")
        assert len(c.agents) == 4

    def test_has_three_tasks(self):
        import crew as m
        c = m.build_crew("analysoi tietokanta")
        assert len(c.tasks) == 3

    def test_first_task_contains_description(self):
        import crew as m
        c = m.build_crew("listaa taulut")
        assert "listaa taulut" in c.tasks[0].description


# ── main() testausreitti suoran kutsun kautta ─────────────────────

class TestMainTestRoute:
    def test_testaa_route_calls_run_test_file(self, monkeypatch, capsys, tmp_path):
        import crew as m
        called_with = []

        def fake_run(path):
            called_with.append(path)
            return f"# Testitulokset: {path}\n\n## OK"

        monkeypatch.setattr("tools.tester_agent._run_test_file", fake_run)
        monkeypatch.setattr(m, "_run_test_file", fake_run)
        monkeypatch.setattr("tools.tester_agent.WORKSPACE", tmp_path)
        monkeypatch.setattr(m, "TESTER_WORKSPACE", tmp_path)
        monkeypatch.setattr(sys, "argv", ["crew.py", "testaa", "agentti/crew.py"])

        m.main()

        assert len(called_with) == 1
        assert called_with[0] == "agentti/crew.py"
