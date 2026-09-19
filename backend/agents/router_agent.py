import json
import logging
from backend.agents.base import BaseAgent
from backend.llm.base import LLMProvider
from backend.models.schemas import ResearchPlan

logger = logging.getLogger(__name__)

ROUTER_SYSTEM_PROMPT = """You are a Research Planning Agent. Your job is to analyze a user's research 
question and create a structured research plan.

Given a research question, you must:
1. Break it down into exactly 2 specific, targeted search queries that will find the most relevant information.
2. Identify the key aspects/dimensions that should be investigated.

You MUST respond in valid JSON format with exactly this structure:
{
    "search_queries": ["query1", "query2", "query3"],
    "key_aspects": ["aspect1", "aspect2", "aspect3"]
}

Guidelines for search queries:
- Make them specific and targeted (not too broad)
- Include academic/technical terms where appropriate
- Mix between general web queries and academic paper queries
- Each query should explore a different angle of the topic

Guidelines for key aspects:
- What are the main dimensions of this research topic?
- What methodologies/approaches exist?
- What are the practical applications?
- What are the current limitations or challenges?

Respond with ONLY the JSON object, no additional text."""


class RouterAgent(BaseAgent):
    """
    Router Agent: Analyzes the user's research question and creates
    a structured research plan with targeted search queries.
    """

    def __init__(self, llm: LLMProvider):
        super().__init__(
            llm=llm,
            name="Router Agent",
            role="Research Planner",
            system_prompt=ROUTER_SYSTEM_PROMPT,
        )

    def run(self, query: str) -> ResearchPlan:
        """
        Create a research plan from the user's query.

        Args:
            query: The user's research question.

        Returns:
            A ResearchPlan with search queries and key aspects.
        """
        logger.info(f"[Router] Planning research for: {query}")

        response = self.call_llm(
            f"Create a research plan for the following question:\n\n{query}"
        )

        # Parse the JSON response
        try:
            # Try to extract JSON from the response (handle markdown code blocks)
            json_str = response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            plan_data = json.loads(json_str.strip())

            plan = ResearchPlan(
                original_query=query,
                search_queries=plan_data.get("search_queries", [query]),
                key_aspects=plan_data.get("key_aspects", []),
            )
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(f"[Router] Failed to parse LLM response as JSON: {e}")
            logger.warning(f"[Router] Raw response: {response}")
            # Fallback: use the original query as the search query
            plan = ResearchPlan(
                original_query=query,
                search_queries=[query, f"{query} research papers", f"{query} recent advances"],
                key_aspects=["overview", "methodologies", "applications", "challenges"],
            )

        logger.info(f"[Router] Created plan with {len(plan.search_queries)} search queries")
        return plan
