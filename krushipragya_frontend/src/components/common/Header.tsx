import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { MapPin, Globe2, User, Sprout, ArrowLeft } from 'lucide-react-native';

export const Header: React.FC<{
  title?: string;
  subtitle?: string;
  showVillage?: boolean;
  onBack?: () => void;
  rightAction?: React.ReactNode;
}> = ({
  title,
  subtitle,
  showVillage = true,
  onBack,
  rightAction,
}) => {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<any>();
  const { user } = useAuth();
  const { language, setLanguage } = useLanguage();

  const villageDisplayName = user?.villageName
    ? (language === 'kn'
        ? (user.villageNameKn || user.villageName)
        : user.villageName)
    : 'Ujire';

  const isKn = language === 'kn';

  const getRoleLabel = () => {
    switch (user?.role) {
      case 'expert':
        return isKn ? 'ಕೃಷಿ ತಜ್ಞ' : 'Agri Expert';
      case 'officer':
        return isKn ? 'ಕೃಷಿ ಅಧಿಕಾರಿ' : 'Govt Officer';
      case 'buyer':
        return isKn ? 'ಖರೀದಿದಾರ' : 'Buyer / Trader';
      case 'community':
      case 'village_node':
        return isKn ? 'ಗ್ರಾಮ ಸಮುದಾಯ' : 'Community Node';
      case 'farmer':
      default:
        return isKn ? 'ಬೆಳೆಗಾರ / ರೈತ' : 'Farmer';
    }
  };

  return (
    <View style={[styles.wrapper, { paddingTop: Math.max(insets.top, 10) + Spacing.xs }]}>
      <View style={styles.topRow}>
        {/* Left: App Logo & Village Identity or Back Button */}
        {onBack ? (
          <View style={styles.backRow}>
            <TouchableOpacity
              activeOpacity={0.7}
              onPress={onBack}
              style={styles.backBtn}
            >
              <ArrowLeft size={20} color={Colors.textPrimary} />
            </TouchableOpacity>
            {title ? (
              <View style={styles.backTitleCol}>
                <Text style={styles.title}>{title}</Text>
                {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
              </View>
            ) : null}
          </View>
        ) : !title ? (
          <View style={styles.brandCol}>
            <View style={styles.logoRow}>
              <View style={styles.appLogoCircle}>
                <Sprout size={18} color="#FFFFFF" strokeWidth={2.4} />
              </View>
              <View>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                  <Text style={styles.appTitle}>
                    <Text style={{ color: '#166534' }}>Krushi</Text>
                    <Text style={{ color: '#16A34A' }}>Pragya</Text>
                  </Text>
                  <View style={styles.roleTagPill}>
                    <Text style={styles.roleTagText}>{getRoleLabel()}</Text>
                  </View>
                </View>
                <View style={styles.villageInline}>
                  <MapPin size={11} color={Colors.primary} />
                  <Text style={styles.villageText} numberOfLines={1}>
                    {villageDisplayName}
                  </Text>
                </View>
              </View>
            </View>
          </View>
        ) : (
          showVillage && (
            <View style={styles.villageContainer}>
              <MapPin size={14} color={Colors.primary} />
              <Text style={styles.villageText} numberOfLines={1}>
                {villageDisplayName}
              </Text>
            </View>
          )
        )}

        {/* Right: Language Pill & Profile Button */}
        <View style={styles.rightActionsRow}>
          {rightAction}

          {/* Language Switcher Pill */}
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => setLanguage(isKn ? 'en' : 'kn')}
            style={styles.langButton}
          >
            <Globe2 size={13} color={Colors.primaryDark} />
            <Text style={styles.langText}>
              {isKn ? 'English' : 'ಕನ್ನಡ'}
            </Text>
          </TouchableOpacity>

          {/* Profile Avatar Button */}
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => navigation.navigate('Profile')}
            style={styles.profileAvatarBtn}
          >
            <User size={16} color={Colors.primaryDark} strokeWidth={2.4} />
          </TouchableOpacity>
        </View>
      </View>

      {title && !onBack && (
        <View style={styles.titleContainer}>
          <View>
            <Text style={styles.title}>{title}</Text>
            {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
          </View>
          {rightAction}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    backgroundColor: Colors.background,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
    paddingBottom: 8,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.xs,
  },
  villageContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: Colors.surface,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: Colors.border,
    maxWidth: '55%',
  },
  villageText: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  rightActionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  langButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.primaryLight,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: '#BFE7D7',
  },
  langText: {
    fontSize: 11,
    fontWeight: '800',
    color: Colors.primaryDark,
  },
  profileAvatarBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.md,
    marginTop: Spacing.xs,
  },
  title: {
    ...Typography.title1,
    color: Colors.textPrimary,
  },
  brandCol: {
    flex: 1,
  },
  logoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  appLogoCircle: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#16A34A',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#16A34A',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 2,
  },
  appTitle: {
    fontSize: 16,
    fontWeight: '900',
    letterSpacing: 0.3,
    lineHeight: 18,
  },
  villageInline: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    marginTop: 2,
  },
  backRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  backTitleCol: {
    flex: 1,
  },
  subtitle: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 1,
  },
  roleTagPill: {
    backgroundColor: Colors.primaryLight,
    paddingHorizontal: 6,
    paddingVertical: 1.5,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: '#BFE7D7',
  },
  roleTagText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.primaryDark,
  },
});