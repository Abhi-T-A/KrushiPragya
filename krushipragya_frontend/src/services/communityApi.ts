/**
 * Community API Client
 * Manages community observations, symptom corroboration, local alerts, and user contributions.
 * Adheres to Trust Ladder: UNVERIFIED -> AI_ANALYSED -> CORROBORATED -> EXPERT_VERIFIED.
 */

export interface CommunityDashboardStats {
  local_reports_count: number;
  my_reports_count: number;
  confirmed_count: number;
  alerts_count: number;
}

export interface LocalCropIssueReport {
  id: string;
  crop_code: string;
  crop_name: string;
  crop_name_kn: string;
  crop_icon: string;
  observed_issue: string;
  observed_issue_kn: string;
  village: string;
  distance_km: number;
  reporter_type: 'FARMER' | 'COMMUNITY_MEMBER';
  reporter_name: string;
  reported_at: string;
  similar_reports_count: number;
  status: 'UNVERIFIED' | 'AI_ANALYSED' | 'CORROBORATED' | 'EXPERT_VERIFIED';
  symptoms: string[];
  image_uri?: string;
  corroborations_count: number;
  corroborations: Array<{
    id: string;
    user_name: string;
    similarity: 'VERY_SIMILAR' | 'SOMEWHAT_SIMILAR' | 'DIFFERENT' | 'NOT_SURE';
    note?: string;
    created_at: string;
  }>;
}

export interface CommunityAlertItem {
  id: string;
  category: 'GOVERNMENT' | 'COMMUNITY' | 'WEATHER';
  category_label: string;
  title: string;
  title_kn: string;
  message: string;
  affected_crop?: string;
  village: string;
  timestamp: string;
  severity: 'HIGH' | 'MODERATE' | 'NORMAL';
}

export interface CommunityContributionItem {
  id: string;
  type: 'OBSERVATION' | 'CORROBORATION';
  title: string;
  title_kn: string;
  crop_name: string;
  crop_icon: string;
  location: string;
  timestamp: string;
  trust_status: 'UNVERIFIED' | 'CORROBORATED' | 'EXPERT_VERIFIED';
  expert_verdict?: string;
  helpfulness_count: number;
}

export const INITIAL_COMMUNITY_STATS: CommunityDashboardStats = {
  local_reports_count: 12,
  my_reports_count: 8,
  confirmed_count: 5,
  alerts_count: 3,
};

