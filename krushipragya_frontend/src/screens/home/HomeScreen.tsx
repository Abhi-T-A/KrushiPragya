import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Header } from '../../components/common/Header';
import { Card } from '../../components/common/Card';
import { VillageCropFeed } from '../../components/village/VillageCropFeed';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { SEED_WEATHER_RISKS, SEED_MARKET_PRICES } from '../../constants/seedData';
import {
  Camera,
  CloudSun,
  TrendingUp,
  Landmark,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  Droplets,
  CloudRain,
  CheckCircle2,
} from 'lucide-react-native';

export const HomeScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const { language } = useLanguage();
  const { user } = useAuth();

  const weatherAlert = SEED_WEATHER_RISKS.arecanut;
  const marketPrice = SEED_MARKET_PRICES[0];

  return (
    <View style={styles.container}>
      <Header />

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Farmer Greeting */}
        <View style={styles.greetingBox}>
          <Text style={styles.greetingText}>
            {language === 'kn' ? 'ನಮಸ್ಕಾರ' : 'Namaskara'}, {user?.name ? (language === 'kn' ? user.name : user.name.split('(')[0].trim()) : (language === 'kn' ? 'ಅಭಿ ಗೌಡ' : 'Abhi Gowda')} 👋
          </Text>
          <Text style={styles.subGreetingText}>
            {language === 'kn'
              ? 'ಇಂದು ನಿಮ್ಮ ಕೃಷಿ ಸ್ಥಿತಿ ಮತ್ತು ಎಚ್ಚರಿಕೆಗಳು'
              : "Today's agricultural status & advisories"}
          </Text>
        </View>

        {/* PRIMARY HERO ACTION: 📷 Check / Report Crop Problem */}
        <TouchableOpacity
          activeOpacity={0.88}
          onPress={() => navigation.navigate('ReportTab', { screen: 'CropSelect' })}
          style={styles.heroButton}
        >
          <View style={styles.heroIconBg}>
            <Camera size={30} color={Colors.textWhite} strokeWidth={2.4} />
          </View>
          <View style={styles.heroTextCol}>
            <View style={styles.heroBadge}>
              <Sparkles size={12} color={Colors.accentGold} />
              <Text style={styles.heroBadgeText}>
                {language === 'kn' ? 'AI ಬೆಳೆ ಆರೋಗ್ಯ' : 'AI Crop Health'}
              </Text>
            </View>
            <Text style={styles.heroTitle}>
              {language === 'kn' ? 'ಬೆಳೆ ಸಮಸ್ಯೆ ವರದಿ ಮಾಡಿ' : 'Report Crop Problem'}
            </Text>
            <Text style={styles.heroSubtitle}>
              {language === 'kn'
                ? 'ಫೋಟೋ ತೆಗೆದು ರೋಗಲಕ್ಷಣ ಮತ್ತು ಸಲಹೆ ಪರಿಶೀಲಿಸಿ'
                : 'Scan leaf symptom & get verified ICAR advisory'}
            </Text>
          </View>
        </TouchableOpacity>

        {/* 📢 VILLAGE CROP HEALTH FEED & FARMER NETWORK (Core Social Early-Warning) */}
        <VillageCropFeed />

        {/* 🌦️ Live Weather & Actionable Advisory Card */}
        <Card variant="alert" style={styles.weatherHeroCard}>
          <View style={styles.weatherTopRow}>
            <View style={styles.weatherTempBox}>
              <Text style={styles.tempText}>27°C</Text>
              <Text style={styles.weatherCityText}>{user?.villageName ? user.villageName.split('(')[0].trim() : 'Ujire'}</Text>
            </View>
            <View style={styles.weatherStatsCol}>
              <View style={styles.statItem}>
                <Droplets size={14} color={Colors.primary} />
                <Text style={styles.statText}>72% {language === 'kn' ? 'ತೇವಾಂಶ' : 'Humidity'}</Text>
              </View>
              <View style={styles.statItem}>
                <CloudRain size={14} color={Colors.primary} />
                <Text style={styles.statText}>70% {language === 'kn' ? 'ಮಳೆಯ ಸಾಧ್ಯತೆ' : 'Rain chance'}</Text>
              </View>
            </View>
          </View>

          {/* Actionable Warning Banner */}
          <View style={styles.sprayWarningBanner}>
            <AlertTriangle size={16} color={Colors.alertHigh} />
            <Text style={styles.sprayWarningText}>
              {language === 'kn' ? '⚠️ ಇಂದು ಸಿಂಪಡಣೆ ತಪ್ಪಿಸಿ (Rain expected)' : '⚠️ Avoid chemical spray today (Rain)'}
            </Text>
          </View>

          <TouchableOpacity
            onPress={() => navigation.navigate('WeatherTab')}
            style={styles.cardActionRow}
          >
            <Text style={styles.cardActionText}>
              {language === 'kn' ? 'ಸಂಪೂರ್ಣ ಹವಾಮಾನ ಮುನ್ನೋಟ' : 'View Full Weather Advisory'}
            </Text>
            <ArrowRight size={15} color={Colors.primary} />
          </TouchableOpacity>
        </Card>

        {/* 🌱 My Crops Section (ನಿಮ್ಮ ಬೆಳೆಗಳು) */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            {language === 'kn' ? 'ನಿಮ್ಮ ಬೆಳೆಗಳು' : 'My Crops'}
          </Text>
        </View>

        <View style={styles.cropsRow}>
          {/* Arecanut Crop Card */}
          <Card style={styles.myCropCard}>
            <View style={styles.cropCardTop}>
              <Text style={styles.cropCardEmoji}>🌴</Text>
              <View style={styles.healthTag}>
                <CheckCircle2 size={12} color={Colors.expertVerified} />
                <Text style={styles.healthTagText}>{language === 'kn' ? 'ಆರೋಗ್ಯಕರ' : 'Healthy'}</Text>
              </View>
            </View>
            <Text style={styles.myCropName}>{language === 'kn' ? 'ಅಡಿಕೆ' : 'Arecanut'}</Text>
            <Text style={styles.myCropArea}>2.0 {language === 'kn' ? 'ಎಕರೆ' : 'Acres'}</Text>
          </Card>

          {/* Paddy Crop Card */}
          <Card style={styles.myCropCard}>
            <View style={styles.cropCardTop}>
              <Text style={styles.cropCardEmoji}>🌾</Text>
              <View style={[styles.healthTag, { backgroundColor: Colors.aiAnalysedBg }]}>
                <AlertTriangle size={12} color={Colors.aiAnalysed} />
                <Text style={[styles.healthTagText, { color: Colors.aiAnalysed }]}>
                  {language === 'kn' ? 'ಗಮನ ಅಗತ್ಯ' : 'Monitoring'}
                </Text>
              </View>
            </View>
            <Text style={styles.myCropName}>{language === 'kn' ? 'ಭತ್ತ' : 'Paddy'}</Text>
            <Text style={styles.myCropArea}>0.5 {language === 'kn' ? 'ಎಕರೆ' : 'Acres'}</Text>
          </Card>
        </View>

        {/* Quick Action Summary Cards (Market, Schemes) */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            {language === 'kn' ? 'ಕೃಷಿ ಮಾಹಿತಿ ಕೇಂದ್ರ' : 'Farm Intelligence Services'}
          </Text>
        </View>

        {/* Market Snippet */}
        <Card
          onPress={() => navigation.navigate('MarketTab')}
          style={styles.summaryCard}
        >
          <View style={styles.summaryRow}>
            <View style={[styles.iconBox, { backgroundColor: '#FEF3C7' }]}>
              <TrendingUp size={20} color={Colors.accentGold} />
            </View>
            <View style={styles.summaryTextCol}>
              <Text style={styles.summaryLabel}>
                {language === 'kn' ? 'ಮಾರುಕಟ್ಟೆ ದರಗಳು' : 'Market Prices'} — {marketPrice.cropKn}
              </Text>
              <Text style={styles.summaryValue}>₹{marketPrice.pricePerQuintal.toLocaleString()} / {language === 'kn' ? 'ಕ್ವಿಂಟಾಲ್' : 'Quintal'}</Text>
              <Text style={styles.summarySub}>{marketPrice.sourceLabel}</Text>
            </View>
            <ArrowRight size={18} color={Colors.textMuted} />
          </View>
        </Card>

        {/* Schemes Snippet */}
        <Card
          onPress={() => navigation.navigate('MarketTab', { initialTab: 'schemes' })}
          style={styles.summaryCard}
        >
          <View style={styles.summaryRow}>
            <View style={[styles.iconBox, { backgroundColor: '#E0E7FF' }]}>
              <Landmark size={20} color={Colors.trustPurple} />
            </View>
            <View style={styles.summaryTextCol}>
              <Text style={styles.summaryLabel}>
                {language === 'kn' ? 'ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು' : 'Government Schemes'}
              </Text>
              <Text style={styles.summaryValue}>
                {language === 'kn' ? 'ತೋಟಗಾರಿಕೆ ಕೀಟನಾಶಕ ಸಹಾಯಧನ' : 'Horticulture Spray Subsidy'}
              </Text>
              <Text style={styles.summarySub}>
                50% {language === 'kn' ? 'ಸಬ್ಸಿಡಿ — ಕರ್ನಾಟಕ ಸರ್ಕಾರ' : 'Subsidy — Govt of Karnataka'}
              </Text>
            </View>
            <ArrowRight size={18} color={Colors.textMuted} />
          </View>
        </Card>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    padding: Spacing.lg,
    paddingTop: Spacing.xs,
    paddingBottom: Spacing.xxxl * 1.5,
  },
  greetingBox: {
    marginBottom: Spacing.md,
  },
  greetingText: {
    ...Typography.title1,
    fontSize: 22,
    color: Colors.textPrimary,
  },
  subGreetingText: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  heroButton: {
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.xl,
    padding: Spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
    marginBottom: Spacing.md,
    shadowColor: Colors.primaryDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 4,
  },
  heroIconBg: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(255,255,255,0.22)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroTextCol: {
    flex: 1,
  },
  heroBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(0,0,0,0.22)',
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: BorderRadius.full,
    marginBottom: 4,
  },
  heroBadgeText: {
    ...Typography.caption,
    color: Colors.textWhite,
    fontWeight: '700',
    fontSize: 10,
  },
  heroTitle: {
    ...Typography.title1,
    fontSize: 19,
    color: Colors.textWhite,
    fontWeight: '800',
  },
  heroSubtitle: {
    ...Typography.caption,
    color: 'rgba(255,255,255,0.85)',
    marginTop: 2,
    fontSize: 11,
  },
  weatherHeroCard: {
    padding: Spacing.md,
    backgroundColor: Colors.surface,
    borderLeftWidth: 4,
    borderLeftColor: Colors.alertHigh,
    marginBottom: Spacing.md,
  },
  weatherTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  weatherTempBox: {
    flexDirection: 'column',
  },
  tempText: {
    fontSize: 32,
    fontWeight: '900',
    color: Colors.textPrimary,
  },
  weatherCityText: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.textSecondary,
  },
  weatherStatsCol: {
    gap: 4,
    alignItems: 'flex-end',
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statText: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  sprayWarningBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: Colors.alertHighBg,
    padding: Spacing.sm,
    borderRadius: BorderRadius.md,
    marginVertical: 4,
  },
  sprayWarningText: {
    ...Typography.label,
    fontSize: 12,
    color: Colors.alertHigh,
    fontWeight: '800',
    flex: 1,
  },
  cardActionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: Spacing.sm,
    alignSelf: 'flex-end',
  },
  cardActionText: {
    ...Typography.caption,
    color: Colors.primary,
    fontWeight: '800',
  },
  sectionHeader: {
    marginVertical: Spacing.xs,
  },
  sectionTitle: {
    ...Typography.title2,
    fontSize: 17,
    color: Colors.textPrimary,
    fontWeight: '800',
  },
  cropsRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
    marginBottom: Spacing.sm,
  },
  myCropCard: {
    flex: 1,
    padding: Spacing.md,
    marginBottom: Spacing.xs,
  },
  cropCardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  cropCardEmoji: {
    fontSize: 24,
  },
  healthTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: Colors.expertVerifiedBg,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: BorderRadius.full,
  },
  healthTagText: {
    fontSize: 10,
    fontWeight: '800',
    color: Colors.expertVerified,
  },
  myCropName: {
    ...Typography.bodyLarge,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  myCropArea: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 1,
  },
  summaryCard: {
    padding: Spacing.md,
    marginBottom: Spacing.sm,
  },
  summaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
  },
  iconBox: {
    width: 42,
    height: 42,
    borderRadius: BorderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  summaryTextCol: {
    flex: 1,
  },
  summaryLabel: {
    ...Typography.caption,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  summaryValue: {
    ...Typography.bodyLarge,
    fontWeight: '800',
    color: Colors.textPrimary,
    marginTop: 1,
  },
  summarySub: {
    ...Typography.caption,
    color: Colors.textMuted,
    fontSize: 11,
    marginTop: 1,
  },
});
