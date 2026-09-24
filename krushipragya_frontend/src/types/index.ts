export interface CropReport {
  id: string;
  crop: 'arecanut' | 'paddy' | 'coconut' | 'cardamom';
  cropNameKn: string;
  cropNameEn: string;
  photoUri?: string;
  symptoms?: string;
  predictedDisease?: string;
  predictedDiseaseKn?: string;
  scientificName?: string;
  confidence: number;
  status: 'unverified' | 'ai_analysed' | 'corroborated' | 'expert_verified';
  villageId: string;
  villageName: string;
  reporterRole: 'farmer' | 'village_node';
  proxyFor?: string; // Farmer name if entered by village node
  createdAt: string;
  remedyKn?: string;
  remedyEn?: string;
  sourceInstitution?: string;
  evidenceFarmsCount?: number; // e.g., 3 independent farms
  verifiedBy?: string;
  verifiedAt?: string;
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
  source: string;
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
