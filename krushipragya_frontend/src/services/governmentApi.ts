/**
 * Government Officer API Service
 * Handles scheme applications, officer reviews, regional insights, farmer assistance, and alerts.
 */

export interface GovernmentDashboardStats {
  farmers_count: number;
  applications_count: number;
  schemes_count: number;
  pending_count: number;
  approved_count: number;
  under_review_count: number;
  rejected_count: number;
}

export interface SchemeApplicationItem {
  id: string;
  application_number: string;
  scheme_id: string;
  scheme_title: string;
  scheme_title_kn?: string;
  scheme_category: string;
  farmer_id: string;
  farmer_name: string;
  farmer_mobile: string;
  village: string;
  district: string;
  crop: string;
  crop_kn?: string;
  land_holding_acres: string;
  submitted_date: string;
  status: 'PENDING' | 'UNDER_REVIEW' | 'APPROVED' | 'REJECTED';
  eligibility_checklist: {
    land_requirement: boolean;
    farmer_category: boolean;
    mandatory_docs: boolean;
  };
  documents: {
    aadhaar_verified: boolean;
    aadhaar_number: string;
    land_record_verified: boolean;
    land_record_number: string;
    bank_verified: boolean;
    bank_name: string;
  };
  farmer_notes?: string;
  officer_notes?: string;
  subsidy_amount?: string;
}

export interface GovernmentSchemeStatItem {
  id: string;
  title: string;
  title_kn: string;
  category: string;
  department: string;
  benefits: string;
  benefits_kn: string;
  eligibility: string;
  eligibility_kn: string;
  required_docs: string[];
  total_applications: number;
  approved: number;
  pending: number;
  rejected: number;
  reach_percentage: number;
}

export interface RegionalCropReportInsight {
  crop_name: string;
  crop_name_kn: string;
  report_count: number;
  verified_disease_count: number;
  risk_level: 'HIGH' | 'MODERATE' | 'NORMAL';
  dominant_disease: string;
  dominant_disease_kn: string;
}

export interface WeatherRiskAlert {
  district: string;
  district_kn: string;
  weather_condition: string;
  risk_level: 'HIGH' | 'MEDIUM' | 'LOW';
  advisory_message: string;
}

export interface GovernmentOfficialAlert {
  id: string;
  title: string;
  title_kn: string;
  district: string;
  affected_crops: string;
  message: string;
  published_at: string;
  published_by: string;
  recipient_farmers_count: number;
}

export interface FarmerAssistanceProfile {
  id: string;
  name: string;
  village: string;
  district: string;
  mobile: string;
  land_acres: string;
  crops: Array<{ name: string; name_kn: string; icon: string }>;
  total_applications: number;
  approved: number;
  pending: number;
}

// Canonical seed data for Government Officer workflow
export const INITIAL_GOVT_STATS: GovernmentDashboardStats = {
  farmers_count: 128,
  applications_count: 34,
  schemes_count: 12,
  pending_count: 7,
  approved_count: 86,
  under_review_count: 12,
  rejected_count: 6,
};

