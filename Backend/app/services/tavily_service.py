from typing import List, Dict, Any, Optional
import os
from app.config import settings
from app.core.logging import logger
from app.workflows.state import EvidenceItem, EvidencePack
from app.workflows.prompts import RESEARCH_SYS_PROMPT

class TavilyService:
    def __init__(self):
        self.api_key = settings.TAVILY_API_KEY or os.environ.get("TAVILY_API_KEY")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def search(self, queries: List[str], max_results: int = 5) -> List[Dict[str, Any]]:
        if not self.is_configured:
            logger.warning("TAVILY_API_KEY is not configured. Web research skipped.")
            return []

        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.api_key)
            raw_results = []
            for query in queries:
                try:
                    response = client.search(
                        query=query,
                        search_depth="advanced",
                        max_results=max_results,
                        include_raw_content=False
                    )
                    results = response.get("results", [])
                    raw_results.extend(results)
                except Exception as query_err:
                    logger.warning(f"Tavily search query '{query}' failed: {query_err}")
            return raw_results
        except ImportError:
            logger.warning("tavily python package not installed")
            return []
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return []

    def synthesize_evidence(self, raw_results: List[Dict[str, Any]], gemini_svc) -> List[EvidenceItem]:
        """Synthesize raw search results into deduplicated EvidenceItem list."""
        if not raw_results:
            return []

        try:
            prompt_input = f"Raw Search Results:\n{raw_results}"
            pack: EvidencePack = gemini_svc.invoke_structured(
                schema=EvidencePack,
                system_prompt=RESEARCH_SYS_PROMPT,
                user_prompt=prompt_input
            )
            # Deduplicate by URL
            unique_evidence: Dict[str, EvidenceItem] = {}
            for item in pack.evidence:
                if item.url and item.url.strip():
                    unique_evidence[item.url.strip()] = item
            return list(unique_evidence.values())
        except Exception as e:
            logger.warning(f"LLM evidence synthesis failed ({e}). Falling back to manual normalization.")
            # Manual fallback
            unique_evidence = {}
            for r in raw_results:
                url = r.get("url")
                if url and url not in unique_evidence:
                    unique_evidence[url] = EvidenceItem(
                        title=r.get("title", "Untitled Source"),
                        url=url,
                        published_at=r.get("published_date"),
                        snippet=r.get("content", "")[:300],
                        source="tavily"
                    )
            return list(unique_evidence.values())

tavily_service = TavilyService()
