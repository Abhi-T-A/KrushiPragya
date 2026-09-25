import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { useLanguage } from '../../context/LanguageContext';
import { Header } from '../../components/common/Header';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { ArrowRight } from 'lucide-react-native';

export interface SupportedCrop {
  id: string;
  emoji: string;
  nameKn: string;
  nameEn: string;
  diseasesKn: string;
  diseasesEn: string;
  accentColor: string;
  bgColor: string;
}

export const SUPPORTED_CROPS: SupportedCrop[] = [
  {
    id: 'arecanut',
    emoji: '🌴',
    nameKn: 'ಅಡಿಕೆ',
    nameEn: 'Arecanut',
    diseasesKn: 'ಮಹಾಳಿ/ಕೊಳೆರೋಗ, ಹಳದಿ ಎಲೆ ರೋಗ, ಸುಳಿ ಕೊಳೆ, ಅನಬೆ ರೋಗ',
    diseasesEn: 'Koleroga (Fruit Rot), Yellow Leaf Disease, Bud Rot, Anabe Roga',
    accentColor: Colors.primary,
    bgColor: Colors.primaryLight,
  },
  {
    id: 'paddy',
    emoji: '🌾',
    nameKn: 'ಭತ್ತ',
    nameEn: 'Paddy',
    diseasesKn: 'ಬ್ಲಾಸ್ಟ್ ರೋಗ, ಬ್ಯಾಕ್ಟೀರಿಯಲ್ ಎಲೆ ಉರಿ, ಕಂದು ಜಿಗಿಹುಳು, ಸೀತ್ ಬ್ಲೈಟ್',
    diseasesEn: 'Blast Disease, Bacterial Leaf Blight, Brown Plant Hopper, Sheath Blight',
    accentColor: '#D97706',
    bgColor: '#FEF3C7',
  },
  {
    id: 'coconut',
    emoji: '🥥',
    nameKn: 'ತೆಂಗು',
    nameEn: 'Coconut',
    diseasesKn: 'ಬುಡ ಕೊಳೆತ, ಸುಳಿ ಕೊಳೆ, ಕಾಂಡ ಸೋರಿಕೆ ರೋಗ, ಎಲೆ ಚುಕ್ಕೆ',
    diseasesEn: 'Bud Rot, Stem Bleeding, Leaf Spot, Root Wilt',
    accentColor: '#0284C7',
    bgColor: '#E0F2FE',
  },
  {
    id: 'black_pepper',
    emoji: '🌶',
    nameKn: 'ಕಾಳುಮೆಣಸು',
    nameEn: 'Black Pepper',
    diseasesKn: 'ಶೀಘ್ರ ಸೊರಗು ರೋಗ (Foot Rot), ನಿಧಾನ ಸೊರಗು, ಪರಾಗು ರೋಗ',
    diseasesEn: 'Quick Wilt (Foot Rot), Slow Wilt, Pollu Disease, Anthracnose',
    accentColor: '#DC2626',
    bgColor: '#FEE2E2',
  },
  {
    id: 'cardamom',
    emoji: '🌿',
    nameKn: 'ಏಲಕ್ಕಿ',
    nameEn: 'Cardamom',
    diseasesKn: 'ಕಟ್ಟೆ ರೋಗ (Katte/Mosaic), ಕೊಳೆ ರೋಗ (Azhukal), ನರ್ಸರಿ ಸೊರಗು',
    diseasesEn: 'Katte (Mosaic Disease), Azhukal (Capsule Rot), Damping Off',
    accentColor: '#059669',
    bgColor: '#D1FAE5',
  },
  {
    id: 'turmeric',
    emoji: '🟡',
    nameKn: 'ಅರಿಶಿನ',
    nameEn: 'Turmeric',
    diseasesKn: 'ಗೆಡ್ಡೆ ಕೊಳೆತ (Rhizome Rot), ಎಲೆ ಚುಕ್ಕೆ, ಎಲೆ ಸುರುಳಿ ರೋಗ',
    diseasesEn: 'Rhizome Rot, Leaf Spot (Colletotrichum), Leaf Blotch',
    accentColor: '#CA8A04',
    bgColor: '#FEF9C3',
  },
  {
    id: 'ginger',
    emoji: '🫚',
    nameKn: 'ಶುಂಠಿ',
    nameEn: 'Ginger',
    diseasesKn: 'ಮೆದು ಕೊಳೆತ ರೋಗ (Soft Rot), ಬ್ಯಾಕ್ಟೀರಿಯಲ್ ಸೊರಗು, ಎಲೆ ಚುಕ್ಕೆ',
    diseasesEn: 'Soft Rot (Rhizome Rot), Bacterial Wilt, Leaf Spot',
    accentColor: '#EA580C',
    bgColor: '#FFEDD5',
  },
];

export const CropSelectScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const { language } = useLanguage();

  const handleSelectCrop = (cropId: string) => {
    navigation.navigate('CameraCapture', { crop: cropId });
  };

  return (
    <View style={styles.container}>
      <Header
        title={language === 'kn' ? 'ಯಾವ ಬೆಳೆ?' : 'Which Crop?'}
        showVillage={false}
      />

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Text style={styles.subtitle}>
          {language === 'kn'
            ? 'ರೋಗಲಕ್ಷಣವಿರುವ ನಿಮ್ಮ ಬೆಳೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ (7 ಮಾದರಿಗಳು ಲಭ್ಯ)'
            : 'Select the crop with symptoms (7 AI Models available)'}
        </Text>

        <View style={styles.cropsList}>
          {SUPPORTED_CROPS.map((crop) => (
            <TouchableOpacity
              key={crop.id}
              activeOpacity={0.85}
              onPress={() => handleSelectCrop(crop.id)}
              style={[styles.cropCard, { borderColor: crop.accentColor }]}
            >
              <View style={[styles.emojiContainer, { backgroundColor: crop.bgColor }]}>
                <Text style={styles.emojiText}>{crop.emoji}</Text>
              </View>

              <View style={styles.cropTextCol}>
                <Text style={styles.cropTitle}>
                  {crop.nameKn} ({crop.nameEn})
                </Text>
                <Text style={styles.cropDescription} numberOfLines={2}>
                  {language === 'kn' ? crop.diseasesKn : crop.diseasesEn}
                </Text>
              </View>

              <ArrowRight size={22} color={crop.accentColor} />
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    padding: Spacing.lg,
    paddingTop: Spacing.xs,
    paddingBottom: Spacing.xxxl * 1.5,
  },
  subtitle: {
    ...Typography.bodyLarge,
    fontSize: 14,
    color: Colors.textSecondary,
    marginBottom: Spacing.md,
  },
  cropsList: {
    gap: Spacing.md,
  },
  cropCard: {
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.xl,
    padding: Spacing.md + 2,
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
    borderWidth: 2,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
  },
  emojiContainer: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emojiText: {
    fontSize: 26,
  },
  cropTextCol: {
    flex: 1,
    gap: 2,
  },
  cropTitle: {
    ...Typography.title2,
    fontSize: 17,
    color: Colors.textPrimary,
    fontWeight: '800',
  },
  cropDescription: {
    ...Typography.caption,
    color: Colors.textSecondary,
    lineHeight: 16,
  },
});
