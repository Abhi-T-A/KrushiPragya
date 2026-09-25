import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  SafeAreaView,
  ImageBackground,
} from 'react-native';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth, UserRole, ROLE_PROFILES } from '../../context/AuthContext';
import { Button } from '../../components/common/Button';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import {
  Phone,
  ChevronRight,
  ArrowLeft,
  Sparkles,
  Sprout,
  Microscope,
  Landmark,
  Store,
  Users,
  CheckCircle2,
} from 'lucide-react-native';

interface RoleCardItem {
  role: UserRole;
  labelEn: string;
  labelKn: string;
  subEn: string;
  subKn: string;
  Icon: React.ComponentType<any>;
  color: string;
  bg: string;
}

const ROLE_ITEMS: RoleCardItem[] = [
  {
    role: 'farmer',
    labelEn: 'Farmer',
    labelKn: 'ಬೆಳೆಗಾರ / ರೈತ',
    subEn: 'Mallikarjuna Gowda (Ujire)',
    subKn: 'ಮಲ್ಲಿಕಾರ್ಜುನ ಗೌಡ (ಉಜಿರೆ)',
    Icon: Sprout,
    color: '#16A34A',
    bg: '#DCFCE7',
  },
  {
    role: 'expert',
    labelEn: 'Agriculture Expert',
    labelKn: 'ಕೃಷಿ ತಜ್ಞ / ವಿಜ್ಞಾನಿ',
    subEn: 'Dr. Ramesh K (KVK Brahmavar)',
    subKn: 'ಡಾ. ರಮೇಶ್ (ಬ್ರಹ್ಮಾವರ)',
    Icon: Microscope,
    color: '#2563EB',
    bg: '#DBEAFE',
  },
  {
    role: 'officer',
    labelEn: 'Government Officer',
    labelKn: 'ಕೃಷಿ ಇಲಾಖೆ ಅಧಿಕಾರಿ',
    subEn: 'Sunitha IAS (Agri Dept)',
    subKn: 'ಶ್ರೀಮತಿ ಸುನಿತಾ (ಕೃಷಿ ಇಲಾಖೆ)',
    Icon: Landmark,
    color: '#9333EA',
    bg: '#F3E8FF',
  },
  {
    role: 'buyer',
    labelEn: 'Buyer / Trader',
    labelKn: 'ಖರೀದಿದಾರ / ವರ್ತಕ',
    subEn: 'Rajesh Seth (APMC Mandi)',
    subKn: 'ರಾಜೇಶ್ ಸೇಠ್ (ಎಪಿಎಂಸಿ)',
    Icon: Store,
    color: '#D97706',
    bg: '#FEF3C7',
  },
  {
    role: 'community',
    labelEn: 'Community / FPO',
    labelKn: 'ಗ್ರಾಮ ಸಮುದಾಯ & ಎಫ್‌ಪಿಒ',
    subEn: 'Suresh Gowda (FPO Hub)',
    subKn: 'ಸುರೇಶ್ ಗೌಡ (ಎಫ್‌ಪಿಒ)',
    Icon: Users,
    color: '#0D9488',
    bg: '#CCFBF1',
  },
];

