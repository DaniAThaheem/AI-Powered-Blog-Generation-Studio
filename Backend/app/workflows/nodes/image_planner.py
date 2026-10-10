from typing import Dict, Any
from app.workflows.state import WorkflowState, GlobalImagePlan
from app.workflows.prompts import IMAGE_DECIDER_PROMPT
from app.services.gemini_service import gemini_service
from app.core.logging import logger

def imageDeciderNode(state: WorkflowState) -> Dict[str, Any]:
    """Decide if images are needed and insert placeholders with prompts."""
    merged_md = state.get("merged_md", "")
    plan = state.get("plan") or {}
    topic = state.get("topic", "")

    if not gemini_service.is_configured:
        logger.info("Gemini not configured; skipping image planning.")
        return {
            "md_with_placeholders": merged_md,
            "image_specs": []
        }

    user_prompt = (
        f"Blog Kind: {plan.get('blog_kind', 'explainer')}\n"
        f"Topic: {topic}\n\n"
        "Analyze the following blog markdown. Insert placeholders (max 3) and propose image prompts:\n\n"
        f"{merged_md}"
    )

    try:
        image_plan: GlobalImagePlan = gemini_service.invoke_structured(
            schema=GlobalImagePlan,
            system_prompt=IMAGE_DECIDER_PROMPT,
            user_prompt=user_prompt
        )

        # Enforce max 3 images constraint
        images = image_plan.images[:3]
        specs = [img.model_dump() for img in images]
        
        logger.info(f"Image decider proposed {len(specs)} images")
        return {
            "md_with_placeholders": image_plan.md_with_placeholders or merged_md,
            "image_specs": specs
        }
    except Exception as e:
        logger.warning(f"Image planning failed: {e}. Keeping original markdown without images.")
        return {
            "md_with_placeholders": merged_md,
            "image_specs": [],
            "warnings": [f"Image planning warning: {str(e)}"]
        }
