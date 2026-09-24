import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, BorderRadius, Spacing, Typography } from '../../constants/theme';
import { useLanguage } from '../../context/LanguageContext';

interface ConfidenceBarProps {
  confidence: number; // 0 to 1
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({ confidence }) => {
  const { t } = useLanguage();
  const percentage = Math.round(confidence * 100);

  const getBarColor = () => {
    if (percentage >= 80) return Colors.aiAnalysed;
    if (percentage >= 50) return Colors.accentGold;
    return Colors.textMuted;
  };

  return (
    <View style={styles.container}>
      <View style={styles.textRow}>
        <Text style={styles.label}>{t.confidenceScore}</Text>
        <Text style={[styles.percentage, { color: getBarColor() }]}>{percentage}%</Text>
      </View>
      <View style={styles.track}>
        <View
          style={[
            styles.fill,
            { width: `${percentage}%`, backgroundColor: getBarColor() },
          ]}
        />
      </View>
      <Text style={styles.hintText}>{t.preliminaryWarning}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: Spacing.sm,
    backgroundColor: Colors.surfaceSubtle,
    padding: Spacing.sm,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  textRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  label: {
    ...Typography.caption,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  percentage: {
    ...Typography.bodyLarge,
    fontWeight: '800',
  },
  track: {
    height: 8,
    backgroundColor: Colors.border,
    borderRadius: 4,
    overflow: 'hidden',
  },
  fill: {
    height: '100%',
    borderRadius: 4,
  },
  hintText: {
    ...Typography.caption,
    color: Colors.textMuted,
    marginTop: 6,
    fontStyle: 'italic',
  },
});
