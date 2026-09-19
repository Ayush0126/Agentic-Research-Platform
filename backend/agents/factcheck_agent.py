import json
import logging
from backend.agents.base import BaseAgent
from backend.llm.base import LLMProvider
from backend.models.schemas import ExtractedFinding, FactCheckResult

logger = logging.getLogger(__name__)

FACTCHECK_SYSTEM_PROMPT = """You are a Fact-Checking Agent. Your job is to cross-reference claims 
across multiple sources and assess their validity.

You will be given a list of claims with their sources. For each major claim, you must:
1. Identify which sources support it
2. Identify which sources contradict it
3. Note any nuance or caveats
4. Assign a confidence score (0.0 to 1.0)

Confidence scoring guide:
- 1.0: All sources agree, strong evidence
- 0.8-0.9: Most sources agree, minor variations
- 0.5-0.7: Mixed evidence, some disagreement
- 0.3-0.4: Significant contradictions
- 0.0-0.2: Mostly contradicted or unverifiable

You MUST respond in valid JSON format with exactly this structure:
{
    "fact_checks": [
        {
            "claim": "The specific claim being checked",
            "supporting_sources": ["url1", "url2"],
            "contradicting_sources": ["url3"],
            "nuance": "Additional context or caveats about this claim",
            "confidence": 0.85
        }
    ]
}

Guidelines:
- Group similar claims together rather than checking each individually
- Focus on the most important/central claims (3-7 checks)
- Be honest about confidence — don't inflate scores
- Note when sources provide different perspectives vs actual contradictions

Respond with ONLY the JSON object, no additional text."""


class FactCheckAgent(BaseAgent):
    """
    Fact-Check Agent: Cross-references claims across multiple sources,
    identifies agreements/contradictions, and assigns confidence scores.
    """

    def __init__(self, llm: LLMProvider):
        super().__init__(
            llm=llm,
            name="Fact-Check Agent",
            role="Fact Checker",
            system_prompt=FACTCHECK_SYSTEM_PROMPT,
        )

    def run(self, findings: list[ExtractedFinding]) -> list[FactCheckResult]:
        """
        Cross-reference claims across sources and produce fact-check results.

        Args:
            findings: List of ExtractedFinding objects from the Extraction Agent.

        Returns:
            List of FactCheckResult objects.
        """
        if not findings:
            logger.warning("[Fact-Check] No findings to check")
            return []

        # Prepare a summary of all findings for the LLM
        findings_text = ""
        for i, f in enumerate(findings, 1):
            findings_text += (
                f"\n--- Finding {i} ---\n"
                f"Claim: {f.claim}\n"
                f"Evidence: {f.evidence}\n"
                f"Source: {f.source_title} ({f.source_url})\n"
            )

        # If findings text is too long, truncate it
        max_chars = 6000
        if len(findings_text) > max_chars:
            findings_text = findings_text[:max_chars] + "\n... [truncated]"

        prompt = (
            f"Cross-reference and fact-check the following {len(findings)} claims "
            f"from multiple sources:\n{findings_text}"
        )

        try:
            response = self.call_llm(prompt)

            # Parse JSON
            json_str = response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())
            checks = data.get("fact_checks", [])

            results = []
            for check in checks:
                results.append(
                    FactCheckResult(
                        claim=check.get("claim", ""),
                        supporting_sources=check.get("supporting_sources", []),
                        contradicting_sources=check.get("contradicting_sources", []),
                        nuance=check.get("nuance", ""),
                        confidence=min(1.0, max(0.0, float(check.get("confidence", 0.5)))),
                    )
                )

            logger.info(f"[Fact-Check] Produced {len(results)} fact-check results")
            return results

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"[Fact-Check] Failed to parse response: {e}")
            # Fallback: return a generic result
            return [
                FactCheckResult(
                    claim="Unable to parse fact-check results from LLM",
                    supporting_sources=[],
                    contradicting_sources=[],
                    nuance="Fact-checking encountered a parsing error. Findings may still be valid.",
                    confidence=0.5,
                )
            ]
        except Exception as e:
            logger.error(f"[Fact-Check] Error: {e}")
            raise
