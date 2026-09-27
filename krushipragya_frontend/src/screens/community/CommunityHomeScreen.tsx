import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  fetchCommunityStats,
  fetchLocalReports,
  fetchCommunityAlerts,
  fetchMyContributions,
  CommunityDashboardStats,
  LocalCropIssueReport,
  CommunityAlertItem,
  CommunityContributionItem,
} from '../../services/communityApi';
import {
  Users,
  MapPin,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  ChevronRight,
  ShieldCheck,
  Send,
  CloudRain,
  Eye,
  Plus,
  Globe2,
  User,
  Layers,
  HeartHandshake,
} from 'lucide-react-native';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface CommunityHomeScreenProps {
  navigation: any;
}

export const CommunityHomeScreen: React.FC<CommunityHomeScreenProps> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { language, setLanguage } = useLanguage();
  const { user } = useAuth();
  const isKn = language === 'kn';

  const [stats, setStats] = useState<CommunityDashboardStats | null>(null);
  const [reports, setReports] = useState<LocalCropIssueReport[]>([]);
  const [alerts, setAlerts] = useState<CommunityAlertItem[]>([]);
  const [contributions, setContributions] = useState<CommunityContributionItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [statsData, reportsData, alertsData, contribsData] = await Promise.all([
        fetchCommunityStats(),
        fetchLocalReports(),
        fetchCommunityAlerts(),
        fetchMyContributions(),
      ]);
      setStats(statsData);
      setReports(reportsData);
      setAlerts(alertsData);
      setContributions(contribsData);
    } catch (e) {
      console.warn('Failed to load community dashboard data:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const topNearbyIssue = reports[0];
  const weatherAlert = alerts.find((a) => a.category === 'WEATHER') || alerts[2];

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* ============================================================== */}
      {/* 1. Header (Section 2) */}
      {/* ============================================================== */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.iconCircle}>
            <Users size={22} color="#16A34A" />
          </View>
          <View>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
              <Text style={styles.appName}>
                <Text style={{ color: '#166534' }}>Krushi</Text>
                <Text style={{ color: '#16A34A' }}>Pragya</Text>
              </Text>
              <View style={styles.villageTag}>
                <Text style={styles.villageTagText}>Village Node</Text>
              </View>
            </View>
            <Text style={styles.headerTitle}>
              {isKn ? 'ಗ್ರಾಮ ಸಮುದಾಯ ಸದಸ್ಯ' : 'Community Member'}
            </Text>
            <Text style={styles.headerSub}>
              📍 {user?.villageName || (isKn ? 'ಉಜಿರೆ ಗ್ರಾಮ' : 'Ujire Village')} • {isKn ? 'ದಕ್ಷಿಣ ಕನ್ನಡ' : 'Dakshina Kannada'}
            </Text>
          </View>
        </View>

        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.langBtn}
            onPress={() => setLanguage(isKn ? 'en' : 'kn')}
            activeOpacity={0.7}
          >
            <Globe2 size={13} color="#0F6E56" />
            <Text style={styles.langBtnText}>{isKn ? 'English' : 'ಕನ್ನಡ'}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.profileAvatar}
            onPress={() => navigation.navigate('Profile')}
            activeOpacity={0.8}
          >
            <User size={18} color="#0F6E56" />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#0F6E56']} />}
      >
        {/* ============================================================== */}
        {/* 2. Dashboard Summary: 4 Cards (Section 2) */}
        {/* ============================================================== */}
        <View style={styles.summaryGrid}>
          {/* Card 1: Local Reports */}
          <View style={[styles.metricCard, { borderLeftColor: '#0D9488' }]}>
            <View style={styles.metricTop}>
              <Text style={styles.metricNum}>{stats?.local_reports_count ?? 12}</Text>
              <View style={[styles.metricIconWrap, { backgroundColor: '#CCFBF1' }]}>
                <Eye size={16} color="#0D9488" />
              </View>
            </View>
            <Text style={styles.metricLabel}>{isKn ? 'ಸ್ಥಳೀಯ ವರದಿಗಳು' : 'Local Reports'}</Text>
            <Text style={styles.metricSub}>{isKn ? 'ಗ್ರಾಮ ವ್ಯಾಪ್ತಿ' : 'Village Cluster'}</Text>
          </View>

          {/* Card 2: My Reports */}
          <View style={[styles.metricCard, { borderLeftColor: '#2563EB' }]}>
            <View style={styles.metricTop}>
              <Text style={[styles.metricNum, { color: '#2563EB' }]}>{stats?.my_reports_count ?? 8}</Text>
              <View style={[styles.metricIconWrap, { backgroundColor: '#DBEAFE' }]}>
                <Send size={16} color="#2563EB" />
              </View>
            </View>
            <Text style={styles.metricLabel}>{isKn ? 'ನನ್ನ ವೀಕ್ಷಣೆಗಳು' : 'My Reports'}</Text>
            <Text style={styles.metricSub}>{isKn ? 'ದಾಖಲಿಸಿದ ವರದಿ' : 'Observations'}</Text>
          </View>

          {/* Card 3: Confirmed */}
          <View style={[styles.metricCard, { borderLeftColor: '#16A34A' }]}>
            <View style={styles.metricTop}>
              <Text style={[styles.metricNum, { color: '#16A34A' }]}>{stats?.confirmed_count ?? 5}</Text>
              <View style={[styles.metricIconWrap, { backgroundColor: '#DCFCE7' }]}>
                <CheckCircle2 size={16} color="#16A34A" />
              </View>
            </View>
            <Text style={styles.metricLabel}>{isKn ? 'ದೃಢೀಕೃತ ಸಮಸ್ಯೆಗಳು' : 'Confirmed'}</Text>
            <Text style={styles.metricSub}>{isKn ? 'ತಜ್ಞರ ಪರಿಶೀಲನೆ' : 'Expert Verified'}</Text>
          </View>

          {/* Card 4: Alerts */}
          <View style={[styles.metricCard, { borderLeftColor: '#DC2626' }]}>
            <View style={styles.metricTop}>
              <Text style={[styles.metricNum, { color: '#DC2626' }]}>{stats?.alerts_count ?? 3}</Text>
              <View style={[styles.metricIconWrap, { backgroundColor: '#FEE2E2' }]}>
                <AlertTriangle size={16} color="#DC2626" />
              </View>
            </View>
            <Text style={styles.metricLabel}>{isKn ? 'ಕೃಷಿ ಎಚ್ಚರಿಕೆಗಳು' : 'Active Alerts'}</Text>
            <Text style={styles.metricSub}>{isKn ? 'ತುರ್ತು ಸೂಚನೆ' : 'Broadcasts'}</Text>
          </View>
        </View>

        {/* ============================================================== */}
        {/* 3. Core Role Purpose Banner: "CORROBORATE" */}
        {/* ============================================================== */}
        <View style={styles.purposeBanner}>
          <View style={styles.purposeHeader}>
            <HeartHandshake size={16} color="#0D9488" />
            <Text style={styles.purposeTitle}>
              {isKn ? 'ಸಮುದಾಯದ ಪಾತ್ರ: ಸಾಕ್ಷ್ಯಾಧಾರ ದೃಢೀಕರಣ (CORROBORATE)' : 'Community Role: CORROBORATE'}
            </Text>
          </View>
          <Text style={styles.purposeDesc}>
            {isKn
              ? 'ರೈತರು = ಕ್ರಮ (Act) • ತಜ್ಞರು = ಪರಿಶೀಲನೆ (Verify) • ಸರ್ಕಾರ = ಸೌಲಭ್ಯ (Enable) • ಖರೀದಿದಾರ = ವ್ಯಾಪಾರ (Trade) • ಸಮುದಾಯ = ಸಾಕ್ಷ್ಯಾಧಾರ (Corroborate)'
              : 'Farmer = Act • Expert = Verify • Government = Enable • Buyer = Trade • Community = Corroborate'}
          </Text>
          <Text style={styles.purposeSubDesc}>
            {isKn
              ? 'ಸಮುದಾಯವು ರೋಗ ನಿರ್ಣಯ ಮಾಡುವುದಿಲ್ಲ. ಬದಲಿಗೆ "ನನಗೂ ಇದೇ ಸಮಸ್ಯೆ ಕಂಡಿದೆ" ಎಂದು ಸಾಕ್ಷ್ಯಾಧಾರ ಒದಗಿಸಿ ತಜ್ಞರಿಗೆ ನೆರವಾಗುತ್ತದೆ.'
              : 'Community members provide supporting field evidence ("I see similar symptoms") without diagnosing.'}
          </Text>
        </View>

        {/* ============================================================== */}
        {/* 4. Trust Ladder Visual (Section 15) */}
        {/* ============================================================== */}
        <View style={styles.trustLadderCard}>
          <View style={styles.trustLadderHeader}>
            <Layers size={15} color="#0D9488" />
            <Text style={styles.trustLadderTitle}>
              {isKn ? 'ಕೃಷಿಪ್ರಜ್ಞಾ ವಿಶ್ವಾಸಾರ್ಹತೆಯ ಹಂತಗಳು (Trust Ladder)' : 'KrushiPragya Trust Ladder'}
            </Text>
          </View>

          <View style={styles.ladderFlow}>
            <View style={styles.ladderStep}>
              <View style={styles.ladderDot}><Text style={styles.ladderDotNum}>1</Text></View>
              <Text style={styles.ladderLabel}>UNVERIFIED</Text>
              <Text style={styles.ladderSubLabel}>Farmer Observation</Text>
            </View>
            <Text style={styles.ladderArrow}>➔</Text>
            <View style={styles.ladderStep}>
              <View style={[styles.ladderDot, { backgroundColor: '#DBEAFE' }]}><Text style={[styles.ladderDotNum, { color: '#2563EB' }]}>2</Text></View>
              <Text style={styles.ladderLabel}>AI ANALYSED</Text>
              <Text style={styles.ladderSubLabel}>Deep Learning</Text>
            </View>
            <Text style={styles.ladderArrow}>➔</Text>
            <View style={styles.ladderStep}>
              <View style={[styles.ladderDot, { backgroundColor: '#CCFBF1' }]}><Text style={[styles.ladderDotNum, { color: '#0D9488' }]}>3</Text></View>
              <Text style={[styles.ladderLabel, { color: '#0D9488', fontWeight: '800' }]}>CORROBORATED</Text>
              <Text style={styles.ladderSubLabel}>Community (You)</Text>
            </View>
            <Text style={styles.ladderArrow}>➔</Text>
            <View style={styles.ladderStep}>
              <View style={[styles.ladderDot, { backgroundColor: '#DCFCE7' }]}><Text style={[styles.ladderDotNum, { color: '#16A34A' }]}>4</Text></View>
              <Text style={[styles.ladderLabel, { color: '#16A34A' }]}>EXPERT VERIFIED</Text>
              <Text style={styles.ladderSubLabel}>Clinical Review</Text>
            </View>
          </View>
        </View>

        {/* ============================================================== */}
        {/* 5. Village Agricultural Status (Section 14) */}
        {/* ============================================================== */}
        <View style={styles.villageStatusCard}>
          <View style={styles.villageStatusHeader}>
            <MapPin size={16} color="#0D9488" />
            <Text style={styles.villageStatusTitle}>
              {isKn ? 'ನಿಮ್ಮ ಗ್ರಾಮದ ಕೃಷಿ ಸ್ಥಿತಿ' : 'Village Agricultural Status'}
            </Text>
          </View>
          <Text style={styles.villageStatusSummary}>
            {isKn
              ? 'ಉಜಿರೆ ವ್ಯಾಪ್ತಿಯಲ್ಲಿ 7 ಸಕ್ರಿಯ ಬೆಳೆ ಸಮಸ್ಯೆಗಳು • 3 ಪ್ರಕರಣಗಳು ತಜ್ಞರಿಂದ ದೃಢೀಕೃತ'
              : '7 Active Crop Reports in Ujire Cluster • 3 Expert-Verified'}
          </Text>

          <TouchableOpacity
            style={styles.newReportBtn}
            onPress={() => navigation.navigate('CommunityReportsTab', { openSubmitModal: true })}
            activeOpacity={0.85}
          >
            <Plus size={15} color="#FFFFFF" strokeWidth={2.5} />
            <Text style={styles.newReportBtnText}>
              {isKn ? 'ಹೊಸ ಸ್ಥಳೀಯ ವೀಕ್ಷಣೆ ದಾಖಲಿಸಿ' : 'Submit Local Observation'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* ============================================================== */}
        {/* 6. Nearby Issue Needing Corroboration (Section 14) */}
        {/* ============================================================== */}
        {topNearbyIssue && (
          <View style={styles.nearbyIssueCard}>
            <View style={styles.nearbyIssueHeader}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                <Text style={styles.cropIcon}>{topNearbyIssue.crop_icon}</Text>
                <View>
                  <Text style={styles.issueCropName}>{topNearbyIssue.crop_name}</Text>
                  <Text style={styles.issueLocation}>📍 {topNearbyIssue.village} • {topNearbyIssue.distance_km} km away</Text>
                </View>
              </View>

              <View style={styles.corrobNeededBadge}>
                <Text style={styles.corrobNeededText}>
                  {topNearbyIssue.similar_reports_count} {isKn ? 'ರೈತರು ವರದಿ ಮಾಡಿದ್ದಾರೆ' : 'farmers reported'}
                </Text>
              </View>
            </View>

            <Text style={styles.issueDescription}>
              {isKn ? topNearbyIssue.observed_issue_kn : topNearbyIssue.observed_issue}
            </Text>

            <View style={styles.symptomsTagRow}>
              {topNearbyIssue.symptoms.map((s, idx) => (
                <View key={idx} style={styles.symptomPill}>
                  <Text style={styles.symptomPillText}>{s}</Text>
                </View>
              ))}
            </View>

            <TouchableOpacity
              style={styles.corroborateActionBtn}
              onPress={() => navigation.navigate('CommunityCorroborateTab', { reportId: topNearbyIssue.id })}
              activeOpacity={0.85}
            >
              <HeartHandshake size={15} color="#FFFFFF" />
              <Text style={styles.corroborateActionBtnText}>
                {isKn ? 'ನನಗೂ ಇದೇ ಸಮಸ್ಯೆ ಕಂಡಿದೆ (Corroborate)' : 'Corroborate This Issue'}
              </Text>
            </TouchableOpacity>
          </View>
        )}

        {/* ============================================================== */}
        {/* 7. Weather Advisory Card (Section 14) */}
        {/* ============================================================== */}
        {weatherAlert && (
          <View style={styles.weatherCard}>
            <View style={styles.weatherTop}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                <CloudRain size={18} color="#0284C7" />
                <Text style={styles.weatherTitle}>{weatherAlert.title}</Text>
              </View>
              <View style={styles.weatherBadge}>
                <Text style={styles.weatherBadgeText}>Advisory</Text>
              </View>
            </View>
            <Text style={styles.weatherMsg}>{weatherAlert.message}</Text>
            <TouchableOpacity
              style={styles.weatherLinkBtn}
              onPress={() => navigation.navigate('CommunityAlertsTab')}
            >
              <Text style={styles.weatherLinkText}>{isKn ? 'ಎಲ್ಲಾ ಸೂಚನೆಗಳನ್ನು ನೋಡಿ' : 'View Advisories'}</Text>
              <ChevronRight size={13} color="#0284C7" />
            </TouchableOpacity>
          </View>
        )}

        {/* ============================================================== */}
        {/* 8. Your Contribution Summary (Section 8 & 14) */}
        {/* ============================================================== */}
        <View style={styles.contributionCard}>
          <View style={styles.contribTopRow}>
            <Text style={styles.contribCardTitle}>
              {isKn ? 'ನನ್ನ ಕೊಡುಗೆಗಳು (My Contributions)' : 'Your Community Contributions'}
            </Text>
          </View>

          <View style={styles.contribMetricsRow}>
            <View style={styles.contribMetricCol}>
              <Text style={styles.contribNum}>8</Text>
              <Text style={styles.contribSub}>{isKn ? 'ದಾಖಲಿಸಿದ ವರದಿ' : 'Reports'}</Text>
            </View>
            <View style={styles.metricDivider} />
            <View style={styles.contribMetricCol}>
              <Text style={[styles.contribNum, { color: '#0D9488' }]}>17</Text>
              <Text style={styles.contribSub}>{isKn ? 'ದೃಢೀಕರಣಗಳು' : 'Corroborations'}</Text>
            </View>
            <View style={styles.metricDivider} />
            <View style={styles.contribMetricCol}>
              <Text style={[styles.contribNum, { color: '#16A34A' }]}>21</Text>
              <Text style={styles.contribSub}>{isKn ? 'ಸಹಾಯಕ ಮತಗಳು' : 'Helpful Votes'}</Text>
            </View>
          </View>

          <View style={styles.sampleContribItem}>
            <Text style={styles.sampleCropIcon}>🌴</Text>
            <View style={{ flex: 1 }}>
              <Text style={styles.sampleContribTitle}>
                {isKn ? 'ಅಡಿಕೆ ಕೊಳೆರೋಗ ಲಕ್ಷಣ ದೃಢೀಕರಣ' : 'Arecanut Koleroga Observation'}
              </Text>
              <Text style={styles.sampleContribSub}>
                📍 Ujire • Status: ✓ Used as corroboration • Expert: Verified
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  iconCircle: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: '#CCFBF1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  appName: {
    fontSize: 16,
    fontWeight: '900',
    letterSpacing: 0.3,
  },
  villageTag: {
    backgroundColor: '#CCFBF1',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 4,
  },
  villageTagText: {
    fontSize: 9.5,
    fontWeight: '800',
    color: '#0D9488',
  },
  headerTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
  },
  headerSub: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '500',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  langBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#E1F5EE',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: '#BFE7D7',
  },
  langBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#0F6E56',
  },
  profileAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#E1F5EE',
    borderWidth: 1.5,
    borderColor: '#0F6E56',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 36,
    gap: 14,
  },
  summaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  metricCard: {
    width: (SCREEN_WIDTH - 42) / 2,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 12,
    borderLeftWidth: 4,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
  },
  metricTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  metricNum: {
    fontSize: 22,
    fontWeight: '900',
    color: '#0F172A',
  },
  metricIconWrap: {
    width: 28,
    height: 28,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  metricLabel: {
    fontSize: 12,
    fontWeight: '800',
    color: '#1E293B',
  },
  metricSub: {
    fontSize: 10.5,
    color: '#64748B',
    marginTop: 1,
  },
  purposeBanner: {
    backgroundColor: '#F0FDFA',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#99F6E4',
    padding: 12,
    gap: 4,
  },
  purposeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  purposeTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0F766E',
  },
  purposeDesc: {
    fontSize: 11.5,
    fontWeight: '700',
    color: '#115E59',
  },
  purposeSubDesc: {
    fontSize: 11,
    color: '#134E4A',
    lineHeight: 16,
  },
  trustLadderCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  trustLadderHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 10,
  },
  trustLadderTitle: {
    fontSize: 12.5,
    fontWeight: '800',
    color: '#0F172A',
  },
  ladderFlow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  ladderStep: {
    alignItems: 'center',
    flex: 1,
  },
  ladderDot: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  ladderDotNum: {
    fontSize: 11,
    fontWeight: '800',
    color: '#475569',
  },
  ladderLabel: {
    fontSize: 9,
    fontWeight: '700',
    color: '#475569',
    textAlign: 'center',
  },
  ladderSubLabel: {
    fontSize: 8,
    color: '#94A3B8',
    textAlign: 'center',
  },
  ladderArrow: {
    fontSize: 11,
    color: '#CBD5E1',
    marginBottom: 10,
  },
  villageStatusCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 8,
  },
  villageStatusHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  villageStatusTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#0F172A',
  },
  villageStatusSummary: {
    fontSize: 12,
    color: '#475569',
    lineHeight: 17,
  },
  newReportBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#0D9488',
    paddingVertical: 10,
    borderRadius: 8,
    marginTop: 4,
  },
  newReportBtnText: {
    fontSize: 12.5,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  nearbyIssueCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 8,
  },
  nearbyIssueHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  cropIcon: {
    fontSize: 22,
  },
  issueCropName: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
  },
  issueLocation: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
  },
  corrobNeededBadge: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  corrobNeededText: {
    fontSize: 10.5,
    fontWeight: '800',
    color: '#D97706',
  },
  issueDescription: {
    fontSize: 13,
    fontWeight: '700',
    color: '#334155',
  },
  symptomsTagRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  symptomPill: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  symptomPillText: {
    fontSize: 11,
    color: '#475569',
    fontWeight: '600',
  },
  corroborateActionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#0D9488',
    paddingVertical: 10,
    borderRadius: 8,
    marginTop: 4,
  },
  corroborateActionBtnText: {
    fontSize: 12.5,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  weatherCard: {
    backgroundColor: '#F0F9FF',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#BAE6FD',
    gap: 6,
  },
  weatherTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  weatherTitle: {
    fontSize: 12.5,
    fontWeight: '800',
    color: '#0369A1',
  },
  weatherBadge: {
    backgroundColor: '#E0F2FE',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  weatherBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#0284C7',
  },
  weatherMsg: {
    fontSize: 11.5,
    color: '#075985',
    lineHeight: 16,
  },
  weatherLinkBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    alignSelf: 'flex-start',
    marginTop: 2,
  },
  weatherLinkText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#0284C7',
  },
  contributionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 10,
  },
  contribTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  contribCardTitle: {
    fontSize: 13.5,
    fontWeight: '800',
    color: '#0F172A',
  },
  contribMetricsRow: {
    flexDirection: 'row',
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    padding: 10,
    justifyContent: 'space-around',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  contribMetricCol: {
    alignItems: 'center',
  },
  contribNum: {
    fontSize: 17,
    fontWeight: '900',
    color: '#0F172A',
  },
  contribSub: {
    fontSize: 10.5,
    color: '#64748B',
    marginTop: 1,
  },
  metricDivider: {
    width: 1,
    height: 24,
    backgroundColor: '#CBD5E1',
  },
  sampleContribItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F0FDFA',
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CCFBF1',
  },
  sampleCropIcon: {
    fontSize: 18,
  },
  sampleContribTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#0F766E',
  },
  sampleContribSub: {
    fontSize: 10.5,
    color: '#134E4A',
    marginTop: 2,
  },
});
