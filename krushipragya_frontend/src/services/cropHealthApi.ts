import axios from 'axios';
import { Platform } from 'react-native';
import { API_BASE_URL } from './api';

export { API_BASE_URL };

export const cropHealthClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30s timeout for image uploads and deep learning inference
});

// ==============================================================================
// Types matching backend models & schemas
// ==============================================================================

export interface DiseaseInfo {
  disease_name_en: string;
  disease_name_kn: string;
  scientific_name?: string;
  category: string;
  symptoms: string;
  cultural_control: string;
  remedy_en: string;
  remedy_kn: string;
  source_institution: string;
}

export interface ClassPrediction {
  class_name: string;
  confidence: number;
}

export interface DiseasePredictionResult {
  crop: string;
  status: 'success' | 'uncertain' | 'rejected';
  predicted_class?: string | null;
  confidence: number;
  low_confidence: boolean;
  input_verified: boolean;
  reason_code?: string | null;
  message?: string | null;
  model_version?: string | null;
  disease_info?: DiseaseInfo | null;
  predictions?: ClassPrediction[];
  metrics?: Record<string, any>;
}

export interface BackendCropCatalogItem {
  id: string;
  code: string;
  name_en: string;
  name_kn: string;
  scientific_name?: string;
  category?: string;
  is_active: boolean;
}

export interface BackendFarmerCropItem {
  id: string;
  farmer_id: string;
  crop_id: string;
  area_acres?: number | null;
  is_primary: boolean;
  crop: BackendCropCatalogItem;
}

export interface BackendDiagnosisRecord {
  id: string;
  crop_report_id: string;
  crop: string;
  predicted_class: string;
  confidence: number;
  model_name: string;
  created_at: string;
}

export interface BackendCropReportItem {
  id: string;
  farmer_crop_id: string;
  notes?: string | null;
  image_filename?: string | null;
  image_storage_path?: string | null;
  status: 'UNVERIFIED' | 'AI_ANALYSED' | 'CORROBORATED' | 'EXPERT_VERIFIED';
  created_at: string;
  updated_at: string;
  farmer_crop?: BackendFarmerCropItem;
  diagnoses?: BackendDiagnosisRecord[];
}

export interface CorroborationSummary {
  total_count: number;
  agreed_count: number;
  disagreed_count: number;
  min_required: number;
  threshold_satisfied: boolean;
  is_corroborated: boolean;
}

export interface ExpertVerificationData {
  id: string;
  crop_report_id: string;
  expert_id?: string | null;
  status: string;
  action_type?: string | null;
  finding?: string | null;
  expert_notes?: string | null;
  recommended_action?: string | null;
  requested_at: string;
  assigned_at?: string | null;
  completed_at?: string | null;
}

export interface VerificationStatusData {
  crop_report_id: string;
  verification_status: 'UNVERIFIED' | 'AI_ANALYSED' | 'CORROBORATED' | 'EXPERT_VERIFIED';
  status_rank: number;
  is_ai_analysed: boolean;
  is_corroborated: boolean;
  is_expert_verified: boolean;
  latest_diagnosis?: {
    crop: string;
    predicted_class: string;
    confidence: number;
    model_name: string;
    created_at: string;
  } | null;
  corroboration_summary?: CorroborationSummary | null;
  expert_verification?: ExpertVerificationData | null;
  status_history?: Array<{
    status: string;
    rank: number;
    timestamp: string;
    actor_role: string;
    description: string;
  }>;
}

export interface FarmerProfileData {
  id: string;
  full_name: string;
  phone: string;
  village_id?: string;
  language: string;
  land_holding_acres?: number;
}

// Build standard auth headers for phone-first identity flow
export const buildFarmerHeaders = (phone?: string, farmerId?: string) => {
  const headers: Record<string, string> = {};
  if (phone) {
    const cleanPhone = phone.replace('+91', '').replace(/\s/g, '').replace(/-/g, '').trim();
    headers['X-Farmer-Phone'] = cleanPhone;
  }
  if (farmerId) {
    headers['X-Farmer-Id'] = farmerId;
  }
  return headers;
};

// ==============================================================================
// 1. Farmer Profile & Crops APIs
// ==============================================================================

export const fetchFarmerProfileByPhone = async (phone: string): Promise<FarmerProfileData | null> => {
  try {
    const cleanPhone = phone.replace('+91', '').replace(/\s/g, '').replace(/-/g, '').trim();
    const res = await cropHealthClient.get<FarmerProfileData>(`/farmers/by-phone/${cleanPhone}`);
    return res.data;
  } catch (err) {
    return null;
  }
};

export const fetchFarmerRegisteredCrops = async (
  farmerId: string,
  phone?: string
): Promise<BackendFarmerCropItem[]> => {
  try {
    const res = await cropHealthClient.get<BackendFarmerCropItem[]>(`/farmers/${farmerId}/crops`, {
      headers: buildFarmerHeaders(phone, farmerId),
    });
    return res.data;
  } catch (err) {
    return [];
  }
};

export const fetchSupportedCropCatalog = async (): Promise<BackendCropCatalogItem[]> => {
  try {
    const res = await cropHealthClient.get<BackendCropCatalogItem[]>('/crops');
    return res.data;
  } catch (err) {
    return [];
  }
};

// ==============================================================================
// 2. Real Disease Prediction & Input Verification Inference
// ==============================================================================

