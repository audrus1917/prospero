"""Define request and response schemas for the HTTP API."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from job_agent.models.application import ApplicationStatus


class CollectionRequest(BaseModel):
    """Parameters for collecting a page of vacancies."""

    query: str = Field(min_length=1, max_length=200)
    page: int = Field(default=0, ge=0)
    per_page: int = Field(default=20, ge=1, le=100)
    analyze: bool = False


class CollectionResponse(BaseModel):
    """Aggregate outcome of a vacancy collection run."""

    fetched: int
    created: int
    duplicates: int
    rejected: int
    analyzed: int
    analysis_failed: int


class VacancyState(StrEnum):
    """Supported vacancy list filters."""

    ALL = "all"
    RECOMMENDED = "recommended"
    OTHER = "other"
    UNANALYZED = "unanalyzed"
    FILTERED = "filtered"


class VacancyResponse(BaseModel):
    """Normalized vacancy returned by the API."""

    id: int
    source: str
    external_id: str
    company: str
    title: str
    url: str
    description: str
    location: str | None
    remote: bool
    salary_from: Decimal | None
    salary_to: Decimal | None
    salary_currency: str | None
    published_at: datetime | None
    filtered_reason: str | None


class AnalysisResponse(BaseModel):
    """Persisted analysis returned by the API."""

    vacancy_id: int
    technical_score: int
    seniority_score: int
    domain_score: int
    location_score: int
    salary_score: int
    final_score: int
    recommended: bool
    strengths: list[str]
    gaps: list[str]
    missing_keywords: list[str]
    explanation: str
    analyzed_at: datetime


class RecommendedVacancyResponse(BaseModel):
    """Recommended vacancy paired with its analysis."""

    vacancy: VacancyResponse
    analysis: AnalysisResponse


class ApplicationCreate(BaseModel):
    """Payload for creating an application record."""

    vacancy_id: int = Field(gt=0)
    status: ApplicationStatus = ApplicationStatus.NEW
    notes: str | None = Field(default=None, max_length=10_000)


class ApplicationUpdate(BaseModel):
    """Payload for partially updating an application record."""

    status: ApplicationStatus | None = None
    notes: str | None = Field(default=None, max_length=10_000)


class ApplicationResponse(BaseModel):
    """Application tracking record returned by the API."""

    id: int
    vacancy_id: int
    status: ApplicationStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime


class VacancyListItemResponse(BaseModel):
    """Vacancy list item with optional analysis and application details."""

    vacancy: VacancyResponse
    analysis: AnalysisResponse | None
    application: ApplicationResponse | None


class PDFDocumentResponse(BaseModel):
    """Filesystem metadata for an available PDF document."""

    name: str
    size: int
    modified_at: datetime


class PDFDocumentRecordResponse(BaseModel):
    """Catalog and processing metadata for a local PDF document."""

    id: int
    kind: str
    filename: str
    content_sha256: str
    file_size: int
    processing_status: str
    processing_error: str | None
    processing_attempts: int
    parser_version: str | None
    classifier_version: str | None
    categories: list[dict[str, object]]
    created_at: datetime
    updated_at: datetime


class PDFProcessingResponse(BaseModel):
    """Aggregate outcome of a local PDF processing run."""

    seen: int
    processed: int
    needs_ocr: int
    failed: int


class PDFAnalysisRequest(BaseModel):
    """Selection of resume and vacancy PDFs to compare."""

    resume_file: str = Field(min_length=1, max_length=255)
    vacancy_files: list[str] | None = Field(default=None, max_length=20)


class PDFMatchResponse(BaseModel):
    """Scored comparison between a resume and a vacancy PDF."""

    vacancy_file: str
    final_score: int
    technical_score: int
    seniority_score: int
    domain_score: int
    strengths: list[str]
    gaps: list[str]
    missing_keywords: list[str]
    recommendations: list[str]
    explanation: str