export const INITIAL_GOVT_APPLICATIONS: SchemeApplicationItem[] = [
  {
    id: 'app-001',
    application_number: 'KP-2026-00124',
    scheme_id: 'scheme-pm-kisan',
    scheme_title: 'PM-KISAN (Farmer Support Scheme)',
    scheme_title_kn: 'ಪ್ರಧಾನಮಂತ್ರಿ ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ (ಪಿಎಂ-ಕಿಸಾನ್)',
    scheme_category: 'Farmer Support',
    farmer_id: 'farmer-mallikarjuna-001',
    farmer_name: 'Mallikarjuna G.',
    farmer_mobile: '+91 98765 43210',
    village: 'Ujire (ಉಜಿರೆ)',
    district: 'Dakshina Kannada (ದಕ್ಷಿಣ ಕನ್ನಡ)',
    crop: 'Paddy & Arecanut',
    crop_kn: 'ಭತ್ತ ಮತ್ತು ಅಡಿಕೆ',
    land_holding_acres: '2.5 Acres (ಸಣ್ಣ ರೈತರು)',
    submitted_date: '24 Sept 2026, 11:30 AM',
    status: 'UNDER_REVIEW',
    eligibility_checklist: {
      land_requirement: true,
      farmer_category: true,
      mandatory_docs: true,
    },
    documents: {
      aadhaar_verified: true,
      aadhaar_number: 'XXXX-XXXX-4321',
      land_record_verified: true,
      land_record_number: 'RTC-2026-UJ-881',
      bank_verified: true,
      bank_name: 'Canara Bank (Ujire Branch - A/C XXXX8910)',
    },
    farmer_notes: 'Small farmer cultivating paddy and arecanut in Ujire village.',
    officer_notes: 'Land records verified against Bhoomi portal. Bank details active.',
    subsidy_amount: '₹6,000 / year (Direct DBT)',
  },
  {
    id: 'app-002',
    application_number: 'KP-2026-00125',
    scheme_id: 'scheme-crop-insurance',
    scheme_title: 'Karnataka Raitha Siri Crop Insurance',
    scheme_title_kn: 'ಕರ್ನಾಟಕ ರೈತ ಸಿರಿ ಬೆಳೆ ವಿಮೆ ಯೋಜನೆ',
    scheme_category: 'Insurance',
    farmer_id: 'farmer-shankara-002',
    farmer_name: 'Shankara Bhat',
    farmer_mobile: '+91 94481 99887',
    village: 'Ujire (ಉಜಿರೆ)',
    district: 'Dakshina Kannada',
    crop: 'Arecanut',
    crop_kn: 'ಅಡಿಕೆ',
    land_holding_acres: '3.0 Acres',
    submitted_date: '25 Sept 2026, 02:15 PM',
    status: 'PENDING',
    eligibility_checklist: {
      land_requirement: true,
      farmer_category: true,
      mandatory_docs: true,
    },
    documents: {
      aadhaar_verified: true,
      aadhaar_number: 'XXXX-XXXX-9988',
      land_record_verified: true,
      land_record_number: 'RTC-2026-UJ-902',
      bank_verified: true,
      bank_name: 'Karnataka Bank (Belthangady)',
    },
    farmer_notes: 'Insurance coverage requested for monsoon fruit rot loss.',
    subsidy_amount: '90% Premium Subsidy by Govt',
  },
  {
    id: 'app-003',
    application_number: 'KP-2026-00126',
    scheme_id: 'scheme-drip-irrigation',
    scheme_title: 'Pradhan Mantri Krishi Sinchayee Yojana (Drip Subsidy)',
    scheme_title_kn: 'ಸೂಕ್ಷ್ಮ ಹನಿ ನೀರಾವರಿ ಸಹಾಯಧನ ಯೋಜನೆ',
    scheme_category: 'Subsidy',
    farmer_id: 'farmer-ravi-003',
    farmer_name: 'Ravi Kumar',
    farmer_mobile: '+91 97401 55443',
    village: 'Mudigere (ಮೂಡಿಗೆರೆ)',
    district: 'Chikkamagaluru',
    crop: 'Cardamom & Pepper',
    crop_kn: 'ಏಲಕ್ಕಿ ಮತ್ತು ಕಾಳುಮೆಣಸು',
    land_holding_acres: '4.2 Acres',
    submitted_date: '25 Sept 2026, 04:45 PM',
    status: 'APPROVED',
    eligibility_checklist: {
      land_requirement: true,
      farmer_category: true,
      mandatory_docs: true,
    },
    documents: {
      aadhaar_verified: true,
      aadhaar_number: 'XXXX-XXXX-5544',
      land_record_verified: true,
      land_record_number: 'RTC-2026-MUD-412',
      bank_verified: true,
      bank_name: 'SBI (Mudigere Branch)',
    },
    farmer_notes: 'Requesting 75% subsidy for 4 acres drip irrigation network.',
    officer_notes: 'Site inspected by Assistant Horticultural Officer. Subsidy approved.',
    subsidy_amount: '₹45,000 Direct Equipment Grant',
  },
  {
    id: 'app-004',
    application_number: 'KP-2026-00127',
    scheme_id: 'scheme-seed-subsidy',
    scheme_title: 'Certified Certified Seed & Fertilizer Subsidy',
    scheme_title_kn: 'ಪ್ರಮಾಣೀಕೃತ ಭತ್ತದ ಬಿತ್ತನೆ ಬೀಜ ಸಹಾಯಧನ',
    scheme_category: 'Input Support',
    farmer_id: 'farmer-devendra-004',
    farmer_name: 'Devendra Gowda',
    farmer_mobile: '+91 99008 33221',
    village: 'Belthangady (ಬೆಳ್ತಂಗಡಿ)',
    district: 'Dakshina Kannada',
    crop: 'Paddy',
    crop_kn: 'ಭತ್ತ',
    land_holding_acres: '1.8 Acres',
    submitted_date: '26 Sept 2026, 09:10 AM',
    status: 'PENDING',
    eligibility_checklist: {
      land_requirement: true,
      farmer_category: true,
      mandatory_docs: false,
    },
    documents: {
      aadhaar_verified: true,
      aadhaar_number: 'XXXX-XXXX-3322',
      land_record_verified: false,
      land_record_number: 'Pending Upload',
      bank_verified: true,
      bank_name: 'Syndicate/Canara Bank',
    },
    farmer_notes: 'Applying for certified high-yield paddy seed distribution.',
    subsidy_amount: '50% Concession on 50 kg Seeds',
  },
];

