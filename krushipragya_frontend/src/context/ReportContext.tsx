import React, { createContext, useContext, useState } from 'react';
import { CropReport } from '../types';
import { SEED_REPORTS } from '../constants/seedData';

interface ReportContextType {
  reports: CropReport[];
  addReport: (report: CropReport) => void;
  getReportById: (id: string) => CropReport | undefined;
  escalateStatus: (reportId: string, forceStatus?: CropReport['status']) => void; // For hackathon demo escalation
  resetDemoData: () => void;
}

const ReportContext = createContext<ReportContextType>({
  reports: [],
  addReport: () => {},
  getReportById: () => undefined,
  escalateStatus: () => {},
  resetDemoData: () => {},
});

export const ReportProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [reports, setReports] = useState<CropReport[]>(SEED_REPORTS);

  const addReport = (newReport: CropReport) => {
    setReports((prev) => [newReport, ...prev]);
  };

  const getReportById = (id: string) => {
    return reports.find((r) => r.id === id);
  };

  // Demo Escalation Simulator: Unverified -> AI Analysed -> Corroborated -> Expert Verified
  const escalateStatus = (reportId: string, forceStatus?: CropReport['status']) => {
    setReports((prev) =>
      prev.map((rep) => {
        if (rep.id !== reportId) return rep;

        if (forceStatus) {
          return {
            ...rep,
            status: forceStatus,
            verifiedBy: forceStatus === 'expert_verified' ? 'Agriculture Officer, KVK Brahmavar' : rep.verifiedBy,
            verifiedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ', Today',
          };
        }

        if (rep.status === 'unverified') {
          return { ...rep, status: 'ai_analysed' };
        } else if (rep.status === 'ai_analysed') {
          return {
            ...rep,
            status: 'corroborated',
            evidenceFarmsCount: 3,
          };
        } else if (rep.status === 'corroborated') {
          return {
            ...rep,
            status: 'expert_verified',
            verifiedBy: 'Agriculture Officer, KVK Dakshina Kannada',
            verifiedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ', Today',
          };
        }
        return rep;
      })
    );
  };

  const resetDemoData = () => {
    setReports(SEED_REPORTS);
  };

  return (
    <ReportContext.Provider
      value={{
        reports,
        addReport,
        getReportById,
        escalateStatus,
        resetDemoData,
      }}
    >
      {children}
    </ReportContext.Provider>
  );
};

export const useReports = () => useContext(ReportContext);
