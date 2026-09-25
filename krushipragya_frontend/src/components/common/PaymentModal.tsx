import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  QrCode,
  Smartphone,
  Banknote,
  AlertTriangle,
  CheckCircle2,
  X,
  ShieldCheck,
  Check,
} from 'lucide-react-native';

export interface PaymentReceipt {
  transactionId: string;
  amount: number;
  paymentMode: 'online_upi' | 'cash_self_risk';
  serviceType: string;
  beneficiaryName: string;
  timestamp: string;
  status: 'SUCCESS' | 'CASH_PENDING_VERIFICATION';
}

interface PaymentModalProps {
  visible: boolean;
  onClose: () => void;
  titleKn: string;
  titleEn: string;
  amount: number;
  serviceType: string;
  beneficiaryName?: string;
  onSuccess: (receipt: PaymentReceipt) => void;
}

export const PaymentModal: React.FC<PaymentModalProps> = ({
  visible,
  onClose,
  titleKn,
  titleEn,
  amount,
  serviceType,
  beneficiaryName = 'ICAR - KVK Brahmavar Official Govt Account',
  onSuccess,
}) => {
  const [paymentTab, setPaymentTab] = useState<'online' | 'cash'>('online');
  const [isProcessing, setIsProcessing] = useState(false);
  const [cashRiskAccepted, setCashRiskAccepted] = useState(false);
  const [receipt, setReceipt] = useState<PaymentReceipt | null>(null);

  const resetState = () => {
    setIsProcessing(false);
    setReceipt(null);
    setCashRiskAccepted(false);
    setPaymentTab('online');
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  // Simulate dummy instant online UPI payment
  const handleSimulateOnlinePay = (app: string) => {
    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
      const newReceipt: PaymentReceipt = {
        transactionId: 'TXN-KVK-2026-' + Math.floor(100000 + Math.random() * 900000),
        amount,
        paymentMode: 'online_upi',
        serviceType,
        beneficiaryName,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: 'SUCCESS',
      };
      setReceipt(newReceipt);
      onSuccess(newReceipt);
    }, 1400);
  };

  // Simulate cash payment with risk disclaimer
  const handleConfirmCashPay = () => {
    if (!cashRiskAccepted) return;
    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
      const newReceipt: PaymentReceipt = {
        transactionId: 'CASH-REF-' + Math.floor(100000 + Math.random() * 900000),
        amount,
        paymentMode: 'cash_self_risk',
        serviceType,
        beneficiaryName,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: 'CASH_PENDING_VERIFICATION',
      };
      setReceipt(newReceipt);
      onSuccess(newReceipt);
    }, 800);
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={handleClose}>
      <View style={styles.overlay}>
        <View style={styles.sheetContainer}>
          {/* Header */}
          <View style={styles.header}>
            <View style={{ flex: 1 }}>
              <Text style={styles.headerTitle}>{titleEn}</Text>
              <Text style={styles.headerSub}>{titleKn}</Text>
            </View>
            <TouchableOpacity onPress={handleClose} style={styles.closeBtn}>
              <X size={20} color={Colors.textSecondary} />
            </TouchableOpacity>
          </View>

          {/* Receipt View after Success */}
          {receipt ? (
            <View style={styles.receiptContent}>
              <View
                style={[
                  styles.receiptCard,
                  receipt.paymentMode === 'online_upi' ? styles.receiptGreen : styles.receiptAmber,
                ]}
              >
                <CheckCircle2
                  size={44}
                  color={receipt.paymentMode === 'online_upi' ? '#16A34A' : '#D97706'}
                />
                <Text style={styles.receiptStatusText}>
                  {receipt.paymentMode === 'online_upi'
                    ? 'Payment Successful / ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆ'
                    : 'Cash Request Recorded / ನಗದು ವಿನಂತಿ ದಾಖಲಾಗಿದೆ'}
                </Text>
                <Text style={styles.receiptSubText}>
                  {receipt.paymentMode === 'online_upi'
                    ? '100% Anti-Bribery Verified Digital Receipt'
                    : 'Self-Risk Cash Payment - Verification Pending'}
                </Text>

                <View style={styles.divider} />

                <View style={styles.receiptRow}>
                  <Text style={styles.receiptLabel}>Transaction / Ref ID:</Text>
                  <Text style={styles.receiptVal}>{receipt.transactionId}</Text>
                </View>
                <View style={styles.receiptRow}>
                  <Text style={styles.receiptLabel}>Amount (ನಿಗದಿತ ಶುಲ್ಕ):</Text>
                  <Text style={[styles.receiptVal, { color: Colors.primary, fontWeight: '800' }]}>
                    ₹{receipt.amount}
                  </Text>
                </View>
                <View style={styles.receiptRow}>
                  <Text style={styles.receiptLabel}>Beneficiary:</Text>
                  <Text style={styles.receiptVal}>{receipt.beneficiaryName}</Text>
                </View>
                <View style={styles.receiptRow}>
                  <Text style={styles.receiptLabel}>Time:</Text>
                  <Text style={styles.receiptVal}>{receipt.timestamp}</Text>
                </View>
              </View>

              <TouchableOpacity style={styles.doneBtn} onPress={handleClose}>
                <Text style={styles.doneBtnText}>Continue / ಮುಂದುವರಿಸಿ</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <ScrollView contentContainerStyle={styles.content}>
              {/* Payment Method Selector Tabs */}
              <View style={styles.tabRow}>
                <TouchableOpacity
                  style={[styles.tab, paymentTab === 'online' && styles.activeTabOnline]}
                  onPress={() => setPaymentTab('online')}
                >
                  <ShieldCheck size={16} color={paymentTab === 'online' ? '#FFFFFF' : '#16A34A'} />
                  <Text style={[styles.tabText, paymentTab === 'online' && styles.activeTabText]}>
                    Online UPI (Recommended)
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.tab, paymentTab === 'cash' && styles.activeTabCash]}
                  onPress={() => setPaymentTab('cash')}
                >
                  <Banknote size={16} color={paymentTab === 'cash' ? '#FFFFFF' : '#DC2626'} />
                  <Text style={[styles.tabText, paymentTab === 'cash' && styles.activeTabText]}>
                    Cash (Self-Risk)
                  </Text>
                </TouchableOpacity>
              </View>

              {/* ONLINE PAYMENT TAB */}
              {paymentTab === 'online' && (
                <View style={styles.methodBox}>
                  <View style={styles.onlineBadge}>
                    <ShieldCheck size={14} color="#166534" />
                    <Text style={styles.onlineBadgeText}>
                      Zero-Corruption Guarantee: Direct transfer to official KVK account.
                    </Text>
                  </View>

                  {/* Dynamic Mock UPI QR Code Box */}
                  <View style={styles.qrContainer}>
                    <View style={styles.qrMock}>
                      <QrCode size={110} color="#1E293B" />
                      <Text style={styles.qrAmountText}>₹{amount}</Text>
                    </View>
                    <Text style={styles.beneficiaryText}>{beneficiaryName}</Text>
                    <Text style={styles.upiIdText}>UPI ID: krushipragya.kvk@sbi</Text>
                  </View>

                  {/* 1-Tap UPI Apps Simulator */}
                  <Text style={styles.upiAppsTitle}>Instant 1-Tap Test Pay (Demo Mode):</Text>
                  <View style={styles.upiGrid}>
                    <TouchableOpacity
                      style={[styles.upiBtn, { borderColor: '#4285F4' }]}
                      onPress={() => handleSimulateOnlinePay('GPay')}
                      disabled={isProcessing}
                    >
                      <Smartphone size={18} color="#4285F4" />
                      <Text style={[styles.upiBtnText, { color: '#4285F4' }]}>GPay</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                      style={[styles.upiBtn, { borderColor: '#5F259F' }]}
                      onPress={() => handleSimulateOnlinePay('PhonePe')}
                      disabled={isProcessing}
                    >
                      <Smartphone size={18} color="#5F259F" />
                      <Text style={[styles.upiBtnText, { color: '#5F259F' }]}>PhonePe</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                      style={[styles.upiBtn, { borderColor: '#00BAF2' }]}
                      onPress={() => handleSimulateOnlinePay('Paytm')}
                      disabled={isProcessing}
                    >
                      <Smartphone size={18} color="#00BAF2" />
                      <Text style={[styles.upiBtnText, { color: '#00BAF2' }]}>Paytm</Text>
                    </TouchableOpacity>
                  </View>

                  {isProcessing && (
                    <View style={styles.processingRow}>
                      <ActivityIndicator size="small" color={Colors.primary} />
                      <Text style={styles.processingText}>Processing secure simulated payment...</Text>
                    </View>
                  )}
                </View>
              )}

              {/* CASH PAYMENT TAB WITH DISCLAIMER */}
              {paymentTab === 'cash' && (
                <View style={styles.methodBox}>
                  {/* Warning Notice */}
                  <View style={styles.cashWarningCard}>
                    <AlertTriangle size={20} color="#DC2626" />
                    <Text style={styles.cashWarningTitle}>
                      ⚠️ Self-Risk Cash Warning / ನಗದು ಪಾವತಿ ಎಚ್ಚರಿಕೆ
                    </Text>
                    <Text style={styles.cashWarningDesc}>
                      • KrushiPragya and Govt KVK strictly discourage unrecorded cash handovers to prevent bribery or overcharging.
                    </Text>
                    <Text style={styles.cashWarningDesc}>
                      • If you choose to pay in cash directly to an agent or officer, it is at your OWN RISK. KrushiPragya is NOT responsible for any unverified cash transactions or financial loss.
                    </Text>
                  </View>

                  {/* Mandatory Checkbox */}
                  <TouchableOpacity
                    style={styles.checkboxRow}
                    activeOpacity={0.8}
                    onPress={() => setCashRiskAccepted(!cashRiskAccepted)}
                  >
                    <View style={[styles.checkbox, cashRiskAccepted && styles.checkboxChecked]}>
                      {cashRiskAccepted && <Check size={14} color="#FFFFFF" />}
                    </View>
                    <Text style={styles.checkboxLabel}>
                      I understand the risk and take full responsibility for paying cash manually. (ನಾನು ಅಪಾಯವನ್ನು ಅರ್ಥಮಾಡಿಕೊಂಡಿದ್ದೇನೆ ಮತ್ತು ನಗದು ಪಾವತಿಗೆ ಸಂಪೂರ್ಣ ಜವಾಬ್ದಾರನಾಗಿರುತ್ತೇನೆ).
                    </Text>
                  </TouchableOpacity>

                  {/* Submit Button */}
                  <TouchableOpacity
                    style={[styles.cashSubmitBtn, !cashRiskAccepted && styles.cashSubmitBtnDisabled]}
                    onPress={handleConfirmCashPay}
                    disabled={!cashRiskAccepted || isProcessing}
                  >
                    {isProcessing ? (
                      <ActivityIndicator size="small" color="#FFFFFF" />
                    ) : (
                      <>
                        <Banknote size={16} color="#FFFFFF" />
                        <Text style={styles.cashSubmitText}>
                          Confirm Cash (₹{amount}) - At Self-Risk
                        </Text>
                      </>
                    )}
                  </TouchableOpacity>
                </View>
              )}
            </ScrollView>
          )}
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'flex-end',
  },
  sheetContainer: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: BorderRadius.xl,
    borderTopRightRadius: BorderRadius.xl,
    maxHeight: '88%',
    paddingBottom: Spacing.xl,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: Spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  headerSub: {
    fontSize: 12,
    color: Colors.textSecondary,
    fontWeight: '600',
    marginTop: 2,
  },
  closeBtn: {
    padding: 6,
  },
  content: {
    padding: Spacing.lg,
    gap: Spacing.md,
  },
  tabRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
    marginBottom: Spacing.xs,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    borderRadius: BorderRadius.md,
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  activeTabOnline: {
    backgroundColor: '#16A34A',
    borderColor: '#16A34A',
  },
  activeTabCash: {
    backgroundColor: '#DC2626',
    borderColor: '#DC2626',
  },
  tabText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#475569',
  },
  activeTabText: {
    color: '#FFFFFF',
  },
  methodBox: {
    gap: Spacing.md,
  },
  onlineBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#DCFCE7',
    padding: 10,
    borderRadius: BorderRadius.sm,
  },
  onlineBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#166534',
    flex: 1,
  },
  qrContainer: {
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  qrMock: {
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: Spacing.md,
    borderRadius: BorderRadius.md,
    marginBottom: 8,
  },
  qrAmountText: {
    fontSize: 18,
    fontWeight: '800',
    color: Colors.primary,
    marginTop: 4,
  },
  beneficiaryText: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  upiIdText: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  upiAppsTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  upiGrid: {
    flexDirection: 'row',
    gap: 10,
  },
  upiBtn: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: BorderRadius.md,
    borderWidth: 1.5,
    backgroundColor: '#FFFFFF',
    gap: 4,
  },
  upiBtnText: {
    fontSize: 12,
    fontWeight: '800',
  },
  processingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 8,
  },
  processingText: {
    fontSize: 12,
    color: Colors.textPrimary,
    fontWeight: '600',
  },
  cashWarningCard: {
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    gap: 6,
  },
  cashWarningTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#991B1B',
  },
  cashWarningDesc: {
    fontSize: 11,
    color: '#7F1D1B',
    lineHeight: 16,
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    paddingVertical: 4,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 4,
    borderWidth: 1.5,
    borderColor: '#94A3B8',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  checkboxChecked: {
    backgroundColor: '#DC2626',
    borderColor: '#DC2626',
  },
  checkboxLabel: {
    flex: 1,
    fontSize: 11,
    fontWeight: '600',
    color: '#334155',
    lineHeight: 16,
  },
  cashSubmitBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#DC2626',
    paddingVertical: 14,
    borderRadius: BorderRadius.md,
    marginTop: 8,
  },
  cashSubmitBtnDisabled: {
    backgroundColor: '#CBD5E1',
  },
  cashSubmitText: {
    fontSize: 12,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  receiptContent: {
    padding: Spacing.lg,
  },
  receiptCard: {
    padding: Spacing.lg,
    borderRadius: BorderRadius.lg,
    borderWidth: 1,
    alignItems: 'center',
    gap: 8,
  },
  receiptGreen: {
    backgroundColor: '#F0FDF4',
    borderColor: '#BBF7D0',
  },
  receiptAmber: {
    backgroundColor: '#FFFBEB',
    borderColor: '#FDE68A',
  },
  receiptStatusText: {
    fontSize: 15,
    fontWeight: '800',
    color: Colors.textPrimary,
    textAlign: 'center',
  },
  receiptSubText: {
    fontSize: 11,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 8,
  },
  divider: {
    width: '100%',
    height: 1,
    backgroundColor: Colors.border,
    marginVertical: 4,
  },
  receiptRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
    paddingVertical: 4,
  },
  receiptLabel: {
    fontSize: 12,
    color: Colors.textSecondary,
  },
  receiptVal: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  doneBtn: {
    backgroundColor: Colors.primary,
    paddingVertical: 12,
    borderRadius: BorderRadius.md,
    alignItems: 'center',
    marginTop: Spacing.lg,
  },
  doneBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '800',
  },
});
