import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { MapPin, Globe2, User } from 'lucide-react-native';

export const Header: React.FC<{
  title?: string;
  showVillage?: boolean;
}> = ({
  title,
  showVillage = true,
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

  return (
    <View style={[styles.wrapper, { paddingTop: Math.max(insets.top, 10) + Spacing.xs }]}>
      <View style={styles.topRow}>
        {/* Clean Location Badge */}
        {showVillage && (
          <View style={styles.villageContainer}>
            <MapPin size={14} color={Colors.primary} />
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

          {/* Profile Avatar / Role Tag */}
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => navigation.navigate('Profile')}
            style={styles.profileAvatarBtn}
          >
            <User size={16} color={Colors.primaryDark} strokeWidth={2.4} />
          </TouchableOpacity>
        </View>
      </View>

      {title && <Text style={styles.title}>{title}</Text>}
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
  title: {
    ...Typography.title1,
    color: Colors.textPrimary,
    paddingHorizontal: Spacing.md,
    marginTop: Spacing.xs,
  },
});