export const predictCropDiseaseDirect = async (
  cropCode: string,
  imageUri: string
): Promise<DiseasePredictionResult> => {
  const formData = new FormData();
  formData.append('crop', cropCode.toLowerCase().trim());

  const filename = imageUri.split('/').pop() || 'leaf.jpg';
  const match = /\.(\w+)$/.exec(filename);
  let ext = match ? match[1].toLowerCase() : 'jpg';
  if (ext === 'jpg') ext = 'jpeg';
  const mimeType = `image/${ext}`;

  // React Native format for file upload
  formData.append('file', {
    uri: Platform.OS === 'ios' ? imageUri.replace('file://', '') : imageUri,
    name: filename,
    type: mimeType,
  } as any);

  try {
    const res = await cropHealthClient.post<DiseasePredictionResult>('/disease/predict', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  } catch (error: any) {
    if (error.response && error.response.data) {
      const data = error.response.data;
      if (data.status === 'rejected') {
        return {
          crop: cropCode,
          status: 'rejected',
          predicted_class: null,
          confidence: 0,
          low_confidence: false,
          input_verified: false,
          reason_code: data.reason_code || 'INVALID_IMAGE',
          message: data.message || data.detail || 'Image rejected by input verification.',
          metrics: data.metrics || {},
        };
      }
      if (data.detail) {
        return {
          crop: cropCode,
          status: 'rejected',
          predicted_class: null,
          confidence: 0,
          low_confidence: false,
          input_verified: false,
          reason_code: 'INVALID_IMAGE',
          message: typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail),
        };
      }
    }
    throw error;
  }
};

// ==============================================================================
// 3. Real Crop Report Creation, Upload & Diagnosis Pipeline
// ==============================================================================

export const createCropReportRecord = async (
  farmerId: string,
  farmerCropId: string,
  notes?: string,
  imageFilename?: string,
  phone?: string
): Promise<BackendCropReportItem> => {
  const res = await cropHealthClient.post<BackendCropReportItem>(
    `/farmers/${farmerId}/crop-reports`,
    {
      farmer_crop_id: farmerCropId,
      notes: notes || null,
      image_filename: imageFilename || 'leaf.jpg',
    },
    {
      headers: buildFarmerHeaders(phone, farmerId),
    }
  );
  return res.data;
};

export const uploadCropReportImageFile = async (
  farmerId: string,
  reportId: string,
  imageUri: string,
  phone?: string
): Promise<BackendCropReportItem> => {
  const formData = new FormData();
  const filename = imageUri.split('/').pop() || 'leaf.jpg';
  const match = /\.(\w+)$/.exec(filename);
  let ext = match ? match[1].toLowerCase() : 'jpg';
  if (ext === 'jpg') ext = 'jpeg';
  const mimeType = `image/${ext}`;

  formData.append('file', {
    uri: Platform.OS === 'ios' ? imageUri.replace('file://', '') : imageUri,
    name: filename,
    type: mimeType,
  } as any);

  const res = await cropHealthClient.put<BackendCropReportItem>(
    `/farmers/${farmerId}/crop-reports/${reportId}/image`,
    formData,
    {
      headers: {
        ...buildFarmerHeaders(phone, farmerId),
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return res.data;
};

export const diagnoseCropReportRecord = async (
  farmerId: string,
  reportId: string,
  phone?: string
): Promise<BackendDiagnosisRecord> => {
  const res = await cropHealthClient.post<BackendDiagnosisRecord>(
    `/farmers/${farmerId}/crop-reports/${reportId}/diagnose`,
    {},
    {
      headers: buildFarmerHeaders(phone, farmerId),
    }
  );
  return res.data;
};

export const fetchFarmerRecentReports = async (
  farmerId: string,
  phone?: string
): Promise<BackendCropReportItem[]> => {
  try {
    const res = await cropHealthClient.get<BackendCropReportItem[]>(
      `/farmers/${farmerId}/crop-reports`,
      {
        headers: buildFarmerHeaders(phone, farmerId),
      }
    );
    return res.data;
  } catch (err) {
    return [];
  }
};

// ==============================================================================
// 4. Trust Ladder, Corroboration & Expert Verification APIs
// ==============================================================================

export const fetchCropReportTrustStatus = async (
  reportId: string,
  phone?: string,
  farmerId?: string
): Promise<VerificationStatusData | null> => {
  try {
    const res = await cropHealthClient.get<VerificationStatusData>(
      `/crop-reports/${reportId}/verification-status`,
      {
        headers: buildFarmerHeaders(phone, farmerId),
      }
    );
    return res.data;
  } catch (err) {
    return null;
  }
};

export const requestAgriExpertVerification = async (
  reportId: string,
  notes?: string,
  phone?: string,
  farmerId?: string
): Promise<ExpertVerificationData> => {
  const res = await cropHealthClient.post<ExpertVerificationData>(
    `/crop-reports/${reportId}/verification-request`,
    {
      notes: notes || 'Expert diagnosis requested by farmer',
    },
    {
      headers: buildFarmerHeaders(phone, farmerId),
    }
  );
  return res.data;
};

export const submitPeerCorroboration = async (
  reportId: string,
  observationType: 'CONFIRMATION' | 'CONTRADICTION' | 'ADDITIONAL_SYMPTOM' | 'FIELD_NOTE',
  notes?: string,
  phone?: string,
  farmerId?: string
) => {
  const res = await cropHealthClient.post(
    `/crop-reports/${reportId}/corroborations`,
    {
      observation_type: observationType,
      notes: notes || undefined,
    },
    {
      headers: buildFarmerHeaders(phone, farmerId),
    }
  );
  return res.data;
};