export const INITIAL_LOCAL_REPORTS: LocalCropIssueReport[] = [
  {
    id: 'comm-rep-001',
    crop_code: 'arecanut',
    crop_name: 'Arecanut',
    crop_name_kn: 'ಅಡಿಕೆ',
    crop_icon: '🌴',
    observed_issue: 'Koleroga-like symptoms (Fruit Rot)',
    observed_issue_kn: 'ಕೊಳೆರೋಗದಂತಹ ಲಕ್ಷಣಗಳು (ಮಹಾಳಿ)',
    village: 'Ujire (ಉಜಿರೆ)',
    distance_km: 2,
    reporter_type: 'FARMER',
    reporter_name: 'Mallikarjuna G. (Farmer)',
    reported_at: 'Today, 8:30 AM',
    similar_reports_count: 4,
    status: 'AI_ANALYSED',
    symptoms: ['Fruit rot', 'Nut dropping', 'Water soaking on nuts'],
    corroborations_count: 4,
    corroborations: [
      {
        id: 'c-1',
        user_name: 'Keshava Hegde (Ujire)',
        similarity: 'VERY_SIMILAR',
        note: 'Saw immature nuts dropping with water soaked spots in northern plot.',
        created_at: 'Today, 9:15 AM',
      },
      {
        id: 'c-2',
        user_name: 'Subramanya Bhat (Belthangady)',
        similarity: 'SOMEWHAT_SIMILAR',
        note: 'Rain continuous for 3 days, rot starting at calyx.',
        created_at: 'Today, 10:00 AM',
      },
    ],
  },
  {
    id: 'comm-rep-002',
    crop_code: 'paddy',
    crop_name: 'Paddy',
    crop_name_kn: 'ಭತ್ತ',
    crop_icon: '🌾',
    observed_issue: 'Possible Blast symptoms (Spindle-shaped lesions)',
    observed_issue_kn: 'ಬೆಂಕಿ ರೋಗದ (ಬ್ಲಾಸ್ಟ್) ಸಂಭವನೀಯ ಲಕ್ಷಣಗಳು',
    village: 'Bantwal (ಬಂಟ್ವಾಳ)',
    distance_km: 7,
    reporter_type: 'FARMER',
    reporter_name: 'Devendra Gowda (Farmer)',
    reported_at: 'Yesterday, 4:00 PM',
    similar_reports_count: 3,
    status: 'CORROBORATED',
    symptoms: ['Leaf yellowing', 'Spindle lesions', 'Ash gray center'],
    corroborations_count: 3,
    corroborations: [
      {
        id: 'c-3',
        user_name: 'Ananda Poojary (Bantwal)',
        similarity: 'VERY_SIMILAR',
        note: '3 adjacent paddy plots have same brownish spindle spots on leaves.',
        created_at: 'Yesterday, 5:30 PM',
      },
    ],
  },
  {
    id: 'comm-rep-003',
    crop_code: 'coconut',
    crop_name: 'Coconut',
    crop_name_kn: 'ತೆಂಗು',
    crop_icon: '🥥',
    observed_issue: 'Stem bleeding & yellowing fronds',
    observed_issue_kn: 'ಕಾಂಡದಲ್ಲಿ ರಸ ಸೋರುವಿಕೆ ಹಾಗೂ ಎಲೆ ಹಳದಿ',
    village: 'Kundapura (ಕುಂದಾಪುರ)',
    distance_km: 15,
    reporter_type: 'COMMUNITY_MEMBER',
    reporter_name: 'Suresh Acharya (Community Scout)',
    reported_at: '25 Sept 2026, 11:20 AM',
    similar_reports_count: 2,
    status: 'UNVERIFIED',
    symptoms: ['Stem issue', 'Leaf yellowing'],
    corroborations_count: 1,
    corroborations: [],
  },
  {
    id: 'comm-rep-004',
    crop_code: 'pepper',
    crop_name: 'Black Pepper',
    crop_name_kn: 'ಕಾಳುಮೆಣಸು',
    crop_icon: '🌶',
    observed_issue: 'Quick Wilt vine flaccidity (Foot rot)',
    observed_issue_kn: 'ಬಳ್ಳಿ ಸೊರಗುವಿಕೆ (ದ್ರುತ ಸೊರಗು ರೋಗ)',
    village: 'Puttur (ಪುತ್ತೂರು)',
    distance_km: 12,
    reporter_type: 'FARMER',
    reporter_name: 'Shankara Bhat (Farmer)',
    reported_at: '26 Sept 2026, 02:45 PM',
    similar_reports_count: 3,
    status: 'EXPERT_VERIFIED',
    symptoms: ['Leaf yellowing', 'Foliar flaccidity', 'Stem issue'],
    corroborations_count: 4,
    corroborations: [],
  },
];

export const INITIAL_COMMUNITY_ALERTS: CommunityAlertItem[] = [
  {
    id: 'alert-c1',
    category: 'COMMUNITY',
    category_label: '👥 Community Observation',
    title: 'Arecanut Koleroga Cluster Alert',
    title_kn: 'ಅಡಿಕೆ ಕೊಳೆರೋಗ ಸಮುದಾಯ ಎಚ್ಚರಿಕೆ',
    message: 'Multiple similar reports around Ujire cluster. 4 farmers observed identical rot symptoms. Expert verification pending.',
    affected_crop: 'Arecanut (ಅಡಿಕೆ)',
    village: 'Ujire Village',
    timestamp: '2 hours ago',
    severity: 'HIGH',
  },
  {
    id: 'alert-g1',
    category: 'GOVERNMENT',
    category_label: '🏛 Official Government Alert',
    title: 'Department of Agriculture Koleroga Directive',
    title_kn: 'ಕೃಷಿ ಇಲಾಖೆಯ ಅಧಿಕೃತ ಮುಂಗಾರು ಮಾರ್ಗಸೂಚಿ',
    message: 'Mandatory 1% Bordeaux mixture spray advised for all arecanut bunches before continuous monsoon rain.',
    affected_crop: 'Arecanut & Paddy',
    village: 'Belthangady Taluk',
    timestamp: 'Yesterday, 10:00 AM',
    severity: 'HIGH',
  },
  {
    id: 'alert-w1',
    category: 'WEATHER',
    category_label: '🌧 Weather Advisory',
    title: 'Heavy Coastal Downpour Expected in 48 Hours',
    title_kn: 'ಮುಂದಿನ 48 ಗಂಟೆಗಳಲ್ಲಿ ಭಾರಿ ಮಳೆ ಮುನ್ಸೂಚನೆ',
    message: 'Ensure free drainage trenches in low basins to prevent root waterlogging.',
    affected_crop: 'All Crops',
    village: 'Dakshina Kannada & Udupi',
    timestamp: 'Yesterday, 3:30 PM',
    severity: 'MODERATE',
  },
];

