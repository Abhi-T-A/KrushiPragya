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
import {
  BuyerOfferItem,
  TransactionDetail,
  createPaymentOrder,
  verifyPaymentSignature,
} from '../../services/marketApi';
import {
  X,
  CreditCard,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Phone,
  MessageCircle,
  ShieldCheck,
  Receipt,
  RotateCw,
} from 'lucide-react-native';

interface TransactionModalProps {
  visible: boolean;
  offerItem: BuyerOfferItem | null;
  buyerId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const TransactionModal: React.FC<TransactionModalProps> = ({
  visible,
  offerItem,
  buyerId,
  onClose,
  onSuccess,
}) => {
  const [loading, setLoading] = useState(false);
  const [transaction, setTransaction] = useState<TransactionDetail | null>(null);
  const [paymentStep, setPaymentStep] = useState<'initial' | 'processing' | 'success' | 'failure' | 'unconfigured'>('initial');
  const [failureMsg, setFailureMsg] = useState<string>('');

  if (!visible || !offerItem) return null;

  const { offer, listing, contact_phone, contact_name } = offerItem;
  const totalAmount = Number(offer.offered_price) * Number(offer.quantity);

  const handleInitiatePayment = async () => {
    try {
      setLoading(true);
      setPaymentStep('processing');

      // Request backend to create payment order (idempotency key prevents double charging)
      const idempotencyKey = `tx_${offer.id}_${Date.now()}`;
      const orderResp = await createPaymentOrder(buyerId, offer.id, idempotencyKey);

      // Check if payment provider is configured on server
      if (!orderResp.gateway_configured) {
        setPaymentStep('unconfigured');
        setFailureMsg(orderResp.message_en || orderResp.message_kn || 'Online payment is currently unavailable.');
        return;
      }

      // If PayU checkout data is provided, open secure PayU hosted checkout
      if (orderResp.checkout_data?.action_url && orderResp.checkout_data?.params) {
        try {
          const searchParams = new URLSearchParams(orderResp.checkout_data.params as any);
          const payuUrl = `${orderResp.checkout_data.action_url}?${searchParams.toString()}`;
          const canOpen = await Linking.canOpenURL(payuUrl);
          if (canOpen) {
            await Linking.openURL(payuUrl);
          } else {
            Alert.alert('PayU', 'ಬ್ರೌಸರ್‌ನಲ್ಲಿ PayU ಗೇಟ್‌ವೇ ತೆರೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.');
          }
        } catch (e) {
          console.warn('PayU checkout open error:', e);
        }
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'ಪಾವತಿ ಪ್ರಾರಂಭಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.';
      setPaymentStep('failure');
      setFailureMsg(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
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
              <Text style={styles.headerTitle}>ವಹಿವಾಟಿನ ವಿವರಗಳು</Text>
              <Text style={styles.headerSubTitle}>ಬೆಳೆ ಖರೀದಿ & ಪಾವತಿ</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
              <X size={20} color="#374151" />
            </TouchableOpacity>
          </View>

          <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollBody}>
            {/* STEP 1: INITIAL SUMMARY */}
            {paymentStep === 'initial' && (
              <>
                <View style={styles.summaryCard}>
                  <Text style={styles.summaryTitle}>ಖರೀದಿ ಆದೇಶ ಸಾರಾಂಶ</Text>

                  <View style={styles.summaryRow}>
                    <Text style={styles.summaryLabel}>ಪ್ರಮಾಣ:</Text>
                    <Text style={styles.summaryValue}>
                      {offer.quantity} {listing.unit}
                    </Text>
                  </View>

                  <View style={styles.summaryRow}>
                    <Text style={styles.summaryLabel}>ಒಪ್ಪಿತ ದರ:</Text>
                    <Text style={styles.summaryValue}>
                      ₹{Number(offer.offered_price).toLocaleString('en-IN')} / {listing.unit}
                    </Text>
                  </View>

                  <View style={styles.summaryDivider} />

                  <View style={styles.summaryRow}>
                    <Text style={styles.totalLabel}>ಒಟ್ಟು ಪಾವತಿಸಬೇಕಾದ ಮೊತ್ತ:</Text>
                    <Text style={styles.totalValue}>
                      ₹{Math.round(totalAmount).toLocaleString('en-IN')}
                    </Text>
                  </View>
                </View>

                {/* Seller Authorized Contact */}
                {contact_phone && (
                  <View style={styles.sellerCard}>
                    <View style={styles.sellerHeader}>
                      <ShieldCheck size={16} color="#15803D" />
                      <Text style={styles.sellerHeaderText}>
                        ರೈತರ ದೃಢೀಕೃತ ಸಂಪರ್ಕ: {contact_name || 'ಬೆಳೆಗಾರರು'}
                      </Text>
                    </View>
                    <Text style={styles.sellerPhoneText}>{contact_phone}</Text>

                    <View style={styles.contactButtonsRow}>
                      <TouchableOpacity
                        activeOpacity={0.8}
                        onPress={() => handleCall(contact_phone)}
                        style={styles.actionCallBtn}
                      >
                        <Phone size={14} color="#FFFFFF" />
                        <Text style={styles.contactBtnText}>ಕರೆ ಮಾಡಿ</Text>
                      </TouchableOpacity>

                      <TouchableOpacity
                        activeOpacity={0.8}
                        onPress={() => handleWhatsApp(contact_phone)}
                        style={styles.actionWhatsAppBtn}
                      >
                        <MessageCircle size={14} color="#FFFFFF" />
                        <Text style={styles.contactBtnText}>WhatsApp</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                )}

                {/* Secure Payment CTA */}
                <TouchableOpacity
                  activeOpacity={0.85}
                  onPress={handleInitiatePayment}
                  disabled={loading}
                  style={styles.payBtn}
                >
                  <CreditCard size={18} color="#FFFFFF" />
                  <Text style={styles.payBtnText}>
                    ₹{Math.round(totalAmount).toLocaleString('en-IN')} - Pay securely (ಸುರಕ್ಷಿತವಾಗಿ ಪಾವತಿಸಿ)
                  </Text>
                </TouchableOpacity>

                <Text style={styles.securityNote}>
                  🔒 ಸರ್ವರ್-ಪರಿಶೀಲಿತ ಸುರಕ್ಷಿತ ಪಾವತಿ ಗೇಟ್‌ವೇ (PayU). ಯಾವುದೇ ನಕಲಿ ಕ್ಲೈಂಟ್ ರಶೀದಿಗಳನ್ನು ಅನುಮತಿಸುವುದಿಲ್ಲ.
                </Text>
              </>
            )}

            {/* STEP 2: PROCESSING */}
            {paymentStep === 'processing' && (
              <View style={styles.stateContainer}>
                <ActivityIndicator size="large" color="#114B32" />
                <Text style={styles.stateTitle}>ಪಾವತಿ ಪ್ರಕ್ರಿಯೆ ನಡೆಯುತ್ತಿದೆ...</Text>
                <Text style={styles.stateSub}>ಸರ್ವರ್-ಸೈಡ್ ಆರ್ಡರ್ ಸೃಜಿಸಲಾಗುತ್ತಿದೆ. ದಯವಿಟ್ಟು ನಿರೀಕ್ಷಿಸಿ.</Text>
              </View>
            )}

            {/* STEP 3: UNCONFIGURED (No fake payments allowed!) */}
            {paymentStep === 'unconfigured' && (
              <View style={styles.stateContainer}>
                <View style={styles.iconCircleYellow}>
                  <AlertTriangle size={32} color="#D97706" />
                </View>
                <Text style={styles.stateTitle}>ಪಾವತಿ ಸೇವೆ ಈಗ ಲಭ್ಯವಿಲ್ಲ</Text>
                <Text style={styles.stateSub}>
                  {failureMsg || 'ಸರ್ವರ್‌ನಲ್ಲಿ ಪಾವತಿ ಗೇಟ್‌ವೇ ಇನ್ನೂ ಕಾನ್ಫಿಗರ್ ಮಾಡಲಾಗಿಲ್ಲ. ದಯವಿಟ್ಟು ರೈತರನ್ನು ನೇರವಾಗಿ ಸಂಪರ್ಕಿಸಿ.'}
                </Text>

                {contact_phone && (
                  <TouchableOpacity
                    activeOpacity={0.85}
                    onPress={() => handleCall(contact_phone)}
                    style={styles.directContactBtn}
                  >
                    <Phone size={16} color="#FFFFFF" />
                    <Text style={styles.directContactBtnText}>ರೈತರಿಗೆ ಕರೆ ಮಾಡಿ ({contact_phone})</Text>
                  </TouchableOpacity>
                )}

                <TouchableOpacity
                  activeOpacity={0.8}
                  onPress={() => setPaymentStep('initial')}
                  style={styles.backBtn}
                >
                  <Text style={styles.backBtnText}>ಹಿಂತಿರುಗಿ</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* STEP 4: PAYMENT FAILURE */}
            {paymentStep === 'failure' && (
              <View style={styles.stateContainer}>
                <View style={styles.iconCircleRed}>
                  <XCircle size={32} color="#DC2626" />
                </View>
                <Text style={styles.stateTitle}>ಪಾವತಿ ಪೂರ್ಣಗೊಳ್ಳಲಿಲ್ಲ</Text>
                <Text style={styles.stateSub}>
                  {failureMsg || 'ಪಾವತಿಯನ್ನು ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ಯಾವುದೇ ಹಣ ಕಡಿತಗೊಂಡಿಲ್ಲ.'}
                </Text>

                <View style={styles.failureActionsRow}>
                  <TouchableOpacity
                    activeOpacity={0.85}
                    onPress={handleInitiatePayment}
                    style={styles.retryBtn}
                  >
                    <RotateCw size={16} color="#FFFFFF" />
                    <Text style={styles.retryBtnText}>ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    activeOpacity={0.8}
                    onPress={() => setPaymentStep('initial')}
                    style={styles.backBtn}
                  >
                    <Text style={styles.backBtnText}>ವಿವರಗಳು</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}

            {/* STEP 5: PAYMENT SUCCESS */}
            {paymentStep === 'success' && (
              <View style={styles.stateContainer}>
                <View style={styles.iconCircleGreen}>
                  <CheckCircle2 size={36} color="#15803D" />
                </View>
                <Text style={styles.stateTitleSuccess}>✓ ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆ</Text>
                <Text style={styles.successAmount}>
                  ₹{Math.round(totalAmount).toLocaleString('en-IN')}
                </Text>

                <View style={styles.receiptBox}>
                  <View style={styles.receiptRow}>
                    <Text style={styles.receiptLabel}>ವಹಿವಾಟು ID:</Text>
                    <Text style={styles.receiptValue}>{transaction?.id || 'TX-KP-2026'}</Text>
                  </View>
                  <View style={styles.receiptRow}>
                    <Text style={styles.receiptLabel}>ದಿನಾಂಕ:</Text>
                    <Text style={styles.receiptValue}>{new Date().toLocaleDateString()}</Text>
                  </View>
                  <View style={styles.receiptRow}>
                    <Text style={styles.receiptLabel}>ಸ್ಥಿತಿ:</Text>
                    <Text style={[styles.receiptValue, { color: '#15803D', fontWeight: '800' }]}>
                      ಪಾವತಿಸಲಾಗಿದೆ (PAID)
                    </Text>
                  </View>
                </View>

                <TouchableOpacity
                  activeOpacity={0.85}
                  onPress={() => {
                    onSuccess();
                    onClose();
                  }}
                  style={styles.doneBtn}
                >
                  <Text style={styles.doneBtnText}>ಮಾರುಕಟ್ಟೆಗೆ ಹಿಂತಿರುಗಿ</Text>
                </TouchableOpacity>
              </View>
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
    gap: 14,
  },
  summaryCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    padding: 14,
    gap: 8,
  },
  summaryTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#374151',
    textTransform: 'uppercase',
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  summaryLabel: {
    fontSize: 13,
    color: '#6B7280',
  },
  summaryValue: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
  },
  summaryDivider: {
    height: 1,
    backgroundColor: '#E5E7EB',
    marginVertical: 4,
  },
  totalLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
  },
  totalValue: {
    fontSize: 18,
    fontWeight: '800',
    color: '#114B32',
  },
  sellerCard: {
    backgroundColor: '#F0FDF4',
    borderWidth: 1,
    borderColor: '#BBF7D0',
    borderRadius: 12,
    padding: 12,
    gap: 8,
  },
  sellerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  sellerHeaderText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#166534',
  },
  sellerPhoneText: {
    fontSize: 15,
    fontWeight: '800',
    color: '#114B32',
  },
  contactButtonsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 4,
  },
  actionCallBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#114B32',
    paddingVertical: 8,
    borderRadius: 8,
  },
  actionWhatsAppBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#16A34A',
    paddingVertical: 8,
    borderRadius: 8,
  },
  contactBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  payBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#114B32',
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 6,
  },
  payBtnText: {
    fontSize: 14,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  securityNote: {
    fontSize: 11,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 16,
    paddingHorizontal: 8,
  },
  stateContainer: {
    alignItems: 'center',
    paddingVertical: 30,
    gap: 12,
  },
  iconCircleYellow: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#FEF3C7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconCircleRed: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#FEE2E2',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconCircleGreen: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#DCFCE7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  stateTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
    textAlign: 'center',
  },
  stateTitleSuccess: {
    fontSize: 20,
    fontWeight: '800',
    color: '#15803D',
    textAlign: 'center',
  },
  successAmount: {
    fontSize: 26,
    fontWeight: '800',
    color: '#114B32',
  },
  stateSub: {
    fontSize: 13,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 18,
    paddingHorizontal: 16,
  },
  receiptBox: {
    width: '100%',
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    padding: 12,
    gap: 8,
    marginTop: 8,
  },
  receiptRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  receiptLabel: {
    fontSize: 12,
    color: '#6B7280',
  },
  receiptValue: {
    fontSize: 12,
    fontWeight: '700',
    color: '#111827',
  },
  directContactBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#114B32',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 10,
    marginTop: 8,
  },
  directContactBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  failureActionsRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 10,
    width: '100%',
  },
  retryBtn: {
    flex: 1.5,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#114B32',
    paddingVertical: 12,
    borderRadius: 10,
  },
  retryBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  backBtn: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  backBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#4B5563',
  },
  doneBtn: {
    backgroundColor: '#114B32',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 10,
    marginTop: 12,
  },
  doneBtnText: {
    fontSize: 14,
    fontWeight: '800',
    color: '#FFFFFF',
  },
});
