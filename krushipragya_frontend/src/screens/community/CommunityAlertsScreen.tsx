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
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  fetchCommunityAlerts,
  CommunityAlertItem,
} from '../../services/communityApi';
import {
  AlertTriangle,
  CloudRain,
  ShieldAlert,
  Users,
  MapPin,
  Clock,
  Sparkles,
  ChevronRight,
  Info,
} from 'lucide-react-native';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

type AlertCategoryFilter = 'ALL' | 'GOVERNMENT' | 'COMMUNITY' | 'WEATHER';

interface CommunityAlertsScreenProps {
  navigation: any;
}

export const CommunityAlertsScreen: React.FC<CommunityAlertsScreenProps> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { language } = useLanguage();
  const isKn = language === 'kn';

  const [alerts, setAlerts] = useState<CommunityAlertItem[]>([]);
  const [filter, setFilter] = useState<AlertCategoryFilter>('ALL');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadAlerts = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchCommunityAlerts();
      setAlerts(data);
    } catch (e) {
      console.warn('Failed to load community alerts:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  const onRefresh = () => {
    setRefreshing(true);
    loadAlerts();
  };

  const filteredAlerts = alerts.filter((a) => {
    if (filter === 'ALL') return true;
    return a.category === filter;
  });

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.iconCircle}>
            <AlertTriangle size={20} color="#16A34A" />
          </View>
          <View>
            <Text style={styles.headerTitle}>
              {isKn ? 'ಸ್ಥಳೀಯ ಕೃಷಿ ಎಚ್ಚರಿಕೆಗಳು' : 'Local Agricultural Alerts'}
            </Text>
            <Text style={styles.headerSub}>
              {isKn ? 'ಸರ್ಕಾರಿ ನಿರ್ದೇಶನಗಳು • ಸಮುದಾಯ ವೀಕ್ಷಣೆಗಳು • ಹವಾಮಾನ' : 'Official Directives & Cluster Surveillance Alerts'}
            </Text>
          </View>
        </View>
      </View>

      {/* Category Filter Tabs (Section 7) */}
      <View style={styles.filterTabs}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterScroll}>
          <TouchableOpacity
            style={[styles.filterChip, filter === 'ALL' && styles.filterChipActive]}
            onPress={() => setFilter('ALL')}
          >
            <Text style={[styles.filterChipText, filter === 'ALL' && styles.filterChipTextActive]}>
              {isKn ? 'ಎಲ್ಲಾ ಸೂಚನೆಗಳು' : 'All Alerts'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.filterChip, filter === 'GOVERNMENT' && styles.filterChipActiveGovt]}
            onPress={() => setFilter('GOVERNMENT')}
          >
            <Text style={[styles.filterChipText, filter === 'GOVERNMENT' && styles.textWhite]}>
              🏛 {isKn ? 'ಸರ್ಕಾರಿ ಅಧಿಕೃತ' : 'Govt Directives'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.filterChip, filter === 'COMMUNITY' && styles.filterChipActiveComm]}
            onPress={() => setFilter('COMMUNITY')}
          >
            <Text style={[styles.filterChipText, filter === 'COMMUNITY' && styles.textWhite]}>
              👥 {isKn ? 'ಸಮುದಾಯ ಕ್ಲಸ್ಟರ್' : 'Community Clusters'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.filterChip, filter === 'WEATHER' && styles.filterChipActiveWeather]}
            onPress={() => setFilter('WEATHER')}
          >
            <Text style={[styles.filterChipText, filter === 'WEATHER' && styles.textWhite]}>
              🌧 {isKn ? 'ಹವಾಮಾನ' : 'Weather'}
            </Text>
          </TouchableOpacity>
        </ScrollView>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.primary]} />}
      >
        {/* Distinction Banner (Section 7) */}
        <View style={styles.infoBanner}>
          <Info size={15} color="#16A34A" />
          <Text style={styles.infoBannerText}>
            {isKn
              ? 'ಸರ್ಕಾರಿ ಅಧಿಕೃತ ಸೂಚನೆಗಳು (🏛) ಇಲಾಖೆಯಿಂದ ನೇರವಾಗಿ ಬಂದಿರುತ್ತವೆ. ಸಮುದಾಯ ವೀಕ್ಷಣೆಗಳು (👥) ಸ್ಥಳೀಯ ರೈತರ ಸಾಕ್ಷ್ಯಾಧಾರಗಳ ಕ್ಲಸ್ಟರ್ ಆಗಿರುತ್ತವೆ.'
              : 'Official Government Alerts (🏛) are statutory departmental advisories. Community Observations (👥) aggregate local farmer field evidence.'}
          </Text>
        </View>

        {loading && !refreshing ? (
          <View style={styles.centerLoading}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingText}>
              {isKn ? 'ಎಚ್ಚರಿಕೆಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...' : 'Loading community alerts...'}
            </Text>
          </View>
        ) : filteredAlerts.length === 0 ? (
          <View style={styles.emptyCard}>
            <AlertTriangle size={40} color="#CBD5E1" />
            <Text style={styles.emptyTitle}>
              {isKn ? 'ಯಾವುದೇ ಸಕ್ರಿಯ ಎಚ್ಚರಿಕೆಗಳಿಲ್ಲ' : 'No Active Alerts'}
            </Text>
            <Text style={styles.emptySub}>
              {isKn ? 'ನಿಮ್ಮ ಗ್ರಾಮ ವ್ಯಾಪ್ತಿಯಲ್ಲಿ ಬೆಳೆಗಳು ಸುರಕ್ಷಿತವಾಗಿವೆ.' : 'No urgent alerts recorded for your village.'}
            </Text>
          </View>
        ) : (
          <View style={styles.alertsList}>
            {filteredAlerts.map((item) => {
              const isGovt = item.category === 'GOVERNMENT';
              const isComm = item.category === 'COMMUNITY';
              const isWeather = item.category === 'WEATHER';

              return (
                <View
                  key={item.id}
                  style={[
                    styles.alertCard,
                    isGovt ? styles.borderGovt : isComm ? styles.borderComm : styles.borderWeather,
                  ]}
                >
                  <View style={styles.alertCardTop}>
                    <View
                      style={[
                        styles.categoryBadge,
                        isGovt
                          ? styles.bgPurpleLight
                          : isComm
                          ? styles.bgTealLight
                          : styles.bgSkyLight,
                      ]}
                    >
                      <Text
                        style={[
                          styles.categoryBadgeText,
                          isGovt
                            ? styles.textPurple
                            : isComm
                            ? styles.textTeal
                            : styles.textSky,
                        ]}
                      >
                        {item.category_label}
                      </Text>
                    </View>

                    <Text style={styles.timestampText}>{item.timestamp}</Text>
                  </View>

                  <Text style={styles.alertTitleText}>
                    {isKn ? item.title_kn : item.title}
                  </Text>

                  <Text style={styles.alertMsgText}>{item.message}</Text>

                  <View style={styles.alertMetaRow}>
                    {item.affected_crop && (
                      <Text style={styles.affectedCropText}>
                        🌾 {item.affected_crop}
                      </Text>
                    )}
                    <Text style={styles.locationMetaText}>
                      📍 {item.village}
                    </Text>
                  </View>
                </View>
              );
            })}
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
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
  headerSub: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '500',
    marginTop: 1,
  },
  filterTabs: {
    backgroundColor: '#FFFFFF',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  filterScroll: {
    paddingHorizontal: 16,
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#F1F5F9',
  },
  filterChipActive: {
    backgroundColor: '#0F6E56',
  },
  filterChipActiveGovt: {
    backgroundColor: '#7E22CE',
  },
  filterChipActiveComm: {
    backgroundColor: '#0D9488',
  },
  filterChipActiveWeather: {
    backgroundColor: '#0284C7',
  },
  filterChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#475569',
  },
  filterChipTextActive: {
    color: '#FFFFFF',
    fontWeight: '800',
  },
  textWhite: {
    color: '#FFFFFF',
    fontWeight: '800',
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 36,
    gap: 12,
  },
  infoBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#E1F5EE',
    borderRadius: 10,
    padding: 10,
    borderWidth: 1,
    borderColor: '#A7F3D0',
  },
  infoBannerText: {
    fontSize: 11,
    color: '#166534',
    flex: 1,
    lineHeight: 16,
  },
  centerLoading: {
    paddingVertical: 50,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  loadingText: {
    fontSize: 13,
    color: '#64748B',
  },
  emptyCard: {
    paddingVertical: 60,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#475569',
  },
  emptySub: {
    fontSize: 12,
    color: '#94A3B8',
  },
  alertsList: {
    gap: 12,
  },
  alertCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    gap: 8,
  },
  borderGovt: {
    borderLeftWidth: 4,
    borderLeftColor: '#7E22CE',
  },
  borderComm: {
    borderLeftWidth: 4,
    borderLeftColor: '#0D9488',
  },
  borderWeather: {
    borderLeftWidth: 4,
    borderLeftColor: '#0284C7',
  },
  alertCardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  categoryBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  bgPurpleLight: {
    backgroundColor: '#F3E8FF',
  },
  bgTealLight: {
    backgroundColor: '#CCFBF1',
  },
  bgSkyLight: {
    backgroundColor: '#E0F2FE',
  },
  textPurple: {
    color: '#7E22CE',
  },
  textTeal: {
    color: '#0D9488',
  },
  textSky: {
    color: '#0284C7',
  },
  categoryBadgeText: {
    fontSize: 10.5,
    fontWeight: '800',
  },
  timestampText: {
    fontSize: 11,
    color: '#94A3B8',
  },
  alertTitleText: {
    fontSize: 14.5,
    fontWeight: '800',
    color: '#0F172A',
  },
  alertMsgText: {
    fontSize: 12.5,
    color: '#334155',
    lineHeight: 18,
  },
  alertMetaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
  },
  affectedCropText: {
    fontSize: 11.5,
    fontWeight: '700',
    color: '#0F766E',
  },
  locationMetaText: {
    fontSize: 11,
    color: '#64748B',
  },
});
