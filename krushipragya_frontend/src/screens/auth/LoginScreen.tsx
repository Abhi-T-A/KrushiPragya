import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  SafeAreaView,
  ImageBackground,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/common/Button';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import {
  ArrowLeft,
  Phone,
  Sparkles,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react-native';

interface LoginScreenProps {
  onProceedToOTP: (phone: string) => void;
  onBack?: () => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({
  onProceedToOTP,
  onBack,
}) => {
  const { language } = useLanguage();
  const { login } = useAuth();
  const [phoneNumber, setPhoneNumber] = useState('');

  const handleContinue = () => {
    const formattedPhone = phoneNumber.trim() ? `+91 ${phoneNumber}` : '+91 98765 43210';
    onProceedToOTP(formattedPhone);
  };

  const handleQuickDemoLogin = () => {
    login('+91 98765 43210', 'farmer', 'v2', 'ಅಭಿ ಗೌಡ (Abhi)');
    onProceedToOTP('+91 98765 43210');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.keyboardView}
      >
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          {/* Top Hero Banner with Realistic Malnad Plantation */}
          <View style={styles.bannerContainer}>
            <ImageBackground
              source={require('../../../assets/login_banner.jpg')}
              style={styles.bannerImage}
              resizeMode="cover"
            >
              <View style={styles.bannerOverlay}>
                {onBack && (
                  <TouchableOpacity
                    activeOpacity={0.7}
                    onPress={onBack}
                    style={styles.backButton}
                  >
                    <ArrowLeft size={20} color={Colors.textPrimary} />
                  </TouchableOpacity>
                )}

                <View style={styles.welcomeTag}>
                  <Sparkles size={14} color={Colors.accentGold} />
                  <Text style={styles.welcomeTagText}>
                    {language === 'kn' ? 'ಸ್ವಾಗತ' : 'Welcome'}
                  </Text>
                </View>

                <Text style={styles.bannerTitle}>
                  {language === 'kn' ? 'ಕೃಷಿಪ್ರಜ್ಞಾ ಲಾಗಿನ್' : 'KrushiPragya Login'}
                </Text>
                <Text style={styles.bannerSubtitle}>
                  {language === 'kn'
                    ? 'ನಿಮ್ಮ ಮೊಬೈಲ್ ಸಂಖ್ಯೆಯೊಂದಿಗೆ ಪ್ರಾರಂಭಿಸಿ'
                    : 'Enter mobile number to continue'}
                </Text>
              </View>
            </ImageBackground>
          </View>

          {/* Form Content Area */}
          <View style={styles.formContainer}>
            {/* Mobile Number Input */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>
                {language === 'kn' ? 'ಮೊಬೈಲ್ ಸಂಖ್ಯೆ (Mobile Number)' : 'Mobile Number'}
              </Text>
              <View style={styles.phoneInputRow}>
                <View style={styles.countryCodeBox}>
                  <Phone size={16} color={Colors.primary} />
                  <Text style={styles.countryCodeText}>+91</Text>
                </View>
                <TextInput
                  style={styles.phoneTextInput}
                  placeholder={language === 'kn' ? '10 ಅಂಕಿಗಳ ಸಂಖ್ಯೆ ನಮೂದಿಸಿ' : '10-digit mobile number'}
                  placeholderTextColor={Colors.textMuted}
                  keyboardType="phone-pad"
                  maxLength={10}
                  value={phoneNumber}
                  onChangeText={setPhoneNumber}
                />
              </View>
            </View>

            {/* Main Submit Button */}
            <Button
              title={language === 'kn' ? 'OTP ಪಡೆಯಿರಿ (Continue)' : 'Get OTP (Continue)'}
              onPress={handleContinue}
              size="large"
              icon={<ChevronRight size={20} color={Colors.textWhite} />}
              style={styles.continueBtn}
            />

            {/* Quick Demo Bypass for Hackathon Judges */}
            <View style={styles.demoBypassBox}>
              <View style={styles.demoHeader}>
                <ShieldCheck size={14} color={Colors.primary} />
                <Text style={styles.demoHeaderText}>
                  {language === 'kn' ? 'ಡೆಮೊ ಲಾಗಿನ್ (1-Tap Judge Demo)' : '1-Tap Demo Quick Login'}
                </Text>
              </View>
              <TouchableOpacity
                onPress={handleQuickDemoLogin}
                style={styles.demoPill}
              >
                <Text style={styles.demoPillText}>
                  👨‍🌾 {language === 'kn' ? 'ರೈತರ ಖಾತೆ ಲಾಗಿನ್ (Quick Demo)' : 'Farmer Login (Quick Demo)'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingBottom: Spacing.xxxl,
  },
  bannerContainer: {
    height: 240,
    width: '100%',
    overflow: 'hidden',
  },
  bannerImage: {
    width: '100%',
    height: '100%',
  },
  bannerOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.38)',
    padding: Spacing.lg,
    justifyContent: 'flex-end',
  },
  backButton: {
    position: 'absolute',
    top: Spacing.md,
    left: Spacing.lg,
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 3,
  },
  welcomeTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(255,255,255,0.92)',
    alignSelf: 'flex-start',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: BorderRadius.full,
    marginBottom: Spacing.xs,
  },
  welcomeTagText: {
    ...Typography.caption,
    fontWeight: '800',
    color: Colors.primaryDark,
  },
  bannerTitle: {
    ...Typography.display,
    fontSize: 26,
    color: Colors.textWhite,
    fontWeight: '800',
    textShadowColor: 'rgba(0,0,0,0.4)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 4,
  },
  bannerSubtitle: {
    ...Typography.bodyLarge,
    color: 'rgba(255,255,255,0.9)',
    marginTop: 2,
  },
  formContainer: {
    padding: Spacing.lg,
    gap: Spacing.md,
  },
  inputGroup: {
    gap: Spacing.xs,
    marginTop: Spacing.sm,
  },
  inputLabel: {
    ...Typography.bodyLarge,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  phoneInputRow: {
    flexDirection: 'row',
    gap: Spacing.xs,
  },
  countryCodeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: BorderRadius.lg,
    paddingHorizontal: Spacing.md,
    height: 52,
  },
  countryCodeText: {
    ...Typography.title2,
    color: Colors.textPrimary,
    fontWeight: '800',
  },
  phoneTextInput: {
    flex: 1,
    height: 52,
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: BorderRadius.lg,
    paddingHorizontal: Spacing.md,
    ...Typography.title2,
    color: Colors.textPrimary,
  },
  continueBtn: {
    marginTop: Spacing.sm,
  },
  demoBypassBox: {
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.xl,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
    marginTop: Spacing.sm,
    gap: Spacing.sm,
  },
  demoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  demoHeaderText: {
    ...Typography.caption,
    fontWeight: '800',
    color: Colors.primaryDark,
  },
  demoPill: {
    paddingVertical: 12,
    borderRadius: BorderRadius.md,
    backgroundColor: Colors.primaryLight,
    borderWidth: 1.5,
    borderColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  demoPillText: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.primaryDark,
  },
});