export const INITIAL_COMMUNITY_CONTRIBUTIONS: CommunityContributionItem[] = [
  {
    id: 'contrib-001',
    type: 'CORROBORATION',
    title: 'Arecanut Koleroga Symptom Corroboration',
    title_kn: 'ಅಡಿಕೆ ಕೊಳೆರೋಗ ಲಕ್ಷಣ ದೃಢೀಕರಣ',
    crop_name: 'Arecanut',
    crop_icon: '🌴',
    location: 'Ujire (ಉಜಿರೆ)',
    timestamp: '26 Sept 2026',
    trust_status: 'EXPERT_VERIFIED',
    expert_verdict: 'Verified by Taluk Agri Expert (Dr. Ramesh)',
    helpfulness_count: 14,
  },
  {
    id: 'contrib-002',
    type: 'OBSERVATION',
    title: 'Paddy Leaf Yellowing Initial Observation',
    title_kn: 'ಭತ್ತದ ಎಲೆ ಹಳದಿ ಪ್ರಾಥಮಿಕ ವೀಕ್ಷಣೆ',
    crop_name: 'Paddy',
    crop_icon: '🌾',
    location: 'Bantwal (ಬಂಟ್ವಾಳ)',
    timestamp: '25 Sept 2026',
    trust_status: 'CORROBORATED',
    expert_verdict: 'Under Expert Review queue',
    helpfulness_count: 5,
  },
  {
    id: 'contrib-003',
    type: 'CORROBORATION',
    title: 'Pepper Vine Flaccidity Corroboration',
    title_kn: 'ಕಾಳುಮೆಣಸು ಬಳ್ಳಿ ಸೊರಗು ದೃಢೀಕರಣ',
    crop_name: 'Black Pepper',
    crop_icon: '🌶',
    location: 'Puttur (ಪುತ್ತೂರು)',
    timestamp: '24 Sept 2026',
    trust_status: 'EXPERT_VERIFIED',
    expert_verdict: 'Confirmed as Quick Wilt / Phytophthora',
    helpfulness_count: 8,
  },
];

// In-Memory state for live interactive session
let inMemoryReports = [...INITIAL_LOCAL_REPORTS];
let inMemoryAlerts = [...INITIAL_COMMUNITY_ALERTS];
let inMemoryContributions = [...INITIAL_COMMUNITY_CONTRIBUTIONS];

export const fetchCommunityStats = async (): Promise<CommunityDashboardStats> => {
  return {
    local_reports_count: inMemoryReports.length,
    my_reports_count: inMemoryContributions.filter((c) => c.type === 'OBSERVATION').length + 5,
    confirmed_count: inMemoryReports.filter((r) => r.status === 'EXPERT_VERIFIED' || r.status === 'CORROBORATED').length,
    alerts_count: inMemoryAlerts.length,
  };
};

export const fetchLocalReports = async (cropFilter?: string, query?: string): Promise<LocalCropIssueReport[]> => {
  let list = [...inMemoryReports];
  if (cropFilter && cropFilter !== 'ALL') {
    list = list.filter((r) => r.crop_code === cropFilter || r.crop_name.toLowerCase().includes(cropFilter.toLowerCase()));
  }
  if (query && query.trim()) {
    const q = query.trim().toLowerCase();
    list = list.filter(
      (r) =>
        r.crop_name.toLowerCase().includes(q) ||
        r.observed_issue.toLowerCase().includes(q) ||
        r.village.toLowerCase().includes(q) ||
        r.reporter_name.toLowerCase().includes(q)
    );
  }
  return list;
};

export const fetchReportById = async (reportId: string): Promise<LocalCropIssueReport | null> => {
  const found = inMemoryReports.find((r) => r.id === reportId);
  return found || null;
};

