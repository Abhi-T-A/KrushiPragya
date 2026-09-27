import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Modal,
  Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  fetchMyTransactions,
  TransactionDetail,
} from '../../services/marketApi';
import {
  Receipt,
  CheckCircle2,
  Clock,
  MapPin,
  ShieldCheck,
  ChevronRight,
  CreditCard,
  X,
  FileCheck,
  Download,
  Share2,
} from 'lucide-react-native';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface BuyerTransactionsScreenProps {
  navigation: any;
}

export const BuyerTransactionsScreen: React.FC<BuyerTransactionsScreenProps> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { language } = useLanguage();
  const { user } = useAuth();
  const isKn = language === 'kn';

  const [transactions, setTransactions] = useState<TransactionDetail[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Transaction Detail Modal
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedTxn, setSelectedTxn] = useState<TransactionDetail | null>(null);

  const buyerId = user?.id || '11111111-1111-4111-8111-111111111114';

  const loadTransactions = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchMyTransactions(buyerId);
      setTransactions(data);
    } catch (e) {
      console.warn('Failed to load transactions:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [buyerId]);

  useEffect(() => {
    loadTransactions();
  }, [loadTransactions]);

  const onRefresh = () => {
    setRefreshing(true);
    loadTransactions();
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.iconCircle}>
            <Receipt size={20} color="#16A34A" />
          </View>
          <View>
            <Text style={styles.headerTitle}>
              {isKn ? 'ವಹಿವಾಟು ಇತಿಹಾಸ' : 'My Transactions'}
            </Text>
            <Text style={styles.headerSub}>
              {isKn ? 'ದೃಢೀಕರಿಸಲ್ಪಟ್ಟ ಖರೀದಿ ಒಪ್ಪಂದಗಳು & ರಶೀದಿ' : 'Settled Escrow & Active Trade History'}
            </Text>
          </View>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.primary]} />}
      >
        {loading && !refreshing ? (
          <View style={styles.centerLoading}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingText}>
              {isKn ? 'ವಹಿವಾಟುಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...' : 'Loading transactions...'}
            </Text>
          </View>
        ) : transactions.length === 0 ? (
          <View style={styles.emptyCard}>
            <Receipt size={40} color="#CBD5E1" />
            <Text style={styles.emptyTitle}>
              {isKn ? 'ಯಾವುದೇ ವಹಿವಾಟುಗಳು ದಾಖಲಾಗಿಲ್ಲ' : 'No Transactions Found'}
            </Text>
            <Text style={styles.emptySub}>
              {isKn ? 'ಅಂಗೀಕೃತ ಆಫರ್‌ಗಳಿಗೆ ಪಾವತಿ ಮಾಡಿದಾಗ ಇಲ್ಲಿ ದಾಖಲಾಗುತ್ತವೆ.' : 'Completed payments will appear here as formal transactions.'}
            </Text>
          </View>
        ) : (
          <View style={styles.txnsList}>
            {transactions.map((txn) => {
              const isPaid = txn.payment_status === 'PAID';

              return (
                <View key={txn.id} style={styles.txnCard}>
                  <View style={styles.cardHeaderRow}>
                    <View style={{ flex: 1 }}>
                      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                        <Text style={styles.cropTitleText}>
                          {txn.crop_name || 'Farmer Produce'}
                        </Text>
                        <View style={[styles.statusBadge, isPaid ? styles.bgGreenLight : styles.bgOrangeLight]}>
                          <Text style={[styles.statusBadgeText, isPaid ? styles.textGreen : styles.textOrange]}>
                            {isPaid ? (isKn ? 'ಪಾವತಿಸಲಾಗಿದೆ ✓' : 'Paid ✓') : (isKn ? 'ಪಾವತಿ ಬಾಕಿ' : 'Awaiting Payment')}
                          </Text>
                        </View>
                      </View>
                      <Text style={styles.txnIdText}>{txn.id}</Text>
                    </View>

                    <View style={{ alignItems: 'flex-end' }}>
                      <Text style={styles.amountText}>
                        ₹{Number(txn.amount).toLocaleString('en-IN')}
                      </Text>
                      <Text style={styles.qtyText}>
                        {txn.quantity} {txn.unit || 'kg'}
                      </Text>
                    </View>
                  </View>

                  <View style={styles.farmerDetailRow}>
                    <Text style={styles.farmerText}>
                      👨‍🌾 {txn.farmer_name || 'Demo Farmer'}
                    </Text>
                    <Text style={styles.dateText}>
                      {new Date(txn.created_at).toLocaleDateString()}
                    </Text>
                  </View>

                  <TouchableOpacity
                    style={styles.viewDetailBtn}
                    onPress={() => {
                      setSelectedTxn(txn);
                      setDetailModalVisible(true);
                    }}
                    activeOpacity={0.8}
                  >
                    <Text style={styles.viewDetailBtnText}>
                      {isKn ? 'ವಹಿವಾಟು ವಿವರ ನೋಡಿ' : 'View Transaction'}
                    </Text>
                    <ChevronRight size={14} color="#D97706" />
                  </TouchableOpacity>
                </View>
              );
            })}
          </View>
        )}
      </ScrollView>

      {/* ============================================================== */}
      {/* Transaction Detail Modal (Section 9) */}
      {/* ============================================================== */}
      <Modal
        visible={detailModalVisible}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setDetailModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalSheet, { paddingBottom: Math.max(insets.bottom, 20) }]}>
            <View style={styles.modalSheetHeader}>
              <View style={{ flex: 1 }}>
                <Text style={styles.modalSheetTitle}>
                  {isKn ? 'ವಹಿವಾಟು ವಿವರ (Transaction)' : 'Transaction Record'}
                </Text>
                <Text style={styles.modalSheetId}>{selectedTxn?.id}</Text>
              </View>
              <TouchableOpacity onPress={() => setDetailModalVisible(false)} style={styles.closeBtn}>
                <X size={18} color="#64748B" />
              </TouchableOpacity>
            </View>

            {selectedTxn && (
              <ScrollView showsVerticalScrollIndicator={false} style={styles.modalBody}>
                {/* Information Grid */}
                <View style={styles.detailsGrid}>
                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>{isKn ? 'ಉತ್ಪನ್ನ (Produce)' : 'Produce'}</Text>
                    <Text style={styles.detailValue}>{selectedTxn.crop_name}</Text>
                  </View>

                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>{isKn ? 'ಪ್ರಮಾಣ (Quantity)' : 'Quantity'}</Text>
                    <Text style={styles.detailValue}>{selectedTxn.quantity} {selectedTxn.unit}</Text>
                  </View>

                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>{isKn ? 'ಒಪ್ಪಿಕೊಂಡ ಬೆಲೆ (Agreed Price)' : 'Agreed Price'}</Text>
                    <Text style={[styles.detailValue, { color: '#B45309', fontWeight: '900' }]}>
                      ₹{Number(selectedTxn.amount).toLocaleString('en-IN')}
                    </Text>
                  </View>

                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>{isKn ? 'ರೈತರು (Farmer)' : 'Farmer'}</Text>
                    <Text style={styles.detailValue}>{selectedTxn.farmer_name}</Text>
                  </View>

                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>{isKn ? 'ಖರೀದಿದಾರರು (Buyer)' : 'Buyer'}</Text>
                    <Text style={styles.detailValue}>{selectedTxn.buyer_name || 'Rajesh Seth'}</Text>
                  </View>

                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>{isKn ? 'ಸ್ಥಳ (Location)' : 'Location'}</Text>
                    <Text style={styles.detailValue}>Ujire (ಉಜಿರೆ)</Text>
                  </View>

                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>{isKn ? 'ಪಾವತಿ ಸ್ಥಿತಿ' : 'Payment Status'}</Text>
                    <View style={styles.paidCheckBadge}>
                      <CheckCircle2 size={13} color="#16A34A" />
                      <Text style={styles.paidCheckText}>Completed</Text>
                    </View>
                  </View>

                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>{isKn ? 'ವಹಿವಾಟಿನ ಸ್ಥಿತಿ' : 'Transaction Status'}</Text>
                    <Text style={[styles.detailValue, { color: '#D97706', fontWeight: '800' }]}>ACTIVE</Text>
                  </View>
                </View>

                {/* 6-Stage Lifecycle Timeline (Section 9) */}
                <View style={styles.timelineCard}>
                  <Text style={styles.timelineTitle}>{isKn ? 'ವಹಿವಾಟಿನ ಪ್ರಕ್ರಿಯೆ (Timeline)' : 'Lifecycle Timeline:'}</Text>

                  <View style={styles.timelineList}>
                    <View style={styles.timelineItem}>
                      <View style={[styles.timelineDot, styles.dotDone]}>
                        <Text style={styles.dotCheckText}>✓</Text>
                      </View>
                      <Text style={styles.timelineItemText}>Listing Created</Text>
                    </View>

                    <View style={styles.timelineConnector} />

                    <View style={styles.timelineItem}>
                      <View style={[styles.timelineDot, styles.dotDone]}>
                        <Text style={styles.dotCheckText}>✓</Text>
                      </View>
                      <Text style={styles.timelineItemText}>Offer Submitted</Text>
                    </View>

                    <View style={styles.timelineConnector} />

                    <View style={styles.timelineItem}>
                      <View style={[styles.timelineDot, styles.dotDone]}>
                        <Text style={styles.dotCheckText}>✓</Text>
                      </View>
                      <Text style={styles.timelineItemText}>Offer Accepted</Text>
                    </View>

                    <View style={styles.timelineConnector} />

                    <View style={styles.timelineItem}>
                      <View style={[styles.timelineDot, styles.dotDone]}>
                        <Text style={styles.dotCheckText}>✓</Text>
                      </View>
                      <Text style={styles.timelineItemText}>Payment Completed</Text>
                    </View>

                    <View style={styles.timelineConnector} />

                    <View style={styles.timelineItem}>
                      <View style={[styles.timelineDot, styles.dotActive]}>
                        <View style={styles.dotActiveInner} />
                      </View>
                      <Text style={[styles.timelineItemText, { fontWeight: '800', color: '#D97706' }]}>
                        Transaction Active (Ready for Yard Delivery)
                      </Text>
                    </View>

                    <View style={styles.timelineConnector} />

                    <View style={styles.timelineItem}>
                      <View style={[styles.timelineDot, styles.dotPending]} />
                      <Text style={[styles.timelineItemText, { color: '#94A3B8' }]}>Completed</Text>
                    </View>
                  </View>
                </View>

                {/* Guarantee Note */}
                <View style={styles.apmcNoteCard}>
                  <ShieldCheck size={16} color="#15803D" />
                  <Text style={styles.apmcNoteText}>
                    {isKn
                      ? 'ಕರ್ನಾಟಕ ಎಪಿಎಂಸಿ ಕಾಯ್ದೆ ಪ್ರಕಾರ ಡಿಜಿಟಲ್ ಇನ್‌ವಾಯ್ಸ್ ಮತ್ತು ಗೋದಾಮು ರಶೀದಿ ಸಿದ್ಧವಾಗಿದೆ.'
                      : 'Digital contract verified under Karnataka APMC Market Trade guidelines.'}
                  </Text>
                </View>
              </ScrollView>
            )}

            <View style={styles.modalSheetActions}>
              <TouchableOpacity
                style={styles.sheetCloseBtn}
                onPress={() => setDetailModalVisible(false)}
                activeOpacity={0.7}
              >
                <Text style={styles.sheetCloseBtnText}>{isKn ? 'ಮುಚ್ಚಿ' : 'Close'}</Text>
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
  txnsList: {
    gap: 12,
  },
  txnCard: {
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
  cardHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  cropTitleText: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
  },
  txnIdText: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
    fontWeight: '600',
  },
  statusBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  bgGreenLight: {
    backgroundColor: '#DCFCE7',
  },
  bgOrangeLight: {
    backgroundColor: '#FEF3C7',
  },
  textGreen: {
    color: '#16A34A',
  },
  textOrange: {
    color: '#D97706',
  },
  statusBadgeText: {
    fontSize: 10,
    fontWeight: '800',
  },
  amountText: {
    fontSize: 16,
    fontWeight: '900',
    color: '#B45309',
  },
  qtyText: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 1,
  },
  farmerDetailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
  },
  farmerText: {
    fontSize: 12,
    color: '#334155',
  },
  dateText: {
    fontSize: 11,
    color: '#94A3B8',
  },
  viewDetailBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#FFFBEB',
    borderWidth: 1,
    borderColor: '#FEF3C7',
  },
  viewDetailBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#D97706',
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
    maxHeight: '90%',
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
  modalSheetId: {
    fontSize: 12,
    color: '#D97706',
    fontWeight: '700',
    marginTop: 2,
  },
  closeBtn: {
    padding: 4,
  },
  modalBody: {
    marginTop: 14,
  },
  detailsGrid: {
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 8,
    marginBottom: 14,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 11.5,
    color: '#64748B',
  },
  detailValue: {
    fontSize: 12.5,
    fontWeight: '700',
    color: '#1E293B',
  },
  paidCheckBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  paidCheckText: {
    fontSize: 10.5,
    fontWeight: '800',
    color: '#16A34A',
  },
  timelineCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 14,
    marginBottom: 14,
  },
  timelineTitle: {
    fontSize: 12.5,
    fontWeight: '800',
    color: '#0F172A',
    marginBottom: 10,
  },
  timelineList: {
    gap: 2,
  },
  timelineItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  timelineDot: {
    width: 20,
    height: 20,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dotDone: {
    backgroundColor: '#16A34A',
  },
  dotActive: {
    backgroundColor: '#FEF3C7',
    borderWidth: 2,
    borderColor: '#D97706',
  },
  dotActiveInner: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#D97706',
  },
  dotPending: {
    borderWidth: 2,
    borderColor: '#CBD5E1',
    backgroundColor: '#F8FAFC',
  },
  dotCheckText: {
    fontSize: 11,
    color: '#FFFFFF',
    fontWeight: '900',
  },
  timelineItemText: {
    fontSize: 12,
    color: '#334155',
    fontWeight: '600',
  },
  timelineConnector: {
    width: 2,
    height: 12,
    backgroundColor: '#CBD5E1',
    marginLeft: 9,
  },
  apmcNoteCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F0FDF4',
    borderRadius: 8,
    padding: 10,
    borderWidth: 1,
    borderColor: '#DCFCE7',
    marginBottom: 16,
  },
  apmcNoteText: {
    fontSize: 11,
    color: '#15803D',
    flex: 1,
    lineHeight: 16,
  },
  modalSheetActions: {
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
  },
  sheetCloseBtn: {
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  sheetCloseBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#475569',
  },
});
