import hashlib
import json

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Union

from src.services.openai_llm import OpenAiLLM
from src.utils.job_description_parser import ParseResult
from src.database.redis_client import get_redis_client, set_with_expiry, get_value, RATE_LIMIT_EXPIRATION

redis_client = get_redis_client()


@dataclass
class MissingKeywordsInfo:
    missing_terms: List[str]
    importance_weight: float


class SimilarityContent:
    def __init__(self, resume_text: str, job_description: str, language: str):
        if not resume_text or not job_description:
            raise ValueError("Resume text and job description cannot be empty.")
        self.resume_text = resume_text
        self.job_description = job_description
        self.language = language
        self.open_ai = OpenAiLLM(language=self.language)
        self.cache_key = self._generate_cache_key(resume_text, job_description)

    @lru_cache(maxsize=1000)
    async def jaccard_similarity(self) -> float:
        return await self.open_ai.calculate_jaccard_similarity(
            self.resume_text, self.job_description
        )

    @lru_cache(maxsize=1000)
    async def contextual_similarity(self) -> dict:
        return await self.open_ai.calculate_contextual_similarity(
            self.resume_text, self.job_description
        )

    def _generate_cache_key(self, resume_text: str, job_description: str) -> str:
        """Generate a similarity key"""
        combined = f"{resume_text}:{job_description}"
        return f"similarity_result:{hashlib.sha256(combined.encode()).hexdigest()}"

    async def compute_similarity(self) -> Dict[str, Union[float, List[str]]]:
        cached_result = get_value(self.cache_key)
        if cached_result:
            return json.loads(cached_result)

        jaccard_score = await self.jaccard_similarity()
        contextual_analysis = await self.contextual_similarity()
        combined_score = (jaccard_score + contextual_analysis.get("score", 0.0)) / 2

        return {
            "similarity_score": round(combined_score, 2),
            "missing_keywords": contextual_analysis.get("keywords", []),
            "total_missing": len(contextual_analysis.get("keywords", [])),
            "feedback": contextual_analysis.get("feedback"),
            "is_position_closed": self.job_description.is_position_closed
            if isinstance(self.job_description, ParseResult)
               and hasattr(self.job_description, "is_position_closed")
            else False,
        }
