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
  state?: string | null;
  predicted_class?: string | null;
  diagnosis?: string | null;
  confidence: number;
  low_confidence: boolean;
  input_verified: boolean;
  reason_code?: string | null;
  message?: string | null;
  model_version?: string | null;
  disease_info?: DiseaseInfo | null;
  predictions?: ClassPrediction[];
  metrics?: Record<string, any>;
  disease?: string | null;
  disease_name_kn?: string | null;
  knowledge_base_reference?: string | null;
  explanation_kn?: string | null;
  approved_actions?: string[];
  verification_state?: string;
  generated_at?: string | null;
  is_llm_generated?: boolean;
  fallback_used?: boolean;
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
  payment_status?: string | null;
  payment_mode?: string | null;
  payment_amount?: number | null;
  crop?: string | null;
  diagnosis?: string | null;
  ai_confidence?: number | null;
}

export interface ExpertQueueItemData {
  id: string;
  crop_report_id: string;
  farmer_id: string;
  farmer_name?: string;
  farmer_phone?: string;
  location?: string;
  priority?: 'HIGH' | 'NORMAL' | 'MODERATE';
  expert_id?: string | null;
  status: string;
  crop_code?: string;
  crop_name?: string;
  crop_name_kn?: string;
  farmer_notes?: string | null;
  image_storage_path?: string | null;
  image_filename?: string | null;
  latest_diagnosis?: {
    crop: string;
    predicted_class: string;
    predicted_class_kn?: string;
    confidence: number;
    category?: string;
    model_name: string;
    created_at: string;
  } | null;
  scientific_info?: {
    causal_agent?: string;
    symptoms?: string;
    recommended_spray?: string;
  };
  corroboration_summary?: {
    total_count: number;
    agreed_count: number;
    disagreed_count: number;
    min_required?: number;
    threshold_satisfied?: boolean;
    is_corroborated?: boolean;
    similarity?: string;
    agree_farmers?: string[];
    disagree_farmers?: string[];
  } | null;
  requested_at: string;
  assigned_at?: string | null;
  completed_at?: string | null;
  payment_status?: string | null;
  payment_mode?: string | null;
  payment_amount?: number | null;
  diagnosis?: string | null;
  ai_confidence?: number | null;
  expert_decision?: 'CONFIRM' | 'CORRECT' | 'REQUIRES_MORE_INFORMATION';
  expert_finding?: string;
  expert_notes?: string;
  expert_remedy?: string;
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
        const cropCodeResolved = (typeof data.crop === 'object' && data.crop?.code) ? data.crop.code : (data.crop || cropCode);
        return {
          crop: cropCodeResolved,
          status: 'rejected',
          state: data.state || data.reason_code || 'IRRELEVANT_IMAGE',
          predicted_class: null,
          diagnosis: null,
          confidence: 0,
          low_confidence: false,
          input_verified: false,
          reason_code: data.reason_code || data.state || 'INVALID_IMAGE',
          message: data.message || data.detail || 'Image rejected by input verification.',
          metrics: data.metrics || {},
        };
      }
      if (data.detail) {
        return {
          crop: cropCode,
          status: 'rejected',
          state: 'INVALID_IMAGE',
          predicted_class: null,
          diagnosis: null,
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
  farmerId?: string,
  paymentData?: {
    payment_status?: string;
    payment_mode?: string;
    amount?: number;
    crop?: string;
    diagnosis?: string;
    ai_confidence?: number;
  }
): Promise<ExpertVerificationData> => {
  const res = await cropHealthClient.post<ExpertVerificationData>(
    `/crop-reports/${reportId}/verification-request`,
    {
      notes: notes || 'Expert diagnosis requested by farmer',
      payment_status: paymentData?.payment_status || 'SUCCESS',
      payment_mode: paymentData?.payment_mode || 'DEMO',
      amount: paymentData?.amount || 49.0,
      crop: paymentData?.crop,
      diagnosis: paymentData?.diagnosis,
      ai_confidence: paymentData?.ai_confidence,
    },
    {
      headers: buildFarmerHeaders(phone, farmerId),
    }
  );
  return res.data;
};

export const INITIAL_DEMO_EXPERT_QUEUE: ExpertQueueItemData[] = [
  {
    id: 'demo-paddy-blast',
    crop_report_id: 'report-paddy-blast-001',
    farmer_id: 'farmer-mallikarjuna-001',
    farmer_name: 'Mallikarjuna G.',
    farmer_phone: '+91 98765 43210',
    location: 'Ujire (ಉಜಿರೆ)',
    priority: 'HIGH',
    status: 'PENDING',
    crop_code: 'paddy',
    crop_name: 'Paddy',
    crop_name_kn: 'ಭತ್ತ',
    diagnosis: 'Blast Disease',
    ai_confidence: 0.94,
    latest_diagnosis: {
      crop: 'Paddy',
      predicted_class: 'Blast Disease (ಬೆಂಕಿ ರೋಗ)',
      predicted_class_kn: 'ಬೆಂಕಿ ರೋಗ (Blast)',
      confidence: 0.94,
      category: 'Fungal (ಶಿಲೀಂಧ್ರ ರೋಗ)',
      model_name: 'ResNet50_CropDisease_v2.4',
      created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
    },
    scientific_info: {
      causal_agent: 'Magnaporthe oryzae (Pyricularia oryzae)',
      symptoms: 'Spindle-shaped lesions with grey center and brown margins on leaves and leaf sheath. Severe neck blast leads to grain shattering.',
      recommended_spray: 'Spray Tricyclazole 75% WP @ 0.6 g/L or Kasugamycin 3% SL @ 2 ml/L before morning dew.',
    },
    corroboration_summary: {
      total_count: 4,
      agreed_count: 3,
      disagreed_count: 1,
      similarity: 'High (80% Agreement)',
      agree_farmers: ['Ravi Hegde (Ujire)', 'Shiva Kumar (Belthangady)', 'Manjunath (Mundaje)'],
      disagree_farmers: ['Anand Gowda (Ujire - suspected brown spot)'],
    },
    requested_at: new Date(Date.now() - 3600000 * 3).toISOString(),
    payment_status: 'SUCCESS',
    payment_mode: 'DEMO',
    payment_amount: 49.0,
    image_storage_path: 'crops/paddy.jpg',
  },
  {
    id: 'demo-arecanut-koleroga',
    crop_report_id: 'report-arecanut-koleroga-002',
    farmer_id: 'farmer-shankara-002',
    farmer_name: 'Shankara Bhat',
    farmer_phone: '+91 94481 99887',
    location: 'Ujire (ಉಜಿರೆ)',
    priority: 'HIGH',
    status: 'PENDING',
    crop_code: 'arecanut',
    crop_name: 'Arecanut',
    crop_name_kn: 'ಅಡಿಕೆ',
    diagnosis: 'Koleroga / Fruit Rot',
    ai_confidence: 0.73,
    latest_diagnosis: {
      crop: 'Arecanut',
      predicted_class: 'Koleroga / Fruit Rot (ಕೊಳೆರೋಗ)',
      predicted_class_kn: 'ಕೊಳೆರೋಗ / ಮಹಾಳಿ (Koleroga)',
      confidence: 0.73,
      category: 'Fungal (ಶಿಲೀಂಧ್ರ ರೋಗ)',
      model_name: 'ResNet50_CropDisease_v2.4',
      created_at: new Date(Date.now() - 3600000 * 5).toISOString(),
    },
    scientific_info: {
      causal_agent: 'Phytophthora meadii McRae',
      symptoms: 'Water-soaked lesions on unripe nuts near perianth, leading to extensive rotting and sudden mass fruit drop in high humidity.',
      recommended_spray: 'Prophylactic application of 1% Bordeaux Mixture or Metalaxyl MZ 72% WP (2 g/L) on all fruit bunches.',
    },
    corroboration_summary: {
      total_count: 5,
      agreed_count: 4,
      disagreed_count: 1,
      similarity: 'High (85% Agreement)',
      agree_farmers: ['Ganesh Bhat (Ujire)', 'Suresh Gowda (FPO Hub)', 'Kariyappa (Ujire)', 'Ramesh H (Ujire)'],
      disagree_farmers: ['Venkatesh (Suspected Bud Rot)'],
    },
    requested_at: new Date(Date.now() - 3600000 * 6).toISOString(),
    payment_status: 'SUCCESS',
    payment_mode: 'DEMO',
    payment_amount: 49.0,
    image_storage_path: 'crops/arecanut.jpg',
  },
  {
    id: 'demo-cardamom-uncertain',
    crop_report_id: 'report-cardamom-uncertain-003',
    farmer_id: 'farmer-ravi-003',
    farmer_name: 'Ravi Kumar',
    farmer_phone: '+91 97401 55443',
    location: 'Mudigere (ಮೂಡಿಗೆರೆ)',
    priority: 'MODERATE',
    status: 'PENDING',
    crop_code: 'cardamom',
    crop_name: 'Cardamom',
    crop_name_kn: 'ಏಲಕ್ಕಿ',
    diagnosis: 'Uncertain Disease',
    ai_confidence: 0.54,
    latest_diagnosis: {
      crop: 'Cardamom',
      predicted_class: 'Uncertain Disease (ರೋಗ ಅನಿಶ್ಚಿತತೆ)',
      predicted_class_kn: 'ರೋಗ ಅನಿಶ್ಚಿತತೆ (Katte / Rot)',
      confidence: 0.54,
      category: 'Uncertain / Low Confidence',
      model_name: 'ResNet50_CropDisease_v2.4',
      created_at: new Date(Date.now() - 3600000 * 8).toISOString(),
    },
    scientific_info: {
      causal_agent: 'Cardamom mosaic virus / Pythium spp.',
      symptoms: 'Irregular chlorotic streaks along veins, stunted young tiller emergence, needs close examination of rhizome collar.',
      recommended_spray: 'Inspect root system for softness; rogue virus-positive clumps and spray systemic insecticide for aphid vector.',
    },
    corroboration_summary: {
      total_count: 3,
      agreed_count: 2,
      disagreed_count: 1,
      similarity: 'Moderate (60% Agreement)',
      agree_farmers: ['Praveen K (Mudigere)', 'Dinesh (Sakleshpur)'],
      disagree_farmers: ['Shekhar (Thought iron chlorosis)'],
    },
    requested_at: new Date(Date.now() - 3600000 * 9).toISOString(),
    payment_status: 'SUCCESS',
    payment_mode: 'DEMO',
    payment_amount: 49.0,
    image_storage_path: 'crops/cardamom.jpg',
  },
  {
    id: 'demo-blackpepper-quickwilt',
    crop_report_id: 'report-blackpepper-quickwilt-004',
    farmer_id: 'farmer-devendra-004',
    farmer_name: 'Devendra Gowda',
    farmer_phone: '+91 99008 33221',
    location: 'Belthangady (ಬೆಳ್ತಂಗಡಿ)',
    priority: 'HIGH',
    status: 'PENDING',
    crop_code: 'black_pepper',
    crop_name: 'Black Pepper',
    crop_name_kn: 'ಕಾಳುಮೆಣಸು',
    diagnosis: 'Quick Wilt (Foot Rot)',
    ai_confidence: 0.88,
    latest_diagnosis: {
      crop: 'Black Pepper',
      predicted_class: 'Quick Wilt / Foot Rot (ದ್ರುತ ಸೊರಗು ರೋಗ)',
      predicted_class_kn: 'ದ್ರುತ ಸೊರಗು ರೋಗ (Quick Wilt)',
      confidence: 0.88,
      category: 'Fungal (ಶಿಲೀಂಧ್ರ ರೋಗ)',
      model_name: 'ResNet50_CropDisease_v2.4',
      created_at: new Date(Date.now() - 3600000 * 12).toISOString(),
    },
    scientific_info: {
      causal_agent: 'Phytophthora capsici',
      symptoms: 'Dark necrotic lesions on collar, total foliar flaccidity, rapid wilting without yellowing, rapid vine collapse.',
      recommended_spray: 'Soil drench with 0.2% Copper Oxychloride or 1% Bordeaux mixture + foliar spray of Potassium Phosphonate 0.3%.',
    },
    corroboration_summary: {
      total_count: 4,
      agreed_count: 4,
      disagreed_count: 0,
      similarity: 'High (100% Agreement)',
      agree_farmers: ['Somesh (Belthangady)', 'Harish (Ujire)', 'Subraya (Puttur)', 'Prakash (Bantwal)'],
      disagree_farmers: [],
    },
    requested_at: new Date(Date.now() - 3600000 * 14).toISOString(),
    payment_status: 'SUCCESS',
    payment_mode: 'DEMO',
    payment_amount: 49.0,
    image_storage_path: 'crops/black_pepper.jpg',
  },
];

let inMemoryDemoExpertQueue: ExpertQueueItemData[] = [...INITIAL_DEMO_EXPERT_QUEUE];

export const fetchExpertQueue = async (
  phone?: string,
  expertId?: string
): Promise<{ items: ExpertQueueItemData[]; total: number }> => {
  try {
    const res = await cropHealthClient.get<{ items: ExpertQueueItemData[]; total: number }>(
      '/expert/verifications',
      {
        headers: buildFarmerHeaders(phone, expertId),
      }
    );
    const backendItems = res.data?.items || [];
    // Ensure all demo requests are merged seamlessly
    const existingIds = new Set(backendItems.map((b) => b.id));
    const merged = [
      ...backendItems,
      ...inMemoryDemoExpertQueue.filter((d) => !existingIds.has(d.id)),
    ];
    return { items: merged, total: merged.length };
  } catch {
    return { items: inMemoryDemoExpertQueue, total: inMemoryDemoExpertQueue.length };
  }
};

export const submitExpertDecision = async (
  requestId: string,
  decision: 'APPROVE' | 'CONFIRM' | 'CORRECT' | 'VERIFIED' | 'REJECT' | 'REQUEST_REVIEW' | 'NEED_MORE_INFO' | 'REQUIRES_MORE_INFORMATION',
  finding?: string,
  notes?: string,
  remedy?: string,
  phone?: string,
  expertId?: string
) => {
  const normalizedStatus =
    decision === 'VERIFIED' || decision === 'APPROVE' || decision === 'CONFIRM' || decision === 'CORRECT'
      ? 'VERIFIED'
      : decision === 'NEED_MORE_INFO' || decision === 'REQUEST_REVIEW' || decision === 'REQUIRES_MORE_INFORMATION'
      ? 'NEED_MORE_INFO'
      : 'REJECTED';

  // Always update in-memory demo queue so immediate state reflects across dashboard and history
  inMemoryDemoExpertQueue = inMemoryDemoExpertQueue.map((item) => {
    if (item.id === requestId) {
      return {
        ...item,
        status: normalizedStatus,
        expert_decision: decision as any,
        expert_finding: finding || item.diagnosis || undefined,
        expert_notes: notes || undefined,
        expert_remedy: remedy || undefined,
        completed_at: new Date().toISOString(),
      };
    }
    return item;
  });

  if (!requestId.startsWith('demo-')) {
    try {
      const res = await cropHealthClient.post(
        `/expert/verifications/${requestId}/decision`,
        {
          decision,
          finding,
          expert_notes: notes,
          recommended_action: remedy,
        },
        {
          headers: buildFarmerHeaders(phone, expertId),
        }
      );
      return res.data;
    } catch (err) {
      console.warn('Backend decision update had network issue, using cached status:', err);
    }
  }

  return { status: normalizedStatus, updated: true };
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
