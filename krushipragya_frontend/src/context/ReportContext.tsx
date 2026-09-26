import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { CropReport } from '../types';
import {
  fetchFarmerRecentReports,
  fetchFarmerRegisteredCrops,
  BackendCropReportItem,
  BackendFarmerCropItem,
} from '../services/cropHealthApi';
import { useAuth } from './AuthContext';

interface ReportContextType {
  reports: CropReport[];
  isLoadingReports: boolean;
  addReport: (report: CropReport) => void;
  getReportById: (id: string) => CropReport | undefined;
  refreshReports: () => Promise<void>;
  escalateStatus: (reportId: string, forceStatus?: CropReport['status']) => void;
  resetDemoData: () => void;
}

const ReportContext = createContext<ReportContextType>({
  reports: [],
  isLoadingReports: false,
  addReport: () => {},
  getReportById: () => undefined,
  refreshReports: async () => {},
  escalateStatus: () => {},
  resetDemoData: () => {},
});

const CROP_LABELS: Record<string, { kn: string; en: string }> = {
  arecanut: { kn: 'ಅಡಿಕೆ', en: 'Arecanut' },
  paddy: { kn: 'ಭತ್ತ', en: 'Paddy' },
  coconut: { kn: 'ತೆಂಗು', en: 'Coconut' },
  black_pepper: { kn: 'ಕಾಳುಮೆಣಸು', en: 'Black Pepper' },
  pepper: { kn: 'ಕಾಳುಮೆಣಸು', en: 'Black Pepper' },
  cardamom: { kn: 'ಏಲಕ್ಕಿ', en: 'Cardamom' },
  turmeric: { kn: 'ಅರಿಶಿನ', en: 'Turmeric' },
  ginger: { kn: 'ಶುಂಠಿ', en: 'Ginger' },
};

const KANNADA_TO_CODE: Record<string, string> = {
  'ಅಡಿಕೆ': 'arecanut',
  'ಭತ್ತ': 'paddy',
  'ತೆಂಗು': 'coconut',
  'ಕಾಳುಮೆಣಸು': 'black_pepper',
  'ಏಲಕ್ಕಿ': 'cardamom',
  'ಅರಿಶಿನ': 'turmeric',
  'ಶುಂಠಿ': 'ginger',
};

const mapBackendToCropReport = (
  item: BackendCropReportItem,
  farmerCropMap?: Map<string, { code: string; name_kn: string; name_en: string }>
): CropReport => {
  // 1. Resolve registered crop directly from backend data (matching farmer_crop_id)
  const registeredCrop = item.farmer_crop_id ? farmerCropMap?.get(item.farmer_crop_id) : undefined;

  // 2. Embedded crop if backend ever provides it
  const embeddedCrop = item.farmer_crop?.crop;

  // 3. Or from diagnoses if available
  const latestDiag = item.diagnoses && item.diagnoses.length > 0 ? item.diagnoses[0] : null;
  const diagCrop = (item as any).crop || latestDiag?.crop;

  // Authoritative crop code
  let rawCode = (
    registeredCrop?.code ||
    embeddedCrop?.code ||
    diagCrop ||
    ''
  ).toLowerCase().trim();

  if (KANNADA_TO_CODE[rawCode]) {
    rawCode = KANNADA_TO_CODE[rawCode];
  } else if (rawCode === 'pepper') {
    rawCode = 'black_pepper';
  }

  const cropCode = rawCode || 'arecanut';
  const fallback = CROP_LABELS[cropCode];

  // If backend already provides Kannada/English crop names, use those directly!
  const cropNameKn =
    registeredCrop?.name_kn ||
    embeddedCrop?.name_kn ||
    fallback?.kn ||
    (cropCode ? cropCode : 'ಬೆಳೆ');

  const cropNameEn =
    registeredCrop?.name_en ||
    embeddedCrop?.name_en ||
    fallback?.en ||
    (cropCode ? (cropCode.charAt(0).toUpperCase() + cropCode.slice(1)) : 'Crop');

  const dateObj = new Date(item.created_at);
  const formattedDate = !isNaN(dateObj.getTime())
    ? `${dateObj.toLocaleDateString('kn-IN', { month: 'short', day: 'numeric' })}, ${dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
    : 'ಇತ್ತೀಚೆಗೆ';

  return {
    id: item.id,
    backendReportId: item.id,
    farmerCropId: item.farmer_crop_id,
    crop: cropCode,
    cropNameKn,
    cropNameEn,
    photoUri: item.image_storage_path ? `https://offmpvifgmzvclrvzweq.supabase.co/storage/v1/object/public/crop-report-images/${item.image_storage_path}` : undefined,
    symptoms: item.notes || '',
    predictedDisease: latestDiag ? latestDiag.predicted_class : 'ಪರಿಶೀಲನೆ ಬಾಕಿಯಿದೆ',
    predictedDiseaseKn: latestDiag ? latestDiag.predicted_class : 'ಪರಿಶೀಲನೆ ಬಾಕಿಯಿದೆ',
    confidence: latestDiag ? Number(latestDiag.confidence) : 0,
    status: (item.status?.toLowerCase() as CropReport['status']) || 'unverified',
    villageId: 'v2',
    villageName: 'Ujire',
    reporterRole: 'farmer',
    createdAt: formattedDate,
    evidenceFarmsCount: 1,
  };
};

