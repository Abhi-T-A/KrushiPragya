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
import { useAuth } from '../../context/AuthContext';
import { useReports } from '../../context/ReportContext';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import {
  ArrowLeft,
  User,
  MapPin,
  Trees,
  Sprout,
  ShieldCheck,
  Globe2,
  FileText,
  Info,
  LogOut,
  ChevronRight,
  Sparkles,
  Award,
} from 'lucide-react-native';

interface ProfileScreenProps {
  navigation: any;
}

export const ProfileScreen: React.FC<ProfileScreenProps> = ({ navigation }) => {
  const { language, setLanguage } = useLanguage();
  const { user, logout } = useAuth();
  const { reports } = useReports();

  const handleLogout = () => {
    Alert.alert(
      language === 'kn' ? 'ಲಾಗ್‌ಔಟ್' : 'Logout',
      language === 'kn'
        ? 'ನೀವು ಖಾತೆಯಿಂದ ನಿರ್ಗಮಿಸಲು ಖಚಿತವಾಗಿ ಬಯಸುವಿರಾ?'
        : 'Are you sure you want to logout?',
      [
        { text: language === 'kn' ? 'ರದ್ದುಮಾಡಿ' : 'Cancel', style: 'cancel' },
        { text: language === 'kn' ? 'ಹೌದು, ಲಾಗ್‌ಔಟ್' : 'Logout', style: 'destructive', onPress: () => logout() },
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
            onPress={() => navigation.goBack()}
            style={styles.backButton}
          >
            <ArrowLeft size={22} color={Colors.textPrimary} />
          </TouchableOpacity>

          <Text style={styles.headerTitle}>
            {language === 'kn' ? 'ನನ್ನ ಪ್ರೊಫೈಲ್' : 'My Profile'}
          </Text>

          <View style={{ width: 40 }} />
        </View>

        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          {/* Farmer Info Hero Card */}
          <Card variant="trust" style={styles.profileHeroCard}>
            <View style={styles.profileRow}>
              <View style={styles.avatarCircle}>
                <User size={36} color={Colors.primary} />
              </View>

              <View style={styles.profileTextCol}>
                <Text style={styles.farmerName}>{user?.name || 'ಅಭಿ ಗೌಡ'}</Text>
                <Text style={styles.phoneNumber}>{user?.phone || '+91 98765 43210'}</Text>
                <View style={styles.villageLocationRow}>
                  <MapPin size={13} color={Colors.primary} />
                  <Text style={styles.villageLocationText}>
                    {user?.villageName || 'Ujire'} · {user?.farmSizeAcres || '2.5'} {language === 'kn' ? 'ಎಕರೆ' : 'Acres'}
                  </Text>
                </View>
              </View>
            </View>

            {/* Progressive Farmer Trust Tag */}
            <View style={styles.progressiveBadge}>
              <Award size={16} color={Colors.primaryDark} />
              <Text style={styles.progressiveBadgeText}>
                {language === 'kn'
                  ? 'ದೃಢೀಕೃತ ಪ್ರಗತಿಪರ ರೈತ (Verified Farmer)'
                  : 'Verified Progressive Farmer'}
              </Text>
            </View>
          </Card>

          {/* Registered Crops Overview */}
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>
              {language === 'kn' ? 'ನೋಂದಾಯಿತ ಬೆಳೆಗಳು' : 'Registered Crops'}
            </Text>
          </View>

          <Card style={styles.cropsCard}>
            <View style={styles.cropItemRow}>
              <Text style={styles.cropEmoji}>🌴</Text>
              <View style={styles.cropInfoCol}>
                <Text style={styles.cropTitle}>{language === 'kn' ? 'ಅಡಿಕೆ (Arecanut)' : 'Arecanut'}</Text>
                <Text style={styles.cropSubtitle}>2.0 {language === 'kn' ? 'ಎಕರೆ' : 'Acres'} · {language === 'kn' ? 'ಮುಖ್ಯ ಬೆಳೆ' : 'Main Crop'}</Text>
              </View>
              <View style={styles.healthyBadge}>
                <Text style={styles.healthyBadgeText}>● {language === 'kn' ? 'ಆರೋಗ್ಯಕರ' : 'Healthy'}</Text>
              </View>
            </View>

            <View style={styles.divider} />

            <View style={styles.cropItemRow}>
              <Text style={styles.cropEmoji}>🌾</Text>
              <View style={styles.cropInfoCol}>
                <Text style={styles.cropTitle}>{language === 'kn' ? 'ಭತ್ತ (Paddy)' : 'Paddy'}</Text>
                <Text style={styles.cropSubtitle}>0.5 {language === 'kn' ? 'ಎಕರೆ' : 'Acres'}</Text>
              </View>
              <View style={[styles.healthyBadge, { backgroundColor: Colors.aiAnalysedBg }]}>
                <Text style={[styles.healthyBadgeText, { color: Colors.aiAnalysed }]}>● {language === 'kn' ? 'ಗಮನ ಅಗತ್ಯ' : 'Monitoring'}</Text>
              </View>
            </View>
          </Card>

          {/* Profile Actions & Settings Menu */}
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>
              {language === 'kn' ? 'ಸೆಟ್ಟಿಂಗ್ಸ್ ಮತ್ತು ವಿವರ' : 'Settings & Options'}
            </Text>
          </View>

          <Card style={styles.menuCard}>
            {/* Language Toggle */}
            <TouchableOpacity
              activeOpacity={0.7}
              onPress={() => setLanguage(language === 'kn' ? 'en' : 'kn')}
              style={styles.menuItem}
            >
              <View style={[styles.menuIconBg, { backgroundColor: Colors.primaryLight }]}>
                <Globe2 size={18} color={Colors.primary} />
              </View>
              <View style={styles.menuTextCol}>
                <Text style={styles.menuTitle}>{language === 'kn' ? 'ಭಾಷೆ (Language)' : 'App Language'}</Text>
                <Text style={styles.menuSubtitle}>{language === 'kn' ? 'ಪ್ರಸ್ತುತ: ಕನ್ನಡ' : 'Current: English'}</Text>
              </View>
              <ChevronRight size={18} color={Colors.textMuted} />
            </TouchableOpacity>

            <View style={styles.divider} />

            {/* My Past Reports */}
            <TouchableOpacity
              activeOpacity={0.7}
              onPress={() => navigation.navigate('HistoryTab')}
              style={styles.menuItem}
            >
              <View style={[styles.menuIconBg, { backgroundColor: '#FEF3C7' }]}>
                <FileText size={18} color={Colors.accentGold} />
              </View>
              <View style={styles.menuTextCol}>
                <Text style={styles.menuTitle}>{language === 'kn' ? 'ನನ್ನ ಬೆಳೆ ವರದಿಗಳು' : 'My Crop Reports'}</Text>
                <Text style={styles.menuSubtitle}>{reports.length} {language === 'kn' ? 'ವರದಿಗಳು ದಾಖಲಾಗಿವೆ' : 'reports recorded'}</Text>
              </View>
              <ChevronRight size={18} color={Colors.textMuted} />
            </TouchableOpacity>

            <View style={styles.divider} />

            {/* About KrushiPragya */}
            <TouchableOpacity
              activeOpacity={0.7}
              onPress={() =>
                Alert.alert(
                  'KrushiPragya (ಕೃಷಿಪ್ರಜ್ಞಾ)',
                  'AI-Powered Agriculture Platform for Coastal & Malnad Karnataka.\nVersion 1.0.0 (SDMIT Innovate-A-Thon 2026)'
                )
              }
              style={styles.menuItem}
            >
              <View style={[styles.menuIconBg, { backgroundColor: Colors.trustPurpleLight }]}>
                <Info size={18} color={Colors.trustPurple} />
              </View>
              <View style={styles.menuTextCol}>
                <Text style={styles.menuTitle}>{language === 'kn' ? 'ಕೃಷಿಪ್ರಜ್ಞಾ ಬಗ್ಗೆ' : 'About KrushiPragya'}</Text>
                <Text style={styles.menuSubtitle}>v1.0.0 (Coastal & Malnad Network)</Text>
              </View>
              <ChevronRight size={18} color={Colors.textMuted} />
            </TouchableOpacity>
          </Card>

          {/* Logout Button */}
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={handleLogout}
            style={styles.logoutButton}
          >
            <LogOut size={18} color={Colors.alertHigh} />
            <Text style={styles.logoutButtonText}>
              {language === 'kn' ? 'ಖಾತೆಯಿಂದ ನಿರ್ಗಮಿಸಿ (Logout)' : 'Logout'}
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
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
    backgroundColor: Colors.background,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  headerTitle: {
    ...Typography.title1,
    fontSize: 20,
    color: Colors.textPrimary,
    fontWeight: '800',
  },
  scrollContent: {
    padding: Spacing.lg,
    paddingBottom: Spacing.xxxl,
    gap: Spacing.md,
  },
  profileHeroCard: {
    backgroundColor: Colors.surface,
    padding: Spacing.lg,
    borderRadius: BorderRadius.xl,
  },
  profileRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
  },
  avatarCircle: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: Colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#BFE7D7',
  },
  profileTextCol: {
    flex: 1,
    gap: 2,
  },
  farmerName: {
    ...Typography.title1,
    fontSize: 22,
    color: Colors.textPrimary,
    fontWeight: '800',
  },
  phoneNumber: {
    ...Typography.caption,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  villageLocationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 2,
  },
  villageLocationText: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.primaryDark,
  },
  progressiveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: Colors.primaryLight,
    paddingHorizontal: Spacing.md,
    paddingVertical: 8,
    borderRadius: BorderRadius.md,
    marginTop: Spacing.md,
    borderWidth: 1,
    borderColor: '#BFE7D7',
  },
  progressiveBadgeText: {
    ...Typography.caption,
    fontWeight: '800',
    color: Colors.primaryDark,
  },
  sectionHeader: {
    marginTop: Spacing.xs,
    marginBottom: -4,
  },
  sectionTitle: {
    ...Typography.title2,
    fontSize: 16,
    color: Colors.textPrimary,
    fontWeight: '800',
  },
  cropsCard: {
    padding: Spacing.md,
    gap: Spacing.sm,
  },
  cropItemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
  },
  cropEmoji: {
    fontSize: 28,
  },
  cropInfoCol: {
    flex: 1,
  },
  cropTitle: {
    ...Typography.bodyLarge,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  cropSubtitle: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 1,
  },
  healthyBadge: {
    backgroundColor: Colors.expertVerifiedBg,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
  },
  healthyBadgeText: {
    fontSize: 11,
    fontWeight: '800',
    color: Colors.expertVerified,
  },
  divider: {
    height: 1,
    backgroundColor: Colors.border,
    marginVertical: 4,
  },
  menuCard: {
    padding: Spacing.xs,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: Spacing.sm + 2,
    gap: Spacing.md,
  },
  menuIconBg: {
    width: 38,
    height: 38,
    borderRadius: BorderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuTextCol: {
    flex: 1,
  },
  menuTitle: {
    ...Typography.bodyLarge,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  menuSubtitle: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 1,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.alertHighBg,
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.lg,
    borderWidth: 1.5,
    borderColor: '#FECDD3',
    marginTop: Spacing.xs,
  },
  logoutButtonText: {
    ...Typography.bodyLarge,
    color: Colors.alertHigh,
    fontWeight: '800',
  },
});
