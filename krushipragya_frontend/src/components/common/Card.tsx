import React from 'react';
import { View, StyleSheet, ViewStyle, TouchableOpacity } from 'react-native';
import { Colors, BorderRadius, Spacing } from '../../constants/theme';

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  onPress?: () => void;
  variant?: 'default' | 'highlight' | 'trust' | 'alert';
}

export const Card: React.FC<CardProps> = ({
  children,
  style,
  onPress,
  variant = 'default',
}) => {
  const getBorderColor = () => {
    switch (variant) {
      case 'highlight':
        return Colors.primary;
      case 'trust':
        return Colors.trustPurple;
      case 'alert':
        return Colors.alertHigh;
      default:
        return Colors.border;
    }
  };

  const Component = onPress ? TouchableOpacity : View;

  return (
    <Component
      activeOpacity={0.85}
      onPress={onPress}
      style={[
        styles.card,
        { borderColor: getBorderColor() },
        variant === 'highlight' && { backgroundColor: Colors.primaryLight },
        style,
      ]}
    >
      {children}
    </Component>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.lg, // 12dp radius
    padding: Spacing.lg,
    borderWidth: 1,
    borderColor: Colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
    marginBottom: Spacing.md,
  },
});