interface LoginScreenProps {
  onProceedToOTP: (phone: string) => void;
  onBack?: () => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({
  onProceedToOTP,
  onBack,
}) => {
  const { language } = useLanguage();
  const { login, setRole } = useAuth();
  const [selectedRole, setSelectedRole] = useState<UserRole>('farmer');
  const [phoneNumber, setPhoneNumber] = useState('9876543210');

  const isKn = language === 'kn';

  const handleSelectRole = (role: UserRole) => {
    setSelectedRole(role);
    setRole(role);
    const profile = ROLE_PROFILES[role];
    if (profile?.phone) {
      setPhoneNumber(profile.phone.replace('+91', '').trim().replace(/\s/g, ''));
    }
  };

  const handleContinue = () => {
    const formattedPhone = phoneNumber.startsWith('+91')
      ? phoneNumber
      : `+91 ${phoneNumber}`;
    login(formattedPhone, selectedRole, 'v2');
    onProceedToOTP(formattedPhone);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.keyboardView}
      >
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          {/* Top Hero Banner */}
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
                    <ArrowLeft size={18} color={Colors.textPrimary} />
                  </TouchableOpacity>
                )}

                <View style={styles.welcomeTag}>
                  <Sparkles size={13} color="#D97706" />
                  <Text style={styles.welcomeTagText}>
                    {isKn ? 'ಕೃಷಿಪ್ರಜ್ಞಾ ಲಾಗಿನ್' : 'KrushiPragya Login'}
                  </Text>
                </View>

                <Text style={styles.bannerTitle}>
                  {isKn ? 'ನಿಮ್ಮ ಪಾತ್ರವನ್ನು ಆಯ್ಕೆಮಾಡಿ' : 'Select Your Role'}
                </Text>
                <Text style={styles.bannerSubtitle}>
                  {isKn
                    ? '5 ಪ್ರಮುಖ ಪಾತ್ರಗಳಲ್ಲಿ ಒಂದನ್ನು ಆಯ್ಕೆಮಾಡಿ ಮುಂದುವರಿಯಿರಿ'
                    : 'Choose your stakeholder profile to enter dashboard'}
                </Text>
              </View>
            </ImageBackground>
          </View>

          {/* Form Content Area */}
          <View style={styles.formContainer}>
            {/* 5-Role Selection Cards Grid */}
            <Text style={styles.roleHeaderLabel}>
              {isKn ? '1. ಪಾತ್ರ ಆಯ್ಕೆ (5 User Personas):' : '1. Select User Role (5 Personas):'}
            </Text>

            <View style={styles.roleList}>
              {ROLE_ITEMS.map((item) => {
                const isSelected = selectedRole === item.role;
                const { Icon, color, bg, labelEn, labelKn, subEn, subKn } = item;

                return (
                  <TouchableOpacity
                    key={item.role}
                    activeOpacity={0.85}
                    onPress={() => handleSelectRole(item.role)}
                    style={[
                      styles.roleCard,
                      isSelected && {
                        borderColor: color,
                        borderWidth: 2,
                        backgroundColor: bg,
                      },
                    ]}
                  >
                    <View style={[styles.roleIconCircle, { backgroundColor: isSelected ? color : '#F1F5F9' }]}>
                      <Icon size={18} color={isSelected ? '#FFFFFF' : color} strokeWidth={2.4} />
                    </View>

                    <View style={{ flex: 1 }}>
                      <Text style={[styles.roleCardTitle, isSelected && { color: color, fontWeight: '800' }]}>
                        {isKn ? labelKn : labelEn}
                      </Text>
                      <Text style={styles.roleCardSub}>
                        {isKn ? subKn : subEn}
                      </Text>
                    </View>

                    {isSelected && (
                      <CheckCircle2 size={18} color={color} strokeWidth={2.4} />
                    )}
                  </TouchableOpacity>
                );
              })}
            </View>

            {/* Mobile Number Input */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>
                {isKn ? '2. ಮೊಬೈಲ್ ಸಂಖ್ಯೆ (Mobile Number):' : '2. Mobile Number:'}
              </Text>
              <View style={styles.phoneInputRow}>
                <View style={styles.countryCodeBox}>
                  <Phone size={15} color={Colors.primary} />
                  <Text style={styles.countryCodeText}>+91</Text>
                </View>
                <TextInput
                  style={styles.phoneTextInput}
                  placeholder={isKn ? '10 ಅಂಕಿಗಳ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ' : '10-digit mobile number'}
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
              title={isKn ? 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಪ್ರವೇಶಿಸಿ (Enter App)' : 'Enter Dashboard (Continue)'}
              onPress={handleContinue}
              size="large"
              icon={<ChevronRight size={20} color={Colors.textWhite} />}
              style={styles.continueBtn}
            />
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
    paddingBottom: 40,
  },
  bannerContainer: {
    height: 190,
    width: '100%',
    overflow: 'hidden',
  },
  bannerImage: {
    width: '100%',
    height: '100%',
  },
  bannerOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.45)',
    padding: Spacing.md,
    justifyContent: 'flex-end',
  },
  backButton: {
    position: 'absolute',
    top: Spacing.sm,
    left: Spacing.md,
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  welcomeTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FEF3C7',
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
    marginBottom: 4,
  },
  welcomeTagText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#B45309',
  },
  bannerTitle: {
    fontSize: 22,
    color: '#FFFFFF',
    fontWeight: '800',
  },
  bannerSubtitle: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.9)',
    marginTop: 2,
  },
  formContainer: {
    padding: Spacing.md,
    gap: Spacing.sm,
  },
  roleHeaderLabel: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0F172A',
    marginBottom: 2,
  },
  roleList: {
    gap: 8,
    marginBottom: Spacing.xs,
  },
  roleCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 10,
    padding: 10,
    gap: 10,
  },
  roleIconCircle: {
    width: 36,
    height: 36,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  roleCardTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F172A',
  },
  roleCardSub: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 1,
  },
  inputGroup: {
    gap: 4,
    marginTop: 4,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0F172A',
  },
  phoneInputRow: {
    flexDirection: 'row',
    gap: 6,
  },
  countryCodeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    borderRadius: 8,
    paddingHorizontal: 10,
    height: 46,
  },
  countryCodeText: {
    fontSize: 14,
    color: '#0F172A',
    fontWeight: '800',
  },
  phoneTextInput: {
    flex: 1,
    height: 46,
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 14,
    color: '#0F172A',
  },
  continueBtn: {
    marginTop: 8,
  },
});