from .base_tool import ResearchTool
from typing import List, Dict, Any
from langchain_community.utilities import SerpAPIWrapper
from datetime import datetime, timedelta
import os

class WebSearchTool(ResearchTool):
    def __init__(self, topics: List[str]):
        super().__init__("web_search", topics)
        self.api_key = os.getenv("SERPAPI_API_KEY")
        if self.api_key:
            self.searcher = SerpAPIWrapper(serpapi_api_key=self.api_key)
        else:
            self.searcher = None

    def search(self, query: str, topics: List[str] = None, days_back: int = 7) -> List[Dict[str, Any]]:
        if not self.searcher:
            return []

        if topics:
            full_query = f"{query} {' '.join(topics)}"
        else:
            full_query = query

        # Add date filter if needed
        if days_back < 30:
            full_query += f" after:{(datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')}"

        results = self.searcher.results(full_query)
        parsed = []
        for res in results.get('organic_results', [])[:5]:
            parsed.append({
                'title': res.get('title', ''),
                'summary': res.get('snippet', ''),
                'link': res.get('link', ''),
                'date': res.get('date', '')
            })
        return parsed