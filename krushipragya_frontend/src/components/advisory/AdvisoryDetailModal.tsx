import React from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import {
  FarmerComprehensiveAdvisoryResponse,
  AdvisoryActionItem,
} from '../../services/advisoryApi';
import {
  X,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle2,
  Clock,
  ShieldCheck,
  Sprout,
  MapPin,
  CloudSun,
  FileText,
  Calendar,
  Layers,
} from 'lucide-react-native';

interface AdvisoryDetailModalProps {
  visible: boolean;
  advisory: FarmerComprehensiveAdvisoryResponse | null;
  onClose: () => void;
  onViewWeather?: () => void;
}

export const AdvisoryDetailModal: React.FC<AdvisoryDetailModalProps> = ({
  visible,
  advisory,
  onClose,
  onViewWeather,
}) => {
  if (!advisory) return null;

  const severity = (advisory.severity || advisory.risk_level || 'INFO').toUpperCase();

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

  const cropDisplay = advisory.crop?.name_kn || advisory.crop?.name_en || 'ಅಡಿಕೆ';
  const locationDisplay = advisory.location?.name_kn || advisory.location?.name || 'ಉಜಿರೆ / ಮಂಗಳೂರು';
  const districtDisplay = advisory.location?.district || 'ದಕ್ಷಿಣ ಕನ್ನಡ';

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

  const confidenceKn =
    advisory.confidence_level_kn ||
    (advisory.confidence_level === 'HIGH'
      ? 'ಹೆಚ್ಚು'
      : advisory.confidence_level === 'MEDIUM'
      ? 'ಮಧ್ಯಮ'
      : advisory.confidence_level === 'LOW'
      ? 'ಕಡಿಮೆ'
      : 'ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ');

  const formatDate = (dtStr?: string) => {
    if (!dtStr) return 'ಲಭ್ಯವಿಲ್ಲ';
    try {
      const d = new Date(dtStr);
      return d.toLocaleDateString('kn-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dtStr;
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalCard}>
          {/* Header */}
          <View style={styles.modalHeader}>
            <View style={styles.headerLeft}>
              <View style={[styles.priorityPill, { backgroundColor: meta.bgColor, borderColor: meta.borderColor }]}>
                <IconComponent size={14} color={meta.color} strokeWidth={2.4} />
                <Text style={[styles.priorityPillText, { color: meta.color }]}>{meta.labelKn}</Text>
              </View>
              <Text style={styles.headerTitle} numberOfLines={1}>ಸಲಹೆಯ ವಿವರಗಳು</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn} activeOpacity={0.8}>
              <X size={20} color={Colors.textSecondary} />
            </TouchableOpacity>
          </View>

          {/* Scrollable Content */}
          <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
            {/* Title & Metadata Banner */}
            <View style={styles.mainTitleBox}>
              <Text style={styles.advisoryTitle}>{advisory.title_kn || advisory.title}</Text>

              <View style={styles.metaRow}>
                <View style={styles.metaItem}>
                  <Sprout size={13} color={Colors.primary} />
                  <Text style={styles.metaText}>{cropDisplay}</Text>
                  {advisory.crop?.area_acres ? (
                    <Text style={styles.metaSubText}>({advisory.crop.area_acres} ಎಕರೆ)</Text>
                  ) : null}
                </View>

                <View style={styles.metaItem}>
                  <MapPin size={13} color={Colors.primary} />
                  <Text style={styles.metaText}>{locationDisplay}, {districtDisplay}</Text>
                </View>
              </View>
            </View>

            {/* 1. ಏನು ಆಗುತ್ತಿದೆ? (What is happening?) */}
            <View style={styles.sectionCard}>
              <View style={styles.sectionHeaderRow}>
                <Text style={styles.sectionQuestion}>1. ಏನು ಆಗುತ್ತಿದೆ?</Text>
                <Text style={styles.sectionSubtitle}>ಪ್ರಸ್ತುತ ಹವಾಮಾನ ಮತ್ತು ಬೆಳೆ ಸ್ಥಿತಿ</Text>
              </View>
              <Text style={styles.sectionBodyText}>
                {advisory.reason || advisory.summary_kn || advisory.summary}
              </Text>
            </View>

            {/* 2. ನನ್ನ ಬೆಳೆಗೆ ಏನು ಪರಿಣಾಮ? (Impact) */}
            <View style={styles.sectionCard}>
              <View style={styles.sectionHeaderRow}>
                <Text style={styles.sectionQuestion}>2. ನನ್ನ ಬೆಳೆಗೆ ಏನು ಪರಿಣಾಮ?</Text>
                <Text style={styles.sectionSubtitle}>ಬೆಳೆಯ ಮೇಲಿನ ನಿರೀಕ್ಷಿತ ಪ್ರಭಾವ</Text>
              </View>
              <Text style={styles.sectionBodyText}>
                {advisory.summary_kn || advisory.summary}
              </Text>
            </View>

            {/* 3. ಏನು ಮಾಡಬೇಕು? (What should I do?) */}
            <View style={styles.sectionCard}>
              <View style={styles.sectionHeaderRow}>
                <Text style={styles.sectionQuestion}>3. ನಾನು ಏನು ಮಾಡಬೇಕು?</Text>
                <Text style={styles.sectionSubtitle}>ಕೃಷಿ ತಜ್ಞರು ಮತ್ತು ಸಂಶೋಧನಾ ಸಂಸ್ಥೆಗಳ ಕ್ರಮಗಳು</Text>
              </View>
              {actionsList.map((act, idx) => (
                <View key={idx} style={styles.detailActionItem}>
                  <View style={styles.actionNumberCircle}>
                    <Text style={styles.actionNumberText}>{idx + 1}</Text>
                  </View>
                  <View style={styles.detailActionContent}>
                    <Text style={styles.detailActionMainText}>{act.action_kn || act.action_en}</Text>
                    {act.action_en && act.action_en !== act.action_kn && (
                      <Text style={styles.detailActionSubText}>{act.action_en}</Text>
                    )}
                    <View style={styles.actionTimingPill}>
                      <Clock size={11} color={Colors.textSecondary} />
                      <Text style={styles.actionTimingPillText}>{act.time_window || 'ಮುಂದಿನ 24-48 ಗಂಟೆಗಳು'}</Text>
                    </View>
                  </View>
                </View>
              ))}
            </View>

            {/* 4. ಯಾವಾಗ ಮಾಡಬೇಕು? (Validity Window) */}
            <View style={styles.sectionCard}>
              <View style={styles.sectionHeaderRow}>
                <Text style={styles.sectionQuestion}>4. ಯಾವಾಗ ಮಾಡಬೇಕು?</Text>
                <Text style={styles.sectionSubtitle}>ಸಲಹೆಯ ಮಾನ್ಯತೆಯ ಅವಧಿ</Text>
              </View>
              <View style={styles.timelineRow}>
                <Calendar size={14} color={Colors.primary} />
                <Text style={styles.timelineText}>
                  ಮಾನ್ಯತೆ: {formatDate(advisory.valid_from || advisory.generated_at)} ರಿಂದ {formatDate(advisory.valid_until)}
                </Text>
              </View>
            </View>

            {/* 5. ಈ ಸಲಹೆ ಎಷ್ಟು ವಿಶ್ವಾಸಾರ್ಹ? (Confidence & Provenance) */}
            <View style={styles.sectionCard}>
              <View style={styles.sectionHeaderRow}>
                <Text style={styles.sectionQuestion}>5. ಈ ಸಲಹೆ ಎಷ್ಟು ವಿಶ್ವಾಸಾರ್ಹ?</Text>
                <Text style={styles.sectionSubtitle}>ದೃಢೀಕರಣ ಮತ್ತು ಮೂಲ</Text>
              </View>

              <View style={styles.trustGrid}>
                <View style={styles.trustBox}>
                  <Text style={styles.trustLabel}>ವಿಶ್ವಾಸ ಮಟ್ಟ</Text>
                  <View style={styles.trustValueRow}>
                    <ShieldCheck size={14} color={Colors.primary} />
                    <Text style={styles.trustValue}>{confidenceKn}</Text>
                  </View>
                </View>

                <View style={styles.trustBox}>
                  <Text style={styles.trustLabel}>ವಿಶ್ಲೇಷಣಾ ವಿಧಾನ</Text>
                  <Text style={styles.trustValue}>
                    {advisory.is_llm_generated ? 'AI ಕೃಷಿ ಸಂಶ್ಲೇಷಣೆ' : 'ದೃಢೀಕೃತ ನಿಯಮಾವಳಿ'}
                  </Text>
                </View>
              </View>

              {/* Verified Sources */}
              {advisory.sources && advisory.sources.length > 0 && (
                <View style={styles.sourcesBox}>
                  <Text style={styles.sourcesHeader}>ದೃಢೀಕೃತ ಮೂಲಗಳು:</Text>
                  {advisory.sources.map((src, idx) => (
                    <Text key={idx} style={styles.sourceBullet}>• {src}</Text>
                  ))}
                </View>
              )}

              {/* Evidence data if available */}
              {advisory.evidence && advisory.evidence.length > 0 && (
                <View style={styles.evidenceContainer}>
                  <Text style={styles.evidenceHeader}>ಲಭ್ಯವಿರುವ ಸಾಕ್ಷ್ಯ ಮತ್ತು ಡೇಟಾ:</Text>
                  {advisory.evidence.map((ev: any, idx: number) => (
                    <View key={idx} style={styles.evidenceItem}>
                      <Layers size={12} color={Colors.textSecondary} />
                      <Text style={styles.evidenceItemText}>
                        {ev.type === 'weather'
                          ? `ಹವಾಮಾನ: ${ev.metrics?.rainfall_48h_mm ?? 0} ಮಿ.ಮೀ ಮಳೆ, ${ev.metrics?.humidity_avg_pct ?? 0}% ಆರ್ದ್ರತೆ (${ev.source || 'OpenWeather'})`
                          : ev.type === 'disease'
                          ? `ರೋಗ ಪತ್ತೆ: ${ev.predicted_class} (ವಿಶ್ವಾಸಾರ್ಹತೆ: ${Math.round((ev.confidence || 0) * 100)}%)`
                          : JSON.stringify(ev)}
                      </Text>
                    </View>
                  ))}
                </View>
              )}
            </View>

            {/* Optional Weather Screen Link */}
            {onViewWeather && (
              <TouchableOpacity
                style={styles.weatherNavButton}
                activeOpacity={0.85}
                onPress={() => {
                  onClose();
                  onViewWeather();
                }}
              >
                <CloudSun size={18} color="#FFFFFF" />
                <Text style={styles.weatherNavButtonText}>ಸಂಪೂರ್ಣ ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ ವೀಕ್ಷಿಸಿ</Text>
              </TouchableOpacity>
            )}
          </ScrollView>

          {/* Close Action */}
          <View style={styles.modalFooter}>
            <TouchableOpacity style={styles.doneBtn} activeOpacity={0.8} onPress={onClose}>
              <Text style={styles.doneBtnText}>ಮುಚ್ಚಿ (Close)</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.55)',
    justifyContent: 'flex-end',
  },
  modalCard: {
    backgroundColor: Colors.surface,
    borderTopLeftRadius: BorderRadius.xl,
    borderTopRightRadius: BorderRadius.xl,
    maxHeight: '90%',
    paddingBottom: Spacing.lg,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.md + 4,
    paddingBottom: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
  },
  priorityPill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: BorderRadius.sm,
    borderWidth: 1,
    gap: 4,
  },
  priorityPillText: {
    fontSize: 11,
    fontWeight: '700',
  },
  headerTitle: {
    ...Typography.title2,
    fontSize: 16,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollContent: {
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.md,
    paddingBottom: Spacing.xl,
  },
  mainTitleBox: {
    marginBottom: Spacing.md,
    paddingBottom: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  advisoryTitle: {
    ...Typography.title1,
    fontSize: 19,
    color: Colors.textPrimary,
    fontWeight: '800',
    lineHeight: 26,
    marginBottom: Spacing.xs,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 12,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaText: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.textSecondary,
  },
  metaSubText: {
    fontSize: 12,
    color: Colors.textMuted,
  },
  sectionCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  sectionHeaderRow: {
    marginBottom: Spacing.xs + 2,
  },
  sectionQuestion: {
    fontSize: 14,
    fontWeight: '800',
    color: Colors.primaryDark,
  },
  sectionSubtitle: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginTop: 1,
  },
  sectionBodyText: {
    fontSize: 13,
    color: Colors.textPrimary,
    lineHeight: 20,
  },
  detailActionItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginTop: Spacing.sm,
    gap: 8,
  },
  actionNumberCircle: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  actionNumberText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  detailActionContent: {
    flex: 1,
  },
  detailActionMainText: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.textPrimary,
    lineHeight: 18,
  },
  detailActionSubText: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  actionTimingPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 4,
  },
  actionTimingPillText: {
    fontSize: 11,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  timelineRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 4,
  },
  timelineText: {
    fontSize: 12,
    color: Colors.textPrimary,
    fontWeight: '600',
  },
  trustGrid: {
    flexDirection: 'row',
    gap: 8,
    marginTop: Spacing.xs,
    marginBottom: Spacing.sm,
  },
  trustBox: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    padding: Spacing.sm,
    borderRadius: BorderRadius.sm,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  trustLabel: {
    fontSize: 10,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  trustValueRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 2,
  },
  trustValue: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.primaryDark,
    marginTop: 2,
  },
  sourcesBox: {
    backgroundColor: '#FFFFFF',
    padding: Spacing.sm,
    borderRadius: BorderRadius.sm,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    marginTop: 4,
  },
  sourcesHeader: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textSecondary,
    marginBottom: 4,
  },
  sourceBullet: {
    fontSize: 11,
    color: Colors.textPrimary,
    lineHeight: 16,
  },
  evidenceContainer: {
    marginTop: Spacing.sm,
    backgroundColor: '#FFFFFF',
    padding: Spacing.sm,
    borderRadius: BorderRadius.sm,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  evidenceHeader: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textSecondary,
    marginBottom: 4,
  },
  evidenceItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    marginBottom: 3,
  },
  evidenceItemText: {
    fontSize: 11,
    color: Colors.textPrimary,
    flex: 1,
  },
  weatherNavButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#0284C7',
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.md,
    marginTop: Spacing.xs,
  },
  weatherNavButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  modalFooter: {
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.sm,
  },
  doneBtn: {
    backgroundColor: Colors.primary,
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.md,
    alignItems: 'center',
  },
  doneBtnText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
});
