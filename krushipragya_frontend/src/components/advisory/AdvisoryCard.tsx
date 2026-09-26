import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import {
  FarmerComprehensiveAdvisoryResponse,
  AdvisoryActionItem,
} from '../../services/advisoryApi';
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle2,
  Clock,
  ShieldCheck,
  Sprout,
  CloudRain,
  ChevronRight,
  MapPin,
} from 'lucide-react-native';

interface AdvisoryCardProps {
  advisory: FarmerComprehensiveAdvisoryResponse;
  onPress?: () => void;
  compact?: boolean;
}

export const AdvisoryCard: React.FC<AdvisoryCardProps> = ({
  advisory,
  onPress,
  compact = false,
}) => {
  const severity = (advisory.severity || advisory.risk_level || 'INFO').toUpperCase();

  // Determine priority color palette and Kannada label
  const getSeverityMeta = () => {
    switch (severity) {
      case 'CRITICAL':
        return {
          labelKn: '⚠️ ತೀರಾ ತುರ್ತು ಸಲಹೆ',
          labelEn: 'Critical Advisory',
          color: Colors.alertHigh,
          bgColor: Colors.alertHighBg,
          borderColor: '#F87171',
          Icon: AlertTriangle,
        };
      case 'HIGH':
        return {
          labelKn: '⚠️ ಪ್ರಮುಖ ಸಲಹೆ',
          labelEn: 'High Priority',
          color: '#C2410C',
          bgColor: '#FFF7ED',
          borderColor: '#FDBA74',
          Icon: AlertCircle,
        };
      case 'MODERATE':
      case 'MEDIUM':
        return {
          labelKn: '⚡ ಎಚ್ಚರಿಕೆಯ ಸಲಹೆ',
          labelEn: 'Moderate Risk',
          color: Colors.alertMedium,
          bgColor: Colors.alertMediumBg,
          borderColor: '#FDE68A',
          Icon: Info,
        };
      case 'LOW':
        return {
          labelKn: '✅ ಸಾಮಾನ್ಯ ಸಲಹೆ',
          labelEn: 'Low Risk',
          color: Colors.alertLow,
          bgColor: Colors.alertLowBg,
          borderColor: '#BBF7D0',
          Icon: CheckCircle2,
        };
      case 'INFO':
      default:
        return {
          labelKn: 'ℹ️ ಮಾಹಿತಿ ಸಲಹೆ',
          labelEn: 'Informational',
          color: Colors.primary,
          bgColor: Colors.primaryLight,
          borderColor: '#A7F3D0',
          Icon: Sprout,
        };
    }
  };

  const meta = getSeverityMeta();
  const IconComponent = meta.Icon;

  // Check if weather-driven
  const isWeatherDriven =
    advisory.evidence?.some((e: any) => e.type === 'weather') ||
    advisory.sources?.some((s: string) => s.toLowerCase().includes('weather') || s.toLowerCase().includes('openweather')) ||
    (advisory.reason && (advisory.reason.includes('ಮಳೆ') || advisory.reason.toLowerCase().includes('rain') || advisory.reason.includes('ಆರ್ದ್ರತೆ')));

  // Confidence text
  const confidenceKn = advisory.confidence_level_kn || (
    advisory.confidence_level === 'HIGH' ? 'ಹೆಚ್ಚು' :
    advisory.confidence_level === 'MEDIUM' ? 'ಮಧ್ಯಮ' :
    advisory.confidence_level === 'LOW' ? 'ಕಡಿಮೆ' : 'ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ'
  );

  // Crop name
  const cropDisplay = advisory.crop?.name_kn || advisory.crop?.name_en || 'ಅಡಿಕೆ';

  // Actions list
  const actionsList: AdvisoryActionItem[] =
    advisory.actions && advisory.actions.length > 0
      ? advisory.actions
      : advisory.recommended_actions?.map((act) => ({
          action_kn: act,
          action_en: act,
          priority: 2,
          time_window: 'ಮುಂದಿನ 24-48 ಗಂಟೆಗಳು',
          category: 'ACTIVITY',
        })) || [];

  // Summary presentation (clean single summary or 5-part summary formatted)
  const displaySummary = advisory.summary_kn || advisory.summary;

  // Format valid until date
  const formatValidUntil = (dtStr?: string) => {
    if (!dtStr) return 'ಮುಂದಿನ 48 ಗಂಟೆಗಳು';
    try {
      const d = new Date(dtStr);
      return d.toLocaleDateString('kn-IN', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dtStr;
    }
  };

  return (
    <TouchableOpacity
      activeOpacity={0.88}
      onPress={onPress}
      style={[
        styles.cardContainer,
        { borderLeftColor: meta.color, borderColor: Colors.border },
        advisory.status === 'SUPERSEDED' && styles.supersededCard,
      ]}
    >
      {/* 1. Header Row: Priority Badge + Crop Badge */}
      <View style={styles.headerRow}>
        <View style={[styles.priorityBadge, { backgroundColor: meta.bgColor, borderColor: meta.borderColor }]}>
          <IconComponent size={14} color={meta.color} strokeWidth={2.4} />
          <Text style={[styles.priorityText, { color: meta.color }]}>{meta.labelKn}</Text>
        </View>

        <View style={styles.badgesRight}>
          {isWeatherDriven && (
            <View style={styles.weatherBadge}>
              <CloudRain size={12} color="#0369A1" strokeWidth={2} />
              <Text style={styles.weatherBadgeText}>ಹವಾಮಾನ ಆಧಾರಿತ</Text>
            </View>
          )}
          <View style={styles.cropBadge}>
            <Text style={styles.cropBadgeText}>{cropDisplay}</Text>
          </View>
        </View>
      </View>

      {/* 2. Title */}
      <Text style={styles.title} numberOfLines={2}>
        {advisory.title_kn || advisory.title}
      </Text>

      {/* 3. Reason / Context: ಏನು ಆಗುತ್ತಿದೆ? */}
      {advisory.reason && (
        <View style={styles.reasonSection}>
          <Text style={styles.reasonLabel}>ಏನು ಆಗುತ್ತಿದೆ?</Text>
          <Text style={styles.reasonText} numberOfLines={compact ? 2 : 4}>
            {advisory.reason}
          </Text>
        </View>
      )}

      {/* 4. Actions: ಏನು ಮಾಡಬೇಕು? */}
      {actionsList.length > 0 && (
        <View style={styles.actionSection}>
          <Text style={styles.actionHeader}>👉 ಏನು ಮಾಡಬೇಕು?</Text>
          {actionsList.slice(0, compact ? 1 : 3).map((act, idx) => (
            <View key={idx} style={styles.actionRow}>
              <Text style={styles.actionBullet}>•</Text>
              <View style={styles.actionContent}>
                <Text style={styles.actionText}>{act.action_kn || act.action_en}</Text>
                {act.time_window && (
                  <View style={styles.actionTimeRow}>
                    <Clock size={11} color={Colors.textSecondary} />
                    <Text style={styles.actionTimeText}>{act.time_window}</Text>
                  </View>
                )}
              </View>
            </View>
          ))}
        </View>
      )}

      {/* 5. Footer: Timing, Confidence, and Tap Indicator */}
      <View style={styles.footerRow}>
        <View style={styles.confidencePill}>
          <ShieldCheck size={13} color={Colors.primary} />
          <Text style={styles.confidenceText}>ವಿಶ್ವಾಸ: {confidenceKn}</Text>
        </View>

        {advisory.valid_until && (
          <View style={styles.timePill}>
            <Clock size={12} color={Colors.textSecondary} />
            <Text style={styles.timePillText}>{formatValidUntil(advisory.valid_until)} ವರೆಗೆ</Text>
          </View>
        )}

        {onPress && (
          <View style={styles.detailsAction}>
            <Text style={styles.detailsActionText}>ವಿವರ</Text>
            <ChevronRight size={14} color={Colors.primary} strokeWidth={2.5} />
          </View>
        )}
      </View>

      {/* Superseded / Inactive tag if not active */}
      {advisory.status && advisory.status !== 'ACTIVE' && (
        <View style={styles.statusBanner}>
          <Text style={styles.statusBannerText}>
            {advisory.status === 'SUPERSEDED' ? 'ಹಿಂದಿನ ಸಲಹೆ (ಬದಲಾಗಿದೆ)' : 'ಅವಧಿ ಮೀರಿದ ಸಲಹೆ'}
          </Text>
        </View>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  cardContainer: {
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.lg,
    padding: Spacing.md + 2,
    borderWidth: 1,
    borderLeftWidth: 5,
    marginBottom: Spacing.md,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  supersededCard: {
    opacity: 0.78,
    backgroundColor: '#F9FAFB',
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: Spacing.xs + 2,
    flexWrap: 'wrap',
    gap: 6,
  },
  priorityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: BorderRadius.sm,
    borderWidth: 1,
    gap: 5,
  },
  priorityText: {
    fontSize: 12,
    fontWeight: '700',
  },
  badgesRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  weatherBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#F0F9FF',
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: BorderRadius.sm,
    borderWidth: 1,
    borderColor: '#BAE6FD',
  },
  weatherBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#0369A1',
  },
  cropBadge: {
    backgroundColor: '#ECFDF5',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: BorderRadius.sm,
    borderWidth: 1,
    borderColor: '#A7F3D0',
  },
  cropBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#065F46',
  },
  title: {
    ...Typography.title2,
    color: Colors.textPrimary,
    fontWeight: '800',
    marginTop: 2,
    marginBottom: Spacing.xs,
    lineHeight: 22,
  },
  reasonSection: {
    backgroundColor: '#F8F9FA',
    borderRadius: BorderRadius.sm,
    padding: Spacing.sm,
    marginVertical: Spacing.xs,
    borderLeftWidth: 2,
    borderLeftColor: '#CBD5E1',
  },
  reasonLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textSecondary,
    marginBottom: 2,
  },
  reasonText: {
    fontSize: 13,
    color: Colors.textPrimary,
    lineHeight: 18,
  },
  actionSection: {
    marginTop: Spacing.xs + 2,
    marginBottom: Spacing.xs,
  },
  actionHeader: {
    fontSize: 13,
    fontWeight: '800',
    color: Colors.primaryDark,
    marginBottom: 4,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  actionBullet: {
    fontSize: 14,
    color: Colors.primary,
    fontWeight: '800',
    marginRight: 6,
    lineHeight: 18,
  },
  actionContent: {
    flex: 1,
  },
  actionText: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textPrimary,
    lineHeight: 18,
  },
  actionTimeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 2,
  },
  actionTimeText: {
    fontSize: 11,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  footerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    marginTop: Spacing.xs,
    flexWrap: 'wrap',
    gap: 6,
  },
  confidencePill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.primaryLight,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: BorderRadius.full,
  },
  confidenceText: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.primaryDark,
  },
  timePill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  timePillText: {
    fontSize: 11,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  detailsAction: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  detailsActionText: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.primary,
  },
  statusBanner: {
    marginTop: Spacing.sm,
    backgroundColor: '#F3F4F6',
    paddingVertical: 3,
    paddingHorizontal: 6,
    borderRadius: BorderRadius.sm,
    alignSelf: 'flex-start',
  },
  statusBannerText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#6B7280',
  },
});
