from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import JSONResponse

from src.controllers.analyze_controller import analyze_controller
from src.utils.job_description_parser import parse_job_description
from src.helpers.logger import logger

router = APIRouter()


@router.post("/resume")
async def analyze_resume(
    resume: UploadFile, job_description: str = Form(...), language: str = Form(...)
):
    if resume.content_type != "application/pdf":
        return JSONResponse({"error": "Only PDF are accepted!"}, status_code=400)

    parsed_job_description = await parse_job_description(job_description)
    if parsed_job_description is None:
        return JSONResponse(
            {"error": "Failed to parse job description"}, status_code=400
        )

    logger.send_log(f"parsed job description {parsed_job_description}")

    return JSONResponse({"error": False, "data": await analyze_controller(
        resume=resume, job_description=parsed_job_description, language=language)})
