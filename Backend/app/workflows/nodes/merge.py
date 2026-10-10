from typing import Dict, Any, List
from app.workflows.state import WorkflowState
from app.core.logging import logger

def mergeNode(state: WorkflowState) -> Dict[str, Any]:
    """Merge parallel worker outputs into ordered single Markdown document."""
    plan = state.get("plan") or {}
    title = plan.get("blog_title", state.get("topic", "Generated Technical Blog"))
    raw_sections: List[Dict[str, Any]] = state.get("sections", []) or []

    logger.info(f"Merging {len(raw_sections)} section results for blog '{title}'...")

    # Deduplicate by section ID (in case of re-tries) and sort by section ID
    seen_ids = set()
    unique_sections = []
    for s in raw_sections:
        sid = s.get("id")
        if sid not in seen_ids:
            seen_ids.add(sid)
            unique_sections.append(s)

    sorted_sections = sorted(unique_sections, key=lambda s: s.get("id", 0))

    if not sorted_sections:
        logger.warning("No sections available to merge")
        blog_content = f"# {title}\n\n*No sections were generated.*"
    else:
        body_sections = []
        for s in sorted_sections:
            content = s.get("content", "").strip()
            if content:
                body_sections.append(content)
        body = "\n\n".join(body_sections)
        blog_content = f"# {title}\n\n{body}"

    return {
        "merged_md": blog_content
    }
