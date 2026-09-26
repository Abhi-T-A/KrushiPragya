/**
 * Government Schemes API Service
 * Integrates directly with KrushiPragya FastAPI backend (/api/v1/schemes)
 */

import { api, API_BASE_URL } from './api';
import { SchemeDetail, SchemeItem, SchemeListResponse, UserActionResponse } from '../types/schemes';

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
