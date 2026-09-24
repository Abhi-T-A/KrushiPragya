import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { useLanguage } from '../../context/LanguageContext';
import { Header } from '../../components/common/Header';
import { Card } from '../../components/common/Card';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { SEED_WEATHER_RISKS } from '../../constants/seedData';
import { CloudRain, Droplets, Thermometer, AlertCircle, Building2 } from 'lucide-react-native';

export const WeatherScreen: React.FC = () => {
  const { t } = useLanguage();
  const [selectedCrop, setSelectedCrop] = useState<'arecanut' | 'paddy'>('arecanut');

  const risk = SEED_WEATHER_RISKS[selectedCrop];

  return (
    <View style={styles.container}>
      <Header title={t.weatherTitle} />

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Simple 2-Crop Selector */}
        <View style={styles.toggleRow}>
          <TouchableOpacity
            onPress={() => setSelectedCrop('arecanut')}
            style={[
              styles.toggleBtn,
              selectedCrop === 'arecanut' && styles.toggleActive,
            ]}
          >
            <Text
              style={[
                styles.toggleText,
                selectedCrop === 'arecanut' && styles.toggleActiveText,
              ]}
            >
              🌴 ಅಡಿಕೆ (Arecanut)
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => setSelectedCrop('paddy')}
            style={[
              styles.toggleBtn,
              selectedCrop === 'paddy' && styles.toggleActive,
            ]}
          >
            <Text
              style={[
                styles.toggleText,
                selectedCrop === 'paddy' && styles.toggleActiveText,
              ]}
            >
              🌾 ಭತ್ತ (Paddy)
            </Text>
          </TouchableOpacity>
        </View>

        {/* Primary Risk Card */}
        <Card
          variant={risk.riskLevel === 'HIGH' ? 'alert' : 'highlight'}
          style={styles.riskCard}
        >
          <View style={styles.riskHeader}>
            <View
              style={[
                styles.riskPill,
                {
                  backgroundColor:
                    risk.riskLevel === 'HIGH' ? Colors.alertHighBg : Colors.aiAnalysedBg,
                },
              ]}
            >
              <Text
                style={[
                  styles.riskPillText,
                  {
                    color:
                      risk.riskLevel === 'HIGH' ? Colors.alertHigh : Colors.aiAnalysed,
                  },
                ]}
              >
                {risk.riskLevel === 'HIGH' ? `🔴 ${t.highRisk}` : `🟡 ${t.mediumRisk}`}
              </Text>
            </View>
            <Text style={styles.validText}>ಮಾನ್ಯತೆ: {risk.validUntil}</Text>
          </View>

          <Text style={styles.riskName}>{risk.diseaseRiskKn}</Text>
          <Text style={styles.triggerText}>ಕಾರಣ: {risk.triggerCondition}</Text>
        </Card>

        {/* Weather Metrics Bar */}
        <View style={styles.metricsRow}>
          <View style={styles.metricCard}>
            <Droplets size={20} color={Colors.primary} />
            <Text style={styles.metricValue}>{risk.humidity}%</Text>
            <Text style={styles.metricLabel}>{t.humidity}</Text>
          </View>

          <View style={styles.metricCard}>
            <CloudRain size={20} color={Colors.primary} />
            <Text style={styles.metricValue}>{risk.rainfallMm} mm</Text>
            <Text style={styles.metricLabel}>{t.rainfall}</Text>
          </View>

          <View style={styles.metricCard}>
            <Thermometer size={20} color={Colors.primary} />
            <Text style={styles.metricValue}>{risk.tempMin}° - {risk.tempMax}°C</Text>
            <Text style={styles.metricLabel}>{t.temp}</Text>
          </View>
        </View>

        {/* Actionable Kannada Advice */}
        <Card style={styles.advisoryCard}>
          <View style={styles.advisoryHeader}>
            <AlertCircle size={20} color={Colors.primaryDark} />
            <Text style={styles.advisoryTitle}>{t.weatherAdviceAction}</Text>
          </View>
          <Text style={styles.advisoryText}>{risk.advisoryKn}</Text>

          <View style={styles.sourceRow}>
            <Building2 size={14} color={Colors.textSecondary} />
            <Text style={styles.sourceText}>{risk.source}</Text>
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
    paddingBottom: Spacing.xxxl,
    gap: Spacing.md,
  },
  toggleRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
  },
  toggleBtn: {
    flex: 1,
    paddingVertical: Spacing.md,
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.md,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  toggleActive: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },
  toggleText: {
    ...Typography.bodyLarge,
    fontWeight: '700',
    color: Colors.textSecondary,
  },
  toggleActiveText: {
    color: Colors.textWhite,
  },
  riskCard: {
    padding: Spacing.lg,
  },
  riskHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  riskPill: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
  },
  riskPillText: {
    ...Typography.label,
    fontWeight: '800',
  },
  validText: {
    ...Typography.caption,
    color: Colors.textMuted,
  },
  riskName: {
    ...Typography.title1,
    color: Colors.textPrimary,
    fontWeight: '800',
    marginTop: 4,
  },
  triggerText: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 4,
    fontWeight: '600',
  },
  metricsRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
  },
  metricCard: {
    flex: 1,
    backgroundColor: Colors.surface,
    padding: Spacing.md,
    borderRadius: BorderRadius.lg,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  metricValue: {
    ...Typography.title2,
    fontWeight: '800',
    color: Colors.textPrimary,
    marginTop: 4,
  },
  metricLabel: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  advisoryCard: {
    backgroundColor: Colors.primaryLight,
    borderWidth: 1.5,
    borderColor: Colors.primary,
  },
  advisoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: Spacing.xs,
  },
  advisoryTitle: {
    ...Typography.title2,
    color: Colors.primaryDark,
    fontWeight: '800',
  },
  advisoryText: {
    ...Typography.bodyLarge,
    color: Colors.textPrimary,
    lineHeight: 22,
    fontWeight: '600',
  },
  sourceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: Spacing.md,
    paddingTop: Spacing.xs,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.08)',
  },
  sourceText: {
    ...Typography.caption,
    color: Colors.textSecondary,
  },
});
