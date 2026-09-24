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
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { SEED_WEATHER_RISKS, SEED_MARKET_PRICES } from '../../constants/seedData';
import {
  Camera,
  CloudRain,
  TrendingUp,
  Landmark,
  AlertTriangle,
  ArrowRight,
  Sparkles,
} from 'lucide-react-native';

export const HomeScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const { t } = useLanguage();
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
            {t.greeting}, {user?.name || 'ರೈತ ಮಿತ್ರ'} 👋
          </Text>
          <Text style={styles.subGreetingText}>
            ನಿಮ್ಮ ತೋಟದ ಇಂದಿನ ಕೃಷಿ ಸ್ಥಿತಿ ಮತ್ತು ಎಚ್ಚರಿಕೆಗಳು
          </Text>
        </View>

        {/* PRIMARY HERO CTA: REPORT CROP PROBLEM (1-Tap Primary Flow) */}
        <TouchableOpacity
          activeOpacity={0.88}
          onPress={() => navigation.navigate('ReportTab', { screen: 'CropSelect' })}
          style={styles.heroButton}
        >
          <View style={styles.heroIconBg}>
            <Camera size={32} color={Colors.textWhite} />
          </View>
          <View style={styles.heroTextCol}>
            <View style={styles.heroBadge}>
              <Sparkles size={12} color={Colors.accentGold} />
              <Text style={styles.heroBadgeText}>AI ವಿಶ್ಲೇಷಣೆ (AI Analysis)</Text>
            </View>
            <Text style={styles.heroTitle}>{t.btnReportProblem}</Text>
            <Text style={styles.heroSubtitle}>
              ಫೋಟೋ ತೆಗೆದು ರೋಗಲಕ್ಷಣ ಮತ್ತು ಸಲಹೆ ಪರಿಶೀಲಿಸಿ
            </Text>
          </View>
        </TouchableOpacity>

        {/* One Major Weather Alert Card */}
        <Card variant="alert" style={styles.alertCard}>
          <View style={styles.alertHeader}>
            <View style={styles.alertTag}>
              <AlertTriangle size={16} color={Colors.alertHigh} />
              <Text style={styles.alertTagText}>🔴 {t.highRisk} — {weatherAlert.diseaseRiskKn}</Text>
            </View>
            <Text style={styles.alertValidUntil}>ಮಾನ್ಯತೆ: {weatherAlert.validUntil}</Text>
          </View>

          <Text style={styles.alertCondition}>
            {weatherAlert.triggerCondition}
          </Text>
          <Text style={styles.alertAdvisoryText}>
            {weatherAlert.advisoryKn}
          </Text>

          <TouchableOpacity
            onPress={() => navigation.navigate('WeatherTab')}
            style={styles.cardActionRow}
          >
            <Text style={styles.cardActionText}>{t.viewDetails}</Text>
            <ArrowRight size={16} color={Colors.primary} />
          </TouchableOpacity>
        </Card>

        {/* Quick Summary Cards (Weather, Market, Schemes) */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>ಕೃಷಿ ಮಾಹಿತಿ ಕೇಂದ್ರ</Text>
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
              <Text style={styles.summaryLabel}>{t.quickMarket} — {marketPrice.cropKn}</Text>
              <Text style={styles.summaryValue}>₹{marketPrice.pricePerQuintal.toLocaleString()} / ಕ್ವಿಂಟಾಲ್</Text>
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
              <Text style={styles.summaryLabel}>{t.quickSchemes}</Text>
              <Text style={styles.summaryValue}>ತೋಟಗಾರಿಕೆ ಕೀಟನಾಶಕ ಸಹಾಯಧನ</Text>
              <Text style={styles.summarySub}>50% ಸಬ್ಸಿಡಿ — ಕರ್ನಾಟಕ ಸರ್ಕಾರ</Text>
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
    paddingBottom: Spacing.xxxl,
  },
  greetingBox: {
    marginBottom: Spacing.md,
  },
  greetingText: {
    ...Typography.title1,
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
    marginBottom: Spacing.lg,
    shadowColor: Colors.primaryDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 4,
  },
  heroIconBg: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255,255,255,0.2)',
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
    backgroundColor: 'rgba(0,0,0,0.2)',
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
  },
  heroTitle: {
    ...Typography.title1,
    color: Colors.textWhite,
    fontWeight: '800',
  },
  heroSubtitle: {
    ...Typography.caption,
    color: 'rgba(255,255,255,0.85)',
    marginTop: 2,
  },
  alertCard: {
    borderLeftWidth: 4,
    borderLeftColor: Colors.alertHigh,
    backgroundColor: Colors.surface,
  },
  alertHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  alertTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  alertTagText: {
    ...Typography.label,
    color: Colors.alertHigh,
    fontWeight: '700',
  },
  alertValidUntil: {
    ...Typography.caption,
    color: Colors.textMuted,
  },
  alertCondition: {
    ...Typography.caption,
    color: Colors.textSecondary,
    fontWeight: '600',
    marginBottom: Spacing.xs,
  },
  alertAdvisoryText: {
    ...Typography.bodyLarge,
    color: Colors.textPrimary,
    lineHeight: 22,
    fontWeight: '600',
  },
  cardActionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: Spacing.md,
    alignSelf: 'flex-end',
  },
  cardActionText: {
    ...Typography.label,
    color: Colors.primary,
    fontWeight: '700',
  },
  sectionHeader: {
    marginVertical: Spacing.sm,
  },
  sectionTitle: {
    ...Typography.title2,
    color: Colors.textPrimary,
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
    width: 44,
    height: 44,
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
    ...Typography.title2,
    color: Colors.textPrimary,
    marginTop: 2,
  },
  summarySub: {
    ...Typography.caption,
    color: Colors.textMuted,
    marginTop: 1,
  },
});
