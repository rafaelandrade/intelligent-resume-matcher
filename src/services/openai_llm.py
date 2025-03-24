import asyncio
import json
import re
from typing import List

from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI

from src.config import config
from src.helpers.logger import logger


class OpenAiLLM:
    def __init__(self, language: str):
        self.api_key = config.get("LLM_API_KEY", None)
        self.language = language
        self.client = ChatOpenAI(
            model_name="gpt-3.5-turbo", temperature=0.1, openai_api_key=self.api_key
        )

    def get_extract_keywords_text(self, text: str) -> str:
        if self.language == "pt-BR":
            return (
                f"Extraia os conceitos principais do seguinte "
                f"texto e retorne-os como uma lista em JSON:\n{text}"
            )

        return f"Extract key concepts from the following text and return them as a JSON list:\n{text}"

    async def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from resume text."""
        messages = [HumanMessage(content=self.get_extract_keywords_text(text=text))]
        response = await asyncio.to_thread(self.client, messages)
        return self._parse_response(response)

    def get_jaccard_similarity_text(self, resume: str, job_description: str):
        if self.language == "pt-BR":
            return (
                "Avalie a relevância do seguinte currículo em relação à descrição da vaga."
                "Analise o alinhamento entre a experiência do candidato e os requisitos do cargo."
                "Forneça uma pontuação de similaridade entre 0 e 1, "
                "onde 0 significa nenhuma similaridade e 1 significa significado idêntico."
                "Retorne apenas o valor da pontuação de similaridade."
                f"Currículo:\n{resume}\n\n"
                f"Descrição da Vaga:\n{job_description}"
            )

        return (
            "Evaluate the relevance of the following resume in relation to the job description. "
            "Assess the alignment between the candidate's experience and the requirements of the job. "
            "Provide a similarity score between 0 and 1, "
            "where 0 means no similarity and 1 means identical meaning. "
            "Return the similarity score value only.\n\n"
            f"Resume:\n{resume}\n\n"
            f"Job Description:\n{job_description}"
        )

    async def calculate_jaccard_similarity(
        self, resume: str, job_description: str
    ) -> float:
        messages = [
            HumanMessage(
                content=self.get_jaccard_similarity_text(
                    resume=resume, job_description=job_description
                )
            )
        ]
        response = await asyncio.to_thread(self.client, messages)
        try:
            return float(response.content.strip())
        except ValueError:
            return 0.0

    def get_contextual_similarity_text(self, resume: str, job_description: str):
        if self.language == "pt-BR":
            return (
                "Avalie a relevância do seguinte currículo em relação à descrição da vaga. "
                "Analise o alinhamento entre a experiência do candidato e os requisitos do cargo. "
                "Forneça uma pontuação de similaridade entre 0 e 1, onde 0 significa nenhuma similaridade "
                "e 1 significa significado idêntico. "
                "Além da pontuação, liste palavras-chave importantes da descrição da vaga "
                "que estão ausentes ou que precisam ser melhoradas no currículo. "
                "Retorne primeiro a pontuação de similaridade, seguida pela lista de palavras-chave "
                "para melhoria no currículo e um pequeno texto explicando se o "
                "currículo está bem alinhado com a vaga.\n\n"
                "O retorno deve seguir este formato: Pontuação: aqui a pontuação, Palavras-chave: "
                "aqui as palavras-chave e Feedback: aqui o feedback.\n\n"
                f"Currículo:\n{resume}\n\n"
                f"Descrição da Vaga:\n{job_description}"
            )

        return (
            "Evaluate the relevance of the following resume in relation to the job description. "
            "Assess the alignment between the candidate's experience and the requirements of the job. "
            "Provide a similarity score between 0 and 1, where 0 means no similarity "
            "and 1 means identical meaning. "
            "Along with the score, list important keywords from the job description "
            "that are either missing or need to be improved in the resume. "
            "Return the similarity score first, followed by the list of keywords for improvement in resume and "
            "a short text explaining if the resume aligns well with the job description.\n\n"
            "Could the return being Score: here the score, Keywords: "
            "here the keywords and Feedback: here the feedback"
            f"Resume:\n{resume}\n\n"
            f"Job Description:\n{job_description}"
        )

    async def calculate_contextual_similarity(
        self, resume: str, job_description: str
    ) -> dict:
        messages = [
            HumanMessage(
                content=self.get_contextual_similarity_text(
                    resume=resume, job_description=job_description
                )
            )
        ]
        response = self.client.invoke(messages)
        try:
            content = response.content.strip()

            score_match = re.search(r"(?:Score|Pontuação):\s*([\d.]+)", content)
            keywords_match = re.search(r"(?:Keywords|Palavras-chave):\s*(.*)", content, re.MULTILINE)
            feedback_match = re.search(
                r"(?:Feedback):\s*(.*)", content, re.MULTILINE | re.DOTALL
            )

            similarity_score = float(score_match.group(1)) if score_match else 0.0

            keywords = (
                [kw.strip() for kw in keywords_match.group(1).split(",") if kw.strip()]
                if keywords_match
                else []
            )

            feedback = feedback_match.group(1).strip() if feedback_match else ""

            return {
                "score": similarity_score,
                "keywords": keywords,
                "feedback": feedback,
            }
        except ValueError:
            return {"similarity_score": 0.0, "keywords_to_improve": [], "feedback": ""}

    def _parse_response(self, response: json) -> List[str]:
        try:
            return json.loads(response.content)
        except (json.JSONDecodeError, AttributeError):
            return []

    async def analyze_resume_job_match(self, resume: str, job_description: str) -> dict:
        """
        Analisa a correspondência entre currículo e vaga em uma única chamada à LLM.
        Retorna escore, palavras-chave faltantes e feedback estruturado.
        """
        logger.info(f"Analyzing resume job match...")
        prompt = self._get_comprehensive_analysis_prompt(resume, job_description)
        messages = [HumanMessage(content=prompt)]
        
        # Configurando um modelo mais adequado para análises complexas
        advanced_client = ChatOpenAI(
            model_name="gpt-4-turbo", # ou outro modelo adequado
            temperature=0.2,
            openai_api_key=self.api_key
        )
        
        # Usando function calling para retornar estrutura específica de dados
        functions = [
            {
                "name": "resume_analysis_result",
                "description": "Returns structured analysis of resume to job match",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "score": {
                            "type": "number",
                            "description": "Similarity score between 0 and 1"
                        },
                        "missing_keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Keywords from job description missing in resume"
                        },
                        "feedback": {
                            "type": "string",
                            "description": "Detailed feedback on resume match"
                        },
                        "suggested_improvements": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific suggestions to improve resume"
                        }
                    },
                    "required": ["score", "missing_keywords", "feedback"]
                }
            }
        ]
        
        response = await asyncio.to_thread(
            lambda: advanced_client.invoke(
                messages,
                functions=functions,
                function_call={"name": "resume_analysis_result"}
            )
        )
        
        try:
            # Extrair o resultado estruturado da resposta function calling
            function_call = response.additional_kwargs.get('function_call', {})
            if function_call and 'arguments' in function_call:
                logger.send_log(f"Function call: {function_call}")
                return json.loads(function_call['arguments'])
            
            # Fallback para o método anterior caso function_call falhe
            logger.send_log(f"Fallback to previous method...")
            return await self.calculate_contextual_similarity(resume, job_description)
        except Exception as e:
            print(f"Error in analyze_resume_job_match: {e}")
            return {
                "score": 0.0,
                "missing_keywords": [],
                "feedback": "",
                "suggested_improvements": []
            }

    def _get_comprehensive_analysis_prompt(self, resume: str, job_description: str) -> str:
        """Cria um prompt completo para análise do currículo vs vaga."""
        if self.language == "pt-BR":
            return (
                "Faça uma análise completa da compatibilidade entre o currículo e a descrição da vaga abaixo. "
                "Analise meticulosamente as habilidades, experiências e requisitos. "
                "\n\n1. Atribua uma pontuação de 0 a 1 que representa o nível de compatibilidade."
                "\n2. Identifique palavras-chave importantes da vaga que estão ausentes no currículo."
                "\n3. Forneça feedback sobre o alinhamento entre currículo e vaga."
                "\n4. Sugira melhorias específicas que poderiam aumentar a correspondência."
                "\n\nRetorne sua análise em formato JSON estruturado com campos: "
                "'score', 'missing_keywords', 'feedback', e 'suggested_improvements'."
                f"\n\nCURRÍCULO:\n{resume}\n\n"
                f"DESCRIÇÃO DA VAGA:\n{job_description}"
            )
        
        return (
            "Perform a comprehensive analysis of compatibility between the resume and job description below. "
            "Meticulously analyze skills, experiences, and requirements. "
            "\n\n1. Assign a score from 0 to 1 representing the level of compatibility."
            "\n2. Identify important keywords from the job posting that are missing in the resume."
            "\n3. Provide feedback on the alignment between resume and job posting."
            "\n4. Suggest specific improvements that could increase the match."
            "\n\nReturn your analysis in structured JSON format with fields: "
            "'score', 'missing_keywords', 'feedback', and 'suggested_improvements'."
            f"\n\nRESUME:\n{resume}\n\n"
            f"JOB DESCRIPTION:\n{job_description}"
        )
