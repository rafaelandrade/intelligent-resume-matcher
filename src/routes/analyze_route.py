from fastapi import APIRouter, UploadFile, Form
from fastapi.responses import JSONResponse

from src.schemas.analyze_resume_schema import AnalyzeResumeSchema
from src.controllers.analyze_controller import analyze_controller

router = APIRouter()


@router.post('/resume')
async def analyze_resume(resume: UploadFile,
    job_description: str = Form(...)):
    try:
        if resume.content_type != "application/pdf":
            return JSONResponse({"error": "Only PDF are accepted!"}, status_code=400)

        return await analyze_controller(resume=resume,
                                        job_description=job_description)
    except Exception as exception:
        return JSONResponse({"error": str(exception)}, status_code=500)