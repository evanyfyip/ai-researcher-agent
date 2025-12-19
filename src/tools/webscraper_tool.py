from .base_tool import ResearchTool
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime, timedelta, timezone
from dateutil import parser
import re
from dateutil import parser

class WebScraperTool(ResearchTool):
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.topics = config.get('topics', [])

    def _parse_date(self, date_str: str) -> datetime or None:
        """Helper to parse date string into datetime object."""
        try:
            return parser.parse(date_str)
        except (ValueError, TypeError):
            return None

    def search(self, query: str, topics: List[str] = None, days_back: int = 7) -> List[Dict[str, Any]]:
        if self.config['type'] == 'rss':
            return self._search_rss(query, topics, days_back)
        elif self.config['type'] == 'html':
            return self._search_html(query, topics, days_back)
        else:
            return []

    def _search_rss(self, query: str, topics: List[str] = None, days_back: int = 7) -> List[Dict[str, Any]]:
        feed = feedparser.parse(self.config['url'])
        results = []
        since = datetime.now(timezone.utc) - timedelta(days=days_back)

        for entry in feed.entries:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc) if entry.published_parsed else datetime.now(timezone.utc)
            if published >= since:
                title = entry.title
                summary = entry.summary if 'summary' in entry else "No summary"
                link = entry.link
                # Filter by topics if provided
                content = (title + " " + summary).lower()
                if topics:
                    if not any(topic.lower() in content for topic in topics):
                        continue
                elif query:
                    if query.lower() not in content:
                        continue
                else:
                    if not any(topic.lower() in content for topic in self.topics):
                        continue
                results.append({
                    'title': title,
                    'summary': summary[:300] + "..." if len(summary) > 300 else summary,
                    'link': link,
                    'date': published.strftime('%Y-%m-%d')
                })
        return results[:5]

    def _search_html(self, query: str, topics: List[str] = None, days_back: int = 7) -> List[Dict[str, Any]]:
        search_terms = topics + [query] if query else topics if topics else self.topics
        base_url = self.config['base_url']
        full_query = " ".join(search_terms)
        url = base_url + requests.utils.quote(full_query)

        use_playwright = self.config.get('use_playwright', False)
        if use_playwright:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(url)
                page.wait_for_selector(self.config['article_selector'])
                html = page.content()
                browser.close()
        else:
            headers = {
                'User-Agent': 'PostmanRuntime/7.49.1',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            response = requests.get(url, headers=headers)
            html = response.text
        
        soup = BeautifulSoup(html, 'html.parser')

        article_selector = self.config['article_selector']
        title_sel = self.config['title_selector']
        link_sel = self.config['link_selector']
        summary_sel = self.config.get('summary_selector')

        articles = soup.select(article_selector)
        print(f"=== Scraping Articles From {self.name}===")
        print(f"Found {len(articles)} articles")
        if not articles:
            print("No articles found with the given selector.")
            return []
        results = []
        since = datetime.now() - timedelta(days=days_back)

        for i, article in enumerate(articles[:self.config.get('max_results', 5)]):
            title_tag = article.select_one(title_sel)
            title = title_tag.text.strip() if title_tag else "No title"
            link_tag = article.select_one(link_sel)
            link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else "#"
            summary_tag = article.select_one(summary_sel) if summary_sel else None
            summary = summary_tag.text.strip() if summary_tag else "No summary"
            
            # Parse date using date_selector
            date_sel = self.config.get('date_selector')
            date = None
            if date_sel:
                date_tag = article.select_one(date_sel)
                date_text = date_tag.text.strip() if date_tag else None
                if date_text:
                    parsed = self._parse_date(date_text)
                    if parsed:
                        date = parsed.strftime('%Y-%m-%d')
                    else:
                        date = datetime.now(timezone.utc).strftime('%Y-%m-%d')  # Fallback
                else:
                    date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            else:
                date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            
            # Check if within days_back
            if date:
                article_date = self._parse_date(date)
                if article_date and article_date >= since:
                    print(f"Article {i+1} is recent: {title}, posted on {date}")
                    results.append({
                        'title': title,
                        'summary': summary,
                        'link': link,
                        'date': date
                    })
                else:
                    print(f"Article {i+1} is not recent: {title}, posted on {date}")
            else:
                # If no date, assume recent
                results.append({
                    'title': title,
                    'description': self.config.get('description', ''),
                    'summary': summary,
                    'link': link,
                    'date': date
                })
        return results