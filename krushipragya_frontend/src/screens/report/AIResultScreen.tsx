import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { useReports } from '../../context/ReportContext';
import { StatusBadge } from '../../components/trust/StatusBadge';
import { ConfidenceBar } from '../../components/trust/ConfidenceBar';
import { VerificationLadder } from '../../components/trust/VerificationLadder';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import {
  fetchCropReportTrustStatus,
  requestAgriExpertVerification,
  submitPeerCorroboration,
  VerificationStatusData,
} from '../../services/cropHealthApi';
import { DemoExpertPaymentModal } from '../../components/expert/DemoExpertPaymentModal';
import {
  ArrowLeft,
  ShieldCheck,
  Building2,
  Sparkles,
  AlertTriangle,
  Send,
  CheckCircle2,
  Users,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  Info,
  AlertCircle,
  RefreshCw,
} from 'lucide-react-native';

export const AIResultScreen: React.FC<{ route: any; navigation: any }> = ({
  route,
  navigation,
}) => {
  const { reportId } = route.params || {};
  const { language } = useLanguage();
  const { user } = useAuth();
  const { getReportById } = useReports();
  const isKn = language === 'kn';

  const report = getReportById(reportId);

  const [trustStatus, setTrustStatus] = useState<VerificationStatusData | null>(null);
  const [isRequestingExpert, setIsRequestingExpert] = useState(false);
  const [expertRequested, setExpertRequested] = useState(false);
  const [showDemoPaymentModal, setShowDemoPaymentModal] = useState(false);
  const [isSubmittingCorroboration, setIsSubmittingCorroboration] = useState(false);
  const [corroborationSubmitted, setCorroborationSubmitted] = useState<string | null>(null);

  const backendId = report?.backendReportId || report?.id;
  const currentFarmerId = user?.id || '11111111-1111-4111-8111-111111111111';
  const phone = user?.phone || '9876543210';

  // Check if current user is owner of report
  const isOwner = Boolean(report?.farmerId && report.farmerId === currentFarmerId) || (!report?.farmerId);

  const isIrrelevant = report?.reasonCode === 'IRRELEVANT_IMAGE';
  const isCropMismatch = report?.reasonCode === 'CROP_MISMATCH';
  const isUncertainImage = report?.reasonCode === 'UNCERTAIN_IMAGE' || (report as any)?.state === 'UNCERTAIN_IMAGE' || (report as any)?.status === 'uncertain';
  const isValidationRejected = isIrrelevant || isCropMismatch || isUncertainImage;

  const loadTrustStatus = useCallback(async () => {
    if (!backendId || backendId.startsWith('rep_')) return;
    try {
      const data = await fetchCropReportTrustStatus(backendId, phone, currentFarmerId);
      if (data) {
        setTrustStatus(data);
        if (data.expert_verification && data.expert_verification.status !== 'REJECTED') {
          setExpertRequested(true);
        }
      }
    } catch {
      // non-fatal
    }
  }, [backendId, phone, currentFarmerId]);

  useEffect(() => {
    loadTrustStatus();
  }, [loadTrustStatus]);

  if (!report) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity activeOpacity={0.7} onPress={() => navigation.goBack()} style={styles.backBtn}>
            <ArrowLeft size={22} color={Colors.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.headerTitleKn}>ವರದಿ ಸಿಗಲಿಲ್ಲ</Text>
          <View style={{ width: 40 }} />
        </View>

        <View style={styles.centerBox}>
          <Text style={styles.errorText}>
            {isKn ? 'ವರದಿಯ ವಿವರಗಳು ಲಭ್ಯವಿಲ್ಲ.' : 'Crop report details are not available.'}
          </Text>
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={() => navigation.navigate('HomeTab')}
            style={styles.actionBtn}
          >
            <Text style={styles.actionBtnText}>{isKn ? 'ಹಿಂದಕ್ಕೆ ಹೋಗಿ' : 'Go to Home'}</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // Request Expert Verification after Demo Payment
  const handlePaymentSuccess = async () => {
    setShowDemoPaymentModal(false);
    setIsRequestingExpert(true);

    try {
      if (backendId && !backendId.startsWith('rep_')) {
        const cropVal = report.cropNameEn || report.cropNameKn || report.crop || 'Arecanut';
        const diagVal = report.predictedDisease || report.predictedDiseaseKn || 'Condition';
        const confVal = report.confidence ? (report.confidence > 1 ? report.confidence / 100 : report.confidence) : 0.85;

        await requestAgriExpertVerification(
          backendId,
          'Farmer requested expert review via Demo Payment',
          phone,
          currentFarmerId,
          {
            payment_status: 'SUCCESS',
            payment_mode: 'DEMO',
            amount: 49.0,
            crop: cropVal,
            diagnosis: diagVal,
            ai_confidence: confVal,
          }
        );
      }
      setExpertRequested(true);
      Alert.alert(
        isKn ? 'ಪರಿಶೀಲನೆ ವಿನಂತಿಸಲಾಗಿದೆ ✓' : 'Verification Requested ✓',
        isKn
          ? 'ಡೆಮೊ ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆ. ವರದಿಯನ್ನು ಕೃಷಿ ತಜ್ಞರ ಪರಿಶೀಲನಾ ಸರದಿಗೆ ಕಳುಹಿಸಲಾಗಿದೆ.'
          : 'Demo payment successful. Report submitted to agricultural expert queue.'
      );
      loadTrustStatus();
    } catch (err: any) {
      setExpertRequested(true);
      loadTrustStatus();
    } finally {
      setIsRequestingExpert(false);
    }
  };

  // Submit Community Corroboration
  const handleCorroborate = async (
    type: 'CONFIRMATION' | 'CONTRADICTION' | 'ADDITIONAL_SYMPTOM' | 'FIELD_NOTE'
  ) => {
    if (isOwner) {
      Alert.alert(
        isKn ? 'ಸ್ವಯಂ ದೃಢೀಕರಣ ಸಾಧ್ಯವಿಲ್ಲ' : 'Self-Corroboration Not Allowed',
        isKn
          ? 'ವರದಿಯ ಮಾಲೀಕರು ತಮ್ಮ ಸ್ವಂತ ವರದಿಯನ್ನು ದೃಢೀಕರಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ.'
          : 'Report owners cannot corroborate their own crop reports.'
      );
      return;
    }

    setIsSubmittingCorroboration(true);
    try {
      if (backendId && !backendId.startsWith('rep_')) {
        await submitPeerCorroboration(backendId, type, undefined, phone, currentFarmerId);
      }
      setCorroborationSubmitted(type);
      Alert.alert(
        isKn ? 'ಅಭಿಪ್ರಾಯ ದಾಖಲಾಗಿದೆ ✓' : 'Observation Recorded ✓',
        isKn
          ? 'ಸಮುದಾಯದ ಪರಿಶೀಲನೆಗೆ ನಿಮ್ಮ ಅಭಿಪ್ರಾಯವನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಸೇರಿಸಲಾಗಿದೆ.'
          : 'Your peer observation was recorded successfully.'
      );
      loadTrustStatus();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Corroboration could not be submitted.';
      Alert.alert(isKn ? 'ಸೂಚನೆ' : 'Notice', isKn ? 'ಅಭಿಪ್ರಾಯ ದಾಖಲಿಸಲಾಗಿದೆ.' : msg);
      setCorroborationSubmitted(type);
    } finally {
      setIsSubmittingCorroboration(false);
    }
  };

  const currentVerificationStatus = trustStatus?.verification_status || (report.status.toUpperCase() as any) || 'AI_ANALYSED';
  const isExpertVerified = currentVerificationStatus === 'EXPERT_VERIFIED' || trustStatus?.expert_verification?.status === 'VERIFIED';
  const isNeedMoreInfo = trustStatus?.expert_verification?.status === 'NEED_MORE_INFO' || trustStatus?.expert_verification?.status === 'REQUIRES_MORE_INFORMATION';
  const corroborationCount = trustStatus?.corroboration_summary?.agreed_count ?? report.evidenceFarmsCount ?? 0;
  const isLowConfidence = Boolean(report.lowConfidence || (report.confidence > 0 && report.confidence < 0.5));

  return (
    <View style={styles.container}>
      {/* Top Header */}
      <View style={styles.header}>
        <TouchableOpacity activeOpacity={0.7} onPress={() => navigation.goBack()} style={styles.backBtn}>
          <ArrowLeft size={22} color={Colors.textPrimary} />
        </TouchableOpacity>
        <View style={styles.headerTitleBox}>
          <Text style={styles.headerTitleKn}>ಬೆಳೆ ಆರೋಗ್ಯ ವರದಿ</Text>
          <Text style={styles.headerTitleEn}>Crop Health Report</Text>
        </View>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Crop & Verification Status Header Row */}
        <View style={styles.metaRow}>
          <View style={styles.cropBadge}>
            <Text style={styles.cropBadgeText}>
              {report.cropNameKn} / {report.cropNameEn}
            </Text>
          </View>
          <StatusBadge status={currentVerificationStatus} />
        </View>

        {/* Uploaded Leaf Image */}
        {report.photoUri && (
          <View style={styles.imageCard}>
            <Image source={{ uri: report.photoUri }} style={styles.leafImage} resizeMode="cover" />
          </View>
        )}

        {/* If Rejected by Relevance / Crop Gate, Show Farmer-Friendly Guidance Only */}
        {isValidationRejected ? (
          <View style={styles.diagnosisCard}>
            <View style={{ alignItems: 'center', paddingVertical: Spacing.md }}>
              <View style={[styles.lowConfidenceAlert, { backgroundColor: '#FEF2F2', borderColor: '#FCA5A5', marginBottom: Spacing.md }]}>
                <AlertCircle size={28} color="#DC2626" />
                <View style={{ flex: 1, marginLeft: Spacing.sm }}>
                  <Text style={[styles.lowConfidenceTitle, { color: '#991B1B', fontSize: 16 }]}>
                    {isIrrelevant
                      ? (isKn ? 'ಚಿತ್ರ ಹೊಂದಿಕೆಯಾಗುತ್ತಿಲ್ಲ' : 'Irrelevant Image')
                      : isCropMismatch
                      ? (isKn ? 'ಬೆಳೆ ಹೊಂದಿಕೆಯಾಗುತ್ತಿಲ್ಲ' : 'Crop Mismatch')
                      : (isKn ? 'ಖಚಿತವಾಗಿ ಗುರುತಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ' : 'Uncertain Image')}
                  </Text>
                  <Text style={[styles.lowConfidenceDesc, { color: '#B91C1C', marginTop: 4 }]}>
                    {isIrrelevant
                      ? (isKn ? 'ಈ ಚಿತ್ರವು ಆಯ್ಕೆ ಮಾಡಿದ ಬೆಳೆಗೆ ಸಂಬಂಧಿಸಿದಂತೆ ಕಾಣುತ್ತಿಲ್ಲ.' : 'The uploaded image does not appear to contain the selected crop.')
                      : isCropMismatch
                      ? (isKn ? 'ಆಯ್ಕೆ ಮಾಡಿದ ಬೆಳೆ ಮತ್ತು ಚಿತ್ರ ಹೊಂದಿಕೆಯಾಗುತ್ತಿಲ್ಲ.' : 'The selected crop does not match the uploaded image.')
                      : (isKn ? 'ಚಿತ್ರದಿಂದ ವಿಶ್ವಾಸಾರ್ಹವಾಗಿ ಬೆಳೆ ಗುರುತಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.' : 'The crop could not be identified reliably from this image.')}
                  </Text>
                </View>
              </View>

              <TouchableOpacity
                activeOpacity={0.88}
                onPress={() => navigation.goBack()}
                style={[styles.actionBtn, { width: '100%', marginTop: Spacing.sm, backgroundColor: '#0F5132' }]}
              >
                <RefreshCw size={18} color="#FFFFFF" style={{ marginRight: 8 }} />
                <Text style={styles.actionBtnText}>
                  {isCropMismatch
                    ? (isKn ? 'ಸರಿಯಾದ ಬೆಳೆ ಆಯ್ಕೆ ಮಾಡಿ' : 'Select Correct Crop')
                    : (isKn ? 'ಮತ್ತೆ ಚಿತ್ರ ಅಪ್ಲೋಡ್ ಮಾಡಿ' : 'Upload Image Again')}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          /* 1. Main Diagnosis Result Card (Only shown for Valid Images) */
          <View style={styles.diagnosisCard}>
            <Text style={styles.diagnosisSectionLabel}>
              {isKn ? 'ಸಂಭಾವ್ಯ ಸಮಸ್ಯೆ' : 'Identified Condition'}
            </Text>

            <Text style={styles.diseaseNameKn}>
              {report.predictedDiseaseKn || report.predictedDisease}
            </Text>

            <Text style={styles.diseaseNameEn}>
              {report.predictedDisease}
              {report.scientificName ? ` (${report.scientificName})` : ''}
            </Text>

            {report.category && (
              <View style={styles.categoryBadge}>
                <Text style={styles.categoryBadgeText}>{report.category}</Text>
              </View>
            )}

            {/* Real Backend Confidence */}
            <View style={styles.confidenceSection}>
              <View style={styles.confidenceLabelRow}>
                <Text style={styles.confidenceLabel}>
                  {isKn ? 'AI ವಿಶ್ಲೇಷಣೆ ಖಚಿತತೆ:' : 'AI Confidence Score:'}
                </Text>
                <Text style={[styles.confidenceValue, isLowConfidence && styles.confidenceValueLow]}>
                  {Math.round(report.confidence * 100)}%
                </Text>
              </View>
              <ConfidenceBar confidence={report.confidence} />
            </View>

            {/* Low Confidence Alert Handling */}
            {isLowConfidence && (
              <View style={styles.lowConfidenceAlert}>
                <AlertTriangle size={18} color="#D97706" />
                <View style={{ flex: 1 }}>
                  <Text style={styles.lowConfidenceTitle}>AI ಗೆ ಖಚಿತತೆ ಕಡಿಮೆ ಇದೆ</Text>
                  <Text style={styles.lowConfidenceDesc}>
                    {isKn
                      ? 'ರೋಗವನ್ನು ದೃಢೀಕರಿಸಲು ಮತ್ತೊಂದು ಸ್ಪಷ್ಟ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ ಅಥವಾ ಕೃಷಿ ತಜ್ಞರ ಪರಿಶೀಲನೆ ಕೇಳಿ.'
                      : 'The model confidence is below the threshold. Please take another clear photo or request expert verification.'}
                  </Text>
                </View>
              </View>
            )}
          </View>
        )}

        {!isValidationRejected && (
          <>
            {/* 2. AI Trust & Transparency Box */}
            <View style={styles.trustTransparencyBox}>
          <View style={styles.trustTransparencyRow}>
            <Sparkles size={16} color="#0F5132" />
            <Text style={styles.trustTransparencyTitle}>AI ಸ್ಥಿತಿ: ✓ AI ವಿಶ್ಲೇಷಿಸಲಾಗಿದೆ</Text>
          </View>
          <Text style={styles.trustTransparencyText}>
            {isExpertVerified
              ? '✓ ಈ ವರದಿಯನ್ನು ಕೃಷಿ ತಜ್ಞರಿಂದ ಅಧಿಕೃತವಾಗಿ ದೃಢೀಕರಿಸಲಾಗಿದೆ.'
              : isKn
              ? 'ಇದು AI ಕಂಪ್ಯೂಟರ್ ದೃಷ್ಟಿ ವಿಶ್ಲೇಷಣೆಯಾಗಿದ್ದು, ಕೃಷಿ ತಜ್ಞರಿಂದ ಅಧಿಕೃತವಾಗಿ ದೃಢೀಕರಿಸುವವರೆಗೆ ತಾತ್ಕಾಲಿಕ ಮಾರ್ಗದರ್ಶನವಾಗಿದೆ.'
              : 'This is an AI model inference and does not constitute certified expert advice until expert verification.'}
          </Text>
        </View>

        {/* 3. "ಈಗ ಏನು ಮಾಡಬೇಕು?" (What Should I Do?) - Only real verified guidance */}
        <View style={styles.advisoryCard}>
          <View style={styles.advisoryHeaderRow}>
            <Sparkles size={18} color="#0F5132" />
            <Text style={styles.advisoryTitle}>ಈಗ ಏನು ಮಾಡಬೇಕು?</Text>
          </View>

          {report.explanationKn || report.remedyKn || report.culturalControl || report.remedyEn ? (
            <View style={styles.advisoryContentBox}>
              {report.explanationKn && (
                <View style={styles.advisorySubSection}>
                  <Text style={styles.advisorySubLabel}>
                    {isKn ? 'ವಿವರಣೆ ಮತ್ತು ಸ್ಥಿತಿ (AI Analysis Summary):' : 'Analysis Summary:'}
                  </Text>
                  <Text style={styles.advisoryBodyText}>{report.explanationKn}</Text>
                </View>
              )}

              {report.approvedActions && report.approvedActions.length > 0 ? (
                <View style={styles.advisorySubSection}>
                  <Text style={styles.advisorySubLabel}>
                    {isKn ? 'ಅನುಮೋದಿತ ಕ್ರಮಗಳು (Approved Actions):' : 'Approved Actions:'}
                  </Text>
                  {report.approvedActions.map((action, idx) => (
                    <Text key={idx} style={[styles.advisoryBodyText, { marginBottom: 6 }]}>
                      • {action}
                    </Text>
                  ))}
                </View>
              ) : (
                <>
                  {report.culturalControl && (
                    <View style={styles.advisorySubSection}>
                      <Text style={styles.advisorySubLabel}>
                        {isKn ? 'ಕೃಷಿ ನಿರ್ವಹಣಾ ಕ್ರಮಗಳು (Agronomic Practice):' : 'Cultural Control:'}
                      </Text>
                      <Text style={styles.advisoryBodyText}>{report.culturalControl}</Text>
                    </View>
                  )}

                  {(report.remedyKn || report.remedyEn) && (
                    <View style={styles.advisorySubSection}>
                      <Text style={styles.advisorySubLabel}>
                        {isKn ? 'ಶಿಫಾರಸು ಮಾಡಿದ ಚಿಕಿತ್ಸೆ (Recommended Treatment):' : 'Curative Remedy:'}
                      </Text>
                      <Text style={styles.advisoryBodyText}>
                        {isKn ? report.remedyKn : (report.remedyEn || report.remedyKn)}
                      </Text>
                    </View>
                  )}
                </>
              )}

              {report.sourceInstitution && (
                <View style={styles.sourceAttributionRow}>
                  <Building2 size={13} color="#64748B" />
                  <Text style={styles.sourceAttributionText}>
                    {isKn ? 'ಮೂಲ ಸಂಸ್ಥೆ' : 'Source'}: <Text style={{ fontWeight: '700' }}>{report.sourceInstitution}</Text>
                  </Text>
                </View>
              )}
            </View>
          ) : (
            <View style={styles.noAdvisoryBox}>
              <Info size={16} color="#64748B" />
              <Text style={styles.noAdvisoryText}>
                {isKn
                  ? 'ಈ ಸಮಸ್ಯೆಗೆ ಈಗ ವಿವರವಾದ ಸಲಹೆ ಲಭ್ಯವಿಲ್ಲ.'
                  : 'Detailed verified advisory is not currently available for this condition.'}
              </Text>
            </View>
          )}
        </View>

        {/* 4. Trust Ladder Widget */}
        <View style={styles.ladderContainer}>
          <Text style={styles.sectionHeaderTitle}>
            {isKn ? 'ಪರಿಶೀಲನಾ ಹಂತ (Trust Ladder)' : 'Verification Ladder'}
          </Text>
          <VerificationLadder
            status={currentVerificationStatus}
            evidenceFarmsCount={corroborationCount}
            verifiedBy={trustStatus?.expert_verification?.expert_notes || (isExpertVerified ? 'KVK Scientist' : undefined)}
            verifiedAt={trustStatus?.expert_verification?.completed_at ? new Date(trustStatus.expert_verification.completed_at).toLocaleDateString('kn-IN') : undefined}
          />
        </View>

        {/* 5. Expert Verification Section */}
        <View style={styles.expertSectionCard}>
          <View style={styles.expertHeaderRow}>
            <ShieldCheck size={20} color="#0F5132" />
            <Text style={styles.expertSectionTitle}>ತಜ್ಞರ ಪರಿಶೀಲನೆ</Text>
          </View>

          <Text style={styles.expertSectionDesc}>
            {isExpertVerified
              ? '✓ ಈ ವರದಿಯನ್ನು ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರದ ತಜ್ಞರಿಂದ ಪರಿಶೀಲಿಸಿ ದೃಢೀಕರಿಸಲಾಗಿದೆ.'
              : expertRequested
              ? 'ತಜ್ಞರ ಪರಿಶೀಲನೆ ಕೋರಲಾಗಿದೆ. ಕೃಷಿ ವಿಜ್ಞಾನಿಗಳ ವರದಿ ನಿರೀಕ್ಷಿಸಲಾಗುತ್ತಿದೆ.'
              : isKn
              ? 'ಈ ವರದಿಯನ್ನು ಕೃಷಿ ತಜ್ಞರಿಂದ ಪರಿಶೀಲಿಸಬಹುದು.'
              : 'You can request official review by certified agronomists.'}
          </Text>

          {isExpertVerified ? (
            <View style={styles.expertVerifiedBadge}>
              <CheckCircle2 size={16} color="#15803D" />
              <View style={{ flex: 1, marginLeft: 6 }}>
                <Text style={styles.expertVerifiedText}>✓ ತಜ್ಞರಿಂದ ದೃಢೀಕರಿಸಲಾಗಿದೆ (VERIFIED)</Text>
                {trustStatus?.expert_verification?.finding ? (
                  <Text style={[styles.expertVerifiedText, { fontSize: 13, fontWeight: '600', marginTop: 2, color: '#14532D' }]}>
                    {isKn ? 'ದೃಢೀಕರಿಸಿದ ರೋಗ:' : 'Confirmed:'} {trustStatus.expert_verification.finding}
                  </Text>
                ) : null}
                {trustStatus?.expert_verification?.expert_notes ? (
                  <Text style={{ fontSize: 12, color: '#166534', marginTop: 4, lineHeight: 16 }}>
                    {trustStatus.expert_verification.expert_notes}
                  </Text>
                ) : null}
              </View>
            </View>
          ) : isNeedMoreInfo ? (
            <View style={[styles.expertRequestedSuccessCard, { borderColor: '#F59E0B', backgroundColor: '#FFFBEB' }]}>
              <View style={styles.expertRequestedSuccessHeader}>
                <AlertCircle size={18} color="#D97706" />
                <Text style={[styles.expertRequestedSuccessTitle, { color: '#B45309' }]}>
                  {isKn ? '⚠️ ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಅಗತ್ಯವಿದೆ' : '⚠️ Requires More Information'}
                </Text>
              </View>
              <Text style={{ fontSize: 13, color: '#92400E', marginTop: 4, lineHeight: 18 }}>
                {trustStatus?.expert_verification?.expert_notes ||
                  (isKn
                    ? 'ಕೃಷಿ ತಜ್ಞರು ರೋಗಪೀಡಿತ ಭಾಗದ ಮತ್ತಷ್ಟು ಸ್ಪಷ್ಟ ಫೋಟೋ ಅಥವಾ ಹೆಚ್ಚಿನ ವಿವರಗಳನ್ನು ಅಪೇಕ್ಷಿಸಿದ್ದಾರೆ.'
                    : 'The agricultural expert requires clearer close-up photos or more details.')}
              </Text>
              <TouchableOpacity
                activeOpacity={0.88}
                onPress={() => navigation.goBack()}
                style={[styles.requestExpertBtn, { backgroundColor: '#D97706', marginTop: 10 }]}
              >
                <RefreshCw size={16} color="#FFFFFF" />
                <Text style={styles.requestExpertBtnText}>
                  {isKn ? 'ಮತ್ತೆ ಸ್ಪಷ್ಟ ಫೋಟೋ ತೆಗೆಯಿರಿ' : 'Upload Clearer Photo'}
                </Text>
              </TouchableOpacity>
            </View>
          ) : expertRequested ? (
            <View style={styles.expertRequestedSuccessCard}>
              <View style={styles.expertRequestedSuccessHeader}>
                <CheckCircle2 size={18} color="#15803D" />
                <Text style={styles.expertRequestedSuccessTitle}>✓ ಪರಿಶೀಲನೆ ವಿನಂತಿಸಲಾಗಿದೆ</Text>
              </View>
              <View style={styles.expertRequestedSuccessRow}>
                <Text style={styles.expertRequestedSuccessLabel}>ಸ್ಥಿತಿ:</Text>
                <Text style={styles.expertRequestedSuccessValue}>ತಜ್ಞರ ಪರಿಶೀಲನೆ ಬಾಕಿಯಿದೆ</Text>
              </View>
              <View style={styles.expertRequestedSuccessRow}>
                <Text style={styles.expertRequestedSuccessLabel}>ಪಾವತಿ:</Text>
                <Text style={styles.expertRequestedSuccessValue}>₹49 • Demo Payment</Text>
              </View>
            </View>
          ) : (
            <TouchableOpacity
              activeOpacity={0.88}
              onPress={() => setShowDemoPaymentModal(true)}
              disabled={isRequestingExpert}
              style={styles.requestExpertBtn}
            >
              {isRequestingExpert ? (
                <ActivityIndicator size="small" color="#FFFFFF" />
              ) : (
                <>
                  <Send size={16} color="#FFFFFF" />
                  <Text style={styles.requestExpertBtnText}>ತಜ್ಞರ ಪರಿಶೀಲನೆ ಕೇಳಿ</Text>
                </>
              )}
            </TouchableOpacity>
          )}
        </View>

        {/* 6. Community Corroboration Section */}
        <View style={styles.communitySectionCard}>
          <View style={styles.communityHeaderRow}>
            <Users size={18} color="#0F5132" />
            <Text style={styles.communitySectionTitle}>ಸಮುದಾಯದ ಅಭಿಪ್ರಾಯ</Text>
          </View>

          <Text style={styles.communitySubText}>
            {corroborationCount > 0
              ? `${corroborationCount} ರೈತರು ಒಪ್ಪಿದ್ದಾರೆ`
              : isKn
              ? 'ಈ ವರದಿಯನ್ನು ಪರಿಶೀಲಿಸಲು ಸಹಾಯ ಮಾಡಿ'
              : 'Help corroborate this report with field observation'}
          </Text>

          {isOwner ? (
            <View style={styles.ownerNoticeBox}>
              <Info size={14} color="#64748B" />
              <Text style={styles.ownerNoticeText}>
                {isKn
                  ? 'ನಿಮ್ಮ ಸ್ವಂತ ವರದಿಯನ್ನು ನೀವೇ ದೃಢೀಕರಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ.'
                  : 'Report owners cannot corroborate their own crop reports.'}
              </Text>
            </View>
          ) : corroborationSubmitted ? (
            <View style={styles.corroborationDoneBox}>
              <CheckCircle2 size={16} color="#15803D" />
              <Text style={styles.corroborationDoneText}>
                {isKn ? 'ನಿಮ್ಮ ಅಭಿಪ್ರಾಯ ದಾಖಲಾಗಿದೆ. ಧನ್ಯವಾದಗಳು!' : 'Observation recorded. Thank you!'}
              </Text>
            </View>
          ) : (
            <View style={styles.corroborationActionsGrid}>
              <TouchableOpacity
                activeOpacity={0.85}
                onPress={() => handleCorroborate('CONFIRMATION')}
                disabled={isSubmittingCorroboration}
                style={[styles.corroborateActionBtn, { backgroundColor: '#F0FDF4', borderColor: '#BBF7D0' }]}
              >
                <ThumbsUp size={15} color="#16A34A" />
                <Text style={[styles.corroborateActionText, { color: '#15803D' }]}>
                  {isKn ? 'ಒಪ್ಪಿಗೆ (Confirm)' : 'Confirm'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                activeOpacity={0.85}
                onPress={() => handleCorroborate('CONTRADICTION')}
                disabled={isSubmittingCorroboration}
                style={[styles.corroborateActionBtn, { backgroundColor: '#FEF2F2', borderColor: '#FECACA' }]}
              >
                <ThumbsDown size={15} color="#DC2626" />
                <Text style={[styles.corroborateActionText, { color: '#B91C1C' }]}>
                  {isKn ? 'ಭಿನ್ನಾಭಿಪ್ರಾಯ (Disagree)' : 'Disagree'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                activeOpacity={0.85}
                onPress={() => handleCorroborate('ADDITIONAL_SYMPTOM')}
                disabled={isSubmittingCorroboration}
                style={[styles.corroborateActionBtn, { backgroundColor: '#FEF3C7', borderColor: '#FDE68A' }]}
              >
                <MessageSquare size={15} color="#D97706" />
                <Text style={[styles.corroborateActionText, { color: '#B45309' }]}>
                  {isKn ? 'ಹೆಚ್ಚುವರಿ ಲಕ್ಷಣ' : 'Add Symptom'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                activeOpacity={0.85}
                onPress={() => handleCorroborate('FIELD_NOTE')}
                disabled={isSubmittingCorroboration}
                style={[styles.corroborateActionBtn, { backgroundColor: '#F1F5F9', borderColor: '#E2E8F0' }]}
              >
                <Info size={15} color="#475569" />
                <Text style={[styles.corroborateActionText, { color: '#334155' }]}>
                  {isKn ? 'ಕ್ಷೇತ್ರ ಟಿಪ್ಪಣಿ' : 'Field Note'}
                </Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
          </>
        )}

        {/* Done / Return CTA */}
        <TouchableOpacity
          activeOpacity={0.88}
          onPress={() => navigation.navigate('HomeTab')}
          style={styles.doneBtn}
        >
          <Text style={styles.doneBtnText}>
            {isKn ? 'ಮುಖಪುಟಕ್ಕೆ ಹಿಂತಿರುಗಿ' : 'Back to Home'}
          </Text>
        </TouchableOpacity>
      </ScrollView>

      <DemoExpertPaymentModal
        visible={showDemoPaymentModal}
        onClose={() => setShowDemoPaymentModal(false)}
        onSuccess={handlePaymentSuccess}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F6F7F9',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 48,
    paddingBottom: 12,
    backgroundColor: '#F6F7F9',
  },
  backBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 2,
  },
  headerTitleBox: {
    alignItems: 'center',
  },
  headerTitleKn: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
  },
  headerTitleEn: {
    fontSize: 12,
    fontWeight: '400',
    color: '#6B7280',
    marginTop: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 48,
    gap: 16,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  cropBadge: {
    backgroundColor: '#EAF7EE',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#BCE5C8',
  },
  cropBadgeText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#114B32',
  },
  imageCard: {
    width: '100%',
    height: 230,
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: '#000000',
    borderWidth: 1,
    borderColor: '#EDF0F2',
  },
  leafImage: {
    width: '100%',
    height: '100%',
  },
  diagnosisCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: '#EDF0F2',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 5,
    elevation: 2,
    gap: 6,
  },
  diagnosisSectionLabel: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
  },
  diseaseNameKn: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1F2937',
    lineHeight: 26,
  },
  diseaseNameEn: {
    fontSize: 14,
    color: '#4B5563',
    fontWeight: '500',
  },
  categoryBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 6,
    marginTop: 2,
    marginBottom: 6,
  },
  categoryBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#B45309',
  },
  confidenceSection: {
    marginTop: 8,
    gap: 6,
  },
  confidenceLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  confidenceLabel: {
    fontSize: 13,
    color: '#6B7280',
    fontWeight: '500',
  },
  confidenceValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#15803D',
  },
  confidenceValueLow: {
    color: '#D97706',
  },
  lowConfidenceAlert: {
    flexDirection: 'row',
    backgroundColor: '#FFFBEB',
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#FDE68A',
    gap: 10,
    marginTop: 8,
    alignItems: 'flex-start',
  },
  lowConfidenceTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#92400E',
    marginBottom: 2,
  },
  lowConfidenceDesc: {
    fontSize: 12,
    color: '#B45309',
    lineHeight: 17,
  },
  trustTransparencyBox: {
    backgroundColor: '#F0FDF4',
    padding: 14,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#BBF7D0',
    gap: 6,
  },
  trustTransparencyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  trustTransparencyTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#114B32',
  },
  trustTransparencyText: {
    fontSize: 12,
    color: '#166534',
    lineHeight: 18,
  },
  advisoryCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: '#EDF0F2',
    gap: 12,
  },
  advisoryHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  advisoryTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#114B32',
  },
  advisoryContentBox: {
    gap: 10,
  },
  advisorySubSection: {
    gap: 4,
  },
  advisorySubLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1F2937',
  },
  advisoryBodyText: {
    fontSize: 13,
    color: '#4B5563',
    lineHeight: 19,
  },
  sourceAttributionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: '#F9FAFB',
  },
  sourceAttributionText: {
    fontSize: 11,
    color: '#6B7280',
  },
  noAdvisoryBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 10,
  },
  noAdvisoryText: {
    fontSize: 13,
    color: '#6B7280',
  },
  ladderContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 16,
    borderWidth: 1,
    borderColor: '#EDF0F2',
    gap: 10,
  },
  sectionHeaderTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 4,
  },
  expertSectionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: '#EDF0F2',
    gap: 8,
  },
  expertHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  expertSectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1F2937',
  },
  expertSectionDesc: {
    fontSize: 13,
    color: '#4B5563',
    lineHeight: 18,
  },
  requestExpertBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#114B32',
    paddingVertical: 12,
    borderRadius: 14,
    gap: 8,
    marginTop: 6,
  },
  requestExpertBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  expertRequestedSuccessCard: {
    backgroundColor: '#F0FDF4',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#BBF7D0',
    padding: 14,
    gap: 8,
    marginTop: 6,
  },
  expertRequestedSuccessHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingBottom: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#DCFCE7',
  },
  expertRequestedSuccessTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#15803D',
  },
  expertRequestedSuccessRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  expertRequestedSuccessLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4B5563',
  },
  expertRequestedSuccessValue: {
    fontSize: 12,
    fontWeight: '700',
    color: '#1F2937',
  },
  expertRequestedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFBEB',
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#FDE68A',
    gap: 8,
    marginTop: 4,
  },
  expertRequestedText: {
    color: '#92400E',
    fontSize: 13,
    fontWeight: '600',
  },
  expertVerifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F0FDF4',
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#BBF7D0',
    gap: 8,
    marginTop: 4,
  },
  expertVerifiedText: {
    color: '#15803D',
    fontSize: 13,
    fontWeight: '600',
  },
  communitySectionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: '#EDF0F2',
    gap: 8,
  },
  communityHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  communitySectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1F2937',
  },
  communitySubText: {
    fontSize: 13,
    color: '#4B5563',
  },
  ownerNoticeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    padding: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    gap: 8,
    marginTop: 4,
  },
  ownerNoticeText: {
    fontSize: 12,
    color: '#6B7280',
    flex: 1,
  },
  corroborationDoneBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDF4',
    padding: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#BBF7D0',
    gap: 8,
    marginTop: 4,
  },
  corroborationDoneText: {
    fontSize: 13,
    color: '#15803D',
    fontWeight: '600',
  },
  corroborationActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 6,
  },
  corroborateActionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 10,
    borderWidth: 1,
    gap: 6,
  },
  corroborateActionText: {
    fontSize: 12,
    fontWeight: '600',
  },
  doneBtn: {
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#E5E7EB',
    paddingVertical: 13,
    borderRadius: 14,
    marginTop: 8,
  },
  doneBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  centerBox: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    gap: 12,
  },
  errorText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
  },
  actionBtn: {
    backgroundColor: '#114B32',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 12,
  },
  actionBtnText: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
});