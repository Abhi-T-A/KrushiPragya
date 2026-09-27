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
  Modal,
  Alert,
  Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  fetchLocalReports,
  submitCommunityObservation,
  LocalCropIssueReport,
} from '../../services/communityApi';
import {
  Eye,
  Search,
  Plus,
  MapPin,
  CheckCircle2,
  AlertTriangle,
  X,
  Camera,
  HeartHandshake,
  Clock,
  Layers,
  Sparkles,
  ChevronRight,
  Filter,
  Send,
} from 'lucide-react-native';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const CROPS_OPTIONS = [
  { code: 'arecanut', nameEn: 'Arecanut', nameKn: 'ಅಡಿಕೆ', icon: '🌴' },
  { code: 'paddy', nameEn: 'Paddy', nameKn: 'ಭತ್ತ', icon: '🌾' },
  { code: 'coconut', nameEn: 'Coconut', nameKn: 'ತೆಂಗು', icon: '🥥' },
  { code: 'pepper', nameEn: 'Black Pepper', nameKn: 'ಕಾಳುಮೆಣಸು', icon: '🌶' },
  { code: 'cardamom', nameEn: 'Cardamom', nameKn: 'ಏಲಕ್ಕಿ', icon: '🌿' },
];

const SYMPTOM_CHECKBOXES = [
  { id: 'Leaf yellowing', labelEn: 'Leaf yellowing', labelKn: 'ಎಲೆ ಹಳದಿ ಬಣ್ಣಕ್ಕೆ ತಿರುಗುವುದು' },
  { id: 'Fruit rot', labelEn: 'Fruit rot', labelKn: 'ಕಾಯಿ ಕೊಳೆಯುವುದು / ಮಹಾಳಿ' },
  { id: 'Stem issue', labelEn: 'Stem issue', labelKn: 'ಕಾಂಡ ಅಥವಾ ತೊಗಟೆಯ ಸಮಸ್ಯೆ' },
  { id: 'Pest presence', labelEn: 'Pest presence', labelKn: 'ಕೀಟ ಅಥವಾ ನೊಣಗಳ ಬಾಧೆ' },
  { id: 'Waterlogging', labelEn: 'Waterlogging', labelKn: 'ಬೇರಿನಲ್ಲಿ ನೀರು ನಿಲ್ಲುವುದು' },
  { id: 'Other', labelEn: 'Other', labelKn: 'ಇತರೆ ಅಸಹಜ ಲಕ್ಷಣಗಳು' },
];

interface CommunityReportsScreenProps {
  route?: any;
  navigation: any;
}

