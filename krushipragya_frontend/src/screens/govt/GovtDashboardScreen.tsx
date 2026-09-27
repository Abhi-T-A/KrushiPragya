import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
  RefreshControl,
  Modal,
  TextInput,
  Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  fetchGovernmentStats,
  fetchGovernmentApplications,
  fetchRegionalAgriculturalInsights,
  fetchGovernmentAlerts,
  publishGovernmentAlert,
  searchFarmersAssistance,
  GovernmentDashboardStats,
  SchemeApplicationItem,
  RegionalCropReportInsight,
  GovernmentOfficialAlert,
  FarmerAssistanceProfile,
} from '../../services/governmentApi';
import {
  Landmark,
  FileText,
  Users,
  Clock,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  Globe2,
  Send,
  Search,
  ChevronRight,
  ShieldAlert,
  Sparkles,
  MapPin,
  X,
  Phone,
  HelpCircle,
  Award,
  User as UserIcon,
} from 'lucide-react-native';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface GovtDashboardProps {
  navigation: any;
}

export const GovtDashboardScreen: React.FC<GovtDashboardProps> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { language, setLanguage } = useLanguage();
  const { user } = useAuth();
  const isKn = language === 'kn';

  const [stats, setStats] = useState<GovernmentDashboardStats | null>(null);
  const [recentApplications, setRecentApplications] = useState<SchemeApplicationItem[]>([]);
  const [regionalInsights, setRegionalInsights] = useState<RegionalCropReportInsight[]>([]);
  const [alerts, setAlerts] = useState<GovernmentOfficialAlert[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Farmer Search state
  const [farmerSearchQuery, setFarmerSearchQuery] = useState('');
  const [foundFarmers, setFoundFarmers] = useState<FarmerAssistanceProfile[]>([]);
  const [selectedFarmer, setSelectedFarmer] = useState<FarmerAssistanceProfile | null>(null);

  // Quick Alert Publish Modal state
  const [isAlertModalVisible, setIsAlertModalVisible] = useState(false);
  const [alertTitle, setAlertTitle] = useState('');
  const [alertDistrict, setAlertDistrict] = useState('Dakshina Kannada & Udupi');
  const [affectedCrops, setAffectedCrops] = useState('Arecanut, Paddy');
  const [alertMessage, setAlertMessage] = useState('');
  const [isPublishingAlert, setIsPublishingAlert] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [s, apps, insights, alts, farmers] = await Promise.all([
        fetchGovernmentStats(),
        fetchGovernmentApplications(),
        fetchRegionalAgriculturalInsights(),
        fetchGovernmentAlerts(),
        searchFarmersAssistance(),
      ]);
      setStats(s);
      setRecentApplications(apps.slice(0, 3));
      setRegionalInsights(insights);
      setAlerts(alts);
      setFoundFarmers(farmers);
    } catch {
      // fallback handled gracefully
    } finally {
      setIsLoading(false);
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

  const handleFarmerSearch = async (text: string) => {
    setFarmerSearchQuery(text);
    const results = await searchFarmersAssistance(text);
    setFoundFarmers(results);
  };

  const handlePublishAlert = async () => {
    if (!alertTitle.trim() || !alertMessage.trim()) {
      Alert.alert(isKn ? 'ಮಾಹಿತಿ ಭರ್ತಿ ಮಾಡಿ' : 'Please Fill Fields', isKn ? 'ಶೀರ್ಷಿಕೆ ಮತ್ತು ಸಂದೇಶವನ್ನು ನಮೂದಿಸಿ.' : 'Please enter title and message.');
      return;
    }

    setIsPublishingAlert(true);
    try {
      await publishGovernmentAlert(
        alertTitle.trim(),
        alertDistrict.trim(),
        affectedCrops.trim(),
        alertMessage.trim(),
        user?.name || 'Department of Agriculture Officer'
      );

      Alert.alert(
        isKn ? 'ಅಧಿಕೃತ ಸೂಚನೆ ಪ್ರಕಟಿಸಲಾಗಿದೆ 📢' : 'Government Alert Published 📢',
        isKn
          ? `${alertDistrict} ವ್ಯಾಪ್ತಿಯ ಎಲ್ಲಾ ನೋಂದಾಯಿತ ರೈತರಿಗೆ ಅಧಿಕೃತ ಕೃಷಿ ಮುನ್ನೆಚ್ಚರಿಕೆ ತಲುಪಿದೆ.`
          : `Official alert successfully broadcasted to all registered farmers in ${alertDistrict}.`
      );

      setIsAlertModalVisible(false);
      setAlertTitle('');
      setAlertMessage('');
      loadData();
    } catch {
      Alert.alert(isKn ? 'ದೋಷ' : 'Error', 'Could not publish alert.');
    } finally {
      setIsPublishingAlert(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* ============================================================== */}
      {/* 1. Header (Matching Section 2 of Specification) */}
      {/* ============================================================== */}
      <View style={[styles.headerWrapper, { paddingTop: Math.max(insets.top, 12) + Spacing.xs }]}>
        <View style={styles.headerTopRow}>
          <View style={styles.brandTitleCol}>
            <View style={styles.logoBadgeRow}>
              <View style={styles.logoCircle}>
                <Landmark size={18} color="#FFFFFF" strokeWidth={2.4} />
              </View>
              <Text style={styles.appTitle}>
                <Text style={{ color: '#166534' }}>Krushi</Text>
                <Text style={{ color: '#16A34A' }}>Pragya</Text>
              </Text>
            </View>
            <Text style={styles.govtRoleTag}>
              {isKn ? '🏛 ಕೃಷಿ ಇಲಾಖೆ • ಕೃಷಿ ಅಧಿಕಾರಿ' : '🏛 Dept of Agriculture • Officer'}
            </Text>
          </View>

          {/* Right: Language switch button & Profile icon */}
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <TouchableOpacity
              activeOpacity={0.8}
              onPress={() => setLanguage(isKn ? 'en' : 'kn')}
              style={styles.langPill}
            >
              <Globe2 size={13} color="#0F6E56" />
              <Text style={styles.langText}>{isKn ? 'English' : 'ಕನ್ನಡ'}</Text>
            </TouchableOpacity>

            <TouchableOpacity
              activeOpacity={0.8}
              onPress={() => navigation.navigate('Profile')}
              style={styles.profileAvatarBtn}
            >
              <UserIcon size={16} color="#0F6E56" strokeWidth={2.4} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Officer Profile Card */}
        <TouchableOpacity
          activeOpacity={0.85}
          onPress={() => navigation.navigate('Profile')}
          style={styles.officerIdentityCard}
        >
          <View style={styles.officerAvatarCircle}>
            <Text style={styles.officerAvatarText}>
              {user?.name ? user.name.slice(0, 2).toUpperCase() : 'AG'}
            </Text>
          </View>
          <View style={{ flex: 1 }}>
            <View style={styles.nameRow}>
              <Text style={styles.officerName}>
                {user?.name || (isKn ? 'ಕೃಷಿ ಅಧಿಕಾರಿ' : 'Agriculture Officer')}
              </Text>
              <View style={styles.badgeGovt}>
                <ShieldAlert size={11} color="#9333EA" />
                <Text style={styles.badgeGovtText}>Govt of Karnataka</Text>
              </View>
            </View>
            <Text style={styles.officerDesignation}>
              {isKn ? 'ತಾಲ್ಲೂಕು ಕೃಷಿ ನಿರ್ದೇಶನಾಲಯ • ಬೆಳ್ತಂಗಡಿ & ಉಜಿರೆ' : 'Taluk Agricultural Office • Belthangady & Ujire'}
            </Text>
          </View>
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#0F6E56']} />}
      >
        {/* ============================================================== */}
        {/* 2. Dashboard Summary (4 Cards Matching Section 2) */}
        {/* ============================================================== */}
        <View style={styles.summaryGrid}>
          {/* Card 1: Farmers */}
          <View style={[styles.metricCard, { borderLeftColor: '#16A34A' }]}>
            <View style={styles.metricCardTop}>
              <Text style={styles.metricNumber}>{stats?.farmers_count ?? 128}</Text>
              <View style={[styles.metricIconWrap, { backgroundColor: '#DCFCE7' }]}>
                <Users size={16} color="#16A34A" />
              </View>
            </View>
            <Text style={styles.metricLabel}>{isKn ? 'ನೋಂದಾಯಿತ ರೈತರು' : 'Farmers'}</Text>
            <Text style={styles.metricSub}>{isKn ? 'ತಾಲ್ಲೂಕು ವ್ಯಾಪ್ತಿ' : 'Registered Taluk'}</Text>
          </View>

          {/* Card 2: Applications */}
          <View style={[styles.metricCard, { borderLeftColor: '#7E22CE' }]}>
            <View style={styles.metricCardTop}>
              <Text style={[styles.metricNumber, { color: '#7E22CE' }]}>{stats?.applications_count ?? 34}</Text>
              <View style={[styles.metricIconWrap, { backgroundColor: '#F3E8FF' }]}>
                <FileText size={16} color="#7E22CE" />
              </View>
            </View>
            <Text style={styles.metricLabel}>{isKn ? 'ಅರ್ಜಿಗಳು' : 'Applications'}</Text>
            <Text style={styles.metricSub}>{isKn ? 'ಯೋಜನಾ ಅರ್ಜಿಗಳು' : 'Active Submissions'}</Text>
          </View>

          {/* Card 3: Schemes */}
          <View style={[styles.metricCard, { borderLeftColor: '#2563EB' }]}>
            <View style={styles.metricCardTop}>
              <Text style={[styles.metricNumber, { color: '#2563EB' }]}>{stats?.schemes_count ?? 12}</Text>
              <View style={[styles.metricIconWrap, { backgroundColor: '#DBEAFE' }]}>
                <Landmark size={16} color="#2563EB" />
              </View>
            </View>
            <Text style={styles.metricLabel}>{isKn ? 'ಸಕ್ರಿಯ ಯೋಜನೆಗಳು' : 'Active Schemes'}</Text>
            <Text style={styles.metricSub}>{isKn ? 'ಕೇಂದ್ರ & ರಾಜ್ಯ' : 'Central & State'}</Text>
          </View>

          {/* Card 4: Pending */}
          <View style={[styles.metricCard, { borderLeftColor: '#D97706' }]}>
            <View style={styles.metricCardTop}>
              <Text style={[styles.metricNumber, { color: '#D97706' }]}>{stats?.pending_count ?? 7}</Text>
              <View style={[styles.metricIconWrap, { backgroundColor: '#FEF3C7' }]}>
                <Clock size={16} color="#D97706" />
              </View>
            </View>
            <Text style={styles.metricLabel}>{isKn ? 'ಬಾಕಿ ಪರಿಶೀಲನೆ' : 'Pending'}</Text>
            <Text style={styles.metricSub}>{isKn ? 'ಕ್ರಮ ಅಗತ್ಯವಿದೆ' : 'Action Required'}</Text>
          </View>
        </View>

        {/* ============================================================== */}
        {/* 3. Core Role Purpose Banner: "ENABLE" */}
        {/* ============================================================== */}
        <View style={styles.purposeCard}>
          <View style={styles.purposeHeader}>
            <Sparkles size={16} color="#7E22CE" />
            <Text style={styles.purposeTitle}>
              {isKn ? 'ಕೃಷಿ ಇಲಾಖೆಯ ಪಾತ್ರ: ಸೌಲಭ್ಯ ಒದಗಿಸುವುದು (ENABLE)' : 'Government Officer Role: ENABLE'}
            </Text>
          </View>
          <Text style={styles.purposeText}>
            {isKn
              ? 'ರೈತರು = ಕ್ರಮ (Act) • ತಜ್ಞರು = ಪರಿಶೀಲನೆ (Verify) • ಸರ್ಕಾರ = ಸೌಲಭ್ಯ ಒದಗಿಸುವುದು (Enable)'
              : 'Farmer = Act • Expert = Verify • Government Officer = Enable'}
          </Text>
          <Text style={styles.purposeSubText}>
            {isKn
              ? 'ಯೋಜನೆಗಳ ಅನುಷ್ಠಾನ, ಅರ್ಜಿ ಪರಿಶೀಲನೆ, ಅರ್ಹತಾ ನಿರ್ಣಯ, ಹಾಗೂ ಅಧಿಕೃತ ಸರ್ಕಾರಿ ಎಚ್ಚರಿಕೆ ರವಾನೆ.'
              : 'Government schemes execution, application verification, subsidy disbursement & official alerts.'}
          </Text>
        </View>

        {/* ============================================================== */}
        {/* 4. Main Service ①: Applications Queue Highlight (Section 4) */}
        {/* ============================================================== */}
        <View style={styles.sectionHeaderRow}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <FileText size={18} color="#7E22CE" />
            <Text style={styles.sectionHeading}>
              {isKn ? 'ಅರ್ಜಿಗಳ ನಿರ್ವಹಣೆ (Applications Queue)' : 'Applications Management'}
            </Text>
          </View>
          <TouchableOpacity
            style={styles.linkBtn}
            onPress={() => navigation.navigate('GovtApplicationsTab')}
            activeOpacity={0.7}
          >
            <Text style={styles.linkBtnText}>{isKn ? 'ಎಲ್ಲವನ್ನೂ ನೋಡಿ' : 'View All'}</Text>
            <ChevronRight size={14} color="#7E22CE" />
          </TouchableOpacity>
        </View>

        <View style={styles.cardsList}>
          {recentApplications.map((app) => (
            <TouchableOpacity
              key={app.id}
              style={styles.appCard}
              activeOpacity={0.85}
              onPress={() => navigation.navigate('GovtApplicationsTab')}
            >
              <View style={styles.appCardTop}>
                <View style={styles.schemeTag}>
                  <Text style={styles.schemeTagText}>{app.scheme_category}</Text>
                </View>
                <View
                  style={[
                    styles.statusPill,
                    app.status === 'UNDER_REVIEW'
                      ? styles.pillOrange
                      : app.status === 'APPROVED'
                      ? styles.pillGreen
                      : styles.pillYellow,
                  ]}
                >
                  <Text
                    style={[
                      styles.statusPillText,
                      app.status === 'UNDER_REVIEW'
                        ? styles.textOrange
                        : app.status === 'APPROVED'
                        ? styles.textGreen
                        : styles.textYellow,
                    ]}
                  >
                    {app.status === 'UNDER_REVIEW'
                      ? (isKn ? 'ಪರಿಶೀಲನೆಯಲ್ಲಿದೆ' : 'Under Review')
                      : app.status === 'APPROVED'
                      ? (isKn ? 'ಅನುಮೋದಿತ' : 'Approved')
                      : (isKn ? 'ಬಾಕಿ ಇದೆ' : 'Pending')}
                  </Text>
                </View>
              </View>

              <Text style={styles.appSchemeTitle}>
                {isKn && app.scheme_title_kn ? app.scheme_title_kn : app.scheme_title}
              </Text>

              <View style={styles.appMetaRow}>
                <Text style={styles.appFarmerName}>{app.farmer_name}</Text>
                <Text style={styles.dot}>•</Text>
                <MapPin size={11} color="#64748B" />
                <Text style={styles.appLocation}>{app.village}</Text>
                <Text style={styles.dot}>•</Text>
                <Text style={styles.appCrop}>{app.crop}</Text>
              </View>

              <View style={styles.appFooterRow}>
                <Text style={styles.appIdText}>ID: {app.application_number}</Text>
                <View style={styles.reviewPrompt}>
                  <Text style={styles.reviewPromptText}>
                    {isKn ? 'ಅರ್ಜಿ ಪರಿಶೀಲಿಸಿ' : 'Review'}
                  </Text>
                  <ChevronRight size={13} color="#7E22CE" />
                </View>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* ============================================================== */}
        {/* 5. Main Service ④: Regional Agricultural Insights (Section 7) */}
        {/* ============================================================== */}
        <View style={[styles.sectionHeaderRow, { marginTop: 8 }]}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <TrendingUp size={18} color="#0F766E" />
            <Text style={styles.sectionHeading}>
              {isKn ? 'ಪ್ರಾದೇಶಿಕ ಕೃಷಿ ಸ್ಥಿತಿ (Regional Insights)' : 'Regional Agricultural Insights'}
            </Text>
          </View>
          <TouchableOpacity
            style={styles.linkBtn}
            onPress={() => navigation.navigate('GovtInsightsTab')}
            activeOpacity={0.7}
          >
            <Text style={[styles.linkBtnText, { color: '#0F766E' }]}>{isKn ? 'ವಿವರಗಳು' : 'Details'}</Text>
            <ChevronRight size={14} color="#0F766E" />
          </TouchableOpacity>
        </View>

        <View style={styles.insightsCard}>
          <Text style={styles.insightsDistrict}>📍 Udupi & Dakshina Kannada District</Text>

          <View style={styles.insightRowsList}>
            {regionalInsights.map((insight) => {
              const isHighRisk = insight.risk_level === 'HIGH';
              const isModRisk = insight.risk_level === 'MODERATE';

              return (
                <View key={insight.crop_name} style={styles.insightRowItem}>
                  <View style={{ flex: 1, gap: 2 }}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                      <Text style={styles.insightCropName}>
                        {isKn ? `${insight.crop_name_kn} (${insight.crop_name})` : insight.crop_name}
                      </Text>
                      <View
                        style={[
                          styles.riskBadge,
                          isHighRisk ? styles.riskHigh : isModRisk ? styles.riskMod : styles.riskLow,
                        ]}
                      >
                        <Text
                          style={[
                            styles.riskBadgeText,
                            isHighRisk ? styles.riskTextHigh : isModRisk ? styles.riskTextMod : styles.riskTextLow,
                          ]}
                        >
                          {isHighRisk ? '🔴 High Risk' : isModRisk ? '🟠 Moderate' : '🟢 Normal'}
                        </Text>
                      </View>
                    </View>
                    <Text style={styles.insightDiseaseText}>
                      {isKn ? insight.dominant_disease_kn : insight.dominant_disease}
                    </Text>
                  </View>
                  <Text style={styles.reportsCountBadge}>
                    {insight.report_count} {isKn ? 'ವರದಿಗಳು' : 'reports'}
                  </Text>
                </View>
              );
            })}
          </View>
        </View>

        {/* ============================================================== */}
        {/* 6. Main Service ③: Farmer Assistance Search (Section 6) */}
        {/* ============================================================== */}
        <View style={[styles.sectionHeaderRow, { marginTop: 8 }]}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <Users size={18} color="#2563EB" />
            <Text style={styles.sectionHeading}>
              {isKn ? 'ರೈತರ ಹುಡುಕಾಟ (Farmer Assistance)' : 'Farmer Assistance Directory'}
            </Text>
          </View>
        </View>

        <View style={styles.farmerSearchCard}>
          <View style={styles.farmerSearchInputRow}>
            <Search size={16} color="#64748B" />
            <TextInput
              style={styles.farmerSearchInput}
              placeholder={isKn ? 'ರೈತರ ಹೆಸರು, ಗ್ರಾಮ ಅಥವಾ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ...' : 'Search farmer / village / mobile...'}
              placeholderTextColor="#94A3B8"
              value={farmerSearchQuery}
              onChangeText={handleFarmerSearch}
            />
            {farmerSearchQuery.length > 0 && (
              <TouchableOpacity onPress={() => handleFarmerSearch('')}>
                <X size={15} color="#64748B" />
              </TouchableOpacity>
            )}
          </View>

          <View style={styles.farmerList}>
            {foundFarmers.slice(0, 2).map((farmer) => (
              <View key={farmer.id} style={styles.farmerItem}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.farmerItemName}>{farmer.name}</Text>
                  <Text style={styles.farmerItemVillage}>
                    {farmer.village} • {farmer.land_acres}
                  </Text>
                  <Text style={styles.farmerItemCrops}>
                    {farmer.crops.map((c) => `${c.icon} ${isKn ? c.name_kn : c.name}`).join('  ')}
                  </Text>
                </View>
                <View style={styles.farmerAppStats}>
                  <Text style={styles.farmerAppCount}>
                    {farmer.total_applications} {isKn ? 'ಅರ್ಜಿಗಳು' : 'Apps'}
                  </Text>
                  <Text style={styles.farmerAppApproved}>
                    ✓ {farmer.approved} {isKn ? 'ಅನುಮೋದಿತ' : 'Approved'}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        </View>

        {/* ============================================================== */}
        {/* 7. Main Service ⑤: 1-Tap Government Alert Trigger (Section 8) */}
        {/* ============================================================== */}
        <TouchableOpacity
          style={styles.broadcastAlertActionBtn}
          activeOpacity={0.85}
          onPress={() => setIsAlertModalVisible(true)}
        >
          <View style={styles.broadcastIconBox}>
            <Send size={18} color="#FFFFFF" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.broadcastBtnTitle}>
              {isKn ? 'ಹೊಸ ಕೃಷಿ ಸೂಚನೆ ಪ್ರಕಟಿಸಿ (Publish Alert)' : 'Publish Official Government Alert'}
            </Text>
            <Text style={styles.broadcastBtnSub}>
              {isKn
                ? 'ರೈತರಿಗೆ ಮುನ್ನೆಚ್ಚರಿಕೆ, ಹವಾಮಾನ ಅಪಾಯ ಅಥವಾ ಸಬ್ಸಿಡಿ ಮಾಹಿತಿ ರವಾನಿಸಿ'
                : 'Broadcast weather risk, disease outbreak, or subsidy notification to farmers'}
            </Text>
          </View>
          <ChevronRight size={18} color="#FFFFFF" />
        </TouchableOpacity>
      </ScrollView>

      {/* ============================================================== */}
      {/* 8. Publish Official Alert Modal */}
      {/* ============================================================== */}
      <Modal
        visible={isAlertModalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setIsAlertModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            <View style={styles.modalHeaderRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.modalTitle}>
                  {isKn ? 'ಹೊಸ ಅಧಿಕೃತ ಕೃಷಿ ಸೂಚನೆ' : 'Publish Official Government Alert'}
                </Text>
                <Text style={styles.modalSub}>
                  {isKn ? 'ತಾಲ್ಲೂಕಿನ ಎಲ್ಲಾ ನೋಂದಾಯಿತ ರೈತರಿಗೆ ರವಾನೆಯಾಗುತ್ತದೆ' : 'Will be dispatched directly to registered farmers'}
                </Text>
              </View>
              <TouchableOpacity onPress={() => setIsAlertModalVisible(false)} style={styles.modalCloseBtn}>
                <X size={20} color="#64748B" />
              </TouchableOpacity>
            </View>

            <ScrollView contentContainerStyle={styles.modalScroll}>
              <View style={styles.formGroup}>
                <Text style={styles.formLabel}>{isKn ? 'ಸೂಚನೆಯ ಶೀರ್ಷಿಕೆ (Title):' : 'Alert Title:'}</Text>
                <TextInput
                  style={styles.formInput}
                  placeholder={isKn ? 'ಉದಾ: ಭಾರೀ ಮಳೆ ಹಾಗೂ ಕೊಳೆರೋಗ ಮುನ್ನೆಚ್ಚರಿಕೆ' : 'e.g. Heavy Rain & Fruit Rot Advisory'}
                  placeholderTextColor="#94A3B8"
                  value={alertTitle}
                  onChangeText={setAlertTitle}
                />
              </View>

              <View style={styles.formGroup}>
                <Text style={styles.formLabel}>{isKn ? 'ವ್ಯಾಪ್ತಿಯ ಜಿಲ್ಲೆ / ತಾಲ್ಲೂಕು:' : 'Target District / Taluk:'}</Text>
                <TextInput
                  style={styles.formInput}
                  value={alertDistrict}
                  onChangeText={setAlertDistrict}
                />
              </View>

              <View style={styles.formGroup}>
                <Text style={styles.formLabel}>{isKn ? 'ಬಾಧಿತ ಬೆಳೆಗಳು (Affected Crops):' : 'Affected Crops:'}</Text>
                <TextInput
                  style={styles.formInput}
                  value={affectedCrops}
                  onChangeText={setAffectedCrops}
                />
              </View>

              <View style={styles.formGroup}>
                <Text style={styles.formLabel}>{isKn ? 'ಅಧಿಕೃತ ಸಂದೇಶ (Advisory Message):' : 'Advisory Message:'}</Text>
                <TextInput
                  style={[styles.formInput, { height: 90, textAlignVertical: 'top' }]}
                  multiline
                  placeholder={isKn ? 'ಮುಂದಿನ 48 ಗಂಟೆಗಳಲ್ಲಿ ಹೆಚ್ಚಿನ ಮಳೆಯ ಸಾಧ್ಯತೆ ಇರುವುದರಿಂದ ಮುನ್ನೆಚ್ಚರಿಕೆ ಕೈಗೊಳ್ಳಿ...' : 'Enter official advisory instructions...'}
                  placeholderTextColor="#94A3B8"
                  value={alertMessage}
                  onChangeText={setAlertMessage}
                />
              </View>

              <TouchableOpacity
                style={styles.publishSubmitBtn}
                activeOpacity={0.85}
                disabled={isPublishingAlert}
                onPress={handlePublishAlert}
              >
                {isPublishingAlert ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <>
                    <Send size={16} color="#FFFFFF" />
                    <Text style={styles.publishSubmitBtnText}>
                      {isKn ? 'ಅಧಿಕೃತವಾಗಿ ಪ್ರಕಟಿಸಿ (PUBLISH ALERT)' : 'PUBLISH OFFICIAL ALERT'}
                    </Text>
                  </>
                )}
              </TouchableOpacity>
            </ScrollView>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC' },
  headerWrapper: {
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.md,
    gap: 12,
  },
  headerTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  brandTitleCol: { gap: 2 },
  logoBadgeRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  logoCircle: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: '#16A34A',
    alignItems: 'center',
    justifyContent: 'center',
  },
  appTitle: { fontSize: 20, fontWeight: '800' },
  govtRoleTag: {
    fontSize: 11,
    color: '#166534',
    fontWeight: '700',
    marginLeft: 40,
  },
  langPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#E1F5EE',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: '#BFE7D7',
  },
  langText: { fontSize: 12, fontWeight: '700', color: '#0F6E56' },
  profileAvatarBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#E1F5EE',
    borderWidth: 1,
    borderColor: '#BFE7D7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  officerIdentityCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
  },
  officerAvatarCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#16A34A',
    alignItems: 'center',
    justifyContent: 'center',
  },
  officerAvatarText: { fontSize: 15, fontWeight: '800', color: '#FFFFFF' },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  officerName: { fontSize: 15, fontWeight: '800', color: '#0F172A' },
  badgeGovt: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#F3E8FF',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  badgeGovtText: { fontSize: 10, fontWeight: '800', color: '#7E22CE' },
  officerDesignation: { fontSize: 11, color: '#64748B', marginTop: 1 },
  scrollContent: { padding: Spacing.md, paddingBottom: 40, gap: 14 },
  summaryGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  metricCard: {
    width: (SCREEN_WIDTH - Spacing.md * 2 - 10) / 2,
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderLeftWidth: 4,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  metricCardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  metricNumber: { fontSize: 24, fontWeight: '800', color: '#0F172A' },
  metricIconWrap: {
    width: 30,
    height: 30,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
  },
  metricLabel: { fontSize: 12, fontWeight: '700', color: '#334155' },
  metricSub: { fontSize: 10, color: '#64748B', marginTop: 1 },
  purposeCard: {
    backgroundColor: '#FAF5FF',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E9D5FF',
    gap: 4,
  },
  purposeHeader: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  purposeTitle: { fontSize: 12.5, fontWeight: '800', color: '#7E22CE' },
  purposeText: { fontSize: 11.5, fontWeight: '700', color: '#1E293B' },
  purposeSubText: { fontSize: 10.5, color: '#64748B' },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sectionHeading: { fontSize: 13.5, fontWeight: '800', color: '#0F172A' },
  linkBtn: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  linkBtnText: { fontSize: 12, fontWeight: '700', color: '#7E22CE' },
  cardsList: { gap: 10 },
  appCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 6,
  },
  appCardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  schemeTag: {
    backgroundColor: '#F3E8FF',
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: 4,
  },
  schemeTagText: { fontSize: 10.5, fontWeight: '800', color: '#7E22CE' },
  statusPill: { paddingHorizontal: 7, paddingVertical: 3, borderRadius: 4 },
  pillOrange: { backgroundColor: '#FFEDD5' },
  pillGreen: { backgroundColor: '#DCFCE7' },
  pillYellow: { backgroundColor: '#FEF3C7' },
  statusPillText: { fontSize: 10.5, fontWeight: '800' },
  textOrange: { color: '#C2410C' },
  textGreen: { color: '#15803D' },
  textYellow: { color: '#B45309' },
  appSchemeTitle: { fontSize: 14, fontWeight: '800', color: '#0F172A' },
  appMetaRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  appFarmerName: { fontSize: 12, fontWeight: '700', color: '#1E293B' },
  dot: { color: '#CBD5E1', marginHorizontal: 2 },
  appLocation: { fontSize: 11, color: '#64748B' },
  appCrop: { fontSize: 11, color: '#64748B' },
  appFooterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: '#F8FAFC',
  },
  appIdText: { fontSize: 11, color: '#94A3B8' },
  reviewPrompt: { flexDirection: 'row', alignItems: 'center', gap: 3 },
  reviewPromptText: { fontSize: 11.5, fontWeight: '800', color: '#7E22CE' },
  insightsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 8,
  },
  insightsDistrict: { fontSize: 11.5, fontWeight: '700', color: '#0F766E' },
  insightRowsList: { gap: 8 },
  insightRowItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  insightCropName: { fontSize: 13, fontWeight: '700', color: '#0F172A' },
  insightDiseaseText: { fontSize: 11, color: '#64748B' },
  riskBadge: { paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 },
  riskHigh: { backgroundColor: '#FEE2E2' },
  riskMod: { backgroundColor: '#FEF3C7' },
  riskLow: { backgroundColor: '#DCFCE7' },
  riskBadgeText: { fontSize: 10, fontWeight: '800' },
  riskTextHigh: { color: '#DC2626' },
  riskTextMod: { color: '#D97706' },
  riskTextLow: { color: '#16A34A' },
  reportsCountBadge: {
    fontSize: 11,
    fontWeight: '700',
    color: '#475569',
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  farmerSearchCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 10,
  },
  farmerSearchInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F1F5F9',
    borderRadius: BorderRadius.sm,
    paddingHorizontal: 10,
    height: 38,
  },
  farmerSearchInput: { flex: 1, fontSize: 12.5, color: '#0F172A' },
  farmerList: { gap: 8 },
  farmerItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#F8FAFC',
  },
  farmerItemName: { fontSize: 13, fontWeight: '800', color: '#0F172A' },
  farmerItemVillage: { fontSize: 11, color: '#64748B' },
  farmerItemCrops: { fontSize: 11, color: '#334155', marginTop: 2 },
  farmerAppStats: { alignItems: 'flex-end', gap: 2 },
  farmerAppCount: { fontSize: 11, fontWeight: '700', color: '#2563EB' },
  farmerAppApproved: { fontSize: 10, color: '#15803D', fontWeight: '600' },
  broadcastAlertActionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#7E22CE',
    borderRadius: BorderRadius.md,
    padding: 14,
  },
  broadcastIconBox: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  broadcastBtnTitle: { fontSize: 13.5, fontWeight: '800', color: '#FFFFFF' },
  broadcastBtnSub: { fontSize: 10.5, color: '#E9D5FF', marginTop: 2 },

  // Modal Sheet
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15,23,42,0.65)',
    justifyContent: 'flex-end',
  },
  modalSheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 18,
    borderTopRightRadius: 18,
    padding: Spacing.md,
    maxHeight: '90%',
  },
  modalHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  modalTitle: { fontSize: 15, fontWeight: '800', color: '#0F172A' },
  modalSub: { fontSize: 11.5, color: '#64748B', marginTop: 2 },
  modalCloseBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalScroll: { paddingVertical: 12, gap: 12 },
  formGroup: { gap: 4 },
  formLabel: { fontSize: 11.5, fontWeight: '700', color: '#334155' },
  formInput: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 13,
    color: '#0F172A',
  },
  publishSubmitBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#7E22CE',
    paddingVertical: 12,
    borderRadius: BorderRadius.sm,
    marginTop: 6,
  },
  publishSubmitBtnText: { fontSize: 13, fontWeight: '800', color: '#FFFFFF' },
});
