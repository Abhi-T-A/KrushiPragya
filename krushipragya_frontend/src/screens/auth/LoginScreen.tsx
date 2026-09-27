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
  ImageBackground,
  Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
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

const { height: SCREEN_HEIGHT } = Dimensions.get('window');

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
    subEn: 'Crop health, weather alerts & mandi rates',
    subKn: 'ಬೆಳೆ ರಕ್ಷಣೆ, ಹವಾಮಾನ & ಮಾರುಕಟ್ಟೆ ಮಾಹಿತಿ',
    Icon: Sprout,
    color: '#16A34A',
    bg: '#DCFCE7',
  },
  {
    role: 'expert',
    labelEn: 'Agriculture Expert',
    labelKn: 'ಕೃಷಿ ತಜ್ಞ / ವಿಜ್ಞಾನಿ',
    subEn: 'Disease diagnosis & expert verification',
    subKn: 'ರೋಗ ತಪಾಸಣೆ & ವೈಜ್ಞಾನಿಕ ದೃಢೀಕರಣ',
    Icon: Microscope,
    color: '#2563EB',
    bg: '#DBEAFE',
  },
  {
    role: 'officer',
    labelEn: 'Government Officer',
    labelKn: 'ಕೃಷಿ ಇಲಾಖೆ ಅಧಿಕಾರಿ',
    subEn: 'Government schemes & subsidies',
    subKn: 'ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು & ರೈತ ಸೌಲಭ್ಯಗಳು',
    Icon: Landmark,
    color: '#9333EA',
    bg: '#F3E8FF',
  },
  {
    role: 'buyer',
    labelEn: 'Buyer / Trader',
    labelKn: 'ಖರೀದಿದಾರ / ವರ್ತಕ',
    subEn: 'Crop procurement & APMC trading',
    subKn: 'ಬೆಳೆ ಖರೀದಿ & ಎಪಿಎಂಸಿ ಮಾರುಕಟ್ಟೆ',
    Icon: Store,
    color: '#D97706',
    bg: '#FEF3C7',
  },
  {
    role: 'community',
    labelEn: 'Community / FPO',
    labelKn: 'ಗ್ರಾಮ ಸಮುದಾಯ & ಎಫ್‌ಪಿಒ',
    subEn: 'FPO coordination & community support',
    subKn: 'ರೈತ ಉತ್ಪಾದಕ ಸಂಸ್ಥೆ & ಸಮುದಾಯ ನೆರವು',
    Icon: Users,
    color: '#0D9488',
    bg: '#CCFBF1',
  },
];

