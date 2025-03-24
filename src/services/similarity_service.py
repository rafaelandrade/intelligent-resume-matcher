from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List

from src.services.openai_llm import OpenAiLLM
from src.utils.job_description_parser import ParseResult


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

    async def compute_similarity(self) -> Dict[str, float | List[str]]:
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
