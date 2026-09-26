import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Header } from '../../components/common/Header';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import {
  FarmerComprehensiveAdvisoryResponse,
  RegisteredFarmerCrop,
  fetchFarmerComprehensiveAdvisory,
  fetchFarmerAdvisoriesHistory,
  fetchFarmerCrops,
} from '../../services/advisoryApi';
import { AdvisoryCard } from '../../components/advisory/AdvisoryCard';
import { AdvisoryDetailModal } from '../../components/advisory/AdvisoryDetailModal';
import {
  Sprout,
  MapPin,
  RefreshCw,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  CloudSun,
  History,
  Info,
} from 'lucide-react-native';

export const AdvisoryScreen: React.FC = () => {
  const navigation = useNavigation<any>();
  const { user } = useAuth();
  const { language } = useLanguage();

  const [registeredCrops, setRegisteredCrops] = useState<RegisteredFarmerCrop[]>([]);
  const [selectedCropCode, setSelectedCropCode] = useState<string>('arecanut');
  const [selectedCropId, setSelectedCropId] = useState<string | undefined>(undefined);

  const [activeAdvisory, setActiveAdvisory] = useState<FarmerComprehensiveAdvisoryResponse | null>(null);
  const [historyAdvisories, setHistoryAdvisories] = useState<FarmerComprehensiveAdvisoryResponse[]>([]);
  const [showHistory, setShowHistory] = useState<boolean>(false);

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedDetailAdvisory, setSelectedDetailAdvisory] = useState<FarmerComprehensiveAdvisoryResponse | null>(null);
  const [modalVisible, setModalVisible] = useState<boolean>(false);

  // Load farmer crops on mount
  useEffect(() => {
    let isMounted = true;
    const loadCrops = async () => {
      if (user?.id) {
        try {
          const crops = await fetchFarmerCrops(user.id, user.phone);
          if (isMounted && crops.length > 0) {
            setRegisteredCrops(crops);
            const primary = crops.find((c) => c.is_primary) || crops[0];
            setSelectedCropCode(primary.crop?.code || 'arecanut');
            setSelectedCropId(primary.id);
          }
        } catch {
          // Fall back gracefully to defaults
        }
      }
    };
    loadCrops();
    return () => {
      isMounted = false;
    };
  }, [user?.id]);

  // Load advisory data
  const loadAdvisoryData = useCallback(
    async (isForceRefresh: boolean = false) => {
      try {
        setError(null);
        if (!isForceRefresh) {
          setLoading(true);
        }

        const farmerId = user?.id;
        const villageId = user?.villageId || 'V001';
        const phone = user?.phone;

        // 1. Fetch current authoritative advisory
        const primaryData = await fetchFarmerComprehensiveAdvisory(
          farmerId,
          selectedCropCode,
          villageId,
          language,
          isForceRefresh,
          selectedCropId,
          phone
        );

        setActiveAdvisory(primaryData);

        // 2. Fetch history if authenticated farmer
        if (farmerId) {
          const hist = await fetchFarmerAdvisoriesHistory(farmerId, 10, phone);
          setHistoryAdvisories(hist);
        }
      } catch (err: any) {
        console.log('[AdvisoryScreen] Error fetching advisory:', err?.message || String(err));
        setError('ಸಲಹೆಗಳನ್ನು ಪಡೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ');
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [user?.id, user?.villageId, user?.phone, selectedCropCode, selectedCropId, language]
  );

  useEffect(() => {
    loadAdvisoryData(false);
  }, [loadAdvisoryData]);

  // Pull-to-refresh handler
  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadAdvisoryData(true);
  }, [loadAdvisoryData]);

  // Filter crops
  const handleCropSelect = (cropCode: string, cropRelId?: string) => {
    setSelectedCropCode(cropCode);
    setSelectedCropId(cropRelId);
  };

  // Open detail modal
  const handleCardPress = (adv: FarmerComprehensiveAdvisoryResponse) => {
    setSelectedDetailAdvisory(adv);
    setModalVisible(true);
  };

  // Format last updated string
  const formatLastUpdated = (dtStr?: string) => {
    if (!dtStr) return 'ಇತ್ತೀಚೆಗೆ';
    try {
      const d = new Date(dtStr);
      return d.toLocaleDateString('kn-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dtStr;
    }
  };

  // Determine active vs historical lists
  const isPrimaryActive =
    activeAdvisory &&
    (activeAdvisory.status === 'ACTIVE' || !activeAdvisory.status) &&
    activeAdvisory.status !== 'no_active_advisory';

  // Other active advisories from history if any
  const otherActiveAdvisories = historyAdvisories.filter(
    (a) =>
      a.advisory_id !== activeAdvisory?.advisory_id &&
      a.status === 'ACTIVE'
  );

  // Past / Superseded advisories
  const pastAdvisories = historyAdvisories.filter(
    (a) => a.status === 'SUPERSEDED' || a.status === 'EXPIRED'
  );

  return (
    <View style={styles.screenContainer}>
      {/* 1. App Top Header */}
      <Header showVillage={true} />

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={[Colors.primary]}
            tintColor={Colors.primary}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* 2. Farmer Advisory Title Banner */}
        <View style={styles.heroBanner}>
          <View style={styles.heroTitleRow}>
            <View style={styles.heroIconCircle}>
              <Sprout size={22} color="#FFFFFF" strokeWidth={2.4} />
            </View>
            <View style={styles.heroTitles}>
              <Text style={styles.heroTitle}>ಸಲಹೆ</Text>
              <Text style={styles.heroSubtitle}>ನಿಮ್ಮ ಬೆಳೆಗೆ ಇಂದಿನ ಕೃಷಿ ಸಲಹೆಗಳು</Text>
            </View>
          </View>

          {/* Crop Filters & Location Badge */}
          <View style={styles.controlsRow}>
            {/* Crop Selector Pills */}
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.cropFilterList}
            >
              {registeredCrops.length > 0 ? (
                registeredCrops.map((c) => {
                  const isSelected = selectedCropCode === c.crop.code;
                  return (
                    <TouchableOpacity
                      key={c.id}
                      activeOpacity={0.8}
                      onPress={() => handleCropSelect(c.crop.code, c.id)}
                      style={[styles.cropChip, isSelected && styles.cropChipActive]}
                    >
                      <Text style={[styles.cropChipText, isSelected && styles.cropChipTextActive]}>
                        {c.crop.name_kn || c.crop.name_en}
                      </Text>
                      {c.is_primary && (
                        <View style={[styles.primaryDot, isSelected && styles.primaryDotActive]} />
                      )}
                    </TouchableOpacity>
                  );
                })
              ) : (
                <>
                  <TouchableOpacity
                    activeOpacity={0.8}
                    onPress={() => handleCropSelect('arecanut')}
                    style={[styles.cropChip, selectedCropCode === 'arecanut' && styles.cropChipActive]}
                  >
                    <Text style={[styles.cropChipText, selectedCropCode === 'arecanut' && styles.cropChipTextActive]}>
                      ಅಡಿಕೆ
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    activeOpacity={0.8}
                    onPress={() => handleCropSelect('paddy')}
                    style={[styles.cropChip, selectedCropCode === 'paddy' && styles.cropChipActive]}
                  >
                    <Text style={[styles.cropChipText, selectedCropCode === 'paddy' && styles.cropChipTextActive]}>
                      ಭತ್ತ
                    </Text>
                  </TouchableOpacity>
                </>
              )}
            </ScrollView>

            {/* Location Badge */}
            <View style={styles.locationChip}>
              <MapPin size={12} color={Colors.primary} />
              <Text style={styles.locationChipText} numberOfLines={1}>
                {user?.villageNameKn || user?.villageName || 'ಉಜಿರೆ'}
              </Text>
            </View>
          </View>
        </View>

        {/* 3. Loading State */}
        {loading && !refreshing && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingText}>ಸಲಹೆಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...</Text>
          </View>
        )}

        {/* 4. Error State */}
        {!loading && error && (
          <View style={styles.errorContainer}>
            <AlertTriangle size={36} color={Colors.alertHigh} strokeWidth={2} />
            <Text style={styles.errorTitle}>⚠️ ಸಲಹೆಗಳನ್ನು ಪಡೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ</Text>
            <Text style={styles.errorSubtitle}>ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.</Text>
            <TouchableOpacity
              style={styles.retryButton}
              activeOpacity={0.8}
              onPress={() => loadAdvisoryData(true)}
            >
              <RefreshCw size={16} color="#FFFFFF" />
              <Text style={styles.retryButtonText}>ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* 5. Main Content: Active Advisories */}
        {!loading && !error && (
          <>
            {isPrimaryActive ? (
              <View style={styles.advisorySection}>
                <View style={styles.sectionHeadingRow}>
                  <Text style={styles.sectionHeading}>ಪ್ರಸ್ತುತ ಸಕ್ರಿಯ ಸಲಹೆ</Text>
                  <Text style={styles.sectionSubheading}>ACTIVE ADVISORY</Text>
                </View>

                {/* Primary Advisory Card */}
                {activeAdvisory && (
                  <AdvisoryCard
                    advisory={activeAdvisory}
                    onPress={() => handleCardPress(activeAdvisory)}
                  />
                )}

                {/* Additional Active Advisories if any */}
                {otherActiveAdvisories.length > 0 && (
                  <View style={styles.otherAdvisoriesContainer}>
                    <Text style={styles.subSectionTitle}>ಇತರ ಸಕ್ರಿಯ ಸಲಹೆಗಳು</Text>
                    {otherActiveAdvisories.map((adv, idx) => (
                      <AdvisoryCard
                        key={adv.advisory_id || idx}
                        advisory={adv}
                        onPress={() => handleCardPress(adv)}
                      />
                    ))}
                  </View>
                )}

                {/* Last Updated Timestamp */}
                <View style={styles.lastUpdatedRow}>
                  <Text style={styles.lastUpdatedText}>
                    ಕೊನೆಯ ನವೀಕರಣ:{' '}
                    {formatLastUpdated(activeAdvisory?.generated_at)}
                  </Text>
                </View>
              </View>
            ) : (
              /* Uncertain / No active advisory empty state */
              <View style={styles.emptyContainer}>
                <View style={styles.emptyIconCircle}>
                  <Sprout size={36} color={Colors.primary} strokeWidth={2} />
                </View>
                <Text style={styles.emptyTitle}>🌱 ಪ್ರಸ್ತುತ ಯಾವುದೇ ಪ್ರಮುಖ ಸಲಹೆ ಇಲ್ಲ</Text>
                <Text style={styles.emptySubtitle}>
                  ಹೊಸ ಹವಾಮಾನ ಅಥವಾ ಬೆಳೆ ಮಾಹಿತಿ ಲಭ್ಯವಾದಾಗ ಸಲಹೆ ಇಲ್ಲಿ ಕಾಣಿಸುತ್ತದೆ.
                </Text>
                <TouchableOpacity
                  style={styles.emptyRefreshBtn}
                  activeOpacity={0.8}
                  onPress={() => loadAdvisoryData(true)}
                >
                  <RefreshCw size={14} color={Colors.primary} />
                  <Text style={styles.emptyRefreshBtnText}>ಮಾಹಿತಿ ನವೀಕರಿಸಿ</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* 6. Weather Screen Shortcut Banner */}
            <TouchableOpacity
              style={styles.weatherShortcutCard}
              activeOpacity={0.85}
              onPress={() => navigation.navigate('WeatherDetails')}
            >
              <View style={styles.weatherShortcutLeft}>
                <View style={styles.weatherIconCircle}>
                  <CloudSun size={20} color="#0369A1" strokeWidth={2.2} />
                </View>
                <View>
                  <Text style={styles.weatherShortcutTitle}>ಹವಾಮಾನ ಆಧಾರಿತ ಮಾಹಿತಿ</Text>
                  <Text style={styles.weatherShortcutSubtitle}>ತಾಪಮಾನ, ಮಳೆ ಮತ್ತು ಆರ್ದ್ರತೆಯ ವಿವರಗಳು</Text>
                </View>
              </View>
              <Text style={styles.weatherShortcutAction}>ವೀಕ್ಷಿಸಿ ›</Text>
            </TouchableOpacity>

            {/* 7. Past Advisories / History Section */}
            {pastAdvisories.length > 0 && (
              <View style={styles.historyContainer}>
                <TouchableOpacity
                  style={styles.historyHeaderToggle}
                  activeOpacity={0.8}
                  onPress={() => setShowHistory(!showHistory)}
                >
                  <View style={styles.historyHeaderLeft}>
                    <History size={16} color={Colors.textSecondary} />
                    <Text style={styles.historyHeaderText}>ಹಿಂದಿನ ಸಲಹೆಗಳು ({pastAdvisories.length})</Text>
                  </View>
                  {showHistory ? (
                    <ChevronUp size={18} color={Colors.textSecondary} />
                  ) : (
                    <ChevronDown size={18} color={Colors.textSecondary} />
                  )}
                </TouchableOpacity>

                {showHistory && (
                  <View style={styles.historyList}>
                    {pastAdvisories.map((histAdv, idx) => (
                      <AdvisoryCard
                        key={histAdv.advisory_id || idx}
                        advisory={histAdv}
                        onPress={() => handleCardPress(histAdv)}
                        compact={true}
                      />
                    ))}
                  </View>
                )}
              </View>
            )}
          </>
        )}
      </ScrollView>

      {/* 8. Advisory Detail Modal */}
      <AdvisoryDetailModal
        visible={modalVisible}
        advisory={selectedDetailAdvisory}
        onClose={() => setModalVisible(false)}
        onViewWeather={() => navigation.navigate('WeatherDetails')}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  screenContainer: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    paddingHorizontal: Spacing.md,
    paddingTop: Spacing.sm,
    paddingBottom: Spacing.xxl + 20,
  },
  heroBanner: {
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  heroTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: Spacing.md,
  },
  heroIconCircle: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 3,
  },
  heroTitles: {
    flex: 1,
  },
  heroTitle: {
    ...Typography.title1,
    fontSize: 22,
    fontWeight: '900',
    color: Colors.textPrimary,
  },
  heroSubtitle: {
    ...Typography.body,
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 1,
  },
  controlsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: Spacing.xs,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    gap: 8,
  },
  cropFilterList: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  cropChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  cropChipActive: {
    backgroundColor: Colors.primaryLight,
    borderColor: Colors.primary,
  },
  cropChipText: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.textSecondary,
  },
  cropChipTextActive: {
    color: Colors.primaryDark,
  },
  primaryDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#9CA3AF',
  },
  primaryDotActive: {
    backgroundColor: Colors.primary,
  },
  locationChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#ECFDF5',
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: '#A7F3D0',
  },
  locationChipText: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.primaryDark,
  },
  loadingContainer: {
    paddingVertical: Spacing.xxxl,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: {
    ...Typography.bodyLarge,
    fontSize: 14,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  errorContainer: {
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.lg,
    padding: Spacing.xl,
    alignItems: 'center',
    marginVertical: Spacing.md,
    borderWidth: 1,
    borderColor: '#FCA5A5',
    gap: 8,
  },
  errorTitle: {
    ...Typography.title2,
    color: Colors.alertHigh,
    fontWeight: '800',
    textAlign: 'center',
  },
  errorSubtitle: {
    fontSize: 13,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  retryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: Colors.primary,
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm + 2,
    borderRadius: BorderRadius.md,
    marginTop: Spacing.sm,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  advisorySection: {
    marginTop: Spacing.xs,
  },
  sectionHeadingRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    marginBottom: Spacing.sm,
    paddingHorizontal: 2,
  },
  sectionHeading: {
    fontSize: 15,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  sectionSubheading: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.textMuted,
    letterSpacing: 0.5,
  },
  otherAdvisoriesContainer: {
    marginTop: Spacing.md,
  },
  subSectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
  },
  lastUpdatedRow: {
    alignItems: 'center',
    marginVertical: Spacing.sm,
  },
  lastUpdatedText: {
    fontSize: 11,
    color: Colors.textMuted,
    fontWeight: '500',
  },
  emptyContainer: {
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.lg,
    padding: Spacing.xxl,
    alignItems: 'center',
    marginVertical: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
    gap: 8,
  },
  emptyIconCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: Colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  emptyTitle: {
    ...Typography.title2,
    color: Colors.textPrimary,
    fontWeight: '800',
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: 13,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 19,
    paddingHorizontal: Spacing.md,
  },
  emptyRefreshBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: Colors.primaryLight,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.full,
    marginTop: Spacing.sm,
  },
  emptyRefreshBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.primaryDark,
  },
  weatherShortcutCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#F0F9FF',
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: '#BAE6FD',
    marginVertical: Spacing.sm,
  },
  weatherShortcutLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  weatherIconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#E0F2FE',
    alignItems: 'center',
    justifyContent: 'center',
  },
  weatherShortcutTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0369A1',
  },
  weatherShortcutSubtitle: {
    fontSize: 11,
    color: '#0284C7',
    marginTop: 1,
  },
  weatherShortcutAction: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0284C7',
  },
  historyContainer: {
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    marginTop: Spacing.sm,
    overflow: 'hidden',
  },
  historyHeaderToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: Spacing.md,
  },
  historyHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  historyHeaderText: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.textSecondary,
  },
  historyList: {
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    paddingTop: Spacing.sm,
  },
});
