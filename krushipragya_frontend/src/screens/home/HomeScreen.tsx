import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Dimensions,
  ActivityIndicator,
  NativeSyntheticEvent,
  NativeScrollEvent,
} from 'react-native';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { useReports } from '../../context/ReportContext';
import { Header } from '../../components/common/Header';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import { fetchLiveWeather, LiveWeather } from '../../services/api';
import {
  Camera,
  CloudSun,
  CloudRain,
  TrendingUp,
  Landmark,
  ArrowRight,
  Sparkles,
  Users,
  BellRing,
  MapPin,
  RefreshCw,
  Sprout,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react-native';

const SCREEN_WIDTH = Dimensions.get('window').width;
const CARD_WIDTH = SCREEN_WIDTH - Spacing.md * 2;

export const HomeScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const { language } = useLanguage();
  const { user } = useAuth();
  const { reports } = useReports();
  const isKn = language === 'kn';

  // Live Weather state from real backend API
  const [weather, setWeather] = useState<LiveWeather | null>(null);
  const [isLoadingWeather, setIsLoadingWeather] = useState(true);

  // Hero Slider active page index
  const [activeSlideIndex, setActiveSlideIndex] = useState(0);
  const sliderRef = useRef<ScrollView>(null);

  // Fetch real live weather on mount or village change
  const loadWeather = async () => {
    setIsLoadingWeather(true);
    try {
      const data = await fetchLiveWeather(user?.villageId || 'V001');
      setWeather(data);
    } catch {
      setWeather(null);
    } finally {
      setIsLoadingWeather(false);
    }
  };

  useEffect(() => {
    loadWeather();
  }, [user?.villageId]);

  const handleBroadcastAlert = () => {
    const villageName = isKn
      ? (user?.villageNameKn || 'ಉಜಿರೆ')
      : (user?.villageName || 'Ujire');

    Alert.alert(
      isKn ? 'ಗ್ರಾಮ ಎಚ್ಚರಿಕೆ ರವಾನೆಯಾಗಿದೆ 🔔' : 'Village Alert Broadcasted 🔔',
      isKn
        ? `${villageName} ಗ್ರಾಮದ ನೆರೆಹೊರೆಯ ರೈತರಿಗೆ ಬೆಳೆ ಎಚ್ಚರಿಕೆ ಸಂದೇಶ ತಲುಪಿದೆ.`
        : `Crop health alert broadcasted to neighbor farms in ${villageName}.`
    );
  };

  const handleSliderScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const slideIndex = Math.round(event.nativeEvent.contentOffset.x / CARD_WIDTH);
    if (slideIndex >= 0 && slideIndex !== activeSlideIndex) {
      setActiveSlideIndex(slideIndex);
    }
  };

  // Hero Carousel Slides (Primary Slide is that EXACT dark green card)
  const HERO_SLIDES = [
    {
      id: 'crop_ai',
      badgeEn: 'AI Crop Doctor',
      badgeKn: 'AI ಬೆಳೆ ತಪಾಸಣೆ',
      titleEn: 'Scan Crop Disease',
      titleKn: 'ರೋಗ ಪತ್ತೆ ಹಚ್ಚಿ',
      subEn: 'Snap photo for instant remedy',
      subKn: 'ಫೋಟೋ ತೆಗೆದು ತಕ್ಷಣ ಪರಿಹಾರ ಪಡೆಯಿರಿ',
      Icon: Camera,
      bg: '#0F5132',
      iconBoxBg: '#16A34A',
      onPress: () => navigation.navigate('ReportTab', { screen: 'CropSelect' }),
    },
    {
      id: 'weather',
      badgeEn: 'Weather Advisory',
      badgeKn: 'ಹವಾಮಾನ ಸಲಹೆ',
      titleEn: 'Rain & Spray Radar',
      titleKn: 'ಮಳೆ & ಸಿಂಪರಣೆ ಮುನ್ಸೂಚನೆ',
      subEn: '7-day forecast & scientific spray advice',
      subKn: 'ವೈಜ್ಞಾನಿಕ ಕೃಷಿ ಮುನ್ಸೂಚನೆ ಪರಿಶೀಲಿಸಿ',
      Icon: CloudSun,
      iconBoxBg: '#2563EB',
      bg: '#1E3A8A',
      onPress: () => navigation.navigate('WeatherTab'),
    },
    {
      id: 'market',
      badgeEn: 'Mandi Rates',
      badgeKn: 'ಮಾರುಕಟ್ಟೆ ಧಾರಣೆ',
      titleEn: 'Live APMC Mandi Rates',
      titleKn: 'ಎಪಿಎಂಸಿ ಮಾರುಕಟ್ಟೆ ದರಗಳು',
      subEn: 'Compare prices across nearby mandis',
      subKn: 'ಅಡಿಕೆ, ಕಾಳುಮೆಣಸು ತಾಜಾ ಬೆಲೆಗಳು',
      Icon: TrendingUp,
      iconBoxBg: '#15803D',
      bg: '#14532D',
      onPress: () => navigation.navigate('MarketTab'),
    },
    {
      id: 'schemes',
      badgeEn: 'Govt Schemes',
      badgeKn: 'ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು',
      titleEn: 'Farmer Subsidies & Benefits',
      titleKn: 'ರೈತ ಕಲ್ಯಾಣ ಸಬ್ಸಿಡಿ ಮಾಹಿತಿ',
      subEn: 'Explore official subsidy schemes',
      subKn: 'ಅರ್ಹ ಯೋಜನೆಗಳನ್ನು ವೀಕ್ಷಿಸಿ',
      Icon: Landmark,
      iconBoxBg: '#7E22CE',
      bg: '#581C87',
      onPress: () => navigation.navigate('SchemesTab'),
    },
  ];

  // Up to 3 Community / Village Crop Status Cards (from real reports)
  const displayReports = reports && reports.length > 0 ? reports.slice(0, 3) : [];

  return (
    <View style={styles.container}>
      {/* 1. TOP HEADER (Matching Hand Sketch) */}
      <Header />

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* 2. LIVE WEATHER ROW (Immediately below header) */}
        <View style={styles.weatherCard}>
          {isLoadingWeather ? (
            <View style={styles.weatherLoadingRow}>
              <ActivityIndicator size="small" color={Colors.primary} />
              <Text style={styles.weatherLoadingText}>
                {isKn ? 'ಹವಾಮಾನ ಮಾಹಿತಿ ಲೋಡ್ ಆಗುತ್ತಿದೆ...' : 'Fetching live weather...'}
              </Text>
            </View>
          ) : weather ? (
            <View style={styles.weatherMainRow}>
              {/* Left Column: Location & Live Weather label */}
              <View style={styles.weatherLeftCol}>
                <View style={styles.locationTitleRow}>
                  <MapPin size={13} color={Colors.primary} />
                  <Text style={styles.locationText} numberOfLines={1}>
                    {isKn ? weather.locationLineKn : weather.locationLine}
                  </Text>
                </View>
                <Text style={styles.liveWeatherTag}>
                  {isKn ? 'ಲೈವ್ ಹವಾಮಾನ (Live Weather)' : 'Live Weather'}
                </Text>
              </View>

              {/* Right Column: Temperature & Condition Icon */}
              <View style={styles.weatherRightCol}>
                <View style={styles.tempBadgeRow}>
                  <Text style={styles.tempValue}>{weather.temperature}°C</Text>
                  {weather.condition.toLowerCase().includes('rain') ? (
                    <CloudRain size={24} color="#0284C7" strokeWidth={2.4} />
                  ) : (
                    <CloudSun size={24} color="#D97706" strokeWidth={2.4} />
                  )}
                </View>
                <Text style={styles.conditionText} numberOfLines={1}>
                  {isKn ? weather.conditionKn : weather.condition}
                </Text>
              </View>
            </View>
          ) : (
            /* Proper unavailable state if real API is unreachable */
            <View style={styles.weatherUnavailableRow}>
              <View style={styles.weatherLeftCol}>
                <Text style={styles.locationText}>
                  {isKn
                    ? `${user?.villageNameKn || 'ಉಜಿರೆ'} • ಹವಾಮಾನ`
                    : `${user?.villageName || 'Ujire'} • Weather`}
                </Text>
                <Text style={styles.weatherUnavailableSub}>
                  {isKn ? 'ಹವಾಮಾನ ಮಾಹಿತಿ ಲಭ್ಯವಿಲ್ಲ' : 'Weather advisory unavailable'}
                </Text>
              </View>
              <TouchableOpacity
                style={styles.retryBtn}
                onPress={loadWeather}
                activeOpacity={0.7}
              >
                <RefreshCw size={13} color={Colors.primary} />
                <Text style={styles.retryBtnText}>{isKn ? 'ಮರುಪ್ರಯತ್ನ' : 'Retry'}</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* 3. HERO / FEATURE SLIDER (Matching Hand Sketch Large Card) */}
        <View style={styles.sliderContainer}>
          <ScrollView
            ref={sliderRef}
            horizontal
            pagingEnabled
            showsHorizontalScrollIndicator={false}
            onScroll={handleSliderScroll}
            scrollEventThrottle={16}
            contentContainerStyle={styles.sliderScrollContent}
          >
            {HERO_SLIDES.map((slide) => {
              const { Icon } = slide;
              return (
                <TouchableOpacity
                  key={slide.id}
                  activeOpacity={0.9}
                  onPress={slide.onPress}
                  style={[styles.heroCard, { backgroundColor: slide.bg }]}
                >
                  <View style={styles.heroRow}>
                    <View style={[styles.heroIconBox, { backgroundColor: slide.iconBoxBg }]}>
                      <Icon size={26} color="#FFFFFF" strokeWidth={2.2} />
                    </View>
                    <View style={{ flex: 1 }}>
                      <View style={styles.badgeRow}>
                        <Sparkles size={12} color="#FDE68A" />
                        <Text style={styles.badgeText}>
                          {isKn ? slide.badgeKn : slide.badgeEn}
                        </Text>
                      </View>
                      <Text style={styles.heroTitle}>
                        {isKn ? slide.titleKn : slide.titleEn}
                      </Text>
                      <Text style={styles.heroSub}>
                        {isKn ? slide.subKn : slide.subEn}
                      </Text>
                    </View>
                    <View style={styles.arrowCircle}>
                      <ArrowRight size={16} color="#FFFFFF" />
                    </View>
                  </View>
                </TouchableOpacity>
              );
            })}
          </ScrollView>

          {/* Pagination Dots (Matching Hand Sketch o • o o) */}
          <View style={styles.paginationRow}>
            {HERO_SLIDES.map((_, i) => (
              <View
                key={i}
                style={[
                  styles.dot,
                  activeSlideIndex === i ? styles.activeDot : styles.inactiveDot,
                ]}
              />
            ))}
          </View>
        </View>

        {/* 4. FARMER / COMMUNITY CROP HEALTH SECTION (Matching Hand Sketch) */}
        <View style={styles.communitySection}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionHeaderLeft}>
              <Sprout size={18} color="#15803D" strokeWidth={2.4} />
              <Text style={styles.sectionTitle}>
                {isKn ? 'ಗ್ರಾಮದ ಬೆಳೆ ಸ್ಥಿತಿ' : 'Village Crop Status'}
              </Text>
            </View>
            <TouchableOpacity
              onPress={handleBroadcastAlert}
              style={styles.alertBtn}
              activeOpacity={0.8}
            >
              <BellRing size={12} color="#FFFFFF" />
              <Text style={styles.alertBtnText}>{isKn ? 'ಎಚ್ಚರಿಸಿ' : 'Alert'}</Text>
            </TouchableOpacity>
          </View>

          {displayReports.length > 0 ? (
            /* Horizontal row of 3 cards matching sketch */
            <View style={styles.threeCardsRow}>
              {displayReports.map((report, idx) => {
                const isHealthy =
                  report.status === 'expert_verified' ||
                  (report.predictedDisease || '').toLowerCase().includes('healthy');

                return (
                  <TouchableOpacity
                    key={report.id || String(idx)}
                    activeOpacity={0.85}
                    onPress={() => navigation.navigate('ReportTab', { screen: 'ReportList' })}
                    style={styles.statusCard}
                  >
                    <Text style={styles.cardFarmerContext} numberOfLines={1}>
                      {report.proxyFor || (isKn ? `ರೈತರು #${idx + 1}` : `Farmer ${idx + 1}`)}
                    </Text>
                    <Text style={styles.cardCropName} numberOfLines={1}>
                      {isKn
                        ? (report.cropNameKn || report.crop)
                        : (report.cropNameEn || report.crop)}
                    </Text>
                    <View
                      style={[
                        styles.statusPill,
                        isHealthy ? styles.pillGreen : styles.pillAmber,
                      ]}
                    >
                      <Text
                        style={[
                          styles.statusPillText,
                          isHealthy ? { color: '#166534' } : { color: '#92400E' },
                        ]}
                      >
                        {isHealthy ? '● Good' : '▲ Alert'}
                      </Text>
                    </View>
                  </TouchableOpacity>
                );
              })}
            </View>
          ) : (
            /* Clean Empty State when no real community reports exist */
            <View style={styles.emptyCardBox}>
              <Users size={28} color="#94A3B8" />
              <Text style={styles.emptyTitle}>
                {isKn ? 'ಗ್ರಾಮದ ಯಾವುದೇ ಹೊಸ ಬೆಳೆ ವರದಿಗಳಿಲ್ಲ' : 'No Village Crop Reports Yet'}
              </Text>
              <Text style={styles.emptySub}>
                {isKn
                  ? 'ಗ್ರಾಮದಲ್ಲಿ ಪ್ರಸ್ತುತ ಸಕ್ರಿಯ ರೋಗ ಬಾಧೆಗಳ ವರದಿ ಇಲ್ಲ.'
                  : 'No active disease alerts reported in this village.'}
              </Text>
              <TouchableOpacity
                style={styles.emptyActionBtn}
                onPress={() => navigation.navigate('ReportTab', { screen: 'CropSelect' })}
                activeOpacity={0.85}
              >
                <Text style={styles.emptyActionBtnText}>
                  {isKn ? '+ ಬೆಳೆ ವರದಿ ಸಲ್ಲಿಸಿ' : '+ Submit Crop Report'}
                </Text>
              </TouchableOpacity>
            </View>
          )}
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
  scrollContent: {
    padding: Spacing.md,
    paddingBottom: 80, // Prevent content clipping behind bottom navigation bar
    gap: 14,
  },
  /* Weather Card Styles */
  weatherCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  weatherLoadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 10,
  },
  weatherLoadingText: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '600',
  },
  weatherMainRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  weatherLeftCol: {
    flex: 1,
    gap: 2,
    marginRight: 8,
  },
  locationTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  locationText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0F172A',
  },
  liveWeatherTag: {
    fontSize: 11,
    fontWeight: '600',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  weatherRightCol: {
    alignItems: 'flex-end',
    gap: 2,
  },
  tempBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  tempValue: {
    fontSize: 22,
    fontWeight: '900',
    color: '#0F172A',
  },
  conditionText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#0369A1',
  },
  weatherUnavailableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  weatherUnavailableSub: {
    fontSize: 11,
    color: '#94A3B8',
    fontWeight: '600',
    marginTop: 2,
  },
  retryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  retryBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.primaryDark,
  },

  /* Hero Slider Styles */
  sliderContainer: {
    width: '100%',
  },
  sliderScrollContent: {
    gap: 0,
  },
  heroCard: {
    width: CARD_WIDTH,
    borderRadius: BorderRadius.lg,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 5,
    elevation: 3,
  },
  heroRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  heroIconBox: {
    width: 48,
    height: 48,
    borderRadius: BorderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 2,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FDE68A',
  },
  heroTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  heroSub: {
    fontSize: 11,
    color: '#D1FAE5',
    marginTop: 2,
  },
  arrowCircle: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  paginationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 10,
  },
  dot: {
    height: 6,
    borderRadius: 3,
  },
  activeDot: {
    width: 18,
    backgroundColor: '#16A34A',
  },
  inactiveDot: {
    width: 6,
    backgroundColor: '#CBD5E1',
  },

  /* Community Crop Status Section Styles */
  communitySection: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 12,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  alertBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#DC2626',
    paddingHorizontal: 9,
    paddingVertical: 4,
    borderRadius: BorderRadius.sm,
  },
  alertBtnText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  threeCardsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  statusCard: {
    flex: 1,
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.sm,
    padding: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 4,
  },
  cardFarmerContext: {
    fontSize: 11,
    fontWeight: '700',
    color: '#0F172A',
  },
  cardCropName: {
    fontSize: 10,
    color: '#64748B',
  },
  statusPill: {
    marginTop: 3,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: BorderRadius.full,
  },
  pillGreen: {
    backgroundColor: '#DCFCE7',
  },
  pillAmber: {
    backgroundColor: '#FEF3C7',
  },
  statusPillText: {
    fontSize: 10,
    fontWeight: '800',
  },

  /* Empty Community Card Styles */
  emptyCardBox: {
    paddingVertical: 18,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  emptyTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#334155',
  },
  emptySub: {
    fontSize: 11,
    color: '#64748B',
    textAlign: 'center',
    paddingHorizontal: Spacing.md,
  },
  emptyActionBtn: {
    marginTop: 6,
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: '#86EFAC',
  },
  emptyActionBtnText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#15803D',
  },
});
