import openai
from backend_shared.schemas.analysis_schema import AnalysisPrompts, AnalysisResponse
from backend_shared.schemas.ingestion_schema import ContentRequest
from fastapi import APIRouter, HTTPException

from analytics.config import settings
from analytics.service.analysis_service import AnalysisService

analysis_router = APIRouter(prefix="/analyse", tags=["Analyse"])


@analysis_router.post("")
async def analyse(article: ContentRequest) -> AnalysisResponse:
    service = AnalysisService(model=f"{settings.AZURE_RESOURCE_PREFIX}-gpt-4o")
    try:
        results = await service.analyse_all(article)
        return results
    except openai.BadRequestError as e:
        if "content_filter_result" in str(e) and "ResponsibleAIPolicyViolation" in str(
            e
        ):
            return {"error": "[LLM API filtered]"}
        else:
            raise HTTPException(status_code=500, detail=str(e))


@analysis_router.post("/prompts")
async def get_prompts(article: ContentRequest) -> AnalysisPrompts:
    service = AnalysisService(model=f"{settings.AZURE_RESOURCE_PREFIX}-gpt-4o")
    try:
        return service.get_prompts(article)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
