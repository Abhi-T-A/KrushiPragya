import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { CropReport } from '../types';
import { fetchFarmerRecentReports, BackendCropReportItem } from '../services/cropHealthApi';
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

const mapBackendToCropReport = (item: BackendCropReportItem): CropReport => {
  const cropCode = item.farmer_crop?.crop?.code?.toLowerCase() || 'arecanut';
  const labels = CROP_LABELS[cropCode] || { kn: item.farmer_crop?.crop?.name_kn || 'ಬೆಳೆ', en: item.farmer_crop?.crop?.name_en || 'Crop' };
  const latestDiag = item.diagnoses && item.diagnoses.length > 0 ? item.diagnoses[0] : null;

  const dateObj = new Date(item.created_at);
  const formattedDate = !isNaN(dateObj.getTime())
    ? `${dateObj.toLocaleDateString('kn-IN', { month: 'short', day: 'numeric' })}, ${dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
    : 'ಇತ್ತೀಚೆಗೆ';

  return {
    id: item.id,
    backendReportId: item.id,
    farmerCropId: item.farmer_crop_id,
    crop: cropCode,
    cropNameKn: labels.kn,
    cropNameEn: labels.en,
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
      const data = await fetchFarmerRecentReports(farmerId, phone);
      if (Array.isArray(data)) {
        const mapped = data.map(mapBackendToCropReport);
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
