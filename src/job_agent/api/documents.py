"""Expose HTTP endpoints for local PDF processing and matching."""

from fastapi import APIRouter, HTTPException, status

from job_agent.api.dependencies import (
    DocumentMatchingServiceDependency,
    PDFProcessingServiceDependency,
)
from job_agent.api.schemas import (
    PDFAnalysisRequest,
    PDFDocumentRecordResponse,
    PDFDocumentResponse,
    PDFMatchResponse,
    PDFProcessingResponse,
)
from job_agent.documents.pdf import PDFDocumentError
from job_agent.llm.base import LLMResponseError
from job_agent.models.pdf_document import DocumentKind
from job_agent.services.document_matching import DocumentBatchError

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/resumes", response_model=list[PDFDocumentResponse])
def list_resumes(service: DocumentMatchingServiceDependency) -> list[PDFDocumentResponse]:
    """List resume PDFs available to the matching service."""
    return [
        PDFDocumentResponse.model_validate(document, from_attributes=True)
        for document in service.list_resumes()
    ]


@router.get("/vacancies", response_model=list[PDFDocumentResponse])
def list_vacancy_documents(
    service: DocumentMatchingServiceDependency,
) -> list[PDFDocumentResponse]:
    """List vacancy PDFs available to the matching service."""
    return [
        PDFDocumentResponse.model_validate(document, from_attributes=True)
        for document in service.list_vacancies()
    ]


@router.post("/analyze", response_model=list[PDFMatchResponse])
async def analyze_documents(
    payload: PDFAnalysisRequest,
    service: DocumentMatchingServiceDependency,
) -> list[PDFMatchResponse]:
    """Compare a resume PDF with selected vacancy PDFs.

    Args:
        payload: Names of the local documents to compare.
        service: Configured document matching workflow.

    Returns:
        Matches sorted by descending final score.

    Raises:
        HTTPException: If document selection is invalid or analysis fails.
    """
    try:
        matches = await service.analyze(payload.resume_file, payload.vacancy_files)
    except (DocumentBatchError, PDFDocumentError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LLMResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Document analysis provider is temporarily unavailable",
        ) from exc
    return [
        PDFMatchResponse(
            vacancy_file=match.vacancy_file,
            final_score=match.final_score,
            **match.result.model_dump(),
        )
        for match in matches
    ]


@router.post("/process", response_model=PDFProcessingResponse)
def process_documents(service: PDFProcessingServiceDependency) -> PDFProcessingResponse:
    """Index, extract, and classify new or changed local PDFs."""
    return PDFProcessingResponse.model_validate(service.process(), from_attributes=True)


@router.get("/catalog/{kind}", response_model=list[PDFDocumentRecordResponse])
def document_catalog(
    kind: DocumentKind, service: PDFProcessingServiceDependency
) -> list[PDFDocumentRecordResponse]:
    """List catalog records for one kind of PDF document."""
    return [
        PDFDocumentRecordResponse.model_validate(record, from_attributes=True)
        for record in service.list(kind)
    ]
