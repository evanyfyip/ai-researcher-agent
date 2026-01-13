from datetime import datetime
from zoneinfo import ZoneInfo
from langchain_anthropic import ChatAnthropic
from src.tools import WebSearchTool, ArxivTool, WebScraperTool
from src.tools.base_tool import ResearchTool
from src.html_formatter import HTMLFormatter
import yaml
import os
from typing import List, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

class ResearcherAgent:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = ResearchTool.load_config(config_path)
        self.banner_map = self.config.get('banners', {})
        self.llm = ChatAnthropic(
            model=os.environ["FOUNDRY_DEPLOYMENT"],
            api_key=os.environ["FOUNDRY_API_KEY"],
            base_url=os.environ["FOUNDRY_ENDPOINT"],
        )
        self._load_tools()
        self.html_formatter = HTMLFormatter()

    def _load_tools(self):
        tools_config = self.config['tools']
        self.tool_instances = {}
        for name, conf in tools_config.items():
            if name == 'web_search':
                self.tool_instances[name] = WebSearchTool(conf['topics'])
            elif name == 'arxiv':
                self.tool_instances[name] = ArxivTool(conf['topics'])
            elif name == 'webscrapers':
                for scraper_name, scraper_conf in conf.items():
                    scraper_conf['topics'] = scraper_conf.get('topics', [])
                    self.tool_instances[scraper_name] = WebScraperTool(scraper_name, scraper_conf)
    
    def _invoke_llm(self, system_prompt, user_prompt: str) -> str:
        messages = [
            (
                "system", system_prompt
            ),
            (
                "user", user_prompt
            )
        ]
        response = self.llm.invoke(messages)
        return response.content

    def _parse_output(self, output):
        """Parses the llm response, extracting json
        out of the xml tags <RESPONSE></RESPONSE>"""
        start_tag = "<RESPONSE>"
        end_tag = "</RESPONSE>"
        start_index = output.find(start_tag)
        end_index = output.find(end_tag)
        if start_index != -1 and end_index != -1:
            output_str = output[start_index + len(start_tag):end_index].strip()
            return output_str
        else:
            print("RESPONSE tags not found in LLM output.")
            return None
    
    def _generate_source_summary(self, source_output: str) -> str:
        """Generate a concise summary from source output using LLM."""
        system_prompt = """
        You are an expert AI Engineer and Researcher. Summarize the following
        recent developments from this source in concise language suitable for
        a technical audience. Highlight key advancements and trends as a bullet list.

        Return the summary and bullets within the following XML tags:
        <RESPONSE></RESPONSE>
        """
        user_prompt  = f"""
        Please summarize the following recent developments from following sources:

        {source_output}
        """
        response = self._invoke_llm(system_prompt, user_prompt)
        print("=== LLM Source Summary Response ===")
        print(f"Type: {type(response)}, Content: {response}")
        summary = self._parse_output(response)
        return summary

    def _generate_overview_summary(self, source_summaries: List[dict]) -> str:
        """
        Create a one-liner bullet overview per source, tagging items under:
        - Tools & Technologies
        - Foundational Knowledge
        - Risks & governance
        """
        system_prompt = """
        You are an AI research coordinator and keynote speaker sharing all the recent developments in AI research and technology.
        Produce a three sentence overview sentence (Call it AI Research Roundup) and produce a concise markdown bullet list.
        For each source, give ONE line that captures what to check out next, and note
        which categories apply: Tools & Technologies, Foundational Knowledge, Risks & governance.
        Keep it crisp and scannable.

        Here are the category details:
        1. Tools & Technologies: 
            - Specific AI tools, platforms, and models (productivity tools & production)
            - New releases or capabilities
            - Build vs. buy discussions
        2. Foundational Knowledge:
            - Common language and baseline knowledge
            - Concepts needed for productive discussion
            - Onboarding context for new participants
        3. Risks & governance:
            - Ethical, legal, and operational considerations
            - Accuracy, bias, and misuse
            - Data privacy and security
        
        ## Example Output:
        <RESPONSE>
        ## AI Research Roundup
        This week’s AI updates highlight a clear shift toward agentic systems, with Google, Microsoft, and OpenAI advancing agent-focused capabilities while research addresses the memory and tool-use challenges needed for production readiness. At the same time, progress in vision-language models and video generation shows generative AI continuing to move beyond text. Safety and governance efforts are also maturing, with compliance frameworks and system cards emerging as competitive differentiators, alongside research into LLM reasoning and interpretability.
        
        ---

        ## Key Updates: 
        1. **Tools & Technologies:**

            - OpenAI’s GPT-5.2-Codex debuts as an agentic coding model with detailed safety mitigations for professional software engineering and cybersecurity work.

            - Google Gemini 3 Flash launches with “frontier intelligence built for speed,” optimizing inference performance without sacrificing capability.

            - Microsoft Foundry rebrand signals expanded platform scope beyond Azure, unifying AI development tools, agents, and model deployment.

        2. **Foundational Knowledge**

            - OpenAI’s Chain-of-Thought Monitorability research evaluates how reasoning transparency scales—critical reading for AI safety practitioners.

            - Next-Embedding Prediction for Vision applies NLP-style generative pretraining to visual learning, predicting embeddings rather than raw features.

        3. **Risks & Governance:**

            - Anthropic’s California SB53 compliance framework introduces a transparency reporting approach that may set industry precedents for AI regulation.

            - OpenAI’s Chain-of-Thought Monitorability research highlights implications for safety and governance as reasoning transparency scales.
            
        </RESPONSE>

        Return the summary and bullets in the following XML tags:
        <RESPONSE></RESPONSE>
        
        """

        user_prompt = "Please create a concise overview of the following source summaries:\n\n"
        lines = []
        for src in source_summaries:
            name = src.get("name", "source")
            summary = src.get("summary", "")
            lines.append(f"{name}: {summary}")
        user_prompt = "\n\n".join(lines)
        overview = self._invoke_llm(system_prompt, user_prompt)
        return overview

    def _source_url(self, name: str, instance) -> str:
        """Derive a homepage URL for the given tool instance."""
        if hasattr(instance, "config") and isinstance(getattr(instance, "config", None), dict):
            base_url = instance.config.get("base_url") or instance.config.get("url")
            if base_url:
                return base_url
        if name == "arxiv":
            return "https://arxiv.org"
        if name == "web_search":
            return "https://www.google.com"
        return ""

    def _source_description(self, name: str, instance) -> str:
        """Return a human-friendly description for a source if available."""
        if hasattr(instance, "config") and isinstance(getattr(instance, "config", None), dict):
            return instance.config.get("description", "")
        return ""

    def pulse_search(self, output_format: str = "markdown", return_data: bool = False) -> str | Tuple[str, Dict[str, Any]]:
        """Aggregate latest from all tools."""
        days_back = self.config.get('days_back', 1)
        sections_md = []
        sources = []

        tool_items = list(self.tool_instances.items())

        def _process_source(name: str, instance) -> Dict[str, Any]:
            res = instance.get_recent(days_back=days_back)
            formatted_res = instance.format_output(res)
            summary = self._generate_source_summary(formatted_res)
            return {
                "name": name,
                "description": self._source_description(name, instance),
                "summary": summary,
                "items": res,
                "formatted_res": formatted_res,
                "banner_url": self.banner_map.get(name),
                "source_url": self._source_url(name, instance),
            }

        results_by_name = {}
        parallelism = self.config.get("parallelism", {})
        max_workers = parallelism.get("max_workers", 8)
        with ThreadPoolExecutor(max_workers=min(max_workers, len(tool_items) or 1)) as executor:
            future_map = {
                executor.submit(_process_source, name, instance): name
                for name, instance in tool_items
            }
            for future in as_completed(future_map):
                name = future_map[future]
                results_by_name[name] = future.result()

        for name, _ in tool_items:
            result = results_by_name[name]
            sections_md.append(f"## {name}\n{result['summary']}\n\n{result['formatted_res']}")
            sources.append({
                "name": result["name"],
                "description": result["description"],
                "summary": result["summary"],
                "items": result["items"],
                "banner_url": result["banner_url"],
                "source_url": result["source_url"],
            })

        combined_results = "\n\n".join(sections_md)
        overall_summary = self._generate_overview_summary(sources)
        combined_markdown = f"# Pulse Summary\n{overall_summary}\n\n{combined_results}"

        report_data = {
            "generated_at": datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(),
            "overall_summary": overall_summary,
            "sources": sources,
            "sections_markdown": sections_md,
            "combined_markdown": combined_markdown,
            "days_back": days_back,
        }

        if output_format == "html":
            html_content = self.html_formatter.format_pulse(overall_summary, sources)
            if return_data:
                return html_content, report_data
            return html_content

        if return_data:
            return combined_markdown, report_data
        return combined_markdown
        

    def targeted_search(self, query: str, tools: List[str] = None) -> str:
        """Search with specific query and optional tool list."""
        if tools:
            selected_tools = [self.tool_instances[t] for t in tools if t in self.tool_instances]
        else:
            selected_tools = list(self.tool_instances.values())

        results = []
        for instance in selected_tools:
            res = instance.search(query)
            results.append(instance.format_output(res))

        return "\n\n".join(results)

# For MCP, we'll add later