export const submitCorroboration = async (
  reportId: string,
  response: 'SIMILAR' | 'DIFFERENT' | 'NOT_SURE',
  similarityLevel?: 'VERY_SIMILAR' | 'SOMEWHAT_SIMILAR',
  note?: string,
  userName: string = 'Community Member (Ujire)'
): Promise<LocalCropIssueReport | null> => {
  let updatedReport: LocalCropIssueReport | null = null;

  inMemoryReports = inMemoryReports.map((report) => {
    if (report.id === reportId) {
      const newCorroboration = {
        id: `corrob-${Date.now()}`,
        user_name: userName,
        similarity: response === 'SIMILAR' ? (similarityLevel || 'VERY_SIMILAR') : response,
        note: note || undefined,
        created_at: 'Just now',
      };

      const updatedCount = report.corroborations_count + (response === 'SIMILAR' ? 1 : 0);
      const newStatus =
        updatedCount >= 3 && report.status === 'AI_ANALYSED'
          ? 'CORROBORATED'
          : report.status;

      updatedReport = {
        ...report,
        similar_reports_count: report.similar_reports_count + (response === 'SIMILAR' ? 1 : 0),
        corroborations_count: updatedCount,
        status: newStatus,
        corroborations: [newCorroboration, ...report.corroborations],
      };
      return updatedReport;
    }
    return report;
  });

  // Add to my contributions
  const targetReport = inMemoryReports.find((r) => r.id === reportId);
  if (targetReport) {
    const newContrib: CommunityContributionItem = {
      id: `contrib-${Date.now()}`,
      type: 'CORROBORATION',
      title: `${targetReport.crop_name} ${response === 'SIMILAR' ? 'Similar Symptoms Corroborated' : 'Field Note'}`,
      title_kn: `${targetReport.crop_name_kn} ಲಕ್ಷಣ ದೃಢೀಕರಣ`,
      crop_name: targetReport.crop_name,
      crop_icon: targetReport.crop_icon,
      location: targetReport.village,
      timestamp: 'Just now',
      trust_status: targetReport.status === 'EXPERT_VERIFIED' ? 'EXPERT_VERIFIED' : 'CORROBORATED',
      expert_verdict: 'Forwarded to Taluk Agriculture Expert review queue',
      helpfulness_count: 1,
    };
    inMemoryContributions = [newContrib, ...inMemoryContributions];
  }

  return updatedReport;
};

export const submitCommunityObservation = async (payload: {
  crop_code: string;
  crop_name: string;
  crop_name_kn: string;
  crop_icon: string;
  symptoms: string[];
  location: string;
  description: string;
  reporter_name?: string;
}): Promise<LocalCropIssueReport> => {
  const newReport: LocalCropIssueReport = {
    id: `comm-rep-${Date.now()}`,
    crop_code: payload.crop_code,
    crop_name: payload.crop_name,
    crop_name_kn: payload.crop_name_kn,
    crop_icon: payload.crop_icon,
    observed_issue: payload.symptoms.join(', ') || 'Local agricultural observation',
    observed_issue_kn: 'ಗ್ರಾಮ ಮಟ್ಟದ ವೀಕ್ಷಣೆ',
    village: payload.location || 'Ujire Village',
    distance_km: 1,
    reporter_type: 'COMMUNITY_MEMBER',
    reporter_name: payload.reporter_name || 'Community Scout (Ujire)',
    reported_at: 'Just now',
    similar_reports_count: 1,
    status: 'UNVERIFIED', // Strictly UNVERIFIED initially as per Trust Ladder
    symptoms: payload.symptoms,
    corroborations_count: 0,
    corroborations: [],
  };

  inMemoryReports = [newReport, ...inMemoryReports];

  // Add to my contributions
  const newContrib: CommunityContributionItem = {
    id: `contrib-${Date.now()}`,
    type: 'OBSERVATION',
    title: `${payload.crop_name} Local Observation`,
    title_kn: `${payload.crop_name_kn} ಸ್ಥಳೀಯ ವೀಕ್ಷಣೆ`,
    crop_name: payload.crop_name,
    crop_icon: payload.crop_icon,
    location: payload.location,
    timestamp: 'Just now',
    trust_status: 'UNVERIFIED',
    expert_verdict: 'Submitted observation • Ready for peer corroboration',
    helpfulness_count: 0,
  };
  inMemoryContributions = [newContrib, ...inMemoryContributions];

  return newReport;
};

export const fetchCommunityAlerts = async (): Promise<CommunityAlertItem[]> => {
  return inMemoryAlerts;
};

export const fetchMyContributions = async (): Promise<CommunityContributionItem[]> => {
  return inMemoryContributions;
};
