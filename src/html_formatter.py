from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape
from typing import Dict, List, Any
from markdown import markdown


class HTMLFormatter:
    """Render research pulse results into an HTML page."""

    def __init__(self, title: str = ""):
        self.title = title
    
    def _accent_color(self, name: str) -> str:
        """Use a consistent accent color for all sources."""
        return "#353434"

    def _render_summary(self, text: str) -> str:
        """Render markdown summary into HTML."""
        if not text:
            return "<p class=\"muted\">No summary available.</p>"
        # Ensure lists render correctly by inserting a blank line before list items when missing.
        lines = text.splitlines()
        fixed_lines = []
        prev_blank = True
        for line in lines:
            stripped = line.strip()
            is_numbered = len(stripped) > 1 and stripped[0].isdigit() and stripped[1:2] == "."
            is_list = stripped.startswith(("-", "*")) or is_numbered
            if is_list and not prev_blank:
                fixed_lines.append("")
            fixed_lines.append(line)
            prev_blank = stripped == ""
        fixed_text = "\n".join(fixed_lines)
        rendered = markdown(fixed_text, extensions=["extra", "sane_lists"])
        return f"<div class=\"md\">{rendered}</div>"


    def _render_posts(self, posts: List[Dict[str, Any]]) -> str:
        if not posts:
            return "<p class=\"muted\">No new posts found.</p>"
        items = []
        for post in posts:
            title = escape(post.get("title", "No title"))
            link = escape(post.get("link", "#"), quote=True)
            date = escape(post.get("date", "Unknown date"))
            summary = escape(post.get("summary", ""))
            items.append(
                """
                <li class=\"post\">
                    <div class=\"post-header\">
                        <a href=\"{link}\" target=\"_blank\" rel=\"noopener\">{title}</a>
                        <span class=\"post-date\">{date}</span>
                    </div>
                    <p class=\"post-summary\">{summary}</p>
                </li>
                """.format(link=link, title=title, date=date, summary=summary)
            )
        return "<ul class=\"posts\">" + "".join(items) + "</ul>"

    def format_pulse(self, overall_summary: str, sources: List[Dict[str, Any]]) -> str:
        generated_at = datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d %H:%M %Z")
        page = [
            "<!DOCTYPE html>",
            "<html lang=\"en\">",
            "<head>",
            f"<meta charset=\"UTF-8\">",
            f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
            f"<title>{escape(self.title)}</title>",
            "<style>" \
            "body{font-family:Inter,system-ui,-apple-system,sans-serif;background:#f6f7fb;color:#1f2a44;padding:32px;line-height:1.6;}" \
            ".page{max-width:1100px;margin:0 auto;}" \
            "header{margin-bottom:28px;padding:30px;border-radius:14px;background:#0f1f3a;color:#eaf1ff;position:relative;overflow:hidden;min-height:150px;display:flex;flex-direction:column;justify-content:flex-end;}" \
            "header::before{content:\"\";position:absolute;inset:0;background:url('assets/banners/header.jpg') center/cover no-repeat;opacity:1.0;mix-blend-mode:screen;}" \
            "header *{position:relative;z-index:1;}" \
            "h1{margin:0;font-size:28px;letter-spacing:0.2px;color:#eaf1ff;}" \
            ".timestamp{color:#c6d4f5;font-size:14px;margin-top:4px;}" \
            ".section{background:#ffffff;border:1px solid #e1e5f0;border-radius:14px;padding:16px 18px;margin-bottom:18px;box-shadow:0 10px 30px rgba(16,35,71,0.08);}" \
            ".section h2{margin:0 0 6px 0;font-size:18px;color:#0f1f3a;}" \
            ".muted{color:#7a829a;}" \
            ".md code{background:#e6eefc;color:#0f3c8a;border-radius:10px;padding:2px 6px;font-size:0.92em;font-weight:600;}" \
            ".md pre code{display:block;padding:10px 12px;}" \
            ".source-card{margin-top:16px;border-top: 0px solid var(--accent, #3f4c62);padding-top:16px;background:#fff;}" \
            ".card-banner{height:130px;border-radius:12px;background-size:cover;background-position:center;position:relative;margin:-6px -2px 12px -2px;overflow:hidden;box-shadow:inset 0 0 0 1px rgba(0,0,0,0.03);}" \
            ".overview-banner{display:flex;align-items:center;justify-content:center;color:#fff;}" \
            ".overview-label{font-size:18px;font-weight:700;text-shadow:0 2px 6px rgba(0,0,0,0.35);}" \
            ".source-header{display:flex;align-items:center;justify-content:space-between;gap:10px;}" \
            ".source-head-left{display:flex;align-items:center;gap:8px;}" \
            ".source-title{font-size:18px;font-weight:700;color:#0f1f3a;margin:0;}" \
            ".source-link{font-size:13px;color:#1b6ac9;text-decoration:none;font-weight:600;}" \
            ".source-link:hover{text-decoration:underline;}" \
            ".source-toggle{margin-left:auto;font-size:12px;background:#e6eefc;color:#0f3c8a;border:1px solid #c8d6f7;border-radius:10px;padding:4px 8px;cursor:pointer;}" \
            ".source-toggle:hover{background:#d9e4fb;}" \
            ".source-body{display:none;margin-top:10px;}" \
            ".source-body.open{display:block;}" \
            ".posts{list-style:none;padding:0;margin:0;}" \
            ".post{padding:12px 14px;border:1px solid #e8ecf5;border-radius:12px;margin:10px 0;background:linear-gradient(135deg, rgba(27,106,201,0.07), rgba(255,255,255,0.96));box-shadow:0 6px 18px rgba(16,35,71,0.05);}" \
            ".post:first-child{margin-top:4px;}" \
            ".post-header{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;}" \
            ".post-header a{color:#1b6ac9;text-decoration:none;font-weight:600;}" \
            ".post-header a:hover{text-decoration:underline;}" \
            ".post-date{color:#7a829a;font-size:12px;white-space:nowrap;}" \
            ".post-summary{margin:6px 0 0 0;color:#35405c;}" \
            ".md ul{padding-left:20px;margin:6px 0;}" \
            ".md p{margin:6px 0;}" \
            "</style>",
            "</head>",
            "<body>",
            "<div class=\"page\">",
            "<header>",
            f"<h1>{escape(self.title)}</h1>",
            f"<div class=\"timestamp\">Updated {escape(generated_at)}</div>",
            "</header>",
            "<div class=\"section\">",
            "<div class=\"card-banner overview-banner\" style=\"background-image:url('assets/banners/overview.jpg'); height:75px;\">",
            "<div class=\"overview-label\">Overview</div>",
            "</div>",
            self._render_summary(overall_summary),
            "</div>",
        ]

        for source in sources:
            name = source.get('name', 'Source')
            accent = self._accent_color(name)
            safe_banner = name.lower().replace(" ", "_")
            banner_url = escape(source.get("banner_url") or f"assets/banners/{safe_banner}.jpg", quote=True)
            source_url = escape(source.get("source_url") or "#", quote=True)
            source_id = escape(name.lower().replace(" ", "_"))
            display_title = source.get("description") or name
            page.extend(
                [
                    f"<div class=\"section source-card\" style=\"--accent:{accent};\">",
                    f"<div class=\"card-banner\" style=\"background-image:url('{banner_url}');\"></div>",
                    "<div class=\"source-header\">",
                    "<div class=\"source-head-left\">",
                    f"<h1 class=\"source-title\">{escape(display_title)}</h1>",
                    f"<a class=\"source-link\" href=\"{source_url}\" target=\"_blank\" rel=\"noopener\">link</a>",
                    "</div>",
                    f"<button class=\"source-toggle\" data-target=\"{source_id}\">Expand</button>",
                    "</div>",
                    f"<div class=\"source-body\" id=\"{source_id}\">",
                    self._render_summary(source.get("summary", "")),
                    "<h3>New Posts</h3>",
                    self._render_posts(source.get("items", [])),
                    "</div>",
                    "</div>",
                ]
            )

        page.extend([
            "</div>",
            "<script>",
            "document.querySelectorAll('.source-toggle').forEach(btn=>{",
            "  btn.addEventListener('click',()=>{",
            "    const id = btn.getAttribute('data-target');",
            "    const body = document.getElementById(id);",
            "    const open = body.classList.toggle('open');",
            "    btn.textContent = open ? 'Collapse' : 'Expand';",
            "  });",
            "});",
            "</script>",
            "</body>",
            "</html>",
        ])
        return "".join(page)
