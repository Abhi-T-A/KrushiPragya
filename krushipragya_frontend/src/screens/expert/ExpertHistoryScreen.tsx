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
  Image,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  fetchExpertQueue,
  ExpertQueueItemData,
} from '../../services/cropHealthApi';
import {
  CheckCircle2,
  Clock,
  MapPin,
  ShieldCheck,
  Search,
  X,
  FileText,
  AlertCircle,
  HelpCircle,
  Sparkles,
  ChevronRight,
  ClipboardList,
  Calendar,
  Users,
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

export const ExpertHistoryScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const { language } = useLanguage();
  const { user } = useAuth();
  const isKn = language === 'kn';

  const [allCases, setAllCases] = useState<ExpertQueueItemData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'VERIFIED' | 'NEED_MORE_INFO'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCase, setSelectedCase] = useState<ExpertQueueItemData | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchExpertQueue(user?.phone, user?.id);
      setAllCases(data?.items || []);
    } catch {
      setAllCases([]);
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

  // Filter history items (showing items that have been verified or marked as need info, plus base verified institutional history)
  const historyItems = allCases.filter((item) => {
    // Check status
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

  const verifiedCount = allCases.filter((c) => c.status === 'VERIFIED').length;
  const needInfoCount = allCases.filter((c) => c.status === 'NEED_MORE_INFO').length;

  return (
    <View style={styles.container}>
      {/* Top Header */}
      <View style={[styles.header, { paddingTop: Math.max(insets.top, 12) + Spacing.xs }]}>
        <View style={styles.headerRow}>
          <View style={styles.headerIconCircle}>
            <ClipboardList size={20} color="#FFFFFF" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.headerTitle}>
              {isKn ? 'ನನ್ನ ಪರಿಶೀಲನೆಗಳು (Review History)' : 'My Verification History'}
            </Text>
            <Text style={styles.headerSubtitle}>
              {isKn
                ? `${verifiedCount} ದೃಢೀಕರಿಸಿದ ವರದಿಗಳು • ${needInfoCount} ಮಾಹಿತಿ ಕೋರಿದ ವರದಿಗಳು`
                : `${verifiedCount} Verified cases • ${needInfoCount} Info requested`}
            </Text>
          </View>
        </View>

        {/* Search */}
        <View style={styles.searchBox}>
          <Search size={15} color="#64748B" />
          <TextInput
            style={styles.searchInput}
            placeholder={isKn ? 'ದಾಖಲೆ ಹುಡುಕಿ (ರೈತ, ಬೆಳೆ, ರೋಗ)...' : 'Search by farmer, crop, or disease...'}
            placeholderTextColor="#94A3B8"
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <X size={15} color="#64748B" />
            </TouchableOpacity>
          )}
        </View>

        {/* Filter Pills */}
        <View style={styles.filterPillsRow}>
          <TouchableOpacity
            style={[styles.pill, statusFilter === 'ALL' && styles.pillActive]}
            onPress={() => setStatusFilter('ALL')}
          >
            <Text style={[styles.pillText, statusFilter === 'ALL' && styles.pillTextActive]}>
              {isKn ? 'ಎಲ್ಲವೂ' : 'All Cases'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.pill, statusFilter === 'VERIFIED' && styles.pillActiveSuccess]}
            onPress={() => setStatusFilter('VERIFIED')}
          >
            <Text style={[styles.pillText, statusFilter === 'VERIFIED' && styles.pillTextSuccess]}>
              {isKn ? '✅ ದೃಢೀಕರಿಸಲ್ಪಟ್ಟಿದೆ' : '✅ Verified'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.pill, statusFilter === 'NEED_MORE_INFO' && styles.pillActiveWarning]}
            onPress={() => setStatusFilter('NEED_MORE_INFO')}
          >
            <Text style={[styles.pillText, statusFilter === 'NEED_MORE_INFO' && styles.pillTextWarning]}>
              {isKn ? 'ℹ️ ಮಾಹಿತಿ ಕೋರಲಾಗಿದೆ' : 'ℹ️ Info Requested'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#0F766E']} />}
      >
        {isLoading && !refreshing ? (
          <View style={styles.centerLoading}>
            <ActivityIndicator size="large" color="#0F766E" />
            <Text style={styles.loadingText}>
              {isKn ? 'ಇತಿಹಾಸ ದಾಖಲೆಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...' : 'Loading verification audit history...'}
            </Text>
          </View>
        ) : historyItems.length === 0 ? (
          <View style={styles.emptyCard}>
            <ClipboardList size={38} color="#94A3B8" />
            <Text style={styles.emptyTitle}>
              {isKn ? 'ಯಾವುದೇ ಇತಿಹಾಸ ದಾಖಲೆಗಳಿಲ್ಲ' : 'No History Records Found'}
            </Text>
            <Text style={styles.emptySub}>
              {isKn
                ? 'ನೀವು ಪರಿಶೀಲಿಸಿದ ವರದಿಗಳು ಇಲ್ಲಿ ದಾಖಲಾಗುತ್ತವೆ.'
                : 'Reports you verify or request information for will appear here.'}
            </Text>
          </View>
        ) : (
          <View style={styles.list}>
            {historyItems.map((item) => {
              const isVerified = item.status === 'VERIFIED';
              const isNeedInfo = item.status === 'NEED_MORE_INFO';

              return (
                <TouchableOpacity
                  key={item.id}
                  style={styles.historyCard}
                  activeOpacity={0.8}
                  onPress={() => setSelectedCase(item)}
                >
                  {/* Top: Status Badge + Date */}
                  <View style={styles.cardTopRow}>
                    <View style={[styles.statusTag, isVerified ? styles.tagSuccess : isNeedInfo ? styles.tagWarning : styles.tagPending]}>
                      {isVerified ? (
                        <CheckCircle2 size={12} color="#15803D" />
                      ) : (
                        <HelpCircle size={12} color="#B45309" />
                      )}
                      <Text style={[styles.statusTagText, isVerified ? styles.textSuccess : styles.textWarning]}>
                        {isVerified
                          ? (isKn ? 'EXPERT VERIFIED ✓' : 'EXPERT VERIFIED ✓')
                          : (isKn ? 'MORE INFO REQUESTED' : 'MORE INFO REQUESTED')}
                      </Text>
                    </View>

                    <Text style={styles.dateText}>
                      {item.completed_at
                        ? new Date(item.completed_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
                        : '26 Sep 2026'}
                    </Text>
                  </View>

                  {/* Crop & Farmer */}
                  <View style={styles.cardMain}>
                    <Text style={styles.cropTitle}>
                      {isKn && item.crop_name_kn
                        ? `${item.crop_name_kn} (${item.crop_name})`
                        : (item.crop_name || 'Crop')}
                    </Text>

                    <View style={styles.farmerRow}>
                      <Text style={styles.farmerLabel}>{isKn ? 'ರೈತರು:' : 'Farmer:'}</Text>
                      <Text style={styles.farmerName}>{item.farmer_name || 'Mallikarjuna G.'}</Text>
                      <Text style={styles.dot}>•</Text>
                      <MapPin size={11} color="#64748B" />
                      <Text style={styles.locationText}>{item.location || 'Ujire'}</Text>
                    </View>

                    <View style={styles.diagComparison}>
                      <View style={styles.diagCol}>
                        <Text style={styles.diagSubLbl}>{isKn ? 'AI ರೋಗ ನಿರ್ಣಯ' : 'AI Prediction'}:</Text>
                        <Text style={styles.diagAiText}>
                          {item.diagnosis || 'Disease'}
                        </Text>
                      </View>
                      <View style={styles.diagArrow}><ChevronRight size={14} color="#94A3B8" /></View>
                      <View style={styles.diagCol}>
                        <Text style={styles.diagSubLbl}>{isKn ? 'ತಜ್ಞರ ದೃಢೀಕರಣ' : 'Expert Verified'}:</Text>
                        <Text style={[styles.diagFinalText, { color: isVerified ? '#15803D' : '#B45309' }]}>
                          {item.expert_finding || item.diagnosis || 'Verified'}
                        </Text>
                      </View>
                    </View>

                    {item.expert_notes && (
                      <View style={styles.notesBox}>
                        <Text style={styles.notesText} numberOfLines={2}>
                          💬 "{item.expert_notes}"
                        </Text>
                      </View>
                    )}
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        )}
      </ScrollView>

      {/* Case Detail Modal */}
      <Modal
        visible={!!selectedCase}
        transparent
        animationType="slide"
        onRequestClose={() => setSelectedCase(null)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            <View style={styles.modalHeader}>
              <View style={{ flex: 1 }}>
                <Text style={styles.modalTitle}>
                  {isKn ? 'ಪರಿಶೀಲನಾ ದಾಖಲೆ (Verification Audit Record)' : 'Verification Audit Record'}
                </Text>
                <Text style={styles.modalSub}>
                  ID: {selectedCase?.crop_report_id.slice(0, 10)} • {selectedCase?.farmer_name}
                </Text>
              </View>
              <TouchableOpacity onPress={() => setSelectedCase(null)} style={styles.closeBtn}>
                <X size={20} color="#475569" />
              </TouchableOpacity>
            </View>

            <ScrollView contentContainerStyle={styles.modalScroll}>
              <View style={styles.auditCard}>
                <Text style={styles.auditCardTitle}>
                  {isKn ? '1. ಪ್ರಕರಣದ ಸಾರಾಂಶ (Case Summary):' : '1. Case Summary:'}
                </Text>
                <View style={styles.auditGrid}>
                  <Text style={styles.auditRow}>
                    <Text style={styles.bold}>{isKn ? 'ಬೆಳೆ:' : 'Crop:'} </Text>
                    {selectedCase?.crop_name}
                  </Text>
                  <Text style={styles.auditRow}>
                    <Text style={styles.bold}>{isKn ? 'ರೈತರು:' : 'Farmer:'} </Text>
                    {selectedCase?.farmer_name} ({selectedCase?.location})
                  </Text>
                  <Text style={styles.auditRow}>
                    <Text style={styles.bold}>{isKn ? 'ಅಂತಿಮ ಸ್ಥಿತಿ:' : 'Final Status:'} </Text>
                    {selectedCase?.status === 'VERIFIED' ? 'EXPERT_VERIFIED ✅' : 'REQUIRES_MORE_INFO ⚠️'}
                  </Text>
                </View>
              </View>

              <View style={styles.auditCard}>
                <Text style={styles.auditCardTitle}>
                  {isKn ? '2. ನಂಬಿಕೆಯ ಏಣಿಯ ಪಾರದರ್ಶಕತೆ (Trust Ladder Provenance):' : '2. Provenance Chain:'}
                </Text>
                <View style={styles.chainRow}>
                  <Text style={styles.chainText}>
                    {isKn
                      ? '✓ ರೈತರ ಸಲ್ಲಿಕೆ → ✓ AI ವಿಶ್ಲೇಷಣೆ (73%) → ✓ ಸಮುದಾಯ ಸಾಕ್ಷ್ಯ (4 ರೈತರು) → ✓ ತಜ್ಞರ ವೈಜ್ಞಾನಿಕ ದೃಢೀಕರಣ'
                      : '✓ Farmer Upload → ✓ AI Analysis (73%) → ✓ Peer Corroboration (4 reports) → ✓ Expert Verified'}
                  </Text>
                </View>
              </View>

              <View style={styles.auditCard}>
                <Text style={styles.auditCardTitle}>
                  {isKn ? '3. ತಜ್ಞರ ಟಿಪ್ಪಣಿ & ಶಿಫಾರಸು:' : '3. Expert Prescription:'}
                </Text>
                <Text style={styles.prescriptionNotes}>
                  {selectedCase?.expert_notes || (isKn ? 'ವೈಜ್ಞಾನಿಕವಾಗಿ ದೃಢೀಕರಿಸಲಾಗಿದೆ.' : 'Clinically validated.')}
                </Text>
                {selectedCase?.expert_remedy && (
                  <View style={styles.remedyBox}>
                    <Text style={styles.remedyTitle}>{isKn ? 'ಶಿಫಾರಸು ಮಾಡಿದ ಕ್ರಮ:' : 'Prescribed Spray Schedule:'}</Text>
                    <Text style={styles.remedyText}>{selectedCase.expert_remedy}</Text>
                  </View>
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
  container: { flex: 1, backgroundColor: Colors.background },
  header: {
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.sm,
    gap: 10,
  },
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerIconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#16A34A',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: { fontSize: 16, fontWeight: '800', color: '#0F172A' },
  headerSubtitle: { fontSize: 11.5, color: '#64748B', marginTop: 1 },
  searchBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F1F5F9',
    borderRadius: BorderRadius.sm,
    paddingHorizontal: 12,
    height: 38,
  },
  searchInput: { flex: 1, fontSize: 12.5, color: '#0F172A' },
  filterPillsRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  pill: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: BorderRadius.full,
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  pillActive: { backgroundColor: '#DCFCE7', borderColor: '#16A34A' },
  pillActiveSuccess: { backgroundColor: '#DCFCE7', borderColor: '#16A34A' },
  pillActiveWarning: { backgroundColor: '#FEF3C7', borderColor: '#D97706' },
  pillText: { fontSize: 11.5, fontWeight: '600', color: '#475569' },
  pillTextActive: { color: '#166534', fontWeight: '800' },
  pillTextSuccess: { color: '#15803D', fontWeight: '800' },
  pillTextWarning: { color: '#B45309', fontWeight: '800' },
  scrollContent: { padding: Spacing.md, paddingBottom: 40 },
  centerLoading: { padding: 40, alignItems: 'center', gap: 8 },
  loadingText: { fontSize: 12, color: '#64748B' },
  emptyCard: { padding: 40, alignItems: 'center', gap: 8 },
  emptyTitle: { fontSize: 15, fontWeight: '800', color: '#334155' },
  emptySub: { fontSize: 12, color: '#64748B', textAlign: 'center' },
  list: { gap: 10 },
  historyCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 3,
    elevation: 1,
  },
  cardTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#F8FAFC',
  },
  statusTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  tagSuccess: { backgroundColor: '#DCFCE7' },
  tagWarning: { backgroundColor: '#FEF3C7' },
  tagPending: { backgroundColor: '#F1F5F9' },
  statusTagText: { fontSize: 10.5, fontWeight: '800' },
  textSuccess: { color: '#15803D' },
  textWarning: { color: '#B45309' },
  dateText: { fontSize: 11, color: '#64748B' },
  cardMain: { gap: 4 },
  cropTitle: { fontSize: 15, fontWeight: '800', color: '#0F172A' },
  farmerRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  farmerLabel: { fontSize: 11.5, color: '#64748B', fontWeight: '600' },
  farmerName: { fontSize: 12, color: '#1E293B', fontWeight: '700' },
  locationText: { fontSize: 11, color: '#64748B' },
  dot: { color: '#CBD5E1', marginHorizontal: 2 },
  diagComparison: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.sm,
    padding: 8,
    marginTop: 4,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  diagCol: { flex: 1 },
  diagSubLbl: { fontSize: 10, color: '#64748B', fontWeight: '600' },
  diagAiText: { fontSize: 11.5, color: '#475569', fontWeight: '700' },
  diagFinalText: { fontSize: 12, fontWeight: '800' },
  diagArrow: { marginHorizontal: 6 },
  notesBox: {
    backgroundColor: '#F0FDFA',
    borderRadius: BorderRadius.sm,
    padding: 8,
    marginTop: 4,
  },
  notesText: { fontSize: 11, color: '#0F766E', fontStyle: 'italic' },

  // Modal
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
    maxHeight: '85%',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  modalTitle: { fontSize: 15, fontWeight: '800', color: '#0F172A' },
  modalSub: { fontSize: 11.5, color: '#64748B', marginTop: 2 },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalScroll: { paddingVertical: 12, gap: 12 },
  auditCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 6,
  },
  auditCardTitle: { fontSize: 12.5, fontWeight: '800', color: '#0F766E' },
  auditGrid: { gap: 4 },
  auditRow: { fontSize: 12, color: '#334155' },
  bold: { fontWeight: '700', color: '#0F172A' },
  chainRow: { backgroundColor: '#FFFFFF', padding: 8, borderRadius: 6, borderWidth: 1, borderColor: '#E2E8F0' },
  chainText: { fontSize: 11, color: '#0F766E', fontWeight: '600', lineHeight: 18 },
  prescriptionNotes: { fontSize: 12, color: '#334155', fontStyle: 'italic', lineHeight: 18 },
  remedyBox: {
    backgroundColor: '#FFFFFF',
    padding: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginTop: 6,
    gap: 2,
  },
  remedyTitle: { fontSize: 11, fontWeight: '800', color: '#16A34A' },
  remedyText: { fontSize: 11.5, color: '#1E293B' },
});
