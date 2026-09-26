import { api } from './api';

export interface AdvisoryActionItem {
  action_kn: string;
  action_en?: string;
  priority: number;
  time_window: string;
  category?: string;
}

export interface AdvisoryCropContext {
  id?: string;
  code: string;
  name_en: string;
  name_kn: string;
  area_acres?: number;
}

export interface AdvisoryLocationContext {
  village_id?: string;
  name: string;
  name_kn?: string;
  district?: string;
  state?: string;
}

export interface AdvisoryProvenance {
  rule_id: number;
  risk_name: string;
  risk_level: string;
  source_name?: string;
  source_reference?: string;
  condition_type?: string;
}

export interface FarmerComprehensiveAdvisoryResponse {
  advisory_id?: string;
  title: string;
  title_kn?: string;
  severity: string;
  risk_level?: string;
  summary: string;
  summary_kn?: string;
  reason: string;
  recommended_actions: string[];
  actions: AdvisoryActionItem[];
  crop?: AdvisoryCropContext;
  location?: AdvisoryLocationContext;
  language: 'en' | 'kn';
  sources: string[];
  provenance: AdvisoryProvenance[];
  is_llm_generated: boolean;
  generated_at?: string;
  valid_from?: string;
  valid_until?: string;
  forecast_valid_until?: string;
  weather_observed_at?: string;
  confidence_level?: string;
  confidence_level_kn?: string;
  status?: string;
  evidence?: any[];
}

export interface WeatherMetricsContext {
  temperature_c?: number;
  humidity_pct?: number;
  rainfall_mm_48h?: number;
  max_temperature_c_48h?: number;
  avg_humidity_pct_48h?: number;
}

export interface RegisteredFarmerCrop {
  id: string;
  farmer_id: string;
  crop_id: string;
  area_acres?: number | string;
  is_primary: boolean;
  crop: {
    id: string;
    code: string;
    name_en: string;
    name_kn: string;
    is_active: boolean;
  };
}

/**
 * Fetch authoritative production agricultural advisory for a farmer or village+crop.
 */
