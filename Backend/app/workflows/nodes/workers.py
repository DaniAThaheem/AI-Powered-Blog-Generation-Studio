from typing import List, Dict, Any
from langgraph.types import Send
from app.workflows.state import WorkflowState, Task, Plan
from app.workflows.prompts import WORKER_SYS_PROMPT
from app.services.gemini_service import gemini_service
from app.core.logging import logger

def fanOut(state: WorkflowState) -> List[Send]:
    """Fan out section tasks to parallel worker nodes."""
    plan_dict = state.get("plan")
    if not plan_dict or "tasks" not in plan_dict:
        logger.warning("No tasks found in plan to fan out")
        return []

    tasks = plan_dict["tasks"]
    logger.info(f"Fanning out {len(tasks)} parallel section workers...")
    
    return [
        Send(
            "worker",
            {
                "task": task,
                "plan": plan_dict,
                "topic": state.get("topic", ""),
                "mode": state.get("mode", "closed_book"),
                "evidence": state.get("evidence", []),
                "document_chunks": state.get("document_chunks", [])
            }
        )
        for task in tasks
    ]

def workerNode(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a single blog section in Markdown format."""
    task = payload["task"]
    plan = payload["plan"]
    topic = payload["topic"]
    mode = payload.get("mode", "closed_book")
    evidence = payload.get("evidence", [])
    document_chunks = payload.get("document_chunks", [])

    task_id = task.get("id", 1)
    task_title = task.get("title", f"Section {task_id}")
    bullets = task.get("bullets", [])
    bullets_text = "\n".join(f"- {b}" for b in bullets)

    # Contextual evidence
    evidence_text = ""
    if evidence:
        evidence_text = "\nWeb Sources (use only these URLs when citing):\n" + "\n".join(
            f"- {e.get('title')} | {e.get('url')} | {e.get('snippet', '')[:100]}"
            for e in evidence[:10]
        )

    doc_text = ""
    if document_chunks:
        doc_text = "\nReference Document Excerpts:\n" + "\n".join(
            f"- [{c.get('filename')} (p.{c.get('page_number', '1')})]: {c.get('content', '')[:150]}"
            for c in document_chunks[:5]
        )

    user_prompt = (
        f"Blog Title: {plan.get('blog_title', topic)}\n"
        f"Audience: {plan.get('audience', 'Technical')}\n"
        f"Tone: {plan.get('tone', 'Engaging')}\n"
        f"Section Title: {task_title}\n"
        f"Section Goal: {task.get('goal', '')}\n"
        f"Target Words: {task.get('target_word', 300)}\n"
        f"Key Bullet Points:\n{bullets_text}\n"
        f"Requires Code: {task.get('requires_code', False)}\n"
        f"Requires Citations: {task.get('requires_citation', False)}\n"
        f"{evidence_text}\n"
        f"{doc_text}\n\n"
        f"Write this section now in clean Markdown. Start with '## {task_title}'."
    )

    try:
        if gemini_service.is_configured:
            content_md = gemini_service.invoke_text(
                system_prompt=WORKER_SYS_PROMPT,
                user_prompt=user_prompt
            )
            # Ensure it starts with heading if missing
            content_clean = content_md.strip()
            if not content_clean.startswith("#"):
                content_clean = f"## {task_title}\n\n{content_clean}"
        else:
            # Fallback mock section for offline / test mode
            bullets_content = "\n\n".join(f"### {b}\n\nDetailed exploration of {b.lower()} in modern systems." for b in bullets)
            code_snippet = "\n\n```python\n# Example implementation\ndef run_pipeline():\n    print('Initialized successfully')\n```" if task.get("requires_code") else ""
            content_clean = f"## {task_title}\n\n{task.get('brief', '')}\n\n{bullets_content}{code_snippet}"

        return {
            "sections": [
                {
                    "id": task_id,
                    "title": task_title,
                    "content": content_clean
                }
            ],
            "warnings": []
        }
    except Exception as e:
        logger.error(f"Worker node for section {task_id} failed: {e}")
        fallback_content = f"## {task_title}\n\n*Note: Section generation encountered an issue and was recovered.*"
        return {
            "sections": [
                {
                    "id": task_id,
                    "title": task_title,
                    "content": fallback_content
                }
            ],
            "warnings": [f"Section {task_id} ({task_title}) generation warning: {str(e)}"]
        }
