import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { useAuth, UserRole } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { Colors, Typography, BorderRadius, Spacing } from '../../constants/theme';
import {
  Sprout,
  Microscope,
  Landmark,
  Store,
  Users,
} from 'lucide-react-native';

interface RoleOption {
  key: UserRole;
  labelEn: string;
  labelKn: string;
  Icon: React.ComponentType<any>;
  color: string;
  activeBg: string;
}

const ROLES: RoleOption[] = [
  {
    key: 'farmer',
    labelEn: 'Farmer',
    labelKn: 'ರೈತ',
    Icon: Sprout,
    color: '#16A34A',
    activeBg: '#DCFCE7',
  },
  {
    key: 'expert',
    labelEn: 'Agri Expert',
    labelKn: 'ಕೃಷಿ ತಜ್ಞ',
    Icon: Microscope,
    color: '#2563EB',
    activeBg: '#DBEAFE',
  },
  {
    key: 'officer',
    labelEn: 'Govt Officer',
    labelKn: 'ಅಧಿಕಾರಿ',
    Icon: Landmark,
    color: '#9333EA',
    activeBg: '#F3E8FF',
  },
  {
    key: 'buyer',
    labelEn: 'Buyer / Trader',
    labelKn: 'ವರ್ತಕ',
    Icon: Store,
    color: '#D97706',
    activeBg: '#FEF3C7',
  },
  {
    key: 'community',
    labelEn: 'Community FPO',
    labelKn: 'ಸಮುದಾಯ',
    Icon: Users,
    color: '#0D9488',
    activeBg: '#CCFBF1',
  },
];

export const RoleSwitcher: React.FC = () => {
  const { user, setRole } = useAuth();
  const { language } = useLanguage();

  const currentRole = user?.role === 'village_node' ? 'community' : (user?.role || 'farmer');

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Text style={styles.headerLabel}>
          {language === 'kn' ? '⚡ ಲೈವ್ ಡೆಮೋ ಪಾತ್ರಗಳು (5 Users):' : '⚡ Live 5-User Demo Switcher:'}
        </Text>
        <Text style={styles.activeUserBadge}>
          {user?.name ? user.name.split('(')[0].trim() : 'Mallikarjuna'}
        </Text>
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {ROLES.map((role) => {
          const isActive = currentRole === role.key;
          const { Icon, color, activeBg, labelEn, labelKn } = role;

          return (
            <TouchableOpacity
              key={role.key}
              activeOpacity={0.8}
              onPress={() => setRole(role.key)}
              style={[
                styles.rolePill,
                isActive && {
                  backgroundColor: activeBg,
                  borderColor: color,
                  borderWidth: 1.5,
                },
              ]}
            >
              <View
                style={[
                  styles.iconCircle,
                  { backgroundColor: isActive ? color : '#E2E8F0' },
                ]}
              >
                <Icon size={14} color={isActive ? '#FFFFFF' : '#64748B'} strokeWidth={2.4} />
              </View>
              <Text
                style={[
                  styles.roleText,
                  isActive && { color: color, fontWeight: '800' },
                ]}
              >
                {language === 'kn' ? labelKn : labelEn}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
    paddingTop: 6,
    paddingBottom: 8,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    marginBottom: 6,
  },
  headerLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  activeUserBadge: {
    fontSize: 11,
    fontWeight: '700',
    color: '#1E293B',
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
  },
  scrollContent: {
    paddingHorizontal: Spacing.md,
    gap: 8,
  },
  rolePill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 20,
    paddingVertical: 6,
    paddingHorizontal: 10,
    gap: 6,
  },
  iconCircle: {
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
  },
  roleText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#475569',
  },
});