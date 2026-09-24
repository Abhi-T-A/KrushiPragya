import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, BorderRadius, Spacing, Typography } from '../../constants/theme';
import { useLanguage } from '../../context/LanguageContext';

export type LadderStatus = 'unverified' | 'ai_analysed' | 'corroborated' | 'expert_verified';

interface StatusBadgeProps {
  status: LadderStatus;
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const { t } = useLanguage();

  const getBadgeConfig = () => {
    switch (status) {
      case 'unverified':
        return {
          label: t.trustUnverified,
          bg: Colors.unverifiedBg,
          color: Colors.unverified,
          dot: '○',
        };
      case 'ai_analysed':
        return {
          label: t.trustAIAnalysed,
          bg: Colors.aiAnalysedBg,
          color: Colors.aiAnalysed,
          dot: '◐',
        };
      case 'corroborated':
        return {
          label: t.trustCorroborated,
          bg: Colors.corroboratedBg,
          color: Colors.corroborated,
          dot: '◕',
        };
      case 'expert_verified':
        return {
          label: t.trustExpertVerified,
          bg: Colors.expertVerifiedBg,
          color: Colors.expertVerified,
          dot: '●',
        };
      default:
        return {
          label: t.trustUnverified,
          bg: Colors.unverifiedBg,
          color: Colors.unverified,
          dot: '○',
        };
    }
  };

  const config = getBadgeConfig();

  return (
    <View style={[styles.badge, { backgroundColor: config.bg }]}>
      <Text style={[styles.dot, { color: config.color }]}>{config.dot}</Text>
      <Text style={[styles.text, { color: config.color }]}>{config.label}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: 5,
    paddingHorizontal: Spacing.sm + 2,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
  },
  dot: {
    fontSize: 12,
    fontWeight: '800',
  },
  text: {
    ...Typography.caption,
    fontWeight: '700',
  },
});