export const INITIAL_GOVT_SCHEMES: GovernmentSchemeStatItem[] = [
  {
    id: 'scheme-pm-kisan',
    title: 'PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)',
    title_kn: 'ಪ್ರಧಾನಮಂತ್ರಿ ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ (ಪಿಎಂ-ಕಿಸಾನ್)',
    category: 'Farmer Support',
    department: 'Ministry of Agriculture & Farmers Welfare, Govt of India',
    benefits: '₹6,000 per year paid in three equal installments directly into bank accounts.',
    benefits_kn: 'ವರ್ಷಕ್ಕೆ ₹6,000 ನೇರ ನಗದು ವರ್ಗಾವಣೆ (ಡಿಬಿಟಿ) 3 ಸಮಾನ ಕಂತುಗಳಲ್ಲಿ.',
    eligibility: 'All landholding farmer families having cultivable land in their names.',
    eligibility_kn: 'ಸ್ವಂತ ಸಾಗುವಳಿ ಜಮೀನು ಹೊಂದಿರುವ ಸಣ್ಣ ಮತ್ತು ಅತಿ ಸಣ್ಣ ರೈತ ಕುಟುಂಬಗಳು.',
    required_docs: ['Aadhaar Card', 'Land Pahani (RTC)', 'Bank Passbook / IFSC'],
    total_applications: 128,
    approved: 96,
    pending: 22,
    rejected: 10,
    reach_percentage: 75,
  },
  {
    id: 'scheme-crop-insurance',
    title: 'Karnataka Raitha Siri Crop Insurance',
    title_kn: 'ಕರ್ನಾಟಕ ರೈತ ಸಿರಿ ಬೆಳೆ ವಿಮೆ ಯೋಜನೆ',
    category: 'Insurance',
    department: 'Department of Agriculture, Govt of Karnataka',
    benefits: 'Comprehensive financial cover against crop yield loss caused by natural calamities, monsoon failure, or pests.',
    benefits_kn: 'ಅತಿವೃಷ್ಟಿ, ಅನಾವೃಷ್ಟಿ ಹಾಗೂ ರೋಗಬಾಧೆಯಿಂದಾಗುವ ಬೆಳೆ ನಷ್ಟಕ್ಕೆ ಪೂರ್ಣ ಪರಿಹಾರ.',
    eligibility: 'Farmers cultivating notified horticultural and agricultural crops in Karnataka.',
    eligibility_kn: 'ಅಧಿಸೂಚಿತ ಬೆಳೆ ಬೆಳೆಯುವ ಎಲ್ಲಾ ಕರ್ನಾಟಕದ ನೋಂದಾಯಿತ ರೈತರು.',
    required_docs: ['Land RTC', 'Crop Sowing Certificate (ಬೆಳೆ ದೃಢೀಕರಣ)', 'Bank Account Details'],
    total_applications: 84,
    approved: 62,
    pending: 14,
    rejected: 8,
    reach_percentage: 68,
  },
  {
    id: 'scheme-drip-irrigation',
    title: 'Micro Irrigation Subsidy (PMKSY - Drip & Sprinkler)',
    title_kn: 'ಸೂಕ್ಷ್ಮ ಹನಿ ನೀರಾವರಿ ಸಹಾಯಧನ ಯೋಜನೆ',
    category: 'Subsidy',
    department: 'Department of Horticulture, Govt of Karnataka',
    benefits: 'Up to 90% subsidy for SC/ST farmers and up to 75% subsidy for general category farmers for drip kits.',
    benefits_kn: 'ಸಾಮಾನ್ಯ ರೈತರಿಗೆ 75% ಮತ್ತು ಎಸ್‌ಸಿ/ಎಸ್‌ಟಿ ರೈತರಿಗೆ 90% ಹನಿ ನೀರಾವರಿ ಸಬ್ಸಿಡಿ.',
    eligibility: 'Farmers with verified water source and agricultural land holding.',
    eligibility_kn: 'ನೀರಾವರಿ ಮೂಲ ಹೊಂದಿರುವ ಎಲ್ಲಾ ತೋಟಗಾರಿಕಾ ಬೆಳೆಗಾರರು.',
    required_docs: ['RTC Pahani', 'Water/Electricity Certificate', 'Aadhaar Card'],
    total_applications: 65,
    approved: 48,
    pending: 12,
    rejected: 5,
    reach_percentage: 60,
  },
  {
    id: 'scheme-seed-subsidy',
    title: 'Certified Quality Seed Distribution Scheme',
    title_kn: 'ಪ್ರಮಾಣೀಕೃತ ಬಿತ್ತನೆ ಬೀಜ ವಿತರಣಾ ಯೋಜನೆ',
    category: 'Input Support',
    department: 'Karnataka State Seeds Corporation / Raitha Samparka Kendra',
    benefits: '50% subsidized rates on certified high-yielding paddy, pulse, and oilseed varieties.',
    benefits_kn: 'ರೈತ ಸಂಪರ್ಕ ಕೇಂದ್ರಗಳ ಮೂಲಕ ರಿಯಾಯಿತಿ ದರದಲ್ಲಿ ಬಿತ್ತನೆ ಬೀಜ ವಿತರಣೆ.',
    eligibility: 'Local resident farmers enrolled in Karnataka Raitha Suraksha.',
    eligibility_kn: 'ಸ್ಥಳೀಯ ರೈತ ಸಂಪರ್ಕ ಕೇಂದ್ರ ವ್ಯಾಪ್ತಿಯ ಸಣ್ಣ ಹಿಡುವಳಿದಾರರು.',
    required_docs: ['Aadhaar Card', 'Farmer ID (FID / FRUITS)'],
    total_applications: 42,
    approved: 35,
    pending: 5,
    rejected: 2,
    reach_percentage: 82,
  },
];

