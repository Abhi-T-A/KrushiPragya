export interface VillageNeighbor {
  id: string;
  name: string;
  phone?: string;
  villageId: string;
  villageName: string;
  role: 'farmer' | 'lead_farmer' | 'village_node';
  crops: {
    cropKey: string;
    emoji: string;
    nameKn: string;
    nameEn: string;
    acres: number;
    healthStatus: 'healthy' | 'issue_reported' | 'monitoring';
    latestIssueKn?: string;
    latestIssueEn?: string;
    reportedDaysAgo?: string;
  }[];
}

export const SEED_VILLAGE_NEIGHBORS: Record<string, VillageNeighbor[]> = {
  v2: [
    {
      id: 'fn_1',
      name: 'ರಮೇಶ್ ಹೆಗ್ಡೆ (Ramesh Hegde)',
      villageId: 'v2',
      villageName: 'Ujire',
      role: 'lead_farmer',
      crops: [
        {
          cropKey: 'arecanut',
          emoji: '🌴',
          nameKn: 'ಅಡಿಕೆ',
          nameEn: 'Arecanut',
          acres: 3.5,
          healthStatus: 'healthy',
        },
        {
          cropKey: 'cardamom',
          emoji: '🌿',
          nameKn: 'ಏಲಕ್ಕಿ',
          nameEn: 'Cardamom',
          acres: 1.0,
          healthStatus: 'healthy',
        },
      ],
    },
    {
      id: 'fn_2',
      name: 'ಮಂಜುನಾಥ ಗೌಡ (Manjunath Gowda)',
      villageId: 'v2',
      villageName: 'Ujire',
      role: 'farmer',
      crops: [
        {
          cropKey: 'arecanut',
          emoji: '🌴',
          nameKn: 'ಅಡಿಕೆ',
          nameEn: 'Arecanut',
          acres: 2.0,
          healthStatus: 'issue_reported',
          latestIssueKn: 'ಕೊಳೆ ರೋಗ (ಮಹಾಳಿ)',
          latestIssueEn: 'Koleroga (Fruit Rot)',
          reportedDaysAgo: '2 ದಿನಗಳ ಹಿಂದೆ (2 days ago)',
        },
      ],
    },
    {
      id: 'fn_3',
      name: 'ಸುರೇಶ್ ಭಟ್ (Suresh Bhat)',
      villageId: 'v2',
      villageName: 'Ujire',
      role: 'farmer',
      crops: [
        {
          cropKey: 'paddy',
          emoji: '🌾',
          nameKn: 'ಭತ್ತ',
          nameEn: 'Paddy',
          acres: 1.5,
          healthStatus: 'monitoring',
          latestIssueKn: 'ಬ್ಲಾಸ್ಟ್ ರೋಗ ಲಕ್ಷಣ',
          latestIssueEn: 'Blast symptoms',
          reportedDaysAgo: 'ನಿನ್ನೆ (Yesterday)',
        },
        {
          cropKey: 'coconut',
          emoji: '🥥',
          nameKn: 'ತೆಂಗು',
          nameEn: 'Coconut',
          acres: 1.0,
          healthStatus: 'healthy',
        },
      ],
    },
    {
      id: 'fn_4',
      name: 'ಗಣೇಶ್ ಪೂಜಾರಿ (Ganesh Poojary)',
      villageId: 'v2',
      villageName: 'Ujire',
      role: 'farmer',
      crops: [
        {
          cropKey: 'arecanut',
          emoji: '🌴',
          nameKn: 'ಅಡಿಕೆ',
          nameEn: 'Arecanut',
          acres: 1.8,
          healthStatus: 'healthy',
        },
      ],
    },
  ],
  v1: [
    {
      id: 'fn_10',
      name: 'ಪ್ರವೀಣ್ ಕುಮಾರ್ (Praveen Kumar)',
      villageId: 'v1',
      villageName: 'Thirthahalli',
      role: 'lead_farmer',
      crops: [
        {
          cropKey: 'paddy',
          emoji: '🌾',
          nameKn: 'ಭತ್ತ',
          nameEn: 'Paddy',
          acres: 3.0,
          healthStatus: 'issue_reported',
          latestIssueKn: 'ಬ್ಲಾಸ್ಟ್ ರೋಗ',
          latestIssueEn: 'Paddy Blast',
          reportedDaysAgo: '3 ದಿನಗಳ ಹಿಂದೆ',
        },
      ],
    },
  ],
};
