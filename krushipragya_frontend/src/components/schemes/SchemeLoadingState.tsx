import React from 'react';
import { View, StyleSheet, ActivityIndicator, Text } from 'react-native';

export const SchemeLoadingState: React.FC<{ message?: string }> = ({
  message = 'ಯೋಜನೆಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...',
}) => {
  return (
    <View style={styles.container}>
      {/* Central Indicator */}
      <View style={styles.spinnerRow}>
        <ActivityIndicator size="large" color="#0F6E56" />
        <Text style={styles.spinnerText}>{message}</Text>
      </View>

      {/* 2 Skeleton Cards */}
      {[1, 2].map((key) => (
        <View key={key} style={styles.skeletonCard}>
          <View style={styles.skeletonImage} />
          <View style={styles.skeletonBody}>
            <View style={styles.skeletonTitle} />
            <View style={styles.skeletonSubtitle} />
            <View style={styles.skeletonMetaRow}>
              <View style={styles.skeletonSmallBar} />
              <View style={styles.skeletonBadge} />
            </View>
          </View>
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingVertical: 12,
  },
  spinnerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    gap: 10,
  },
  spinnerText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#0F6E56',
  },
  skeletonCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    overflow: 'hidden',
  },
  skeletonImage: {
    width: '100%',
    height: 120,
    backgroundColor: '#E5E7EB',
  },
  skeletonBody: {
    padding: 14,
  },
  skeletonTitle: {
    width: '75%',
    height: 18,
    backgroundColor: '#E5E7EB',
    borderRadius: 4,
    marginBottom: 8,
  },
  skeletonSubtitle: {
    width: '45%',
    height: 14,
    backgroundColor: '#F3F4F6',
    borderRadius: 4,
    marginBottom: 12,
  },
  skeletonMetaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  skeletonSmallBar: {
    width: '35%',
    height: 12,
    backgroundColor: '#F3F4F6',
    borderRadius: 4,
  },
  skeletonBadge: {
    width: 60,
    height: 22,
    backgroundColor: '#E5E7EB',
    borderRadius: 6,
  },
});
