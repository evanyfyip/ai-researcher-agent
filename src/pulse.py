#!/usr/bin/env python3
"""
Generate research pulse reports (HTML, Markdown, JSON) or regenerate from saved JSON.
"""
import argparse
import json
import shutil
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

from src.agent import ResearcherAgent
from src.html_formatter import HTMLFormatter


OUTPUT_ROOT = Path("output")


def _timestamp_slug() -> str:
    return datetime.now(ZoneInfo("America/Los_Angeles")).strftime("generated_at_%Y%m%d_%H%M%S")


def _ensure_assets(dest_dir: Path):
    """Copy banner assets alongside the report for relative paths."""
    src_assets = Path("assets")
    if not src_assets.exists():
        return
    dest_assets = dest_dir / "assets"
    if dest_assets.exists():
        return
    shutil.copytree(src_assets, dest_assets)


def _resolve_json_path(arg: str) -> Path:
    candidate = Path(arg)
    if candidate.is_dir():
        return candidate / "report.json"
    if candidate.suffix.lower() == ".json":
        return candidate
    return OUTPUT_ROOT / arg / "report.json"


def write_report_from_live():
    agent = ResearcherAgent()
    markdown_content, data = agent.pulse_search(output_format="markdown", return_data=True)
    html_content = agent.html_formatter.format_pulse(data["overall_summary"], data["sources"])

    output_dir = OUTPUT_ROOT / _timestamp_slug()
    output_dir.mkdir(parents=True, exist_ok=True)
    _ensure_assets(output_dir)

    md_path = output_dir / "pulse_report.md"
    html_path = output_dir / "pulse_report.html"
    json_path = output_dir / "report.json"

    md_path.write_text(markdown_content, encoding="utf-8")
    html_path.write_text(html_content, encoding="utf-8")
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print(f"Reports generated in: {output_dir}")
    print(f"- Markdown: {md_path}")
    print(f"- HTML:     {html_path}")
    print(f"- JSON:     {json_path}")


def write_report_from_json(json_arg: str):
    json_path = _resolve_json_path(json_arg)
    if not json_path.exists():
        raise FileNotFoundError(f"Could not find JSON at {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    output_dir = json_path.parent
    _ensure_assets(output_dir)

    combined_markdown = data.get("combined_markdown")
    if not combined_markdown:
        sections = data.get("sections_markdown", [])
        combined_markdown = f"# Pulse Summary\n{data.get('overall_summary','')}\n\n" + "\n\n".join(sections)

    formatter = HTMLFormatter()
    html_content = formatter.format_pulse(data.get("overall_summary", ""), data.get("sources", []))

    md_path = output_dir / "pulse_report.md"
    html_path = output_dir / "pulse_report.html"

    md_path.write_text(combined_markdown, encoding="utf-8")
    html_path.write_text(html_content, encoding="utf-8")

    print(f"Regenerated reports in: {output_dir}")
    print(f"- Markdown: {md_path}")
    print(f"- HTML:     {html_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate or regenerate research pulse reports.")
    parser.add_argument("--from-json", dest="from_json", help="Path or subfolder to report.json to regenerate outputs")
    args = parser.parse_args()

    if args.from_json:
        write_report_from_json(args.from_json)
    else:
        write_report_from_live()


if __name__ == "__main__":
    main()
