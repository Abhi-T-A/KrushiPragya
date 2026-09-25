import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useLanguage } from '../../context/LanguageContext';
import { useReports } from '../../context/ReportContext';
import { Header } from '../../components/common/Header';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { StatusBadge } from '../../components/trust/StatusBadge';
import { ConfidenceBar } from '../../components/trust/ConfidenceBar';
import { VerificationLadder } from '../../components/trust/VerificationLadder';
import { ProvenanceDrawer } from '../../components/trust/ProvenanceDrawer';
import { PaymentModal, PaymentReceipt } from '../../components/common/PaymentModal';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import {
  ShieldCheck,
  Building2,
  Sparkles,
  RefreshCw,
  Send,
  Store,
  Landmark,
} from 'lucide-react-native';

export const AIResultScreen: React.FC<{ route: any; navigation: any }> = ({
  route,
  navigation,
}) => {
  const { reportId } = route.params;
  const { language } = useLanguage();
  const { getReportById, escalateStatus } = useReports();
  const [showProvenance, setShowProvenance] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [expertRequested, setExpertRequested] = useState(false);

  const report = getReportById(reportId);
  const isKn = language === 'kn';

  if (!report) {
    return (
      <View style={styles.container}>
        <Header title={isKn ? 'ವರದಿ ಸಿಗಲಿಲ್ಲ' : 'Report Not Found'} />
        <View style={styles.centerBox}>
          <Text style={styles.errorText}>
            {isKn ? 'ವರದಿಯ ವಿವರಗಳು ಲಭ್ಯವಿಲ್ಲ.' : 'Report details are not available.'}
          </Text>
          <Button
            title={isKn ? 'ಹಿಂದಕ್ಕೆ ಹೋಗಿ' : 'Go Back'}
            onPress={() => navigation.navigate('HomeTab')}
          />
        </View>
      </View>
    );
  }

  const handleRequestExpert = () => {
    setExpertRequested(true);
    escalateStatus(report.id, 'expert_verified');
    Alert.alert(
      isKn ? 'ತಜ್ಞರ ಪರಿಶೀಲನೆಗೆ ಕಳುಹಿಸಲಾಗಿದೆ 🔬' : 'Sent to Agri Expert Queue 🔬',
      isKn
        ? 'ಬ್ರಹ್ಮಾವರ ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರದ ವಿಜ್ಞಾನಿ ಡಾ. ರಮೇಶ್ ರವರ ಪರಿಶೀಲನಾ ಸರದಿಗೆ ವರದಿ ರವಾನಿಸಲಾಗಿದೆ.'
        : 'Report dispatched to Dr. Ramesh (KVK Agronomist) for official verification.'
    );
  };

  return (
    <View style={styles.container}>
      <Header
        title={isKn ? 'AI ರೋಗ ಪತ್ತೆ ಫಲಿತಾಂಶ' : 'AI Diagnosis Result'}
        showVillage={false}
      />

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Status Badge & Crop Name */}
        <View style={styles.statusRow}>
          <StatusBadge status={report.status} />
          <Text style={styles.cropBadge}>
            {isKn ? `${report.cropNameKn} (${report.cropNameEn})` : report.cropNameEn}
          </Text>
        </View>

        {/* Primary Diagnosis Card */}
        <Card variant="trust" style={styles.resultCard}>
          <Text style={styles.resultCardSubtitle}>
            {isKn ? 'ಪತ್ತೆಯಾದ ರೋಗ / ಸಮಸ್ಯೆ:' : 'Possible Condition Identified:'}
          </Text>
          <Text style={styles.diseaseNameKn}>
            {isKn ? report.predictedDiseaseKn : report.predictedDisease}
          </Text>
          <Text style={styles.diseaseNameEn}>
            {report.predictedDisease} {report.scientificName ? `(${report.scientificName})` : ''}
          </Text>

          {/* AI Confidence Bar */}
          <ConfidenceBar confidence={report.confidence} />
        </Card>

        {/* ICAR Recommended Remedy Card */}
        <Card variant="highlight" style={styles.remedyCard}>
          <View style={styles.remedyHeader}>
            <Sparkles size={18} color={Colors.primaryDark} />
            <Text style={styles.remedyTitle}>
              {isKn ? 'ವೈಜ್ಞಾನಿಕ ಕೃಷಿ ಚಿಕಿತ್ಸೆ (ICAR Protocol)' : 'Recommended Agronomic Action'}
            </Text>
          </View>
          <Text style={styles.remedyText}>
            {isKn ? report.remedyKn : (report.remedyEn || report.remedyKn)}
          </Text>

          {/* Explicit ICAR Attribution */}
          <View style={styles.sourceBox}>
            <Building2 size={14} color={Colors.textSecondary} />
            <Text style={styles.sourceText}>
              {isKn ? 'ಮೂಲ ಸಂಸ್ಥೆ' : 'Source'}: <Text style={{ fontWeight: '700' }}>{report.sourceInstitution || 'ICAR Research Institute'}</Text>
            </Text>
          </View>
        </Card>

        {/* 4-Stage Verification Ladder Widget */}
        <VerificationLadder
          status={report.status}
          evidenceFarmsCount={report.evidenceFarmsCount}
          verifiedBy={report.verifiedBy}
          verifiedAt={report.verifiedAt}
        />

        {/* Action 1: Request Agri Expert Sign-off */}
        {!expertRequested && report.status !== 'expert_verified' && (
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={() => setShowPaymentModal(true)}
            style={styles.expertBtn}
          >
            <Send size={16} color="#FFFFFF" />
            <Text style={styles.expertBtnText}>
              {isKn ? 'ಕೃಷಿ ತಜ್ಞರ ಧೃಢೀಕರಣಕ್ಕೆ ಕಳುಹಿಸಿ (Request Expert)' : 'Request Agri Expert Sign-off'}
            </Text>
          </TouchableOpacity>
        )}

        {/* Action 2: Multi-Role Bridge Buttons */}
        <View style={styles.bridgeRow}>
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={() => navigation.navigate('MarketTab')}
            style={[styles.bridgeBtn, { backgroundColor: '#FEF3C7', borderColor: '#FDE68A' }]}
          >
            <Store size={15} color="#D97706" />
            <Text style={[styles.bridgeBtnText, { color: '#B45309' }]}>
              {isKn ? 'ಮಾರುಕಟ್ಟೆಯಲ್ಲಿ ಮಾರಿ' : 'List on Market'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            activeOpacity={0.85}
            onPress={() => navigation.navigate('MarketTab', { initialTab: 'schemes' })}
            style={[styles.bridgeBtn, { backgroundColor: '#F3E8FF', borderColor: '#E9D5FF' }]}
          >
            <Landmark size={15} color="#9333EA" />
            <Text style={[styles.bridgeBtnText, { color: '#7E22CE' }]}>
              {isKn ? 'ಪರಿಹಾರಕ್ಕೆ ಅರ್ಜಿ ಹಾಕಿ' : 'Claim PMFBY Relief'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* CTA: View Full Provenance & Evidence */}
        <Button
          title={isKn ? 'ವೈಜ್ಞಾನಿಕ ಸಾಕ್ಷ್ಯ ವಿವರ ನೋಡಿ' : 'View Scientific Evidence & Provenance'}
          variant="outline"
          onPress={() => setShowProvenance(true)}
          icon={<ShieldCheck size={18} color={Colors.primary} />}
          style={{ marginTop: Spacing.sm }}
        />
      </ScrollView>

      {/* Provenance Drawer Modal */}
      {showProvenance && (
        <ProvenanceDrawer
          visible={showProvenance}
          onClose={() => setShowProvenance(false)}
          report={report}
        />
      )}

      {/* Payment Modal */}
      <PaymentModal
        visible={showPaymentModal}
        onClose={() => setShowPaymentModal(false)}
        titleKn="ಅಾವೞಿತ  c81ೱವಿಶ  ca4ರಿವೝಶ  cafವೝವ (Standard KVK Lab Test)"
        titleEn="Official KVK Diagnostic Lab Test"
        amount={120}
        serviceType="Lab Testing"
        beneficiaryName="ICAR - KVK Brahmavar Research Account"
        onSuccess={(rec: PaymentReceipt) => {
          handleRequestExpert();
        }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    padding: Spacing.md,
    paddingBottom: 40,
    gap: Spacing.sm,
  },
  centerBox: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.lg,
    gap: Spacing.md,
  },
  errorText: {
    fontSize: 14,
    color: '#64748B',
    textAlign: 'center',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  cropBadge: {
    fontSize: 13,
    fontWeight: '800',
    color: Colors.textPrimary,
    backgroundColor: Colors.surface,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  resultCard: {
    gap: 4,
  },
  resultCardSubtitle: {
    fontSize: 11,
    fontWeight: '700',
    color: '#64748B',
    textTransform: 'uppercase',
  },
  diseaseNameKn: {
    fontSize: 20,
    fontWeight: '800',
    color: '#DC2626',
    letterSpacing: -0.3,
  },
  diseaseNameEn: {
    fontSize: 13,
    fontWeight: '600',
    color: '#475569',
    marginBottom: 6,
  },
  remedyCard: {
    gap: 8,
  },
  remedyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  remedyTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: Colors.primaryDark,
  },
  remedyText: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.textPrimary,
    lineHeight: 19,
  },
  sourceBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderTopWidth: 1,
    borderTopColor: '#BFE7D7',
    paddingTop: 8,
    marginTop: 4,
  },
  sourceText: {
    fontSize: 11,
    color: Colors.textSecondary,
  },
  expertBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#2563EB',
    paddingVertical: 12,
    borderRadius: 10,
    marginTop: 4,
  },
  expertBtnText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  bridgeRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 4,
  },
  bridgeBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
  },
  bridgeBtnText: {
    fontSize: 12,
    fontWeight: '700',
  },
});