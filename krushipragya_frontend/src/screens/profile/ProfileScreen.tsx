import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth, UserRole } from '../../context/AuthContext';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import {
  ArrowLeft,
  User,
  MapPin,
  Globe2,
  LogOut,
  Sparkles,
  Award,
  Sprout,
  Microscope,
  Landmark,
  Store,
  Users,
  CheckCircle2,
} from 'lucide-react-native';

import { CommonActions } from '@react-navigation/native';

interface ProfileScreenProps {
  navigation: any;
}

const ROLES_LIST: { role: UserRole; titleEn: string; titleKn: string; Icon: any; color: string }[] = [
  { role: 'farmer', titleEn: 'Farmer', titleKn: 'ಬೆಳೆಗಾರ / ರೈತ', Icon: Sprout, color: '#16A34A' },
  { role: 'expert', titleEn: 'Agri Expert', titleKn: 'ಕೃಷಿ ತಜ್ಞ / ವಿಜ್ಞಾನಿ', Icon: Microscope, color: '#2563EB' },
  { role: 'officer', titleEn: 'Govt Officer', titleKn: 'ಕೃಷಿ ಅಧಿಕಾರಿ', Icon: Landmark, color: '#9333EA' },
  { role: 'buyer', titleEn: 'Buyer / Trader', titleKn: 'ಖರೀದಿದಾರ / ವರ್ತಕ', Icon: Store, color: '#D97706' },
  { role: 'community', titleEn: 'Community / FPO', titleKn: 'ಗ್ರಾಮ ಸಮುದಾಯ & ಎಫ್‌ಪಿಒ', Icon: Users, color: '#0D9488' },
];

