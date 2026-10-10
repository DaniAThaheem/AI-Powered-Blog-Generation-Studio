from typing import Dict, Any, List
from app.workflows.state import WorkflowState, Plan, Task
from app.workflows.prompts import ORCHESTRATOR_SYS_PROMPT
from app.services.gemini_service import gemini_service
from app.core.logging import logger
from langgraph.types import interrupt

def orchestratorNode(state: WorkflowState) -> Dict[str, Any]:
    """Generate structured blog plan with ordered sections."""
    topic = state.get("topic", "")
    audience = state.get("audience", "Technical Practitioners")
    tone = state.get("tone", "Informative and Engaging")
    blog_kind = state.get("blog_kind", "explainer")
    target_word_count = state.get("target_word_count", 1500)
    evidence = state.get("evidence", [])
    document_chunks = state.get("document_chunks", [])
    enable_hitl = state.get("enable_hitl", False)

    # Build prompt context
    evidence_summary = ""
    if evidence:
        evidence_summary = "\nWeb Research Evidence Available:\n" + "\n".join(
            f"- {e.get('title')} ({e.get('url')}): {e.get('snippet', '')[:150]}"
            for e in evidence[:10]
        )

    rag_summary = ""
    if document_chunks:
        rag_summary = "\nUploaded Reference Document Excerpts:\n" + "\n".join(
            f"- Doc [{c.get('filename')}]: {c.get('content', '')[:150]}"
            for c in document_chunks[:8]
        )

    user_prompt = (
        f"Blog Topic: {topic}\n"
        f"Target Audience: {audience}\n"
        f"Tone: {tone}\n"
        f"Blog Kind: {blog_kind}\n"
        f"Target Word Count: {target_word_count}\n"
        f"{evidence_summary}\n"
        f"{rag_summary}\n\n"
        "Generate a structured plan with 4-7 detailed sections matching these requirements."
    )

    try:
        if gemini_service.is_configured:
            plan: Plan = gemini_service.invoke_structured(
                schema=Plan,
                system_prompt=ORCHESTRATOR_SYS_PROMPT,
                user_prompt=user_prompt
            )
        else:
            # Fallback plan for offline / testing
            plan = Plan(
                blog_title=f"A Deep Dive into {topic}",
                audience=audience,
                tone=tone,
                blog_kind=blog_kind if blog_kind in ["explainer", "tutorial", "new_roundup", "comparison", "system_design"] else "explainer",
                constraint=["Clear explanations", "Practical insights"],
                tasks=[
                    Task(
                        id=1,
                        title=f"Introduction to {topic}",
                        goal="Introduce core concepts and motivation",
                        bullets=["Historical context", "Current challenges", "Key architectures"],
                        brief=f"Provide a strong introductory foundation for {topic}",
                        target_word=250
                    ),
                    Task(
                        id=2,
                        title="Core Architecture & Implementation",
                        goal="Examine technical mechanics and workflow",
                        bullets=["Component breakdown", "Data flow", "Implementation trade-offs"],
                        brief="Deep dive into system architecture and mechanics",
                        target_word=350,
                        requires_code=True
                    ),
                    Task(
                        id=3,
                        title="Key Takeaways and Future Directions",
                        goal="Summarize insights and next steps",
                        bullets=["Industry adoption", "Best practices", "Conclusion"],
                        brief="Wrap up with concrete recommendations",
                        target_word=200
                    )
                ]
            )

        logger.info(f"Generated blog plan '{plan.blog_title}' with {len(plan.tasks)} sections")

        # Optional Human-In-The-Loop approval
        if enable_hitl:
            logger.info("Human-in-the-loop enabled: interrupting for plan approval")
            try:
                decision = interrupt({
                    "type": "plan_approval",
                    "message": f"Review and approve blog plan: '{plan.blog_title}'",
                    "plan": plan.model_dump()
                })
                if decision and isinstance(decision, dict) and "plan" in decision:
                    # If human edited or supplied an updated plan
                    plan = Plan(**decision["plan"])
            except Exception as hitl_err:
                logger.warning(f"HITL interrupt skipped outside running graph: {hitl_err}")

        return {"plan": plan.model_dump()}

    except Exception as e:
        logger.error(f"Orchestrator node failed: {e}")
        raise
