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
} from 'react-native';
import { Header } from '../../components/common/Header';
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
} from 'lucide-react-native';

export const ExpertQueueScreen: React.FC = () => {
  const { language } = useLanguage();
  const { user } = useAuth();
  const isKn = language === 'kn';

  const [verificationRequests, setVerificationRequests] = useState<ExpertQueueItemData[]>([]);
  const [isLoadingQueue, setIsLoadingQueue] = useState(false);

  // Review Modal State
  const [selectedRequest, setSelectedRequest] = useState<ExpertQueueItemData | null>(null);
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
    }
  }, [user?.phone, user?.id]);

  useEffect(() => {
    loadRequests();
  }, [loadRequests]);


  // Expert action: change PENDING -> VERIFIED or PENDING -> REQUIRES_MORE_INFORMATION
  const handleDecision = async (decision: 'VERIFIED' | 'REQUIRES_MORE_INFORMATION') => {
    if (!selectedRequest) return;

    // RBAC check: only AGRICULTURE_EXPERT
    if (user?.role !== 'expert') {
      Alert.alert(
        isKn ? 'ಅನಧಿಕೃತ ಪ್ರವೇಶ' : 'Unauthorized Access',
        isKn
          ? 'ಕೇವಲ ಅಧಿಕೃತ ಕೃಷಿ ತಜ್ಞರು (AGRICULTURE_EXPERT) ಮಾತ್ರ ಈ ವರದಿಯನ್ನು ದೃಢೀಕರಿಸಬಹುದು.'
          : 'Only certified AGRICULTURE_EXPERT can perform expert verification.'
      );
      return;
    }

    // Farmer cannot verify their own report
    if (selectedRequest.farmer_id === user?.id) {
      Alert.alert(
        isKn ? 'ಸ್ವಯಂ ದೃಢೀಕರಣ ಸಾಧ್ಯವಿಲ್ಲ' : 'Self Verification Forbidden',
        isKn
          ? 'ರೈತರು ತಮ್ಮ ಸ್ವಂತ ವರದಿಯನ್ನು ಪರಿಶೀಲಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ.'
          : 'Farmers cannot verify their own crop reports.'
      );
      return;
    }

    setIsSubmittingDecision(true);
    try {
      const expertName = user?.name || (isKn ? 'ಕೃಷಿ ತಜ್ಞರು' : 'Agriculture Expert');
      const expertOrg = user?.organization || 'ICAR - KVK';

      if (!selectedRequest.id.startsWith('demo-')) {
        await submitExpertDecision(
          selectedRequest.id,
          decision,
          selectedRequest.diagnosis || 'Confirmed Diagnosis',
          decision === 'VERIFIED'
            ? `${expertName} (${expertOrg}) verified diagnosis and prescribed schedule.`
            : 'Requires clearer close-up photograph of leaf lesion.',
          decision === 'VERIFIED' ? 'Apply standard 1% Bordeaux Mixture spray' : undefined,
          user?.phone,
          user?.id
        );
      }

      const updatedStatus = decision === 'VERIFIED' ? 'VERIFIED' : 'NEED_MORE_INFO';
      setVerificationRequests((prev) =>
        prev.map((r) => (r.id === selectedRequest.id ? { ...r, status: updatedStatus } : r))
      );

      setSelectedRequest((prev: ExpertQueueItemData | null) => (prev ? { ...prev, status: updatedStatus } : null));

      Alert.alert(
        decision === 'VERIFIED'
          ? (isKn ? 'ವರದಿ ದೃಢೀಕರಿಸಲಾಗಿದೆ ✅' : 'Report Verified ✅')
          : (isKn ? 'ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಕೋರಲಾಗಿದೆ ℹ️' : 'More Info Requested ℹ️'),
        decision === 'VERIFIED'
          ? (isKn ? 'ಸ್ಥಿತಿ: VERIFIED ಗೆ ನವೀಕರಿಸಲಾಗಿದೆ.' : 'Status updated to VERIFIED.')
          : (isKn ? 'ಸ್ಥಿತಿ: REQUIRES_MORE_INFORMATION ಗೆ ನವೀಕರಿಸಲಾಗಿದೆ.' : 'Status updated to REQUIRES_MORE_INFORMATION.')
      );
      setSelectedRequest(null);
      loadRequests();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Could not update verification status.';
      Alert.alert(isKn ? 'ದೋಷ' : 'Error', msg);
    } finally {
      setIsSubmittingDecision(false);
    }
  };

  const pendingVerificationCount = verificationRequests.filter((r) => r.status === 'PENDING').length;

  return (
    <View style={styles.container}>
      <Header />

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Compact Header */}
        <View style={styles.topCard}>
          <View style={styles.iconBox}>
            <Microscope size={20} color="#FFFFFF" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.topTitle}>
              {user?.nameKn && isKn
                ? user.nameKn
                : user?.name
                ? user.name
                : isKn
                ? 'ಕೃಷಿ ವಿಜ್ಞಾನಿ / ತಜ್ಞರು'
                : 'Agriculture Expert'}
            </Text>
            <Text style={styles.topSub}>
              {user?.organization || (isKn ? 'ICAR - ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರ' : 'ICAR - Krishi Vigyan Kendra')}
            </Text>
          </View>
          <View style={styles.counterBadge}>
            <Text style={styles.counterText}>
              {pendingVerificationCount} Pending
            </Text>
          </View>
        </View>

        {/* ============================================================== */}
        {/* Section: ತಜ್ಞರ ಪರಿಶೀಲನೆ ವಿನಂತಿಗಳು (Pending Verification) */}
        {/* ============================================================== */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>
            {isKn ? '🔬 ತಜ್ಞರ ಪರಿಶೀಲನೆ ವಿನಂತಿಗಳು' : '🔬 Pending Verification'}
          </Text>
          {isLoadingQueue && <ActivityIndicator size="small" color="#0F766E" />}
        </View>

        <View style={styles.list}>
          {verificationRequests.map((item) => {
            const formattedDate = item.requested_at
              ? new Date(item.requested_at).toLocaleDateString('en-GB', {
                  day: '2-digit',
                  month: 'short',
                  year: 'numeric',
                })
              : '26 Sep 2026';

            const statusDisplay =
              item.status === 'VERIFIED'
                ? 'Verified'
                : item.status === 'NEED_MORE_INFO'
                ? 'Requires More Info'
                : 'Pending Review';

            const isItemVerified = item.status === 'VERIFIED';
            const isItemNeedInfo = item.status === 'NEED_MORE_INFO';

            return (
              <View
                key={item.id}
                style={[
                  styles.requestCard,
                  isItemVerified && styles.cardVerified,
                  isItemNeedInfo && styles.cardNeedInfo,
                ]}
              >
                {/* Header Badge */}
                <View style={styles.requestCardHeader}>
                  <View style={styles.requestTitleRow}>
                    <Microscope size={16} color="#0F766E" />
                    <Text style={styles.requestCardTitle}>ತಜ್ಞರ ಪರಿಶೀಲನೆ</Text>
                  </View>
                  <View style={styles.paymentBadge}>
                    <ShieldCheck size={12} color="#15803D" />
                    <Text style={styles.paymentBadgeText}>
                      ₹{item.payment_amount || 49} • Paid
                    </Text>
                  </View>
                </View>

                {/* Details Grid */}
                <View style={styles.detailsGrid}>
                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>ಬೆಳೆ:</Text>
                    <Text style={styles.detailValue}>{item.crop_name || 'ಅಡಿಕೆ / Arecanut'}</Text>
                  </View>

                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>AI ಫಲಿತಾಂಶ:</Text>
                    <Text style={[styles.detailValue, styles.diseaseHighlight]}>
                      {item.diagnosis || item.latest_diagnosis?.predicted_class || 'Koleroga / Mahali'}
                    </Text>
                  </View>

                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>AI Confidence:</Text>
                    <Text style={styles.detailValue}>
                      {Math.round((item.ai_confidence ?? item.latest_diagnosis?.confidence ?? 0.73) * 100)}%
                    </Text>
                  </View>

                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>ಸ್ಥಿತಿ:</Text>
                    <Text
                      style={[
                        styles.detailValue,
                        isItemVerified ? styles.statusVerified : isItemNeedInfo ? styles.statusNeedInfo : styles.statusPending,
                      ]}
                    >
                      {statusDisplay}
                    </Text>
                  </View>

                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>ಪಾವತಿ:</Text>
                    <Text style={styles.detailValue}>
                      ₹{item.payment_amount || 49} • Paid
                    </Text>
                  </View>

                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>ದಿನಾಂಕ:</Text>
                    <Text style={styles.detailValue}>{formattedDate}</Text>
                  </View>
                </View>

                {/* Action button */}
                <TouchableOpacity
                  style={styles.reviewBtn}
                  activeOpacity={0.85}
                  onPress={() => setSelectedRequest(item)}
                >
                  <FileText size={14} color="#FFFFFF" />
                  <Text style={styles.reviewBtnText}>ವರದಿ ಪರಿಶೀಲಿಸಿ</Text>
                </TouchableOpacity>
              </View>
            );
          })}
          {verificationRequests.length === 0 && !isLoadingQueue && (
            <View style={styles.emptyContainer}>
              <FileText size={32} color="#94A3B8" />
              <Text style={styles.emptyText}>
                {isKn ? 'ಯಾವುದೇ ಹೊಸ ತಜ್ಞರ ಪರಿಶೀಲನೆ ವಿನಂತಿಗಳಿಲ್ಲ' : 'No pending expert review requests'}
              </Text>
            </View>
          )}
        </View>
      </ScrollView>

      {/* ============================================================== */}
      {/* Expert Review Modal: [ ವರದಿ ಪರಿಶೀಲಿಸಿ ] */}
      {/* ============================================================== */}
      <Modal
        visible={!!selectedRequest}
        transparent
        animationType="slide"
        onRequestClose={() => setSelectedRequest(null)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            {/* Modal Header */}
            <View style={styles.modalHeaderRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.modalTitleKn}>ವರದಿ ಪರಿಶೀಲನೆ</Text>
                <Text style={styles.modalSubtitle}>
                  🔬 ತಜ್ಞರ ಪರಿಶೀಲನೆ • ID: {selectedRequest?.crop_report_id.slice(0, 8)}
                </Text>
              </View>
              <TouchableOpacity
                onPress={() => setSelectedRequest(null)}
                style={styles.modalCloseBtn}
                activeOpacity={0.7}
              >
                <X size={20} color="#64748B" />
              </TouchableOpacity>
            </View>

            {/* Diagnostic Information Card */}
            <View style={styles.modalInfoCard}>
              {selectedRequest?.image_storage_path ? (
                <View style={styles.modalImageCard}>
                  <Image
                    source={{
                      uri: selectedRequest.image_storage_path.startsWith('http')
                        ? selectedRequest.image_storage_path
                        : `https://offmpvifgmzvclrvzweq.supabase.co/storage/v1/object/public/crop-report-images/${selectedRequest.image_storage_path}`,
                    }}
                    style={styles.modalImage}
                    resizeMode="cover"
                  />
                </View>
              ) : null}

              <View style={styles.modalInfoRow}>
                <Text style={styles.modalInfoLabel}>ಬೆಳೆ (Crop):</Text>
                <Text style={styles.modalInfoValue}>
                  {selectedRequest?.crop_name || 'ಅಡಿಕೆ / Arecanut'}
                </Text>
              </View>

              <View style={styles.modalInfoRow}>
                <Text style={styles.modalInfoLabel}>AI ಫಲಿತಾಂಶ (Diagnosis):</Text>
                <Text style={[styles.modalInfoValue, styles.diseaseHighlight]}>
                  {selectedRequest?.diagnosis || selectedRequest?.latest_diagnosis?.predicted_class || 'Koleroga / Mahali'}
                </Text>
              </View>

              <View style={styles.modalInfoRow}>
                <Text style={styles.modalInfoLabel}>AI Confidence:</Text>
                <Text style={styles.modalInfoValue}>
                  {Math.round((selectedRequest?.ai_confidence ?? selectedRequest?.latest_diagnosis?.confidence ?? 0.73) * 100)}%
                </Text>
              </View>

              <View style={styles.modalInfoRow}>
                <Text style={styles.modalInfoLabel}>ಸ್ಥಿತಿ (Status):</Text>
                <Text style={[styles.modalInfoValue, { fontWeight: '800' }]}>
                  {selectedRequest?.status}
                </Text>
              </View>

              <View style={styles.modalInfoRow}>
                <Text style={styles.modalInfoLabel}>ಪಾವತಿ (Payment):</Text>
                <Text style={styles.modalInfoValue}>
                  ₹{selectedRequest?.payment_amount || 49} • Paid ({selectedRequest?.payment_mode || 'DEMO'})
                </Text>
              </View>

              <View style={styles.modalInfoRow}>
                <Text style={styles.modalInfoLabel}>ದಿನಾಂಕ (Date):</Text>
                <Text style={styles.modalInfoValue}>
                  {selectedRequest?.requested_at
                    ? new Date(selectedRequest.requested_at).toLocaleString()
                    : '26 Sep 2026'}
                </Text>
              </View>
            </View>

            {/* Status Announcement if already resolved */}
            {selectedRequest?.status === 'VERIFIED' && (
              <View style={styles.resolvedBadgeVerified}>
                <CheckCircle2 size={16} color="#15803D" />
                <Text style={styles.resolvedTextVerified}>
                  ✓ ಈ ವರದಿಯನ್ನು ಕೃಷಿ ತಜ್ಞರಿಂದ ಅಧಿಕೃತವಾಗಿ ದೃಢೀಕರಿಸಲಾಗಿದೆ (VERIFIED).
                </Text>
              </View>
            )}

            {selectedRequest?.status === 'NEED_MORE_INFO' && (
              <View style={styles.resolvedBadgeNeedInfo}>
                <AlertCircle size={16} color="#B45309" />
                <Text style={styles.resolvedTextNeedInfo}>
                  ⚠️ ರೈತರಿಂದ ಹೆಚ್ಚಿನ ಮಾಹಿತಿ/ಸ್ಪಷ್ಟ ಫೋಟೋ ಅಪೇಕ್ಷಿಸಲಾಗಿದೆ (REQUIRES_MORE_INFORMATION).
                </Text>
              </View>
            )}

            {/* Action Buttons for Expert: PENDING -> VERIFIED or REQUIRES_MORE_INFORMATION */}
            {selectedRequest?.status === 'PENDING' && (
              <View style={styles.decisionActions}>
                <TouchableOpacity
                  style={[styles.decisionBtn, styles.btnVerify]}
                  activeOpacity={0.85}
                  disabled={isSubmittingDecision}
                  onPress={() => handleDecision('VERIFIED')}
                >
                  {isSubmittingDecision ? (
                    <ActivityIndicator size="small" color="#FFFFFF" />
                  ) : (
                    <>
                      <CheckCircle2 size={16} color="#FFFFFF" />
                      <Text style={styles.decisionBtnText}>ದೃಢೀಕರಿಸಿ (VERIFIED)</Text>
                    </>
                  )}
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.decisionBtn, styles.btnNeedInfo]}
                  activeOpacity={0.85}
                  disabled={isSubmittingDecision}
                  onPress={() => handleDecision('REQUIRES_MORE_INFORMATION')}
                >
                  <HelpCircle size={16} color="#92400E" />
                  <Text style={styles.decisionBtnTextNeedInfo}>
                    ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಅಗತ್ಯವಿದೆ (REQUIRES MORE INFO)
                  </Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC' },
  scrollContent: { padding: Spacing.md, paddingBottom: 40, gap: 12 },
  topCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#0F766E',
    borderRadius: BorderRadius.md,
    padding: 12,
  },
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: BorderRadius.sm,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  topTitle: { fontSize: 14, fontWeight: '800', color: '#FFFFFF' },
  topSub: { fontSize: 11, color: '#CCFBF1' },
  counterBadge: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
  },
  counterText: { fontSize: 10, fontWeight: '800', color: '#FFFFFF' },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  sectionTitle: { fontSize: 13, fontWeight: '800', color: Colors.textPrimary },
  list: { gap: 10 },

  // Expert Review Request Card
  requestCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 10,
  },
  cardVerified: { backgroundColor: '#F0FDF4', borderColor: '#BBF7D0' },
  cardNeedInfo: { backgroundColor: '#FFFBEB', borderColor: '#FDE68A' },
  requestCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  requestTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  requestCardTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#0F766E',
  },
  paymentBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: BorderRadius.full,
  },
  paymentBadgeText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#15803D',
  },
  detailsGrid: {
    gap: 4,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 2,
  },
  detailLabel: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '600',
  },
  detailValue: {
    fontSize: 12,
    color: '#1E293B',
    fontWeight: '700',
  },
  diseaseHighlight: {
    color: '#DC2626',
    fontWeight: '800',
  },
  statusPending: {
    color: '#D97706',
  },
  statusVerified: {
    color: '#15803D',
  },
  statusNeedInfo: {
    color: '#B45309',
  },
  reviewBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#0F766E',
    paddingVertical: 10,
    borderRadius: BorderRadius.sm,
    marginTop: 4,
  },
  reviewBtnText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#FFFFFF',
  },

  // Existing Inbound Cases Styles
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 8,
  },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  nameText: { fontSize: 13, fontWeight: '800', color: Colors.textPrimary },
  locText: { fontSize: 11, color: Colors.textSecondary, marginTop: 1 },
  feeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  feeText: { fontSize: 10, fontWeight: '800', color: '#166534' },
  findingBox: { backgroundColor: '#F8FAFC', padding: 8, borderRadius: BorderRadius.sm, gap: 2 },
  diseaseText: { fontSize: 11, fontWeight: '700', color: '#DC2626' },
  remedyText: { fontSize: 11, color: '#334155' },
  actionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#0F766E',
    paddingVertical: 10,
    borderRadius: BorderRadius.sm,
  },
  actionBtnText: { fontSize: 11, fontWeight: '800', color: '#FFFFFF' },
  signedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    backgroundColor: '#DCFCE7',
    paddingVertical: 6,
    borderRadius: BorderRadius.sm,
  },
  signedText: { fontSize: 11, fontWeight: '700', color: '#166534' },

  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.65)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: Spacing.xl,
    gap: 16,
    maxHeight: '85%',
  },
  modalHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  modalTitleKn: {
    fontSize: 18,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  modalSubtitle: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  modalCloseBtn: {
    padding: 6,
  },
  modalInfoCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 14,
    gap: 8,
  },
  modalInfoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  modalInfoLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748B',
  },
  modalInfoValue: {
    fontSize: 12,
    fontWeight: '700',
    color: '#1E293B',
  },
  resolvedBadgeVerified: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#DCFCE7',
    padding: 12,
    borderRadius: BorderRadius.sm,
  },
  resolvedTextVerified: {
    fontSize: 12,
    fontWeight: '700',
    color: '#15803D',
    flex: 1,
  },
  resolvedBadgeNeedInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FEF3C7',
    padding: 12,
    borderRadius: BorderRadius.sm,
  },
  resolvedTextNeedInfo: {
    fontSize: 12,
    fontWeight: '700',
    color: '#92400E',
    flex: 1,
  },
  decisionActions: {
    gap: 10,
    marginTop: 4,
  },
  decisionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 13,
    borderRadius: BorderRadius.md,
  },
  btnVerify: {
    backgroundColor: '#15803D',
  },
  btnNeedInfo: {
    backgroundColor: '#FFFBEB',
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  decisionBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '800',
  },
  decisionBtnTextNeedInfo: {
    color: '#92400E',
    fontSize: 13,
    fontWeight: '800',
  },
  modalImageCard: {
    width: '100%',
    height: 180,
    borderRadius: BorderRadius.md,
    overflow: 'hidden',
    marginBottom: Spacing.sm,
    backgroundColor: '#E2E8F0',
  },
  modalImage: {
    width: '100%',
    height: '100%',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 36,
    gap: 8,
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginTop: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#64748B',
    fontWeight: '600',
  },
});
