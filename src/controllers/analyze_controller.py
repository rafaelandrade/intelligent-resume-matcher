from fastapi import UploadFile

from src.services.resume_matcher_service import resume_matcher_service

async def analyze_controller(resume: UploadFile, job_description: str, language: str):
    """

    :param resume:
    :param job_description:
    :return:
    """
    return await resume_matcher_service(
        resume=resume, job_description=job_description, language=language
    )
