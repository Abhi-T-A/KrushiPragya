import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
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
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { ShieldCheck, ArrowRight, Building2, Sparkles, RefreshCw } from 'lucide-react-native';

export const AIResultScreen: React.FC<{ route: any; navigation: any }> = ({
  route,
  navigation,
}) => {
  const { reportId } = route.params;
  const { language } = useLanguage();
  const { getReportById, escalateStatus } = useReports();
  const [showProvenance, setShowProvenance] = useState(false);

  const report = getReportById(reportId);

  if (!report) {
    return (
      <View style={styles.container}>
        <Header title={language === 'kn' ? 'ವರದಿ ಸಿಗಲಿಲ್ಲ' : 'Report Not Found'} />
        <View style={styles.centerBox}>
          <Text style={styles.errorText}>
            {language === 'kn' ? 'ವರದಿ ಲಭ್ಯವಿಲ್ಲ.' : 'Report details are not available.'}
          </Text>
          <Button
            title={language === 'kn' ? 'ಹಿಂದೆ' : 'Go Back'}
            onPress={() => navigation.navigate('HomeTab')}
          />
        </View>
      </View>
    );
  }

  // Low confidence check
  if (report.confidence < 0.5) {
    return (
      <View style={styles.container}>
        <Header title={language === 'kn' ? 'AI ವಿಶ್ಲೇಷಣೆ' : 'AI Analysis'} />
        <View style={styles.errorCard}>
          <Text style={styles.lowConfidenceTitle}>
            {language === 'kn'
              ? 'ರೋಗವನ್ನು ಖಚಿತವಾಗಿ ಗುರುತಿಸಲಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಸ್ಪಷ್ಟವಾದ ಫೋಟೋ ತೆಗೆಯಿರಿ.'
              : 'Could not confidently identify the condition. Please take a clearer photo.'}
          </Text>
          <Button
            title={language === 'kn' ? 'ಮತ್ತೆ ಫೋಟೋ ತೆಗೆಯಿರಿ' : 'Retake Clear Photo'}
            onPress={() => navigation.navigate('CameraCapture', { crop: report.crop })}
          />
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Header
        title={language === 'kn' ? 'ವಿಶ್ಲೇಷಣೆ ಫಲಿತಾಂಶ' : 'Analysis Result'}
        showVillage={false}
      />

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Status Badge & Crop Name */}
        <View style={styles.statusRow}>
          <StatusBadge status={report.status} />
          <Text style={styles.cropBadge}>
            {language === 'kn' ? `${report.cropNameKn} (${report.cropNameEn})` : report.cropNameEn}
          </Text>
        </View>

        {/* Primary Diagnosis Card */}
        <Card variant="trust" style={styles.resultCard}>
          <Text style={styles.resultCardSubtitle}>
            {language === 'kn' ? 'ಸಾಧ್ಯವಿರುವ ಸಮಸ್ಯೆ (Possible Issue):' : 'Possible Condition Identified:'}
          </Text>
          <Text style={styles.diseaseNameKn}>
            {language === 'kn' ? report.predictedDiseaseKn : report.predictedDisease}
          </Text>
          <Text style={styles.diseaseNameEn}>
            {report.predictedDisease} {report.scientificName ? `(${report.scientificName})` : ''}
          </Text>

          {/* AI Confidence Bar with Preliminary Warning */}
          <ConfidenceBar confidence={report.confidence} />
        </Card>

        {/* Hardcoded ICAR Remedy Card */}
        <Card variant="highlight" style={styles.remedyCard}>
          <View style={styles.remedyHeader}>
            <Sparkles size={18} color={Colors.primaryDark} />
            <Text style={styles.remedyTitle}>
              {language === 'kn' ? 'ಶಿಫಾರಸು ಮಾಡಿದ ಕ್ರಮ (ಸಲಹೆ)' : 'Recommended Agronomic Action'}
            </Text>
          </View>
          <Text style={styles.remedyText}>
            {language === 'kn' ? report.remedyKn : (report.remedyEn || report.remedyKn)}
          </Text>

          {/* Explicit ICAR Attribution */}
          <View style={styles.sourceBox}>
            <Building2 size={14} color={Colors.textSecondary} />
            <Text style={styles.sourceText}>
              {language === 'kn' ? 'ಮೂಲ ಸಂಸ್ಥೆ' : 'Source'}: <Text style={{ fontWeight: '700' }}>{report.sourceInstitution}</Text>
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

        {/* CTA: View Full Provenance & Evidence */}
        <Button
          title={language === 'kn' ? 'ಸಾಕ್ಷ್ಯ ಮತ್ತು ವಿವರ ನೋಡಿ (View Provenance)' : 'View Evidence & Provenance'}
          variant="outline"
          onPress={() => setShowProvenance(true)}
          icon={<ShieldCheck size={18} color={Colors.primary} />}
        />

        {/* DEMO ESCALATION CONTROLLER */}
        <View style={styles.demoControllerBox}>
          <View style={styles.demoHeader}>
            <RefreshCw size={14} color={Colors.trustPurple} />
            <Text style={styles.demoTitle}>
              {language === 'kn' ? 'ಡೆಮೊ ಮೋಡ್ — ಪರಿಶೀಲನೆ ಪರೀಕ್ಷಿಸಿ' : 'Demo Mode — Verification Simulation'}
            </Text>
          </View>

          <Text style={styles.demoDesc}>
            {language === 'kn'
              ? 'ನ್ಯಾಯಾಧೀಶರ ಪ್ರಸ್ತುತಿಗಾಗಿ: 3 ತೋಟಗಳ ದೃಢೀಕರಣ ಮತ್ತು ತಜ್ಞರ ಪರಿಶೀಲನೆ ಹಂತಗಳನ್ನು ಪರೀಕ್ಷಿಸಿ.'
              : 'For Judge Presentation: Test community corroboration and expert verification stages.'}
          </Text>

          {report.status === 'ai_analysed' && (
            <Button
              title={language === 'kn' ? 'ಹಂತ 3: ಗ್ರಾಮ ದೃಢೀಕರಣ (3 Farms Signal)' : 'Stage 3: Corroborate (3 Farms)'}
              size="normal"
              onPress={() => escalateStatus(report.id)}
              style={styles.demoButton}
            />
          )}

          {report.status === 'corroborated' && (
            <Button
              title={language === 'kn' ? 'ಹಂತ 4: ಕೃಷಿ ಅಧಿಕಾರಿ ಪರಿಶೀಲನೆ (Expert Verify)' : 'Stage 4: Officer Verification (Sign-off)'}
              size="normal"
              onPress={() => escalateStatus(report.id)}
              style={styles.demoButton}
            />
          )}
        </View>

        <Button
          title={language === 'kn' ? 'ಮುಖಪುಟಕ್ಕೆ ಹಿಂತಿರುಗಿ (Done)' : 'Done (Back to Home)'}
          variant="secondary"
          onPress={() => navigation.navigate('HomeTab')}
          style={{ marginTop: Spacing.sm }}
        />
      </ScrollView>

      {/* Provenance Drawer Modal */}
      <ProvenanceDrawer
        visible={showProvenance}
        onClose={() => setShowProvenance(false)}
        report={report}
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
    padding: Spacing.lg,
    paddingBottom: Spacing.xxxl,
    gap: Spacing.md,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  cropBadge: {
    ...Typography.label,
    color: Colors.textSecondary,
    backgroundColor: Colors.surface,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  resultCard: {
    backgroundColor: Colors.surface,
  },
  resultCardSubtitle: {
    ...Typography.caption,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  diseaseNameKn: {
    ...Typography.display,
    color: Colors.alertHigh,
    marginTop: 2,
  },
  diseaseNameEn: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  remedyCard: {
    backgroundColor: Colors.primaryLight,
    borderColor: Colors.primary,
    borderWidth: 1.5,
  },
  remedyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: Spacing.xs,
  },
  remedyTitle: {
    ...Typography.title2,
    color: Colors.primaryDark,
    fontWeight: '800',
  },
  remedyText: {
    ...Typography.bodyLarge,
    color: Colors.textPrimary,
    lineHeight: 22,
    fontWeight: '600',
  },
  sourceBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: Spacing.md,
    paddingTop: Spacing.xs,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.08)',
  },
  sourceText: {
    ...Typography.caption,
    color: Colors.textSecondary,
  },
  demoControllerBox: {
    backgroundColor: Colors.trustPurpleLight,
    padding: Spacing.md,
    borderRadius: BorderRadius.lg,
    borderWidth: 1,
    borderColor: Colors.trustPurple,
    gap: Spacing.xs,
    marginTop: Spacing.sm,
  },
  demoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  demoTitle: {
    ...Typography.caption,
    color: Colors.trustPurple,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
  demoDesc: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  demoButton: {
    backgroundColor: Colors.trustPurple,
  },
  centerBox: {
    flex: 1,
    padding: Spacing.xl,
    alignItems: 'center',
    justifyContent: 'center',
  },
  errorText: {
    ...Typography.title2,
    color: Colors.alertHigh,
    marginBottom: Spacing.lg,
  },
  errorCard: {
    margin: Spacing.xl,
    padding: Spacing.xl,
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.xl,
    gap: Spacing.lg,
    alignItems: 'center',
  },
  lowConfidenceTitle: {
    ...Typography.title2,
    color: Colors.alertHigh,
    textAlign: 'center',
  },
});