export const INITIAL_REGIONAL_INSIGHTS: RegionalCropReportInsight[] = [
  {
    crop_name: 'Arecanut',
    crop_name_kn: 'ಅಡಿಕೆ',
    report_count: 42,
    verified_disease_count: 38,
    risk_level: 'HIGH',
    dominant_disease: 'Koleroga / Fruit Rot (Phytophthora)',
    dominant_disease_kn: 'ಕೊಳೆರೋಗ (ಮಹಾಳಿ)',
  },
  {
    crop_name: 'Paddy',
    crop_name_kn: 'ಭತ್ತ',
    report_count: 28,
    verified_disease_count: 21,
    risk_level: 'MODERATE',
    dominant_disease: 'Leaf Blast (Magnaporthe oryzae)',
    dominant_disease_kn: 'ಎಲೆ ಬ್ಲಾಸ್ಟ್ (ಬೆಂಕಿ ರೋಗ)',
  },
  {
    crop_name: 'Coconut',
    crop_name_kn: 'ತೆಂಗು',
    report_count: 19,
    verified_disease_count: 18,
    risk_level: 'NORMAL',
    dominant_disease: 'Healthy / Minor Rugose Spiraling Whitefly',
    dominant_disease_kn: 'ಸಾಮಾನ್ಯ / ಬಿಳಿ ನೊಣ ನಿಯಂತ್ರಣದಲ್ಲಿದೆ',
  },
  {
    crop_name: 'Black Pepper',
    crop_name_kn: 'ಕಾಳುಮೆಣಸು',
    report_count: 14,
    verified_disease_count: 12,
    risk_level: 'MODERATE',
    dominant_disease: 'Quick Wilt (Foot Rot)',
    dominant_disease_kn: 'ಶೀಘ್ರ ಸೊರಗು ರೋಗ',
  },
];

