import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  Alert,
  Modal,
  ActivityIndicator,
  TextInput,
  RefreshControl,
  Dimensions,
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
  MapPin,
  ShieldCheck,
  FileCheck,
  X,
  FileText,
  AlertCircle,
  HelpCircle,
  Sparkles,
  Search,
  Filter,
  Users,
  ChevronRight,
  TrendingUp,
} from 'lucide-react-native';

const CROP_ASSET_IMAGES: Record<string, any> = {
  paddy: require('../../../assets/crops/paddy.jpg'),
  arecanut: require('../../../assets/crops/arecanut.jpg'),
  cardamom: require('../../../assets/crops/cardamom.jpg'),
  black_pepper: require('../../../assets/crops/black_pepper.jpg'),
  coconut: require('../../../assets/crops/coconut.jpg'),
  ginger: require('../../../assets/crops/ginger.jpg'),
  turmeric: require('../../../assets/crops/turmeric.jpg'),
};

const CROP_FILTERS = [
  { key: 'all', labelEn: 'All Crops', labelKn: 'ಎಲ್ಲ ಬೆಳೆಗಳು' },
  { key: 'paddy', labelEn: 'Paddy', labelKn: 'ಭತ್ತ' },
  { key: 'arecanut', labelEn: 'Arecanut', labelKn: 'ಅಡಿಕೆ' },
  { key: 'cardamom', labelEn: 'Cardamom', labelKn: 'ಏಲಕ್ಕಿ' },
  { key: 'black_pepper', labelEn: 'Black Pepper', labelKn: 'ಕಾಳುಮೆಣಸು' },
];

