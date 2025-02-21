from pydantic import BaseModel
from fastapi import UploadFile, Form


class AnalyzeResumeSchema(BaseModel):
    resume: UploadFile
    job_description: str = Form(...)
