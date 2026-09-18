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

export interface Vacancy {
  id: number;
  source: string;
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
  filtered_reason: string | null;
}

export interface VacancyAnalysis {
  vacancy_id: number;
  technical_score: number;
  seniority_score: number;
  domain_score: number;
  location_score: number;
  salary_score: number;
  final_score: number;
  recommended: boolean;
  strengths: string[];
  gaps: string[];
  missing_keywords: string[];
  explanation: string;
  analyzed_at: string;
}

export interface Application {
  id: number;
  vacancy_id: number;
  status: ApplicationStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface VacancyListItem {
  vacancy: Vacancy;
  analysis: VacancyAnalysis | null;
  application: Application | null;
}

export interface CollectionResult {
  fetched: number;
  created: number;
  duplicates: number;
  rejected: number;
  analyzed: number;
  analysis_failed: number;
}

export interface PDFDocument {
  name: string;
  size: number;
  modified_at: string;
}

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
  categories: Record<string, unknown>[];
  created_at: string;
  updated_at: string;
}

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
  explanation: string;
}

export interface PDFProcessingResult {
  seen: number;
  processed: number;
  needs_ocr: number;
  failed: number;
}
