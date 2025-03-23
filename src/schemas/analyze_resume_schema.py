from fastapi import Form, UploadFile
from pydantic import BaseModel


class AnalyzeResumeSchema(BaseModel):
    resume: UploadFile
    job_description: str = Form(...)
