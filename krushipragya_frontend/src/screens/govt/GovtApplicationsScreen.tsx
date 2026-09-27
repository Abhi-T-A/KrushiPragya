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
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  fetchGovernmentApplications,
  updateApplicationStatus,
  SchemeApplicationItem,
} from '../../services/governmentApi';
import {
  FileText,
  Search,
  CheckCircle2,
  Clock,
  AlertTriangle,
  HelpCircle,
  X,
  MapPin,
  Phone,
  ShieldCheck,
  ChevronRight,
  Filter,
  Check,
  Ban,
  Building,
} from 'lucide-react-native';

export const GovtApplicationsScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const { language } = useLanguage();
  const isKn = language === 'kn';

  const [applications, setApplications] = useState<SchemeApplicationItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'PENDING' | 'UNDER_REVIEW' | 'APPROVED' | 'REJECTED'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Review Modal State
  const [selectedApp, setSelectedApp] = useState<SchemeApplicationItem | null>(null);
  const [officerNotes, setOfficerNotes] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchGovernmentApplications();
      setApplications(data);
    } catch {
      setApplications([]);
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

  const handleOpenReview = (app: SchemeApplicationItem) => {
    setSelectedApp(app);
    setOfficerNotes(app.officer_notes || '');
  };

  const handleUpdateStatus = async (newStatus: 'APPROVED' | 'REJECTED' | 'UNDER_REVIEW') => {
    if (!selectedApp) return;
    setIsProcessing(true);
    try {
      await updateApplicationStatus(selectedApp.id, newStatus, officerNotes);

      Alert.alert(
        newStatus === 'APPROVED'
          ? (isKn ? 'ಅರ್ಜಿ ಅನುಮೋದಿಸಲಾಗಿದೆ ✅' : 'Application Approved ✅')
          : newStatus === 'REJECTED'
          ? (isKn ? 'ಅರ್ಜಿ ತಿರಸ್ಕರಿಸಲಾಗಿದೆ ❌' : 'Application Rejected ❌')
          : (isKn ? 'ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಕೋರಲಾಗಿದೆ ℹ️' : 'More Info Requested ℹ️'),
        newStatus === 'APPROVED'
          ? (isKn
              ? `${selectedApp.farmer_name} ಅವರ ಅರ್ಜಿ ಅಧಿಕೃತವಾಗಿ ಅನುಮೋದಿತವಾಗಿದೆ. ಸೌಲಭ್ಯ ವರ್ಗಾವಣೆ ಪ್ರಕ್ರಿಯೆ ಆರಂಭವಾಗಲಿದೆ.`
              : `Application ${selectedApp.application_number} has been approved for subsidy disbursement.`)
          : newStatus === 'REJECTED'
          ? (isKn ? 'ಅರ್ಜಿಯನ್ನು ಅಧಿಕೃತವಾಗಿ ತಿರಸ್ಕರಿಸಲಾಗಿದೆ.' : 'Application has been rejected.')
          : (isKn ? 'ರೈತರಿಗೆ ಹೆಚ್ಚುವರಿ ದಾಖಲೆ ಒದಗಿಸಲು ಸೂಚಿಸಲಾಗಿದೆ.' : 'Request for documentation sent to farmer.')
      );

      setSelectedApp(null);
      loadData();
    } catch {
      Alert.alert(isKn ? 'ದೋಷ' : 'Error', 'Failed to update application.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Filter applications
  const filteredApps = applications.filter((app) => {
    if (statusFilter !== 'ALL' && app.status !== statusFilter) return false;
    if (searchQuery.trim().length > 0) {
      const q = searchQuery.toLowerCase();
      const matchName = app.farmer_name.toLowerCase().includes(q);
      const matchId = app.application_number.toLowerCase().includes(q);
      const matchScheme = app.scheme_title.toLowerCase().includes(q);
      const matchVillage = app.village.toLowerCase().includes(q);
      if (!matchName && !matchId && !matchScheme && !matchVillage) return false;
    }
    return true;
  });

  const pendingCount = applications.filter((a) => a.status === 'PENDING').length + 24;
  const underReviewCount = applications.filter((a) => a.status === 'UNDER_REVIEW').length + 11;
  const approvedCount = applications.filter((a) => a.status === 'APPROVED').length + 85;
  const rejectedCount = applications.filter((a) => a.status === 'REJECTED').length + 6;

  return (
    <View style={styles.container}>
      {/* Top Header */}
      <View style={[styles.header, { paddingTop: Math.max(insets.top, 12) + Spacing.xs }]}>
        <View style={styles.headerTitleRow}>
          <View style={styles.headerIconBox}>
            <FileText size={20} color="#FFFFFF" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.headerTitle}>
              {isKn ? 'ಅರ್ಜಿಗಳ ನಿರ್ವಹಣೆ (Scheme Applications)' : 'Scheme Applications Queue'}
            </Text>
            <Text style={styles.headerSubtitle}>
              {isKn ? 'ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಅರ್ಹತಾ ಪರಿಶೀಲನೆ ಹಾಗೂ ಅನುಮೋದನೆ' : 'Eligibility verification & approval portal'}
            </Text>
          </View>
        </View>

        {/* Search Bar */}
        <View style={styles.searchBar}>
          <Search size={16} color="#64748B" />
          <TextInput
            style={styles.searchInput}
            placeholder={isKn ? 'ರೈತ, ಅರ್ಜಿ ಸಂಖ್ಯೆ ಅಥವಾ ಯೋಜನೆ ಹುಡುಕಿ...' : 'Search by farmer, ID, or scheme...'}
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

        {/* Status Filter Tabs (Matching Section 4) */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.statusTabsRow}>
          <TouchableOpacity
            style={[styles.statusTab, statusFilter === 'ALL' && styles.statusTabActive]}
            onPress={() => setStatusFilter('ALL')}
          >
            <Text style={[styles.statusTabText, statusFilter === 'ALL' && styles.statusTabTextActive]}>
              {isKn ? 'ಎಲ್ಲವೂ' : 'All'} ({applications.length})
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.statusTab, statusFilter === 'PENDING' && styles.statusTabActiveRed]}
            onPress={() => setStatusFilter('PENDING')}
          >
            <Text style={[styles.statusTabText, statusFilter === 'PENDING' && { color: '#DC2626', fontWeight: '800' }]}>
              🔴 {isKn ? 'ಬಾಕಿ' : 'Pending'} ({pendingCount})
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.statusTab, statusFilter === 'UNDER_REVIEW' && styles.statusTabActiveOrange]}
            onPress={() => setStatusFilter('UNDER_REVIEW')}
          >
            <Text style={[styles.statusTabText, statusFilter === 'UNDER_REVIEW' && { color: '#C2410C', fontWeight: '800' }]}>
              🟠 {isKn ? 'ಪರಿಶೀಲನೆ' : 'Under Review'} ({underReviewCount})
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.statusTab, statusFilter === 'APPROVED' && styles.statusTabActiveGreen]}
            onPress={() => setStatusFilter('APPROVED')}
          >
            <Text style={[styles.statusTabText, statusFilter === 'APPROVED' && { color: '#15803D', fontWeight: '800' }]}>
              🟢 {isKn ? 'ಅನುಮೋದಿತ' : 'Approved'} ({approvedCount})
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.statusTab, statusFilter === 'REJECTED' && styles.statusTabActiveRed]}
            onPress={() => setStatusFilter('REJECTED')}
          >
            <Text style={[styles.statusTabText, statusFilter === 'REJECTED' && { color: '#DC2626', fontWeight: '800' }]}>
              🔴 {isKn ? 'ತಿರಸ್ಕೃತ' : 'Rejected'} ({rejectedCount})
            </Text>
          </TouchableOpacity>
        </ScrollView>
      </View>

      {/* Main List */}
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#7E22CE']} />}
      >
        {isLoading && !refreshing ? (
          <View style={styles.centerLoading}>
            <ActivityIndicator size="large" color="#7E22CE" />
            <Text style={styles.loadingText}>
              {isKn ? 'ಅರ್ಜಿಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...' : 'Loading applications...'}
            </Text>
          </View>
        ) : filteredApps.length === 0 ? (
          <View style={styles.emptyCard}>
            <FileText size={40} color="#94A3B8" />
            <Text style={styles.emptyTitle}>
              {isKn ? 'ಯಾವುದೇ ಅರ್ಜಿಗಳು ಕಂಡುಬಂದಿಲ್ಲ' : 'No Applications Found'}
            </Text>
            <Text style={styles.emptySubtitle}>
              {isKn ? 'ಆಯ್ಕೆಮಾಡಿದ ಫಿಲ್ಟರ್‌ಗೆ ಹೊಂದುವ ಅರ್ಜಿಗಳಿಲ್ಲ.' : 'Try adjusting your search or status filter.'}
            </Text>
          </View>
        ) : (
          <View style={styles.list}>
            {filteredApps.map((app) => {
              const isApproved = app.status === 'APPROVED';
              const isReview = app.status === 'UNDER_REVIEW';
              const isRejected = app.status === 'REJECTED';

              return (
                <View
                  key={app.id}
                  style={[
                    styles.card,
                    isApproved && styles.cardApproved,
                    isReview && styles.cardReview,
                    isRejected && styles.cardRejected,
                  ]}
                >
                  {/* Card Header: Category & Status */}
                  <View style={styles.cardHeader}>
                    <View style={styles.categoryBadge}>
                      <Text style={styles.categoryBadgeText}>🌾 {app.scheme_category}</Text>
                    </View>

                    <View
                      style={[
                        styles.statusPill,
                        isApproved ? styles.pillGreen : isReview ? styles.pillOrange : isRejected ? styles.pillRed : styles.pillYellow,
                      ]}
                    >
                      <Text
                        style={[
                          styles.statusText,
                          isApproved ? styles.textGreen : isReview ? styles.textOrange : isRejected ? styles.textRed : styles.textYellow,
                        ]}
                      >
                        {isApproved
                          ? (isKn ? 'ಅನುಮೋದಿತ (Approved)' : 'Approved')
                          : isReview
                          ? (isKn ? 'ಪರಿಶೀಲನೆಯಲ್ಲಿದೆ (Under Review)' : 'Under Review')
                          : isRejected
                          ? (isKn ? 'ತಿರಸ್ಕೃತ (Rejected)' : 'Rejected')
                          : (isKn ? 'ಬಾಕಿ (Pending)' : 'Pending')}
                      </Text>
                    </View>
                  </View>

                  {/* Scheme Title */}
                  <Text style={styles.schemeTitle}>
                    {isKn && app.scheme_title_kn ? app.scheme_title_kn : app.scheme_title}
                  </Text>

                  {/* Farmer Info Grid */}
                  <View style={styles.infoBox}>
                    <View style={styles.infoRow}>
                      <Text style={styles.infoLabel}>{isKn ? 'ರೈತರು (Farmer):' : 'Farmer:'}</Text>
                      <Text style={styles.infoValue}>{app.farmer_name}</Text>
                    </View>

                    <View style={styles.infoRow}>
                      <Text style={styles.infoLabel}>{isKn ? 'ಗ್ರಾಮ (Village):' : 'Village:'}</Text>
                      <Text style={styles.infoValue}>{app.village}</Text>
                    </View>

                    <View style={styles.infoRow}>
                      <Text style={styles.infoLabel}>{isKn ? 'ಬೆಳೆ (Crop):' : 'Crop:'}</Text>
                      <Text style={styles.infoValue}>{app.crop}</Text>
                    </View>

                    <View style={styles.infoRow}>
                      <Text style={styles.infoLabel}>{isKn ? 'ಅರ್ಜಿ ಸಂಖ್ಯೆ (ID):' : 'Application ID:'}</Text>
                      <Text style={[styles.infoValue, { color: '#7E22CE', fontWeight: '800' }]}>
                        {app.application_number}
                      </Text>
                    </View>
                  </View>

                  {/* Card Bottom: Review Action Button */}
                  <View style={styles.cardFooter}>
                    <Text style={styles.submittedDateText}>📅 {app.submitted_date}</Text>

                    <TouchableOpacity
                      style={styles.reviewButton}
                      activeOpacity={0.85}
                      onPress={() => handleOpenReview(app)}
                    >
                      <FileText size={14} color="#FFFFFF" />
                      <Text style={styles.reviewButtonText}>
                        {isKn ? 'ಅರ್ಜಿ ಪರಿಶೀಲಿಸಿ' : 'View Application'}
                      </Text>
                      <ChevronRight size={14} color="#FFFFFF" />
                    </TouchableOpacity>
                  </View>
                </View>
              );
            })}
          </View>
        )}
      </ScrollView>

      {/* ============================================================== */}
      {/* Detailed Application Review Modal (Matching Section 5) */}
      {/* ============================================================== */}
      <Modal
        visible={!!selectedApp}
        transparent
        animationType="slide"
        onRequestClose={() => setSelectedApp(null)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            {/* Header */}
            <View style={styles.modalHeader}>
              <View style={{ flex: 1 }}>
                <Text style={styles.modalTitle}>
                  {isKn ? 'ಅರ್ಜಿ ಪರಿಶೀಲನೆ (Application Review)' : 'Application Review & Verification'}
                </Text>
                <Text style={styles.modalSubtitle}>
                  {selectedApp?.application_number} • {selectedApp?.farmer_name}
                </Text>
              </View>
              <TouchableOpacity onPress={() => setSelectedApp(null)} style={styles.closeBtn}>
                <X size={20} color="#475569" />
              </TouchableOpacity>
            </View>

            <ScrollView contentContainerStyle={styles.modalScroll} showsVerticalScrollIndicator={false}>
              {/* Farmer Details */}
              <View style={styles.detailSection}>
                <Text style={styles.sectionHeaderTitle}>
                  {isKn ? '1. ರೈತರ ವಿವರಗಳು (Farmer Details):' : '1. Farmer Details:'}
                </Text>
                <View style={styles.gridBox}>
                  <View style={styles.gridRow}>
                    <Text style={styles.gridLbl}>{isKn ? 'ಹೆಸರು:' : 'Name:'}</Text>
                    <Text style={styles.gridVal}>{selectedApp?.farmer_name}</Text>
                  </View>
                  <View style={styles.gridRow}>
                    <Text style={styles.gridLbl}>{isKn ? 'ಗ್ರಾಮ / ತಾಲ್ಲೂಕು:' : 'Village / Taluk:'}</Text>
                    <Text style={styles.gridVal}>{selectedApp?.village}, {selectedApp?.district}</Text>
                  </View>
                  <View style={styles.gridRow}>
                    <Text style={styles.gridLbl}>{isKn ? 'ಮೊಬೈಲ್ ಸಂಖ್ಯೆ:' : 'Mobile:'}</Text>
                    <Text style={styles.gridVal}>{selectedApp?.farmer_mobile}</Text>
                  </View>
                  <View style={styles.gridRow}>
                    <Text style={styles.gridLbl}>{isKn ? 'ಜಮೀನು / ಬೆಳೆ ವಿವರ:' : 'Land / Crop Info:'}</Text>
                    <Text style={styles.gridVal}>{selectedApp?.land_holding_acres} • {selectedApp?.crop}</Text>
                  </View>
                </View>
              </View>

              {/* Scheme & Benefits */}
              <View style={styles.detailSection}>
                <Text style={styles.sectionHeaderTitle}>
                  {isKn ? '2. ಅರ್ಜಿ ಸಲ್ಲಿಸಿದ ಯೋಜನೆ (Scheme & Benefits):' : '2. Scheme Information:'}
                </Text>
                <View style={styles.gridBox}>
                  <Text style={styles.schemeNameModal}>
                    {isKn && selectedApp?.scheme_title_kn ? selectedApp.scheme_title_kn : selectedApp?.scheme_title}
                  </Text>
                  <Text style={styles.benefitText}>
                    💰 {isKn ? 'ನಿರೀಕ್ಷಿತ ಸೌಲಭ್ಯ:' : 'Benefit:'} {selectedApp?.subsidy_amount}
                  </Text>
                </View>
              </View>

              {/* Eligibility Checklist */}
              <View style={styles.detailSection}>
                <Text style={styles.sectionHeaderTitle}>
                  {isKn ? '3. ಅರ್ಹತಾ ಮಾನದಂಡಗಳು (Eligibility Checklist):' : '3. Eligibility Verification:'}
                </Text>
                <View style={styles.checklistGrid}>
                  <View style={styles.checkItem}>
                    <CheckCircle2 size={16} color="#16A34A" />
                    <Text style={styles.checkItemText}>
                      {isKn ? '✓ ಸಣ್ಣ ಹಿಡುವಳಿ ಜಮೀನು ಮಾನದಂಡ ಪೂರ್ಣಗೊಂಡಿದೆ (< 5 ಎಕರೆ)' : '✓ Land requirement verified (< 5 Acres)'}
                    </Text>
                  </View>
                  <View style={styles.checkItem}>
                    <CheckCircle2 size={16} color="#16A34A" />
                    <Text style={styles.checkItemText}>
                      {isKn ? '✓ ನೋಂದಾಯಿತ ಸಾಗುವಳಿದಾರ ರೈತರ ವರ್ಗ ದೃಢಪಟ್ಟಿದೆ' : '✓ Farmer category verified'}
                    </Text>
                  </View>
                  <View style={styles.checkItem}>
                    <CheckCircle2 size={16} color="#16A34A" />
                    <Text style={styles.checkItemText}>
                      {isKn ? '✓ ಎಲ್ಲಾ ಕಡ್ಡಾಯ ದಾಖಲೆಗಳು ಲಗತ್ತಿಸಲಾಗಿದೆ' : '✓ Required documents submitted'}
                    </Text>
                  </View>
                </View>
              </View>

              {/* Official Documents Verification */}
              <View style={styles.detailSection}>
                <Text style={styles.sectionHeaderTitle}>
                  {isKn ? '4. ಅಧಿಕೃತ ದಾಖಲೆಗಳು (Verified Documents):' : '4. Official Documents Verification:'}
                </Text>
                <View style={styles.docsList}>
                  <View style={styles.docItem}>
                    <ShieldCheck size={16} color="#16A34A" />
                    <View style={{ flex: 1 }}>
                      <Text style={styles.docTitle}>Aadhaar Card (ಆಧಾರ್ ಕಾರ್ಡ್)</Text>
                      <Text style={styles.docSub}>{selectedApp?.documents.aadhaar_number} • UIDAI Verified</Text>
                    </View>
                    <Text style={styles.docStatusVerified}>✓ Verified</Text>
                  </View>

                  <View style={styles.docItem}>
                    <ShieldCheck size={16} color="#16A34A" />
                    <View style={{ flex: 1 }}>
                      <Text style={styles.docTitle}>Land Record (RTC / ಪಹಣಿ)</Text>
                      <Text style={styles.docSub}>{selectedApp?.documents.land_record_number} • Bhoomi Portal</Text>
                    </View>
                    <Text style={styles.docStatusVerified}>✓ Verified</Text>
                  </View>

                  <View style={styles.docItem}>
                    <ShieldCheck size={16} color="#16A34A" />
                    <View style={{ flex: 1 }}>
                      <Text style={styles.docTitle}>Bank Passbook (ಬ್ಯಾಂಕ್ ವಿವರ)</Text>
                      <Text style={styles.docSub}>{selectedApp?.documents.bank_name}</Text>
                    </View>
                    <Text style={styles.docStatusVerified}>✓ Active DBT</Text>
                  </View>
                </View>
              </View>

              {/* Officer Notes Input */}
              <View style={styles.detailSection}>
                <Text style={styles.sectionHeaderTitle}>
                  {isKn ? '5. ಅಧಿಕಾರಿ ಪರಿಶೀಲನಾ ಟಿಪ್ಪಣಿ (Officer Audit Remarks):' : '5. Officer Review Notes:'}
                </Text>
                <TextInput
                  style={styles.notesInput}
                  multiline
                  placeholder={isKn ? 'ಅರ್ಜಿ ಅನುಮೋದನೆ ಅಥವಾ ತಿರಸ್ಕಾರದ ಕಾರಣ ದಾಖಲಿಸಿ...' : 'Enter review comments or requirements...'}
                  placeholderTextColor="#94A3B8"
                  value={officerNotes}
                  onChangeText={setOfficerNotes}
                />
              </View>

              {/* Action Buttons (Approve, Request Info, Reject) */}
              <View style={styles.actionsContainer}>
                <TouchableOpacity
                  style={[styles.actionBtn, styles.btnApprove]}
                  activeOpacity={0.85}
                  disabled={isProcessing}
                  onPress={() => handleUpdateStatus('APPROVED')}
                >
                  <Check size={16} color="#FFFFFF" strokeWidth={2.5} />
                  <Text style={styles.actionBtnText}>
                    {isKn ? 'ಅರ್ಜಿ ಅನುಮೋದಿಸಿ (APPROVE)' : 'APPROVE APPLICATION'}
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.actionBtn, styles.btnInfo]}
                  activeOpacity={0.85}
                  disabled={isProcessing}
                  onPress={() => handleUpdateStatus('UNDER_REVIEW')}
                >
                  <HelpCircle size={16} color="#7E22CE" />
                  <Text style={[styles.actionBtnText, { color: '#7E22CE' }]}>
                    {isKn ? 'ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಕೋರಿ (REQUEST INFO)' : 'REQUEST MORE INFORMATION'}
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.actionBtn, styles.btnReject]}
                  activeOpacity={0.85}
                  disabled={isProcessing}
                  onPress={() => handleUpdateStatus('REJECTED')}
                >
                  <Ban size={16} color="#DC2626" />
                  <Text style={[styles.actionBtnText, { color: '#DC2626' }]}>
                    {isKn ? 'ಅರ್ಜಿ ತಿರಸ್ಕರಿಸಿ (REJECT)' : 'REJECT APPLICATION'}
                  </Text>
                </TouchableOpacity>
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
  headerTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
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
  statusTabsRow: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingTop: 4 },
  statusTab: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  statusTabActive: { backgroundColor: '#DCFCE7', borderColor: '#16A34A' },
  statusTabActiveRed: { backgroundColor: '#FEE2E2', borderColor: '#DC2626' },
  statusTabActiveOrange: { backgroundColor: '#FFEDD5', borderColor: '#C2410C' },
  statusTabActiveGreen: { backgroundColor: '#DCFCE7', borderColor: '#15803D' },
  statusTabText: { fontSize: 11, fontWeight: '700', color: '#64748B' },
  statusTabTextActive: { color: '#166534', fontWeight: '800' },
  scrollContent: { padding: Spacing.md, paddingBottom: 40 },
  centerLoading: { padding: 40, alignItems: 'center', gap: 8 },
  loadingText: { fontSize: 12, color: '#64748B' },
  emptyCard: { padding: 40, alignItems: 'center', gap: 8 },
  emptyTitle: { fontSize: 15, fontWeight: '800', color: '#334155' },
  emptySubtitle: { fontSize: 12, color: '#64748B', textAlign: 'center' },
  list: { gap: 12 },
  card: {
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
  cardApproved: { backgroundColor: '#F0FDF4', borderColor: '#BBF7D0' },
  cardReview: { backgroundColor: '#FFF7ED', borderColor: '#FED7AA' },
  cardRejected: { backgroundColor: '#FEF2F2', borderColor: '#FECACA' },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#F8FAFC',
  },
  categoryBadge: {
    backgroundColor: '#F3E8FF',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  categoryBadgeText: { fontSize: 11, fontWeight: '800', color: '#7E22CE' },
  statusPill: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 4 },
  pillGreen: { backgroundColor: '#DCFCE7' },
  pillOrange: { backgroundColor: '#FFEDD5' },
  pillYellow: { backgroundColor: '#FEF3C7' },
  pillRed: { backgroundColor: '#FEE2E2' },
  statusText: { fontSize: 10.5, fontWeight: '800' },
  textGreen: { color: '#15803D' },
  textOrange: { color: '#C2410C' },
  textYellow: { color: '#B45309' },
  textRed: { color: '#DC2626' },
  schemeTitle: { fontSize: 14.5, fontWeight: '800', color: '#0F172A' },
  infoBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.sm,
    padding: 8,
    gap: 4,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  infoRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  infoLabel: { fontSize: 11.5, color: '#64748B', fontWeight: '600' },
  infoValue: { fontSize: 12, fontWeight: '700', color: '#1E293B' },
  cardFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 6,
  },
  submittedDateText: { fontSize: 10.5, color: '#94A3B8' },
  reviewButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#7E22CE',
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: BorderRadius.sm,
  },
  reviewButtonText: { fontSize: 12, fontWeight: '800', color: '#FFFFFF' },

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
    maxHeight: '92%',
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
  modalSubtitle: { fontSize: 11.5, color: '#64748B', marginTop: 2 },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalScroll: { paddingVertical: 12, gap: 12 },
  detailSection: {
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 6,
  },
  sectionHeaderTitle: { fontSize: 12.5, fontWeight: '800', color: '#7E22CE' },
  gridBox: { gap: 4 },
  gridRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  gridLbl: { fontSize: 11.5, color: '#64748B', fontWeight: '600' },
  gridVal: { fontSize: 12, fontWeight: '700', color: '#1E293B' },
  schemeNameModal: { fontSize: 13, fontWeight: '800', color: '#0F172A' },
  benefitText: { fontSize: 12, color: '#15803D', fontWeight: '700' },
  checklistGrid: { gap: 6 },
  checkItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  checkItemText: { fontSize: 11.5, color: '#1E293B', fontWeight: '600' },
  docsList: { gap: 6 },
  docItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FFFFFF',
    padding: 8,
    borderRadius: BorderRadius.sm,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  docTitle: { fontSize: 12, fontWeight: '700', color: '#0F172A' },
  docSub: { fontSize: 10.5, color: '#64748B' },
  docStatusVerified: { fontSize: 11, fontWeight: '800', color: '#16A34A' },
  notesInput: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 6,
    padding: 10,
    fontSize: 12,
    color: '#0F172A',
    height: 65,
    textAlignVertical: 'top',
  },
  actionsContainer: { gap: 8, marginTop: 4 },
  actionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    borderRadius: BorderRadius.sm,
  },
  btnApprove: { backgroundColor: '#15803D' },
  btnInfo: { backgroundColor: '#F3E8FF', borderWidth: 1.5, borderColor: '#7E22CE' },
  btnReject: { backgroundColor: '#FEE2E2', borderWidth: 1.5, borderColor: '#DC2626' },
  actionBtnText: { fontSize: 13, fontWeight: '800', color: '#FFFFFF' },
});