export const CommunityReportsScreen: React.FC<CommunityReportsScreenProps> = ({ route, navigation }) => {
  const insets = useSafeAreaInsets();
  const { language } = useLanguage();
  const { user } = useAuth();
  const isKn = language === 'kn';

  const autoOpenSubmit = route?.params?.openSubmitModal;

  const [reports, setReports] = useState<LocalCropIssueReport[]>([]);
  const [selectedCropFilter, setSelectedCropFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Submit Observation Modal State
  const [isSubmitModalVisible, setIsSubmitModalVisible] = useState(autoOpenSubmit || false);
  const [selectedCropCode, setSelectedCropCode] = useState('arecanut');
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>(['Fruit rot']);
  const [observationLocation, setObservationLocation] = useState('Ujire Village (ಉಜಿರೆ)');
  const [observationDesc, setObservationDesc] = useState('');
  const [isPhotoAttached, setIsPhotoAttached] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadReports = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchLocalReports(selectedCropFilter, searchQuery);
      setReports(data);
    } catch (e) {
      console.warn('Failed to load local reports:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedCropFilter, searchQuery]);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  const onRefresh = () => {
    setRefreshing(true);
    loadReports();
  };

  const toggleSymptom = (sym: string) => {
    if (selectedSymptoms.includes(sym)) {
      setSelectedSymptoms(selectedSymptoms.filter((s) => s !== sym));
    } else {
      setSelectedSymptoms([...selectedSymptoms, sym]);
    }
  };

  const handleConfirmSubmit = async () => {
    if (selectedSymptoms.length === 0) {
      Alert.alert(
        isKn ? 'ಲಕ್ಷಣಗಳನ್ನು ಆಯ್ಕೆಮಾಡಿ' : 'Select Symptoms',
        isKn ? 'ದಯವಿಟ್ಟು ನೀವು ಗಮನಿಸಿದ ಕನಿಷ್ಠ ಒಂದು ಲಕ್ಷಣವನ್ನು ಆಯ್ಕೆಮಾಡಿ.' : 'Please select at least one observed symptom.'
      );
      return;
    }

    const cropObj = CROPS_OPTIONS.find((c) => c.code === selectedCropCode) || CROPS_OPTIONS[0];

    setIsSubmitting(true);
    try {
      await submitCommunityObservation({
        crop_code: cropObj.code,
        crop_name: cropObj.nameEn,
        crop_name_kn: cropObj.nameKn,
        crop_icon: cropObj.icon,
        symptoms: selectedSymptoms,
        location: observationLocation,
        description: observationDesc,
        reporter_name: user?.name || 'Community Member (Ujire)',
      });

      setIsSubmitting(false);
      setIsSubmitModalVisible(false);
      setObservationDesc('');

      Alert.alert(
        isKn ? '✅ ವೀಕ್ಷಣೆ ದಾಖಲಾಗಿದೆ!' : '✅ Observation Submitted!',
        isKn
          ? 'ನಿಮ್ಮ ವರದಿಯನ್ನು "UNVERIFIED" (ದೃಢೀಕರಣವಿಲ್ಲದ) ಹಂತದಲ್ಲಿ ದಾಖಲಿಸಲಾಗಿದೆ. ಸಮುದಾಯ ಸದಸ್ಯರ ಸಾಕ್ಷ್ಯಾಧಾರ ಹಾಗೂ ತಜ್ಞರ ಪರಿಶೀಲನೆ ನಂತರ ಇದು ದೃಢಪಡುತ್ತದೆ.'
          : 'Your field observation is logged with initial status UNVERIFIED under the KrushiPragya Trust Ladder.',
        [{ text: 'OK', onPress: () => loadReports() }]
      );
    } catch (e) {
      setIsSubmitting(false);
      Alert.alert('Error', 'Failed to submit observation.');
    }
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.iconCircle}>
            <Eye size={20} color="#16A34A" />
          </View>
          <View>
            <Text style={styles.headerTitle}>
              {isKn ? 'ಸ್ಥಳೀಯ ವರದಿಗಳು' : 'Local Crop Reports'}
            </Text>
            <Text style={styles.headerSub}>
              {isKn ? 'ಗ್ರಾಮದಲ್ಲಿ ರೈತರು ಮತ್ತು ಸಮುದಾಯ ಗಮನಿಸಿದ ಬೆಳೆ ಸಮಸ್ಯೆಗಳು' : 'Community Surveillance Feed • Ujire Cluster'}
            </Text>
          </View>
        </View>

        <TouchableOpacity
          style={styles.newBtn}
          onPress={() => setIsSubmitModalVisible(true)}
          activeOpacity={0.8}
        >
          <Plus size={14} color="#FFFFFF" strokeWidth={2.5} />
          <Text style={styles.newBtnText}>{isKn ? 'ಹೊಸ ವರದಿ' : 'Report'}</Text>
        </TouchableOpacity>
      </View>

      {/* Search Input */}
      <View style={styles.searchBarWrap}>
        <View style={styles.searchInputRow}>
          <Search size={16} color="#94A3B8" />
          <TextInput
            style={styles.searchInput}
            placeholder={isKn ? 'ಬೆಳೆ, ಗ್ರಾಮ ಅಥವಾ ಲಕ್ಷಣ ಹುಡುಕಿ...' : 'Search crop / village / symptom...'}
            placeholderTextColor="#94A3B8"
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <X size={16} color="#64748B" />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Filter Tabs */}
      <View style={styles.filterWrap}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterScroll}>
          <TouchableOpacity
            style={[styles.filterChip, selectedCropFilter === 'ALL' && styles.filterChipActive]}
            onPress={() => setSelectedCropFilter('ALL')}
          >
            <Text style={[styles.filterChipText, selectedCropFilter === 'ALL' && styles.filterChipTextActive]}>
              {isKn ? 'ಎಲ್ಲಾ ಬೆಳೆಗಳು' : 'All Crops'}
            </Text>
          </TouchableOpacity>

          {CROPS_OPTIONS.map((crop) => {
            const isSelected = selectedCropFilter === crop.code;
            return (
              <TouchableOpacity
                key={crop.code}
                style={[styles.filterChip, isSelected && styles.filterChipActive]}
                onPress={() => setSelectedCropFilter(crop.code)}
              >
                <Text style={[styles.filterChipText, isSelected && styles.filterChipTextActive]}>
                  {crop.icon} {isKn ? crop.nameKn : crop.nameEn}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      {/* Reports Feed */}
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.primary]} />}
      >
        {loading && !refreshing ? (
          <View style={styles.centerLoading}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingText}>
              {isKn ? 'ಸ್ಥಳೀಯ ವರದಿಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...' : 'Loading local surveillance feed...'}
            </Text>
          </View>
        ) : reports.length === 0 ? (
          <View style={styles.emptyCard}>
            <Eye size={40} color="#CBD5E1" />
            <Text style={styles.emptyTitle}>
              {isKn ? 'ಯಾವುದೇ ವರದಿಗಳು ಕಂಡುಬಂದಿಲ್ಲ' : 'No Local Reports Found'}
            </Text>
            <Text style={styles.emptySub}>
              {isKn ? 'ನಿಮ್ಮ ಗ್ರಾಮದಲ್ಲಿ ಹೊಸ ಬೆಳೆ ವೀಕ್ಷಣೆಯನ್ನು ದಾಖಲಿಸಿ.' : 'Submit a local observation to alert the community.'}
            </Text>
          </View>
        ) : (
          <View style={styles.feedList}>
            {reports.map((item) => {
              const isCorroborated = item.status === 'CORROBORATED';
              const isVerified = item.status === 'EXPERT_VERIFIED';
              const isUnverified = item.status === 'UNVERIFIED';

              return (
                <View key={item.id} style={styles.feedCard}>
                  <View style={styles.cardTopRow}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, flex: 1 }}>
                      <Text style={styles.feedCropIcon}>{item.crop_icon}</Text>
                      <View>
                        <Text style={styles.feedCropName}>{item.crop_name}</Text>
                        <Text style={styles.feedLocation}>📍 {item.village} • {item.distance_km} km</Text>
                      </View>
                    </View>

                    {/* Trust Ladder Status Badge */}
                    <View
                      style={[
                        styles.trustPill,
                        isVerified
                          ? styles.bgGreenLight
                          : isCorroborated
                          ? styles.bgTealLight
                          : isUnverified
                          ? styles.bgGrayLight
                          : styles.bgBlueLight,
                      ]}
                    >
                      <Text
                        style={[
                          styles.trustPillText,
                          isVerified
                            ? styles.textGreen
                            : isCorroborated
                            ? styles.textTeal
                            : isUnverified
                            ? styles.textGray
                            : styles.textBlue,
                        ]}
                      >
                        {item.status}
                      </Text>
                    </View>
                  </View>

                  <Text style={styles.issueText}>
                    {isKn ? item.observed_issue_kn : item.observed_issue}
                  </Text>

                  <View style={styles.symptomsListRow}>
                    {item.symptoms.map((s, idx) => (
                      <View key={idx} style={styles.symptomTag}>
                        <Text style={styles.symptomTagText}>{s}</Text>
                      </View>
                    ))}
                  </View>

                  <View style={styles.reporterInfoRow}>
                    <Text style={styles.reporterText}>
                      👤 {item.reporter_name} • {item.reported_at}
                    </Text>
                    <Text style={styles.corrobCountText}>
                      👥 {item.similar_reports_count} {isKn ? 'ರೈತರ ವರದಿ' : 'similar reports'}
                    </Text>
                  </View>

                  {/* Corroborate Action */}
                  <TouchableOpacity
                    style={styles.corroborateCardBtn}
                    onPress={() => navigation.navigate('CommunityCorroborateTab', { reportId: item.id })}
                    activeOpacity={0.85}
                  >
                    <HeartHandshake size={14} color="#0D9488" />
                    <Text style={styles.corroborateCardBtnText}>
                      {isKn ? 'ನನಗೂ ಇದೇ ಸಮಸ್ಯೆ ಕಂಡಿದೆ (Corroborate)' : 'Corroborate This Report'}
                    </Text>
                    <ChevronRight size={13} color="#0D9488" />
                  </TouchableOpacity>
                </View>
              );
            })}
          </View>
        )}
      </ScrollView>

      {/* ============================================================== */}
      {/* Submit Local Observation Modal (Section 6) */}
      {/* ============================================================== */}
      <Modal
        visible={isSubmitModalVisible}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setIsSubmitModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalSheet, { paddingBottom: Math.max(insets.bottom, 20) }]}>
            <View style={styles.modalSheetHeader}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <View style={[styles.iconCircle, { backgroundColor: '#CCFBF1' }]}>
                  <Plus size={18} color="#0D9488" />
                </View>
                <View>
                  <Text style={styles.modalSheetTitle}>
                    {isKn ? 'ಹೊಸ ಸ್ಥಳೀಯ ವರದಿ (New Observation)' : 'Submit Local Observation'}
                  </Text>
                  <Text style={styles.modalSheetSub}>
                    {isKn ? 'ಪ್ರಾರಂಭಿಕ ಹಂತ: UNVERIFIED • ತಜ್ಞರ ತೀರ್ಪಲ್ಲ' : 'Initial Status: UNVERIFIED • Non-clinical observation'}
                  </Text>
                </View>
              </View>
              <TouchableOpacity onPress={() => setIsSubmitModalVisible(false)} style={styles.closeBtn}>
                <X size={18} color="#64748B" />
              </TouchableOpacity>
            </View>

            <ScrollView showsVerticalScrollIndicator={false} style={styles.modalForm}>
              {/* Crop Selector */}
              <Text style={styles.formSectionLabel}>
                {isKn ? 'ಬೆಳೆ ಆಯ್ಕೆ (Crop)' : 'Select Crop'}
              </Text>
              <View style={styles.cropPickRow}>
                {CROPS_OPTIONS.map((c) => {
                  const isSel = selectedCropCode === c.code;
                  return (
                    <TouchableOpacity
                      key={c.code}
                      style={[styles.cropPickItem, isSel && styles.cropPickItemActive]}
                      onPress={() => setSelectedCropCode(c.code)}
                    >
                      <Text style={styles.cropPickIcon}>{c.icon}</Text>
                      <Text style={[styles.cropPickText, isSel && styles.cropPickTextActive]}>
                        {isKn ? c.nameKn : c.nameEn}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>

              {/* Symptoms Checklist (Section 6) */}
              <Text style={styles.formSectionLabel}>
                {isKn ? 'ನೀವು ಏನು ಗಮನಿಸಿದ್ದೀರಿ? (What did you observe?)' : 'Observed Symptoms:'}
              </Text>
              <View style={styles.symptomsGrid}>
                {SYMPTOM_CHECKBOXES.map((sym) => {
                  const isChecked = selectedSymptoms.includes(sym.id);
                  return (
                    <TouchableOpacity
                      key={sym.id}
                      style={[styles.checkboxItem, isChecked && styles.checkboxItemActive]}
                      onPress={() => toggleSymptom(sym.id)}
                      activeOpacity={0.7}
                    >
                      <View style={[styles.checkboxBox, isChecked && styles.checkboxBoxActive]}>
                        {isChecked && <Text style={styles.checkMark}>✓</Text>}
                      </View>
                      <Text style={[styles.checkboxLabel, isChecked && styles.checkboxLabelActive]}>
                        {isKn ? sym.labelKn : sym.labelEn}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>

              {/* Photo Upload Attachment */}
              <Text style={styles.formSectionLabel}>{isKn ? 'ಭಾವಚಿತ್ರ (Photo)' : 'Photo:'}</Text>
              <TouchableOpacity
                style={styles.photoAttachBox}
                onPress={() => setIsPhotoAttached(!isPhotoAttached)}
                activeOpacity={0.8}
              >
                <Camera size={18} color={isPhotoAttached ? '#0D9488' : '#94A3B8'} />
                <Text style={[styles.photoAttachText, isPhotoAttached && { color: '#0D9488', fontWeight: '800' }]}>
                  {isPhotoAttached ? (isKn ? '✓ ಕೃಷಿ ಫೋಟೋ ಲಗತ್ತಿಸಲಾಗಿದೆ' : '✓ Photo Attached (field_obs_01.jpg)') : (isKn ? '+ ಫೋಟೋ ಸೇರಿಸಿ' : '+ Add Photo')}
                </Text>
              </TouchableOpacity>

              {/* Location */}
              <Text style={styles.formSectionLabel}>{isKn ? 'ಸ್ಥಳ (Location)' : 'Location:'}</Text>
              <View style={styles.locationInputRow}>
                <MapPin size={16} color="#0D9488" />
                <TextInput
                  style={styles.locationInput}
                  value={observationLocation}
                  onChangeText={setObservationLocation}
                  placeholder="Village / Taluk"
                />
              </View>

              {/* Description */}
              <Text style={styles.formSectionLabel}>
                {isKn ? 'ವಿವರಣೆ (Description)' : 'Additional Description:'}
              </Text>
              <TextInput
                style={styles.descInput}
                placeholder={
                  isKn
                    ? 'ಗಮನಿಸಿದ ಲಕ್ಷಣಗಳು, ಹರಡುವಿಕೆ ವೇಗ ಇತ್ಯಾದಿ ವಿವರಗಳನ್ನು ಬರೆಯಿರಿ...'
                    : 'Describe symptom severity, affected farm area, or recent weather triggers...'
                }
                placeholderTextColor="#94A3B8"
                value={observationDesc}
                onChangeText={setObservationDesc}
                multiline
                numberOfLines={3}
                textAlignVertical="top"
              />

              {/* Trust Ladder Non-diagnosis Guarantee */}
              <View style={styles.ladderNoteBox}>
                <Text style={styles.ladderNoteText}>
                  {isKn
                    ? 'ಗಮನಿಸಿ: ಈ ವರದಿಯು ಪ್ರಾರಂಭದಲ್ಲಿ "UNVERIFIED" (ದೃಢೀಕರಣವಿಲ್ಲದ) ಹಂತದಲ್ಲಿರುತ್ತದೆ. ತಜ್ಞರ ಪರಿಶೀಲನೆ ಇಲ್ಲದೆ ಯಾವುದೇ ಔಷಧಿಯನ್ನು ಶಿಫಾರಸು ಮಾಡಲಾಗುವುದಿಲ್ಲ.'
                    : 'Notice: This report will be tagged UNVERIFIED. It does not automatically become a disease diagnosis until expert validation.'}
                </Text>
              </View>
            </ScrollView>

            <View style={styles.modalSheetActions}>
              <TouchableOpacity
                style={styles.cancelBtn}
                onPress={() => setIsSubmitModalVisible(false)}
                activeOpacity={0.7}
              >
                <Text style={styles.cancelBtnText}>{isKn ? 'ರದ್ದುಮಾಡಿ' : 'Cancel'}</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.confirmSubmitBtn}
                onPress={handleConfirmSubmit}
                disabled={isSubmitting}
                activeOpacity={0.85}
              >
                {isSubmitting ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <>
                    <Send size={15} color="#FFFFFF" />
                    <Text style={styles.confirmSubmitBtnText}>
                      {isKn ? 'ವರದಿ ಸಲ್ಲಿಸಿ (SUBMIT)' : 'SUBMIT REPORT'}
                    </Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
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
  newBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#0F6E56',
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: 8,
  },
  newBtnText: {
    fontSize: 12,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  searchBarWrap: {
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 6,
    backgroundColor: '#FFFFFF',
  },
  searchInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    paddingHorizontal: 12,
    paddingVertical: 7,
    gap: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 13,
    color: '#0F172A',
    padding: 0,
  },
  filterWrap: {
    backgroundColor: '#FFFFFF',
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  filterScroll: {
    paddingHorizontal: 16,
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#F1F5F9',
  },
  filterChipActive: {
    backgroundColor: '#0F6E56',
  },
  filterChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#475569',
  },
  filterChipTextActive: {
    color: '#FFFFFF',
    fontWeight: '800',
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 36,
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
  emptyCard: {
    paddingVertical: 60,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#475569',
  },
  emptySub: {
    fontSize: 12,
    color: '#94A3B8',
  },
  feedList: {
    gap: 12,
  },
  feedCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    gap: 8,
  },
  cardTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  feedCropIcon: {
    fontSize: 22,
  },
  feedCropName: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
  },
  feedLocation: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 1,
  },
  trustPill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  bgGreenLight: {
    backgroundColor: '#DCFCE7',
  },
  bgTealLight: {
    backgroundColor: '#CCFBF1',
  },
  bgBlueLight: {
    backgroundColor: '#DBEAFE',
  },
  bgGrayLight: {
    backgroundColor: '#F1F5F9',
  },
  textGreen: {
    color: '#16A34A',
  },
  textTeal: {
    color: '#0D9488',
  },
  textBlue: {
    color: '#2563EB',
  },
  textGray: {
    color: '#64748B',
  },
  trustPillText: {
    fontSize: 9.5,
    fontWeight: '800',
  },
  issueText: {
    fontSize: 13.5,
    fontWeight: '700',
    color: '#334155',
  },
  symptomsListRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  symptomTag: {
    backgroundColor: '#F8FAFC',
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  symptomTagText: {
    fontSize: 11,
    color: '#475569',
  },
  reporterInfoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
  },
  reporterText: {
    fontSize: 11,
    color: '#64748B',
  },
  corrobCountText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#0D9488',
  },
  corroborateCardBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#F0FDFA',
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CCFBF1',
    marginTop: 2,
  },
  corroborateCardBtnText: {
    fontSize: 11.5,
    fontWeight: '800',
    color: '#0D9488',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalSheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '88%',
    padding: 18,
  },
  modalSheetHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  modalSheetTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  modalSheetSub: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 1,
  },
  closeBtn: {
    padding: 4,
  },
  modalForm: {
    marginTop: 12,
  },
  formSectionLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#334155',
    marginBottom: 6,
    marginTop: 8,
  },
  cropPickRow: {
    flexDirection: 'row',
    gap: 8,
    flexWrap: 'wrap',
  },
  cropPickItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#F8FAFC',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  cropPickItemActive: {
    backgroundColor: '#CCFBF1',
    borderColor: '#0D9488',
  },
  cropPickIcon: {
    fontSize: 14,
  },
  cropPickText: {
    fontSize: 12,
    color: '#475569',
    fontWeight: '600',
  },
  cropPickTextActive: {
    color: '#0F766E',
    fontWeight: '800',
  },
  symptomsGrid: {
    gap: 6,
  },
  checkboxItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F8FAFC',
    padding: 9,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  checkboxItemActive: {
    backgroundColor: '#F0FDFA',
    borderColor: '#99F6E4',
  },
  checkboxBox: {
    width: 18,
    height: 18,
    borderRadius: 4,
    borderWidth: 1.5,
    borderColor: '#CBD5E1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxBoxActive: {
    backgroundColor: '#0D9488',
    borderColor: '#0D9488',
  },
  checkMark: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '900',
  },
  checkboxLabel: {
    fontSize: 12,
    color: '#334155',
  },
  checkboxLabelActive: {
    fontWeight: '700',
    color: '#0F766E',
  },
  photoAttachBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F8FAFC',
    borderRadius: 8,
    padding: 10,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  photoAttachText: {
    fontSize: 12,
    color: '#64748B',
  },
  locationInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F8FAFC',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  locationInput: {
    flex: 1,
    fontSize: 12.5,
    color: '#0F172A',
    padding: 0,
  },
  descInput: {
    backgroundColor: '#F8FAFC',
    borderRadius: 8,
    padding: 10,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    fontSize: 12.5,
    color: '#0F172A',
    height: 60,
  },
  ladderNoteBox: {
    backgroundColor: '#F1F5F9',
    borderRadius: 8,
    padding: 10,
    marginTop: 12,
    marginBottom: 16,
  },
  ladderNoteText: {
    fontSize: 11,
    color: '#475569',
    lineHeight: 16,
  },
  modalSheetActions: {
    flexDirection: 'row',
    gap: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
  },
  cancelBtn: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  cancelBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#475569',
  },
  confirmSubmitBtn: {
    flex: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: '#0F6E56',
  },
  confirmSubmitBtnText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#FFFFFF',
  },
});
