/**
 * Government Schemes API Service
 * Integrates directly with KrushiPragya FastAPI backend (/api/v1/schemes)
 */

import { api, API_BASE_URL } from './api';
import {
  PaymentProofSubmitResponse,
  PaymentReceipt,
  SchemeApplication,
  SchemeDetail,
  SchemeItem,
  SchemeListResponse,
  SchemePaymentInitiateResponse,
  UserActionResponse,
} from '../types/schemes';

export { API_BASE_URL };

export interface FetchSchemesParams {
  search?: string;
  category?: string;
  state?: string;
  crop?: string;
  language?: 'kn' | 'en';
  page?: number;
  limit?: number;
}

const getAuthHeaders = (user?: { phone?: string; id?: string } | null) => {
  const headers: Record<string, string> = {};
  const phone = user?.phone || '9876543210';
  const id = user?.id || '11111111-1111-4111-8111-111111111111';

  if (phone) {
    headers['x-farmer-phone'] = phone;
  }
  if (id) {
    headers['x-farmer-id'] = id;
  }
  return headers;
};

/**
 * Fetch paginated schemes list from backend
 */
export const fetchSchemesList = async (
  params?: FetchSchemesParams,
  user?: { phone?: string; id?: string } | null
): Promise<SchemeListResponse> => {
  const queryParams = new URLSearchParams();

  // If state is not specified, pass 'all' so central & state schemes are both available
  const stateParam = params?.state !== undefined ? params.state : 'all';
  if (stateParam) {
    queryParams.append('state', stateParam);
  }

  if (params?.search && params.search.trim().length > 0) {
    queryParams.append('search', params.search.trim());
  }

  if (params?.category && params.category.trim().length > 0 && params.category !== 'all') {
    queryParams.append('category', params.category.trim());
  }

  if (params?.crop && params.crop.trim().length > 0) {
    queryParams.append('crop', params.crop.trim());
  }

  const lang = params?.language || 'kn';
  queryParams.append('language', lang);

  if (params?.page) {
    queryParams.append('page', params.page.toString());
  }

  if (params?.limit) {
    queryParams.append('limit', params.limit.toString());
  }

  const url = `/schemes?${queryParams.toString()}`;
  console.log('[SCHEMES] API base URL:', API_BASE_URL);
  console.log('[SCHEMES] requesting:', `${API_BASE_URL}${url}`);

  try {
    const response = await api.get<SchemeListResponse>(url, {
      headers: getAuthHeaders(user),
    });
    console.log('[SCHEMES] response status:', response.status);
    console.log('[SCHEMES] response data:', response.data);
    return response.data;
  } catch (err: any) {
    console.log('[SCHEMES] error:', err?.message || String(err));
    throw err;
  }
};

/**
 * Fetch complete detail for a single scheme by UUID
 */
export const fetchSchemeDetail = async (
  schemeId: string,
  language: 'kn' | 'en' = 'kn',
  user?: { phone?: string; id?: string } | null
): Promise<SchemeDetail> => {
  const response = await api.get<SchemeDetail>(`/schemes/${schemeId}?language=${language}`, {
    headers: getAuthHeaders(user),
  });
  return response.data;
};

/**
 * Bookmark / save a scheme for the farmer
 */
export const saveScheme = async (
  schemeId: string,
  user?: { phone?: string; id?: string } | null
): Promise<UserActionResponse> => {
  const response = await api.post<UserActionResponse>(
    `/schemes/${schemeId}/save`,
    {},
    {
      headers: getAuthHeaders(user),
    }
  );
  return response.data;
};

/**
 * Remove bookmark / unsave a scheme
 */
export const unsaveScheme = async (
  schemeId: string,
  user?: { phone?: string; id?: string } | null
): Promise<UserActionResponse> => {
  const response = await api.delete<UserActionResponse>(
    `/schemes/${schemeId}/save`,
    {
      headers: getAuthHeaders(user),
    }
  );
  return response.data;
};

/**
 * Mark a scheme as read to clear unread badge
 */
export const markSchemeRead = async (
  schemeId: string,
  user?: { phone?: string; id?: string } | null
): Promise<UserActionResponse> => {
  const response = await api.post<UserActionResponse>(
    `/schemes/${schemeId}/read`,
    {},
    {
      headers: getAuthHeaders(user),
    }
  );
  return response.data;
};

