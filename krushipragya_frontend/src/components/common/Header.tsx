import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { MapPin, Globe2, User } from 'lucide-react-native';

export const Header: React.FC<{ title?: string; showVillage?: boolean }> = ({
  title,
  showVillage = true,
}) => {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<any>();
  const { user } = useAuth();
  const { language, setLanguage } = useLanguage();

  const villageDisplayName = user?.villageName
    ? (language === 'kn'
        ? user.villageName.replace(/\(.*?\)/g, '').trim()
        : (user.villageName.includes('(')
            ? user.villageName.match(/\((.*?)\)/)?.[1] || user.villageName
            : user.villageName))
    : 'Ujire';

  return (
    <View style={[styles.container, { paddingTop: Math.max(insets.top, 12) + Spacing.xs }]}>
      <View style={styles.topRow}>
        {/* Clean Location Badge */}
        {showVillage && (
          <View style={styles.villageContainer}>
            <MapPin size={15} color={Colors.primary} />
            <Text style={styles.villageText} numberOfLines={1}>
              {villageDisplayName}
            </Text>
          </View>
        )}

        <View style={styles.rightActionsRow}>
          {/* Language Switcher Pill */}
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => setLanguage(language === 'kn' ? 'en' : 'kn')}
            style={styles.langButton}
          >
            <Globe2 size={13} color={Colors.primaryDark} />
            <Text style={styles.langText}>
              {language === 'kn' ? 'English' : 'ಕನ್ನಡ'}
            </Text>
          </TouchableOpacity>

          {/* 1-Tap Farmer Profile Avatar */}
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => navigation.navigate('Profile')}
            style={styles.profileAvatarBtn}
          >
            <User size={18} color={Colors.primaryDark} strokeWidth={2.4} />
          </TouchableOpacity>
        </View>
      </View>

      {title && <Text style={styles.title}>{title}</Text>}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: Spacing.lg,
    paddingBottom: Spacing.sm,
    backgroundColor: Colors.background,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  villageContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: Colors.surface,
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    borderWidth: 1.5,
    borderColor: Colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 2,
    elevation: 1,
    maxWidth: '55%',
  },
  villageText: {
    ...Typography.label,
    fontSize: 13,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  rightActionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  langButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: Colors.primaryLight,
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    borderWidth: 1.5,
    borderColor: '#BFE7D7',
  },
  langText: {
    ...Typography.label,
    fontSize: 12,
    fontWeight: '800',
    color: Colors.primaryDark,
  },
  profileAvatarBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 2,
    elevation: 2,
  },
  title: {
    ...Typography.title1,
    color: Colors.textPrimary,
    marginTop: Spacing.xs,
  },
});
