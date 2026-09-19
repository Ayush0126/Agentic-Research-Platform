import json
import logging
from backend.agents.base import BaseAgent
from backend.llm.base import LLMProvider
from backend.models.schemas import SourceContent, ExtractedFinding

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are an Information Extraction Agent. Your job is to analyze source 
content and extract structured findings.

For each source provided, extract:
1. Key claims or findings made in the source
2. Evidence supporting each claim
3. Methodology used (if applicable)

You MUST respond in valid JSON format with exactly this structure:
{
    "findings": [
        {
            "claim": "A specific claim or finding from the source",
            "evidence": "The evidence or reasoning supporting this claim",
            "methodology": "The methodology used, or null if not applicable"
        }
    ]
}

Guidelines:
- Be specific and factual — extract what the source actually says
- Each finding should be a distinct, self-contained claim
- Include 2-5 findings per source
- Do NOT add your own opinions or analysis
- If the content is not useful or too short, return an empty findings array

Respond with ONLY the JSON object, no additional text."""


class ExtractionAgent(BaseAgent):
    """
    Extraction Agent: Reads raw source content and extracts structured
    findings including claims, evidence, and methodologies.
    """

    def __init__(self, llm: LLMProvider):
        super().__init__(
            llm=llm,
            name="Extraction Agent",
            role="Information Extractor",
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
        )

    def run(self, scraped_content: list[SourceContent]) -> list[ExtractedFinding]:
        """
        Extract structured findings from all scraped sources.

        Args:
            scraped_content: List of SourceContent objects with raw text.

        Returns:
            List of ExtractedFinding objects.
        """
        all_findings: list[ExtractedFinding] = []

        for source in scraped_content:
            logger.info(f"[Extraction] Processing: {source.title[:60]}...")

            prompt = (
                f"Extract key findings from this source:\n\n"
                f"Title: {source.title}\n"
                f"URL: {source.url}\n"
                f"Type: {source.source_type}\n\n"
                f"Content:\n{source.content[:3000]}"
            )

            try:
                response = self.call_llm(prompt)

                # Parse the JSON response
                json_str = response
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]

                data = json.loads(json_str.strip())
                findings = data.get("findings", [])

                for f in findings:
                    all_findings.append(
                        ExtractedFinding(
                            claim=f.get("claim", ""),
                            evidence=f.get("evidence", ""),
                            methodology=f.get("methodology"),
                            source_url=source.url,
                            source_title=source.title,
                        )
                    )

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(
                    f"[Extraction] Failed to parse findings for {source.title}: {e}"
                )
                # Fallback: create a single finding from the snippet
                all_findings.append(
                    ExtractedFinding(
                        claim=f"Information from: {source.title}",
                        evidence=source.content[:500],
                        methodology=None,
                        source_url=source.url,
                        source_title=source.title,
                    )
                )
            except Exception as e:
                logger.error(f"[Extraction] Error processing {source.title}: {e}")

        logger.info(f"[Extraction] Extracted {len(all_findings)} findings total")
        return all_findings
