import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Bookmark, SearchX, ArrowRight } from 'lucide-react-native';

interface SchemeEmptyStateProps {
  type?: 'saved' | 'search' | 'default';
  title?: string;
  subtitle?: string;
  buttonText?: string;
  onButtonPress?: () => void;
}

export const SchemeEmptyState: React.FC<SchemeEmptyStateProps> = ({
  type = 'default',
  title,
  subtitle,
  buttonText,
  onButtonPress,
}) => {
  const getDefaultContent = () => {
    if (type === 'saved') {
      return {
        title: 'ಯಾವುದೇ ಯೋಜನೆಗಳನ್ನು ಉಳಿಸಿಲ್ಲ',
        subtitle: 'ನಿಮಗೆ ಉಪಯುಕ್ತವಾದ ಯೋಜನೆಗಳನ್ನು ಉಳಿಸಿ, ನಂತರ ಸುಲಭವಾಗಿ ನೋಡಬಹುದು.',
        buttonText: 'ಯೋಜನೆಗಳನ್ನು ನೋಡಿ',
        icon: <Bookmark size={36} color="#0F6E56" strokeWidth={1.7} />,
      };
    }
    if (type === 'search') {
      return {
        title: 'ಯಾವುದೇ ಯೋಜನೆಗಳು ಕಂಡುಬಂದಿಲ್ಲ',
        subtitle: 'ದಯವಿಟ್ಟು ಬೇರೆ ಕೀವರ್ಡ್ ಅಥವಾ ವಿಭಾಗವನ್ನು ಆಯ್ಕೆ ಮಾಡಿ ಪ್ರಯತ್ನಿಸಿ.',
        buttonText: 'ಎಲ್ಲಾ ಯೋಜನೆಗಳನ್ನು ನೋಡಿ',
        icon: <SearchX size={36} color="#0F6E56" strokeWidth={1.7} />,
      };
    }
    return {
      title: 'ಯಾವುದೇ ಯೋಜನೆಗಳು ಲಭ್ಯವಿಲ್ಲ',
      subtitle: 'ಪ್ರಸ್ತುತ ಈ ವಿಭಾಗದಲ್ಲಿ ಯಾವುದೇ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು ಲಭ್ಯವಿಲ್ಲ.',
      buttonText: 'ಮರುಲೋಡ್ ಮಾಡಿ',
      icon: <Bookmark size={36} color="#0F6E56" strokeWidth={1.7} />,
    };
  };

  const defaultContent = getDefaultContent();
  const displayTitle = title || defaultContent.title;
  const displaySubtitle = subtitle || defaultContent.subtitle;
  const displayButtonText = buttonText || defaultContent.buttonText;

  return (
    <View style={styles.container}>
      <View style={styles.iconCircle}>
        {defaultContent.icon}
      </View>
      <Text style={styles.title}>{displayTitle}</Text>
      <Text style={styles.subtitle}>{displaySubtitle}</Text>

      {onButtonPress && (
        <TouchableOpacity
          activeOpacity={0.8}
          onPress={onButtonPress}
          style={styles.actionButton}
          accessibilityRole="button"
        >
          <Text style={styles.buttonText}>{displayButtonText}</Text>
          <ArrowRight size={16} color="#FFFFFF" style={{ marginLeft: 6 }} />
        </TouchableOpacity>
      )}
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
    marginVertical: 20,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  iconCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#EAF7EE',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 17,
    fontWeight: '600',
    color: '#111827',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 13.5,
    fontWeight: '400',
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 20,
    maxWidth: 280,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0F6E56',
    paddingHorizontal: 20,
    paddingVertical: 11,
    borderRadius: 10,
    shadowColor: '#0F6E56',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 2,
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
