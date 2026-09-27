import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Linking,
  Alert,
} from 'react-native';
import { BuyerOfferItem, respondToOffer, createPaymentOrder } from '../../services/marketApi';
import {
  X,
  Check,
  XCircle,
  Phone,
  MessageCircle,
  User,
  ShieldCheck,
  Calendar,
  AlertCircle,
  CreditCard,
  CheckCircle2,
} from 'lucide-react-native';

interface OfferReviewModalProps {
  visible: boolean;
  offers: BuyerOfferItem[];
  farmerId: string;
  onClose: () => void;
  onRefresh: () => void;
}

export const OfferReviewModal: React.FC<OfferReviewModalProps> = ({
  visible,
  offers,
  farmerId,
  onClose,
  onRefresh,
}) => {
  const [actingOfferId, setActingOfferId] = useState<string | null>(null);
  const [payingOfferId, setPayingOfferId] = useState<string | null>(null);

  if (!visible) return null;

  const handleDemoPayment = async (offer: any, totalAmount: number) => {
    try {
      setPayingOfferId(offer.id);
      const idempotencyKey = `tx_farmer_demo_${offer.id}_${Date.now()}`;
      await createPaymentOrder(farmerId, offer.id, idempotencyKey, 'DEMO');
      Alert.alert(
        'ಡೆಮೊ ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆ ✅',
        `₹${Math.round(totalAmount).toLocaleString('en-IN')} ಮೊತ್ತದ ಡೆಮೊ ಪಾವತಿ ದೃಢೀಕರಿಸಲಾಗಿದೆ. ವಹಿವಾಟು ಯಶಸ್ವಿಯಾಗಿ ನವೀಕರಿಸಲಾಗಿದೆ.`
      );
      onRefresh();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'ಡೆಮೊ ಪಾವತಿ ವಿಫಲವಾಗಿದೆ.';
      Alert.alert('ದೋಷ', typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setPayingOfferId(null);
    }
  };

  const handleAction = async (offerId: string, action: 'ACCEPT' | 'REJECT') => {
    try {
      setActingOfferId(offerId);
      await respondToOffer(offerId, farmerId, action);
      Alert.alert(
        action === 'ACCEPT' ? 'ಆಫರ್ ಸ್ವೀಕರಿಸಲಾಗಿದೆ ✅' : 'ಆಫರ್ ತಿರಸ್ಕರಿಸಲಾಗಿದೆ ❌',
        action === 'ACCEPT'
          ? 'ವ್ಯಾಪಾರ ದೃಢೀಕರಿಸಲಾಗಿದೆ. ಖರೀದಿದಾರರ ಸಂಪರ್ಕ ವಿವರಗಳನ್ನು ಕೆಳಗೆ ನೋಡಬಹುದು.'
          : 'ಖರೀದಿದಾರರಿಗೆ ಆಫರ್ ತಿರಸ್ಕರಿಸಿದ ಮಾಹಿತಿ ತಲುಪಿದೆ.'
      );
      onRefresh();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'ಕ್ರಿಯೆ ವಿಫಲವಾಗಿದೆ.';
      Alert.alert('ದೋಷ', typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setActingOfferId(null);
    }
  };

  const handleCall = (phone: string) => {
    Linking.openURL(`tel:${phone}`);
  };

  const handleWhatsApp = (phone: string) => {
    const clean = phone.replace(/[^0-9]/g, '');
    Linking.openURL(`https://wa.me/91${clean}`);
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          {/* Header */}
          <View style={styles.header}>
            <View>
              <Text style={styles.headerTitle}>ಬಂದಿರುವ ಖರೀದಿ ಆಫರ್‌ಗಳು</Text>
              <Text style={styles.headerSubTitle}>
                ಒಟ್ಟು {offers.length} ಆಫರ್‌ಗಳು
              </Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
              <X size={20} color="#374151" />
            </TouchableOpacity>
          </View>

          <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollBody}>
            {offers.length === 0 ? (
              <View style={styles.emptyContainer}>
                <AlertCircle size={36} color="#9CA3AF" />
                <Text style={styles.emptyText}>ಇನ್ನೂ ಯಾವುದೇ ಆಫರ್ ಬಂದಿಲ್ಲ.</Text>
              </View>
            ) : (
              offers.map((item) => {
                const { offer, buyer_name, contact_phone, farmer_expected_price } = item;
                const totalAmount = Number(offer.offered_price) * Number(offer.quantity);
                const isActing = actingOfferId === offer.id;
                const isAccepted = offer.status === 'ACCEPTED';
                const isRejected = offer.status === 'REJECTED';

                return (
                  <View key={offer.id} style={[styles.offerCard, isAccepted && styles.acceptedCard]}>
                    {/* Buyer Info Row */}
                    <View style={styles.buyerHeader}>
                      <View style={styles.buyerAvatar}>
                        <User size={16} color="#114B32" />
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.buyerNameText}>
                          {buyer_name || 'ಖರೀದಿದಾರ / ವರ್ತಕ'}
                        </Text>
                        <Text style={styles.dateText}>
                          ಆಫರ್ ದಿನಾಂಕ: {new Date(offer.created_at).toLocaleDateString()}
                        </Text>
                      </View>

                      <View
                        style={[
                          styles.statusBadge,
                          isAccepted
                            ? styles.statusBadgeAccepted
                            : isRejected
                            ? styles.statusBadgeRejected
                            : styles.statusBadgePending,
                        ]}
                      >
                        <Text
                          style={[
                            styles.statusBadgeText,
                            isAccepted
                              ? styles.statusTextAccepted
                              : isRejected
                              ? styles.statusTextRejected
                              : styles.statusTextPending,
                          ]}
                        >
                          {isAccepted ? 'ಸ್ವೀಕರಿಸಲಾಗಿದೆ' : isRejected ? 'ತಿರಸ್ಕರಿಸಲಾಗಿದೆ' : 'ಬಾಕಿ ಇದೆ'}
                        </Text>
                      </View>
                    </View>

                    {/* Offer Pricing Details */}
                    <View style={styles.pricingGrid}>
                      <View style={styles.gridCol}>
                        <Text style={styles.gridLabel}>ಆಫರ್ ಬೆಲೆ</Text>
                        <Text style={styles.gridPrice}>
                          ₹{Number(offer.offered_price).toLocaleString('en-IN')}
                        </Text>
                        <Text style={styles.gridSub}>ಪ್ರತಿ ಘಟಕ</Text>
                      </View>

                      <View style={styles.gridDivider} />

                      <View style={styles.gridCol}>
                        <Text style={styles.gridLabel}>ಪ್ರಮಾಣ</Text>
                        <Text style={styles.gridValue}>
                          {offer.quantity}
                        </Text>
                        <Text style={styles.gridSub}>ಕೋರಿಕೆ</Text>
                      </View>

                      <View style={styles.gridDivider} />

                      <View style={styles.gridCol}>
                        <Text style={styles.gridLabel}>ಒಟ್ಟು ಮೊತ್ತ</Text>
                        <Text style={[styles.gridPrice, { color: '#166534' }]}>
                          ₹{Math.round(totalAmount).toLocaleString('en-IN')}
                        </Text>
                        <Text style={styles.gridSub}>ಅಂದಾಜು</Text>
                      </View>
                    </View>

                    {/* Buyer Message */}
                    {offer.message ? (
                      <View style={styles.messageBox}>
                        <Text style={styles.messageLabel}>ಖರೀದಿದಾರರ ಟಿಪ್ಪಣಿ:</Text>
                        <Text style={styles.messageContent}>{offer.message}</Text>
                      </View>
                    ) : null}

                    {/* Authorized Contact Information (Shown strictly after acceptance) */}
                    {isAccepted && contact_phone ? (
                      <View style={styles.contactRevealCard}>
                        <View style={styles.contactTitleRow}>
                          <ShieldCheck size={14} color="#15803D" />
                          <Text style={styles.contactTitleText}>
                            ಖರೀದಿದಾರರ ದೃಢೀಕೃತ ಸಂಪರ್ಕ ಸಂಖ್ಯೆ: {contact_phone}
                          </Text>
                        </View>

                        <View style={styles.contactActionButtons}>
                          <TouchableOpacity
                            activeOpacity={0.8}
                            onPress={() => handleCall(contact_phone)}
                            style={styles.callBtn}
                          >
                            <Phone size={14} color="#FFFFFF" />
                            <Text style={styles.callBtnText}>ಕರೆ ಮಾಡಿ</Text>
                          </TouchableOpacity>

                          <TouchableOpacity
                            activeOpacity={0.8}
                            onPress={() => handleWhatsApp(contact_phone)}
                            style={styles.whatsAppBtn}
                          >
                            <MessageCircle size={14} color="#FFFFFF" />
                            <Text style={styles.whatsAppBtnText}>WhatsApp</Text>
                          </TouchableOpacity>
                        </View>
                      </View>
                    ) : null}

                    {/* Farmer Demo Payment Action for Accepted Offer */}
                    {isAccepted && (
                      <View style={styles.demoPaymentBox}>
                        <TouchableOpacity
                          activeOpacity={0.88}
                          onPress={() => handleDemoPayment(offer, totalAmount)}
                          disabled={payingOfferId === offer.id}
                          style={styles.demoPayBtn}
                        >
                          {payingOfferId === offer.id ? (
                            <ActivityIndicator size="small" color="#FFFFFF" />
                          ) : (
                            <>
                              <CreditCard size={15} color="#FFFFFF" />
                              <Text style={styles.demoPayBtnText}>
                                💳 ಡೆಮೊ ಪಾವತಿ ದೃಢೀಕರಿಸಿ (DEMO PAYMENT ₹{Math.round(totalAmount).toLocaleString('en-IN')})
                              </Text>
                            </>
                          )}
                        </TouchableOpacity>
                        <Text style={styles.demoPayNote}>
                          DEMO PAYMENT: ನೈಜ ಡೇಟಾಬೇಸ್ ವಹಿವಾಟನ್ನು ಸೃಷ್ಟಿಸುತ್ತದೆ ಮತ್ತು ಪಾವತಿಯನ್ನು PAID ಎಂದು ಗುರುತಿಸುತ್ತದೆ.
                        </Text>
                      </View>
                    )}

                    {/* Completed Transaction Status */}
                    {offer.status === 'COMPLETED' && (
                      <View style={styles.completedBox}>
                        <CheckCircle2 size={16} color="#15803D" />
                        <Text style={styles.completedText}>
                          ✓ ವಹಿವಾಟು ಪೂರ್ಣಗೊಂಡಿದೆ • ಡೆಮೊ ಪಾವತಿ ಯಶಸ್ವಿ (PAID ₹{Math.round(totalAmount).toLocaleString('en-IN')})
                        </Text>
                      </View>
                    )}

                    {/* Action Buttons for Pending Offer */}
                    {offer.status === 'PENDING' && (
                      <View style={styles.cardActions}>
                        {isActing ? (
                          <ActivityIndicator color="#114B32" style={{ padding: 10 }} />
                        ) : (
                          <>
                            <TouchableOpacity
                              activeOpacity={0.8}
                              onPress={() => handleAction(offer.id, 'REJECT')}
                              style={styles.rejectBtn}
                            >
                              <XCircle size={15} color="#B91C1C" />
                              <Text style={styles.rejectBtnText}>ತಿರಸ್ಕರಿಸಿ</Text>
                            </TouchableOpacity>

                            <TouchableOpacity
                              activeOpacity={0.8}
                              onPress={() => handleAction(offer.id, 'ACCEPT')}
                              style={styles.acceptBtn}
                            >
                              <Check size={15} color="#FFFFFF" />
                              <Text style={styles.acceptBtnText}>ಸ್ವೀಕರಿಸಿ</Text>
                            </TouchableOpacity>
                          </>
                        )}
                      </View>
                    )}
                  </View>
                );
              })
            )}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '85%',
    paddingBottom: 24,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: '#111827',
  },
  headerSubTitle: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  closeBtn: {
    padding: 6,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
  },
  scrollBody: {
    padding: 16,
    gap: 12,
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
    gap: 10,
  },
  emptyText: {
    fontSize: 13,
    color: '#6B7280',
  },
  offerCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    padding: 14,
    gap: 10,
  },
  acceptedCard: {
    borderColor: '#86EFAC',
    backgroundColor: '#F0FDF4',
  },
  buyerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  buyerAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#EAF7EE',
    alignItems: 'center',
    justifyContent: 'center',
  },
  buyerNameText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
  },
  dateText: {
    fontSize: 10,
    color: '#6B7280',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  statusBadgePending: {
    backgroundColor: '#FEF3C7',
  },
  statusBadgeAccepted: {
    backgroundColor: '#DCFCE7',
  },
  statusBadgeRejected: {
    backgroundColor: '#FEE2E2',
  },
  statusBadgeText: {
    fontSize: 10,
    fontWeight: '700',
  },
  statusTextPending: {
    color: '#92400E',
  },
  statusTextAccepted: {
    color: '#15803D',
  },
  statusTextRejected: {
    color: '#B91C1C',
  },
  pricingGrid: {
    flexDirection: 'row',
    backgroundColor: '#F9FAFB',
    borderRadius: 10,
    padding: 10,
    alignItems: 'center',
  },
  gridCol: {
    flex: 1,
    alignItems: 'center',
  },
  gridDivider: {
    width: 1,
    height: 30,
    backgroundColor: '#E5E7EB',
  },
  gridLabel: {
    fontSize: 10,
    color: '#6B7280',
  },
  gridPrice: {
    fontSize: 15,
    fontWeight: '800',
    color: '#114B32',
    marginTop: 2,
  },
  gridValue: {
    fontSize: 15,
    fontWeight: '800',
    color: '#111827',
    marginTop: 2,
  },
  gridSub: {
    fontSize: 10,
    color: '#9CA3AF',
  },
  messageBox: {
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    padding: 8,
  },
  messageLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: '#4B5563',
  },
  messageContent: {
    fontSize: 12,
    color: '#1F2937',
    marginTop: 2,
  },
  contactRevealCard: {
    backgroundColor: '#DCFCE7',
    borderRadius: 10,
    padding: 10,
    gap: 8,
    borderWidth: 1,
    borderColor: '#86EFAC',
  },
  contactTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  contactTitleText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#166534',
  },
  contactActionButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  callBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#114B32',
    paddingVertical: 8,
    borderRadius: 8,
  },
  callBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  whatsAppBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#16A34A',
    paddingVertical: 8,
    borderRadius: 8,
  },
  whatsAppBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  cardActions: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 4,
  },
  rejectBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#FEE2E2',
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FCA5A5',
  },
  rejectBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#B91C1C',
  },
  acceptBtn: {
    flex: 1.5,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#114B32',
    paddingVertical: 10,
    borderRadius: 8,
  },
  acceptBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  demoPaymentBox: {
    marginTop: 10,
    gap: 4,
  },
  demoPayBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#0F766E',
    paddingVertical: 11,
    borderRadius: 8,
  },
  demoPayBtnText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  demoPayNote: {
    fontSize: 10,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 14,
  },
  completedBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#DCFCE7',
    padding: 10,
    borderRadius: 8,
    marginTop: 8,
  },
  completedText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#15803D',
    flex: 1,
  },
});
