import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { MapPin, Globe2, UserCheck } from 'lucide-react-native';

export const Header: React.FC<{ title?: string; showVillage?: boolean }> = ({
  title,
  showVillage = true,
}) => {
  const { user, toggleRole } = useAuth();
  const { language, setLanguage, t } = useLanguage();

  return (
    <View style={styles.container}>
      <View style={styles.topRow}>
        {showVillage && user && (
          <View style={styles.villageContainer}>
            <MapPin size={16} color={Colors.primary} />
            <Text style={styles.villageText}>{user.villageName}</Text>
          </View>
        )}

        <View style={styles.actionsRow}>
          {/* Role Pill Switcher */}
          {user && (
            <TouchableOpacity
              onPress={toggleRole}
              style={[
                styles.roleBadge,
                user.role === 'village_node' && styles.villageNodeBadge,
              ]}
            >
              <UserCheck size={12} color={user.role === 'village_node' ? Colors.trustPurple : Colors.primaryDark} />
              <Text style={[styles.roleText, user.role === 'village_node' && { color: Colors.trustPurple }]}>
                {user.role === 'village_node' ? t.roleVillageNode : t.roleFarmer}
              </Text>
            </TouchableOpacity>
          )}

          {/* Bilingual Language Switcher */}
          <TouchableOpacity
            onPress={() => setLanguage(language === 'kn' ? 'en' : 'kn')}
            style={styles.langButton}
          >
            <Globe2 size={14} color={Colors.textPrimary} />
            <Text style={styles.langText}>
              {language === 'kn' ? 'EN' : 'ಕನ್ನಡ'}
            </Text>
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
    paddingTop: Spacing.md,
    paddingBottom: Spacing.sm,
    backgroundColor: Colors.background,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: Spacing.xs,
  },
  villageContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
    backgroundColor: Colors.surface,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  villageText: {
    ...Typography.label,
    color: Colors.textPrimary,
  },
  actionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  roleBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.primaryLight,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
  },
  villageNodeBadge: {
    backgroundColor: Colors.trustPurpleLight,
  },
  roleText: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.primaryDark,
  },
  langButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.surface,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  langText: {
    ...Typography.label,
    color: Colors.textPrimary,
  },
  title: {
    ...Typography.title1,
    color: Colors.textPrimary,
    marginTop: Spacing.xs,
  },
});
