from typing import Dict, Any, List
from pathlib import Path
from app.workflows.state import WorkflowState
from app.services.gemini_service import gemini_service
from app.services.cloudinary_service import cloudinary_service
from app.config import settings
from app.core.logging import logger

def gNpImagePlace(state: WorkflowState) -> Dict[str, Any]:
    """Generate planned images, upload to Cloudinary/storage, and replace placeholders."""
    plan = state.get("plan") or {}
    title = plan.get("blog_title", state.get("topic", "blog"))
    md = state.get("md_with_placeholders") or state.get("merged_md", "")
    image_specs = state.get("image_specs", []) or []
    warnings: List[str] = []

    updated_specs = []

    if image_specs and gemini_service.is_configured:
        logger.info(f"Generating and uploading {len(image_specs)} images...")
        for spec in image_specs:
            placeholder = spec.get("placeholder", "")
            filename = spec.get("filename", "image.png")
            prompt = spec.get("prompt", "")
            alt = spec.get("alt", "Technical Illustration")
            caption = spec.get("caption", "")

            try:
                # 1. Generate image bytes
                image_bytes = gemini_service.generate_image_bytes(prompt)
                
                # 2. Upload to Cloudinary (or local storage fallback)
                image_url, public_id = cloudinary_service.upload_image_bytes(
                    image_bytes=image_bytes,
                    filename=filename
                )

                spec_copy = dict(spec)
                spec_copy["url"] = image_url
                spec_copy["cloudinary_public_id"] = public_id
                updated_specs.append(spec_copy)

                # 3. Replace placeholder with Markdown image link
                img_md = f"![{alt}]({image_url})\n\n*{caption}*\n\n"
                if placeholder in md:
                    md = md.replace(placeholder, img_md)
                else:
                    md += f"\n\n{img_md}"
                logger.info(f"Successfully processed image '{filename}' -> {image_url}")

            except Exception as img_err:
                msg = f"Image generation/upload failed for '{filename}': {str(img_err)}"
                logger.warning(msg)
                warnings.append(msg)
                # Graceful fallback: replace placeholder with a descriptive blockquote or clean text
                fallback_placeholder_text = f"> **[Diagram: {alt}]**\n> *{caption}*\n\n"
                if placeholder in md:
                    md = md.replace(placeholder, fallback_placeholder_text)

    # Clean up any remaining unreplaced placeholders
    for i in range(1, 10):
        ph = f"[[IMAGE_{i}]]"
        if ph in md:
            md = md.replace(ph, "")

    # Save to storage directory
    safe_title = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in title.lower())
    storage_dir = Path(settings.STORAGE_DIR) / "documents"
    storage_dir.mkdir(parents=True, exist_ok=True)
    out_file = storage_dir / f"{safe_title[:40]}.md"
    out_file.write_text(md, encoding="utf-8")

    return {
        "final": md,
        "image_specs": updated_specs,
        "output_path": str(out_file.resolve()),
        "warnings": warnings
    }