export const INITIAL_WEATHER_RISKS: WeatherRiskAlert[] = [
  {
    district: 'Udupi District',
    district_kn: 'ಉಡುಪಿ ಜಿಲ್ಲೆ',
    weather_condition: 'Heavy Coastal Monsoon Downpour',
    risk_level: 'HIGH',
    advisory_message: 'High humidity (>90%) with continuous rain favors rapid arecanut fruit rot spread.',
  },
  {
    district: 'Dakshina Kannada',
    district_kn: 'ದಕ್ಷಿಣ ಕನ್ನಡ ಜಿಲ್ಲೆ',
    weather_condition: 'Moderate Rain with Gusty Winds',
    risk_level: 'MEDIUM',
    advisory_message: 'Ensure adequate drainage in low-lying paddy basins to prevent seedling submergence.',
  },
  {
    district: 'Kodagu District',
    district_kn: 'ಕೊಡಗು ಜಿಲ್ಲೆ',
    weather_condition: 'Heavy Rainfall in Hilly Terrain',
    risk_level: 'HIGH',
    advisory_message: 'High risk of quick wilt in black pepper vine root zones.',
  },
];

export const INITIAL_OFFICIAL_ALERTS: GovernmentOfficialAlert[] = [
  {
    id: 'alert-001',
    title: 'Pre-Monsoon Koleroga Containment Advisory',
    title_kn: 'ಮುಂಗಾರು ಪೂರ್ವ ಕೊಳೆರೋಗ ನಿಯಂತ್ರಣ ಮಾರ್ಗಸೂಚಿ',
    district: 'Dakshina Kannada & Udupi',
    affected_crops: 'Arecanut (ಅಡಿಕೆ)',
    message: 'ಕೃಷಿ ಇಲಾಖೆ ಸೂಚನೆ: ಮುಂಗಾರು ಮಳೆ ಆರಂಭಕ್ಕೂ ಮುನ್ನ ಅಡಿಕೆ ಗೊನೆಗಳಿಗೆ ಕಡ್ಡಾಯವಾಗಿ 1% ಬೋರ್ಡೋ ದ್ರಾವಣ ಸಿಂಪಡಿಸಿ.',
    published_at: '25 Sept 2026, 10:00 AM',
    published_by: 'Department of Agriculture, Belthangady Taluk',
    recipient_farmers_count: 420,
  },
  {
    id: 'alert-002',
    title: 'Subsidized Certified Paddy Seed Distribution',
    title_kn: 'ರಿಯಾಯಿತಿ ದರದ ಭತ್ತದ ಬೀಜ ವಿತರಣೆ ಪ್ರಕಟಣೆ',
    district: 'Belthangady Taluk',
    affected_crops: 'Paddy (ಭತ್ತ)',
    message: 'ಉಜಿರೆ ಹಾಗೂ ಬೆಳ್ತಂಗಡಿ ರೈತ ಸಂಪರ್ಕ ಕೇಂದ್ರಗಳಲ್ಲಿ ಪ್ರಮಾಣೀಕೃತ ಭತ್ತದ ಬೀಜ 50% ರಿಯಾಯಿತಿ ದರದಲ್ಲಿ ಲಭ್ಯವಿದೆ.',
    published_at: '24 Sept 2026, 03:30 PM',
    published_by: 'Agriculture Officer, Raitha Samparka Kendra',
    recipient_farmers_count: 380,
  },
];

export const INITIAL_FARMERS_ASSISTANCE: FarmerAssistanceProfile[] = [
  {
    id: 'farmer-mallikarjuna-001',
    name: 'Mallikarjuna G.',
    village: 'Ujire (ಉಜಿರೆ)',
    district: 'Dakshina Kannada',
    mobile: '+91 98765 43210',
    land_acres: '2.5 Acres',
    crops: [
      { name: 'Paddy', name_kn: 'ಭತ್ತ', icon: '🌾' },
      { name: 'Arecanut', name_kn: 'ಅಡಿಕೆ', icon: '🌴' },
    ],
    total_applications: 4,
    approved: 3,
    pending: 1,
  },
  {
    id: 'farmer-shankara-002',
    name: 'Shankara Bhat',
    village: 'Ujire (ಉಜಿರೆ)',
    district: 'Dakshina Kannada',
    mobile: '+91 94481 99887',
    land_acres: '3.0 Acres',
    crops: [
      { name: 'Arecanut', name_kn: 'ಅಡಿಕೆ', icon: '🌴' },
      { name: 'Black Pepper', name_kn: 'ಕಾಳುಮೆಣಸು', icon: '🌿' },
    ],
    total_applications: 2,
    approved: 1,
    pending: 1,
  },
  {
    id: 'farmer-ravi-003',
    name: 'Ravi Kumar',
    village: 'Mudigere (ಮೂಡಿಗೆರೆ)',
    district: 'Chikkamagaluru',
    mobile: '+91 97401 55443',
    land_acres: '4.2 Acres',
    crops: [
      { name: 'Cardamom', name_kn: 'ಏಲಕ್ಕಿ', icon: '🌱' },
      { name: 'Pepper', name_kn: 'ಕಾಳುಮೆಣಸು', icon: '🌿' },
    ],
    total_applications: 3,
    approved: 3,
    pending: 0,
  },
];

