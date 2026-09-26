import React, { useState } from 'react';
import { TouchableOpacity, StyleSheet, ActivityIndicator, View } from 'react-native';
import { Bookmark } from 'lucide-react-native';

interface SchemeBookmarkButtonProps {
  isSaved: boolean;
  onToggle: () => Promise<void> | void;
  size?: 'small' | 'medium' | 'large';
  showBackground?: boolean;
}

export const SchemeBookmarkButton: React.FC<SchemeBookmarkButtonProps> = ({
  isSaved,
  onToggle,
  size = 'medium',
  showBackground = true,
}) => {
  const [loading, setLoading] = useState(false);

  const iconSize = size === 'small' ? 18 : size === 'large' ? 24 : 20;
  const buttonPadding = size === 'small' ? 6 : size === 'large' ? 12 : 8;

  const handlePress = async () => {
    if (loading) return;
    try {
      setLoading(true);
      await onToggle();
    } finally {
      setLoading(false);
    }
  };

  return (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel={isSaved ? 'ಯೋಜನೆ ಉಳಿಸಲಾಗಿದೆ' : 'ಯೋಜನೆ ಉಳಿಸಿ'}
      activeOpacity={0.7}
      onPress={handlePress}
      disabled={loading}
      style={[
        styles.button,
        showBackground && (isSaved ? styles.buttonSavedBg : styles.buttonNormalBg),
        { padding: buttonPadding },
      ]}
    >
      {loading ? (
        <ActivityIndicator size="small" color="#0F6E56" />
      ) : (
        <Bookmark
          size={iconSize}
          color={isSaved ? '#0F6E56' : '#6B7280'}
          fill={isSaved ? '#0F6E56' : 'transparent'}
          strokeWidth={2}
        />
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 36,
    minHeight: 36,
  },
  buttonNormalBg: {
    backgroundColor: '#F3F4F6',
  },
  buttonSavedBg: {
    backgroundColor: '#EAF7EE',
  },
});