interface LoginScreenProps {
  onProceedToOTP: (phone: string) => void;
  onEnterApp?: () => void;
  onBack?: () => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({
  onProceedToOTP,
  onEnterApp,
  onBack,
}) => {
  const insets = useSafeAreaInsets();
  const { language } = useLanguage();
  const { login, setRole } = useAuth();
  const [selectedRole, setSelectedRole] = useState<UserRole>('farmer');
  const [phoneNumber, setPhoneNumber] = useState('');

  const isKn = language === 'kn';
  const isTallScreen = SCREEN_HEIGHT >= 800;
  const isCompactScreen = SCREEN_HEIGHT < 720;

  const handleSelectRole = (role: UserRole) => {
    setSelectedRole(role);
    setRole(role);
  };

  const handleContinue = () => {
    const raw = phoneNumber.trim();
    const formattedPhone = raw
      ? (raw.startsWith('+91') ? raw : `+91 ${raw}`)
      : '+91 9876543210';
    login(formattedPhone, selectedRole, 'v2');
    if (onEnterApp) {
      onEnterApp();
    } else {
      onProceedToOTP(formattedPhone);
    }
  };

  const bannerHeight = Math.min(210, Math.max(160, Math.round(SCREEN_HEIGHT * 0.22))) + insets.top;

  return (
    <View style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={[
            styles.scrollContent,
            { minHeight: SCREEN_HEIGHT },
          ]}
          showsVerticalScrollIndicator={false}
          bounces={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Top Hero Banner */}
          <View style={[styles.bannerContainer, { height: bannerHeight }]}>
            <ImageBackground
              source={require('../../../assets/login_banner.jpg')}
              style={styles.bannerImage}
              resizeMode="cover"
            >
              <View style={[styles.bannerOverlay, { paddingTop: insets.top + (isCompactScreen ? 4 : 8) }]}>
                {onBack && (
                  <TouchableOpacity
                    activeOpacity={0.7}
                    onPress={onBack}
                    style={[styles.backButton, { top: insets.top + (isCompactScreen ? 6 : 10) }]}
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

                <Text style={[styles.bannerTitle, isCompactScreen && { fontSize: 20 }]}>
                  {isKn ? 'ನಿಮ್ಮ ಪಾತ್ರವನ್ನು ಆಯ್ಕೆಮಾಡಿ' : 'Select Your Role'}
                </Text>
                <Text style={styles.bannerSubtitle}>
                  {isKn
                    ? 'ಮುಂದುವರಿಯಲು ನಿಮ್ಮ ಪಾತ್ರವನ್ನು ಆಯ್ಕೆಮಾಡಿ ಲಾಗಿನ್ ಆಗಿ'
                    : 'Choose your role to enter KrushiPragya'}
                </Text>
              </View>
            </ImageBackground>
          </View>

          {/* Form Content Area: properly fills remaining vertical screen space */}
          <View
            style={[
              styles.formContainer,
              {
                paddingBottom: Math.max(insets.bottom, 16) + (isCompactScreen ? 6 : 12),
              },
            ]}
          >
            <View style={styles.upperFormSection}>
              {/* 5-Role Selection Cards Grid */}
              <Text style={styles.roleHeaderLabel}>
                {isKn ? '1. ಪಾತ್ರ ಆಯ್ಕೆಮಾಡಿ:' : '1. Select Your Role:'}
              </Text>

              <View style={[styles.roleList, { gap: isCompactScreen ? 6 : (isTallScreen ? 10 : 8) }]}>
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
                        {
                          paddingVertical: isCompactScreen ? 8 : (isTallScreen ? 11 : 9.5),
                        },
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
              <View style={[styles.inputGroup, { marginTop: isCompactScreen ? 4 : (isTallScreen ? 8 : 6) }]}>
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
            </View>

            {/* Bottom Action Area: Anchored cleanly at the bottom, eliminating empty space and avoiding floating button overlap */}
            <View style={[styles.bottomActionSection, { marginTop: isCompactScreen ? 8 : (isTallScreen ? 16 : 12) }]}>
              <Button
                title={isKn ? 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಪ್ರವೇಶಿಸಿ (Enter App)' : 'Enter Dashboard (Continue)'}
                onPress={handleContinue}
                size="large"
                icon={<ChevronRight size={20} color={Colors.textWhite} />}
                style={styles.continueBtn}
              />
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    backgroundColor: Colors.background,
  },
  bannerContainer: {
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
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.md,
    justifyContent: 'flex-end',
  },
  backButton: {
    position: 'absolute',
    left: Spacing.md,
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.15,
    shadowRadius: 2,
    elevation: 2,
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
    flex: 1,
    paddingHorizontal: Spacing.md,
    paddingTop: Spacing.sm,
    justifyContent: 'space-between',
  },
  upperFormSection: {
    gap: Spacing.xs,
  },
  roleHeaderLabel: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0F172A',
    marginBottom: 2,
  },
  roleList: {
    marginBottom: Spacing.xs,
  },
  roleCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 10,
    paddingHorizontal: 12,
    gap: 10,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 2,
    elevation: 1,
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
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0F172A',
  },
  phoneInputRow: {
    flexDirection: 'row',
    gap: 8,
  },
  countryCodeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    borderRadius: 8,
    paddingHorizontal: 12,
    height: 48,
  },
  countryCodeText: {
    fontSize: 14,
    color: '#0F172A',
    fontWeight: '800',
  },
  phoneTextInput: {
    flex: 1,
    height: 48,
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 15,
    fontWeight: '600',
    color: '#0F172A',
  },
  bottomActionSection: {
    width: '100%',
  },
  continueBtn: {
    width: '100%',
  },
});