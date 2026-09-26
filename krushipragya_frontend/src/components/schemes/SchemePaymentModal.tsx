/**
 * Scheme Payment Modal & Application Flow Component
 *
 * Implements:
 * 1. Transparent Fee Breakdown (Official Govt Fee + KrushiPragya Service Fee)
 * 2. Kannada-first UI with transparency disclosure
 * 3. PhonePe Static QR Code checkout flow
 * 4. UTR submission & PENDING_VERIFICATION state
 * 5. Free scheme bypass (no payment screen, direct submission)
 * 6. Audited official receipt upon payment confirmation
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Image,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import {
  X,
  CheckCircle,
  Clock,
  AlertCircle,
  ShieldCheck,
  FileText,
  QrCode,
  ArrowRight,
  ExternalLink,
} from 'lucide-react-native';

import { SchemeDetail, SchemeApplication, SchemePaymentInitiateResponse, PaymentReceipt } from '../../types/schemes';
import {
  applyForScheme,
  initiateSchemePayment,
  submitSchemePaymentProof,
  fetchSchemePaymentDetails,
  submitSchemeApplication,
} from '../../services/schemesApi';

interface SchemePaymentModalProps {
  visible: boolean;
  scheme: SchemeDetail;
  user?: { phone?: string; id?: string; full_name?: string } | null;
  onClose: () => void;
  onApplicationCompleted?: (application: SchemeApplication) => void;
}

type ModalStep = 'FEE_SUMMARY' | 'QR_PAYMENT' | 'PROOF_SUBMITTED' | 'RECEIPT';

export const SchemePaymentModal: React.FC<SchemePaymentModalProps> = ({
  visible,
  scheme,
  user,
  onClose,
  onApplicationCompleted,
}) => {
  const [step, setStep] = useState<ModalStep>('FEE_SUMMARY');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [application, setApplication] = useState<SchemeApplication | null>(null);
  const [paymentData, setPaymentData] = useState<SchemePaymentInitiateResponse | null>(null);
  const [utrInput, setUtrInput] = useState('');
  const [submittedUtr, setSubmittedUtr] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<PaymentReceipt | null>(null);

  // Initialize application draft on modal open
  useEffect(() => {
    if (visible && scheme) {
      initApplication();
    } else {
      resetState();
    }
  }, [visible, scheme?.id]);

  const resetState = () => {
    setStep('FEE_SUMMARY');
    setLoading(false);
    setErrorMsg(null);
    setApplication(null);
    setPaymentData(null);
    setUtrInput('');
    setSubmittedUtr(null);
    setReceipt(null);
  };

  const initApplication = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const app = await applyForScheme(scheme.id, undefined, user);
      setApplication(app);

      // Check if existing application is already paid or proof submitted
      if (app.payment_status === 'PAID') {
        const details = await fetchSchemePaymentDetails(app.id, user);
        if (details.receipt) {
          setReceipt(details.receipt);
          setStep('RECEIPT');
        } else {
          setStep('FEE_SUMMARY');
        }
      } else if (app.payment_status === 'PENDING_VERIFICATION') {
        const details = await fetchSchemePaymentDetails(app.id, user);
        setSubmittedUtr(details.payment_reference || '');
        setStep('PROOF_SUBMITTED');
      } else {
        setStep('FEE_SUMMARY');
      }
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'ಅರ್ಜಿ ಪ್ರಾರಂಭಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.');
    } finally {
      setLoading(false);
    }
  };

  const feeInfo = application?.fee_info || scheme.fee_info;
  const isFree = feeInfo?.fee_type === 'FREE' || feeInfo?.total_payable === 0;
  const isUnknown = feeInfo?.fee_type === 'UNKNOWN' || feeInfo?.is_verified === false;

  const officialFeeVal = feeInfo?.official_fee ?? 0;
  const serviceFeeVal = feeInfo?.krushipragya_service_fee ?? 0;
  const totalPayableVal = feeInfo?.total_payable ?? (officialFeeVal + serviceFeeVal);

  const handleProceedToPayment = async () => {
    if (!application) return;

    if (isUnknown) {
      Alert.alert('ಪರಿಶೀಲನೆ ಅಗತ್ಯ', 'ಈ ಯೋಜನೆಯ ಶುಲ್ಕ ಮಾಹಿತಿಯನ್ನು ಅಧಿಕೃತ ಮೂಲದಿಂದ ಪರಿಶೀಲಿಸಬೇಕಾಗಿದೆ. ದಯವಿಟ್ಟು ನಂತರ ಪ್ರಯತ್ನಿಸಿ.');
      return;
    }

    if (isFree) {
      // Free scheme -> Submit application directly!
      handleSubmitApplication();
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    try {
      const payRes = await initiateSchemePayment(application.id, user);
      setPaymentData(payRes);
      setStep('QR_PAYMENT');
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'ಪಾವತಿ ಆದೇಶ ರಚಿಸಲು ವಿಫಲವಾಗಿದೆ.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitProof = async () => {
    if (!application || !paymentData) return;
    const cleanUtr = utrInput.trim();

    if (!cleanUtr || cleanUtr.length < 8) {
      Alert.alert('ಅಮಾನ್ಯ UTR', 'ದಯವಿಟ್ಟು ಮಾನ್ಯವಾದ 12-ಅಂಕಿಯ ಬ್ಯಾಂಕ್ UTR / UPI Reference ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await submitSchemePaymentProof(
        application.id,
        cleanUtr,
        paymentData.total_amount,
        undefined,
        user
      );
      setSubmittedUtr(res.payment_reference);
      setStep('PROOF_SUBMITTED');
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'UTR ಸಲ್ಲಿಸುವಾಗ ದೋಷ ಸಂಭವಿಸಿದೆ.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitApplication = async () => {
    if (!application) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const updatedApp = await submitSchemeApplication(application.id, user);
      setApplication(updatedApp);
      Alert.alert(
        'ಅರ್ಜಿ ಯಶಸ್ವಿಯಾಗಿ ಸಲ್ಲಿಕೆಯಾಗಿದೆ!',
        'ನಿಮ್ಮ ಯೋಜನಾ ಅರ್ಜಿಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಕಳುಹಿಸಲಾಗಿದೆ. ನೀವು ಇದನ್ನು ನನ್ನ ಅರ್ಜಿಗಳ ಪಟ್ಟಿಯಲ್ಲಿ ಟ್ರ್ಯಾಕ್ ಮಾಡಬಹುದು.',
        [
          {
            text: 'ಸರಿ (OK)',
            onPress: () => {
              if (onApplicationCompleted) {
                onApplicationCompleted(updatedApp);
              }
              onClose();
            },
          },
        ]
      );
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.sheetContainer}>
          {/* Header */}
          <View style={styles.headerRow}>
            <View style={styles.headerTextGroup}>
              <Text style={styles.headerTitle}>
                {step === 'RECEIPT' ? 'ಪಾವತಿ ರಶೀದಿ (Receipt)' : 'ಯೋಜನೆ ಅರ್ಜಿ & ಪಾವತಿ'}
              </Text>
              <Text style={styles.headerSubtitle} numberOfLines={1}>
                {scheme.title_kn || scheme.name}
              </Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn} accessibilityRole="button">
              <X size={20} color="#6B7280" />
            </TouchableOpacity>
          </View>

          {/* Content */}
          <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
            {loading && (
              <View style={styles.loadingBox}>
                <ActivityIndicator size="large" color="#16A34A" />
                <Text style={styles.loadingText}>ದಯವಿಟ್ಟು ನಿರೀಕ್ಷಿಸಿ...</Text>
              </View>
            )}

            {errorMsg && !loading && (
              <View style={styles.errorBox}>
                <AlertCircle size={20} color="#DC2626" style={{ marginTop: 2 }} />
                <Text style={styles.errorText}>{errorMsg}</Text>
              </View>
            )}

            {/* STEP 1: FEE SUMMARY */}
            {step === 'FEE_SUMMARY' && !loading && (
              <View>
                {/* Fee Breakdown Card */}
                <View style={styles.summaryCard}>
                  <View style={styles.summaryCardHeader}>
                    <FileText size={18} color="#16A34A" />
                    <Text style={styles.summaryCardTitle}>ಪಾವತಿ ವಿವರ (Payment Summary)</Text>
                  </View>

                  <View style={styles.divider} />

                  {/* Component 1: Official Govt Fee */}
                  <View style={styles.feeRow}>
                    <Text style={styles.feeLabel}>ಸರ್ಕಾರದ ಅರ್ಜಿ ಶುಲ್ಕ (Govt Fee):</Text>
                    <Text style={styles.feeValue}>₹{officialFeeVal.toFixed(2)}</Text>
                  </View>

                  {/* Component 2: KrushiPragya Service Fee */}
                  <View style={styles.feeRow}>
                    <Text style={styles.feeLabel}>KrushiPragya ಸೇವಾ ಶುಲ್ಕ (Service Fee):</Text>
                    <Text style={styles.feeValue}>₹{serviceFeeVal.toFixed(2)}</Text>
                  </View>

                  <View style={styles.totalDivider} />

                  {/* Total */}
                  <View style={styles.totalRow}>
                    <Text style={styles.totalLabel}>ಒಟ್ಟು ಪಾವತಿ (Total Payable):</Text>
                    <Text style={styles.totalValue}>
                      {isUnknown ? 'ಪರಿಶೀಲನೆಯಲ್ಲಿದೆ' : `₹${totalPayableVal.toFixed(2)}`}
                    </Text>
                  </View>

                  {/* Mandatory Transparency Note */}
                  <View style={styles.transparencyBox}>
                    <ShieldCheck size={16} color="#15803D" />
                    <Text style={styles.transparencyText}>
                      ಶುಲ್ಕಗಳನ್ನು ಪಾರದರ್ಶಕತೆಗಾಗಿ ಪ್ರತ್ಯೇಕವಾಗಿ ತೋರಿಸಲಾಗಿದೆ. (Fees are displayed separately for transparency.)
                    </Text>
                  </View>
                </View>

                {/* Free Scheme Banner */}
                {isFree && (
                  <View style={styles.freeBanner}>
                    <CheckCircle size={20} color="#16A34A" />
                    <Text style={styles.freeBannerText}>
                      ಈ ಯೋಜನೆಗೆ ಯಾವುದೇ ಪಾವತಿ ಅಗತ್ಯವಿಲ್ಲ. ನೀವು ಉಚಿತವಾಗಿ ನೇರವಾಗಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದು.
                    </Text>
                  </View>
                )}

                {/* Unknown Fee Warning */}
                {isUnknown && (
                  <View style={styles.warningBanner}>
                    <AlertCircle size={20} color="#D97706" />
                    <Text style={styles.warningBannerText}>
                      ಶುಲ್ಕದ ಮಾಹಿತಿಯನ್ನು ಪರಿಶೀಲಿಸಬೇಕಾಗಿದೆ (Fee information needs verification). ಅಧಿಕೃತ ದೃಢೀಕರಣದ ನಂತರವೇ ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದು.
                    </Text>
                  </View>
                )}

                {/* Action CTA */}
                <TouchableOpacity
                  style={[
                    styles.primaryBtn,
                    isUnknown && styles.primaryBtnDisabled,
                  ]}
                  disabled={isUnknown}
                  onPress={handleProceedToPayment}
                  accessibilityRole="button"
                >
                  <Text style={styles.primaryBtnText}>
                    {isFree
                      ? 'ಉಚಿತವಾಗಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ (Submit Free Application)'
                      : `ಪಾವತಿಸಲು ಮುಂದುವರಿಯಿರಿ (Pay ₹${totalPayableVal.toFixed(2)})`}
                  </Text>
                  <ArrowRight size={18} color="#FFFFFF" style={{ marginLeft: 8 }} />
                </TouchableOpacity>
              </View>
            )}

            {/* STEP 2: PHONEPE STATIC QR CHECKOUT */}
            {step === 'QR_PAYMENT' && paymentData && !loading && (
              <View>
                <View style={styles.qrCard}>
                  <Text style={styles.qrTitle}>PhonePe ಮೂಲಕ ಪಾವತಿಸಿ</Text>
                  <Text style={styles.qrSubtitle}>
                    ಕೆಳಗಿನ PhonePe QR ಕೋಡ್ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ ಸರಿಯಾದ ಮೊತ್ತವನ್ನು ಪಾವತಿಸಿ.
                  </Text>

                  {/* PhonePe QR Code Image */}
                  <View style={styles.qrImageContainer}>
                    <Image
                      source={require('../../../assets/phonepe_static_qr.png')}
                      style={styles.qrImage}
                      resizeMode="contain"
                    />
                  </View>

                  {/* Authoritative Amount Badge */}
                  <View style={styles.amountBadge}>
                    <Text style={styles.amountBadgeLabel}>ಪಾವತಿಸಬೇಕಾದ ನಿಖರ ಮೊತ್ತ:</Text>
                    <Text style={styles.amountBadgeValue}>₹{paymentData.total_amount.toFixed(2)}</Text>
                  </View>

                  <View style={styles.qrMetaBox}>
                    <Text style={styles.qrMetaText}>
                      UPI ID: <Text style={styles.qrMetaBold}>{paymentData.qr_data.upi_id}</Text>
                    </Text>
                    <Text style={styles.qrMetaText}>
                      ಸ್ವೀಕೃತಿದಾರರು: <Text style={styles.qrMetaBold}>{paymentData.qr_data.payee_name}</Text>
                    </Text>
                  </View>
                </View>

                {/* UTR Input Section */}
                <View style={styles.utrSection}>
                  <Text style={styles.utrLabel}>
                    ಪಾವತಿಯ ನಂತರ 12-ಅಂಕಿಯ UTR / Reference ನಮೂದಿಸಿ:
                  </Text>
                  <TextInput
                    style={styles.utrInput}
                    placeholder="ಉದಾ: 202609260001 (12 digits)"
                    value={utrInput}
                    onChangeText={setUtrInput}
                    autoCapitalize="characters"
                    keyboardType="default"
                  />

                  <TouchableOpacity
                    style={styles.submitProofBtn}
                    onPress={handleSubmitProof}
                    accessibilityRole="button"
                  >
                    <ShieldCheck size={18} color="#FFFFFF" />
                    <Text style={styles.submitProofBtnText}>UTR ಸಲ್ಲಿಸಿ (Submit Proof)</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}

            {/* STEP 3: PROOF SUBMITTED (PENDING VERIFICATION) */}
            {step === 'PROOF_SUBMITTED' && !loading && (
              <View style={styles.pendingVerificationBox}>
                <Clock size={48} color="#D97706" style={{ alignSelf: 'center', marginBottom: 12 }} />
                <Text style={styles.pendingTitle}>ಪಾವತಿ ಪರಿಶೀಲನೆಯಲ್ಲಿದೆ</Text>
                <Text style={styles.pendingSubtitle}>
                  ನಿಮ್ಮ UTR ಸಂಖ್ಯೆ: <Text style={styles.qrMetaBold}>{submittedUtr || utrInput}</Text>
                </Text>

                <View style={styles.pendingInfoCard}>
                  <Text style={styles.pendingInfoText}>
                    ಕೃಷಿಪ್ರಜ್ಞಾ ತಂಡವು ನಿಮ್ಮ ಪಾವತಿಯನ್ನು ಅಧಿಕೃತವಾಗಿ ಪರಿಶೀಲಿಸುತ್ತಿದೆ. ಪರಿಶೀಲನೆಯ ನಂತರ ನಿಮ್ಮ ಅರ್ಜಿ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಅನುಮೋದನೆಗೆ ಸಿದ್ಧವಾಗುತ್ತದೆ.
                  </Text>
                  <Text style={[styles.pendingInfoText, { marginTop: 6, fontStyle: 'italic' }]}>
                    Payment is pending verification by KrushiPragya administrative team.
                  </Text>
                </View>

                <TouchableOpacity style={styles.primaryBtn} onPress={onClose} accessibilityRole="button">
                  <Text style={styles.primaryBtnText}>ಮುಚ್ಚಿ (Close)</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* STEP 4: RECEIPT */}
            {step === 'RECEIPT' && receipt && !loading && (
              <View style={styles.receiptContainer}>
                <View style={styles.receiptCard}>
                  <View style={styles.receiptHeader}>
                    <ShieldCheck size={32} color="#16A34A" />
                    <Text style={styles.receiptTitle}>ಅಧಿಕೃತ ಪಾವತಿ ರಶೀದಿ</Text>
                    <Text style={styles.receiptNo}>ರಶೀದಿ ಸಂ: {receipt.receipt_id}</Text>
                  </View>

                  <View style={styles.receiptDivider} />

                  <View style={styles.receiptRow}>
                    <Text style={styles.receiptLabel}>ಯೋಜನೆ:</Text>
                    <Text style={styles.receiptVal}>{receipt.scheme_name}</Text>
                  </View>

                  <View style={styles.receiptRow}>
                    <Text style={styles.receiptLabel}>ಅರ್ಜಿ ID:</Text>
                    <Text style={styles.receiptVal}>{receipt.application_id.slice(0, 8)}...</Text>
                  </View>

                  <View style={styles.receiptRow}>
                    <Text style={styles.receiptLabel}>ಸರ್ಕಾರದ ಅರ್ಜಿ ಶುಲ್ಕ:</Text>
                    <Text style={styles.receiptVal}>₹{receipt.official_fee.toFixed(2)}</Text>
                  </View>

                  <View style={styles.receiptRow}>
                    <Text style={styles.receiptLabel}>KrushiPragya ಸೇವಾ ಶುಲ್ಕ:</Text>
                    <Text style={styles.receiptVal}>₹{receipt.krushipragya_service_fee.toFixed(2)}</Text>
                  </View>

                  <View style={styles.receiptDivider} />

                  <View style={styles.receiptRow}>
                    <Text style={styles.receiptTotalLabel}>ಒಟ್ಟು ಪಾವತಿಸಿದ ಮೊತ್ತ:</Text>
                    <Text style={styles.receiptTotalVal}>₹{receipt.total_paid.toFixed(2)}</Text>
                  </View>

                  <View style={styles.receiptRow}>
                    <Text style={styles.receiptLabel}>ಪಾವತಿ ವಿಧಾನ:</Text>
                    <Text style={styles.receiptVal}>{receipt.payment_method}</Text>
                  </View>

                  <View style={styles.receiptRow}>
                    <Text style={styles.receiptLabel}>UTR / Reference:</Text>
                    <Text style={styles.receiptVal}>{receipt.payment_reference}</Text>
                  </View>

                  <View style={styles.receiptRow}>
                    <Text style={styles.receiptLabel}>ಸ್ಥಿತಿ:</Text>
                    <Text style={[styles.receiptVal, { color: '#16A34A', fontWeight: '700' }]}>
                      {receipt.payment_status} (ಯಶಸ್ವಿ)
                    </Text>
                  </View>
                </View>

                {/* Submit Final Application Button */}
                <TouchableOpacity
                  style={styles.primaryBtn}
                  onPress={handleSubmitApplication}
                  accessibilityRole="button"
                >
                  <Text style={styles.primaryBtnText}>ಅರ್ಜಿಯನ್ನು ಅಂತಿಮವಾಗಿ ಸಲ್ಲಿಸಿ (Submit Application)</Text>
                  <ArrowRight size={18} color="#FFFFFF" style={{ marginLeft: 8 }} />
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
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.55)',
    justifyContent: 'flex-end',
  },
  sheetContainer: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '90%',
    paddingBottom: 24,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTextGroup: {
    flex: 1,
    marginRight: 12,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  headerSubtitle: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 2,
  },
  closeBtn: {
    padding: 6,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 32,
  },
  loadingBox: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#4B5563',
  },
  errorBox: {
    flexDirection: 'row',
    backgroundColor: '#FEF2F2',
    borderColor: '#FCA5A5',
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
    gap: 8,
  },
  errorText: {
    flex: 1,
    fontSize: 13,
    color: '#DC2626',
    lineHeight: 18,
  },
  summaryCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    marginBottom: 16,
  },
  summaryCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
  },
  summaryCardTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1F2937',
  },
  divider: {
    height: 1,
    backgroundColor: '#E5E7EB',
    marginVertical: 10,
  },
  feeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  feeLabel: {
    fontSize: 14,
    color: '#4B5563',
  },
  feeValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  totalDivider: {
    height: 1,
    backgroundColor: '#D1D5DB',
    marginVertical: 10,
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  totalLabel: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111827',
  },
  totalValue: {
    fontSize: 18,
    fontWeight: '800',
    color: '#16A34A',
  },
  transparencyBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDF4',
    borderRadius: 10,
    padding: 10,
    marginTop: 12,
    gap: 8,
  },
  transparencyText: {
    fontSize: 12,
    color: '#15803D',
    flex: 1,
    lineHeight: 16,
  },
  freeBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDF4',
    borderColor: '#86EFAC',
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    gap: 10,
  },
  freeBannerText: {
    fontSize: 13,
    color: '#166534',
    flex: 1,
    lineHeight: 18,
    fontWeight: '600',
  },
  warningBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFBEB',
    borderColor: '#FCD34D',
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    gap: 10,
  },
  warningBannerText: {
    fontSize: 13,
    color: '#92400E',
    flex: 1,
    lineHeight: 18,
  },
  primaryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#16A34A',
    borderRadius: 12,
    paddingVertical: 14,
    marginTop: 8,
  },
  primaryBtnDisabled: {
    backgroundColor: '#9CA3AF',
  },
  primaryBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  qrCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    alignItems: 'center',
    marginBottom: 16,
  },
  qrTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#111827',
  },
  qrSubtitle: {
    fontSize: 13,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 4,
    marginBottom: 12,
  },
  qrImageContainer: {
    width: 220,
    height: 220,
    backgroundColor: '#000000',
    borderRadius: 16,
    padding: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  qrImage: {
    width: 200,
    height: 200,
  },
  amountBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginTop: 14,
    gap: 6,
  },
  amountBadgeLabel: {
    fontSize: 13,
    color: '#166534',
  },
  amountBadgeValue: {
    fontSize: 17,
    fontWeight: '800',
    color: '#15803D',
  },
  qrMetaBox: {
    marginTop: 12,
    alignItems: 'center',
  },
  qrMetaText: {
    fontSize: 12,
    color: '#6B7280',
    marginVertical: 2,
  },
  qrMetaBold: {
    fontWeight: '700',
    color: '#1F2937',
  },
  utrSection: {
    backgroundColor: '#F9FAFB',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    marginBottom: 16,
  },
  utrLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  utrInput: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
    color: '#111827',
    marginBottom: 12,
  },
  submitProofBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2563EB',
    borderRadius: 10,
    paddingVertical: 12,
    gap: 8,
  },
  submitProofBtnText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  pendingVerificationBox: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  pendingTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#92400E',
    marginBottom: 4,
  },
  pendingSubtitle: {
    fontSize: 14,
    color: '#4B5563',
    marginBottom: 16,
  },
  pendingInfoCard: {
    backgroundColor: '#FFFBEB',
    borderColor: '#FDE68A',
    borderWidth: 1,
    borderRadius: 14,
    padding: 14,
    marginBottom: 20,
  },
  pendingInfoText: {
    fontSize: 13,
    color: '#78350F',
    lineHeight: 18,
    textAlign: 'center',
  },
  receiptContainer: {
    paddingVertical: 8,
  },
  receiptCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 6,
    elevation: 2,
  },
  receiptHeader: {
    alignItems: 'center',
    marginBottom: 12,
  },
  receiptTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#111827',
    marginTop: 6,
  },
  receiptNo: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  receiptDivider: {
    height: 1,
    backgroundColor: '#E5E7EB',
    marginVertical: 10,
  },
  receiptRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  receiptLabel: {
    fontSize: 13,
    color: '#6B7280',
  },
  receiptVal: {
    fontSize: 13,
    fontWeight: '600',
    color: '#111827',
    maxWidth: '65%',
    textAlign: 'right',
  },
  receiptTotalLabel: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111827',
  },
  receiptTotalVal: {
    fontSize: 16,
    fontWeight: '800',
    color: '#16A34A',
  },
});
