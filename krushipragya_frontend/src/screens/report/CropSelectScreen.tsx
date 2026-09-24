import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useLanguage } from '../../context/LanguageContext';
import { Header } from '../../components/common/Header';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { ArrowRight } from 'lucide-react-native';

export const CropSelectScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const { t } = useLanguage();

  const handleSelectCrop = (crop: 'arecanut' | 'paddy') => {
    navigation.navigate('CameraCapture', { crop });
  };

  return (
    <View style={styles.container}>
      <Header title={t.selectCropTitle} showVillage={false} />

      <View style={styles.content}>
        <Text style={styles.subtitle}>{t.selectCropSub}</Text>

        {/* Big Arecanut Button */}
        <TouchableOpacity
          activeOpacity={0.85}
          onPress={() => handleSelectCrop('arecanut')}
          style={[styles.cropCard, { borderColor: Colors.primary }]}
        >
          <View style={styles.emojiContainer}>
            <Text style={styles.emojiText}>🌴</Text>
          </View>
          <View style={styles.cropTextCol}>
            <Text style={styles.cropTitle}>ಅಡಿಕೆ (Arecanut)</Text>
            <Text style={styles.cropDescription}>
              ಮಹಾಳಿ, ಕೊಳೆರೋಗ, ಹಳದಿ ಎಲೆ ರೋಗ, ಸುಳಿ ಕೊಳೆ
            </Text>
          </View>
          <ArrowRight size={24} color={Colors.primary} />
        </TouchableOpacity>

        {/* Big Paddy Button */}
        <TouchableOpacity
          activeOpacity={0.85}
          onPress={() => handleSelectCrop('paddy')}
          style={[styles.cropCard, { borderColor: Colors.accentGold }]}
        >
          <View style={[styles.emojiContainer, { backgroundColor: '#FEF3C7' }]}>
            <Text style={styles.emojiText}>🌾</Text>
          </View>
          <View style={styles.cropTextCol}>
            <Text style={styles.cropTitle}>ಭತ್ತ (Paddy)</Text>
            <Text style={styles.cropDescription}>
              ಬ್ಲಾಸ್ಟ್ ರೋಗ, ಬ್ಯಾಕ್ಟೀರಿಯಲ್ ಎಲೆ ಉರಿ, ಕಂದು ಜಿಗಿಹುಳು
            </Text>
          </View>
          <ArrowRight size={24} color={Colors.accentGold} />
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    padding: Spacing.lg,
    gap: Spacing.lg,
  },
  subtitle: {
    ...Typography.bodyLarge,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  cropCard: {
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.xl,
    padding: Spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
    borderWidth: 2,
    elevation: 3,
  },
  emojiContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: Colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emojiText: {
    fontSize: 32,
  },
  cropTextCol: {
    flex: 1,
  },
  cropTitle: {
    ...Typography.title1,
    color: Colors.textPrimary,
    fontWeight: '800',
  },
  cropDescription: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 4,
  },
});
