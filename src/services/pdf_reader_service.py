from fastapi import UploadFile
from PyPDF2 import PdfReader


def pdf_reader(pdf_file: UploadFile) -> str:
    """
    Service responsible for get the content of PDF file.
    :param pdf_file: PDF file
    :return: Responsible for return the content of PDF in string format.
    """

    content = PdfReader(pdf_file.file)
    resume_text = " ".join(page.extract_text() for page in content.pages)
    return resume_text



