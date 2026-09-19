import json
import logging
from backend.agents.base import BaseAgent
from backend.llm.base import LLMProvider
from backend.models.schemas import (
    ExtractedFinding,
    FactCheckResult,
    ResearchReport,
    SourceContent,
)

logger = logging.getLogger(__name__)

SYNTHESIS_SYSTEM_PROMPT = """You are a Research Synthesis Agent. Your job is to combine research 
findings, fact-check results, and source information into a comprehensive, well-structured 
research report.

You MUST respond in valid JSON format with exactly this structure:
{
    "title": "A descriptive title for the research report",
    "summary": "A 2-3 paragraph executive summary of the key findings",
    "key_findings": [
        {
            "finding": "A key finding title",
            "details": "Detailed explanation of this finding with evidence"
        }
    ],
    "methodology_overview": "Overview of the research methodologies found across sources",
    "research_gaps": ["Gap 1 description", "Gap 2 description"],
    "sources": [
        {
            "title": "Source title",
            "url": "Source URL"
        }
    ]
}

Guidelines:
- The summary should give a reader a complete overview without reading the full report
- Organize key findings by theme/relevance (most important first)
- Include 4-8 key findings
- Reference specific sources when making claims
- Identify 2-4 research gaps or areas needing further investigation
- Be objective and balanced
- Include all unique sources that contributed to the findings

Respond with ONLY the JSON object, no additional text."""


class SynthesisAgent(BaseAgent):
    """
    Synthesis Agent: Combines findings, fact-checks, and sources into
    a structured research report with citations.
    """

    def __init__(self, llm: LLMProvider):
        super().__init__(
            llm=llm,
            name="Synthesis Agent",
            role="Report Writer",
            system_prompt=SYNTHESIS_SYSTEM_PROMPT,
        )

    def run(self, data: dict) -> ResearchReport:
        """
        Synthesize all research data into a final report.

        Args:
            data: dict with keys:
                - 'query': original research question
                - 'findings': list of ExtractedFinding
                - 'fact_checks': list of FactCheckResult
                - 'sources': list of SourceContent

        Returns:
            A ResearchReport object.
        """
        query = data["query"]
        findings: list[ExtractedFinding] = data["findings"]
        fact_checks: list[FactCheckResult] = data["fact_checks"]
        sources: list[SourceContent] = data["sources"]

        # Build the prompt with all gathered data
        findings_text = ""
        for i, f in enumerate(findings, 1):
            findings_text += (
                f"\n{i}. Claim: {f.claim}\n"
                f"   Evidence: {f.evidence}\n"
                f"   Source: {f.source_title} ({f.source_url})\n"
            )

        factcheck_text = ""
        for i, fc in enumerate(fact_checks, 1):
            factcheck_text += (
                f"\n{i}. Claim: {fc.claim}\n"
                f"   Confidence: {fc.confidence}\n"
                f"   Supporting sources: {len(fc.supporting_sources)}\n"
                f"   Contradicting sources: {len(fc.contradicting_sources)}\n"
                f"   Nuance: {fc.nuance}\n"
            )

        sources_text = ""
        unique_sources = {}
        for s in sources:
            if s.url not in unique_sources:
                unique_sources[s.url] = s.title
        for url, title in unique_sources.items():
            sources_text += f"  - {title}: {url}\n"

        prompt = (
            f"Create a comprehensive research report for the following question:\n\n"
            f"RESEARCH QUESTION: {query}\n\n"
            f"EXTRACTED FINDINGS ({len(findings)} total):\n{findings_text}\n\n"
            f"FACT-CHECK RESULTS ({len(fact_checks)} checks):\n{factcheck_text}\n\n"
            f"SOURCES USED:\n{sources_text}\n\n"
            f"Generate a well-structured research report synthesizing all of this information."
        )

        # Truncate if too long
        max_chars = 8000
        if len(prompt) > max_chars:
            prompt = prompt[:max_chars] + "\n... [input truncated for context limits]"

        try:
            response = self.call_llm(prompt)

            # Parse JSON
            json_str = response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())

            report = ResearchReport(
                title=data.get("title", f"Research Report: {query}"),
                query=query,
                summary=data.get("summary", "Summary generation failed."),
                key_findings=data.get("key_findings", []),
                methodology_overview=data.get("methodology_overview", ""),
                fact_check_results=fact_checks,
                research_gaps=data.get("research_gaps", []),
                sources=data.get("sources", [{"title": t, "url": u} for u, t in unique_sources.items()]),
            )
            return report

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"[Synthesis] Failed to parse LLM response: {e}")
            # Fallback: create a basic report
            return ResearchReport(
                title=f"Research Report: {query}",
                query=query,
                summary=f"Research was conducted on: {query}. "
                        f"{len(findings)} findings were extracted from {len(unique_sources)} sources.",
                key_findings=[
                    {"finding": f.claim, "details": f.evidence}
                    for f in findings[:8]
                ],
                methodology_overview="Automated extraction from multiple web and academic sources.",
                fact_check_results=fact_checks,
                research_gaps=["Further manual review recommended"],
                sources=[{"title": t, "url": u} for u, t in unique_sources.items()],
            )