// In-memory state for live interaction during session
let inMemoryApplications: SchemeApplicationItem[] = [...INITIAL_GOVT_APPLICATIONS];
let inMemoryAlerts: GovernmentOfficialAlert[] = [...INITIAL_OFFICIAL_ALERTS];

export const fetchGovernmentStats = async (): Promise<GovernmentDashboardStats> => {
  const pending = inMemoryApplications.filter((a) => a.status === 'PENDING' || a.status === 'UNDER_REVIEW').length;
  const approved = inMemoryApplications.filter((a) => a.status === 'APPROVED').length;
  return {
    ...INITIAL_GOVT_STATS,
    pending_count: pending,
    approved_count: approved,
    applications_count: inMemoryApplications.length,
  };
};

export const fetchGovernmentApplications = async (
  status?: string,
  search?: string
): Promise<SchemeApplicationItem[]> => {
  let list = [...inMemoryApplications];
  if (status && status !== 'ALL') {
    list = list.filter((a) => a.status === status);
  }
  if (search && search.trim().length > 0) {
    const q = search.trim().toLowerCase();
    list = list.filter(
      (a) =>
        a.farmer_name.toLowerCase().includes(q) ||
        a.application_number.toLowerCase().includes(q) ||
        a.village.toLowerCase().includes(q) ||
        a.scheme_title.toLowerCase().includes(q)
    );
  }
  return list;
};

export const updateApplicationStatus = async (
  applicationId: string,
  newStatus: 'APPROVED' | 'REJECTED' | 'UNDER_REVIEW',
  officerNotes?: string
): Promise<SchemeApplicationItem | null> => {
  let updatedItem: SchemeApplicationItem | null = null;
  inMemoryApplications = inMemoryApplications.map((app) => {
    if (app.id === applicationId) {
      updatedItem = {
        ...app,
        status: newStatus,
        officer_notes: officerNotes || app.officer_notes,
      };
      return updatedItem;
    }
    return app;
  });
  return updatedItem;
};

export const fetchGovernmentSchemesStats = async (): Promise<GovernmentSchemeStatItem[]> => {
  return INITIAL_GOVT_SCHEMES;
};

export const fetchRegionalAgriculturalInsights = async (): Promise<RegionalCropReportInsight[]> => {
  return INITIAL_REGIONAL_INSIGHTS;
};

export const fetchRegionalWeatherRisks = async (): Promise<WeatherRiskAlert[]> => {
  return INITIAL_WEATHER_RISKS;
};

export const fetchGovernmentAlerts = async (): Promise<GovernmentOfficialAlert[]> => {
  return inMemoryAlerts;
};

export const publishGovernmentAlert = async (
  title: string,
  district: string,
  affectedCrops: string,
  message: string,
  officerName: string = 'Department of Agriculture Officer'
): Promise<GovernmentOfficialAlert> => {
  const newAlert: GovernmentOfficialAlert = {
    id: `alert-${Date.now()}`,
    title,
    title_kn: title,
    district,
    affected_crops: affectedCrops,
    message,
    published_at: 'Just now',
    published_by: officerName,
    recipient_farmers_count: 450,
  };
  inMemoryAlerts = [newAlert, ...inMemoryAlerts];
  return newAlert;
};

export const searchFarmersAssistance = async (query?: string): Promise<FarmerAssistanceProfile[]> => {
  if (!query || !query.trim()) return INITIAL_FARMERS_ASSISTANCE;
  const q = query.trim().toLowerCase();
  return INITIAL_FARMERS_ASSISTANCE.filter(
    (f) =>
      f.name.toLowerCase().includes(q) ||
      f.village.toLowerCase().includes(q) ||
      f.mobile.includes(q)
  );
};
