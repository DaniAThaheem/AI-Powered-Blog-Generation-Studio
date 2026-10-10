from typing import Dict, Any
from app.workflows.state import WorkflowState, RouterDecision
from app.workflows.prompts import ROUTER_SYS_PROMPT
from app.services.gemini_service import gemini_service
from app.core.logging import logger

def routerNode(state: WorkflowState) -> Dict[str, Any]:
    """Decide whether research is needed based on topic and preferences."""
    topic = state.get("topic", "")
    enable_research = state.get("enable_research", True)

    if not enable_research:
        logger.info(f"Research disabled by user configuration for topic: {topic}")
        return {
            "needs_research": False,
            "mode": "closed_book",
            "queries": []
        }

    try:
        if not gemini_service.is_configured:
            logger.warning("Gemini not configured. Skipping research.")
            return {
                "needs_research": False,
                "mode": "closed_book",
                "queries": []
            }

        decision: RouterDecision = gemini_service.invoke_structured(
            schema=RouterDecision,
            system_prompt=ROUTER_SYS_PROMPT,
            user_prompt=topic
        )
        logger.info(f"Router decision: needs_research={decision.needs_research}, mode={decision.mode}, queries={len(decision.queries)}")
        return {
            "needs_research": decision.needs_research,
            "mode": decision.mode,
            "queries": decision.queries
        }
    except Exception as e:
        logger.warning(f"Router LLM decision failed: {e}. Defaulting to closed_book.")
        return {
            "needs_research": False,
            "mode": "closed_book",
            "queries": []
        }

def route_next(state: WorkflowState) -> str:
    """Conditional routing: research if needed, otherwise orchestrator."""
    return "research" if state.get("needs_research") else "orchestrator"
