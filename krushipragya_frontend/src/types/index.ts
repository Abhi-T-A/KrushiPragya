export interface CropReport {
  id: string;
  crop: 'arecanut' | 'paddy' | 'coconut' | 'cardamom' | 'pepper' | 'ginger' | 'turmeric' | string;
  cropNameKn: string;
  cropNameEn: string;
  photoUri?: string;
  symptoms?: string;
  predictedDisease?: string;
  predictedDiseaseKn?: string;
  scientificName?: string;
  category?: string;
  confidence: number;
  lowConfidence?: boolean;
  inputVerified?: boolean;
  reasonCode?: string;
  status: 'unverified' | 'ai_analysed' | 'corroborated' | 'expert_verified' | 'UNVERIFIED' | 'AI_ANALYSED' | 'CORROBORATED' | 'EXPERT_VERIFIED';
  villageId: string;
  villageName: string;
  reporterRole: 'farmer' | 'village_node' | 'expert' | 'officer' | 'buyer' | 'community';
  proxyFor?: string;
  createdAt: string;
  remedyKn?: string;
  remedyEn?: string;
  culturalControl?: string;
  explanationKn?: string;
  approvedActions?: string[];
  sourceInstitution?: string;
  evidenceFarmsCount?: number;
  verifiedBy?: string;
  verifiedAt?: string;
  backendReportId?: string;
  farmerId?: string;
  farmerCropId?: string;
  predictions?: Array<{ class_name: string; confidence: number }>;
  corroborationCount?: number;
  contradictionCount?: number;
  expertDecision?: string;
  expertNotes?: string;
  expertRequested?: boolean;
}

export interface WeatherRisk {
  villageId: string;
  villageName: string;
  crop: string;
  riskLevel: 'HIGH' | 'MEDIUM' | 'LOW';
  diseaseRisk: string;
  diseaseRiskKn: string;
  triggerCondition: string;
  advisoryKn: string;
  advisoryEn: string;
  humidity: number;
  tempMin: number;
  tempMax: number;
  rainfallMm: number;
  validUntil: string;
  source?: string;
}

export interface MandiPrice {
  crop: string;
  cropKn: string;
  market: string;
  marketKn: string;
  pricePerQuintal: number;
  changePercent: number;
  isPositive: boolean;
  date: string;
}

export interface MarketPrice {
  id: string;
  crop: string;
  cropKn: string;
  sourceLabel: string;
  sourceType: 'APMC' | 'Buyer' | 'Farmer Reported';
  pricePerQuintal: number;
  recordedAt: string;
}

export interface Scheme {
  id: string;
  nameKn: string;
  nameEn: string;
  department: string;
  crop: string;
  district: string;
  eligibilityKn: string;
  eligibilityEn: string;
  benefitKn: string;
  benefitEn: string;
  officialSourceUrl: string;
  lastVerified: string;
}

export interface DiseaseKnowledge {
  id: string;
  crop: string;
  diseaseEn: string;
  diseaseKn: string;
  scientificName: string;
  symptomsEn: string;
  symptomsKn: string;
  favorableConditionsEn: string;
  favorableConditionsKn: string;
  organicRemedyEn: string;
  organicRemedyKn: string;
  chemicalRemedyEn: string;
  chemicalRemedyKn: string;
  dosageEn: string;
  dosageKn: string;
  stageRecommendations: {
    earlyEn: string;
    earlyKn: string;
    moderateEn: string;
    moderateKn: string;
    severeEn: string;
    severeKn: string;
  };
  source: string;
}
