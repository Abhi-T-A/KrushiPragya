import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  TextInput,
  RefreshControl,
  Modal,
  Alert,
  Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  fetchRegionalAgriculturalInsights,
  fetchRegionalWeatherRisks,
  fetchGovernmentAlerts,
  publishGovernmentAlert,
  RegionalCropReportInsight,
  WeatherRiskAlert,
  GovernmentOfficialAlert,
} from '../../services/governmentApi';
import {
  BarChart3,
  AlertTriangle,
  CloudRain,
  TrendingUp,
  Send,
  ShieldCheck,
  CheckCircle2,
  MapPin,
  RefreshCw,
  Plus,
  X,
  Info,
  Calendar,
  Layers,
  ArrowUpRight,
  ArrowRight,
  ShieldAlert,
  Sparkles,
  Users,
} from 'lucide-react-native';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// Market overview prices (Read-only as per specification Section 13)
const MARKET_OVERVIEW_DATA = [
  {
    crop: 'Arecanut (ಅಡಿಕೆ)',
    crop_kn: 'ಅಡಿಕೆ',
    avg_price: '₹38,000 / quintal',
    trend: 'increasing',
    change: '+₹1,200',
    market: 'Mangalore & Puttur APMC',
  },
  {
    crop: 'Paddy (ಭತ್ತ)',
    crop_kn: 'ಭತ್ತ',
    avg_price: '₹3,200 / quintal',
    trend: 'stable',
    change: '0.0%',
    market: 'Kundapura & Udupi APMC',
  },
  {
    crop: 'Black Pepper (ಕಾಳುಮೆಣಸು)',
    crop_kn: 'ಕಾಳುಮೆಣಸು',
    avg_price: '₹55,000 / quintal',
    trend: 'increasing',
    change: '+₹2,500',
    market: 'Chikkamagaluru & Sakleshpur APMC',
  },
];

