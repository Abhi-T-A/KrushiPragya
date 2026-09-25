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
import { ArrowRight, Sparkles } from 'lucide-react-native';

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
    id: 'paddy',
    emoji: '🌾',
    nameKn: 'ಭತ್ತ',
    nameEn: 'Paddy',
    diseasesKn: 'ಬೆಂಕಿ ರೋಗ (ಬ್ಲಾಸ್ಟ್), ಎಲೆ ಒಣಗು ರೋಗ, ಕಂದು ಜಿಗಿ ಹುಳು',
    diseasesEn: 'Blast Disease, Bacterial Leaf Blight, Brown Plant Hopper',
    accentColor: '#16A34A',
    bgColor: '#DCFCE7',
  },
  {
    id: 'arecanut',
    emoji: '🌴',
    nameKn: 'ಅಡಿಕೆ',
    nameEn: 'Arecanut',
    diseasesKn: 'ಕೊಳೆರೋಗ (ಮಹಾಲಿ), ಹಳದಿ ಎಲೆ ರೋಗ, ಅನಬೆ ರೋಗ',
    diseasesEn: 'Koleroga (Fruit Rot), Yellow Leaf Disease, Anabe Roga',
    accentColor: '#D97706',
    bgColor: '#FEF3C7',
  },
  {
    id: 'coconut',
    emoji: '🥥',
    nameKn: 'ತೆಂಗು',
    nameEn: 'Coconut',
    diseasesKn: 'ಸುಳಿ ಕೊಳೆ ರೋಗ, ಕಾಂಡ ಸೋರುವಿಕೆ, ಬೇರು ಸೊರಗು ರೋಗ',
    diseasesEn: 'Bud Rot, Stem Bleeding, Leaf Spot, Root Wilt',
    accentColor: '#0284C7',
    bgColor: '#E0F2FE',
  },
  {
    id: 'black_pepper',
    emoji: '🌿',
    nameKn: 'ಕರಿಮೆಣಸು',
    nameEn: 'Black Pepper',
    diseasesKn: 'ಧೃಢ ಸೊರಗು ರೋಗ (Foot Rot), ನಿಧಾನ ಸೊರಗು ರೋಗ, ಪೊಲ್ಲು ರೋಗ',
    diseasesEn: 'Quick Wilt (Foot Rot), Slow Wilt, Pollu Disease, Anthracnose',
    accentColor: '#DC2626',
    bgColor: '#FEE2E2',
  },
  {
    id: 'cardamom',
    emoji: '🌱',
    nameKn: 'ಏಲಕ್ಕಿ',
    nameEn: 'Cardamom',
    diseasesKn: 'ಕಟ್ಟೆ ರೋಗ (ಮೊಸಾಯಿಕ್), ಅಳಿವು ಕೊಳೆ ರೋಗ (Azurukal)',
    diseasesEn: 'Katte Disease (Mosaic), Capsule Rot (Azurukal), Clump Rot',
    accentColor: '#059669',
    bgColor: '#D1FAE5',
  },
  {
    id: 'ginger',
    emoji: '🫚',
    nameKn: 'ಶುಂಠಿ',
    nameEn: 'Ginger',
    diseasesKn: 'ಮೃದು ಕೊಳೆ ರೋಗ (Soft Rot), ಬ್ಯಾಕ್ಟೀರಿಯಲ್ ಸೊರಗು ರೋಗ',
    diseasesEn: 'Soft Rot (Rhizome Rot), Bacterial Wilt, Leaf Spot',
    accentColor: '#CA8A04',
    bgColor: '#FEF08A',
  },
  {
    id: 'turmeric',
    emoji: '🌾',
    nameKn: 'ಅರಿಶಿನ',
    nameEn: 'Turmeric',
    diseasesKn: 'ಎಲೆ ಚುಕ್ಕೆ ರೋಗ, ಎಲೆ ಕರಕಲು ರೋಗ, ಗೆಡ್ಡೆ ಕೊಳೆ ರೋಗ',
    diseasesEn: 'Leaf Spot, Leaf Blotch, Rhizome Rot',
    accentColor: '#EA580C',
    bgColor: '#FFEDD5',
  },
];

export const CropSelectScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const { language } = useLanguage();
  const isKn = language === 'kn';

  const handleSelectCrop = (crop: SupportedCrop) => {
    navigation.navigate('CameraCapture', { crop: crop.id, cropNameKn: crop.nameKn, cropNameEn: crop.nameEn });
  };

  return (
    <View style={styles.container}>
      <Header title={isKn ? 'ಬೆಳೆ ಆಯ್ಕೆಮಾಡಿ' : 'Select Crop for AI Diagnosis'} />

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.introBanner}>
          <Sparkles size={16} color="#D97706" />
          <Text style={styles.introText}>
            {isKn
              ? '7 ಪ್ರಮುಖ ಬೆಳೆಗಳ ರೋಗ ಪತ್ತೆಗಾಗಿ ಐಸಿಎಆರ್ (ICAR) ಮಾದರಿಗಳು ಲಭ್ಯವಿವೆ'
              : 'Instant crop health checkup ready for 7 regional crops'}
          </Text>
        </View>

        <View style={styles.cropList}>
          {SUPPORTED_CROPS.map((crop) => (
            <TouchableOpacity
              key={crop.id}
              activeOpacity={0.85}
              onPress={() => handleSelectCrop(crop)}
              style={styles.cropCard}
            >
              <View style={[styles.emojiCircle, { backgroundColor: crop.bgColor }]}>
                <Text style={styles.emojiText}>{crop.emoji}</Text>
              </View>

              <View style={styles.cropInfo}>
                <Text style={styles.cropName}>
                  {isKn ? `${crop.nameKn} (${crop.nameEn})` : `${crop.nameEn} (${crop.nameKn})`}
                </Text>
                <Text style={styles.diseasesText} numberOfLines={2}>
                  {isKn ? crop.diseasesKn : crop.diseasesEn}
                </Text>
              </View>

              <View style={[styles.arrowCircle, { backgroundColor: crop.bgColor }]}>
                <ArrowRight size={16} color={crop.accentColor} strokeWidth={2.4} />
              </View>
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
    backgroundColor: '#F8FAFC',
  },
  scrollContent: {
    padding: Spacing.md,
    paddingBottom: 40,
  },
  introBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FEF3C7',
    borderWidth: 1,
    borderColor: '#FDE68A',
    borderRadius: 10,
    padding: 12,
    marginBottom: Spacing.md,
  },
  introText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#92400E',
    flex: 1,
    lineHeight: 16,
  },
  cropList: {
    gap: 10,
  },
  cropCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 12,
    padding: 12,
    gap: 12,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  emojiCircle: {
    width: 44,
    height: 44,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emojiText: {
    fontSize: 22,
  },
  cropInfo: {
    flex: 1,
  },
  cropName: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
    marginBottom: 2,
  },
  diseasesText: {
    fontSize: 11,
    color: '#64748B',
    lineHeight: 15,
  },
  arrowCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
});