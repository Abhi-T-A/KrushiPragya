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

export interface SchemeFeeInfo {
  fee_type: 'FREE' | 'OFFICIAL_FEE' | 'SERVICE_FEE' | 'OFFICIAL_PLUS_SERVICE_FEE' | 'GOVERNMENT_BORNE' | 'UNKNOWN' | string;
  payment_required: boolean;
  official_fee?: number | null;
  krushipragya_service_fee?: number | null;
  total_payable?: number | null;
  total_amount?: number | null;
  currency: string;
  fee_description?: string | null;
  fee_source?: string | null;
  fee_last_verified?: string | null;
  is_verified: boolean;
  notice_kn: string;
  notice_en: string;
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
  fee_info?: SchemeFeeInfo | null;
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
  fee_info?: SchemeFeeInfo | null;
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

export interface SchemeApplication {
  id: string;
  scheme_id: string;
  scheme_title: string;
  scheme_title_kn?: string | null;
  category: string;
  farmer_id: string;
  status: string;
  payment_status: string;
  fee_info: SchemeFeeInfo;
  payment_transaction_id?: string | null;
  application_notes?: string | null;
  review_notes?: string | null;
  can_submit: boolean;
  submitted_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface SchemePaymentInitiateResponse {
  transaction_id: string;
  application_id: string;
  scheme_id: string;
  scheme_title: string;
  scheme_title_kn?: string | null;
  payment_method: string;
  provider?: string;
  gateway_order_id?: string;
  checkout_data?: {
    action_url: string;
    params: Record<string, string>;
    checkout_url?: string;
  } | null;
  payment_status: string;
  official_fee: number;
  service_fee: number;
  total_amount: number;
  currency: string;
  qr_data?: {
    upi_id: string;
    payee_name: string;
    amount: number;
    currency: string;
    transaction_note: string;
    qr_asset_path: string;
    payment_flow: string;
  } | null;
  fee_summary: {
    official_fee: number;
    krushipragya_service_fee: number;
    total_payable: number;
    label_official_kn: string;
    label_service_kn: string;
    label_total_kn: string;
    transparency_note_kn: string;
    transparency_note_en: string;
  };
  message_kn: string;
  message_en: string;
}

export interface PaymentProofSubmitResponse {
  transaction_id: string;
  application_id: string;
  payment_reference: string;
  payment_status: string;
  application_status: string;
  amount: number;
  message_kn: string;
  message_en: string;
}

export interface PaymentReceipt {
  receipt_id: string;
  app_name: string;
  scheme_name: string;
  scheme_title_kn?: string | null;
  application_id: string;
  transaction_id: string;
  farmer_id: string;
  farmer_name?: string | null;
  official_fee: number;
  krushipragya_service_fee: number;
  total_paid: number;
  currency: string;
  payment_method: string;
  payment_reference: string;
  payment_status: string;
  paid_at?: string | null;
  verified_at?: string | null;
  transparency_notice_kn: string;
  transparency_notice_en: string;
}

