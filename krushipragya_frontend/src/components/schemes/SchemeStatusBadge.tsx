import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface SchemeStatusBadgeProps {
  label: string;
  variant?: 'primary' | 'success' | 'warning' | 'info' | 'neutral';
  icon?: React.ReactNode;
}

export const SchemeStatusBadge: React.FC<SchemeStatusBadgeProps> = ({
  label,
  variant = 'primary',
  icon,
}) => {
  const getBadgeStyle = () => {
    switch (variant) {
      case 'success':
        return { container: styles.successBg, text: styles.successText };
      case 'warning':
        return { container: styles.warningBg, text: styles.warningText };
      case 'info':
        return { container: styles.infoBg, text: styles.infoText };
      case 'neutral':
        return { container: styles.neutralBg, text: styles.neutralText };
      case 'primary':
      default:
        return { container: styles.primaryBg, text: styles.primaryText };
    }
  };

  const styleConfig = getBadgeStyle();

  return (
    <View style={[styles.badge, styleConfig.container]}>
      {icon && <View style={styles.iconBox}>{icon}</View>}
      <Text style={[styles.label, styleConfig.text]} numberOfLines={1}>
        {label}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  iconBox: {
    marginRight: 4,
  },
  label: {
    fontSize: 12,
    fontWeight: '500',
    letterSpacing: 0.1,
  },
  primaryBg: {
    backgroundColor: '#E8F5E9',
    borderColor: '#C8E6C9',
    borderWidth: 1,
  },
  primaryText: {
    color: '#1B5E20',
  },
  successBg: {
    backgroundColor: '#EAF7EE',
    borderColor: '#C2E8CE',
    borderWidth: 1,
  },
  successText: {
    color: '#0F6E56',
  },
  warningBg: {
    backgroundColor: '#FFF8E1',
    borderColor: '#FFE082',
    borderWidth: 1,
  },
  warningText: {
    color: '#8D6E63',
  },
  infoBg: {
    backgroundColor: '#E3F2FD',
    borderColor: '#BBDEFB',
    borderWidth: 1,
  },
  infoText: {
    color: '#1565C0',
  },
  neutralBg: {
    backgroundColor: '#F3F4F6',
    borderColor: '#E5E7EB',
    borderWidth: 1,
  },
  neutralText: {
    color: '#4B5563',
  },
});
