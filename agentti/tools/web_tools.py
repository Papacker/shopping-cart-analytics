from crewai.tools import tool
from duckduckgo_search import DDGS

@tool("search_web")
def search_web(hakusana: str) -> str:
    """Hyödyllinen, kun sinun täytyy etsiä tietoa, ideoita tai ajankohtaisia asioita internetistä (esim. kaupan alan trendit). Anna hakusana stringinä."""
    try:
        results = DDGS().text(hakusana, max_results=5)
        if not results:
            return "Ei hakutuloksia."
        
        teksti = "Internetin hakutulokset:\n\n"
        for r in results:
            teksti += f"Otsikko: {r.get('title')}\n"
            teksti += f"Kuvaus: {r.get('body')}\n"
            teksti += f"URL: {r.get('href')}\n\n"
            
        return teksti
    except Exception as e:
        return f"Virhe internet-haussa: {str(e)}"
