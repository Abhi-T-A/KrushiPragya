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
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  fetchGovernmentSchemesStats,
  GovernmentSchemeStatItem,
} from '../../services/governmentApi';
import {
  Landmark,
  Search,
  CheckCircle2,
  Clock,
  TrendingUp,
  X,
  FileCheck,
  ChevronRight,
  ShieldCheck,
  Building,
  BarChart3,
  Award,
} from 'lucide-react-native';

export const GovtSchemesScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const { language } = useLanguage();
  const isKn = language === 'kn';

  const [schemes, setSchemes] = useState<GovernmentSchemeStatItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedScheme, setSelectedScheme] = useState<GovernmentSchemeStatItem | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchGovernmentSchemesStats();
      setSchemes(data);
    } catch {
      setSchemes([]);
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const filteredSchemes = schemes.filter((s) => {
    if (searchQuery.trim().length > 0) {
      const q = searchQuery.toLowerCase();
      const matchTitle = s.title.toLowerCase().includes(q) || s.title_kn.toLowerCase().includes(q);
      const matchCat = s.category.toLowerCase().includes(q);
      if (!matchTitle && !matchCat) return false;
    }
    return true;
  });

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={[styles.header, { paddingTop: Math.max(insets.top, 12) + Spacing.xs }]}>
        <View style={styles.headerRow}>
          <View style={styles.headerIconBox}>
            <Landmark size={20} color="#FFFFFF" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.headerTitle}>
              {isKn ? 'ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು (Government Schemes)' : 'Government Schemes Performance'}
            </Text>
            <Text style={styles.headerSubtitle}>
              {isKn ? 'ಯೋಜನೆಗಳ ಅನುಷ್ಠಾನ, ಫಲಾನುಭವಿಗಳ ತಲುಪುವಿಕೆ & ಸೌಲಭ್ಯ ಅಂಕಿಅಂಶ' : 'Implementation, reach & disbursement stats'}
            </Text>
          </View>
        </View>

        {/* Search */}
        <View style={styles.searchBar}>
          <Search size={16} color="#64748B" />
          <TextInput
            style={styles.searchInput}
            placeholder={isKn ? 'ಯೋಜನೆ ಅಥವಾ ಇಲಾಖೆ ಹುಡುಕಿ...' : 'Search by scheme or category...'}
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

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#0F6E56']} />}
      >
        {/* Performance High-level Summary */}
        <View style={styles.overviewCard}>
          <View style={styles.overviewTop}>
            <BarChart3 size={18} color="#0F6E56" />
            <Text style={styles.overviewTitle}>
              {isKn ? 'ಯೋಜನಾ ಸಾಧನೆ ಸಾರಾಂಶ (Scheme Reach Metrics)' : 'Scheme Reach & Performance Metrics'}
            </Text>
          </View>
          <View style={styles.overviewGrid}>
            <View style={styles.overviewBox}>
              <Text style={styles.overviewNum}>71%</Text>
              <Text style={styles.overviewLbl}>{isKn ? 'ಸರಾಸರಿ ತಲುಪುವಿಕೆ' : 'Average Reach'}</Text>
            </View>
            <View style={styles.overviewBox}>
              <Text style={[styles.overviewNum, { color: '#15803D' }]}>241</Text>
              <Text style={styles.overviewLbl}>{isKn ? 'ಒಟ್ಟು ಅನುಮೋದನೆ' : 'Total Approved'}</Text>
            </View>
            <View style={styles.overviewBox}>
              <Text style={[styles.overviewNum, { color: '#D97706' }]}>53</Text>
              <Text style={styles.overviewLbl}>{isKn ? 'ಬಾಕಿ ಅರ್ಜಿಗಳು' : 'Pending Action'}</Text>
            </View>
          </View>
        </View>

        {/* Schemes List */}
        {isLoading && !refreshing ? (
          <View style={styles.centerLoading}>
            <ActivityIndicator size="large" color="#7E22CE" />
            <Text style={styles.loadingText}>
              {isKn ? 'ಯೋಜನೆಗಳನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...' : 'Loading schemes data...'}
            </Text>
          </View>
        ) : (
          <View style={styles.list}>
            {filteredSchemes.map((scheme) => (
              <TouchableOpacity
                key={scheme.id}
                style={styles.schemeCard}
                activeOpacity={0.85}
                onPress={() => setSelectedScheme(scheme)}
              >
                <View style={styles.schemeHeader}>
                  <View style={styles.categoryBadge}>
                    <Text style={styles.categoryBadgeText}>{scheme.category}</Text>
                  </View>
                  <View style={styles.reachPill}>
                    <TrendingUp size={11} color="#15803D" />
                    <Text style={styles.reachPillText}>{scheme.reach_percentage}% Reach</Text>
                  </View>
                </View>

                <Text style={styles.schemeTitle}>
                  {isKn && scheme.title_kn ? scheme.title_kn : scheme.title}
                </Text>
                <Text style={styles.deptText}>{scheme.department}</Text>

                {/* Performance Stats Bar */}
                <View style={styles.statsBar}>
                  <View style={styles.statCol}>
                    <Text style={styles.statNum}>{scheme.total_applications}</Text>
                    <Text style={styles.statLbl}>{isKn ? 'ಅರ್ಜಿಗಳು' : 'Applications'}</Text>
                  </View>
                  <View style={styles.statCol}>
                    <Text style={[styles.statNum, { color: '#15803D' }]}>{scheme.approved}</Text>
                    <Text style={styles.statLbl}>{isKn ? 'ಅನುಮೋದನೆ' : 'Approved'}</Text>
                  </View>
                  <View style={styles.statCol}>
                    <Text style={[styles.statNum, { color: '#D97706' }]}>{scheme.pending}</Text>
                    <Text style={styles.statLbl}>{isKn ? 'ಬಾಕಿ' : 'Pending'}</Text>
                  </View>
                  <View style={styles.statCol}>
                    <Text style={[styles.statNum, { color: '#DC2626' }]}>{scheme.rejected}</Text>
                    <Text style={styles.statLbl}>{isKn ? 'ತಿರಸ್ಕೃತ' : 'Rejected'}</Text>
                  </View>
                </View>

                <View style={styles.cardBottomRow}>
                  <Text style={styles.benefitsSnippet} numberOfLines={1}>
                    💰 {isKn ? scheme.benefits_kn : scheme.benefits}
                  </Text>
                  <View style={styles.detailsLink}>
                    <Text style={styles.detailsLinkText}>{isKn ? 'ವಿವರ ವೀಕ್ಷಿಸಿ' : 'View Details'}</Text>
                    <ChevronRight size={14} color="#7E22CE" />
                  </View>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </ScrollView>

      {/* Scheme Detail Modal */}
      <Modal
        visible={!!selectedScheme}
        transparent
        animationType="slide"
        onRequestClose={() => setSelectedScheme(null)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            <View style={styles.modalHeader}>
              <View style={{ flex: 1 }}>
                <Text style={styles.modalTitle}>
                  {isKn && selectedScheme?.title_kn ? selectedScheme.title_kn : selectedScheme?.title}
                </Text>
                <Text style={styles.modalSub}>{selectedScheme?.department}</Text>
              </View>
              <TouchableOpacity onPress={() => setSelectedScheme(null)} style={styles.closeBtn}>
                <X size={20} color="#475569" />
              </TouchableOpacity>
            </View>

            <ScrollView contentContainerStyle={styles.modalScroll}>
              <View style={styles.modalSection}>
                <Text style={styles.modalSectionHeader}>
                  {isKn ? '1. ಯೋಜನೆಯ ಸೌಲಭ್ಯಗಳು (Benefits):' : '1. Scheme Benefits:'}
                </Text>
                <Text style={styles.modalText}>
                  {isKn && selectedScheme?.benefits_kn ? selectedScheme.benefits_kn : selectedScheme?.benefits}
                </Text>
              </View>

              <View style={styles.modalSection}>
                <Text style={styles.modalSectionHeader}>
                  {isKn ? '2. ಅರ್ಹತಾ ಮಾನದಂಡಗಳು (Eligibility Criteria):' : '2. Eligibility Criteria:'}
                </Text>
                <Text style={styles.modalText}>
                  {isKn && selectedScheme?.eligibility_kn ? selectedScheme.eligibility_kn : selectedScheme?.eligibility}
                </Text>
              </View>

              <View style={styles.modalSection}>
                <Text style={styles.modalSectionHeader}>
                  {isKn ? '3. ಅಗತ್ಯವಿರುವ ದಾಖಲೆಗಳು (Required Documents):' : '3. Required Documents:'}
                </Text>
                <View style={styles.docsGrid}>
                  {selectedScheme?.required_docs.map((doc) => (
                    <View key={doc} style={styles.docChip}>
                      <ShieldCheck size={14} color="#15803D" />
                      <Text style={styles.docChipText}>{doc}</Text>
                    </View>
                  ))}
                </View>
              </View>

              <View style={styles.modalSection}>
                <Text style={styles.modalSectionHeader}>
                  {isKn ? '4. ಅನುಷ್ಠಾನ ಪ್ರಗತಿ (Implementation Status):' : '4. Implementation Reach:'}
                </Text>
                <View style={styles.perfBreakdown}>
                  <Text style={styles.perfRow}>
                    • {isKn ? 'ಒಟ್ಟು ಸ್ವೀಕೃತ ಅರ್ಜಿಗಳು:' : 'Total Applications:'} <Text style={styles.bold}>{selectedScheme?.total_applications}</Text>
                  </Text>
                  <Text style={styles.perfRow}>
                    • {isKn ? 'ಅನುಮೋದಿಸಿದ ಫಲಾನುಭವಿಗಳು:' : 'Approved Beneficiaries:'} <Text style={[styles.bold, { color: '#15803D' }]}>{selectedScheme?.approved}</Text>
                  </Text>
                  <Text style={styles.perfRow}>
                    • {isKn ? 'ಪ್ರಗತಿಯಲ್ಲಿರುವ ಪರಿಶೀಲನೆ:' : 'Pending Review:'} <Text style={[styles.bold, { color: '#D97706' }]}>{selectedScheme?.pending}</Text>
                  </Text>
                  <Text style={styles.perfRow}>
                    • {isKn ? 'ತಲುಪುವಿಕೆ ದರ (Reach Rate):' : 'Reach Percentage:'} <Text style={[styles.bold, { color: '#2563EB' }]}>{selectedScheme?.reach_percentage}%</Text>
                  </Text>
                </View>
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
  headerIconBox: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#16A34A',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: { fontSize: 16, fontWeight: '800', color: '#0F172A' },
  headerSubtitle: { fontSize: 11.5, color: '#64748B', marginTop: 1 },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F1F5F9',
    borderRadius: BorderRadius.sm,
    paddingHorizontal: 12,
    height: 38,
  },
  searchInput: { flex: 1, fontSize: 12.5, color: '#0F172A' },
  scrollContent: { padding: Spacing.md, paddingBottom: 40, gap: 12 },
  overviewCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 10,
  },
  overviewTop: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  overviewTitle: { fontSize: 13, fontWeight: '800', color: '#0F6E56' },
  overviewGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
  },
  overviewBox: { alignItems: 'center' },
  overviewNum: { fontSize: 20, fontWeight: '800', color: '#0F172A' },
  overviewLbl: { fontSize: 10.5, color: '#64748B', marginTop: 1 },
  centerLoading: { padding: 40, alignItems: 'center', gap: 8 },
  loadingText: { fontSize: 12, color: '#64748B' },
  list: { gap: 10 },
  schemeCard: {
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
  schemeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  categoryBadge: {
    backgroundColor: '#F3E8FF',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  categoryBadgeText: { fontSize: 10.5, fontWeight: '800', color: '#7E22CE' },
  reachPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: 4,
  },
  reachPillText: { fontSize: 10.5, fontWeight: '800', color: '#15803D' },
  schemeTitle: { fontSize: 14.5, fontWeight: '800', color: '#0F172A' },
  deptText: { fontSize: 11, color: '#64748B' },
  statsBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.sm,
    padding: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginTop: 2,
  },
  statCol: { alignItems: 'center' },
  statNum: { fontSize: 14, fontWeight: '800', color: '#0F172A' },
  statLbl: { fontSize: 10, color: '#64748B' },
  cardBottomRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 4,
  },
  benefitsSnippet: { flex: 1, fontSize: 11.5, color: '#16A34A', fontWeight: '600' },
  detailsLink: { flexDirection: 'row', alignItems: 'center', gap: 2 },
  detailsLinkText: { fontSize: 11.5, fontWeight: '700', color: '#7E22CE' },

  // Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(15,23,42,0.65)', justifyContent: 'flex-end' },
  modalSheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 18,
    borderTopRightRadius: 18,
    padding: Spacing.md,
    maxHeight: '90%',
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
  modalSection: {
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 6,
  },
  modalSectionHeader: { fontSize: 12.5, fontWeight: '800', color: '#7E22CE' },
  modalText: { fontSize: 12, color: '#334155', lineHeight: 18 },
  docsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  docChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  docChipText: { fontSize: 11, fontWeight: '600', color: '#1E293B' },
  perfBreakdown: { gap: 4 },
  perfRow: { fontSize: 12, color: '#334155' },
  bold: { fontWeight: '800', color: '#0F172A' },
});
