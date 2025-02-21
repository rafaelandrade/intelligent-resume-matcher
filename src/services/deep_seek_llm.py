from typing import List
import requests


class DeepSeekLLM:
    def __init__(self):
        self.base_url = 'https://api.deepseek.com/v1'
        self.api_key = 'sk-1f3db9c4f756483aa37d560bd2f99ab4'
        self.headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}",}
        self.model = "deepseek-chat"

    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords of resume text"""
        payload = {
            "model": self.model,
            "prompt": f"Extract the most important keywords from the following text:\n\n{text}",
            "max_tokens": 100,
            "temperature": 0.3,
        }

        response = requests.post(url=f"{self.base_url}/completions", headers=self.headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Failed to extract keywords: {response.text}")

        try:
            keywords = response.json()["choices"][0]["text"].strip().split(", ")
            return keywords
        except (KeyError, IndexError) as e:
            raise Exception(f"Invalid API response format: {e}")

    def get_synonyms(self, word: str):
        """GET SYNONYMS OF SPECIFIC WORD"""
        payload = {
            "model": self.model,
            "prompt": f"Generate a list of synonyms or related terms for the word: {word}",
            "max_tokens": 50,
            "temperature": 0.5,
        }

        response = requests.post(url=f"{self.base_url}/completions", headers=self.headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Failed to get SYNONYMS: {response.text}")

        try:
            synonyms = response.json()["choices"][0]["text"].strip().split(", ")
            return synonyms
        except (KeyError, IndexError) as e:
            raise Exception(f"Invalid API response format: {e}")

    def calculate_contextual_similarity(self, resume_text: str, job_description: str) -> float:
        """Calculate contextual similarity"""

        payload = {
            "model": self.model,
            "prompt": f"Rate the similarity between the following resume "
                      f"and job description on a scale of 0 to 1:\n\nResume:\n{resume_text}\n\nJob Description:\n{job_description}",
            "max_tokens": 10,
            "temperature": 0.2,
        }

        response = requests.post(url=f"{self.base_url}/completions", headers=self.headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Failed to calculate similarity: {response.text}")

        try:
            similarity_score = float(response.json()["choices"][0]["text"].strip())
            return similarity_score
        except (KeyError, IndexError) as e:
            raise Exception(f"Invalid API response format: {e}")

    def rank_keywords_with_context(self, missing_keywords: List[str], job_description: str) -> List[str]:
        """RANK KEYWORDS WITH CONTEXT"""
        payload = {
            "model": self.model,
            "prompt": f"Rank the following keywords based on their "
                      f"importance in the job description:\n\nKeywords:\n{', '.join(missing_keywords)}\n\nJob Description:\n{job_description}",
            "max_tokens": 100,
            "temperature": 0.3,
        }
        response = requests.post(url=f"{self.base_url}/completions", headers=self.headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Failed to rank keywords: {response.text}")

        try:
            ranked_keywords = response.json()["choices"][0]["text"].strip().split(", ")
            return ranked_keywords
        except (KeyError, IndexError) as e:
            raise Exception(f"Invalid API response format: {e}")