export const ExpertQueueScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const { language } = useLanguage();
  const { user } = useAuth();
  const isKn = language === 'kn';

  const [verificationRequests, setVerificationRequests] = useState<ExpertQueueItemData[]>([]);
  const [isLoadingQueue, setIsLoadingQueue] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Filters
  const [selectedCropFilter, setSelectedCropFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'PENDING' | 'HIGH' | 'VERIFIED' | 'NEED_MORE_INFO'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Review Modal State
  const [selectedRequest, setSelectedRequest] = useState<ExpertQueueItemData | null>(null);
  const [decisionMode, setDecisionMode] = useState<'CONFIRM' | 'CORRECT' | 'NEED_MORE_INFO'>('CONFIRM');
  const [correctedDiagnosis, setCorrectedDiagnosis] = useState('');
  const [expertNotes, setExpertNotes] = useState('');
  const [expertRemedy, setExpertRemedy] = useState('');
  const [isSubmittingDecision, setIsSubmittingDecision] = useState(false);

  // Fetch pending verification requests from backend
  const loadRequests = useCallback(async () => {
    setIsLoadingQueue(true);
    try {
      const data = await fetchExpertQueue(user?.phone, user?.id);
      setVerificationRequests(data?.items || []);
    } catch {
      setVerificationRequests([]);
    } finally {
      setIsLoadingQueue(false);
      setRefreshing(false);
    }
  }, [user?.phone, user?.id]);

  useEffect(() => {
    loadRequests();
  }, [loadRequests]);

  const onRefresh = () => {
    setRefreshing(true);
    loadRequests();
  };

  // Open review modal with pre-populated evidence
  const handleOpenReview = (item: ExpertQueueItemData) => {
    setSelectedRequest(item);
    setDecisionMode('CONFIRM');
    setCorrectedDiagnosis('');
    setExpertNotes(
      isKn
        ? `ತಜ್ಞರ ಪರಿಶೀಲನೆ ಪೂರ್ಣಗೊಂಡಿದೆ. ${item.latest_diagnosis?.predicted_class_kn || item.diagnosis} ರೋಗ ಲಕ್ಷಣಗಳು ಅಧಿಕೃತವಾಗಿ ದೃಢಪಟ್ಟಿವೆ.`
        : `Verified diagnosis. Laboratory and visual symptoms confirm ${item.diagnosis}. Recommended immediate treatment.`
    );
    setExpertRemedy(
      item.scientific_info?.recommended_spray ||
        (isKn ? '1% ಬೋರ್ಡೋ ದ್ರಾವಣವನ್ನು ಗಿಡದ ಬುಡ ಹಾಗೂ ಗೊನೆಗಳಿಗೆ ಸಿಂಪಡಿಸಿ.' : 'Apply 1% Bordeaux mixture on fruit bunches.')
    );
  };

  // Submit expert decision
  const handleFinalizeDecision = async (overrideMode?: 'NEED_MORE_INFO') => {
    if (!selectedRequest) return;
    const mode = overrideMode || decisionMode;
    setIsSubmittingDecision(true);

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
              ? 'ರೈತರಿಗೆ ಹೆಚ್ಚುವರಿ ನಿಕಟ ಛಾಯಾಚಿತ್ರ ಹಾಗೂ ವಿವರ ಒದಗಿಸಲು ಸೂಚನೆ ರವಾನಿಸಲಾಗಿದೆ.'
              : 'Status updated to REQUIRES_MORE_INFORMATION. Request sent to farmer.')
          : (isKn
              ? 'ದೃಢೀಕರಣ ಪೂರ್ಣಗೊಂಡಿದೆ. ರೈತರಿಗೆ ಪರಿಶೀಲಿಸಿದ ವೈಜ್ಞಾನಿಕ ಕೃಷಿ ಸಲಹೆ ರವಾನೆಯಾಗಿದೆ.'
              : 'Status updated to VERIFIED. Verified advisory dispatched to farmer.')
      );

      setSelectedRequest(null);
      loadRequests();
    } catch {
      Alert.alert(isKn ? 'ದೋಷ' : 'Error', 'Failed to save decision.');
    } finally {
      setIsSubmittingDecision(false);
    }
  };

  // Filter items
  const filteredRequests = verificationRequests.filter((item) => {
    // Crop filter
    if (selectedCropFilter !== 'all' && item.crop_code !== selectedCropFilter) {
      return false;
    }
    // Status filter
    if (statusFilter === 'PENDING' && item.status !== 'PENDING') return false;
    if (statusFilter === 'HIGH' && (item.priority !== 'HIGH' || item.status !== 'PENDING')) return false;
    if (statusFilter === 'VERIFIED' && item.status !== 'VERIFIED') return false;
    if (statusFilter === 'NEED_MORE_INFO' && item.status !== 'NEED_MORE_INFO') return false;

    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchName = item.farmer_name?.toLowerCase().includes(q);
      const matchCrop = item.crop_name?.toLowerCase().includes(q) || item.crop_name_kn?.toLowerCase().includes(q);
      const matchDiag = item.diagnosis?.toLowerCase().includes(q);
      const matchLoc = item.location?.toLowerCase().includes(q);
      if (!matchName && !matchCrop && !matchDiag && !matchLoc) return false;
    }

    return true;
  });

  const pendingCount = verificationRequests.filter((r) => r.status === 'PENDING').length;

  return (
    <View style={styles.container}>
      {/* Top Header */}
      <View style={[styles.header, { paddingTop: Math.max(insets.top, 12) + Spacing.xs }]}>
        <View style={styles.headerTitleRow}>
          <View style={styles.headerIconCircle}>
            <Microscope size={20} color="#FFFFFF" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.headerTitle}>
              {isKn ? 'ತಜ್ಞರ ಪರಿಶೀಲನೆ ಕ್ಯೂ (Verification Queue)' : 'Expert Verification Queue'}
            </Text>
            <Text style={styles.headerSub}>
              {isKn ? `${pendingCount} ಹೊಸ ಪರಿಶೀಲನೆ ವಿನಂತಿಗಳು ಲಭ್ಯವಿವೆ` : `${pendingCount} Pending review requests`}
            </Text>
          </View>
        </View>

        {/* Search Input Bar */}
        <View style={styles.searchBar}>
          <Search size={16} color="#64748B" />
          <TextInput
            style={styles.searchInput}
            placeholder={isKn ? 'ರೈತ, ಬೆಳೆ ಅಥವಾ ರೋಗ ಹುಡುಕಿ...' : 'Search by farmer, crop, or disease...'}
            placeholderTextColor="#94A3B8"
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
              <X size={16} color="#64748B" />
            </TouchableOpacity>
          )}
        </View>

        {/* Crop Catalog Chips */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.cropChipsRow}>
          {CROP_FILTERS.map((crop) => {
            const isSelected = selectedCropFilter === crop.key;
            return (
              <TouchableOpacity
                key={crop.key}
                style={[styles.cropChip, isSelected && styles.cropChipActive]}
                onPress={() => setSelectedCropFilter(crop.key)}
                activeOpacity={0.8}
              >
                <Text style={[styles.cropChipText, isSelected && styles.cropChipTextActive]}>
                  {isKn ? crop.labelKn : crop.labelEn}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {/* Status / Priority Filter Tabs */}
        <View style={styles.statusTabsRow}>
          <TouchableOpacity
            style={[styles.statusTab, statusFilter === 'ALL' && styles.statusTabActive]}
            onPress={() => setStatusFilter('ALL')}
          >
            <Text style={[styles.statusTabText, statusFilter === 'ALL' && styles.statusTabTextActive]}>
              {isKn ? 'ಎಲ್ಲವೂ' : 'All'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.statusTab, statusFilter === 'HIGH' && styles.statusTabActiveHigh]}
            onPress={() => setStatusFilter('HIGH')}
          >
            <Text style={[styles.statusTabText, statusFilter === 'HIGH' && { color: '#DC2626', fontWeight: '800' }]}>
              {isKn ? '🔴 ತುರ್ತು' : '🔴 High'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.statusTab, statusFilter === 'PENDING' && styles.statusTabActive]}
            onPress={() => setStatusFilter('PENDING')}
          >
            <Text style={[styles.statusTabText, statusFilter === 'PENDING' && styles.statusTabTextActive]}>
              {isKn ? 'ಬಾಕಿ (Pending)' : 'Pending'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.statusTab, statusFilter === 'VERIFIED' && styles.statusTabActive]}
            onPress={() => setStatusFilter('VERIFIED')}
          >
            <Text style={[styles.statusTabText, statusFilter === 'VERIFIED' && styles.statusTabTextActive]}>
              {isKn ? 'ದೃಢೀಕೃತ' : 'Verified'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Main List */}
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.primary]} />}
      >
        {isLoadingQueue && !refreshing ? (
          <View style={styles.centerLoading}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingText}>
              {isKn ? 'ವರದಿಗಳನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...' : 'Loading verification queue...'}
            </Text>
          </View>
        ) : filteredRequests.length === 0 ? (
          <View style={styles.emptyContainer}>
            <FileText size={40} color="#94A3B8" />
            <Text style={styles.emptyTitle}>
              {isKn ? 'ಯಾವುದೇ ವರದಿಗಳು ಕಂಡುಬಂದಿಲ್ಲ' : 'No Verification Requests Found'}
            </Text>
            <Text style={styles.emptySubtitle}>
              {isKn ? 'ಆಯ್ಕೆಮಾಡಿದ ಫಿಲ್ಟರ್‌ಗೆ ಹೊಂದುವ ವಿನಂತಿಗಳಿಲ್ಲ.' : 'Try adjusting the crop or status filters.'}
            </Text>
          </View>
        ) : (
          <View style={styles.cardsList}>
            {filteredRequests.map((item) => {
              const isHigh = item.priority === 'HIGH';
              const isVerified = item.status === 'VERIFIED';
              const isNeedInfo = item.status === 'NEED_MORE_INFO';
              const confidencePct = Math.round(
                (item.ai_confidence ?? item.latest_diagnosis?.confidence ?? 0.75) * 100
              );

              return (
                <View
                  key={item.id}
                  style={[
                    styles.requestCard,
                    isVerified && styles.requestCardVerified,
                    isNeedInfo && styles.requestCardNeedInfo,
                  ]}
                >
                  {/* Top Bar: Priority Badge + Fee Status */}
                  <View style={styles.cardHeader}>
                    <View style={[styles.priorityPill, isHigh ? styles.pillHigh : styles.pillNormal]}>
                      <Text style={[styles.priorityPillText, isHigh ? styles.textHigh : styles.textNormal]}>
                        {isHigh
                          ? (isKn ? '🔴 ತುರ್ತು ಆದ್ಯತೆ (High Priority)' : '🔴 High Priority')
                          : (isKn ? '🟡 ಸಾಮಾನ್ಯ ಆದ್ಯತೆ' : '🟡 Normal Priority')}
                      </Text>
                    </View>
                    <View style={styles.paymentBadge}>
                      <ShieldCheck size={12} color="#15803D" />
                      <Text style={styles.paymentBadgeText}>₹49 Paid</Text>
                    </View>
                  </View>

                  {/* Card Content Row */}
                  <View style={styles.cardBody}>
                    <View style={{ flex: 1, gap: 5 }}>
                      <Text style={styles.cropHeader}>
                        {isKn && item.crop_name_kn
                          ? `${item.crop_name_kn} (${item.crop_name})`
                          : (item.crop_name || 'Crop')}
                      </Text>

                      <View style={styles.metaRow}>
                        <Text style={styles.metaLabel}>{isKn ? 'ರೈತರು:' : 'Farmer:'}</Text>
                        <Text style={styles.metaValue}>{item.farmer_name || 'Farmer'}</Text>
                        <Text style={styles.dot}>•</Text>
                        <MapPin size={11} color="#64748B" />
                        <Text style={styles.metaLocation}>{item.location || 'Ujire'}</Text>
                      </View>

                      <View style={styles.metaRow}>
                        <Text style={styles.metaLabel}>{isKn ? 'AI ರೋಗ ನಿರ್ಣಯ:' : 'AI Diagnosis:'}</Text>
                        <Text style={[styles.metaValue, styles.diseaseHighlight]}>
                          {isKn && item.latest_diagnosis?.predicted_class_kn
                            ? item.latest_diagnosis.predicted_class_kn
                            : (item.diagnosis || item.latest_diagnosis?.predicted_class || 'Disease')}
                        </Text>
                      </View>

                      <View style={styles.metaRow}>
                        <Text style={styles.metaLabel}>{isKn ? 'AI ಖಚಿತತೆ (Confidence):' : 'AI Confidence:'}</Text>
                        <Text style={[styles.confidenceText, { color: confidencePct > 75 ? '#16A34A' : '#D97706' }]}>
                          {confidencePct}%
                        </Text>
                      </View>

                      {item.corroboration_summary && (
                        <View style={styles.corroborationSnippet}>
                          <Users size={12} color="#0F766E" />
                          <Text style={styles.corroborationText}>
                            {item.corroboration_summary.agreed_count} of {item.corroboration_summary.total_count} farmers agreed
                          </Text>
                        </View>
                      )}
                    </View>
                  </View>

                  {/* Card Footer: Action */}
                  <View style={styles.cardFooter}>
                    {isVerified ? (
                      <View style={styles.verifiedTag}>
                        <CheckCircle2 size={16} color="#16A34A" />
                        <Text style={styles.verifiedTagText}>
                          {isKn ? 'ತಜ್ಞರಿಂದ ದೃಢೀಕರಿಸಲ್ಪಟ್ಟಿದೆ ✓' : 'Expert Verified ✓'}
                        </Text>
                      </View>
                    ) : isNeedInfo ? (
                      <View style={styles.needInfoTag}>
                        <HelpCircle size={16} color="#B45309" />
                        <Text style={styles.needInfoTagText}>
                          {isKn ? 'ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಕೋರಲಾಗಿದೆ ℹ️' : 'More Info Requested ℹ️'}
                        </Text>
                      </View>
                    ) : (
                      <TouchableOpacity
                        style={styles.reviewButton}
                        activeOpacity={0.85}
                        onPress={() => handleOpenReview(item)}
                      >
                        <FileText size={15} color="#FFFFFF" />
                        <Text style={styles.reviewButtonText}>
                          {isKn ? 'ವರದಿ ಪರಿಶೀಲಿಸಿ' : 'Review Report'}
                        </Text>
                        <ChevronRight size={15} color="#FFFFFF" />
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
      {/* Full Clinical Evidence Review Modal ("ವರದಿ ಪರಿಶೀಲಿಸಿ") */}
      {/* ============================================================== */}
      <Modal
        visible={!!selectedRequest}
        transparent
        animationType="slide"
        onRequestClose={() => setSelectedRequest(null)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalSheet, { maxHeight: '92%' }]}>
            {/* Header */}
            <View style={styles.modalHeaderRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.modalTitle}>
                  {isKn ? 'ವರದಿ ಪರಿಶೀಲನೆ (Clinical Evidence Review)' : 'Clinical Evidence Review'}
                </Text>
                <Text style={styles.modalSub}>
                  {selectedRequest?.farmer_name} • {selectedRequest?.crop_name} • {selectedRequest?.location}
                </Text>
              </View>
              <TouchableOpacity
                onPress={() => setSelectedRequest(null)}
                style={styles.modalCloseBtn}
                activeOpacity={0.7}
              >
                <X size={20} color="#475569" />
              </TouchableOpacity>
            </View>

            <ScrollView contentContainerStyle={styles.modalScroll} showsVerticalScrollIndicator={false}>
              {/* Section 1: Crop Health Evidence */}
              <View style={styles.sectionCard}>
                <Text style={styles.sectionHeading}>
                  {isKn ? '1. ಬೆಳೆ ಆರೋಗ್ಯ ಸಾಕ್ಷ್ಯ (Crop Health Evidence):' : '1. Crop Health Evidence:'}
                </Text>

                <View style={styles.dataGrid}>
                  <View style={styles.dataRow}>
                    <Text style={styles.dataLabel}>{isKn ? 'ಬೆಳೆ (Crop):' : 'Crop:'}</Text>
                    <Text style={styles.dataValue}>
                      {isKn && selectedRequest?.crop_name_kn
                        ? `${selectedRequest.crop_name_kn} (${selectedRequest.crop_name})`
                        : (selectedRequest?.crop_name || 'Crop')}
                    </Text>
                  </View>

                  <View style={styles.dataRow}>
                    <Text style={styles.dataLabel}>{isKn ? 'ರೈತರು (Farmer):' : 'Farmer:'}</Text>
                    <Text style={styles.dataValue}>{selectedRequest?.farmer_name || 'Mallikarjuna G.'}</Text>
                  </View>

                  <View style={styles.dataRow}>
                    <Text style={styles.dataLabel}>{isKn ? 'ಸ್ಥಳ (Location):' : 'Location:'}</Text>
                    <Text style={styles.dataValue}>{selectedRequest?.location || 'Ujire'}</Text>
                  </View>

                  <View style={styles.dataRow}>
                    <Text style={styles.dataLabel}>{isKn ? 'ಸಲ್ಲಿಸಿದ ದಿನಾಂಕ (Submitted):' : 'Submitted:'}</Text>
                    <Text style={styles.dataValue}>
                      {selectedRequest?.requested_at
                        ? new Date(selectedRequest.requested_at).toLocaleString()
                        : '26 Sept 2026, 12:45 PM'}
                    </Text>
                  </View>
                </View>
              </View>

              {/* Section 2: Actual Submitted Photo */}
              <View style={styles.sectionCard}>
                <Text style={styles.sectionHeading}>
                  {isKn ? '2. ರೈತರು ಸಲ್ಲಿಸಿದ ಫೋಟೋ (Submitted Leaf Photo):' : '2. Submitted Leaf/Crop Photo:'}
                </Text>

                <View style={styles.photoContainer}>
                  <Image
                    source={
                      selectedRequest?.crop_code && CROP_ASSET_IMAGES[selectedRequest.crop_code]
                        ? CROP_ASSET_IMAGES[selectedRequest.crop_code]
                        : require('../../../assets/crops/crop_scan_hero.jpg')
                    }
                    style={styles.photo}
                    resizeMode="cover"
                  />
                  <View style={styles.photoTag}>
                    <ShieldCheck size={12} color="#FFFFFF" />
                    <Text style={styles.photoTagText}>
                      {isKn ? 'ಅಸಲಿ ಸಾಕ್ಷಿ ಫೋಟೋ' : 'Original Submitted Photo'}
                    </Text>
                  </View>
                </View>
              </View>

              {/* Section 3: AI Analysis */}
              <View style={styles.sectionCard}>
                <Text style={styles.sectionHeading}>
                  {isKn ? '3. AI ವಿಶ್ಲೇಷಣೆ & ವೈಜ್ಞಾನಿಕ ಮಾಹಿತಿ (AI Analysis):' : '3. AI Analysis & KB Evidence:'}
                </Text>

                <View style={styles.aiBox}>
                  <View style={styles.aiHeader}>
                    <Text style={styles.aiDiseaseTitle}>
                      {selectedRequest?.diagnosis || selectedRequest?.latest_diagnosis?.predicted_class || 'Disease'}
                    </Text>
                    <View style={styles.confBadge}>
                      <Text style={styles.confBadgeText}>
                        {Math.round((selectedRequest?.ai_confidence ?? 0.73) * 100)}% Confidence
                      </Text>
                    </View>
                  </View>

                  <View style={styles.kbItem}>
                    <Text style={styles.kbItemLabel}>{isKn ? 'ರೋಗಕಾರಕ (Causal Organism):' : 'Causal Agent:'}</Text>
                    <Text style={styles.kbItemText}>
                      {selectedRequest?.scientific_info?.causal_agent || 'Phytophthora meadii McRae'}
                    </Text>
                  </View>

                  <View style={styles.kbItem}>
                    <Text style={styles.kbItemLabel}>{isKn ? 'ಲಕ್ಷಣಗಳು (Symptoms):' : 'Key Symptoms:'}</Text>
                    <Text style={styles.kbItemText}>
                      {selectedRequest?.scientific_info?.symptoms || 'Water-soaked lesions on unripe nuts with heavy rotting.'}
                    </Text>
                  </View>
                </View>
              </View>

              {/* Section 4: Community Evidence */}
              <View style={styles.sectionCard}>
                <Text style={styles.sectionHeading}>
                  {isKn ? '4. ಸಮುದಾಯ ದೃಢೀಕರಣ ಸಾಕ್ಷ್ಯ (Community Evidence):' : '4. Community Corroboration Evidence:'}
                </Text>

                <View style={styles.commBox}>
                  <View style={styles.commGrid}>
                    <View style={styles.commCol}>
                      <Text style={styles.commNum}>{selectedRequest?.corroboration_summary?.total_count || 4}</Text>
                      <Text style={styles.commLbl}>{isKn ? 'ವರದಿಗಳು' : 'Peer Reports'}</Text>
                    </View>
                    <View style={styles.commCol}>
                      <Text style={[styles.commNum, { color: '#16A34A' }]}>
                        {selectedRequest?.corroboration_summary?.agreed_count || 3}
                      </Text>
                      <Text style={styles.commLbl}>{isKn ? 'ಸಹಮತ' : 'Agree'}</Text>
                    </View>
                    <View style={styles.commCol}>
                      <Text style={[styles.commNum, { color: '#DC2626' }]}>
                        {selectedRequest?.corroboration_summary?.disagreed_count || 1}
                      </Text>
                      <Text style={styles.commLbl}>{isKn ? 'ಭಿನ್ನಾಭಿಪ್ರಾಯ' : 'Disagree'}</Text>
                    </View>
                  </View>

                  <View style={styles.commDetails}>
                    <Users size={14} color="#0F766E" />
                    <Text style={styles.commDetailsText}>
                      {isKn
                        ? 'ಉಜಿರೆ ಗ್ರಾಮದ 3 ರೈತರು ಇದೇ ರೀತಿಯ ರೋಗಲಕ್ಷಣಗಳನ್ನು ವರದಿ ಮಾಡಿದ್ದಾರೆ (ಹೋಲಿಕೆ: ಅಧಿಕ).'
                        : '3 local farmers confirmed matching symptoms in neighbor farms. Peer Similarity: High.'}
                    </Text>
                  </View>
                </View>
              </View>

              {/* Section 5: Trust Ladder Progression */}
              <View style={styles.sectionCard}>
                <Text style={styles.sectionHeading}>
                  {isKn ? '5. ನಂಬಿಕೆಯ ಏಣಿಯ ಸ್ಥಿತಿ (Trust Ladder Status):' : '5. Trust Ladder Progression:'}
                </Text>
                <View style={styles.ladderFlow}>
                  <View style={styles.ladderStep}>
                    <CheckCircle2 size={16} color="#16A34A" />
                    <Text style={styles.ladderStepText}>AI ANALYSED</Text>
                  </View>
                  <Text style={styles.ladderArrow}>→</Text>
                  <View style={styles.ladderStep}>
                    <CheckCircle2 size={16} color="#16A34A" />
                    <Text style={styles.ladderStepText}>CORROBORATED</Text>
                  </View>
                  <Text style={styles.ladderArrow}>→</Text>
                  <View style={[styles.ladderStep, styles.ladderStepActive]}>
                    <Microscope size={16} color="#0F766E" />
                    <Text style={[styles.ladderStepText, { color: '#0F766E', fontWeight: '800' }]}>
                      EXPERT VERIFY
                    </Text>
                  </View>
                </View>
              </View>

              {/* Section 6: Expert Clinical Decision */}
              <View style={styles.sectionCard}>
                <Text style={styles.sectionHeading}>
                  {isKn ? '6. ತಜ್ಞರ ನಿರ್ಧಾರ (Expert Assessment):' : '6. Expert Assessment & Decision:'}
                </Text>

                <View style={styles.radioGroup}>
                  {/* Confirm */}
                  <TouchableOpacity
                    style={[styles.radioItem, decisionMode === 'CONFIRM' && styles.radioItemActive]}
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
                      <Text style={styles.radioDesc}>
                        {isKn
                          ? 'AI ಸೂಚಿಸಿದ ರೋಗದ ಮಾದರಿ ನಿಖರವಾಗಿದೆ ಎಂದು ಅನುಮೋದಿಸಿ.'
                          : 'Validate that the AI predicted diagnosis is medically accurate.'}
                      </Text>
                    </View>
                  </TouchableOpacity>

                  {/* Correct */}
                  <TouchableOpacity
                    style={[styles.radioItem, decisionMode === 'CORRECT' && styles.radioItemActive]}
                    onPress={() => setDecisionMode('CORRECT')}
                    activeOpacity={0.8}
                  >
                    <View style={[styles.radioCircle, decisionMode === 'CORRECT' && styles.radioCircleActive]}>
                      {decisionMode === 'CORRECT' && <View style={styles.radioDot} />}
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.radioTitle}>
                        {isKn ? 'ರೋಗನಿರ್ಣಯ ತಿದ್ದಿ (Correct Diagnosis)' : 'Correct / Override Diagnosis'}
                      </Text>
                      <Text style={styles.radioDesc}>
                        {isKn
                          ? 'AI ರೋಗ ತಪ್ಪಾಗಿದ್ದು, ಪರ್ಯಾಯ ಸರಿಯಾದ ರೋಗವನ್ನು ದಾಖಲಿಸಿ.'
                          : 'Override AI prediction with the correct scientific pathogen.'}
                      </Text>
                    </View>
                  </TouchableOpacity>

                  {decisionMode === 'CORRECT' && (
                    <View style={styles.overrideInputBox}>
                      <Text style={styles.overrideInputLabel}>
                        {isKn ? 'ಸರಿಯಾದ ರೋಗದ ಹೆಸರು ನಮೂದಿಸಿ:' : 'Enter Correct Diagnosis:'}
                      </Text>
                      <TextInput
                        style={styles.overrideInput}
                        placeholder={isKn ? 'ಉದಾ: ಸುಳಿ ಕೊಳೆ (Bud Rot / Anabe)' : 'e.g. Bud Rot / Foot Rot'}
                        placeholderTextColor="#94A3B8"
                        value={correctedDiagnosis}
                        onChangeText={setCorrectedDiagnosis}
                      />
                    </View>
                  )}

                  {/* Need More Info */}
                  <TouchableOpacity
                    style={[styles.radioItem, decisionMode === 'NEED_MORE_INFO' && styles.radioItemWarning]}
                    onPress={() => setDecisionMode('NEED_MORE_INFO')}
                    activeOpacity={0.8}
                  >
                    <View style={[styles.radioCircle, decisionMode === 'NEED_MORE_INFO' && styles.radioCircleWarning]}>
                      {decisionMode === 'NEED_MORE_INFO' && <View style={[styles.radioDot, { backgroundColor: '#D97706' }]} />}
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.radioTitle}>
                        {isKn ? 'ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಅಗತ್ಯವಿದೆ (Needs More Information)' : 'Needs More Information'}
                      </Text>
                      <Text style={styles.radioDesc}>
                        {isKn
                          ? 'ಸ್ಪಷ್ಟ ಫೋಟೋ ಅಥವಾ ಹೆಚ್ಚುವರಿ ಲಕ್ಷಣಗಳ ವಿವರ ಒದಗಿಸಲು ಕೋರಿ.'
                          : 'Request clearer close-up photograph of leaf lesion or collar.'}
                      </Text>
                    </View>
                  </TouchableOpacity>
                </View>
              </View>

              {/* Section 7: Notes & Prescription */}
              <View style={styles.sectionCard}>
                <Text style={styles.sectionHeading}>
                  {isKn ? '7. ತಜ್ಞರ ಟಿಪ್ಪಣಿ & ಸಿಂಪರಣಾ ಶಿಫಾರಸು (Expert Advice):' : '7. Expert Notes & Scientific Advice:'}
                </Text>

                <View style={styles.fieldGroup}>
                  <Text style={styles.fieldTitle}>
                    {isKn ? 'ತಜ್ಞರ ಟಿಪ್ಪಣಿ (Expert Clinical Observations):' : 'Expert Observations:'}
                  </Text>
                  <TextInput
                    style={[styles.fieldArea, { height: 75 }]}
                    multiline
                    value={expertNotes}
                    onChangeText={setExpertNotes}
                    placeholder={isKn ? 'ವೈಜ್ಞಾನಿಕ ವಿವರಣೆ...' : 'Enter professional observations...'}
                    placeholderTextColor="#94A3B8"
                  />
                </View>

                {decisionMode !== 'NEED_MORE_INFO' && (
                  <View style={[styles.fieldGroup, { marginTop: 10 }]}>
                    <Text style={styles.fieldTitle}>
                      {isKn ? 'ವೈಜ್ಞಾನಿಕ ಸಿಂಪರಣಾ ಕ್ರಮ (Recommended Treatment):' : 'Recommended Spray / Treatment:'}
                    </Text>
                    <TextInput
                      style={[styles.fieldArea, { height: 60 }]}
                      multiline
                      value={expertRemedy}
                      onChangeText={setExpertRemedy}
                      placeholder={isKn ? 'ದ್ರಾವಣ ಪ್ರಮಾಣ ಹಾಗೂ ಕ್ರಮ...' : 'Prescribed chemical / organic dosage...'}
                      placeholderTextColor="#94A3B8"
                    />
                  </View>
                )}
              </View>

              {/* Modal Bottom Actions */}
              <View style={styles.modalActions}>
                {decisionMode === 'NEED_MORE_INFO' ? (
                  <TouchableOpacity
                    style={[styles.mainActionBtn, styles.mainActionWarning]}
                    activeOpacity={0.85}
                    disabled={isSubmittingDecision}
                    onPress={() => handleFinalizeDecision('NEED_MORE_INFO')}
                  >
                    {isSubmittingDecision ? (
                      <ActivityIndicator size="small" color="#FFFFFF" />
                    ) : (
                      <>
                        <HelpCircle size={18} color="#FFFFFF" />
                        <Text style={styles.mainActionText}>
                          {isKn ? 'ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಕೋರಿ (REQUEST INFO)' : 'REQUEST MORE INFORMATION'}
                        </Text>
                      </>
                    )}
                  </TouchableOpacity>
                ) : (
                  <TouchableOpacity
                    style={[styles.mainActionBtn, styles.mainActionSuccess]}
                    activeOpacity={0.85}
                    disabled={isSubmittingDecision}
                    onPress={() => handleFinalizeDecision()}
                  >
                    {isSubmittingDecision ? (
                      <ActivityIndicator size="small" color="#FFFFFF" />
                    ) : (
                      <>
                        <CheckCircle2 size={18} color="#FFFFFF" />
                        <Text style={styles.mainActionText}>
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
    backgroundColor: Colors.background,
  },
  header: {
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.sm,
    gap: 10,
  },
  headerTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  headerIconCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#16A34A',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  headerSub: {
    fontSize: 11.5,
    color: '#64748B',
    marginTop: 1,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F1F5F9',
    borderRadius: BorderRadius.sm,
    paddingHorizontal: 12,
    height: 38,
  },
  searchInput: {
    flex: 1,
    fontSize: 12.5,
    color: '#0F172A',
  },
  cropChipsRow: {
    gap: 6,
    paddingVertical: 2,
  },
  cropChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  cropChipActive: {
    backgroundColor: '#0F6E56',
    borderColor: '#0F6E56',
  },
  cropChipText: {
    fontSize: 11.5,
    fontWeight: '600',
    color: '#475569',
  },
  cropChipTextActive: {
    color: '#FFFFFF',
    fontWeight: '800',
  },
  statusTabsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingTop: 4,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
  },
  statusTab: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    backgroundColor: '#F8FAFC',
  },
  statusTabActive: {
    backgroundColor: '#DCFCE7',
  },
  statusTabActiveHigh: {
    backgroundColor: '#FEE2E2',
  },
  statusTabText: {
    fontSize: 11.5,
    fontWeight: '600',
    color: '#64748B',
  },
  statusTabTextActive: {
    color: '#166534',
    fontWeight: '800',
  },
  scrollContent: {
    padding: Spacing.md,
    paddingBottom: 40,
  },
  centerLoading: {
    padding: 30,
    alignItems: 'center',
    gap: 8,
  },
  loadingText: {
    fontSize: 12,
    color: '#64748B',
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
    gap: 8,
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#334155',
  },
  emptySubtitle: {
    fontSize: 12,
    color: '#64748B',
    textAlign: 'center',
  },
  cardsList: {
    gap: 12,
  },
  requestCard: {
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
  requestCardVerified: {
    backgroundColor: '#F0FDF4',
    borderColor: '#BBF7D0',
  },
  requestCardNeedInfo: {
    backgroundColor: '#FFFBEB',
    borderColor: '#FDE68A',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F8FAFC',
  },
  priorityPill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  pillHigh: {
    backgroundColor: '#FEE2E2',
  },
  pillNormal: {
    backgroundColor: '#FEF3C7',
  },
  priorityPillText: {
    fontSize: 11,
    fontWeight: '800',
  },
  textHigh: {
    color: '#DC2626',
  },
  textNormal: {
    color: '#D97706',
  },
  paymentBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 4,
  },
  paymentBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#15803D',
  },
  cardBody: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  cropHeader: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaLabel: {
    fontSize: 11.5,
    fontWeight: '600',
    color: '#64748B',
  },
  metaValue: {
    fontSize: 12,
    fontWeight: '700',
    color: '#1E293B',
  },
  metaLocation: {
    fontSize: 11,
    color: '#64748B',
  },
  dot: {
    color: '#CBD5E1',
    marginHorizontal: 2,
  },
  diseaseHighlight: {
    color: '#DC2626',
  },
  confidenceText: {
    fontSize: 12,
    fontWeight: '800',
  },
  corroborationSnippet: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#F0FDFA',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    marginTop: 2,
  },
  corroborationText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#0F766E',
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    paddingTop: 4,
  },
  reviewButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#0F766E',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: BorderRadius.sm,
  },
  reviewButtonText: {
    fontSize: 12.5,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  verifiedTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingVertical: 4,
  },
  verifiedTagText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#16A34A',
  },
  needInfoTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingVertical: 4,
  },
  needInfoTagText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#B45309',
  },

  // Modal Styles
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
  modalTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
  },
  modalSub: {
    fontSize: 11.5,
    color: '#64748B',
    marginTop: 2,
  },
  modalCloseBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalScroll: {
    paddingVertical: 12,
    gap: 14,
  },
  sectionCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 8,
  },
  sectionHeading: {
    fontSize: 12.5,
    fontWeight: '800',
    color: '#0F766E',
  },
  dataGrid: {
    gap: 4,
  },
  dataRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  dataLabel: {
    fontSize: 11.5,
    color: '#64748B',
    fontWeight: '600',
  },
  dataValue: {
    fontSize: 12,
    fontWeight: '700',
    color: '#1E293B',
  },
  photoContainer: {
    width: '100%',
    height: 160,
    borderRadius: BorderRadius.sm,
    overflow: 'hidden',
    position: 'relative',
    backgroundColor: '#E2E8F0',
  },
  photo: {
    width: '100%',
    height: '100%',
  },
  photoTag: {
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
  photoTagText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  aiBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.sm,
    padding: 10,
    gap: 6,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  aiHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  aiDiseaseTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#DC2626',
  },
  confBadge: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  confBadgeText: {
    fontSize: 10.5,
    fontWeight: '800',
    color: '#15803D',
  },
  kbItem: {
    gap: 2,
  },
  kbItemLabel: {
    fontSize: 10.5,
    fontWeight: '700',
    color: '#475569',
  },
  kbItemText: {
    fontSize: 11,
    color: '#334155',
    lineHeight: 16,
  },
  commBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.sm,
    padding: 10,
    gap: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  commGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  commCol: {
    alignItems: 'center',
  },
  commNum: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0F172A',
  },
  commLbl: {
    fontSize: 10,
    fontWeight: '600',
    color: '#64748B',
  },
  commDetails: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  commDetailsText: {
    fontSize: 11,
    color: '#334155',
    flex: 1,
  },
  ladderFlow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
    padding: 10,
    borderRadius: BorderRadius.sm,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  ladderStep: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  ladderStepActive: {
    backgroundColor: '#CCFBF1',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  ladderStepText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#475569',
  },
  ladderArrow: {
    color: '#94A3B8',
    fontWeight: '800',
  },
  radioGroup: {
    gap: 8,
  },
  radioItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.sm,
    padding: 10,
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
  },
  radioItemActive: {
    borderColor: '#0F766E',
    backgroundColor: '#F0FDFA',
  },
  radioItemWarning: {
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
  radioCircleWarning: {
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
  radioDesc: {
    fontSize: 10.5,
    color: '#64748B',
    marginTop: 1,
  },
  overrideInputBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.sm,
    padding: 10,
    gap: 4,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  overrideInputLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#334155',
  },
  overrideInput: {
    height: 38,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 6,
    paddingHorizontal: 10,
    fontSize: 12,
    color: '#0F172A',
  },
  fieldGroup: {
    gap: 4,
  },
  fieldTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: '#334155',
  },
  fieldArea: {
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
  modalActions: {
    marginTop: 6,
  },
  mainActionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    borderRadius: BorderRadius.sm,
  },
  mainActionSuccess: {
    backgroundColor: '#0F6E56',
  },
  mainActionWarning: {
    backgroundColor: '#D97706',
  },
  mainActionText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#FFFFFF',
  },
});