export const ReportProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [reports, setReports] = useState<CropReport[]>([]);
  const [isLoadingReports, setIsLoadingReports] = useState(false);

  const loadReportsFromBackend = useCallback(async () => {
    const farmerId = user?.id || '11111111-1111-4111-8111-111111111111';
    const phone = user?.phone || '9876543210';
    setIsLoadingReports(true);
    try {
      const [reportsData, registeredCrops] = await Promise.all([
        fetchFarmerRecentReports(farmerId, phone),
        fetchFarmerRegisteredCrops(farmerId, phone).catch(() => [] as BackendFarmerCropItem[]),
      ]);

      const farmerCropMap = new Map<string, { code: string; name_kn: string; name_en: string }>();
      if (Array.isArray(registeredCrops)) {
        for (const fc of registeredCrops) {
          if (fc && fc.id && fc.crop) {
            farmerCropMap.set(fc.id, {
              code: fc.crop.code,
              name_kn: fc.crop.name_kn,
              name_en: fc.crop.name_en,
            });
          }
        }
      }

      if (Array.isArray(reportsData)) {
        const mapped = reportsData.map((item) => mapBackendToCropReport(item, farmerCropMap));
        setReports(mapped);
      }
    } catch (e) {
      console.log('Error fetching backend crop reports:', e);
    } finally {
      setIsLoadingReports(false);
    }
  }, [user?.id, user?.phone]);

  useEffect(() => {
    loadReportsFromBackend();
  }, [loadReportsFromBackend]);

  const addReport = (newReport: CropReport) => {
    setReports((prev) => [newReport, ...prev.filter((r) => r.id !== newReport.id)]);
  };

  const getReportById = (id: string) => {
    return reports.find((r) => r.id === id || r.backendReportId === id);
  };

  const escalateStatus = (reportId: string, forceStatus?: CropReport['status']) => {
    setReports((prev) =>
      prev.map((rep) => {
        if (rep.id !== reportId && rep.backendReportId !== reportId) return rep;
        const newStatus = forceStatus || (rep.status === 'unverified' ? 'ai_analysed' : rep.status === 'ai_analysed' ? 'corroborated' : 'expert_verified');
        return {
          ...rep,
          status: newStatus,
          verifiedBy: newStatus === 'expert_verified' ? 'ಕೃಷಿ ತಜ್ಞರು (KVK Scientist)' : rep.verifiedBy,
          verifiedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ', ಇಂದು',
        };
      })
    );
  };

  const resetDemoData = () => {
    loadReportsFromBackend();
  };

  return (
    <ReportContext.Provider
      value={{
        reports,
        isLoadingReports,
        addReport,
        getReportById,
        refreshReports: loadReportsFromBackend,
        escalateStatus,
        resetDemoData,
      }}
    >
      {children}
    </ReportContext.Provider>
  );
};

export const useReports = () => useContext(ReportContext);
