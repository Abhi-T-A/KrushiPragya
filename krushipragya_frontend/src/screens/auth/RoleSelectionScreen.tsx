import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Dimensions,
  ImageBackground,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth, UserRole } from '../../context/AuthContext';
import { Button } from '../../components/common/Button';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import {
  ArrowLeft,
  ChevronRight,
  Sparkles,
  Sprout,
  Microscope,
  Landmark,
  Store,
  Users,
  CheckCircle2,
  Globe2,
} from 'lucide-react-native';

const { height: SCREEN_HEIGHT } = Dimensions.get('window');

interface RoleItem {
  role: UserRole;
  labelEn: string;
  labelKn: string;
  subEn: string;
  subKn: string;
  Icon: React.ComponentType<any>;
  color: string;
  bg: string;
}

const ROLE_ITEMS: RoleItem[] = [
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
    labelEn: 'Community Member / FPO',
    labelKn: 'ಗ್ರಾಮ ಸಮುದಾಯ & ಎಫ್‌ಪಿಒ',
    subEn: 'FPO coordination & locality corroboration',
    subKn: 'ಗ್ರಾಮ ದೃಢೀಕರಣ & ಸಮುದಾಯ ನೆರವು',
    Icon: Users,
    color: '#0D9488',
    bg: '#CCFBF1',
  },
];

interface RoleSelectionScreenProps {
  onContinue: (role: UserRole) => void;
  onBack?: () => void;
}

export const RoleSelectionScreen: React.FC<RoleSelectionScreenProps> = ({
  onContinue,
  onBack,
}) => {
  const insets = useSafeAreaInsets();
  const { language, setLanguage } = useLanguage();
  const { user, setRole } = useAuth();
  const [selectedRole, setSelectedRole] = useState<UserRole>(user?.role || 'farmer');

  const isKn = language === 'kn';
  const isCompact = SCREEN_HEIGHT < 720;
  const isTall = SCREEN_HEIGHT >= 800;

  const handleSelectRole = (role: UserRole) => {
    setSelectedRole(role);
    setRole(role);
  };

  const handleNext = () => {
    setRole(selectedRole);
    onContinue(selectedRole);
  };

  const bannerHeight = Math.min(190, Math.max(150, Math.round(SCREEN_HEIGHT * 0.20))) + insets.top;

  return (
    <View style={styles.container}>
      <ScrollView
        contentContainerStyle={[
          styles.scrollContent,
          { minHeight: SCREEN_HEIGHT },
        ]}
        showsVerticalScrollIndicator={false}
        bounces={false}
      >
        {/* Top Hero Banner */}
        <View style={[styles.bannerContainer, { height: bannerHeight }]}>
          <ImageBackground
            source={require('../../../assets/login_banner.jpg')}
            style={styles.bannerImage}
            resizeMode="cover"
          >
            <View style={[styles.bannerOverlay, { paddingTop: insets.top + (isCompact ? 6 : 10) }]}>
              {/* Top Navigation Row */}
              <View style={styles.navRow}>
                {onBack ? (
                  <TouchableOpacity
                    activeOpacity={0.7}
                    onPress={onBack}
                    style={styles.backButton}
                  >
                    <ArrowLeft size={18} color={Colors.textPrimary} />
                  </TouchableOpacity>
                ) : (
                  <View style={{ width: 36 }} />
                )}

                <TouchableOpacity
                  activeOpacity={0.8}
                  onPress={() => setLanguage(isKn ? 'en' : 'kn')}
                  style={styles.langPill}
                >
                  <Globe2 size={13} color="#D97706" />
                  <Text style={styles.langPillText}>{isKn ? 'English' : 'ಕನ್ನಡ'}</Text>
                </TouchableOpacity>
              </View>

              <View style={styles.welcomeTag}>
                <Sparkles size={13} color="#D97706" />
                <Text style={styles.welcomeTagText}>
                  {isKn ? 'ಹಂತ 1: ಪಾತ್ರ ಆಯ್ಕೆ' : 'Step 1: Role Selection'}
                </Text>
              </View>

              <Text style={[styles.bannerTitle, isCompact && { fontSize: 20 }]}>
                {isKn ? 'ನಿಮ್ಮ ಪಾತ್ರವನ್ನು ಆಯ್ಕೆಮಾಡಿ' : 'Select Your Role'}
              </Text>
              <Text style={styles.bannerSubtitle}>
                {isKn
                  ? 'ಕೃಷಿಪ್ರಜ್ಞಾ ಪ್ರವೇಶಿಸಲು ನಿಮ್ಮ ಸಂಬಂಧಿತ ಪಾತ್ರ ಆಯ್ಕೆಮಾಡಿ'
                  : 'Choose your persona to customize your dashboard'}
              </Text>
            </View>
          </ImageBackground>
        </View>

        {/* 5-Role Selection Cards Container */}
        <View
          style={[
            styles.cardsContainer,
            { paddingBottom: Math.max(insets.bottom, 16) + (isCompact ? 8 : 14) },
          ]}
        >
          <View style={styles.cardsList}>
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
                    { paddingVertical: isCompact ? 9 : (isTall ? 12 : 10.5) },
                    isSelected && {
                      borderColor: color,
                      borderWidth: 2,
                      backgroundColor: bg,
                    },
                  ]}
                >
                  <View style={[styles.roleIconCircle, { backgroundColor: isSelected ? color : '#F1F5F9' }]}>
                    <Icon size={19} color={isSelected ? '#FFFFFF' : color} strokeWidth={2.4} />
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
                    <CheckCircle2 size={19} color={color} strokeWidth={2.4} />
                  )}
                </TouchableOpacity>
              );
            })}
          </View>

          {/* Action Button: Proceed to Profile Setup */}
          <View style={styles.bottomSection}>
            <Button
              title={isKn ? 'ಮುಂದುವರಿಸಿ (ವೈಯಕ್ತಿಕ ವಿವರ)' : 'Continue to Profile Setup'}
              onPress={handleNext}
              size="large"
              icon={<ChevronRight size={20} color={Colors.textWhite} />}
              style={styles.continueBtn}
            />
          </View>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
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
    backgroundColor: 'rgba(0,0,0,0.48)',
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.md,
    justifyContent: 'flex-end',
  },
  navRow: {
    position: 'absolute',
    top: 0,
    left: Spacing.md,
    right: Spacing.md,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    zIndex: 10,
  },
  backButton: {
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
  langPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  langPillText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#D97706',
  },
  welcomeTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 9,
    paddingVertical: 3.5,
    borderRadius: BorderRadius.full,
    alignSelf: 'flex-start',
    marginBottom: 4,
  },
  welcomeTagText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#92400E',
  },
  bannerTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: '#FFFFFF',
    textShadowColor: 'rgba(0,0,0,0.5)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  bannerSubtitle: {
    fontSize: 12,
    color: '#F1F5F9',
    marginTop: 2,
  },
  cardsContainer: {
    flex: 1,
    paddingHorizontal: Spacing.md,
    paddingTop: Spacing.md,
    justifyContent: 'space-between',
  },
  cardsList: {
    gap: 9,
    marginBottom: Spacing.md,
  },
  roleCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 12,
    paddingHorizontal: 12,
    gap: 12,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1.5,
  },
  roleIconCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
  },
  roleCardTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1E293B',
  },
  roleCardSub: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 1,
    lineHeight: 15,
  },
  bottomSection: {
    width: '100%',
    paddingTop: Spacing.xs,
  },
  continueBtn: {
    width: '100%',
  },
});
