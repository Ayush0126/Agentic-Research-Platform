import logging
import time
from backend.llm.factory import get_llm_provider
from backend.agents.router_agent import RouterAgent
from backend.agents.research_agent import ResearchAgent
from backend.agents.extraction_agent import ExtractionAgent
from backend.agents.factcheck_agent import FactCheckAgent
from backend.agents.synthesis_agent import SynthesisAgent
from backend.models.schemas import ResearchReport

logger = logging.getLogger(__name__)


class ResearchPipeline:
    """
    Orchestrates the full research agent pipeline:
    Router → Research → Extraction → Fact-Check → Synthesis

    Tracks execution time per agent and handles errors gracefully.
    """

    def __init__(self):
        self.llm = get_llm_provider()
        self.router = RouterAgent(self.llm)
        self.researcher = ResearchAgent(self.llm)
        self.extractor = ExtractionAgent(self.llm)
        self.fact_checker = FactCheckAgent(self.llm)
        self.synthesizer = SynthesisAgent(self.llm)

    def run(self, query: str) -> ResearchReport:
        """
        Execute the full research pipeline.

        Args:
            query: The user's research question.

        Returns:
            A fully populated ResearchReport.
        """
        total_start = time.time()
        agent_trace = []

        # ── Step 1: Router Agent ─────────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 1/5: Router Agent — Creating research plan")
        logger.info("=" * 60)

        router_result = self.router.execute(query)
        agent_trace.append({
            "agent": router_result["agent_name"],
            "duration_seconds": router_result["duration"],
            "status": router_result["status"],
        })

        if router_result["status"] != "success":
            raise RuntimeError(f"Router Agent failed: {router_result['status']}")

        plan = router_result["result"]
        logger.info(f"Research plan: {len(plan.search_queries)} queries, "
                     f"{len(plan.key_aspects)} aspects")

        # ── Step 2: Research Agent ───────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 2/5: Research Agent — Searching & scraping")
        logger.info("=" * 60)

        research_result = self.researcher.execute(plan)
        agent_trace.append({
            "agent": research_result["agent_name"],
            "duration_seconds": research_result["duration"],
            "status": research_result["status"],
        })

        if research_result["status"] != "success":
            raise RuntimeError(f"Research Agent failed: {research_result['status']}")

        research_data = research_result["result"]
        scraped_content = research_data["scraped_content"]
        logger.info(f"Collected {len(scraped_content)} sources with content")

        if not scraped_content:
            raise RuntimeError("Research Agent found no sources. Try a different query.")

        # ── Step 3: Extraction Agent ─────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 3/5: Extraction Agent — Extracting findings")
        logger.info("=" * 60)

        extraction_result = self.extractor.execute(scraped_content)
        agent_trace.append({
            "agent": extraction_result["agent_name"],
            "duration_seconds": extraction_result["duration"],
            "status": extraction_result["status"],
        })

        if extraction_result["status"] != "success":
            raise RuntimeError(f"Extraction Agent failed: {extraction_result['status']}")

        findings = extraction_result["result"]
        logger.info(f"Extracted {len(findings)} findings")

        # ── Step 4: Fact-Check Agent ─────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 4/5: Fact-Check Agent — Cross-referencing claims")
        logger.info("=" * 60)

        factcheck_result = self.fact_checker.execute(findings)
        agent_trace.append({
            "agent": factcheck_result["agent_name"],
            "duration_seconds": factcheck_result["duration"],
            "status": factcheck_result["status"],
        })

        if factcheck_result["status"] != "success":
            raise RuntimeError(f"Fact-Check Agent failed: {factcheck_result['status']}")

        fact_checks = factcheck_result["result"]
        logger.info(f"Produced {len(fact_checks)} fact-check results")

        # ── Step 5: Synthesis Agent ──────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 5/5: Synthesis Agent — Generating report")
        logger.info("=" * 60)

        synthesis_input = {
            "query": query,
            "findings": findings,
            "fact_checks": fact_checks,
            "sources": scraped_content,
        }

        synthesis_result = self.synthesizer.execute(synthesis_input)
        agent_trace.append({
            "agent": synthesis_result["agent_name"],
            "duration_seconds": synthesis_result["duration"],
            "status": synthesis_result["status"],
        })

        if synthesis_result["status"] != "success":
            raise RuntimeError(f"Synthesis Agent failed: {synthesis_result['status']}")

        report: ResearchReport = synthesis_result["result"]

        # Attach the agent trace to the report
        report.agent_trace = agent_trace

        total_duration = round(time.time() - total_start, 2)
        logger.info("=" * 60)
        logger.info(f"PIPELINE COMPLETE — Total time: {total_duration}s")
        logger.info(f"Report: {report.title}")
        logger.info(f"Sources: {len(report.sources)}")
        logger.info(f"Findings: {len(report.key_findings)}")
        logger.info(f"Fact-checks: {len(report.fact_check_results)}")
        logger.info("=" * 60)

        return report
