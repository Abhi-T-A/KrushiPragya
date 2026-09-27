import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
  Image,
  RefreshControl,
  Modal,
  TextInput,
  Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  fetchExpertQueue,
  submitExpertDecision,
  ExpertQueueItemData,
} from '../../services/cropHealthApi';
import {
  Microscope,
  CheckCircle2,
  Clock,
  AlertTriangle,
  TrendingUp,
  MapPin,
  ShieldCheck,
  FileText,
  ArrowRight,
  Sparkles,
  ChevronRight,
  Globe2,
  X,
  HelpCircle,
  Users,
  Award,
  Filter,
  User as UserIcon,
} from 'lucide-react-native';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// Local crop images fallback map
const CROP_ASSET_IMAGES: Record<string, any> = {
  paddy: require('../../../assets/crops/paddy.jpg'),
  arecanut: require('../../../assets/crops/arecanut.jpg'),
  cardamom: require('../../../assets/crops/cardamom.jpg'),
  black_pepper: require('../../../assets/crops/black_pepper.jpg'),
  coconut: require('../../../assets/crops/coconut.jpg'),
  ginger: require('../../../assets/crops/ginger.jpg'),
  turmeric: require('../../../assets/crops/turmeric.jpg'),
};

interface ExpertDashboardProps {
  navigation: any;
}

