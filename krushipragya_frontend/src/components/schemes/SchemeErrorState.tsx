import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { AlertCircle, RefreshCw, ArrowLeft } from 'lucide-react-native';

interface SchemeErrorStateProps {
  title?: string;
  subtitle?: string;
  onRetry?: () => void;
  onBack?: () => void;
}

export const SchemeErrorState: React.FC<SchemeErrorStateProps> = ({
  title = 'ಯೋಜನೆಗಳನ್ನು ಲೋಡ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ',
  subtitle = 'ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.',
  onRetry,
  onBack,
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.iconCircle}>
        <AlertCircle size={38} color="#DC2626" />
      </View>

      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>

      <View style={styles.buttonRow}>
        {onBack && (
          <TouchableOpacity
            activeOpacity={0.7}
            onPress={onBack}
            style={styles.backButton}
            accessibilityRole="button"
          >
            <ArrowLeft size={16} color="#374151" style={{ marginRight: 6 }} />
            <Text style={styles.backButtonText}>ಹಿಂದೆ ಹೋಗಿ</Text>
          </TouchableOpacity>
        )}

        {onRetry && (
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={onRetry}
            style={styles.retryButton}
            accessibilityRole="button"
          >
            <RefreshCw size={15} color="#FFFFFF" style={{ marginRight: 6 }} />
            <Text style={styles.retryButtonText}>ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 32,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    marginHorizontal: 16,
    marginVertical: 24,
    borderWidth: 1,
    borderColor: '#FEE2E2',
  },
  iconCircle: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: '#FEF2F2',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 16.5,
    fontWeight: '600',
    color: '#111827',
    textAlign: 'center',
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 14,
    fontWeight: '400',
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 22,
  },
  buttonRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  retryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0F6E56',
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 10,
    shadowColor: '#0F6E56',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 2,
  },
  retryButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
  },
  backButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
});
