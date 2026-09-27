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
  Alert,
  Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  fetchBuyerOffers,
  completeDemoPayment,
  BuyerOfferItem,
  TransactionDetail,
} from '../../services/marketApi';
import {
  Tag,
  Clock,
  CheckCircle2,
  XCircle,
  CreditCard,
  MapPin,
  Sparkles,
  Phone,
  ShieldCheck,
  ChevronRight,
  DollarSign,
  Receipt,
  X,
  Store,
} from 'lucide-react-native';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

type StatusFilter = 'ALL' | 'PENDING' | 'ACCEPTED' | 'COMPLETED';

interface BuyerOffersScreenProps {
  navigation: any;
}

export const BuyerOffersScreen: React.FC<BuyerOffersScreenProps> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { language } = useLanguage();
  const { user } = useAuth();
  const isKn = language === 'kn';

  const [offers, setOffers] = useState<BuyerOfferItem[]>([]);
  const [filter, setFilter] = useState<StatusFilter>('ALL');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Payment Confirmation Modal
  const [paymentModalVisible, setPaymentModalVisible] = useState(false);
  const [selectedOfferForPay, setSelectedOfferForPay] = useState<BuyerOfferItem | null>(null);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);

  const buyerId = user?.id || '11111111-1111-4111-8111-111111111114';

  const loadOffers = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchBuyerOffers(buyerId);
      setOffers(data);
    } catch (err) {
      console.warn('Failed to load buyer offers:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [buyerId]);

  useEffect(() => {
    loadOffers();
  }, [loadOffers]);

  const onRefresh = () => {
    setRefreshing(true);
    loadOffers();
  };

  const filteredOffers = offers.filter((o) => {
    if (filter === 'ALL') return true;
    return o.offer.status === filter;
  });

  const handleStartPayment = (offerItem: BuyerOfferItem) => {
    setSelectedOfferForPay(offerItem);
    setPaymentModalVisible(true);
  };

  const handleConfirmPayment = async () => {
    if (!selectedOfferForPay) return;
    setIsProcessingPayment(true);
    try {
      const txn = await completeDemoPayment(buyerId, selectedOfferForPay);
      setIsProcessingPayment(false);
      setPaymentModalVisible(false);

      Alert.alert(
        isKn ? '✅ ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆ!' : '✅ Payment Successful!',
        isKn
          ? `ವಹಿವಾಟು ಸಂಖ್ಯೆ: ${txn.id}\nಸ್ಥಿತಿ: ಪಾವತಿ ಪೂರ್ಣಗೊಂಡಿದೆ (PAYMENT COMPLETED)\nವಹಿವಾಟು ಇತಿಹಾಸದಲ್ಲಿ ವಿವರಗಳು ದಾಖಲಾಗಿವೆ.`
          : `Transaction ID: ${txn.id}\nStatus: PAYMENT COMPLETED\nAmount: ₹${Number(txn.amount).toLocaleString('en-IN')}\n\nTransaction record has been updated and is active.`,
        [
          {
            text: isKn ? 'ವಹಿವಾಟು ನೋಡಿ' : 'View Transactions',
            onPress: () => navigation.navigate('BuyerTransactionsTab'),
          },
          {
            text: 'OK',
            onPress: () => loadOffers(),
          },
        ]
      );
    } catch (e) {
      setIsProcessingPayment(false);
      Alert.alert('Payment Error', 'Failed to process payment. Please try again.');
    }
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.iconCircle}>
            <Tag size={20} color="#16A34A" />
          </View>
          <View>
            <Text style={styles.headerTitle}>
              {isKn ? 'ನನ್ನ ಆಫರ್‌ಗಳು' : 'My Purchase Offers'}
            </Text>
            <Text style={styles.headerSub}>
              {isKn ? 'ರೈತರಿಗೆ ಸಲ್ಲಿಸಿದ ಖರೀದಿ ಬಿಡ್‌ಗಳು & ಪಾವತಿ' : 'Buyer Negotiation & Escrow Checkout'}
            </Text>
          </View>
        </View>
      </View>

      {/* Filter Tabs */}
      <View style={styles.filterTabs}>
        {(['ALL', 'PENDING', 'ACCEPTED', 'COMPLETED'] as StatusFilter[]).map((tab) => {
          const isSelected = filter === tab;
          let label: string = tab;
          if (tab === 'ALL') label = isKn ? 'ಎಲ್ಲವೂ' : 'All';
          if (tab === 'PENDING') label = isKn ? 'ಬಾಕಿ ಇದೆ' : 'Pending';
          if (tab === 'ACCEPTED') label = isKn ? 'ಅಂಗೀಕೃತ ✓' : 'Accepted ✓';
          if (tab === 'COMPLETED') label = isKn ? 'ಪೂರ್ಣಗೊಂಡಿದೆ' : 'Completed';

          const count = offers.filter((o) => (tab === 'ALL' ? true : o.offer.status === tab)).length;

          return (
            <TouchableOpacity
              key={tab}
              style={[styles.tabItem, isSelected && styles.tabItemActive]}
              onPress={() => setFilter(tab)}
              activeOpacity={0.7}
            >
              <Text style={[styles.tabLabel, isSelected && styles.tabLabelActive]}>
                {label} ({count})
              </Text>
            </TouchableOpacity>
          );
        })}
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
              {isKn ? 'ಆಫರ್‌ಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...' : 'Loading offers...'}
            </Text>
          </View>
        ) : filteredOffers.length === 0 ? (
          <View style={styles.emptyCard}>
            <Tag size={40} color="#CBD5E1" />
            <Text style={styles.emptyTitle}>
              {isKn ? 'ಯಾವುದೇ ಆಫರ್‌ಗಳು ಕಂಡುಬಂದಿಲ್ಲ' : 'No Offers in this Category'}
            </Text>
            <Text style={styles.emptySub}>
              {isKn ? 'ಮಾರುಕಟ್ಟೆಯಲ್ಲಿ ಹೊಸ ಆಫರ್‌ಗಳನ್ನು ಸಲ್ಲಿಸಲು ಬೆಳೆಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.' : 'Browse the produce marketplace to submit purchase offers.'}
            </Text>
          </View>
        ) : (
          <View style={styles.offersList}>
            {filteredOffers.map((item) => {
              const { offer, listing } = item;
              const isAccepted = offer.status === 'ACCEPTED';
              const isPending = offer.status === 'PENDING';
              const isCompleted = offer.status === 'COMPLETED';
              const isRejected = offer.status === 'REJECTED';

              const cropTitle = listing.crop_id ? listing.crop_id.replace('crop-', '').toUpperCase() : 'PRODUCE LOT';

              return (
                <View
                  key={offer.id}
                  style={[
                    styles.offerCard,
                    isAccepted ? styles.borderGreen : isPending ? styles.borderOrange : styles.borderGray,
                  ]}
                >
                  <View style={styles.cardTopRow}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.cropTitleText}>
                        {cropTitle} ({offer.quantity} {listing.unit || 'kg'})
                      </Text>
                      <Text style={styles.farmerDetailText}>
                        👨‍🌾 {item.contact_name || 'Farmer'} • 📍 {listing.location || 'Dakshina Kannada'}
                      </Text>
                    </View>

                    <View
                      style={[
                        styles.statusPill,
                        isAccepted
                          ? styles.bgGreenLight
                          : isPending
                          ? styles.bgOrangeLight
                          : isCompleted
                          ? styles.bgPurpleLight
                          : styles.bgGrayLight,
                      ]}
                    >
                      <Text
                        style={[
                          styles.statusPillText,
                          isAccepted
                            ? styles.textGreen
                            : isPending
                            ? styles.textOrange
                            : isCompleted
                            ? styles.textPurple
                            : styles.textGray,
                        ]}
                      >
                        {isAccepted
                          ? isKn
                            ? 'ಅಂಗೀಕೃತ ✓'
                            : 'ACCEPTED'
                          : isPending
                          ? isKn
                            ? 'ಪರಿಶೀಲನೆಯಲ್ಲಿದೆ'
                            : 'PENDING'
                          : isCompleted
                          ? isKn
                            ? 'ಪಾವತಿ ಪೂರ್ಣ'
                            : 'PAID ✓'
                          : isKn
                          ? 'ತಿರಸ್ಕೃತ'
                          : 'REJECTED'}
                      </Text>
                    </View>
                  </View>

                  {/* Amounts Row */}
                  <View style={styles.amountsRow}>
                    <View style={styles.amountCol}>
                      <Text style={styles.amountLabel}>{isKn ? 'ನಿಮ್ಮ ಆಫರ್ ದರ' : 'Your Offer'}</Text>
                      <Text style={styles.amountOffered}>
                        ₹{Number(offer.offered_price).toLocaleString('en-IN')}
                      </Text>
                    </View>

                    <View style={styles.amountCol}>
                      <Text style={styles.amountLabel}>{isKn ? 'ರೈತರ ನಿರೀಕ್ಷೆ' : 'Farmer Asking'}</Text>
                      <Text style={styles.amountAsking}>
                        ₹{Number(item.farmer_expected_price).toLocaleString('en-IN')}
                      </Text>
                    </View>

                    <View style={styles.amountCol}>
                      <Text style={styles.amountLabel}>{isKn ? 'ಪ್ರಮಾಣ' : 'Quantity'}</Text>
                      <Text style={styles.amountQty}>
                        {offer.quantity} {listing.unit || 'kg'}
                      </Text>
                    </View>
                  </View>

                  {offer.message ? (
                    <Text style={styles.offerMessageText}>"{offer.message}"</Text>
                  ) : null}

                  {/* Prominent Action for ACCEPTED offers: [ Pay ₹X ] (Section 7) */}
                  {isAccepted && (
                    <View style={styles.acceptedActionCard}>
                      <View style={styles.acceptedActionHeader}>
                        <CheckCircle2 size={16} color="#16A34A" />
                        <Text style={styles.acceptedActionTitle}>
                          {isKn ? 'ರೈತರು ನಿಮ್ಮ ಆಫರ್ ಅನ್ನು ಒಪ್ಪಿಕೊಂಡಿದ್ದಾರೆ!' : 'Offer Accepted by Farmer!'}
                        </Text>
                      </View>
                      <Text style={styles.acceptedActionDesc}>
                        {isKn
                          ? 'ವಹಿವಾಟನ್ನು ದೃಢೀಕರಿಸಲು ಹಾಗೂ ಗೋದಾಮು ಬಿಡುಗಡೆ ಕೋಡ್ ಪಡೆಯಲು ಪಾವತಿ ಮಾಡಿ.'
                          : 'Agreed Amount: ₹' +
                            Number(offer.offered_price).toLocaleString('en-IN') +
                            '. Complete payment to lock transaction.'}
                      </Text>

                      <TouchableOpacity
                        style={styles.payNowBtn}
                        onPress={() => handleStartPayment(item)}
                        activeOpacity={0.85}
                      >
                        <CreditCard size={15} color="#FFFFFF" />
                        <Text style={styles.payNowBtnText}>
                          {isKn
                            ? `₹${Number(offer.offered_price).toLocaleString('en-IN')} ಪಾವತಿಸಿ (Pay Now)`
                            : `Pay ₹${Number(offer.offered_price).toLocaleString('en-IN')}`}
                        </Text>
                      </TouchableOpacity>
                    </View>
                  )}

                  {isCompleted && (
                    <View style={styles.completedRow}>
                      <Receipt size={14} color="#7E22CE" />
                      <Text style={styles.completedText}>
                        {isKn ? 'ಪಾವತಿ ಯಶಸ್ವಿ • ವಹಿವಾಟು ಸಕ್ರಿಯವಾಗಿದೆ' : 'Payment completed • Escrow active'}
                      </Text>
                    </View>
                  )}
                </View>
              );
            })}
          </View>
        )}
      </ScrollView>

      {/* ============================================================== */}
      {/* Buyer Payment Modal (Section 7) */}
      {/* ============================================================== */}
      <Modal
        visible={paymentModalVisible}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setPaymentModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalSheet, { paddingBottom: Math.max(insets.bottom, 20) }]}>
            <View style={styles.modalSheetHeader}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <View style={[styles.iconCircle, { backgroundColor: '#DCFCE7' }]}>
                  <CheckCircle2 size={18} color="#16A34A" />
                </View>
                <View>
                  <Text style={styles.modalSheetTitle}>
                    {isKn ? 'ಖರೀದಿ ಪಾವತಿ (Offer Accepted ✓)' : 'Complete Escrow Payment'}
                  </Text>
                  <Text style={styles.modalSheetSub}>
                    {isKn ? 'ಎಪಿಎಂಸಿ ದೃಢೀಕೃತ ಎಸ್ಕ್ರೋ ವ್ಯವಸ್ಥೆ' : 'Secured Digital Settlement'}
                  </Text>
                </View>
              </View>
              <TouchableOpacity onPress={() => setPaymentModalVisible(false)} style={styles.closeBtn}>
                <X size={18} color="#64748B" />
              </TouchableOpacity>
            </View>

            {selectedOfferForPay && (
              <ScrollView showsVerticalScrollIndicator={false} style={styles.modalBody}>
                <View style={styles.billCard}>
                  <View style={styles.billRow}>
                    <Text style={styles.billLabel}>{isKn ? 'ಉತ್ಪನ್ನ (Produce)' : 'Produce'}</Text>
                    <Text style={styles.billValue}>
                      {selectedOfferForPay.listing.crop_id ? selectedOfferForPay.listing.crop_id.replace('crop-', '').toUpperCase() : 'Arecanut'}
                    </Text>
                  </View>

                  <View style={styles.billRow}>
                    <Text style={styles.billLabel}>{isKn ? 'ಖರೀದಿ ಪ್ರಮಾಣ' : 'Quantity'}</Text>
                    <Text style={styles.billValue}>
                      {selectedOfferForPay.offer.quantity} {selectedOfferForPay.listing.unit || 'kg'}
                    </Text>
                  </View>

                  <View style={styles.billRow}>
                    <Text style={styles.billLabel}>{isKn ? 'ರೈತರ ಹೆಸರು' : 'Farmer'}</Text>
                    <Text style={styles.billValue}>
                      {selectedOfferForPay.contact_name || 'Demo Farmer 1'}
                    </Text>
                  </View>

                  <View style={styles.billRow}>
                    <Text style={styles.billLabel}>{isKn ? 'ಸ್ಥಳ (Location)' : 'Location'}</Text>
                    <Text style={styles.billValue}>
                      {selectedOfferForPay.listing.location || 'Ujire'}
                    </Text>
                  </View>

                  <View style={[styles.billRow, styles.totalRow]}>
                    <Text style={styles.totalLabel}>{isKn ? 'ಒಪ್ಪಿಕೊಂಡ ಮೊತ್ತ' : 'Agreed Amount'}</Text>
                    <Text style={styles.totalValue}>
                      ₹{Number(selectedOfferForPay.offer.offered_price).toLocaleString('en-IN')}
                    </Text>
                  </View>
                </View>

                {/* Gateway assurance badge */}
                <View style={styles.gatewayBadge}>
                  <ShieldCheck size={16} color="#15803D" />
                  <Text style={styles.gatewayBadgeText}>
                    {isKn
                      ? 'ಡಿಜಿಟಲ್ ಎಸ್ಕ್ರೋ ಖಾತ್ರಿ: ರೈತರಿಂದ ಉತ್ಪನ್ನ ಪರಿಶೀಲನೆ ನಂತರವೇ ಹಣ ಬಿಡುಗಡೆಯಾಗುತ್ತದೆ.'
                      : 'APMC Digital Escrow: Funds released to farmer only upon physical produce receipt.'}
                  </Text>
                </View>
              </ScrollView>
            )}

            <View style={styles.modalActionsRow}>
              <TouchableOpacity
                style={styles.modalCancelBtn}
                onPress={() => setPaymentModalVisible(false)}
                activeOpacity={0.7}
              >
                <Text style={styles.modalCancelBtnText}>{isKn ? 'ರದ್ದುಮಾಡಿ' : 'Cancel'}</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.modalConfirmPayBtn}
                onPress={handleConfirmPayment}
                disabled={isProcessingPayment}
                activeOpacity={0.85}
              >
                {isProcessingPayment ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <>
                    <CreditCard size={15} color="#FFFFFF" />
                    <Text style={styles.modalConfirmPayBtnText}>
                      {isKn
                        ? `₹${Number(selectedOfferForPay?.offer.offered_price || 0).toLocaleString('en-IN')} ಪಾವತಿಸಿ`
                        : `Pay ₹${Number(selectedOfferForPay?.offer.offered_price || 0).toLocaleString('en-IN')}`}
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
  filterTabs: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  tabItem: {
    paddingVertical: 10,
    paddingHorizontal: 10,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabItemActive: {
    borderBottomColor: Colors.primary,
  },
  tabLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748B',
  },
  tabLabelActive: {
    color: Colors.primary,
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
  offersList: {
    gap: 12,
  },
  offerCard: {
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
    gap: 10,
  },
  borderGreen: {
    borderLeftWidth: 4,
    borderLeftColor: '#16A34A',
  },
  borderOrange: {
    borderLeftWidth: 4,
    borderLeftColor: '#D97706',
  },
  borderGray: {
    borderLeftWidth: 4,
    borderLeftColor: '#94A3B8',
  },
  cardTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  cropTitleText: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
  },
  farmerDetailText: {
    fontSize: 11.5,
    color: '#64748B',
    marginTop: 2,
  },
  statusPill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  bgGreenLight: {
    backgroundColor: '#DCFCE7',
  },
  bgOrangeLight: {
    backgroundColor: '#FEF3C7',
  },
  bgPurpleLight: {
    backgroundColor: '#F3E8FF',
  },
  bgGrayLight: {
    backgroundColor: '#F1F5F9',
  },
  textGreen: {
    color: '#16A34A',
  },
  textOrange: {
    color: '#D97706',
  },
  textPurple: {
    color: '#7E22CE',
  },
  textGray: {
    color: '#64748B',
  },
  statusPillText: {
    fontSize: 10.5,
    fontWeight: '800',
  },
  amountsRow: {
    flexDirection: 'row',
    backgroundColor: '#F8FAFC',
    borderRadius: 8,
    padding: 10,
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  amountCol: {
    alignItems: 'center',
  },
  amountLabel: {
    fontSize: 10,
    color: '#64748B',
    fontWeight: '600',
  },
  amountOffered: {
    fontSize: 14,
    fontWeight: '800',
    color: '#D97706',
    marginTop: 2,
  },
  amountAsking: {
    fontSize: 13,
    fontWeight: '700',
    color: '#475569',
    marginTop: 2,
  },
  amountQty: {
    fontSize: 13,
    fontWeight: '700',
    color: '#1E293B',
    marginTop: 2,
  },
  offerMessageText: {
    fontSize: 11.5,
    fontStyle: 'italic',
    color: '#475569',
  },
  acceptedActionCard: {
    backgroundColor: '#F0FDF4',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#BBF7D0',
    padding: 12,
    gap: 6,
  },
  acceptedActionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  acceptedActionTitle: {
    fontSize: 12.5,
    fontWeight: '800',
    color: '#15803D',
  },
  acceptedActionDesc: {
    fontSize: 11,
    color: '#166534',
    lineHeight: 16,
  },
  payNowBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#16A34A',
    paddingVertical: 10,
    borderRadius: 8,
    marginTop: 6,
  },
  payNowBtnText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  completedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FAF5FF',
    padding: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#F3E8FF',
  },
  completedText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#7E22CE',
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
    maxHeight: '85%',
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
  modalBody: {
    marginTop: 14,
  },
  billCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 8,
  },
  billRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  billLabel: {
    fontSize: 12,
    color: '#64748B',
  },
  billValue: {
    fontSize: 13,
    fontWeight: '700',
    color: '#1E293B',
  },
  totalRow: {
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
    marginTop: 4,
  },
  totalLabel: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0F172A',
  },
  totalValue: {
    fontSize: 17,
    fontWeight: '900',
    color: '#16A34A',
  },
  gatewayBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F0FDF4',
    borderRadius: 8,
    padding: 10,
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#DCFCE7',
  },
  gatewayBadgeText: {
    fontSize: 11,
    color: '#15803D',
    flex: 1,
    lineHeight: 16,
  },
  modalActionsRow: {
    flexDirection: 'row',
    gap: 10,
    paddingTop: 14,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
  },
  modalCancelBtn: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  modalCancelBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#475569',
  },
  modalConfirmPayBtn: {
    flex: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: '#16A34A',
  },
  modalConfirmPayBtnText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#FFFFFF',
  },
});
