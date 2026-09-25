import axios from 'axios';
import { SEED_REPORTS, SEED_WEATHER_RISKS, SEED_MARKET_PRICES, SEED_SCHEMES } from '../constants/seedData';
import { CropReport, WeatherRisk, MarketPrice, Scheme } from '../types';

// Points to local FastAPI backend or fallback
const BASE_URL = 'http://10.0.2.2:8000/api/v1'; // standard Android emulator localhost, or change to LAN IP

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 4000,
});

// Full 7 Crop Disease Knowledge Base Mapping
const CROP_FALLBACKS: Record<string, {
  nameKn: string;
  nameEn: string;
  disease: string;
  diseaseKn: string;
  scientificName: string;
  remedyKn: string;
  remedyEn: string;
  source: string;
}> = {
  arecanut: {
    nameKn: 'ಅಡಿಕೆ',
    nameEn: 'Arecanut',
    disease: 'Koleroga (Mahali)',
    diseaseKn: 'ಕೊಳೆರೋಗ (ಮಹಾಲಿ)',
    scientificName: 'Phytophthora meadii',
    remedyKn: 'ಬೋರ್ಡೋ ದ್ರಾವಣ 1% (Bordeaux mixture 1%) ಸಿಂಪಡಿಸಿ. ತೋಟದಲ್ಲಿ ನೀರು ನಿಲ್ಲದಂತೆ ಬಸಿಗಾಲುವೆ ಸರಿಪಡಿಸಿ.',
    remedyEn: 'Spray 1% Bordeaux mixture before monsoon showers. Ensure drainage channels.',
    source: 'ICAR-CPCRI Kasaragod',
  },
  paddy: {
    nameKn: 'ಭತ್ತ',
    nameEn: 'Paddy',
    disease: 'Blast Disease',
    diseaseKn: 'ಬೆಂಕಿ ರೋಗ (ಬ್ಲಾಸ್ಟ್)',
    scientificName: 'Magnaporthe oryzae',
    remedyKn: 'ಟ್ರೈಸೈಕ್ಲಾಜೋಲ್ 75 ಡಬ್ಲ್ಯೂಪಿ @ 0.6 ಗ್ರಾಂ/ಲೀಟರ್ ನೀರಿಗೆ ಬೆರೆಸಿ ಸಿಂಪಡಿಸಿ.',
    remedyEn: 'Spray Tricyclazole 75% WP @ 0.6g/L water. Maintain moderate nitrogen application.',
    source: 'ICAR-IIRR Hyderabad',
  },
  coconut: {
    nameKn: 'ತೆಂಗು',
    nameEn: 'Coconut',
    disease: 'Bud Rot',
    diseaseKn: 'ಸುಳಿ ಕೊಳೆ ರೋಗ',
    scientificName: 'Phytophthora palmivora',
    remedyKn: 'ಬಾಧಿತ ಸುಳಿಯನ್ನು ಕತ್ತರಿಸಿ ತೆಗೆದು ಬೋರ್ಡೋ ಪೇಸ್ಟ್ ಲೇಪಿಸಿ. 1% ಬೋರ್ಡೋ ದ್ರಾವಣ ಸಿಂಪಡಿಸಿ.',
    remedyEn: 'Remove infected tissues and apply Bordeaux paste. Spray 1% Bordeaux mixture.',
    source: 'ICAR-CPCRI Kasaragod',
  },
  cardamom: {
    nameKn: 'ಏಲಕ್ಕಿ',
    nameEn: 'Cardamom',
    disease: 'Azhukal (Capsule Rot)',
    diseaseKn: 'ಅಳುಕಲ್ (ಕಾಯಿ ಕೊಳೆ ರೋಗ)',
    scientificName: 'Phytophthora nicotianae',
    remedyKn: '1% ಬೋರ್ಡೋ ದ್ರಾವಣ ಅಥವಾ ಕಾಪರ್ ಆಕ್ಸಿಕ್ಲೋರೈಡ್ 0.2% ಸಿಂಪಡಿಸಿ.',
    remedyEn: 'Spray 1% Bordeaux mixture or 0.2% Copper Oxychloride at base of clumps.',
    source: 'IISR Calicut',
  },
  pepper: {
    nameKn: 'ಕಾಳುಮೆಣಸು',
    nameEn: 'Black Pepper',
    disease: 'Quick Wilt (Foot Rot)',
    diseaseKn: 'ದ್ರುತ ಬಾಡುವ ರೋಗ (ಬುಡ ಕೊಳೆ ರೋಗ)',
    scientificName: 'Phytophthora capsici',
    remedyKn: 'ಬುಡಕ್ಕೆ 1% ಬೋರ್ಡೋ ದ್ರಾವಣ ಸುರಿಯಿರಿ ಅಥವಾ ಟ್ರೈಕೋಡರ್ಮಾ ಜೈವಿಕ ಶಿಲೀಂಧ್ರನಾಶಕ ಬಳಸಿ.',
    remedyEn: 'Drench root zone with 1% Bordeaux mixture or apply Trichoderma harzianum.',
    source: 'IISR Calicut',
  },
  ginger: {
    nameKn: 'ಶುಂಠಿ',
    nameEn: 'Ginger',
    disease: 'Soft Rot (Rhizome Rot)',
    diseaseKn: 'ಗಡ್ಡೆ ಕೊಳೆ ರೋಗ',
    scientificName: 'Pythium aphanidermatum',
    remedyKn: 'ಬೀಜೋಪಚಾರಕ್ಕಾಗಿ ಮೆಟಲಾಕ್ಸಿಲ್-ಎಂ 31.8% ಇಎಸ್ ಬಳಸಿ. ಮಣ್ಣಿಗೆ ನೀರು ಸರಾಗವಾಗಿ ಹರಿಯುವಂತೆ ಮಾಡಿ.',
    remedyEn: 'Treat seed rhizomes with Metalaxyl-M 31.8% ES. Ensure adequate field drainage.',
    source: 'IISR Calicut',
  },
  turmeric: {
    nameKn: 'ಅರಿಶಿನ',
    nameEn: 'Turmeric',
    disease: 'Leaf Spot (Colletotrichum)',
    diseaseKn: 'ಎಲೆ ಚುಕ್ಕೆ ರೋಗ',
    scientificName: 'Colletotrichum capsici',
    remedyKn: 'ಮ್ಯಾಂಕೋಜೆಬ್ 0.25% ಅಥವಾ ಕಾರ್ಬೆಂಡಾಜಿಮ್ 0.1% ಎಲೆಗಳ ಮೇಲೆ ಸಿಂಪಡಿಸಿ.',
    remedyEn: 'Spray Mancozeb 0.25% or Carbendazim 0.1% on foliage at 15-day intervals.',
    source: 'ICAR-IISR Calicut',
  },
};

