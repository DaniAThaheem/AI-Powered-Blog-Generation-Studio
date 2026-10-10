from typing import Dict, Any, List
from app.workflows.state import WorkflowState
from app.services.tavily_service import tavily_service
from app.services.gemini_service import gemini_service
from app.core.logging import logger

def researchNode(state: WorkflowState) -> Dict[str, Any]:
    """Execute search queries with Tavily and synthesize evidence."""
    queries = state.get("queries", []) or []
    if not queries:
        return {"evidence": [], "warnings": ["No research queries generated"]}

    logger.info(f"Executing {len(queries)} research queries with Tavily...")
    try:
        raw_results = tavily_service.search(queries, max_results=5)
        if not raw_results:
            logger.info("Tavily returned no search results")
            return {"evidence": [], "warnings": ["Web search returned 0 results"]}

        evidence_items = tavily_service.synthesize_evidence(raw_results, gemini_service)
        logger.info(f"Synthesized {len(evidence_items)} deduplicated evidence sources")
        return {
            "evidence": [item.model_dump() for item in evidence_items],
            "warnings": []
        }
    except Exception as e:
        logger.error(f"Research node error: {e}")
        return {
            "evidence": [],
            "warnings": [f"Web research failed: {str(e)}"]
        }
