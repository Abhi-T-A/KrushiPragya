import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/common/Button';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { ArrowLeft, KeyRound, CheckCircle2, RefreshCw } from 'lucide-react-native';

interface OTPVerificationScreenProps {
  phone: string;
  onVerifySuccess: () => void;
  onBack: () => void;
}

export const OTPVerificationScreen: React.FC<OTPVerificationScreenProps> = ({
  phone,
  onVerifySuccess,
  onBack,
}) => {
  const { language } = useLanguage();
  const { user, login } = useAuth();

  const [otp, setOtp] = useState('123456');
  const [timer, setTimer] = useState(30);

  useEffect(() => {
    if (timer > 0) {
      const interval = setInterval(() => setTimer((prev) => prev - 1), 1000);
      return () => clearInterval(interval);
    }
  }, [timer]);

  const handleVerify = () => {
    const activeRole = user?.role || 'farmer';
    login(phone, activeRole, user?.villageId || 'v2', user?.name);
    onVerifySuccess();
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.container}
      >
        {/* Top Header */}
        <View style={styles.topBar}>
          <TouchableOpacity activeOpacity={0.7} onPress={onBack} style={styles.backButton}>
            <ArrowLeft size={22} color={Colors.textPrimary} />
          </TouchableOpacity>
        </View>

        <View style={styles.content}>
          {/* Key Icon Badge */}
          <View style={styles.iconCircle}>
            <KeyRound size={40} color={Colors.primary} />
          </View>

          {/* Title & Sent Notice */}
          <Text style={styles.title}>
            {language === 'kn' ? 'OTP ಕಳುಹಿಸಲಾಗಿದೆ' : 'Verify Mobile OTP'}
          </Text>
          <Text style={styles.subtitle}>
            {language === 'kn'
              ? `ನಾವು ನಿಮ್ಮ ಸಂಖ್ಯೆ ${phone} ಗೆ 6 ಅಂಕಿಗಳ ಕೋಡ್ ಕಳುಹಿಸಿದ್ದೇವೆ`
              : `Enter the 6-digit verification code sent to ${phone}`}
          </Text>

          {/* 6 Digit Input Display */}
          <View style={styles.otpInputBox}>
            <TextInput
              style={styles.otpInput}
              value={otp}
              onChangeText={setOtp}
              keyboardType="number-pad"
              maxLength={6}
              textAlign="center"
            />
          </View>

          {/* Timer / Resend Row */}
          <View style={styles.timerRow}>
            {timer > 0 ? (
              <Text style={styles.timerText}>
                {language === 'kn' ? `ಮತ್ತೆ ಕಳುಹಿಸಿ (${timer} ಸೆಕೆಂಡುಗಳು)` : `Resend OTP in 00:${timer < 10 ? `0${timer}` : timer}`}
              </Text>
            ) : (
              <TouchableOpacity onPress={() => setTimer(30)} style={styles.resendBtn}>
                <RefreshCw size={14} color={Colors.primary} />
                <Text style={styles.resendText}>
                  {language === 'kn' ? 'ಮತ್ತೆ OTP ಕಳುಹಿಸಿ (Resend OTP)' : 'Resend OTP'}
                </Text>
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* Bottom Verify Action */}
        <View style={styles.bottomSection}>
          <Button
            title={language === 'kn' ? 'ದೃಢೀಕರಿಸಿ (Verify OTP)' : 'Verify & Continue'}
            onPress={handleVerify}
            size="large"
            icon={<CheckCircle2 size={20} color={Colors.textWhite} />}
          />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  container: {
    flex: 1,
    paddingHorizontal: Spacing.xl,
    paddingVertical: Spacing.md,
    justifyContent: 'space-between',
  },
  topBar: {
    paddingVertical: Spacing.xs,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  content: {
    alignItems: 'center',
    paddingHorizontal: Spacing.sm,
    marginTop: -Spacing.xxl,
  },
  iconCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.lg,
    borderWidth: 1.5,
    borderColor: '#BFE7D7',
  },
  title: {
    ...Typography.display,
    fontSize: 26,
    color: Colors.textPrimary,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: Spacing.xs,
  },
  subtitle: {
    ...Typography.bodyLarge,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: Spacing.xxl,
  },
  otpInputBox: {
    width: '100%',
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.lg,
    borderWidth: 2,
    borderColor: Colors.primary,
    paddingVertical: Spacing.md,
    marginBottom: Spacing.lg,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 2,
  },
  otpInput: {
    fontSize: 28,
    fontWeight: '900',
    color: Colors.textPrimary,
  },
  timerRow: {
    alignItems: 'center',
    marginTop: Spacing.xs,
  },
  timerText: {
    ...Typography.bodyLarge,
    color: Colors.textMuted,
    fontWeight: '600',
  },
  resendBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  resendText: {
    ...Typography.bodyLarge,
    color: Colors.primary,
    fontWeight: '700',
  },
  bottomSection: {
    paddingBottom: Spacing.lg,
  },
});