/**
 * Fetch all saved schemes for the farmer directly from backend
 * Backend is the source of truth!
 */
export const fetchSavedSchemes = async (
  user?: { phone?: string; id?: string } | null,
  language: 'kn' | 'en' = 'kn'
): Promise<SchemeItem[]> => {
  // Query all schemes with the farmer's credentials
  const res = await fetchSchemesList({ state: 'all', limit: 100, language }, user);
  return (res.items || []).filter((item) => item.is_saved === true);
};

/**
 * Apply for a scheme (creates draft/pending application with fee structure)
 */
export const applyForScheme = async (
  schemeId: string,
  applicationNotes?: string,
  user?: { phone?: string; id?: string } | null
): Promise<SchemeApplication> => {
  const response = await api.post<SchemeApplication>(
    `/schemes/${schemeId}/apply`,
    { application_notes: applicationNotes || undefined },
    { headers: getAuthHeaders(user) }
  );
  return response.data;
};

/**
 * Initiate PhonePe Static QR payment for a scheme application
 */
export const initiateSchemePayment = async (
  applicationId: string,
  user?: { phone?: string; id?: string } | null
): Promise<SchemePaymentInitiateResponse> => {
  const response = await api.post<SchemePaymentInitiateResponse>(
    `/schemes/applications/${applicationId}/payment`,
    {},
    { headers: getAuthHeaders(user) }
  );
  return response.data;
};

/**
 * Submit UTR bank reference proof after paying via PhonePe QR
 */
export const submitSchemePaymentProof = async (
  applicationId: string,
  utr: string,
  amountPaid: number,
  notes?: string,
  user?: { phone?: string; id?: string } | null
): Promise<PaymentProofSubmitResponse> => {
  const response = await api.post<PaymentProofSubmitResponse>(
    `/schemes/applications/${applicationId}/payment/submit-proof`,
    {
      utr: utr.trim(),
      amount_paid: amountPaid,
      notes: notes || undefined,
    },
    { headers: getAuthHeaders(user) }
  );
  return response.data;
};

/**
 * Fetch scheme payment details, status, and receipt
 */
export const fetchSchemePaymentDetails = async (
  applicationId: string,
  user?: { phone?: string; id?: string } | null
): Promise<{
  application_id: string;
  scheme_id: string;
  scheme_title?: string;
  scheme_title_kn?: string;
  application_status: string;
  payment_status: string;
  transaction_id?: string;
  total_amount?: number;
  official_fee?: number;
  service_fee?: number;
  payment_reference?: string;
  payment_method: string;
  receipt?: PaymentReceipt;
  fee_info?: any;
}> => {
  const response = await api.get(
    `/schemes/applications/${applicationId}/payment`,
    { headers: getAuthHeaders(user) }
  );
  return response.data;
};

/**
 * Submit scheme application after verified payment (or immediately if free)
 */
export const submitSchemeApplication = async (
  applicationId: string,
  user?: { phone?: string; id?: string } | null
): Promise<SchemeApplication> => {
  const response = await api.post<SchemeApplication>(
    `/schemes/applications/${applicationId}/submit`,
    {},
    { headers: getAuthHeaders(user) }
  );
  return response.data;
};

/**
 * Fetch all applications submitted or tracked by the farmer
 */
export const fetchMyApplications = async (
  user?: { phone?: string; id?: string } | null
): Promise<SchemeApplication[]> => {
  const response = await api.get<SchemeApplication[]>(
    '/schemes/my-applications',
    { headers: getAuthHeaders(user) }
  );
  return response.data;
};

/**
 * Fetch scheme payment status by application ID (polled after PayU checkout)
 */
export const fetchSchemePaymentStatus = async (
  applicationId: string,
  user?: { phone?: string; id?: string } | null
): Promise<{
  application_id: string;
  scheme_id: string;
  application_status: string;
  payment_status: string;
  transaction_id?: string;
  total_amount?: number;
  provider?: string;
}> => {
  const response = await api.get(
    `/schemes/applications/${applicationId}/payment/status`,
    { headers: getAuthHeaders(user) }
  );
  return response.data;
};

