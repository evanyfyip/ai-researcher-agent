from .base_tool import ResearchTool
from typing import List, Dict, Any
import requests
import html
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
    def _best_rss_text(self, entry) -> str:
        # 1) Prefer full content blocks if present
        if getattr(entry, "content", None):
            # entry.content is usually a list of dict-like objects
            val = entry.content[0].get("value") if entry.content else None
            if val:
                return val

        # 2) Some feeds store full HTML in these fields
        for key in ("content_encoded", "content:encoded", "description", "summary"):
            val = getattr(entry, key, None)
            if val:
                return val

        return "No summary"
    
    def _clean_html_fragment(self, s: str) -> str:
        # Unescape &lt; &amp; etc.
        s = html.unescape(s)
        # Strip HTML tags while keeping readable text
        return BeautifulSoup(s, "html.parser").get_text(" ", strip=True)

    def _is_year_only_date(self, date_str: str | None) -> bool:
        if not date_str:
            return False
        return bool(re.fullmatch(r"\d{4}", date_str.strip()))

    def _search_rss(self, query: str, topics: List[str] = None, days_back: int = 7) -> List[Dict[str, Any]]:
        feed_url = self.config.get("url") or self.config.get("feed_url")
        if not feed_url:
            return []

        feed = feedparser.parse(feed_url)
        results = []
        since = datetime.now(timezone.utc) - timedelta(days=days_back)
        max_results = self.config.get("max_results", 5)

        for entry in feed.entries:
            # published_parsed may be missing; try updated_parsed; else skip recency filter
            published_dt = None
            if getattr(entry, "published_parsed", None):
                published_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif getattr(entry, "updated_parsed", None):
                published_dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            published_text = getattr(entry, "published", None) or getattr(entry, "updated", None)
            year_only_date = self._is_year_only_date(published_text)

            if published_dt and published_dt < since and not year_only_date:
                continue

            title = getattr(entry, "title", "No title")
            raw = self._best_rss_text(entry)
            summary = self._clean_html_fragment(raw)
            link = getattr(entry, "link", "#")

            content = (title + " " + summary).lower()
            effective_topics = topics if topics is not None else self.topics

            if topics:
                if not any(t.lower() in content for t in topics):
                    continue
            elif query:
                if query.lower() not in content:
                    continue
            else:
                if effective_topics and not any(t.lower() in content for t in effective_topics):
                    continue

            date_str = (published_dt or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
            results.append({
                "title": title,
                "summary": (summary[:300] + "...") if len(summary) > 300 else summary,
                "link": link,
                "date": date_str,
            })

            if len(results) >= max_results:
                break

        return results

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