export const GovtInsightsScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const { language } = useLanguage();
  const isKn = language === 'kn';

  const [cropInsights, setCropInsights] = useState<RegionalCropReportInsight[]>([]);
  const [weatherRisks, setWeatherRisks] = useState<WeatherRiskAlert[]>([]);
  const [officialAlerts, setOfficialAlerts] = useState<GovernmentOfficialAlert[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Active filter tab: 'ALL' | 'CROPS' | 'WEATHER' | 'ALERTS' | 'MARKET'
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'HEALTH' | 'WEATHER' | 'ALERTS'>('OVERVIEW');

  // New Alert Modal
  const [isAlertModalVisible, setIsAlertModalVisible] = useState(false);
  const [alertTitle, setAlertTitle] = useState('');
  const [alertDistrict, setAlertDistrict] = useState('Udupi & Dakshina Kannada');
  const [affectedCrops, setAffectedCrops] = useState('Arecanut, Paddy');
  const [alertMessage, setAlertMessage] = useState('');
  const [isPublishing, setIsPublishing] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [insights, weather, alerts] = await Promise.all([
        fetchRegionalAgriculturalInsights(),
        fetchRegionalWeatherRisks(),
        fetchGovernmentAlerts(),
      ]);
      setCropInsights(insights);
      setWeatherRisks(weather);
      setOfficialAlerts(alerts);
    } catch (e) {
      console.error('Failed to load insights data:', e);
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

  const handleOpenAlertWithPreset = (district: string, defaultTitle: string, defaultMsg: string) => {
    setAlertDistrict(district);
    setAlertTitle(defaultTitle);
    setAlertMessage(defaultMsg);
    setIsAlertModalVisible(true);
  };

  const handlePublishAlert = async () => {
    if (!alertTitle.trim() || !alertMessage.trim()) {
      Alert.alert(
        isKn ? 'ಮಾಹಿತಿ ಅಪೂರ್ಣ' : 'Incomplete Alert',
        isKn ? 'ದಯವಿಟ್ಟು ಶೀರ್ಷಿಕೆ ಮತ್ತು ಎಚ್ಚರಿಕೆಯ ಸಂದೇಶವನ್ನು ನಮೂದಿಸಿ.' : 'Please provide alert title and message.'
      );
      return;
    }

    setIsPublishing(true);
    try {
      await publishGovernmentAlert(alertTitle, alertDistrict, affectedCrops, alertMessage);
      Alert.alert(
        isKn ? '✅ ಪ್ರಕಟಣೆ ಯಶಸ್ವಿ!' : '✅ Alert Broadcasted!',
        isKn
          ? `ಕೃಷಿ ಸೂಚನೆಯು ${alertDistrict} ವ್ಯಾಪ್ತಿಯ 450+ ನೋಂದಾಯಿತ ರೈತರಿಗೆ ರವಾನೆಯಾಗಿದೆ.`
          : `Official alert successfully broadcasted to 450+ registered farmers across ${alertDistrict}.`
      );
      setIsAlertModalVisible(false);
      setAlertTitle('');
      setAlertMessage('');
      await loadData();
    } catch (e) {
      Alert.alert('Error', 'Failed to broadcast alert. Please try again.');
    } finally {
      setIsPublishing(false);
    }
  };

  // Find max report count for proportional bar rendering
  const maxReportCount = Math.max(...cropInsights.map((c) => c.report_count), 45);

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* ============================================================== */}
      {/* 1. Header with Official Emblem & Language Toggle */}
      {/* ============================================================== */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.iconCircle}>
            <BarChart3 size={20} color="#7E22CE" />
          </View>
          <View>
            <Text style={styles.headerTitle}>
              {isKn ? 'ಪ್ರಾದೇಶಿಕ ಕೃಷಿ ಸ್ಥಿತಿ' : 'Agricultural Insights'}
            </Text>
            <Text style={styles.headerSubtitle}>
              {isKn ? 'ಪರಿಶೀಲಿತ ಕೃಷಿ ಗುಪ್ತಚರ • ಉಡುಪಿ & ದ.ಕ.' : 'Verified Intelligence • Regional Trends & Alerts'}
            </Text>
          </View>
        </View>

        <TouchableOpacity
          style={styles.publishHeaderBtn}
          onPress={() => {
            setAlertTitle('');
            setAlertMessage('');
            setIsAlertModalVisible(true);
          }}
          activeOpacity={0.8}
        >
          <Plus size={15} color="#FFFFFF" strokeWidth={2.5} />
          <Text style={styles.publishHeaderBtnText}>
            {isKn ? 'ಸೂಚನೆ ಪ್ರಕಟಿಸಿ' : 'New Alert'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Sub Tabs */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tabItem, activeTab === 'OVERVIEW' && styles.tabItemActive]}
          onPress={() => setActiveTab('OVERVIEW')}
        >
          <Text style={[styles.tabText, activeTab === 'OVERVIEW' && styles.tabTextActive]}>
            {isKn ? 'ಸ್ಥಿತಿ ನೋಟ' : 'Overview'}
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabItem, activeTab === 'HEALTH' && styles.tabItemActive]}
          onPress={() => setActiveTab('HEALTH')}
        >
          <Text style={[styles.tabText, activeTab === 'HEALTH' && styles.tabTextActive]}>
            {isKn ? 'ಬೆಳೆ ರೋಗ ಸ್ಥಿತಿ' : 'Crop Health'}
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabItem, activeTab === 'WEATHER' && styles.tabItemActive]}
          onPress={() => setActiveTab('WEATHER')}
        >
          <Text style={[styles.tabText, activeTab === 'WEATHER' && styles.tabTextActive]}>
            {isKn ? 'ಹವಾಮಾನ ಅಪಾಯ' : 'Weather Risk'}
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabItem, activeTab === 'ALERTS' && styles.tabItemActive]}
          onPress={() => setActiveTab('ALERTS')}
        >
          <Text style={[styles.tabText, activeTab === 'ALERTS' && styles.tabTextActive]}>
            {isKn ? 'ಸರ್ಕಾರಿ ಸೂಚನೆಗಳು' : 'Alerts'}
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#0F6E56']} />}
      >
        {/* ============================================================== */}
        {/* Verification Guarantee Banner (Section 10) */}
        {/* ============================================================== */}
        <View style={styles.guaranteeCard}>
          <View style={styles.guaranteeHeader}>
            <ShieldCheck size={16} color="#0F6E56" />
            <Text style={styles.guaranteeTitle}>
              {isKn ? 'ತಜ್ಞರಿಂದ ದೃಢೀಕರಿಸಲ್ಪಟ್ಟ ಕೃಷಿ ಮಾಹಿತಿ' : 'Verified Agricultural Intelligence Layer'}
            </Text>
          </View>
          <Text style={styles.guaranteeDesc}>
            {isKn
              ? 'ಕೃಷಿ ಅಧಿಕಾರಿಗಳು ಕೇವಲ ಪರಿಶೀಲಿತ ತಜ್ಞರ ದತ್ತಾಂಶವನ್ನು ವೀಕ್ಷಿಸುತ್ತಾರೆ (Raw AI ಅಲ್ಲ). AI → ಸಮುದಾಯ → ತಜ್ಞರ ದೃಢೀಕರಣ → ಸರ್ಕಾರಿ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್.'
              : 'Consuming verified agricultural intelligence, not raw AI predictions: AI → Community → Expert Verification → Verified Government Insights.'}
          </Text>
          <View style={styles.privacyPill}>
            <Info size={12} color="#475569" />
            <Text style={styles.privacyText}>
              {isKn
                ? 'ಗೌಪ್ಯತೆ ರಕ್ಷಣೆ: ವೈಯಕ್ತಿಕ ರೈತರ ಖಾಸಗಿ ವಿವರಗಳನ್ನು ಬಹಿರಂಗಪಡಿಸದೆ ಕೇವಲ ಒಟ್ಟುಗೂಡಿಸಿದ ಮಾಹಿತಿಯನ್ನು ಪ್ರದರ್ಶಿಸಲಾಗುತ್ತದೆ.'
                : 'Privacy Protected: Aggregated district intelligence without exposing individual farmer private records.'}
            </Text>
          </View>
        </View>

        {isLoading ? (
          <View style={styles.loadingBox}>
            <ActivityIndicator size="large" color="#7E22CE" />
            <Text style={styles.loadingText}>
              {isKn ? 'ಪ್ರಾದೇಶಿಕ ಅಂಕಿ-ಅಂಶಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...' : 'Aggregating regional crop intelligence...'}
            </Text>
          </View>
        ) : (
          <>
            {/* ============================================================== */}
            {/* 1. Regional Crop Distribution (Section 7) */}
            {/* ============================================================== */}
            {(activeTab === 'OVERVIEW' || activeTab === 'HEALTH') && (
              <View style={styles.sectionCard}>
                <View style={styles.sectionTitleRow}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <MapPin size={16} color="#7E22CE" />
                    <Text style={styles.cardHeaderTitle}>
                      {isKn ? 'ಪ್ರಾದೇಶಿಕ ಕೃಷಿ ಸ್ಥಿತಿ (Regional Crop Trends)' : 'Regional Agricultural Status'}
                    </Text>
                  </View>
                  <View style={styles.districtBadge}>
                    <Text style={styles.districtBadgeText}>📍 Udupi & DK</Text>
                  </View>
                </View>
                <Text style={styles.cardHeaderSub}>
                  {isKn
                    ? 'ತಾಲ್ಲೂಕಿನಲ್ಲಿ ದಾಖಲಾದ ಬೆಳೆ ಸಮಸ್ಯೆಗಳ ಒಟ್ಟು ವರದಿಗಳ ವಿತರಣೆ'
                    : 'Aggregated crop issue reports logged across the district'}
                </Text>

                {/* Bar Graph / Visual representation */}
                <View style={styles.barGraphContainer}>
                  {cropInsights.map((item) => {
                    const pct = Math.min(Math.round((item.report_count / maxReportCount) * 100), 100);
                    const isHigh = item.risk_level === 'HIGH';
                    const isMod = item.risk_level === 'MODERATE';

                    return (
                      <View key={item.crop_name} style={styles.graphRow}>
                        <View style={styles.cropLabelRow}>
                          <Text style={styles.cropNameMain}>{item.crop_name}</Text>
                          <Text style={styles.cropReportsCount}>
                            {item.report_count} {isKn ? 'ವರದಿಗಳು' : 'reports'}
                          </Text>
                        </View>

                        <View style={styles.progressTrack}>
                          <View
                            style={[
                              styles.progressBar,
                              {
                                width: `${pct}%`,
                                backgroundColor: isHigh ? '#DC2626' : isMod ? '#D97706' : '#16A34A',
                              },
                            ]}
                          />
                        </View>
                        <View style={styles.verifiedCountRow}>
                          <Text style={styles.verifiedCountText}>
                            ✓ {item.verified_disease_count} {isKn ? 'ತಜ್ಞರಿಂದ ದೃಢೀಕೃತ' : 'expert-verified'}
                          </Text>
                          <Text
                            style={[
                              styles.riskLevelText,
                              isHigh ? styles.textRed : isMod ? styles.textOrange : styles.textGreen,
                            ]}
                          >
                            {isHigh ? '🔴 High Risk' : isMod ? '🟠 Moderate' : '🟢 Normal'}
                          </Text>
                        </View>
                      </View>
                    );
                  })}
                </View>
              </View>
            )}

            {/* ============================================================== */}
            {/* 2. Crop Health Alerts (Section 7 & 10) */}
            {/* ============================================================== */}
            {(activeTab === 'OVERVIEW' || activeTab === 'HEALTH') && (
              <View style={styles.sectionCard}>
                <View style={styles.sectionTitleRow}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <AlertTriangle size={16} color="#DC2626" />
                    <Text style={styles.cardHeaderTitle}>
                      {isKn ? 'ಬೆಳೆ ಆರೋಗ್ಯ ಎಚ್ಚರಿಕೆಗಳು (Crop Health Alerts)' : 'Crop Health Disease Trends'}
                    </Text>
                  </View>
                </View>
                <Text style={styles.cardHeaderSub}>
                  {isKn
                    ? 'ಕೃಷಿ ತಜ್ಞರ ಕ್ಲಿನಿಕಲ್ ಪರಿಶೀಲನೆಯ ನಂತರ ಸಿದ್ಧಪಡಿಸಿದ ಪ್ರಮುಖ ರೋಗಗಳ ಸ್ಥಿತಿ'
                    : 'Validated disease surveillance from certified agricultural experts'}
                </Text>

                <View style={styles.alertsList}>
                  {cropInsights.map((insight) => {
                    const isHigh = insight.risk_level === 'HIGH';
                    const isMod = insight.risk_level === 'MODERATE';

                    return (
                      <View
                        key={`health-${insight.crop_name}`}
                        style={[
                          styles.healthAlertItem,
                          isHigh
                            ? styles.borderLeftRed
                            : isMod
                            ? styles.borderLeftOrange
                            : styles.borderLeftGreen,
                        ]}
                      >
                        <View style={styles.healthAlertTop}>
                          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                            <Text style={styles.healthCropName}>{insight.crop_name}</Text>
                            <Text style={styles.healthCropKn}>({insight.crop_name_kn})</Text>
                          </View>
                          <View
                            style={[
                              styles.healthPill,
                              isHigh
                                ? styles.bgRedLight
                                : isMod
                                ? styles.bgOrangeLight
                                : styles.bgGreenLight,
                            ]}
                          >
                            <Text
                              style={[
                                styles.healthPillText,
                                isHigh ? styles.textRed : isMod ? styles.textOrange : styles.textGreen,
                              ]}
                            >
                              {isHigh
                                ? isKn
                                  ? '🔴 ಅಧಿಕ ರೋಗ ಬಾಧೆ'
                                  : 'High Disease Reports'
                                : isMod
                                ? isKn
                                  ? '🟠 ಮಧ್ಯಮ ರೋಗ ಬಾಧೆ'
                                  : 'Moderate Reports'
                                : isKn
                                ? '🟢 ಸಹಜ ಸ್ಥಿತಿ'
                                : 'Normal'}
                            </Text>
                          </View>
                        </View>

                        <Text style={styles.diseaseNameText}>
                          {isKn ? insight.dominant_disease_kn : insight.dominant_disease}
                        </Text>
                        <Text style={styles.diseaseStatsText}>
                          {isKn
                            ? `ಒಟ್ಟು ${insight.report_count} ವರದಿಗಳ ಪೈಕಿ ${insight.verified_disease_count} ಪ್ರಕರಣಗಳು ತಜ್ಞರಿಂದ ಖಚಿತಪಟ್ಟಿವೆ.`
                            : `${insight.verified_disease_count} of ${insight.report_count} regional reports clinically confirmed by taluk experts.`}
                        </Text>

                        {isHigh && (
                          <TouchableOpacity
                            style={styles.quickAdvisoryTriggerBtn}
                            onPress={() =>
                              handleOpenAlertWithPreset(
                                'Dakshina Kannada & Udupi',
                                `Koleroga (Fruit Rot) Warning for ${insight.crop_name}`,
                                `ಮುಂಗಾರು ಮಳೆ ತೀವ್ರತೆಯಿಂದ ಅಡಿಕೆ ಕೊಳೆರೋಗ (ಮಹಾಳಿ) ಹೆಚ್ಚಾಗುತ್ತಿದ್ದು, ತಕ್ಷಣವೇ 1% ಬೋರ್ಡೋ ದ್ರಾವಣ ಸಿಂಪಡಿಸಿ.`
                              )
                            }
                            activeOpacity={0.8}
                          >
                            <Send size={12} color="#7E22CE" />
                            <Text style={styles.quickAdvisoryTriggerText}>
                              {isKn ? 'ಈ ರೋಗದ ಕುರಿತು ರೈತರಿಗೆ ಎಚ್ಚರಿಕೆ ಕಳುಹಿಸಿ' : 'Broadcast Advisory to Farmers'}
                            </Text>
                          </TouchableOpacity>
                        )}
                      </View>
                    );
                  })}
                </View>
              </View>
            )}

            {/* ============================================================== */}
            {/* 3. Regional Weather Risk Intelligence (Section 12) */}
            {/* ============================================================== */}
            {(activeTab === 'OVERVIEW' || activeTab === 'WEATHER') && (
              <View style={styles.sectionCard}>
                <View style={styles.sectionTitleRow}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <CloudRain size={16} color="#0284C7" />
                    <Text style={styles.cardHeaderTitle}>
                      {isKn ? 'ಹವಾಮಾನ ಅಪಾಯ ಸ್ಥಿತಿ (Weather Risk Intelligence)' : 'Regional Weather Risk'}
                    </Text>
                  </View>
                </View>
                <Text style={styles.cardHeaderSub}>
                  {isKn
                    ? 'ಹವಾಮಾನ ಮುನ್ಸೂಚನೆಯ ಆಧಾರದ ಮೇಲೆ ಕೃಷಿ ಬೆಳೆಗಳ ಮೇಲಾಗುವ ಸಂಭಾವ್ಯ ಅಪಾಯಗಳು'
                    : 'Meteorological risk assessment for taluk-level agricultural preparedness'}
                </Text>

                <View style={styles.weatherRiskList}>
                  {weatherRisks.map((w, idx) => {
                    const isHigh = w.risk_level === 'HIGH';
                    const isMed = w.risk_level === 'MEDIUM';

                    return (
                      <View key={idx} style={styles.weatherItemCard}>
                        <View style={styles.weatherItemTop}>
                          <View>
                            <Text style={styles.weatherDistrict}>{w.district}</Text>
                            <Text style={styles.weatherCondition}>{w.weather_condition}</Text>
                          </View>
                          <View
                            style={[
                              styles.weatherRiskBadge,
                              isHigh ? styles.bgRedLight : isMed ? styles.bgOrangeLight : styles.bgGreenLight,
                            ]}
                          >
                            <Text
                              style={[
                                styles.weatherRiskBadgeText,
                                isHigh ? styles.textRed : isMed ? styles.textOrange : styles.textGreen,
                              ]}
                            >
                              {isHigh
                                ? '🌧 HIGH RISK'
                                : isMed
                                ? '⛅ MEDIUM RISK'
                                : '☀️ LOW RISK'}
                            </Text>
                          </View>
                        </View>
                        <Text style={styles.weatherAdvisoryText}>{w.advisory_message}</Text>

                        {/* Action: Create Official Alert from Weather risk */}
                        <TouchableOpacity
                          style={styles.createAlertFromWeatherBtn}
                          onPress={() =>
                            handleOpenAlertWithPreset(
                              w.district,
                              `🌧 Weather Alert: ${w.weather_condition}`,
                              w.advisory_message
                            )
                          }
                          activeOpacity={0.8}
                        >
                          <Send size={13} color="#2563EB" />
                          <Text style={styles.createAlertFromWeatherBtnText}>
                            {isKn ? 'ಅಧಿಕೃತ ಕೃಷಿ ಎಚ್ಚರಿಕೆ ಪ್ರಕಟಿಸಿ' : 'Create Official Alert'}
                          </Text>
                        </TouchableOpacity>
                      </View>
                    );
                  })}
                </View>
              </View>
            )}

            {/* ============================================================== */}
            {/* 4. Published Official Government Alerts (Section 8) */}
            {/* ============================================================== */}
            {(activeTab === 'OVERVIEW' || activeTab === 'ALERTS') && (
              <View style={styles.sectionCard}>
                <View style={styles.sectionTitleRow}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <ShieldAlert size={16} color="#7E22CE" />
                    <Text style={styles.cardHeaderTitle}>
                      {isKn ? 'ಪ್ರಕಟಿತ ಕೃಷಿ ಸೂಚನೆಗಳು (Published Alerts)' : 'Broadcasted Official Alerts'}
                    </Text>
                  </View>
                  <TouchableOpacity
                    style={styles.newAlertSmallBtn}
                    onPress={() => {
                      setAlertTitle('');
                      setAlertMessage('');
                      setIsAlertModalVisible(true);
                    }}
                    activeOpacity={0.7}
                  >
                    <Plus size={13} color="#7E22CE" />
                    <Text style={styles.newAlertSmallBtnText}>{isKn ? 'ಹೊಸ ಸೂಚನೆ' : 'Publish'}</Text>
                  </TouchableOpacity>
                </View>
                <Text style={styles.cardHeaderSub}>
                  {isKn
                    ? 'ಸರ್ಕಾರಿ ಅಧಿಕಾರಿಯಿಂದ ರೈತರ ಮೊಬೈಲ್‌ಗೆ ಕಳುಹಿಸಲಾದ ಅಧಿಕೃತ ನಿರ್ದೇಶನಗಳು'
                    : 'Official directives dispatched directly to registered farmers in the app'}
                </Text>

                <View style={styles.alertsList}>
                  {officialAlerts.map((alert) => (
                    <View key={alert.id} style={styles.publishedAlertCard}>
                      <View style={styles.publishedAlertHeader}>
                        <View style={{ flex: 1 }}>
                          <Text style={styles.publishedAlertTitle}>{alert.title}</Text>
                          <Text style={styles.publishedAlertTarget}>
                            📍 {alert.district} • 🌾 {alert.affected_crops}
                          </Text>
                        </View>
                        <View style={styles.broadcastPill}>
                          <CheckCircle2 size={11} color="#16A34A" />
                          <Text style={styles.broadcastPillText}>{isKn ? 'ಪ್ರಸಾರವಾಗಿದೆ' : 'Live'}</Text>
                        </View>
                      </View>

                      <Text style={styles.publishedAlertMsg}>{alert.message}</Text>

                      <View style={styles.publishedAlertFooter}>
                        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                          <Users size={12} color="#64748B" />
                          <Text style={styles.publishedAlertFooterText}>
                            {alert.recipient_farmers_count} {isKn ? 'ರೈತರಿಗೆ ತಲುಪಿದೆ' : 'farmers reached'}
                          </Text>
                        </View>
                        <Text style={styles.publishedAlertTime}>{alert.published_at}</Text>
                      </View>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {/* ============================================================== */}
            {/* 5. Read-Only Mandi Market Overview (Section 13) */}
            {/* ============================================================== */}
            <View style={styles.sectionCard}>
              <View style={styles.sectionTitleRow}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                  <TrendingUp size={16} color="#059669" />
                  <Text style={styles.cardHeaderTitle}>
                    {isKn ? 'ಮಾರುಕಟ್ಟೆ ಸ್ಥಿತಿ (Market Overview - Read Only)' : 'Market Intelligence (Read-Only)'}
                  </Text>
                </View>
                <View style={styles.readOnlyBadge}>
                  <Text style={styles.readOnlyBadgeText}>{isKn ? 'ಓದಲು ಮಾತ್ರ' : 'Read-Only'}</Text>
                </View>
              </View>
              <Text style={styles.cardHeaderSub}>
                {isKn
                  ? 'ಕೃಷಿ ಉತ್ಪನ್ನ ಮಾರುಕಟ್ಟೆ ಸಮಿತಿ (APMC) ಯ ಅಧಿಕೃತ ಸರಾಸರಿ ಧಾರಣೆಗಳು'
                  : 'Official APMC price intelligence for officer contextual awareness (non-editable)'}
              </Text>

              <View style={styles.marketList}>
                {MARKET_OVERVIEW_DATA.map((item, idx) => (
                  <View key={idx} style={styles.marketItemRow}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.marketCropName}>{item.crop}</Text>
                      <Text style={styles.marketNameSub}>{item.market}</Text>
                    </View>
                    <View style={{ alignItems: 'flex-end' }}>
                      <Text style={styles.marketPriceText}>{item.avg_price}</Text>
                      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 3 }}>
                        <ArrowUpRight
                          size={12}
                          color={item.trend === 'increasing' ? '#16A34A' : '#64748B'}
                        />
                        <Text
                          style={[
                            styles.marketTrendText,
                            { color: item.trend === 'increasing' ? '#16A34A' : '#64748B' },
                          ]}
                        >
                          {item.trend === 'increasing' ? '↑ Increasing' : '→ Stable'}
                        </Text>
                      </View>
                    </View>
                  </View>
                ))}
              </View>
            </View>
          </>
        )}
      </ScrollView>

      {/* ============================================================== */}
      {/* Official Alert Publishing Modal (Section 8) */}
      {/* ============================================================== */}
      <Modal
        visible={isAlertModalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setIsAlertModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContainer, { paddingBottom: Math.max(insets.bottom, 20) }]}>
            <View style={styles.modalHeader}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <View style={[styles.iconCircle, { backgroundColor: '#F3E8FF' }]}>
                  <ShieldAlert size={18} color="#7E22CE" />
                </View>
                <View>
                  <Text style={styles.modalTitle}>
                    {isKn ? 'ಹೊಸ ಕೃಷಿ ಸೂಚನೆ ಪ್ರಕಟಿಸಿ' : 'Publish Official Government Alert'}
                  </Text>
                  <Text style={styles.modalSub}>
                    {isKn ? 'ಕೃಷಿ ಇಲಾಖೆ → ರೈತರ ಮೊಬೈಲ್ ಪ್ರಸಾರ' : 'Government Officer → Registered Farmers Broadcast'}
                  </Text>
                </View>
              </View>
              <TouchableOpacity onPress={() => setIsAlertModalVisible(false)} style={styles.closeBtn}>
                <X size={18} color="#64748B" />
              </TouchableOpacity>
            </View>

            <ScrollView showsVerticalScrollIndicator={false} style={styles.modalForm}>
              {/* Alert Title */}
              <View style={styles.formGroup}>
                <Text style={styles.formLabel}>
                  {isKn ? 'ಸೂಚನೆಯ ಶೀರ್ಷಿಕೆ (Alert Title) *' : 'Alert Title *'}
                </Text>
                <TextInput
                  style={styles.inputField}
                  placeholder={
                    isKn
                      ? 'ಉದಾ: ಮುಂಗಾರು ಮಳೆಯ ಅಡಿಕೆ ಕೊಳೆರೋಗ ಎಚ್ಚರಿಕೆ'
                      : 'e.g. Heavy Rain Advisory / Pest Outbreak Warning'
                  }
                  placeholderTextColor="#94A3B8"
                  value={alertTitle}
                  onChangeText={setAlertTitle}
                />
              </View>

              {/* District */}
              <View style={styles.formGroup}>
                <Text style={styles.formLabel}>
                  {isKn ? 'ವ್ಯಾಪ್ತಿಯ ಜಿಲ್ಲೆ / ತಾಲ್ಲೂಕು (District / Taluk) *' : 'Target District / Taluk *'}
                </Text>
                <TextInput
                  style={styles.inputField}
                  placeholder="Udupi / Dakshina Kannada"
                  placeholderTextColor="#94A3B8"
                  value={alertDistrict}
                  onChangeText={setAlertDistrict}
                />
              </View>

              {/* Affected Crops */}
              <View style={styles.formGroup}>
                <Text style={styles.formLabel}>
                  {isKn ? 'ಬಾಧಿತ ಬೆಳೆಗಳು (Affected Crops)' : 'Affected Crops'}
                </Text>
                <TextInput
                  style={styles.inputField}
                  placeholder="Arecanut, Paddy, Coconut"
                  placeholderTextColor="#94A3B8"
                  value={affectedCrops}
                  onChangeText={setAffectedCrops}
                />
              </View>

              {/* Message */}
              <View style={styles.formGroup}>
                <Text style={styles.formLabel}>
                  {isKn ? 'ಸರ್ಕಾರಿ ಅಧಿಕೃತ ಸಂದೇಶ (Official Message) *' : 'Official Advisory Message *'}
                </Text>
                <TextInput
                  style={[styles.inputField, styles.textArea]}
                  placeholder={
                    isKn
                      ? 'ಮುಂದಿನ 48 ಗಂಟೆಗಳಲ್ಲಿ ಹೆಚ್ಚಿನ ಮಳೆಯ ಸಾಧ್ಯತೆ ಇರುವುದರಿಂದ ಮುನ್ನೆಚ್ಚರಿಕೆ ಕ್ರಮ ಕೈಗೊಳ್ಳಲು ಕೋರಲಾಗಿದೆ...'
                      : 'Provide actionable preventive guidelines, spray formulas, and safety measures...'
                  }
                  placeholderTextColor="#94A3B8"
                  value={alertMessage}
                  onChangeText={setAlertMessage}
                  multiline
                  numberOfLines={4}
                  textAlignVertical="top"
                />
              </View>

              {/* Flow Explanation */}
              <View style={styles.flowCard}>
                <Text style={styles.flowTitle}>{isKn ? 'ಪ್ರಸಾರ ಪ್ರಕ್ರಿಯೆ:' : 'Broadcast Flow:'}</Text>
                <Text style={styles.flowStep}>
                  🏛 Government Officer ➔ 📡 KrushiPragya System ➔ 📱 Affected Farmers
                </Text>
              </View>
            </ScrollView>

            <View style={styles.modalActionRow}>
              <TouchableOpacity
                style={styles.cancelBtn}
                onPress={() => setIsAlertModalVisible(false)}
                activeOpacity={0.7}
              >
                <Text style={styles.cancelBtnText}>{isKn ? 'ರದ್ದುಮಾಡಿ' : 'Cancel'}</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.confirmPublishBtn}
                onPress={handlePublishAlert}
                disabled={isPublishing}
                activeOpacity={0.85}
              >
                {isPublishing ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <>
                    <Send size={15} color="#FFFFFF" />
                    <Text style={styles.confirmPublishBtnText}>
                      {isKn ? 'ಈಗಲೇ ಪ್ರಕಟಿಸಿ' : 'Broadcast Alert'}
                    </Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
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
    width: 38,
    height: 38,
    borderRadius: 10,
    backgroundColor: '#DCFCE7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  headerSubtitle: {
    fontSize: 11,
    fontWeight: '500',
    color: '#64748B',
    marginTop: 1,
  },
  publishHeaderBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#0F6E56',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  publishHeaderBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  tabItem: {
    paddingVertical: 10,
    paddingHorizontal: 10,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabItemActive: {
    borderBottomColor: '#0F6E56',
  },
  tabText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748B',
  },
  tabTextActive: {
    color: '#0F6E56',
    fontWeight: '800',
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
    gap: 16,
  },
  guaranteeCard: {
    backgroundColor: '#F0FDF4',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#BBF7D0',
    padding: 14,
  },
  guaranteeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  guaranteeTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0F6E56',
  },
  guaranteeDesc: {
    fontSize: 12,
    lineHeight: 18,
    color: '#4B5563',
  },
  privacyPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F3E8FF',
  },
  privacyText: {
    fontSize: 10.5,
    color: '#475569',
    flex: 1,
    lineHeight: 15,
  },
  loadingBox: {
    paddingVertical: 40,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  loadingText: {
    fontSize: 13,
    color: '#64748B',
    fontWeight: '500',
  },
  sectionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
  },
  sectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  cardHeaderTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
  },
  cardHeaderSub: {
    fontSize: 11.5,
    color: '#64748B',
    marginTop: 2,
    marginBottom: 14,
  },
  districtBadge: {
    backgroundColor: '#F3E8FF',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  districtBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#7E22CE',
  },
  barGraphContainer: {
    gap: 14,
  },
  graphRow: {
    gap: 4,
  },
  cropLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cropNameMain: {
    fontSize: 13.5,
    fontWeight: '700',
    color: '#1E293B',
  },
  cropReportsCount: {
    fontSize: 12.5,
    fontWeight: '700',
    color: '#0F172A',
  },
  progressTrack: {
    height: 10,
    backgroundColor: '#F1F5F9',
    borderRadius: 5,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    borderRadius: 5,
  },
  verifiedCountRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  verifiedCountText: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '500',
  },
  riskLevelText: {
    fontSize: 11,
    fontWeight: '700',
  },
  alertsList: {
    gap: 12,
  },
  healthAlertItem: {
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    padding: 12,
    borderLeftWidth: 4,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  borderLeftRed: {
    borderLeftColor: '#DC2626',
  },
  borderLeftOrange: {
    borderLeftColor: '#D97706',
  },
  borderLeftGreen: {
    borderLeftColor: '#16A34A',
  },
  healthAlertTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  healthCropName: {
    fontSize: 14,
    fontWeight: '800',
    color: '#0F172A',
  },
  healthCropKn: {
    fontSize: 12.5,
    fontWeight: '600',
    color: '#64748B',
  },
  healthPill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  bgRedLight: {
    backgroundColor: '#FEE2E2',
  },
  bgOrangeLight: {
    backgroundColor: '#FEF3C7',
  },
  bgGreenLight: {
    backgroundColor: '#DCFCE7',
  },
  textRed: {
    color: '#DC2626',
  },
  textOrange: {
    color: '#D97706',
  },
  textGreen: {
    color: '#16A34A',
  },
  healthPillText: {
    fontSize: 11,
    fontWeight: '700',
  },
  diseaseNameText: {
    fontSize: 12.5,
    fontWeight: '700',
    color: '#334155',
    marginBottom: 2,
  },
  diseaseStatsText: {
    fontSize: 11.5,
    color: '#64748B',
    lineHeight: 16,
  },
  quickAdvisoryTriggerBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 8,
    alignSelf: 'flex-start',
    backgroundColor: '#F3E8FF',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
  },
  quickAdvisoryTriggerText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#7E22CE',
  },
  weatherRiskList: {
    gap: 12,
  },
  weatherItemCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  weatherItemTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 6,
  },
  weatherDistrict: {
    fontSize: 13.5,
    fontWeight: '800',
    color: '#0F172A',
  },
  weatherCondition: {
    fontSize: 11.5,
    color: '#0284C7',
    fontWeight: '600',
    marginTop: 1,
  },
  weatherRiskBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  weatherRiskBadgeText: {
    fontSize: 10,
    fontWeight: '800',
  },
  weatherAdvisoryText: {
    fontSize: 12,
    color: '#475569',
    lineHeight: 17,
  },
  createAlertFromWeatherBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 10,
    alignSelf: 'flex-start',
    backgroundColor: '#EFF6FF',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#BFDBFE',
  },
  createAlertFromWeatherBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#2563EB',
  },
  newAlertSmallBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#F3E8FF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  newAlertSmallBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#7E22CE',
  },
  publishedAlertCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 6,
  },
  publishedAlertHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  publishedAlertTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0F172A',
  },
  publishedAlertTarget: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
    fontWeight: '500',
  },
  broadcastPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  broadcastPillText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#16A34A',
  },
  publishedAlertMsg: {
    fontSize: 12,
    color: '#334155',
    lineHeight: 17,
  },
  publishedAlertFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
  },
  publishedAlertFooterText: {
    fontSize: 11,
    color: '#64748B',
  },
  publishedAlertTime: {
    fontSize: 10.5,
    color: '#94A3B8',
  },
  readOnlyBadge: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 4,
  },
  readOnlyBadgeText: {
    fontSize: 10.5,
    fontWeight: '600',
    color: '#64748B',
  },
  marketList: {
    gap: 8,
  },
  marketItemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  marketCropName: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F172A',
  },
  marketNameSub: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 1,
  },
  marketPriceText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#059669',
  },
  marketTrendText: {
    fontSize: 11,
    fontWeight: '700',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContainer: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
    padding: 18,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  modalTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
  },
  modalSub: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 1,
  },
  closeBtn: {
    padding: 4,
  },
  modalForm: {
    marginTop: 14,
  },
  formGroup: {
    marginBottom: 12,
  },
  formLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#334155',
    marginBottom: 6,
  },
  inputField: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 9,
    fontSize: 13,
    color: '#0F172A',
  },
  textArea: {
    height: 80,
  },
  flowCard: {
    backgroundColor: '#F1F5F9',
    borderRadius: 8,
    padding: 10,
    marginBottom: 16,
  },
  flowTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: '#475569',
    marginBottom: 2,
  },
  flowStep: {
    fontSize: 11,
    color: '#334155',
  },
  modalActionRow: {
    flexDirection: 'row',
    gap: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
  },
  cancelBtn: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  cancelBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#475569',
  },
  confirmPublishBtn: {
    flex: 2,
    backgroundColor: '#0F6E56',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 12,
    borderRadius: 8,
  },
  confirmPublishBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
