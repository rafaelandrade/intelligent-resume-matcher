import re

from fastapi import UploadFile

from src.services.pdf_reader_service import pdf_reader
from src.services.similarity_service import SimilarityContent
from src.helpers.logger import logger
from src.exceptions.NotResume import NotResume


async def resume_matcher_service(
    resume: UploadFile, job_description: str, language: str
):
    """
    Function responsible for checking if the PDF contains actual resume content
    in either English or Portuguese

    :param resume: PDF content file
    :param job_description: Optional job description to compare against
    :param language: Language
    :return: tuple (bool, str, str) - (is_resume, reason, detected_language)
    :raises NotResume: If the document is not a valid resume
    """
    pdf_content = pdf_reader(pdf_file=resume)
    is_resume_content(resume=pdf_content, language=language)

    similarity_score = SimilarityContent(
        resume_text=pdf_content, job_description=job_description, language=language
    )
    similarity_response = {}  # await similarity_score.compute_similarity()

    logger.send_log(f"Similarity Score {similarity_response}")

    return {
        "score": round(similarity_response["similarity_score"] * 100, 2),
        "missing_keywords": similarity_response["missing_keywords"],
        "total_missing": similarity_response["total_missing"],
        "message": similarity_response["feedback"],
        "is_position_closed": similarity_response["is_position_closed"],
    }


def is_resume_content(resume: str, language: str):
    """
    Function responsible for checking if the resume is related with resume content
    :param resume: PDF content file
    :param language
    :return:
    """

    if not resume or len(resume.strip()) < 100:
        raise NotResume(language=language)

    content_lower = resume.lower()

    if language.lower() in ['pt-br', 'pt', 'portuguese']:
        language = "Portuguese"
        resume_sections = [
            r"formação", r"formacao", r"educação", r"educacao",
            r"experiência", r"experiencia", r"experiência profissional", r"experiencia profissional",
            r"habilidades", r"competências", r"competencias", r"qualificações", r"qualificacoes",
            r"certificações", r"certificacoes", r"certificados",
            r"projetos", r"realizações", r"realizacoes", r"conquistas",
            r"objetivo", r"objetivos", r"resumo", r"perfil", r"perfil profissional",
            r"contato", r"informações pessoais", r"informacoes pessoais", r"referências", r"referencias",
            r"idiomas", r"línguas", r"linguas",
            r"currículo", r"curriculo", r"curriculum"
        ]

        education_terms = [
            r"\bdiploma\b", r"\bbacharelado\b", r"\blicenciatura\b", r"\bmestrado\b",
            r"\bdoutorado\b", r"\bpós-graduação\b", r"\bpos-graduacao\b",
            r"\buniversidade\b", r"\bfaculdade\b", r"\bescola\b",
            r"\bformado\b", r"\bgraduado\b", r"\bconcluído\b", r"\bconcluido\b"
        ]
    else:
        language = "English"
        resume_sections = [
            r"education", r"experience", r"work experience", r"employment",
            r"skills", r"technical skills", r"professional skills",
            r"certifications", r"projects", r"achievements",
            r"objective", r"summary", r"profile", r"professional profile",
            r"contact", r"personal information", r"references", r"languages",
            r"resume", r"curriculum vitae", r"cv"
        ]

        education_terms = [
            r"\bdegree\b", r"\bbachelor\b", r"\bmaster\b", r"\bphd\b",
            r"\buniversity\b", r"\bcollege\b", r"\bschool\b",
            r"\bgraduated\b", r"\bgpa\b"
        ]

    section_pattern = r'\b(' + '|'.join(resume_sections) + r')\b'
    sections_found = len(re.findall(section_pattern, content_lower))

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'(\+\d{1,3}[-\s]?)?\(?\d{2,3}\)?[-\s]?\d{3,5}[-\s]?\d{4}'

    has_email = bool(re.search(email_pattern, resume))
    has_phone = bool(re.search(phone_pattern, resume))

    if language.lower() in ['pt-br', 'pt', 'portuguese']:
        date_pattern = r'\b(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[a-z]*[\s,-]+\d{4}\b'
        date_pattern_alt = r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'
        date_pattern_full = r'\b(janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)[\s,-]+\d{4}\b'
    else:
        date_pattern = r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,-]+\d{4}\b'
        date_pattern_alt = r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'
        date_pattern_full = r'\b(january|february|march|april|may|june|july|august|september|october|november|december)[\s,-]+\d{4}\b'

    has_dates = (bool(re.search(date_pattern, content_lower)) or
                 bool(re.search(date_pattern_alt, content_lower)) or
                 bool(re.search(date_pattern_full, content_lower)))

    education_pattern = r'(' + '|'.join(education_terms) + r')'
    has_education = bool(re.search(education_pattern, content_lower))

    score = 0
    if sections_found >= 3:
        score += 3
    elif sections_found >= 1:
        score += 1

    if has_email:
        score += 2
    if has_phone:
        score += 2
    if has_dates:
        score += 2
    if has_education:
        score += 1

    logger.send_log({
        "message": "Resume validation score",
        "language": language,
        "score": score,
        "sections_found": sections_found,
        "has_email": has_email,
        "has_phone": has_phone,
        "has_dates": has_dates,
        "has_education": has_education,
    })

    is_resume = score >= 5

    if not is_resume:
        if language.lower() in ['pt-br', 'pt', 'portuguese']:
            error_message = f"O documento não possui características de um currículo."
        else:
            error_message = f"Document is not a resume."

        raise NotResume(language=language, message=error_message)

    return True
