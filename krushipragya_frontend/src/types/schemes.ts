/**
 * Government Schemes TypeScript Type Definitions
 * Matching KrushiPragya Backend API Contracts (/api/v1/schemes)
 */

export interface SchemeSourceInfo {
  name: string;
  url?: string | null;
  last_verified_at?: string | null;
  source_type?: string | null;
  crawler_status?: string | null;
}

export interface RelatedSchemeItem {
  id: string;
  name: string;
  category: string;
  department?: string | null;
}

export interface SchemeItem {
  id: string;
  name: string;
  title_en: string;
  title_kn?: string | null;
  description: string;
  department: string;
  state: string;
  category: string;
  benefits_summary: string;
  application_url?: string | null;
  is_read: boolean;
  is_saved: boolean;
  source: SchemeSourceInfo;
  created_at?: string | null;
  updated_at?: string | null;
  image_url?: string | null;
}

export interface SchemeDetail extends SchemeItem {
  status: string;
  eligibility: string[];
  benefits: string[];
  application_process: string[];
  documents_required: string[];
  related_schemes?: RelatedSchemeItem[];
}

export interface SchemeListResponse {
  items: SchemeItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface UserActionResponse {
  success: boolean;
  message: string;
}

export type SchemeCategoryFilter = 'all' | 'state' | 'agriculture' | 'crop' | 'subsidy' | 'insurance';
