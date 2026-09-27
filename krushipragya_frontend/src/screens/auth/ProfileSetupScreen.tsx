import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth, UserRole } from '../../context/AuthContext';
import { Button } from '../../components/common/Button';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import {
  ArrowLeft,
  User,
  Phone,
  ChevronRight,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Sprout,
  Microscope,
  Landmark,
  Store,
  Users,
} from 'lucide-react-native';

interface ProfileSetupScreenProps {
  onProceedToOTP: (data: { fullName: string; phone: string }) => void;
  onBack: () => void;
  initialName?: string;
  initialPhone?: string;
}

export const ProfileSetupScreen: React.FC<ProfileSetupScreenProps> = ({
  onProceedToOTP,
  onBack,
  initialName = '',
  initialPhone = '',
}) => {
  const { language } = useLanguage();
  const { user } = useAuth();
  const isKn = language === 'kn';

  const [fullName, setFullName] = useState(initialName || user?.name || '');
  const [phoneNumber, setPhoneNumber] = useState(
    (initialPhone || user?.phone || '')
      .replace('+91', '')
      .replace(/\s+/g, '')
      .trim()
  );
  const [errorMessage, setErrorMessage] = useState('');

  const currentRole = user?.role || 'farmer';

  const getRoleBadge = (role: UserRole) => {
    switch (role) {
      case 'expert':
        return {
          titleEn: 'Agriculture Expert',
          titleKn: 'ಕೃಷಿ ತಜ್ಞ / ವಿಜ್ಞಾನಿ',
          color: '#2563EB',
          bg: '#DBEAFE',
          Icon: Microscope,
        };
      case 'officer':
        return {
          titleEn: 'Government Officer',
          titleKn: 'ಕೃಷಿ ಇಲಾಖೆ ಅಧಿಕಾರಿ',
          color: '#9333EA',
          bg: '#F3E8FF',
          Icon: Landmark,
        };
      case 'buyer':
        return {
          titleEn: 'Buyer / Trader',
          titleKn: 'ಖರೀದಿದಾರ / ವರ್ತಕ',
          color: '#D97706',
          bg: '#FEF3C7',
          Icon: Store,
        };
      case 'community':
      case 'village_node':
        return {
          titleEn: 'Community Member',
          titleKn: 'ಗ್ರಾಮ ಸಮುದಾಯ ಸದಸ್ಯ',
          color: '#0D9488',
          bg: '#CCFBF1',
          Icon: Users,
        };
      case 'farmer':
      default:
        return {
          titleEn: 'Farmer',
          titleKn: 'ಬೆಳೆಗಾರ / ರೈತ',
          color: '#16A34A',
          bg: '#DCFCE7',
          Icon: Sprout,
        };
    }
  };

  const roleMeta = getRoleBadge(currentRole);
  const RoleIcon = roleMeta.Icon;

  const handleContinue = () => {
    setErrorMessage('');
    const cleanName = fullName.trim();
    const cleanDigits = phoneNumber.replace(/\D/g, '').trim();

    if (!cleanName) {
      setErrorMessage(
        isKn ? 'ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪೂರ್ಣ ಹೆಸರನ್ನು ನಮೂದಿಸಿ.' : 'Please enter your full name.'
      );
      return;
    }

    if (!cleanDigits || cleanDigits.length < 10) {
      setErrorMessage(
        isKn
          ? 'ದಯವಿಟ್ಟು ಸರಿಯಾದ 10 ಅಂಕಿಗಳ ಮೊಬೈಲ್ ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ.'
          : 'Please enter a valid 10-digit mobile number.'
      );
      return;
    }

    const formattedPhone = cleanDigits.startsWith('91') && cleanDigits.length === 12
      ? `+${cleanDigits}`
      : `+91 ${cleanDigits.slice(-10)}`;

    onProceedToOTP({
      fullName: cleanName,
      phone: formattedPhone,
    });
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.container}
      >
        {/* Top Header Bar */}
        <View style={styles.topBar}>
          <TouchableOpacity activeOpacity={0.7} onPress={onBack} style={styles.backButton}>
            <ArrowLeft size={20} color={Colors.textPrimary} />
          </TouchableOpacity>

          <View style={styles.headerStepPill}>
            <Sparkles size={13} color={Colors.primary} />
            <Text style={styles.headerStepText}>
              {isKn ? 'ಹಂತ 2: ವಿವರ' : 'Step 2: Profile'}
            </Text>
          </View>

          <View style={{ width: 36 }} />
        </View>

        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Active Role Card Badge */}
          <View style={[styles.roleBadgeBanner, { backgroundColor: roleMeta.bg, borderColor: roleMeta.color }]}>
            <View style={[styles.roleIconWrap, { backgroundColor: roleMeta.color }]}>
              <RoleIcon size={18} color="#FFFFFF" strokeWidth={2.4} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[styles.roleBadgeTitle, { color: roleMeta.color }]}>
                {isKn ? roleMeta.titleKn : roleMeta.titleEn}
              </Text>
              <Text style={styles.roleBadgeSub}>
                {isKn ? 'ಆಯ್ಕೆಮಾಡಿದ ಪಾತ್ರ' : 'Selected Persona'}
              </Text>
            </View>
            <CheckCircle2 size={18} color={roleMeta.color} />
          </View>

          {/* Heading */}
          <View style={styles.titleSection}>
            <Text style={styles.screenTitle}>
              {isKn ? 'ನಿಮ್ಮ ವೈಯಕ್ತಿಕ ವಿವರ' : 'Enter Your Profile Details'}
            </Text>
            <Text style={styles.screenSubtitle}>
              {isKn
                ? 'ಕೃಷಿಪ್ರಜ್ಞಾ ಸೇವೆಗಳು ಮತ್ತು ದೃಢೀಕರಣಕ್ಕಾಗಿ ನಿಮ್ಮ ಹೆಸರು ಮತ್ತು ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ನೀಡಿ.'
                : 'Enter your details to create your verified KrushiPragya profile.'}
            </Text>
          </View>

          {/* Error Message */}
          {errorMessage ? (
            <View style={styles.errorBox}>
              <AlertCircle size={16} color="#DC2626" />
              <Text style={styles.errorText}>{errorMessage}</Text>
            </View>
          ) : null}

          {/* Form Section */}
          <View style={styles.formCard}>
            {/* 1. Full Name */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>
                {isKn ? '1. ಪೂರ್ಣ ಹೆಸರು (Full Name)' : '1. Full Name'}
              </Text>
              <View style={styles.inputBox}>
                <User size={18} color={Colors.primary} />
                <TextInput
                  style={styles.textInput}
                  placeholder={isKn ? 'ಉದಾ: ಅಭಿ ಗೌಡ (Abhi Gowda)' : 'e.g. Abhi Gowda'}
                  placeholderTextColor={Colors.textMuted}
                  value={fullName}
                  onChangeText={(t) => {
                    setFullName(t);
                    if (errorMessage) setErrorMessage('');
                  }}
                  autoCapitalize="words"
                />
              </View>
            </View>

            {/* 2. Mobile Number */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>
                {isKn ? '2. ಮೊಬೈಲ್ ಸಂಖ್ಯೆ (Mobile Number)' : '2. Mobile Number'}
              </Text>
              <View style={styles.phoneInputRow}>
                <View style={styles.countryCodeBox}>
                  <Phone size={16} color={Colors.primary} />
                  <Text style={styles.countryCodeText}>+91</Text>
                </View>
                <TextInput
                  style={styles.phoneTextInput}
                  placeholder={isKn ? '10 ಅಂಕಿಗಳ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ' : '10-digit number'}
                  placeholderTextColor={Colors.textMuted}
                  keyboardType="phone-pad"
                  maxLength={10}
                  value={phoneNumber}
                  onChangeText={(t) => {
                    setPhoneNumber(t);
                    if (errorMessage) setErrorMessage('');
                  }}
                />
              </View>
              <Text style={styles.helperText}>
                {isKn
                  ? '🔒 ಮುಂದಿನ ಹಂತದಲ್ಲಿ ಈ ಸಂಖ್ಯೆಗೆ 6 ಅಂಕಿಗಳ OTP ಕಳುಹಿಸಲಾಗುವುದು.'
                  : '🔒 A 6-digit OTP will be verified in the next step.'}
              </Text>
            </View>
          </View>

          {/* Bottom Security / Trust Pill */}
          <View style={styles.trustBadge}>
            <ShieldCheck size={16} color="#16A34A" />
            <Text style={styles.trustBadgeText}>
              {isKn
                ? 'ಸುರಕ್ಷಿತ Supabase & PostgreSQL ಅಧಿಕೃತ ವ್ಯವಸ್ಥೆ'
                : 'Secured with Supabase Auth & PostgreSQL RBAC'}
            </Text>
          </View>
        </ScrollView>

        {/* Bottom Sticky Action Button */}
        <View style={styles.bottomBar}>
          <Button
            title={isKn ? 'ಮುಂದುವರಿಸಿ (OTP ಪಡೆಯಿರಿ)' : 'Get OTP & Continue'}
            onPress={handleContinue}
            size="large"
            icon={<ChevronRight size={20} color={Colors.textWhite} />}
            style={styles.continueBtn}
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
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
    backgroundColor: Colors.surface,
  },
  backButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  headerStepPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: '#BBF7D0',
  },
  headerStepText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#166534',
  },
  scrollContent: {
    padding: Spacing.md,
    gap: Spacing.md,
  },
  roleBadgeBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: BorderRadius.md,
    borderWidth: 1.5,
    gap: 12,
  },
  roleIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  roleBadgeTitle: {
    fontSize: 14,
    fontWeight: '800',
  },
  roleBadgeSub: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 1,
  },
  titleSection: {
    gap: 4,
  },
  screenTitle: {
    ...Typography.display,
    fontSize: 22,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  screenSubtitle: {
    ...Typography.bodyLarge,
    fontSize: 13,
    color: Colors.textSecondary,
    lineHeight: 18,
  },
  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FEE2E2',
    borderWidth: 1,
    borderColor: '#FCA5A5',
    padding: 10,
    borderRadius: BorderRadius.sm,
  },
  errorText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#B91C1C',
    flex: 1,
  },
  formCard: {
    backgroundColor: Colors.surface,
    padding: Spacing.md,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    gap: Spacing.md,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  inputGroup: {
    gap: 6,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  inputBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    borderRadius: BorderRadius.sm,
    paddingHorizontal: 12,
    height: 48,
    gap: 10,
  },
  textInput: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: '#0F172A',
  },
  phoneInputRow: {
    flexDirection: 'row',
    gap: 8,
  },
  countryCodeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#F8FAFC',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    borderRadius: BorderRadius.sm,
    paddingHorizontal: 12,
    height: 48,
  },
  countryCodeText: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  phoneTextInput: {
    flex: 1,
    height: 48,
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    borderRadius: BorderRadius.sm,
    paddingHorizontal: 12,
    fontSize: 15,
    fontWeight: '600',
    color: '#0F172A',
  },
  helperText: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
  },
  trustBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
  },
  trustBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#15803D',
  },
  bottomBar: {
    padding: Spacing.md,
    backgroundColor: Colors.surface,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
  },
  continueBtn: {
    width: '100%',
  },
});
