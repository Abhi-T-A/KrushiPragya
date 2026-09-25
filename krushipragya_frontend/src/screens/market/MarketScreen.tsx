import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Linking,
} from 'react-native';
import { useLanguage } from '../../context/LanguageContext';
import { Header } from '../../components/common/Header';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { SEED_MARKET_PRICES, SEED_SCHEMES } from '../../constants/seedData';
import { TrendingUp, Landmark, ExternalLink, Clock, Building2, CheckCircle2 } from 'lucide-react-native';

export const MarketScreen: React.FC<{ route: any }> = ({ route }) => {
  const { initialTab } = route?.params || { initialTab: 'market' };
  const { t, language } = useLanguage();
  const [activeTab, setActiveTab] = useState<'market' | 'schemes'>(initialTab);

  const openUrl = (url: string) => {
    Linking.openURL(url);
  };

  return (
    <View style={styles.container}>
      <Header />

      {/* Top Segmented Control */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          onPress={() => setActiveTab('market')}
          style={[styles.tabButton, activeTab === 'market' && styles.tabButtonActive]}
        >
          <TrendingUp size={16} color={activeTab === 'market' ? Colors.textWhite : Colors.textSecondary} />
          <Text style={[styles.tabButtonText, activeTab === 'market' && styles.tabButtonTextActive]}>
            {language === 'kn' ? 'ಮಾರುಕಟ್ಟೆ ದರಗಳು' : 'Market Prices'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => setActiveTab('schemes')}
          style={[styles.tabButton, activeTab === 'schemes' && styles.tabButtonActive]}
        >
          <Landmark size={16} color={activeTab === 'schemes' ? Colors.textWhite : Colors.textSecondary} />
          <Text style={[styles.tabButtonText, activeTab === 'schemes' && styles.tabButtonTextActive]}>
            {language === 'kn' ? 'ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು' : 'Govt Schemes'}
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {activeTab === 'market' ? (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                {language === 'kn' ? 'ಮಾರುಕಟ್ಟೆ ದರಗಳ ಪಾರದರ್ಶಕತೆ' : 'Market Price Transparency'}
              </Text>
              <Text style={styles.sectionSubtitle}>
                {language === 'kn'
                  ? 'ಹೋಲಿಕೆಗಾಗಿ ಮಾತ್ರ — ಮಾರಾಟ ಮಾಡುವ ಮುನ್ನ ಪರಿಶೀಲಿಸಿ'
                  : 'Prices shown for comparison only. Verify before selling.'}
              </Text>
            </View>

            {SEED_MARKET_PRICES.map((item) => (
              <Card key={item.id} style={styles.priceCard}>
                <View style={styles.priceHeader}>
                  <Text style={styles.cropTitle}>
                    {language === 'kn' ? item.cropKn : item.crop}
                  </Text>
                  <View style={styles.sourceTag}>
                    <Text style={styles.sourceTagText}>{item.sourceType}</Text>
                  </View>
                </View>

                <View style={styles.priceRow}>
                  <Text style={styles.priceAmount}>₹{item.pricePerQuintal.toLocaleString()}</Text>
                  <Text style={styles.priceUnit}>
                    / {language === 'kn' ? 'ಕ್ವಿಂಟಾಲ್' : 'Quintal'}
                  </Text>
                </View>

                <View style={styles.sourceFooter}>
                  <Building2 size={12} color={Colors.textSecondary} />
                  <Text style={styles.sourceLabel}>{item.sourceLabel}</Text>
                  <View style={styles.timeTag}>
                    <Clock size={12} color={Colors.textMuted} />
                    <Text style={styles.timeText}>{item.recordedAt}</Text>
                  </View>
                </View>
              </Card>
            ))}

            <View style={styles.disclaimerBox}>
              <Text style={styles.disclaimerText}>
                {language === 'kn'
                  ? '⚠️ ಸೂಚನೆ: ಈ ಬೆಲೆಗಳು ಹೋಲಿಕೆಗಾಗಿ ಮಾತ್ರ. ಯಾವುದೇ ನೇರ ಖರೀದಿ/ಮಾರಾಟ ಒಪ್ಪಂದ ಮಾಡುವ ಮುನ್ನ ಮಂಡಿ ಅಥವಾ ವ್ಯಾಪಾರಿಗಳೊಂದಿಗೆ ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ.'
                  : '⚠️ Disclaimer: Prices are for information only. Confirm terms directly with mandi or buyers before transaction.'}
              </Text>
            </View>
          </>
        ) : (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                {language === 'kn' ? 'ಕರ್ನಾಟಕ ಸರ್ಕಾರಿ ಕೃಷಿ ಯೋಜನೆಗಳು' : 'Karnataka Agriculture Schemes'}
              </Text>
              <Text style={styles.sectionSubtitle}>
                {language === 'kn' ? 'ಅಧಿಕೃತ ಇಲಾಖೆಗಳಿಂದ ಪರಿಶೀಲಿಸಿದ ಮಾಹಿತಿ' : 'Verified from official departments'}
              </Text>
            </View>

            {SEED_SCHEMES.map((scheme) => (
              <Card key={scheme.id} variant="trust" style={styles.schemeCard}>
                <Text style={styles.schemeTitle}>
                  {language === 'kn' ? scheme.nameKn : scheme.nameEn}
                </Text>
                <Text style={styles.schemeDept}>{scheme.department}</Text>

                <View style={styles.benefitBox}>
                  <CheckCircle2 size={16} color={Colors.primary} />
                  <Text style={styles.benefitText}>
                    {language === 'kn' ? scheme.benefitKn : scheme.benefitEn}
                  </Text>
                </View>

                <View style={styles.eligibilityRow}>
                  <Text style={styles.eligibilityLabel}>
                    {language === 'kn' ? 'ಅರ್ಹತೆ:' : 'Eligibility:'}
                  </Text>
                  <Text style={styles.eligibilityText}>
                    {language === 'kn' ? scheme.eligibilityKn : scheme.eligibilityEn}
                  </Text>
                </View>

                <Button
                  title={language === 'kn' ? 'ಅಧಿಕೃತ ತಾಣ ತೆರೆಯಿರಿ (Official Portal)' : 'Open Official Portal'}
                  variant="outline"
                  size="normal"
                  onPress={() => openUrl(scheme.officialSourceUrl)}
                  icon={<ExternalLink size={16} color={Colors.primary} />}
                  style={{ marginTop: Spacing.sm }}
                />
              </Card>
            ))}
          </>
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
  tabBar: {
    flexDirection: 'row',
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.xs,
    gap: Spacing.sm,
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: Spacing.sm + 2,
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  tabButtonActive: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },
  tabButtonText: {
    ...Typography.label,
    color: Colors.textSecondary,
  },
  tabButtonTextActive: {
    color: Colors.textWhite,
  },
  scrollContent: {
    padding: Spacing.lg,
    paddingBottom: Spacing.xxxl,
    gap: Spacing.sm,
  },
  sectionHeader: {
    marginBottom: Spacing.xs,
  },
  sectionTitle: {
    ...Typography.title2,
    color: Colors.textPrimary,
  },
  sectionSubtitle: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  priceCard: {
    padding: Spacing.md,
  },
  priceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cropTitle: {
    ...Typography.title2,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  sourceTag: {
    backgroundColor: Colors.surfaceSubtle,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  sourceTagText: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.textSecondary,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: Spacing.xs,
    marginVertical: Spacing.xs,
  },
  priceAmount: {
    ...Typography.display,
    color: Colors.primaryDark,
    fontWeight: '800',
  },
  priceUnit: {
    ...Typography.caption,
    color: Colors.textSecondary,
  },
  sourceFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: Spacing.xs,
    paddingTop: Spacing.xs,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  sourceLabel: {
    ...Typography.caption,
    color: Colors.textSecondary,
    flex: 1,
  },
  timeTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  timeText: {
    ...Typography.caption,
    color: Colors.textMuted,
  },
  disclaimerBox: {
    backgroundColor: Colors.surfaceSubtle,
    padding: Spacing.sm,
    borderRadius: BorderRadius.md,
    marginTop: Spacing.sm,
  },
  disclaimerText: {
    ...Typography.caption,
    color: Colors.textSecondary,
    lineHeight: 16,
  },
  schemeCard: {
    padding: Spacing.md,
    gap: Spacing.xs,
  },
  schemeTitle: {
    ...Typography.title2,
    color: Colors.textPrimary,
    fontWeight: '800',
  },
  schemeDept: {
    ...Typography.caption,
    color: Colors.textMuted,
  },
  benefitBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: Colors.primaryLight,
    padding: Spacing.xs + 2,
    borderRadius: BorderRadius.sm,
    marginVertical: 4,
  },
  benefitText: {
    ...Typography.label,
    color: Colors.primaryDark,
    flex: 1,
  },
  eligibilityRow: {
    marginVertical: 2,
  },
  eligibilityLabel: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.textSecondary,
  },
  eligibilityText: {
    ...Typography.caption,
    color: Colors.textPrimary,
  },
});
