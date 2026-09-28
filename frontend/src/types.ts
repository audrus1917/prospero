/** States supported by the application-tracking workflow. */
export type ApplicationStatus =
  | "new"
  | "shortlisted"
  | "applied"
  | "hr"
  | "technical"
  | "final"
  | "offer"
  | "rejected"
  | "withdrawn";

/** Normalized vacancy returned by the backend, independent of its source. */
export interface Vacancy {
  /** Internal database identifier used by Prospero API routes. */
  id: number;
  /** Collector identifier, for example `hh`. */
  source: string;
  /** Stable identifier assigned by the external vacancy source. */
  external_id: string;
  company: string;
  title: string;
  url: string;
  description: string;
  location: string | null;
  remote: boolean;
  salary_from: string | null;
  salary_to: string | null;
  salary_currency: string | null;
  published_at: string | null;
  /** Explanation produced by deterministic pre-LLM filtering, if rejected. */
  filtered_reason: string | null;
}

/** Structured and scored result of matching one vacancy to the profile. */
export interface VacancyAnalysis {
  vacancy_id: number;
  technical_score: number;
  seniority_score: number;
  domain_score: number;
  location_score: number;
  salary_score: number;
  /** Deterministic weighted score calculated by the backend. */
  final_score: number;
  recommended: boolean;
  strengths: string[];
  gaps: string[];
  missing_keywords: string[];
  explanation: string;
  analyzed_at: string;
}

/** User-managed tracking record for a vacancy. */
export interface Application {
  id: number;
  vacancy_id: number;
  status: ApplicationStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

/** Composite representation used by vacancy list and detail components. */
export interface VacancyListItem {
  vacancy: Vacancy;
  analysis: VacancyAnalysis | null;
  application: Application | null;
}

/** Counters returned after collecting a page of external vacancies. */
export interface CollectionResult {
  fetched: number;
  created: number;
  duplicates: number;
  rejected: number;
  analyzed: number;
  analysis_failed: number;
}

/** Basic metadata for a supported file available in a configured data directory. */
export interface PDFDocument {
  name: string;
  size: number;
  modified_at: string;
}

/** Persisted processing metadata for a local document. */
export interface PDFDocumentRecord {
  id: number;
  kind: string;
  filename: string;
  content_sha256: string;
  file_size: number;
  processing_status: string;
  processing_error: string | null;
  processing_attempts: number;
  parser_version: string | null;
  classifier_version: string | null;
  /** Classifier-specific metadata; its schema is intentionally provider-owned. */
  categories: Record<string, unknown>[];
  created_at: string;
  updated_at: string;
}

/** Result of comparing one vacancy document against the selected resume. */
export interface PDFMatch {
  vacancy_file: string;
  final_score: number;
  technical_score: number;
  seniority_score: number;
  domain_score: number;
  strengths: string[];
  gaps: string[];
  missing_keywords: string[];
  recommendations: string[];
  /** A vacancy-specific cover letter represented as 10–12 display lines. */
  cover_letter: string[];
  explanation: string;
}

/** Aggregate counters produced by the document processing endpoint. */
export interface PDFProcessingResult {
  seen: number;
  processed: number;
  needs_ocr: number;
  failed: number;
}