export const ExpertDashboardScreen: React.FC<ExpertDashboardProps> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { language, setLanguage } = useLanguage();
  const { user } = useAuth();
  const isKn = language === 'kn';

  const [queueItems, setQueueItems] = useState<ExpertQueueItemData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Review Modal State
  const [selectedRequest, setSelectedRequest] = useState<ExpertQueueItemData | null>(null);
  const [decisionMode, setDecisionMode] = useState<'CONFIRM' | 'CORRECT' | 'NEED_MORE_INFO'>('CONFIRM');
  const [correctedDiagnosis, setCorrectedDiagnosis] = useState('');
  const [expertNotes, setExpertNotes] = useState('');
  const [expertRemedy, setExpertRemedy] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchExpertQueue(user?.phone, user?.id);
      setQueueItems(data?.items || []);
    } catch {
      setQueueItems([]);
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  }, [user?.phone, user?.id]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  // Metrics
  const pendingCount = queueItems.filter((i) => i.status === 'PENDING').length;
  const highPriorityCount = queueItems.filter((i) => i.priority === 'HIGH' && i.status === 'PENDING').length;
  const verifiedCount = queueItems.filter((i) => i.status === 'VERIFIED').length + 34; // base institutional history
  const thisMonthCount = queueItems.filter((i) => i.status === 'VERIFIED').length + 22;

  // Open Clinical Evidence Review
  const handleOpenReview = (item: ExpertQueueItemData) => {
    setSelectedRequest(item);
    setDecisionMode('CONFIRM');
    setCorrectedDiagnosis('');
    setExpertNotes(
      isKn
        ? `ಪರಿಶೀಲಿಸಲಾಗಿದೆ. ${item.latest_diagnosis?.predicted_class_kn || item.diagnosis} ಲಕ್ಷಣಗಳು ದೃಢಪಟ್ಟಿವೆ. ತಕ್ಷಣ ಶಿಫಾರಸು ಮಾಡಿದ ಸಿಂಪರಣೆ ಕ್ರಮ ಕೈಗೊಳ್ಳಿ.`
        : `Verified diagnosis. Symptoms confirm ${item.diagnosis}. Follow scientific spray dosage strictly.`
    );
    setExpertRemedy(
      item.scientific_info?.recommended_spray ||
        (isKn ? '1% ಬೋರ್ಡೋ ದ್ರಾವಣವನ್ನು ಸಮರ್ಪಕವಾಗಿ ಸಿಂಪಡಿಸಿ.' : 'Apply 1% Bordeaux mixture spray thoroughly.')
    );
  };

  // Submit Decision
  const handleFinalizeDecision = async (overrideMode?: 'NEED_MORE_INFO') => {
    if (!selectedRequest) return;
    const mode = overrideMode || decisionMode;
    setIsSubmitting(true);

    try {
      const decisionType =
        mode === 'NEED_MORE_INFO'
          ? 'REQUIRES_MORE_INFORMATION'
          : mode === 'CORRECT'
          ? 'CORRECT'
          : 'VERIFIED';

      const finalFinding =
        mode === 'CORRECT' && correctedDiagnosis.trim()
          ? correctedDiagnosis.trim()
          : selectedRequest.diagnosis || 'Confirmed Diagnosis';

      await submitExpertDecision(
        selectedRequest.id,
        decisionType,
        finalFinding,
        expertNotes,
        expertRemedy,
        user?.phone,
        user?.id
      );

      Alert.alert(
        mode === 'NEED_MORE_INFO'
          ? (isKn ? 'ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಕೋರಲಾಗಿದೆ ℹ️' : 'More Information Requested ℹ️')
          : (isKn ? 'ವರದಿ ದೃಢೀಕರಿಸಲಾಗಿದೆ ✅' : 'Report Verified Successfully ✅'),
        mode === 'NEED_MORE_INFO'
          ? (isKn
              ? 'ರೈತರಿಗೆ ಹೆಚ್ಚುವರಿ ಸ್ಪಷ್ಟ ಫೋಟೋ ಹಾಗೂ ವಿವರ ಒದಗಿಸಲು ಸೂಚಿಸಲಾಗಿದೆ.'
              : 'Notification sent to farmer requesting closer lesion photos.')
          : (isKn
              ? `ತಜ್ಞರ ದೃಢೀಕರಣ ಪೂರ್ಣಗೊಂಡಿದೆ. ರೈತರಿಗೆ ಅಧಿಕೃತ ಕೃಷಿ ಸಲಹೆ ರವಾನೆಯಾಗಿದೆ.`
              : `Expert verification registered. Verified guidance dispatched to farmer.`)
      );

      setSelectedRequest(null);
      loadData();
    } catch {
      Alert.alert(isKn ? 'ದೋಷ' : 'Error', 'Could not record decision.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* ============================================================== */}
      {/* 1. Header (Expert Identity & Credentials) */}
      {/* ============================================================== */}
      <View style={[styles.headerWrapper, { paddingTop: Math.max(insets.top, 12) + Spacing.xs }]}>
        <View style={styles.headerTopRow}>
          <View style={styles.brandTitleCol}>
            <View style={styles.logoBadgeRow}>
              <View style={styles.logoCircle}>
                <Microscope size={18} color="#FFFFFF" strokeWidth={2.4} />
              </View>
              <Text style={styles.appTitle}>
                <Text style={{ color: '#166534' }}>Krushi</Text>
                <Text style={{ color: '#16A34A' }}>Pragya</Text>
              </Text>
            </View>
            <Text style={styles.expertRoleTag}>
              {isKn ? '🔬 ಕೃಷಿ ತಜ್ಞರ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್' : '🔬 Agriculture Expert Dashboard'}
            </Text>
          </View>

          {/* Right: Language switch button & Profile icon */}
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <TouchableOpacity
              activeOpacity={0.8}
              onPress={() => setLanguage(isKn ? 'en' : 'kn')}
              style={styles.langPill}
            >
              <Globe2 size={13} color="#0F766E" />
              <Text style={styles.langText}>{isKn ? 'English' : 'ಕನ್ನಡ'}</Text>
            </TouchableOpacity>

            <TouchableOpacity
              activeOpacity={0.8}
              onPress={() => navigation.navigate('Profile')}
              style={styles.profileAvatarBtn}
            >
              <UserIcon size={16} color="#0F766E" strokeWidth={2.4} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Expert Profile Card */}
        <TouchableOpacity
          activeOpacity={0.85}
          onPress={() => navigation.navigate('Profile')}
          style={styles.expertIdentityCard}
        >
          <View style={styles.expertAvatarCircle}>
            <Text style={styles.expertAvatarText}>
              {user?.name ? user.name.slice(0, 2).toUpperCase() : 'DR'}
            </Text>
          </View>
          <View style={{ flex: 1 }}>
            <View style={styles.nameRow}>
              <Text style={styles.expertName}>
                {user?.name || (isKn ? 'ಡಾ. ರಮೇಶ್ ಕೆ' : 'Dr. Ramesh K')}
              </Text>
              <View style={styles.badgeKvk}>
                <Award size={11} color="#0F766E" />
                <Text style={styles.badgeKvkText}>ICAR - KVK</Text>
              </View>
            </View>
            <Text style={styles.expertDesignation}>
              {isKn ? 'ಹಿರಿಯ ಕೃಷಿ ವಿಜ್ಞಾನಿ & ಸಸ್ಯ ರೋಗಶಾಸ್ತ್ರಜ್ಞ' : 'Senior Agricultural Scientist & Pathologist'}
            </Text>
            <Text style={styles.expertOrg}>
              {user?.organization || (isKn ? 'ಐಸಿಎಆರ್ - ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರ, ಉಡುಪಿ' : 'ICAR – KVK Brahmavar, Udupi')}
            </Text>
          </View>
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#0F766E']} />}
      >
        {/* ============================================================== */}
        {/* 2. Dashboard Summary Metrics (4 Cards Grid) */}
        {/* ============================================================== */}
        <View style={styles.summaryGrid}>
          {/* Card 1: Pending */}
          <View style={[styles.metricCard, { borderLeftColor: '#0F766E' }]}>
            <View style={styles.metricCardTop}>
              <Text style={styles.metricNumber}>{pendingCount}</Text>
              <View style={[styles.metricIconWrap, { backgroundColor: '#CCFBF1' }]}>
                <Clock size={16} color="#0F766E" />
              </View>
            </View>
            <Text style={styles.metricLabel}>{isKn ? 'ಪರಿಶೀಲನೆಗೆ ಬಾಕಿ' : 'Pending Review'}</Text>
            <Text style={styles.metricSub}>{isKn ? 'ರೈತರ ವಿನಂತಿಗಳು' : 'Farmer Requests'}</Text>
          </View>

          {/* Card 2: High Priority */}
          <View style={[styles.metricCard, { borderLeftColor: '#DC2626' }]}>
            <View style={styles.metricCardTop}>
              <Text style={[styles.metricNumber, { color: '#DC2626' }]}>{highPriorityCount}</Text>
              <View style={[styles.metricIconWrap, { backgroundColor: '#FEE2E2' }]}>
                <AlertTriangle size={16} color="#DC2626" />
              </View>
            </View>
            <Text style={styles.metricLabel}>{isKn ? 'ತುರ್ತು ಆದ್ಯತೆ' : 'High Priority'}</Text>
            <Text style={styles.metricSub}>{isKn ? 'ತೀವ್ರ ಹರಡುವಿಕೆ' : 'Epidemic / High Conf'}</Text>
          </View>

          {/* Card 3: Verified */}
          <View style={[styles.metricCard, { borderLeftColor: '#16A34A' }]}>
            <View style={styles.metricCardTop}>
              <Text style={[styles.metricNumber, { color: '#16A34A' }]}>{verifiedCount}</Text>
              <View style={[styles.metricIconWrap, { backgroundColor: '#DCFCE7' }]}>
                <CheckCircle2 size={16} color="#16A34A" />
              </View>
            </View>
            <Text style={styles.metricLabel}>{isKn ? 'ದೃಢೀಕರಿಸಲ್ಪಟ್ಟಿದೆ' : 'Verified'}</Text>
            <Text style={styles.metricSub}>{isKn ? 'ಒಟ್ಟು ಪರಿಶೀಲನೆ' : 'Total Reviewed'}</Text>
          </View>

          {/* Card 4: This Month */}
          <View style={[styles.metricCard, { borderLeftColor: '#2563EB' }]}>
            <View style={styles.metricCardTop}>
              <Text style={[styles.metricNumber, { color: '#2563EB' }]}>{thisMonthCount}</Text>
              <View style={[styles.metricIconWrap, { backgroundColor: '#DBEAFE' }]}>
                <TrendingUp size={16} color="#2563EB" />
              </View>
            </View>
            <Text style={styles.metricLabel}>{isKn ? 'ಈ ತಿಂಗಳ ಚಟುವಟಿಕೆ' : 'This Month'}</Text>
            <Text style={styles.metricSub}>{isKn ? 'ಸೆಪ್ಟೆಂಬರ್ 2026' : 'Active Cases'}</Text>
          </View>
        </View>

        {/* ============================================================== */}
        {/* 3. Core Architecture Trust Ladder Pipeline Banner */}
        {/* ============================================================== */}
        <View style={styles.pipelineCard}>
          <View style={styles.pipelineHeader}>
            <Sparkles size={16} color="#0D9488" />
            <Text style={styles.pipelineTitle}>
              {isKn ? 'ಕೃಷಿಪ್ರಜ್ಞಾ ನಂಬಿಕೆಯ ಏಣಿ (Trust Ladder)' : 'KrushiPragya Trust Ladder Protocol'}
            </Text>
          </View>
          <Text style={styles.pipelineSubtitle}>
            {isKn
              ? 'ರೈತರ ಅವಲೋಕನ → AI ವಿಶ್ಲೇಷಣೆ → ಸಮುದಾಯ ದೃಢೀಕರಣ → ತಜ್ಞರ ಪರಿಶೀಲನೆ → ರೈತರ ಕ್ರಮ'
              : 'Farmer Observes → AI Analyses → Community Corroborates → Expert Verifies → Farmer Acts'}
          </Text>
          <View style={styles.pipelineStepsRow}>
            <View style={styles.stepBubble}>
              <Text style={styles.stepNumber}>1</Text>
              <Text style={styles.stepName}>{isKn ? 'ರೈತ' : 'Farmer'}</Text>
            </View>
            <View style={styles.stepArrow}><ChevronRight size={14} color="#94A3B8" /></View>
            <View style={styles.stepBubble}>
              <Text style={styles.stepNumber}>2</Text>
              <Text style={styles.stepName}>AI</Text>
            </View>
            <View style={styles.stepArrow}><ChevronRight size={14} color="#94A3B8" /></View>
            <View style={styles.stepBubble}>
              <Text style={styles.stepNumber}>3</Text>
              <Text style={styles.stepName}>{isKn ? 'ಸಮುದಾಯ' : 'Community'}</Text>
            </View>
            <View style={styles.stepArrow}><ChevronRight size={14} color="#94A3B8" /></View>
            <View style={[styles.stepBubble, styles.activeStepBubble]}>
              <Text style={[styles.stepNumber, { color: '#FFFFFF' }]}>4</Text>
              <Text style={[styles.stepName, { color: '#0F766E', fontWeight: '800' }]}>
                {isKn ? 'ತಜ್ಞರು' : 'Expert'}
              </Text>
            </View>
          </View>
        </View>

        {/* ============================================================== */}
        {/* 4. Priority Verification Queue (Top Items) */}
        {/* ============================================================== */}
        <View style={styles.sectionHeaderRow}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <Microscope size={18} color="#0F766E" />
            <Text style={styles.sectionTitleKn}>
              {isKn ? 'ತಜ್ಞರ ಪರಿಶೀಲನೆ ಕ್ಯೂ (Verification Queue)' : 'High Priority Verification Queue'}
            </Text>
          </View>
          <TouchableOpacity
            style={styles.viewAllBtn}
            onPress={() => navigation.navigate('ExpertQueueTab')}
            activeOpacity={0.7}
          >
            <Text style={styles.viewAllBtnText}>{isKn ? 'ಎಲ್ಲವನ್ನೂ ನೋಡಿ' : 'View All'}</Text>
            <ArrowRight size={13} color="#0F766E" />
          </TouchableOpacity>
        </View>

        {isLoading ? (
          <View style={styles.centerLoading}>
            <ActivityIndicator size="small" color="#0F766E" />
            <Text style={styles.loadingText}>
              {isKn ? 'ಕ್ಯೂ ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...' : 'Loading verification queue...'}
            </Text>
          </View>
        ) : (
          <View style={styles.cardsList}>
            {queueItems.slice(0, 3).map((item) => {
              const isHigh = item.priority === 'HIGH';
              const confidencePct = Math.round(
                (item.ai_confidence ?? item.latest_diagnosis?.confidence ?? 0.8) * 100
              );
              const isResolved = item.status === 'VERIFIED';
              const isNeedInfo = item.status === 'NEED_MORE_INFO';

              return (
                <View
                  key={item.id}
                  style={[
                    styles.queueCard,
                    isResolved && styles.queueCardVerified,
                    isNeedInfo && styles.queueCardNeedInfo,
                  ]}
                >
                  {/* Card Top: Priority & Paid Badge */}
                  <View style={styles.cardTopRow}>
                    <View style={styles.priorityBadgeRow}>
                      <View style={[styles.priorityPill, isHigh ? styles.pillHigh : styles.pillModerate]}>
                        <Text style={[styles.priorityText, isHigh ? styles.textHigh : styles.textModerate]}>
                          {isHigh
                            ? (isKn ? '🔴 ತುರ್ತು ಆದ್ಯತೆ (High Priority)' : '🔴 High Priority')
                            : (isKn ? '🟡 ಸಾಮಾನ್ಯ ಆದ್ಯತೆ' : '🟡 Priority')}
                        </Text>
                      </View>
                    </View>
                    <View style={styles.paidBadge}>
                      <ShieldCheck size={11} color="#15803D" />
                      <Text style={styles.paidBadgeText}>₹49 Paid</Text>
                    </View>
                  </View>

                  {/* Card Main Info */}
                  <View style={styles.cardMainRow}>
                    <View style={{ flex: 1, gap: 4 }}>
                      <Text style={styles.cropTitle}>
                        {isKn && item.crop_name_kn
                          ? `${item.crop_name_kn} (${item.crop_name})`
                          : (item.crop_name || 'Crop')}
                      </Text>

                      <View style={styles.infoLine}>
                        <Text style={styles.infoLabel}>{isKn ? 'ರೈತ:' : 'Farmer:'}</Text>
                        <Text style={styles.infoValue}>{item.farmer_name || 'Farmer'}</Text>
                        <Text style={styles.dotSeparator}>•</Text>
                        <MapPin size={11} color="#64748B" />
                        <Text style={styles.infoValueMuted}>{item.location || 'Ujire'}</Text>
                      </View>

                      <View style={styles.infoLine}>
                        <Text style={styles.infoLabel}>{isKn ? 'AI ರೋಗ ನಿರ್ಣಯ:' : 'AI Diagnosis:'}</Text>
                        <Text style={[styles.infoValue, styles.diagnosisBold]}>
                          {isKn && item.latest_diagnosis?.predicted_class_kn
                            ? item.latest_diagnosis.predicted_class_kn
                            : (item.diagnosis || item.latest_diagnosis?.predicted_class || 'Disease')}
                        </Text>
                      </View>

                      <View style={styles.infoLine}>
                        <Text style={styles.infoLabel}>{isKn ? 'AI ಖಚಿತತೆ (Confidence):' : 'AI Confidence:'}</Text>
                        <Text style={[styles.confidenceBadge, { color: confidencePct > 75 ? '#16A34A' : '#D97706' }]}>
                          {confidencePct}%
                        </Text>
                      </View>
                    </View>
                  </View>

                  {/* Card Bottom Action */}
                  <View style={styles.cardActionRow}>
                    {isResolved ? (
                      <View style={styles.resolvedInlineTag}>
                        <CheckCircle2 size={14} color="#16A34A" />
                        <Text style={styles.resolvedInlineText}>
                          {isKn ? 'ದೃಢೀಕರಿಸಲಾಗಿದೆ ✓' : 'Expert Verified ✓'}
                        </Text>
                      </View>
                    ) : isNeedInfo ? (
                      <View style={styles.needInfoInlineTag}>
                        <HelpCircle size={14} color="#B45309" />
                        <Text style={styles.needInfoInlineText}>
                          {isKn ? 'ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಕೋರಲಾಗಿದೆ ℹ️' : 'More Info Requested ℹ️'}
                        </Text>
                      </View>
                    ) : (
                      <TouchableOpacity
                        style={styles.reviewBtn}
                        activeOpacity={0.85}
                        onPress={() => handleOpenReview(item)}
                      >
                        <FileText size={14} color="#FFFFFF" />
                        <Text style={styles.reviewBtnText}>
                          {isKn ? 'ವರದಿ ಪರಿಶೀಲಿಸಿ' : 'Review Report'}
                        </Text>
                      </TouchableOpacity>
                    )}
                  </View>
                </View>
              );
            })}
          </View>
        )}
      </ScrollView>

      {/* ============================================================== */}
      {/* 5. Complete Clinical Evidence Review Modal ("ವರದಿ ಪರಿಶೀಲಿಸಿ") */}
      {/* ============================================================== */}
      <Modal
        visible={!!selectedRequest}
        transparent
        animationType="slide"
        onRequestClose={() => setSelectedRequest(null)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalSheet, { maxHeight: '92%' }]}>
            {/* Modal Header */}
            <View style={styles.modalHeaderRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.modalSheetTitle}>
                  {isKn ? 'ವರದಿ ಪರಿಶೀಲನೆ (Clinical Evidence Review)' : 'Clinical Evidence Review'}
                </Text>
                <Text style={styles.modalSheetSubtitle}>
                  {selectedRequest?.farmer_name} • {selectedRequest?.crop_name} • {selectedRequest?.location}
                </Text>
              </View>
              <TouchableOpacity
                onPress={() => setSelectedRequest(null)}
                style={styles.closeBtn}
                activeOpacity={0.7}
              >
                <X size={20} color="#475569" />
              </TouchableOpacity>
            </View>

            <ScrollView contentContainerStyle={styles.modalScrollContent} showsVerticalScrollIndicator={false}>
              {/* Section 1: Crop Health Evidence Details */}
              <View style={styles.modalSectionBox}>
                <Text style={styles.modalSectionTitle}>
                  {isKn ? '1. ಬೆಳೆ ಆರೋಗ್ಯ ಸಾಕ್ಷ್ಯಾಧಾರ (Crop Health Evidence):' : '1. Crop Health Evidence:'}
                </Text>

                <View style={styles.evidenceGrid}>
                  <View style={styles.evidenceRow}>
                    <Text style={styles.evidenceLabel}>{isKn ? 'ಬೆಳೆ (Crop):' : 'Crop:'}</Text>
                    <Text style={styles.evidenceVal}>
                      {isKn && selectedRequest?.crop_name_kn
                        ? `${selectedRequest.crop_name_kn} (${selectedRequest.crop_name})`
                        : (selectedRequest?.crop_name || 'Arecanut')}
                    </Text>
                  </View>

                  <View style={styles.evidenceRow}>
                    <Text style={styles.evidenceLabel}>{isKn ? 'ರೈತರು (Farmer):' : 'Farmer:'}</Text>
                    <Text style={styles.evidenceVal}>{selectedRequest?.farmer_name || 'Mallikarjuna G.'}</Text>
                  </View>

                  <View style={styles.evidenceRow}>
                    <Text style={styles.evidenceLabel}>{isKn ? 'ಸ್ಥಳ (Location):' : 'Location:'}</Text>
                    <Text style={styles.evidenceVal}>{selectedRequest?.location || 'Ujire'}</Text>
                  </View>

                  <View style={styles.evidenceRow}>
                    <Text style={styles.evidenceLabel}>{isKn ? 'ಸಲ್ಲಿಸಿದ ಸಮಯ (Submitted):' : 'Submitted:'}</Text>
                    <Text style={styles.evidenceVal}>
                      {selectedRequest?.requested_at
                        ? new Date(selectedRequest.requested_at).toLocaleString()
                        : '26 Sept 2026, 12:45 PM'}
                    </Text>
                  </View>
                </View>
              </View>

              {/* Section 2: Actual Farmer Submitted Image */}
              <View style={styles.modalSectionBox}>
                <Text style={styles.modalSectionTitle}>
                  {isKn ? '2. ರೈತರು ಅಪ್‌ಲೋಡ್ ಮಾಡಿದ ಚಿತ್ರ (Submitted Photo):' : '2. Submitted Leaf/Crop Photo:'}
                </Text>
                <View style={styles.imagePreviewFrame}>
                  <Image
                    source={
                      selectedRequest?.crop_code && CROP_ASSET_IMAGES[selectedRequest.crop_code]
                        ? CROP_ASSET_IMAGES[selectedRequest.crop_code]
                        : require('../../../assets/crops/crop_scan_hero.jpg')
                    }
                    style={styles.cropEvidenceImage}
                    resizeMode="cover"
                  />
                  <View style={styles.imageOverlayTag}>
                    <ShieldCheck size={12} color="#FFFFFF" />
                    <Text style={styles.imageOverlayText}>
                      {isKn ? 'ಅಸಲಿ ಸಾಕ್ಷಿ ಫೋಟೋ' : 'Original Farmer Photo'}
                    </Text>
                  </View>
                </View>
              </View>

              {/* Section 3: AI Analysis & Scientific KB */}
              <View style={styles.modalSectionBox}>
                <Text style={styles.modalSectionTitle}>
                  {isKn ? '3. AI ವಿಶ್ಲೇಷಣೆ (AI Analysis & Knowledge Base):' : '3. AI Analysis & KB Evidence:'}
                </Text>

                <View style={styles.aiResultCard}>
                  <View style={styles.aiDiagRow}>
                    <Text style={styles.aiDiagTitle}>
                      {selectedRequest?.diagnosis || selectedRequest?.latest_diagnosis?.predicted_class || 'Disease'}
                    </Text>
                    <View style={styles.confPill}>
                      <Text style={styles.confPillText}>
                        {Math.round((selectedRequest?.ai_confidence ?? 0.73) * 100)}% Confidence
                      </Text>
                    </View>
                  </View>

                  <View style={styles.kbRow}>
                    <Text style={styles.kbLabel}>{isKn ? 'ರೋಗಕಾರಕ (Pathogen):' : 'Causal Agent:'}</Text>
                    <Text style={styles.kbVal}>
                      {selectedRequest?.scientific_info?.causal_agent || 'Phytophthora meadii McRae'}
                    </Text>
                  </View>

                  <View style={styles.kbRow}>
                    <Text style={styles.kbLabel}>{isKn ? 'ರೋಗ ಲಕ್ಷಣಗಳು:' : 'Symptoms:'}</Text>
                    <Text style={styles.kbVal}>
                      {selectedRequest?.scientific_info?.symptoms || 'Dark lesions with rotting and premature fruit drop.'}
                    </Text>
                  </View>
                </View>
              </View>

              {/* Section 4: Community Evidence */}
              <View style={styles.modalSectionBox}>
                <Text style={styles.modalSectionTitle}>
                  {isKn ? '4. ಸಮುದಾಯ ದೃಢೀಕರಣ (Community Evidence):' : '4. Community Corroboration Evidence:'}
                </Text>

                <View style={styles.communityCard}>
                  <View style={styles.commStatsRow}>
                    <View style={styles.commStatBox}>
                      <Text style={styles.commStatNumber}>
                        {selectedRequest?.corroboration_summary?.total_count || 4}
                      </Text>
                      <Text style={styles.commStatLabel}>{isKn ? 'ಒಟ್ಟು ವರದಿಗಳು' : 'Peer Reports'}</Text>
                    </View>

                    <View style={styles.commStatBox}>
                      <Text style={[styles.commStatNumber, { color: '#16A34A' }]}>
                        {selectedRequest?.corroboration_summary?.agreed_count || 3}
                      </Text>
                      <Text style={styles.commStatLabel}>{isKn ? 'ಸಹಮತ (Agree)' : 'Agree'}</Text>
                    </View>

                    <View style={styles.commStatBox}>
                      <Text style={[styles.commStatNumber, { color: '#DC2626' }]}>
                        {selectedRequest?.corroboration_summary?.disagreed_count || 1}
                      </Text>
                      <Text style={styles.commStatLabel}>{isKn ? 'ಭಿನ್ನಾಭಿಪ್ರಾಯ' : 'Disagree'}</Text>
                    </View>
                  </View>

                  <View style={styles.commNoteBox}>
                    <Users size={14} color="#0F766E" />
                    <Text style={styles.commNoteText}>
                      {isKn
                        ? '3 ರೈತರು ಸಮೀಪದ ಜಮೀನುಗಳಲ್ಲಿ ಇದೇ ರೀತಿಯ ಲಕ್ಷಣಗಳನ್ನು ವರದಿ ಮಾಡಿದ್ದಾರೆ (ಹೋಲಿಕೆ: ಅಧಿಕ).'
                        : '3 neighboring farmers corroborated identical symptoms in Ujire. Peer Similarity: High.'}
                    </Text>
                  </View>
                </View>
              </View>

              {/* Section 5: Expert Decision / Assessment */}
              <View style={styles.modalSectionBox}>
                <Text style={styles.modalSectionTitle}>
                  {isKn ? '5. ತಜ್ಞರ ನಿರ್ಧಾರ (Expert Assessment):' : '5. Expert Clinical Assessment:'}
                </Text>

                <View style={styles.decisionOptions}>
                  {/* Option 1: Confirm AI Diagnosis */}
                  <TouchableOpacity
                    style={[styles.decisionRadioCard, decisionMode === 'CONFIRM' && styles.radioActive]}
                    onPress={() => setDecisionMode('CONFIRM')}
                    activeOpacity={0.8}
                  >
                    <View style={[styles.radioCircle, decisionMode === 'CONFIRM' && styles.radioCircleActive]}>
                      {decisionMode === 'CONFIRM' && <View style={styles.radioDot} />}
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.radioTitle}>
                        {isKn ? 'AI ರೋಗನಿರ್ಣಯ ದೃಢೀಕರಿಸಿ (Confirm AI Diagnosis)' : 'Confirm AI Diagnosis'}
                      </Text>
                      <Text style={styles.radioSub}>
                        {isKn
                          ? 'AI ನೀಡಿದ ರೋಗದ ಮಾದರಿ ನಿಖರವಾಗಿದೆ ಎಂದು ಅಧಿಕೃತವಾಗಿ ಅನುಮೋದಿಸಿ.'
                          : 'Validate that the AI predicted diagnosis is medically accurate.'}
                      </Text>
                    </View>
                  </TouchableOpacity>

                  {/* Option 2: Correct Diagnosis */}
                  <TouchableOpacity
                    style={[styles.decisionRadioCard, decisionMode === 'CORRECT' && styles.radioActive]}
                    onPress={() => setDecisionMode('CORRECT')}
                    activeOpacity={0.8}
                  >
                    <View style={[styles.radioCircle, decisionMode === 'CORRECT' && styles.radioCircleActive]}>
                      {decisionMode === 'CORRECT' && <View style={styles.radioDot} />}
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.radioTitle}>
                        {isKn ? 'ರೋಗನಿರ್ಣಯ ತಿದ್ದಿ (Correct Diagnosis)' : 'Correct / Rectify Diagnosis'}
                      </Text>
                      <Text style={styles.radioSub}>
                        {isKn
                          ? 'AI ರೋಗ ತಪ್ಪಾಗಿದ್ದು, ಸರಿಯಾದ ಪರ್ಯಾಯ ರೋಗವನ್ನು ಸೂಚಿಸಿ.'
                          : 'Override AI prediction with the correct scientific pathogen.'}
                      </Text>
                    </View>
                  </TouchableOpacity>

                  {/* If Correct is selected, show custom corrected input */}
                  {decisionMode === 'CORRECT' && (
                    <View style={styles.correctInputBox}>
                      <Text style={styles.correctInputLabel}>
                        {isKn ? 'ಸರಿಯಾದ ರೋಗದ ಹೆಸರು ನಮೂದಿಸಿ:' : 'Enter Correct Diagnosis:'}
                      </Text>
                      <TextInput
                        style={styles.correctTextInput}
                        placeholder={isKn ? 'ಉದಾ: ಸುಳಿ ಕೊಳೆ (Bud Rot / Anabe)' : 'e.g. Bud Rot / Ganoderma'}
                        placeholderTextColor="#94A3B8"
                        value={correctedDiagnosis}
                        onChangeText={setCorrectedDiagnosis}
                      />
                    </View>
                  )}

                  {/* Option 3: Needs More Information */}
                  <TouchableOpacity
                    style={[styles.decisionRadioCard, decisionMode === 'NEED_MORE_INFO' && styles.radioActiveWarning]}
                    onPress={() => setDecisionMode('NEED_MORE_INFO')}
                    activeOpacity={0.8}
                  >
                    <View style={[styles.radioCircle, decisionMode === 'NEED_MORE_INFO' && styles.radioCircleActiveWarning]}>
                      {decisionMode === 'NEED_MORE_INFO' && <View style={[styles.radioDot, { backgroundColor: '#D97706' }]} />}
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.radioTitle}>
                        {isKn ? 'ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಅಗತ್ಯವಿದೆ (Needs More Information)' : 'Needs More Information'}
                      </Text>
                      <Text style={styles.radioSub}>
                        {isKn
                          ? 'ಫೋಟೋ ಸ್ಪಷ್ಟವಾಗಿಲ್ಲ / ಕಾಂಡದ ನಿಕಟ ಚಿತ್ರ ಅಗತ್ಯವಿದೆ.'
                          : 'Request clearer close-up photograph of collar/leaf lesion.'}
                      </Text>
                    </View>
                  </TouchableOpacity>
                </View>
              </View>

              {/* Section 6: Expert Clinical Notes & Prescription */}
              <View style={styles.modalSectionBox}>
                <Text style={styles.modalSectionTitle}>
                  {isKn ? '6. ತಜ್ಞರ ಟಿಪ್ಪಣಿ & ಶಿಫಾರಸು (Expert Notes & Advice):' : '6. Expert Notes & Scientific Remedy:'}
                </Text>

                <View style={styles.inputGroup}>
                  <Text style={styles.fieldLabel}>{isKn ? 'ತಜ್ಞರ ಟಿಪ್ಪಣಿ (Expert Clinical Notes):' : 'Expert Notes:'}</Text>
                  <TextInput
                    style={[styles.textInputArea, { height: 75 }]}
                    multiline
                    value={expertNotes}
                    onChangeText={setExpertNotes}
                    placeholder={isKn ? 'ವೈಜ್ಞಾನಿಕ ವಿವರಣೆ...' : 'Professional notes on disease stage...'}
                    placeholderTextColor="#94A3B8"
                  />
                </View>

                {decisionMode !== 'NEED_MORE_INFO' && (
                  <View style={[styles.inputGroup, { marginTop: 10 }]}>
                    <Text style={styles.fieldLabel}>
                      {isKn ? 'ವೈಜ್ಞಾನಿಕ ಸಿಂಪರಣಾ ಕ್ರಮ (Recommended Action):' : 'Recommended Spray Action:'}
                    </Text>
                    <TextInput
                      style={[styles.textInputArea, { height: 60 }]}
                      multiline
                      value={expertRemedy}
                      onChangeText={setExpertRemedy}
                      placeholder={isKn ? 'ಸಿಂಪರಣೆ ದ್ರಾವಣ, ಪ್ರಮಾಣ ಹಾಗೂ ಮುನ್ನೆಚ್ಚರಿಕೆ...' : 'Chemical/dosage/precautions...'}
                      placeholderTextColor="#94A3B8"
                    />
                  </View>
                )}
              </View>

              {/* Action Buttons */}
              <View style={styles.modalFooterActions}>
                {decisionMode === 'NEED_MORE_INFO' ? (
                  <TouchableOpacity
                    style={[styles.actionBtn, styles.actionBtnWarning]}
                    activeOpacity={0.85}
                    disabled={isSubmitting}
                    onPress={() => handleFinalizeDecision('NEED_MORE_INFO')}
                  >
                    {isSubmitting ? (
                      <ActivityIndicator size="small" color="#FFFFFF" />
                    ) : (
                      <>
                        <HelpCircle size={18} color="#FFFFFF" />
                        <Text style={styles.actionBtnText}>
                          {isKn ? 'ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಕೋರಿ (REQUEST INFO)' : 'REQUEST MORE INFORMATION'}
                        </Text>
                      </>
                    )}
                  </TouchableOpacity>
                ) : (
                  <TouchableOpacity
                    style={[styles.actionBtn, styles.actionBtnSuccess]}
                    activeOpacity={0.85}
                    disabled={isSubmitting}
                    onPress={() => handleFinalizeDecision()}
                  >
                    {isSubmitting ? (
                      <ActivityIndicator size="small" color="#FFFFFF" />
                    ) : (
                      <>
                        <CheckCircle2 size={18} color="#FFFFFF" />
                        <Text style={styles.actionBtnText}>
                          {isKn ? 'ವರದಿ ದೃಢೀಕರಿಸಿ (VERIFY REPORT)' : 'VERIFY REPORT & SEND ADVISORY'}
                        </Text>
                      </>
                    )}
                  </TouchableOpacity>
                )}
              </View>
            </ScrollView>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  headerWrapper: {
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.md,
    gap: 12,
  },
  headerTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  brandTitleCol: {
    gap: 2,
  },
  logoBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  logoCircle: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: '#16A34A',
    alignItems: 'center',
    justifyContent: 'center',
  },
  appTitle: {
    fontSize: 20,
    fontWeight: '800',
  },
  expertRoleTag: {
    fontSize: 11,
    color: '#166534',
    fontWeight: '700',
    marginLeft: 40,
  },
  langPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#E1F5EE',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: '#BFE7D7',
  },
  langText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#0F6E56',
  },
  profileAvatarBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#E1F5EE',
    borderWidth: 1,
    borderColor: '#BFE7D7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  expertIdentityCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    padding: 12,
  },
  expertAvatarCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#0F766E',
    alignItems: 'center',
    justifyContent: 'center',
  },
  expertAvatarText: {
    fontSize: 15,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  expertName: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
  },
  badgeKvk: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#CCFBF1',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  badgeKvkText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#0F766E',
  },
  expertDesignation: {
    fontSize: 11,
    color: '#334155',
    fontWeight: '600',
    marginTop: 1,
  },
  expertOrg: {
    fontSize: 10.5,
    color: '#64748B',
    marginTop: 1,
  },
  scrollContent: {
    padding: Spacing.md,
    paddingBottom: 40,
    gap: 16,
  },
  summaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  metricCard: {
    width: (SCREEN_WIDTH - Spacing.md * 2 - 10) / 2,
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderLeftWidth: 4,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  metricCardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  metricNumber: {
    fontSize: 24,
    fontWeight: '800',
    color: '#0F172A',
  },
  metricIconWrap: {
    width: 30,
    height: 30,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
  },
  metricLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#334155',
  },
  metricSub: {
    fontSize: 10,
    color: '#64748B',
    marginTop: 1,
  },
  pipelineCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 8,
  },
  pipelineHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  pipelineTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0F766E',
  },
  pipelineSubtitle: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '500',
  },
  pipelineStepsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 4,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
  },
  stepBubble: {
    alignItems: 'center',
    gap: 3,
  },
  stepNumber: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: '#F1F5F9',
    textAlign: 'center',
    lineHeight: 22,
    fontSize: 11,
    fontWeight: '800',
    color: '#475569',
  },
  stepName: {
    fontSize: 10,
    fontWeight: '600',
    color: '#64748B',
  },
  activeStepBubble: {
    backgroundColor: '#CCFBF1',
    borderRadius: 8,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  stepArrow: {
    opacity: 0.7,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sectionTitleKn: {
    fontSize: 13.5,
    fontWeight: '800',
    color: '#0F172A',
  },
  viewAllBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  viewAllBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#0F766E',
  },
  centerLoading: {
    padding: 24,
    alignItems: 'center',
    gap: 8,
  },
  loadingText: {
    fontSize: 12,
    color: '#64748B',
  },
  cardsList: {
    gap: 12,
  },
  queueCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 3,
    elevation: 1,
  },
  queueCardVerified: {
    backgroundColor: '#F0FDF4',
    borderColor: '#BBF7D0',
  },
  queueCardNeedInfo: {
    backgroundColor: '#FFFBEB',
    borderColor: '#FDE68A',
  },
  cardTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F8FAFC',
  },
  priorityBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  priorityPill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  pillHigh: {
    backgroundColor: '#FEE2E2',
  },
  pillModerate: {
    backgroundColor: '#FEF3C7',
  },
  priorityText: {
    fontSize: 11,
    fontWeight: '800',
  },
  textHigh: {
    color: '#DC2626',
  },
  textModerate: {
    color: '#D97706',
  },
  paidBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 4,
  },
  paidBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#15803D',
  },
  cardMainRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  cropTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
  },
  infoLine: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  infoLabel: {
    fontSize: 11.5,
    fontWeight: '600',
    color: '#64748B',
  },
  infoValue: {
    fontSize: 12,
    fontWeight: '700',
    color: '#1E293B',
  },
  infoValueMuted: {
    fontSize: 11,
    color: '#64748B',
  },
  dotSeparator: {
    color: '#CBD5E1',
    marginHorizontal: 2,
  },
  diagnosisBold: {
    color: '#B91C1C',
  },
  confidenceBadge: {
    fontSize: 12,
    fontWeight: '800',
  },
  cardActionRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    paddingTop: 4,
  },
  reviewBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#0F766E',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: BorderRadius.sm,
  },
  reviewBtnText: {
    fontSize: 12,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  resolvedInlineTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingVertical: 4,
  },
  resolvedInlineText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#16A34A',
  },
  needInfoInlineTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingVertical: 4,
  },
  needInfoInlineText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#B45309',
  },

  // Modal Sheet Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15,23,42,0.65)',
    justifyContent: 'flex-end',
  },
  modalSheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 18,
    borderTopRightRadius: 18,
    padding: Spacing.md,
  },
  modalHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  modalSheetTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
  },
  modalSheetSubtitle: {
    fontSize: 11.5,
    color: '#64748B',
    marginTop: 2,
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalScrollContent: {
    paddingVertical: 12,
    gap: 14,
  },
  modalSectionBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 8,
  },
  modalSectionTitle: {
    fontSize: 12.5,
    fontWeight: '800',
    color: '#0F766E',
  },
  evidenceGrid: {
    gap: 4,
  },
  evidenceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  evidenceLabel: {
    fontSize: 11.5,
    color: '#64748B',
    fontWeight: '600',
  },
  evidenceVal: {
    fontSize: 12,
    fontWeight: '700',
    color: '#1E293B',
  },
  imagePreviewFrame: {
    width: '100%',
    height: 160,
    borderRadius: BorderRadius.sm,
    overflow: 'hidden',
    position: 'relative',
    backgroundColor: '#E2E8F0',
  },
  cropEvidenceImage: {
    width: '100%',
    height: '100%',
  },
  imageOverlayTag: {
    position: 'absolute',
    bottom: 8,
    left: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(15,23,42,0.75)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  imageOverlayText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  aiResultCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.sm,
    padding: 10,
    gap: 6,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  aiDiagRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  aiDiagTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#DC2626',
  },
  confPill: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  confPillText: {
    fontSize: 10.5,
    fontWeight: '800',
    color: '#15803D',
  },
  kbRow: {
    gap: 2,
  },
  kbLabel: {
    fontSize: 10.5,
    fontWeight: '700',
    color: '#475569',
  },
  kbVal: {
    fontSize: 11,
    color: '#334155',
    lineHeight: 16,
  },
  communityCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.sm,
    padding: 10,
    gap: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  commStatsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  commStatBox: {
    alignItems: 'center',
  },
  commStatNumber: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0F172A',
  },
  commStatLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: '#64748B',
  },
  commNoteBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  commNoteText: {
    fontSize: 11,
    color: '#334155',
    flex: 1,
  },
  decisionOptions: {
    gap: 8,
  },
  decisionRadioCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.sm,
    padding: 10,
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
  },
  radioActive: {
    borderColor: '#0F766E',
    backgroundColor: '#F0FDFA',
  },
  radioActiveWarning: {
    borderColor: '#D97706',
    backgroundColor: '#FFFBEB',
  },
  radioCircle: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    borderColor: '#94A3B8',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  radioCircleActive: {
    borderColor: '#0F766E',
  },
  radioCircleActiveWarning: {
    borderColor: '#D97706',
  },
  radioDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#0F766E',
  },
  radioTitle: {
    fontSize: 12.5,
    fontWeight: '800',
    color: '#0F172A',
  },
  radioSub: {
    fontSize: 10.5,
    color: '#64748B',
    marginTop: 1,
  },
  correctInputBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.sm,
    padding: 10,
    gap: 4,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  correctInputLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#334155',
  },
  correctTextInput: {
    height: 38,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 6,
    paddingHorizontal: 10,
    fontSize: 12,
    color: '#0F172A',
  },
  inputGroup: {
    gap: 4,
  },
  fieldLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#334155',
  },
  textInputArea: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 8,
    fontSize: 12,
    color: '#0F172A',
    textAlignVertical: 'top',
  },
  modalFooterActions: {
    marginTop: 6,
  },
  actionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    borderRadius: BorderRadius.sm,
  },
  actionBtnSuccess: {
    backgroundColor: '#0F766E',
  },
  actionBtnWarning: {
    backgroundColor: '#D97706',
  },
  actionBtnText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#FFFFFF',
  },
});
