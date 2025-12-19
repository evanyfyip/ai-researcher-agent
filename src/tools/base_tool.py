from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime, timedelta
import yaml

class ResearchTool(ABC):
    def __init__(self, name: str, topics: List[str]):
        self.name = name
        self.topics = topics

    @abstractmethod
    def search(self, query: str, topics: List[str] = None, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Search for content based on query and topics.
        Returns list of dicts with keys: title, summary, link, date
        """
        pass

    def get_recent(self, topics: List[str] = None, days_back: int = 1) -> List[Dict[str, Any]]:
        """
        Get recent developments from the source.
        """
        if topics is None:
            topics = self.topics
        # Default implementation: search with empty query
        return self.search("", topics, days_back)

    def format_output(self, results: List[Dict[str, Any]]) -> str:
        """
        Format results into a summary string.
        """
        if not results:
            return f"No recent results from {self.name}."

        output = f"**{self.name.title()}:**\n"
        output += f"Description: {results[0].get('description', 'No description available.')}\n\n"
        for item in results:
            title = item.get('title', 'No title')
            summary = item.get('summary', 'No summary')[:200] + "..." if len(item.get('summary', '')) > 200 else item.get('summary', '')
            link = item.get('link', '#')
            date = item.get('date', 'Unknown date')
            output += f"- **{title}**: {summary} [Link]({link}) (Posted on: {date})\n"
        return output

    @staticmethod
    def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)