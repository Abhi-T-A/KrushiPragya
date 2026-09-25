import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Header } from '../../components/common/Header';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  Camera,
  CloudSun,
  TrendingUp,
  Landmark,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  Users,
  Droplets,
  BellRing,
} from 'lucide-react-native';

const NEIGHBOR_FARMS = [
  { id: 'n1', name: 'Manjunath H.', crop: 'Paddy', status: 'healthy', label: 'Healthy' },
  { id: 'n2', name: 'Shekar P.', crop: 'Arecanut', status: 'alert', label: 'Pest Alert' },
  { id: 'n3', name: 'Anand R.', crop: 'Pepper', status: 'healthy', label: 'Healthy' },
];

export const HomeScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const { language } = useLanguage();
  const { user } = useAuth();
  const isKn = language === 'kn';

  const handleBroadcastAlert = () => {
    Alert.alert(
      isKn ? 'ಎಚ್ಚರಿಕೆ ರವಾನೆಯಾಗಿದೆ 🔔' : 'Village Alert Sent 🔔',
      isKn ? 'ನೆರೆಹೊರೆಯ 18 ರೈತರಿಗೆ ಸಂದೇಶ ತಲುಪಿದೆ.' : 'Alert sent to 18 neighbor farms in Ujire.'
    );
  };

  return (
    <View style={styles.container}>
      <Header />

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Compact Hero Scan Button */}
        <TouchableOpacity
          activeOpacity={0.9}
          onPress={() => navigation.navigate('ReportTab', { screen: 'CropSelect' })}
          style={styles.heroCard}
        >
          <View style={styles.heroRow}>
            <View style={styles.heroIconBox}>
              <Camera size={26} color="#FFFFFF" strokeWidth={2.2} />
            </View>
            <View style={{ flex: 1 }}>
              <View style={styles.badgeRow}>
                <Sparkles size={12} color="#F59E0B" />
                <Text style={styles.badgeText}>{isKn ? 'AI ಬೆಳೆ ತಪಾಸಣೆ' : 'AI Crop Doctor'}</Text>
              </View>
              <Text style={styles.heroTitle}>{isKn ? 'ರೋಗ ಪತ್ತೆ ಹಚ್ಚಿ' : 'Scan Crop Disease'}</Text>
              <Text style={styles.heroSub}>{isKn ? 'ಫೋಟೋ ತೆಗೆದು ತಕ್ಷಣ ಪರಿಹಾರ ಪಡೆಯಿರಿ' : 'Snap photo for instant remedy'}</Text>
            </View>
            <View style={styles.arrowCircle}>
              <ArrowRight size={16} color="#FFFFFF" />
            </View>
          </View>
        </TouchableOpacity>

        {/* Short & Sweet Weather Card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <View style={styles.headerLeft}>
              <CloudSun size={18} color="#2563EB" />
              <Text style={styles.cardTitle}>{isKn ? 'ಹವಾಮಾನ' : 'Weather'}</Text>
            </View>
            <Text style={styles.tempBadge}>28°C • Ujire</Text>
          </View>

          <View style={styles.weatherMiniRow}>
            <View style={styles.weatherChip}>
              <Droplets size={13} color="#0284C7" />
              <Text style={styles.weatherChipText}>{isKn ? 'ತೇವಾಂಶ 84%' : 'Humidity 84%'}</Text>
            </View>
            <View style={styles.weatherChip}>
              <CloudSun size={13} color="#D97706" />
              <Text style={styles.weatherChipText}>{isKn ? 'ಮಳೆ ಸಂಭವ 70%' : 'Rain 70%'}</Text>
            </View>
          </View>

          <View style={styles.sprayAlert}>
            <AlertTriangle size={14} color="#B45309" />
            <Text style={styles.sprayText}>
              {isKn ? '🌧️ ನಾಳೆ ಮಳೆ: ಇಂದು ಸಿಂಪರಣೆ ಬೇಡ' : '🌧️ Rain expected: Avoid crop spray today'}
            </Text>
          </View>
        </View>

        {/* Compact Village Radar Card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <View style={styles.headerLeft}>
              <Users size={18} color="#15803D" />
              <Text style={styles.cardTitle}>{isKn ? 'ಗ್ರಾಮದ ಬೆಳೆ ಸ್ಥಿತಿ' : 'Village Crop Radar'}</Text>
            </View>
            <TouchableOpacity onPress={handleBroadcastAlert} style={styles.alertBtn}>
              <BellRing size={12} color="#FFFFFF" />
              <Text style={styles.alertBtnText}>{isKn ? 'ಎಚ್ಚರಿಸಿ' : 'Alert'}</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.neighborRow}>
            {NEIGHBOR_FARMS.map((f) => (
              <View key={f.id} style={styles.neighborChip}>
                <Text style={styles.nName}>{f.name}</Text>
                <Text style={styles.nCrop}>{f.crop}</Text>
                <View style={[styles.statusDot, f.status === 'healthy' ? styles.dotGreen : styles.dotAmber]}>
                  <Text style={[styles.statusText, f.status === 'healthy' ? { color: '#166534' } : { color: '#92400E' }]}>
                    {f.status === 'healthy' ? '● Good' : '▲ Alert'}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        </View>

        {/* 2 Big Action Tiles */}
        <View style={styles.grid2x2}>
          <TouchableOpacity
            style={styles.actionTile}
            onPress={() => navigation.navigate('MarketTab')}
            activeOpacity={0.85}
          >
            <View style={[styles.tileIcon, { backgroundColor: '#DCFCE7' }]}>
              <TrendingUp size={20} color="#16A34A" />
            </View>
            <Text style={styles.tileTitle}>{isKn ? 'ಮಾರುಕಟ್ಟೆ ದರ' : 'Mandi Rates'}</Text>
            <Text style={styles.tileSub}>{isKn ? 'ಅಡಿಕೆ ₹48,500' : 'Areca ₹48.5k ↑'}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionTile}
            onPress={() => navigation.navigate('WeatherTab')}
            activeOpacity={0.85}
          >
            <View style={[styles.tileIcon, { backgroundColor: '#EFF6FF' }]}>
              <CloudSun size={20} color="#2563EB" />
            </View>
            <Text style={styles.tileTitle}>{isKn ? 'ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ' : 'Weather Radar'}</Text>
            <Text style={styles.tileSub}>{isKn ? '7-ದಿನಗಳ ಮುನ್ಸೂಚನೆ' : '7-Day Forecast'}</Text>
          </TouchableOpacity>
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
    paddingBottom: 40,
    gap: 12,
  },
  heroCard: {
    backgroundColor: '#0F5132',
    borderRadius: BorderRadius.lg,
    padding: 16,
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
    backgroundColor: '#16A34A',
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
    marginTop: 1,
  },
  arrowCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 10,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  tempBadge: {
    fontSize: 11,
    fontWeight: '700',
    color: '#1D4ED8',
    backgroundColor: '#EFF6FF',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: BorderRadius.full,
  },
  weatherMiniRow: {
    flexDirection: 'row',
    gap: 8,
  },
  weatherChip: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 5,
    backgroundColor: '#F1F5F9',
    paddingVertical: 6,
    borderRadius: BorderRadius.sm,
  },
  weatherChipText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#334155',
  },
  sprayAlert: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FEF3C7',
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: BorderRadius.sm,
  },
  sprayText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#92400E',
    flex: 1,
  },
  alertBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#DC2626',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: BorderRadius.sm,
  },
  alertBtnText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  neighborRow: {
    flexDirection: 'row',
    gap: 8,
  },
  neighborChip: {
    flex: 1,
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.sm,
    padding: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 2,
  },
  nName: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  nCrop: {
    fontSize: 10,
    color: Colors.textSecondary,
  },
  statusDot: {
    marginTop: 2,
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: BorderRadius.full,
  },
  dotGreen: {
    backgroundColor: '#DCFCE7',
  },
  dotAmber: {
    backgroundColor: '#FEF3C7',
  },
  statusText: {
    fontSize: 9,
    fontWeight: '800',
  },
  grid2x2: {
    flexDirection: 'row',
    gap: 10,
  },
  actionTile: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    alignItems: 'center',
    gap: 4,
  },
  tileIcon: {
    width: 38,
    height: 38,
    borderRadius: BorderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 2,
  },
  tileTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  tileSub: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
});
