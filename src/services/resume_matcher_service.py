from fastapi import UploadFile
from src.services.similarity_service import SimilarityContent
from src.services.pdf_reader_service import pdf_reader


async def resume_matcher_service(resume: UploadFile, job_description: str):
    """

    :param resume:
    :param job_description:
    :return:
    """

    pdf_content = pdf_reader(pdf_file=resume)
    similarity_score = SimilarityContent(resume_text=pdf_content, job_description=job_description)
    similarity_response = await similarity_score.compute_similarity()

    print("Similarity Score -> ", similarity_response)

    return {"score": round(similarity_response["similarity_score"] * 100, 2),
            "missing_keywords": similarity_response["missing_keywords"],
            "total_missing": similarity_response["total_missing"],
            "message": similarity_response['feedback']}