export const fetchFarmerComprehensiveAdvisory = async (
  farmerId?: string,
  cropCode: string = 'arecanut',
  villageId: string = 'V001',
  language: 'en' | 'kn' = 'kn',
  forceRefresh: boolean = false,
  cropId?: string,
  phone?: string
): Promise<FarmerComprehensiveAdvisoryResponse> => {
  // If authenticated farmerId is provided, call authoritative farmer advisory endpoint
  if (farmerId) {
    try {
      const endpoint = `/farmers/${farmerId}/advisory`;
      const headers: Record<string, string> = { 'x-farmer-id': farmerId };
      if (phone) headers['x-farmer-phone'] = phone;

      if (forceRefresh) {
        const payload: Record<string, any> = {
          language,
          force_refresh: true,
        };
        if (cropId) payload.crop_id = cropId;

        const postRes = await api.post(endpoint, payload, { headers });
        if (postRes.data) {
          return postRes.data;
        }
      } else {
        const params: Record<string, any> = { language };
        if (cropId) params.crop_id = cropId;

        const getRes = await api.get(endpoint, {
          headers,
          params,
        });
        if (getRes.data) {
          return getRes.data;
        }
      }
    } catch (err: any) {
      console.log('[AdvisoryAPI] Farmer endpoint error, trying fallback to weather advisory:', err?.message);
    }
  }

  // Fallback to village + crop forecast advisory endpoint
  const weatherRes = await api.get('/weather/farmer-advisory', {
    params: {
      village_id: villageId || 'V001',
      crop: cropCode,
      language,
    },
  });

  const wData = weatherRes.data;
  const isKn = language === 'kn';
  const advisories = wData.advisories || [];
  const primaryAdv = advisories.length > 0 ? advisories[0] : null;

  const actionsList: AdvisoryActionItem[] = advisories.map((adv: any) => ({
    action_kn: adv.message_kn || adv.message_en,
    action_en: adv.message_en,
    priority: adv.risk_level === 'HIGH' ? 1 : (adv.risk_level === 'MODERATE' ? 2 : 3),
    time_window: isKn ? 'ಮುಂದಿನ 24-48 ಗಂಟೆಗಳು' : 'Next 24-48 hours',
    category: 'WEATHER',
  }));

  const recommendedStrings: string[] = advisories.map((adv: any) =>
    isKn ? (adv.message_kn || adv.message_en) : adv.message_en
  );

  const highestRisk = advisories.some((a: any) => a.risk_level === 'HIGH')
    ? 'HIGH'
    : (advisories.some((a: any) => a.risk_level === 'MODERATE') ? 'MODERATE' : 'LOW');

  const cropNameKn = cropCode.toLowerCase().includes('paddy') ? 'ಭತ್ತ' : 'ಅಡಿಕೆ';
  const cropNameEn = cropCode.toLowerCase().includes('paddy') ? 'Paddy' : 'Arecanut';

  return {
    title: isKn ? `${cropNameKn} - ಕೃಷಿ ಸಲಹೆ` : `Agricultural Advisory - ${cropNameEn}`,
    title_kn: `${cropNameKn} - ಕೃಷಿ ಸಲಹೆ`,
    severity: highestRisk,
    risk_level: highestRisk,
    summary: primaryAdv
      ? (isKn ? (primaryAdv.message_kn || primaryAdv.message_en) : primaryAdv.message_en)
      : (isKn ? 'ಪ್ರಸ್ತುತ ಯಾವುದೇ ಪ್ರತಿಕೂಲ ಹವಾಮಾನ ಅಥವಾ ರೋಗದ ಗಂಭೀರ ಅಪಾಯವಿಲ್ಲ.' : 'No acute weather risks currently detected.'),
    summary_kn: primaryAdv?.message_kn || 'ಪ್ರಸ್ತುತ ಯಾವುದೇ ಹವಾಮಾನ ಅಪಾಯವಿಲ್ಲ.',
    reason: primaryAdv
      ? (primaryAdv.matched_factors?.[0] || primaryAdv.risk_name)
      : (isKn ? 'ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ ಸ್ಥಿರವಾಗಿದೆ.' : 'Weather forecast conditions are stable.'),
    recommended_actions: recommendedStrings.length > 0
      ? recommendedStrings
      : [isKn ? 'ನಿಯಮಿತ ತೋಟ ಪರಿಶೀಲನೆ ಮುಂದುವರಿಸಿ.' : 'Continue routine plot inspection.'],
    actions: actionsList.length > 0 ? actionsList : [
      {
        action_kn: 'ನಿಯಮಿತ ತೋಟ ಪರಿಶೀಲನೆ ಮುಂದುವರಿಸಿ.',
        action_en: 'Continue routine plot inspection.',
        priority: 3,
        time_window: isKn ? 'ಮುಂದಿನ 24-48 ಗಂಟೆಗಳು' : 'Next 24-48 hours',
        category: 'ACTIVITY',
      }
    ],
    crop: {
      code: cropCode,
      name_en: cropNameEn,
      name_kn: cropNameKn,
    },
    location: {
      village_id: villageId,
      name: villageId === 'v2' || villageId === 'V001' ? 'Ujire' : 'Village',
      name_kn: 'ಉಜಿರೆ',
      district: 'Dakshina Kannada',
      state: 'Karnataka',
    },
    language,
    sources: primaryAdv?.source_name ? [primaryAdv.source_name] : ['ICAR - CPCRI / KrushiPragya'],
    provenance: primaryAdv?.provenance ? [primaryAdv.provenance] : [],
    is_llm_generated: false,
    generated_at: new Date().toISOString(),
    confidence_level: advisories.length > 0 ? 'HIGH' : 'MEDIUM',
    confidence_level_kn: advisories.length > 0 ? 'ಹೆಚ್ಚು' : 'ಮಧ್ಯಮ',
    status: 'ACTIVE',
  };
};

/**
 * Fetch historical advisories for the authenticated farmer.
 */
export const fetchFarmerAdvisoriesHistory = async (
  farmerId: string,
  limit: number = 10,
  phone?: string
): Promise<FarmerComprehensiveAdvisoryResponse[]> => {
  try {
    const headers: Record<string, string> = { 'x-farmer-id': farmerId };
    if (phone) headers['x-farmer-phone'] = phone;

    const res = await api.get(`/farmers/${farmerId}/advisories`, {
      headers,
      params: { limit },
    });
    return res.data?.advisories || [];
  } catch (err: any) {
    console.log('[AdvisoryAPI] Error fetching advisories history:', err?.message);
    return [];
  }
};

/**
 * Fetch registered crops for the authenticated farmer.
 */
export const fetchFarmerCrops = async (
  farmerId: string,
  phone?: string
): Promise<RegisteredFarmerCrop[]> => {
  try {
    const headers: Record<string, string> = { 'x-farmer-id': farmerId };
    if (phone) headers['x-farmer-phone'] = phone;

    const res = await api.get(`/farmers/${farmerId}/crops`, {
      headers,
    });
    return Array.isArray(res.data) ? res.data : [];
  } catch (err: any) {
    console.log('[AdvisoryAPI] Error fetching farmer crops:', err?.message);
    return [];
  }
};
