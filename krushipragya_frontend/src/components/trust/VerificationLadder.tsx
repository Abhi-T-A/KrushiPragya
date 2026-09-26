import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { useLanguage } from '../../context/LanguageContext';
import { LadderStatus } from './StatusBadge';
import { CheckCircle2, CircleDot, AlertTriangle } from 'lucide-react-native';

interface VerificationLadderProps {
  status: LadderStatus;
  evidenceFarmsCount?: number;
  verifiedBy?: string;
  verifiedAt?: string;
}

export const VerificationLadder: React.FC<VerificationLadderProps> = ({
  status,
  evidenceFarmsCount = 1,
  verifiedBy,
  verifiedAt,
}) => {
  const { t } = useLanguage();

  const stages: { key: LadderStatus; title: string; subtitle: string }[] = [
    {
      key: 'unverified',
      title: t.trustUnverified,
      subtitle: 'ರೈತರು ಸಲ್ಲಿಸಿದ ಪ್ರಾಥಮಿಕ ವರದಿ',
    },
    {
      key: 'ai_analysed',
      title: t.trustAIAnalysed,
      subtitle: 'ಪ್ರಾಥಮಿಕ ವಿಶ್ಲೇಷಣೆ — ಐಸಿಎಆರ್ ಜ್ಞಾನಕೋಶ',
    },
    {
      key: 'corroborated',
      title: t.trustCorroborated,
      subtitle: `${evidenceFarmsCount}+ ಸ್ವತಂತ್ರ ತೋಟಗಳಲ್ಲಿ ಇದೇ ಲಕ್ಷಣ`,
    },
    {
      key: 'expert_verified',
      title: t.trustExpertVerified,
      subtitle: verifiedBy ? `${verifiedBy}` : 'ಕೃಷಿ ಅಧಿಕಾರಿಗಳಿಂದ ಪರಿಶೀಲಿಸಲಾಗಿದೆ',
    },
  ];

  const getStageIndex = (s: LadderStatus) => {
    const normalized = (s || '').toLowerCase();
    switch (normalized) {
      case 'unverified':
        return 0;
      case 'ai_analysed':
        return 1;
      case 'corroborated':
        return 2;
      case 'expert_verified':
        return 3;
      default:
        return 0;
    }
  };

  const currentIndex = getStageIndex(status);

  return (
    <View style={styles.container}>
      <Text style={styles.headerTitle}>ಪರಿಶೀಲನೆ ಸ್ಥಿತಿ ಹಂತಗಳು (Verification Ladder)</Text>

      {stages.map((stage, idx) => {
        const isCompleted = idx <= currentIndex;
        const isCurrent = idx === currentIndex;

        return (
          <View key={stage.key} style={styles.stageRow}>
            {/* Timeline indicator */}
            <View style={styles.indicatorCol}>
              <View
                style={[
                  styles.circle,
                  isCompleted && styles.circleCompleted,
                  isCurrent && styles.circleCurrent,
                ]}
              >
                {isCompleted ? (
                  <CheckCircle2 size={16} color={isCurrent ? Colors.primaryDark : Colors.textWhite} />
                ) : (
                  <Text style={styles.circleNumber}>{idx + 1}</Text>
                )}
              </View>
              {idx < stages.length - 1 && (
                <View
                  style={[
                    styles.connectorLine,
                    idx < currentIndex && styles.connectorActive,
                  ]}
                />
              )}
            </View>

            {/* Stage text */}
            <View style={styles.textCol}>
              <Text
                style={[
                  styles.stageTitle,
                  isCurrent && styles.currentStageTitle,
                  !isCompleted && styles.futureStageTitle,
                ]}
              >
                {stage.title}
              </Text>
              <Text style={styles.stageSubtitle}>{stage.subtitle}</Text>
              {stage.key === 'corroborated' && isCompleted && (
                <View style={styles.corroborationNotice}>
                  <AlertTriangle size={14} color={Colors.corroborated} />
                  <Text style={styles.corroborationNoticeText}>
                    {t.corroborationNotice}
                  </Text>
                </View>
              )}
              {stage.key === 'expert_verified' && isCompleted && verifiedAt && (
                <Text style={styles.verifiedAtText}>ದೃಢೀಕರಿಸಿದ ಸಮಯ: {verifiedAt}</Text>
              )}
            </View>
          </View>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.surface,
    padding: Spacing.md,
    borderRadius: BorderRadius.lg,
    borderWidth: 1,
    borderColor: Colors.border,
    marginVertical: Spacing.sm,
  },
  headerTitle: {
    ...Typography.title2,
    color: Colors.textPrimary,
    marginBottom: Spacing.md,
  },
  stageRow: {
    flexDirection: 'row',
    marginBottom: Spacing.sm,
  },
  indicatorCol: {
    alignItems: 'center',
    width: 32,
    marginRight: Spacing.sm,
  },
  circle: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  circleCompleted: {
    backgroundColor: Colors.primary,
  },
  circleCurrent: {
    backgroundColor: Colors.accentGold,
  },
  circleNumber: {
    ...Typography.caption,
    color: Colors.textSecondary,
    fontWeight: '700',
  },
  connectorLine: {
    width: 2,
    flex: 1,
    backgroundColor: Colors.border,
    minHeight: 28,
    marginVertical: 2,
  },
  connectorActive: {
    backgroundColor: Colors.primary,
  },
  textCol: {
    flex: 1,
    paddingBottom: Spacing.sm,
  },
  stageTitle: {
    ...Typography.bodyLarge,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  currentStageTitle: {
    color: Colors.primary,
  },
  futureStageTitle: {
    color: Colors.textMuted,
  },
  stageSubtitle: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  corroborationNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: Colors.corroboratedBg,
    padding: Spacing.xs + 2,
    borderRadius: BorderRadius.sm,
    marginTop: 4,
  },
  corroborationNoticeText: {
    ...Typography.caption,
    color: Colors.corroborated,
    fontWeight: '600',
    flex: 1,
  },
  verifiedAtText: {
    ...Typography.caption,
    color: Colors.expertVerified,
    fontWeight: '600',
    marginTop: 4,
  },
});
