from fastapi import UploadFile

from src.services.resume_matcher_service import resume_matcher_service


async def analyze_controller(resume: UploadFile, job_description: str):
    """

    :param resume:
    :param job_description:
    :return:
    """
    try:
        return await resume_matcher_service(resume=resume, job_description=job_description)
    except Exception as exception:
        return f"Some error exception here {exception}"
