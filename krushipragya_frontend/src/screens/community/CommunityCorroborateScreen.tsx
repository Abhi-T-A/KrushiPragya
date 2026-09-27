import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  TextInput,
  RefreshControl,
  Alert,
  Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  fetchLocalReports,
  submitCorroboration,
  LocalCropIssueReport,
} from '../../services/communityApi';
import {
  HeartHandshake,
  MapPin,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ShieldCheck,
  Send,
  Sparkles,
  Info,
  Clock,
  Layers,
  ChevronRight,
  User,
} from 'lucide-react-native';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface CommunityCorroborateScreenProps {
  route?: any;
  navigation: any;
}

export const CommunityCorroborateScreen: React.FC<CommunityCorroborateScreenProps> = ({ route, navigation }) => {
  const insets = useSafeAreaInsets();
  const { language } = useLanguage();
  const { user } = useAuth();
  const isKn = language === 'kn';

  const paramReportId = route?.params?.reportId;

  const [reports, setReports] = useState<LocalCropIssueReport[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(paramReportId || null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Corroboration Form State
  const [similarityDecision, setSimilarityDecision] = useState<'SIMILAR' | 'DIFFERENT' | 'NOT_SURE' | null>(null);
  const [similarityLevel, setSimilarityLevel] = useState<'VERY_SIMILAR' | 'SOMEWHAT_SIMILAR'>('VERY_SIMILAR');
  const [corroborationNote, setCorroborationNote] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchLocalReports();
      setReports(data);
      if (!selectedReportId && data.length > 0) {
        setSelectedReportId(paramReportId || data[0].id);
      }
    } catch (e) {
      console.warn('Failed to load corroboration reports:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [paramReportId, selectedReportId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const activeReport = reports.find((r) => r.id === selectedReportId) || reports[0];

  const handleSubmit = async () => {
    if (!activeReport || !similarityDecision) {
      Alert.alert(
        isKn ? 'ಆಯ್ಕೆ ಅಗತ್ಯವಿದೆ' : 'Selection Required',
        isKn ? 'ದಯವಿಟ್ಟು ನೀವು ಇದೇ ಲಕ್ಷಣಗಳನ್ನು ಗಮನಿಸಿದ್ದೀರಾ ಎಂಬುದನ್ನು ಆಯ್ಕೆಮಾಡಿ.' : 'Please select whether you observed similar symptoms.'
      );
      return;
    }

    setIsSubmitting(true);
    try {
      await submitCorroboration(
        activeReport.id,
        similarityDecision,
        similarityLevel,
        corroborationNote,
        user?.name || 'Community Member (Ujire)'
      );

      setIsSubmitting(false);
      setCorroborationNote('');
      setSimilarityDecision(null);

      Alert.alert(
        isKn ? '✅ ಸಾಕ್ಷ್ಯಾಧಾರ ದೃಢೀಕರಣ ಸಲ್ಲಿಸಲಾಗಿದೆ!' : '✅ Corroboration Submitted!',
        isKn
          ? 'ನಿಮ್ಮ ವೀಕ್ಷಣೆಯು ತಜ್ಞರ ಪರಿಶೀಲನಾ ಪಟ್ಟಿಗೆ (Expert Verification Queue) ಸೇರಿದೆ. ಸಮುದಾಯದ ಸಹಯೋಗಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು!'
          : 'Your symptom observation evidence has been linked to this case and forwarded to the Agriculture Expert review queue!',
        [
          { text: 'OK', onPress: () => loadData() },
        ]
      );
    } catch (e) {
      setIsSubmitting(false);
      Alert.alert('Error', 'Failed to submit corroboration.');
    }
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.iconCircle}>
            <HeartHandshake size={20} color="#16A34A" />
          </View>
          <View>
            <Text style={styles.headerTitle}>
              {isKn ? 'ರೋಗಲಕ್ಷಣ ದೃಢೀಕರಣ' : 'Corroborate Reports'}
            </Text>
            <Text style={styles.headerSub}>
              {isKn ? 'ರೈತರ ಸಮಸ್ಯೆಗೆ ಸ್ಥಳೀಯ ಸಾಕ್ಷಿ • ರೋಗ ನಿರ್ಣಯವಲ್ಲ' : 'Community Evidence Corroboration • Non-Diagnostic'}
            </Text>
          </View>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.primary]} />}
      >
        {/* ============================================================== */}
        {/* Core Philosophy Banner (Section 5) */}
        {/* ============================================================== */}
        <View style={styles.ruleBanner}>
          <ShieldCheck size={16} color="#16A34A" />
          <View style={{ flex: 1 }}>
            <Text style={styles.ruleBannerTitle}>
              {isKn ? 'ಸಮುದಾಯದ ಜವಾಬ್ದಾರಿ: ಸಾಕ್ಷ್ಯಾಧಾರ ಮಾತ್ರ' : 'Community Principle: Supporting Evidence'}
            </Text>
            <Text style={styles.ruleBannerText}>
              {isKn
                ? 'ನೀವು ರೋಗ ನಿರ್ಣಯ ಮಾಡುವುದಿಲ್ಲ. ಕೇವಲ "ನನಗೂ ಇದೇ ರೋಗಲಕ್ಷಣಗಳು ಕಂಡಿವೆ" ಎಂದು ಸಾಕ್ಷ್ಯಾಧಾರ ನೀಡುತ್ತೀರಿ. ಅಂತಿಮ ನಿರ್ಧಾರವನ್ನು ಕೃಷಿ ತಜ್ಞರು (Expert) ಕೈಗೊಳ್ಳುತ್ತಾರೆ.'
                : 'Community members report visible field symptoms. You do NOT confirm diseases. Final diagnosis is strictly made by certified Agriculture Experts.'}
            </Text>
          </View>
        </View>

        {/* Report Selector Pills */}
        <View style={styles.selectorWrap}>
          <Text style={styles.selectorLabel}>{isKn ? 'ದೃಢೀಕರಣಕ್ಕಾಗಿ ರೈತರ ವರದಿಗಳು:' : 'Select Case to Corroborate:'}</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.selectorScroll}>
            {reports.map((r) => {
              const isSelected = r.id === (activeReport ? activeReport.id : '');
              return (
                <TouchableOpacity
                  key={r.id}
                  style={[styles.selectorChip, isSelected && styles.selectorChipActive]}
                  onPress={() => {
                    setSelectedReportId(r.id);
                    setSimilarityDecision(null);
                  }}
                  activeOpacity={0.75}
                >
                  <Text style={styles.selectorChipIcon}>{r.crop_icon}</Text>
                  <Text style={[styles.selectorChipText, isSelected && styles.selectorChipTextActive]}>
                    {r.crop_name} ({r.village})
                  </Text>
                  {r.corroborations_count > 0 && (
                    <View style={styles.chipCountBadge}>
                      <Text style={styles.chipCountBadgeText}>{r.corroborations_count}</Text>
                    </View>
                  )}
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>

        {loading && !refreshing ? (
          <View style={styles.centerLoading}>
            <ActivityIndicator size="large" color="#0D9488" />
            <Text style={styles.loadingText}>{isKn ? 'ವರದಿ ಲೋಡ್ ಆಗುತ್ತಿದೆ...' : 'Loading case details...'}</Text>
          </View>
        ) : activeReport ? (
          <View style={styles.activeCaseCard}>
            {/* Case Overview (Section 4) */}
            <View style={styles.caseHeader}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <Text style={styles.caseCropIcon}>{activeReport.crop_icon}</Text>
                <View>
                  <Text style={styles.caseCropTitle}>{activeReport.crop_name}</Text>
                  <Text style={styles.caseLocation}>📍 {activeReport.village} • {activeReport.distance_km} km away</Text>
                </View>
              </View>
              <View style={styles.trustTag}>
                <Text style={styles.trustTagText}>{activeReport.status}</Text>
              </View>
            </View>

            <View style={styles.caseDetailsBox}>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>{isKn ? 'ಗಮನಿಸಿದ ಸಮಸ್ಯೆ:' : 'Observed Issue:'}</Text>
                <Text style={styles.detailValue}>
                  {isKn ? activeReport.observed_issue_kn : activeReport.observed_issue}
                </Text>
              </View>

              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>{isKn ? 'ವರದಿ ಮಾಡಿದವರು:' : 'Reported By:'}</Text>
                <Text style={styles.detailValue}>{activeReport.reporter_name}</Text>
              </View>

              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>{isKn ? 'ದಾಖಲಾದ ಸಮಯ:' : 'Reported At:'}</Text>
                <Text style={styles.detailValue}>{activeReport.reported_at}</Text>
              </View>
            </View>

            {/* Core Corroboration Question (Section 4) */}
            <View style={styles.questionSection}>
              <Text style={styles.questionTitle}>
                {isKn ? 'ನೀವು ಇದೇ ರೀತಿಯ ಲಕ್ಷಣಗಳನ್ನು ನಿಮ್ಮ ಹೊಲದಲ್ಲಿ/ಗ್ರಾಮದಲ್ಲಿ ಗಮನಿಸಿದ್ದೀರಾ?' : 'Have you observed similar symptoms in your locality?'}
              </Text>

              {/* 3 Core Decision Buttons */}
              <View style={styles.decisionButtonsRow}>
                {/* YES */}
                <TouchableOpacity
                  style={[styles.decisionBtn, similarityDecision === 'SIMILAR' && styles.decisionBtnYesActive]}
                  onPress={() => setSimilarityDecision('SIMILAR')}
                  activeOpacity={0.8}
                >
                  <CheckCircle2 size={16} color={similarityDecision === 'SIMILAR' ? '#FFFFFF' : '#16A34A'} />
                  <Text style={[styles.decisionBtnText, similarityDecision === 'SIMILAR' && styles.textWhite]}>
                    {isKn ? 'ಹೌದು — ನನಗೂ ಕಂಡಿದೆ' : 'YES — I SEE SIMILAR'}
                  </Text>
                </TouchableOpacity>

                {/* NO */}
                <TouchableOpacity
                  style={[styles.decisionBtn, similarityDecision === 'DIFFERENT' && styles.decisionBtnNoActive]}
                  onPress={() => setSimilarityDecision('DIFFERENT')}
                  activeOpacity={0.8}
                >
                  <XCircle size={16} color={similarityDecision === 'DIFFERENT' ? '#FFFFFF' : '#DC2626'} />
                  <Text style={[styles.decisionBtnText, similarityDecision === 'DIFFERENT' && styles.textWhite]}>
                    {isKn ? 'ಇಲ್ಲ — ಭಿನ್ನವಾಗಿದೆ' : 'NO — DIFFERENT'}
                  </Text>
                </TouchableOpacity>

                {/* NOT SURE */}
                <TouchableOpacity
                  style={[styles.decisionBtn, similarityDecision === 'NOT_SURE' && styles.decisionBtnUnsureActive]}
                  onPress={() => setSimilarityDecision('NOT_SURE')}
                  activeOpacity={0.8}
                >
                  <HelpCircle size={16} color={similarityDecision === 'NOT_SURE' ? '#FFFFFF' : '#64748B'} />
                  <Text style={[styles.decisionBtnText, similarityDecision === 'NOT_SURE' && styles.textWhite]}>
                    {isKn ? 'ಖಚಿತವಿಲ್ಲ' : 'NOT SURE'}
                  </Text>
                </TouchableOpacity>
              </View>

              {/* Sub-form if YES: How similar? (Section 4) */}
              {similarityDecision === 'SIMILAR' && (
                <View style={styles.similaritySubForm}>
                  <Text style={styles.subFormTitle}>
                    {isKn ? 'ಎಷ್ಟು ಹೋಲಿಕೆಯಾಗುತ್ತಿದೆ? (How similar?)' : 'How similar are the symptoms?'}
                  </Text>

                  <View style={styles.similarityRadioRow}>
                    <TouchableOpacity
                      style={[styles.radioItem, similarityLevel === 'VERY_SIMILAR' && styles.radioItemActive]}
                      onPress={() => setSimilarityLevel('VERY_SIMILAR')}
                      activeOpacity={0.7}
                    >
                      <View style={[styles.radioCircle, similarityLevel === 'VERY_SIMILAR' && styles.radioCircleActive]}>
                        {similarityLevel === 'VERY_SIMILAR' && <View style={styles.radioInner} />}
                      </View>
                      <Text style={[styles.radioLabel, similarityLevel === 'VERY_SIMILAR' && styles.radioLabelActive]}>
                        {isKn ? 'ತುಂಬಾ ಹೋಲುತ್ತದೆ (Very similar)' : 'Very similar'}
                      </Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                      style={[styles.radioItem, similarityLevel === 'SOMEWHAT_SIMILAR' && styles.radioItemActive]}
                      onPress={() => setSimilarityLevel('SOMEWHAT_SIMILAR')}
                      activeOpacity={0.7}
                    >
                      <View style={[styles.radioCircle, similarityLevel === 'SOMEWHAT_SIMILAR' && styles.radioCircleActive]}>
                        {similarityLevel === 'SOMEWHAT_SIMILAR' && <View style={styles.radioInner} />}
                      </View>
                      <Text style={[styles.radioLabel, similarityLevel === 'SOMEWHAT_SIMILAR' && styles.radioLabelActive]}>
                        {isKn ? 'ಸ್ವಲ್ಪ ಹೋಲುತ್ತದೆ (Somewhat similar)' : 'Somewhat similar'}
                      </Text>
                    </TouchableOpacity>
                  </View>

                  <Text style={styles.noteInputLabel}>
                    {isKn ? 'ಐಚ್ಛಿಕ ಟಿಪ್ಪಣಿ (Optional field note):' : 'Optional Field Note:'}
                  </Text>
                  <TextInput
                    style={styles.noteInput}
                    placeholder={
                      isKn
                        ? 'ಉದಾ: ನನ್ನ ತೋಟದಲ್ಲೂ 2 ದಿನಗಳ ಮಳೆಯ ನಂತರ ಕಾಯಿ ಉದುರುತ್ತಿವೆ...'
                        : 'e.g. Observed on 5 vines in north corner after heavy rain...'
                    }
                    placeholderTextColor="#94A3B8"
                    value={corroborationNote}
                    onChangeText={setCorroborationNote}
                    multiline
                    numberOfLines={2}
                  />
                </View>
              )}

              {/* Submit Corroboration Action Button */}
              {similarityDecision && (
                <TouchableOpacity
                  style={styles.submitCorrobBtn}
                  onPress={handleSubmit}
                  disabled={isSubmitting}
                  activeOpacity={0.85}
                >
                  {isSubmitting ? (
                    <ActivityIndicator size="small" color="#FFFFFF" />
                  ) : (
                    <>
                      <Send size={15} color="#FFFFFF" />
                      <Text style={styles.submitCorrobBtnText}>
                        {isKn ? 'ಸಾಕ್ಷ್ಯಾಧಾರ ಸಲ್ಲಿಸಿ (SUBMIT CORROBORATION)' : 'SUBMIT CORROBORATION'}
                      </Text>
                    </>
                  )}
                </TouchableOpacity>
              )}
            </View>

            {/* Existing Peer Corroborations list */}
            {activeReport.corroborations.length > 0 && (
              <View style={styles.existingCorrobsBox}>
                <Text style={styles.existingCorrobsTitle}>
                  {isKn ? 'ಇತರೆ ಸಮುದಾಯ ಸದಸ್ಯರ ಸಾಕ್ಷ್ಯಗಳು:' : 'Peer Evidence Log:'}
                </Text>
                {activeReport.corroborations.map((c) => (
                  <View key={c.id} style={styles.corrobItem}>
                    <View style={styles.corrobItemTop}>
                      <Text style={styles.corrobUser}>{c.user_name}</Text>
                      <View style={styles.simBadge}>
                        <Text style={styles.simBadgeText}>{c.similarity}</Text>
                      </View>
                    </View>
                    {c.note ? <Text style={styles.corrobNote}>"{c.note}"</Text> : null}
                  </View>
                ))}
              </View>
            )}
          </View>
        ) : null}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  iconCircle: {
    width: 38,
    height: 38,
    borderRadius: 10,
    backgroundColor: '#DCFCE7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  headerSub: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '500',
    marginTop: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 36,
    gap: 14,
  },
  ruleBanner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: '#E1F5EE',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#A7F3D0',
    padding: 12,
  },
  ruleBannerTitle: {
    fontSize: 12.5,
    fontWeight: '800',
    color: '#0F6E56',
    marginBottom: 2,
  },
  ruleBannerText: {
    fontSize: 11,
    color: '#166534',
    lineHeight: 16,
  },
  selectorWrap: {
    gap: 8,
  },
  selectorLabel: {
    fontSize: 12.5,
    fontWeight: '700',
    color: '#334155',
  },
  selectorScroll: {
    gap: 8,
  },
  selectorChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  selectorChipActive: {
    backgroundColor: '#DCFCE7',
    borderColor: '#16A34A',
  },
  selectorChipIcon: {
    fontSize: 14,
  },
  selectorChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#475569',
  },
  selectorChipTextActive: {
    color: '#166534',
    fontWeight: '800',
  },
  chipCountBadge: {
    backgroundColor: '#16A34A',
    borderRadius: 8,
    paddingHorizontal: 5,
    paddingVertical: 1,
  },
  chipCountBadgeText: {
    fontSize: 9.5,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  centerLoading: {
    paddingVertical: 50,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  loadingText: {
    fontSize: 13,
    color: '#64748B',
  },
  activeCaseCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    gap: 14,
  },
  caseHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  caseCropIcon: {
    fontSize: 24,
  },
  caseCropTitle: {
    fontSize: 17,
    fontWeight: '900',
    color: '#0F172A',
  },
  caseLocation: {
    fontSize: 11.5,
    color: '#64748B',
    marginTop: 1,
  },
  trustTag: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  trustTagText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#D97706',
  },
  caseDetailsBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 8,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '600',
  },
  detailValue: {
    fontSize: 12.5,
    fontWeight: '700',
    color: '#1E293B',
  },
  questionSection: {
    gap: 12,
  },
  questionTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#0F172A',
    lineHeight: 20,
  },
  decisionButtonsRow: {
    gap: 8,
  },
  decisionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: '#CBD5E1',
    backgroundColor: '#F8FAFC',
  },
  decisionBtnYesActive: {
    backgroundColor: '#16A34A',
    borderColor: '#16A34A',
  },
  decisionBtnNoActive: {
    backgroundColor: '#DC2626',
    borderColor: '#DC2626',
  },
  decisionBtnUnsureActive: {
    backgroundColor: '#64748B',
    borderColor: '#64748B',
  },
  decisionBtnText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#334155',
  },
  textWhite: {
    color: '#FFFFFF',
  },
  similaritySubForm: {
    backgroundColor: '#F0FDFA',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#CCFBF1',
    gap: 8,
  },
  subFormTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: '#0F766E',
  },
  similarityRadioRow: {
    flexDirection: 'row',
    gap: 12,
  },
  radioItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flex: 1,
    backgroundColor: '#FFFFFF',
    padding: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  radioItemActive: {
    borderColor: '#0D9488',
    backgroundColor: '#CCFBF1',
  },
  radioCircle: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: '#CBD5E1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioCircleActive: {
    borderColor: '#0D9488',
  },
  radioInner: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#0D9488',
  },
  radioLabel: {
    fontSize: 11,
    color: '#475569',
    fontWeight: '600',
  },
  radioLabelActive: {
    color: '#0F766E',
    fontWeight: '800',
  },
  noteInputLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#475569',
    marginTop: 4,
  },
  noteInput: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    padding: 8,
    fontSize: 12,
    color: '#0F172A',
  },
  submitCorrobBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#0F6E56',
    paddingVertical: 12,
    borderRadius: 10,
    marginTop: 6,
  },
  submitCorrobBtnText: {
    fontSize: 13,
    fontWeight: '900',
    color: '#FFFFFF',
  },
  existingCorrobsBox: {
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    paddingTop: 12,
    gap: 8,
  },
  existingCorrobsTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: '#475569',
  },
  corrobItem: {
    backgroundColor: '#F8FAFC',
    borderRadius: 8,
    padding: 10,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 4,
  },
  corrobItemTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  corrobUser: {
    fontSize: 11.5,
    fontWeight: '700',
    color: '#1E293B',
  },
  simBadge: {
    backgroundColor: '#CCFBF1',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  simBadgeText: {
    fontSize: 9.5,
    fontWeight: '700',
    color: '#0F766E',
  },
  corrobNote: {
    fontSize: 11,
    fontStyle: 'italic',
    color: '#475569',
  },
});