export const fetchWeatherRisks = async (): Promise<WeatherRisk[]> => {
  try {
    const res = await api.get('/weather/risks');
    return res.data;
  } catch {
    return SEED_WEATHER_RISKS;
  }
};

export const fetchMarketPrices = async (): Promise<MarketPrice[]> => {
  try {
    const res = await api.get('/market/prices');
    return res.data;
  } catch {
    return SEED_MARKET_PRICES;
  }
};

export const fetchSchemes = async (): Promise<Scheme[]> => {
  try {
    const res = await api.get('/schemes');
    return res.data;
  } catch {
    return SEED_SCHEMES;
  }
};

export const submitCropReport = async (reportData: Partial<CropReport>): Promise<CropReport> => {
  const cropKey = (reportData.crop || 'arecanut').toLowerCase();
  const fallbackInfo = CROP_FALLBACKS[cropKey] || CROP_FALLBACKS.arecanut;

  const newReport: CropReport = {
    id: 'rep_' + Date.now(),
    crop: reportData.crop || 'arecanut',
    cropNameKn: fallbackInfo.nameKn,
    cropNameEn: fallbackInfo.nameEn,
    photoUri: reportData.photoUri,
    symptoms: reportData.symptoms || '',
    predictedDisease: fallbackInfo.disease,
    predictedDiseaseKn: fallbackInfo.diseaseKn,
    scientificName: fallbackInfo.scientificName,
    confidence: 0.92,
    status: 'ai_analysed',
    villageId: reportData.villageId || 'v2',
    villageName: reportData.villageName || 'ಉಜಿರೆ (Ujire)',
    reporterRole: reportData.reporterRole || 'farmer',
    proxyFor: reportData.proxyFor,
    createdAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ', ಇಂದು',
    remedyKn: fallbackInfo.remedyKn,
    remedyEn: fallbackInfo.remedyEn,
    sourceInstitution: fallbackInfo.source,
    evidenceFarmsCount: 1,
  };

  try {
    const res = await api.post('/reports', newReport);
    return res.data;
  } catch {
    return newReport;
  }
};

export const diseaseService = {
  predict: async (crop: string, imageUri?: string) => {
    const cropKey = (crop || 'arecanut').toLowerCase();
    const fallbackInfo = CROP_FALLBACKS[cropKey] || CROP_FALLBACKS.arecanut;
    return {
      predictedDisease: fallbackInfo.disease,
      predictedDiseaseKn: fallbackInfo.diseaseKn,
      scientificName: fallbackInfo.scientificName,
      confidence: 0.92,
      remedyKn: fallbackInfo.remedyKn,
      remedyEn: fallbackInfo.remedyEn,
      sourceInstitution: fallbackInfo.source,
    };
  },
};