export const ProfileScreen: React.FC<ProfileScreenProps> = ({ navigation }) => {
  const { language, setLanguage } = useLanguage();
  const { user, setRole, logout } = useAuth();

  const isKn = language === 'kn';

  const handleBack = () => {
    if (navigation.canGoBack()) {
      navigation.goBack();
    } else {
      let rootNav = navigation;
      while (rootNav.getParent()) {
        rootNav = rootNav.getParent();
      }
      try {
        rootNav.dispatch(
          CommonActions.reset({
            index: 0,
            routes: [{ name: 'MainTabs' }],
          })
        );
      } catch {
        navigation.navigate('MainTabs');
      }
    }
  };

  const handleSelectRole = (newRole: UserRole) => {
    setRole(newRole);
    // Profile role selection → immediately reset and navigate to the selected role's dashboard
    let rootNav = navigation;
    while (rootNav.getParent()) {
      rootNav = rootNav.getParent();
    }
    try {
      rootNav.dispatch(
        CommonActions.reset({
          index: 0,
          routes: [{ name: 'MainTabs' }],
        })
      );
    } catch {
      if (navigation.canGoBack()) {
        navigation.goBack();
      } else {
        navigation.navigate('MainTabs');
      }
    }
  };

  const handleLogout = () => {
    Alert.alert(
      isKn ? 'ಲಾಗ್‌ಔಟ್' : 'Logout',
      isKn ? 'ನೀವು ಖಾತೆಯಿಂದ ಲಾಗ್‌ಔಟ್ ಮಾಡಲು ಬಯಸುವಿರಾ?' : 'Are you sure you want to logout and change role?',
      [
        { text: isKn ? 'ರದ್ದುಮಾಡಿ' : 'Cancel', style: 'cancel' },
        {
          text: isKn ? 'ಹೌದು, ಲಾಗ್‌ಔಟ್' : 'Logout',
          style: 'destructive',
          onPress: () => {
            logout();
          },
        },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        {/* Top Header */}
        <View style={styles.topBar}>
          <TouchableOpacity
            activeOpacity={0.7}
            onPress={handleBack}
            style={styles.backButton}
          >
            <ArrowLeft size={20} color={Colors.textPrimary} />
          </TouchableOpacity>

          <Text style={styles.headerTitle}>
            {isKn ? 'ನನ್ನ ಪ್ರೊಫೈಲ್' : 'My Profile & Persona'}
          </Text>

          <View style={{ width: 36 }} />
        </View>

        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          {/* User Profile Card */}
          <View style={styles.profileCard}>
            <View style={styles.profileRow}>
              <View style={styles.avatarCircle}>
                <User size={30} color={Colors.primary} />
              </View>

              <View style={styles.profileTextCol}>
                <Text style={styles.farmerName}>
                  {isKn && user?.nameKn ? user.nameKn : (user?.name || (isKn ? 'ರೈತರು' : 'Farmer'))}
                </Text>
                <Text style={styles.phoneNumber}>{user?.phone || '+91 98765 43210'}</Text>
                <View style={styles.villageLocationRow}>
                  <MapPin size={12} color={Colors.primary} />
                  <Text style={styles.villageLocationText}>
                    {user?.villageName || 'Ujire'} • {user?.roleTitleEn || 'Farmer'}
                  </Text>
                </View>
              </View>
            </View>

            <View style={styles.verifiedTag}>
              <Award size={14} color="#15803D" />
              <Text style={styles.verifiedTagText}>
                {isKn ? 'ಧೃಢೀಕರಿಸಲ್ಪಟ್ಟ ಕೃಷಿಪ್ರಜ್ಞಾ ಬಳಕೆದಾರ' : 'Verified KrushiPragya Stakeholder'}
              </Text>
            </View>
          </View>

          {/* Switch Active Role */}
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>
              {isKn ? 'ಪಾತ್ರ ಬದಲಾಯಿಸಿ' : 'Switch Active Role'}
            </Text>
          </View>

          <View style={styles.roleSelectionBox}>
            {ROLES_LIST.map((item) => {
              const isSelected = user?.role === item.role;
              const { Icon, color, titleEn, titleKn } = item;

              return (
                <TouchableOpacity
                  key={item.role}
                  activeOpacity={0.8}
                  onPress={() => handleSelectRole(item.role)}
                  style={[
                    styles.roleItem,
                    isSelected && { borderColor: color, borderWidth: 1.5, backgroundColor: '#F8FAFC' },
                  ]}
                >
                  <View style={[styles.roleIconBox, { backgroundColor: `${color}15` }]}>
                    <Icon size={16} color={color} strokeWidth={2.4} />
                  </View>
                  <Text style={[styles.roleLabel, isSelected && { color: color, fontWeight: '800' }]}>
                    {isKn ? titleKn : titleEn}
                  </Text>
                  {isSelected && <CheckCircle2 size={16} color={color} strokeWidth={2.4} />}
                </TouchableOpacity>
              );
            })}
          </View>

          {/* Language Preference */}
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>
              {isKn ? 'ಭಾಷಾ ಆದ್ಯತೆ' : 'Language Preference'}
            </Text>
          </View>

          <View style={styles.langBox}>
            <TouchableOpacity
              activeOpacity={0.8}
              onPress={() => setLanguage('kn')}
              style={[styles.langChoice, isKn && styles.activeLangChoice]}
            >
              <Text style={[styles.langChoiceText, isKn && styles.activeLangText]}>
                ಕನ್ನಡ (Kannada)
              </Text>
              {isKn && <CheckCircle2 size={16} color="#16A34A" />}
            </TouchableOpacity>

            <TouchableOpacity
              activeOpacity={0.8}
              onPress={() => setLanguage('en')}
              style={[styles.langChoice, !isKn && styles.activeLangChoice]}
            >
              <Text style={[styles.langChoiceText, !isKn && styles.activeLangText]}>
                English
              </Text>
              {!isKn && <CheckCircle2 size={16} color="#16A34A" />}
            </TouchableOpacity>
          </View>

          {/* Logout Button */}
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={handleLogout}
            style={styles.logoutBtn}
          >
            <LogOut size={16} color="#DC2626" />
            <Text style={styles.logoutBtnText}>
              {isKn ? 'ಲಾಗ್‌ಔಟ್ ಮಾಡಿ & ಪಾತ್ರ ಆಯ್ಕೆಮಾಡಿ' : 'Logout & Choose Role'}
            </Text>
          </TouchableOpacity>
        </ScrollView>
      </View>
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
    backgroundColor: '#F8FAFC',
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  backButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  scrollContent: {
    padding: Spacing.md,
    paddingBottom: 40,
  },
  profileCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 16,
    marginBottom: Spacing.md,
  },
  profileRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatarCircle: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#DCFCE7',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: '#86EFAC',
  },
  profileTextCol: {
    flex: 1,
  },
  farmerName: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  phoneNumber: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 1,
  },
  villageLocationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 3,
  },
  villageLocationText: {
    fontSize: 12,
    color: '#475569',
    fontWeight: '600',
  },
  verifiedTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#DCFCE7',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginTop: 12,
  },
  verifiedTagText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#15803D',
  },
  sectionHeader: {
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#1E293B',
  },
  roleSelectionBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 8,
    gap: 6,
    marginBottom: Spacing.md,
  },
  roleItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'transparent',
    gap: 10,
  },
  roleIconBox: {
    width: 32,
    height: 32,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  roleLabel: {
    flex: 1,
    fontSize: 13,
    fontWeight: '600',
    color: '#334155',
  },
  langBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 8,
    gap: 6,
    marginBottom: Spacing.lg,
  },
  langChoice: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
  },
  activeLangChoice: {
    backgroundColor: '#F0FDF4',
  },
  langChoiceText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#334155',
  },
  activeLangText: {
    color: '#16A34A',
    fontWeight: '800',
  },
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FCA5A5',
    paddingVertical: 12,
    borderRadius: 10,
  },
  logoutBtnText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#DC2626',
  },
});