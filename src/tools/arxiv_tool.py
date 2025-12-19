from .base_tool import ResearchTool
from typing import List, Dict, Any
import arxiv
from datetime import datetime, timedelta, timezone

class ArxivTool(ResearchTool):
    def __init__(self, topics: List[str]):
        super().__init__("arxiv", topics)

    def search(self, query: str, topics: List[str] = None, days_back: int = 7) -> List[Dict[str, Any]]:
        if topics:
            search_terms = topics + [query] if query else topics
        else:
            search_terms = self.topics + [query] if query else self.topics

        # Combine topics into query
        full_query = " OR ".join(search_terms)

        # Search with date filter
        since = datetime.now(timezone.utc) - timedelta(days=days_back)
        search = arxiv.Search(
            query=full_query,
            max_results=10,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        results = []
        for paper in search.results():
            if paper.published >= since:
                results.append({
                    'title': paper.title,
                    'summary': paper.summary[:300] + "..." if len(paper.summary) > 300 else paper.summary,
                    'link': paper.pdf_url,
                    'date': paper.published.strftime('%Y-%m-%d')
                })
        return results