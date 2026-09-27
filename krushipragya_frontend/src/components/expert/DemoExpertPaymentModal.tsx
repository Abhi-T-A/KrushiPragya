import React, { useState, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  CheckCircle2,
  X,
  ShieldCheck,
  FlaskConical,
  Sparkles,
} from 'lucide-react-native';

interface DemoExpertPaymentModalProps {
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const DemoExpertPaymentModal: React.FC<DemoExpertPaymentModalProps> = ({
  visible,
  onClose,
  onSuccess,
}) => {
  const [step, setStep] = useState<'prompt' | 'processing' | 'success'>('prompt');

  useEffect(() => {
    if (visible) {
      setStep('prompt');
    }
  }, [visible]);

  const handlePay = () => {
    setStep('processing');
    // Simulate payment processing
    setTimeout(() => {
      setStep('success');
      setTimeout(() => {
        onSuccess();
      }, 1200);
    }, 1300);
  };

  const handleClose = () => {
    if (step === 'processing') return;
    setStep('prompt');
    onClose();
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={handleClose}
    >
      <View style={styles.overlay}>
        <View style={styles.modalBox}>
          {/* Close button */}
          {step !== 'processing' && (
            <TouchableOpacity
              onPress={handleClose}
              style={styles.closeBtn}
              activeOpacity={0.7}
            >
              <X size={20} color="#64748B" />
            </TouchableOpacity>
          )}

          {step === 'prompt' && (
            <View style={styles.content}>
              {/* Demo Badge */}
              <View style={styles.demoBadge}>
                <FlaskConical size={14} color="#0D9488" />
                <Text style={styles.demoBadgeText}>DEMO PAYMENT</Text>
              </View>

              {/* Title */}
              <Text style={styles.titleKn}>ತಜ್ಞರ ಪರಿಶೀಲನೆ</Text>

              {/* Description */}
              <Text style={styles.descriptionKn}>
                ಕೃಷಿ ತಜ್ಞರಿಂದ ನಿಮ್ಮ ಬೆಳೆ ವರದಿಯನ್ನು{'\n'}ಪರಿಶೀಲಿಸಲು ವಿನಂತಿ ಸಲ್ಲಿಸಿ.
              </Text>

              {/* Fee Box */}
              <View style={styles.feeContainer}>
                <Text style={styles.feeLabel}>ಪರಿಶೀಲನೆ ಶುಲ್ಕ:</Text>
                <Text style={styles.feeAmount}>₹49</Text>
              </View>

              <View style={styles.demoNoticeBox}>
                <ShieldCheck size={14} color="#059669" />
                <Text style={styles.demoNoticeText}>
                  ಹ್ಯಾಕಥಾನ್ ಡೆಮೊ ಪಾವತಿ • ಯಾವುದೇ ನೈಜ ಶುಲ್ಕ ವಿಧಿಸಲಾಗುವುದಿಲ್ಲ
                </Text>
              </View>

              {/* Pay Button */}
              <TouchableOpacity
                style={styles.payBtn}
                activeOpacity={0.85}
                onPress={handlePay}
              >
                <Sparkles size={16} color="#FFFFFF" />
                <Text style={styles.payBtnText}>ಪಾವತಿಸಿ ₹49</Text>
              </TouchableOpacity>
            </View>
          )}

          {step === 'processing' && (
            <View style={styles.statusContainer}>
              <ActivityIndicator size="large" color="#0F766E" />
              <Text style={styles.processingText}>ಪಾವತಿ ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿದೆ...</Text>
              <Text style={styles.subStatusText}>Simulating secure demo transaction</Text>
            </View>
          )}

          {step === 'success' && (
            <View style={styles.statusContainer}>
              <View style={styles.successIconWrapper}>
                <CheckCircle2 size={44} color="#15803D" />
              </View>
              <Text style={styles.successTitle}>Demo Payment Successful</Text>
              <Text style={styles.successSubKn}>₹49 ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆ</Text>
              <Text style={styles.successMeta}>mode: DEMO • status: SUCCESS</Text>
            </View>
          )}
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.65)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing.lg,
  },
  modalBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.lg,
    padding: Spacing.xl,
    width: '100%',
    maxWidth: 360,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 10,
    position: 'relative',
  },
  closeBtn: {
    position: 'absolute',
    top: 14,
    right: 14,
    zIndex: 10,
    padding: 6,
  },
  content: {
    alignItems: 'center',
    gap: 12,
  },
  demoBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#F0FDFA',
    borderWidth: 1,
    borderColor: '#99F6E4',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
    marginTop: 4,
  },
  demoBadgeText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#0D9488',
    letterSpacing: 0.5,
  },
  titleKn: {
    fontSize: 20,
    fontWeight: '800',
    color: Colors.textPrimary,
    marginTop: 2,
    textAlign: 'center',
  },
  descriptionKn: {
    fontSize: 14,
    lineHeight: 22,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginHorizontal: 8,
  },
  feeContainer: {
    width: '100%',
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    paddingVertical: 14,
    paddingHorizontal: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 4,
  },
  feeLabel: {
    fontSize: 13,
    color: '#64748B',
    marginBottom: 4,
    fontWeight: '600',
  },
  feeAmount: {
    fontSize: 28,
    fontWeight: '900',
    color: '#0F766E',
  },
  demoNoticeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#ECFDF5',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: BorderRadius.sm,
    width: '100%',
  },
  demoNoticeText: {
    fontSize: 11,
    color: '#065F46',
    flex: 1,
    fontWeight: '500',
  },
  payBtn: {
    backgroundColor: '#0F766E',
    width: '100%',
    paddingVertical: 14,
    borderRadius: BorderRadius.md,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 6,
  },
  payBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
  },
  statusContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 24,
    gap: 12,
  },
  processingText: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginTop: 6,
  },
  subStatusText: {
    fontSize: 12,
    color: '#64748B',
  },
  successIconWrapper: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: '#DCFCE7',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  successTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: '#15803D',
  },
  successSubKn: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textPrimary,
  },
  successMeta: {
    fontSize: 11,
    color: '#64748B',
    fontFamily: 'monospace',
    marginTop: 2,
  },
});
