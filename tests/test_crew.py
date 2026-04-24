import pytest
from unittest.mock import MagicMock, patch
from agentti.crew import build_crew

def test_crew_initialization():
    # Testataan, että crew rakentuu ilman virheitä
    crew = build_crew("Testitehtävä")
    assert len(crew.agents) > 0
    assert crew.tasks[0].description.contains("Testitehtävä")

@patch('crewai.Agent.execute_task')
def test_agent_logic_without_llm(mock_execute):
    # Mockataan agentin vastaus, ettei se yritä ottaa yhteyttä Ollamaan
    mock_execute.return_value = "Tietokannassa on taulut: Zone, Visit."
    
    crew = build_crew("Listaa taulut")
    result = crew.kickoff()
    
    assert "Zone" in str(result)