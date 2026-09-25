import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { Button } from '../../components/common/Button';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import {
  ArrowLeft,
  ChevronRight,
  Sparkles,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react-native';

const { width } = Dimensions.get('window');

interface OnboardingScreenProps {
  onFinish: () => void;
  onBack?: () => void;
}

export const OnboardingScreen: React.FC<OnboardingScreenProps> = ({
  onFinish,
  onBack,
}) => {
  const { language } = useLanguage();
  const [currentSlide, setCurrentSlide] = useState(0);

  const slides = [
    // Slide 1: Crop Health / AI Diagnosis
    {
      id: 1,
      image: require('../../../assets/onboarding_1.jpg'),
      badgeIcon: <Sparkles size={14} color={Colors.accentGold} />,
      badgeKn: 'AI ಬೆಳೆ ಆರೋಗ್ಯ',
      badgeEn: 'AI Crop Health',
      titleKn: 'ಬೆಳೆಯ ಸಮಸ್ಯೆಯ\nಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ',
      titleEn: 'Capture Crop Problem\nin 1 Tap',
      descKn: 'AI ನಿಮ್ಮ ಬೆಳೆಯ ಸಮಸ್ಯೆಯನ್ನು ಪ್ರಾಥಮಿಕವಾಗಿ ವಿಶ್ಲೇಷಿಸಲು ಸಹಾಯ ಮಾಡುತ್ತದೆ. ICAR ಮಾರ್ಗದರ್ಶನದ ಸೂಕ್ತ ಔಷಧ ತಿಳಿಯಿರಿ.',
      descEn: 'AI assists with preliminary symptom analysis. Get authentic ICAR-CPCRI remedy guidance.',
      accentColor: Colors.primary,
    },
    // Slide 2: Hyper-Local Weather Advisory
    {
      id: 2,
      image: require('../../../assets/onboarding_2.jpg'),
      badgeIcon: <ShieldCheck size={14} color={Colors.primary} />,
      badgeKn: 'ಗ್ರಾಮ ಹವಾಮಾನ',
      badgeEn: 'Village Weather',
      titleKn: 'ನಿಮ್ಮ ಗ್ರಾಮದ\nಹವಾಮಾನ ಮತ್ತು ಅಪಾಯ',
      titleEn: 'Hyper-Local Weather\n& Disease Risk',
      descKn: 'ಮಳೆ, ತಾಪಮಾನ ಮತ್ತು ತೇವಾಂಶದ ಆಧಾರದ ಮೇಲೆ ಮಹಾಳಿ ಮತ್ತು ಬ್ಲಾಸ್ಟ್ ರೋಗಗಳ ಮುನ್ಸೂಚನೆ ಹಾಗೂ ಕೃಷಿ ಸಲಹೆ ಪಡೆಯಿರಿ.',
      descEn: 'Rule-based disease risk warnings (Koleroga & Blast) based on humidity and rainfall patterns.',
      accentColor: Colors.accentGold,
    },
    // Slide 3: All-in-One Farm Intelligence
    {
      id: 3,
      image: require('../../../assets/onboarding_3.jpg'),
      badgeIcon: <TrendingUp size={14} color={Colors.trustPurple} />,
      badgeKn: 'ಸಮಗ್ರ ಕೃಷಿ ವೇದಿಕೆ',
      badgeEn: 'All-in-One Intelligence',
      titleKn: 'ಒಂದೇ ಅಪ್ಲಿಕೇಶನ್‌ನಲ್ಲಿ\nಸಮಗ್ರ ಕೃಷಿ ನೆರವು',
      titleEn: 'Complete Farm Network\nin One App',
      descKn: 'ಬೆಳೆ ಆರೋಗ್ಯ, ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ, ಪಾರದರ್ಶಕ ಮಂಡಿ ಬೆಲೆಗಳು ಮತ್ತು ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಮಾಹಿತಿ ಒಂದೇ ಕಡೆ.',
      descEn: 'Crop health diagnosis, weather advisories, transparent mandi price comparisons, and official schemes.',
      accentColor: Colors.trustPurple,
    },
  ];

  const slide = slides[currentSlide];

  const handleNext = () => {
    if (currentSlide < slides.length - 1) {
      setCurrentSlide(currentSlide + 1);
    } else {
      onFinish();
    }
  };

  const handlePrev = () => {
    if (currentSlide > 0) {
      setCurrentSlide(currentSlide - 1);
    } else if (onBack) {
      onBack();
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        {/* Top Header Bar with BACK BUTTON and SKIP BUTTON */}
        <View style={styles.topBar}>
          <TouchableOpacity
            activeOpacity={0.7}
            onPress={handlePrev}
            style={styles.backButton}
          >
            <ArrowLeft size={22} color={Colors.textPrimary} />
          </TouchableOpacity>

          <View style={styles.badgePill}>
            {slide.badgeIcon}
            <Text style={styles.badgeText}>
              {language === 'kn' ? slide.badgeKn : slide.badgeEn}
            </Text>
          </View>

          <TouchableOpacity onPress={onFinish} style={styles.skipButton}>
            <Text style={styles.skipText}>
              {language === 'kn' ? 'ಬಿಟ್ಟುಬಿಡಿ' : 'Skip'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Center Section: Beautiful High-Resolution Realistic Circular Hero Image */}
        <View style={styles.centerSection}>
          <View style={[styles.imageCircleWrapper, { borderColor: slide.accentColor }]}>
            <Image
              source={slide.image}
              style={styles.heroImage}
              resizeMode="cover"
            />
          </View>

          {/* Title */}
          <Text style={styles.titleText}>
            {language === 'kn' ? slide.titleKn : slide.titleEn}
          </Text>

          {/* Description */}
          <Text style={styles.descText}>
            {language === 'kn' ? slide.descKn : slide.descEn}
          </Text>

          {/* Feature Highlights for Slide 3 */}
          {slide.id === 3 && (
            <View style={styles.featurePillsRow}>
              <View style={[styles.featurePill, { borderColor: '#BFE7D7' }]}>
                <Text style={styles.featurePillText}>🌱 {language === 'kn' ? 'ಬೆಳೆ ಆರೋಗ್ಯ' : 'Crop Health'}</Text>
              </View>
              <View style={[styles.featurePill, { borderColor: '#FEF3C7' }]}>
                <Text style={styles.featurePillText}>🌦️ {language === 'kn' ? 'ಹವಾಮಾನ' : 'Weather'}</Text>
              </View>
              <View style={[styles.featurePill, { borderColor: '#FED7AA' }]}>
                <Text style={styles.featurePillText}>💰 {language === 'kn' ? 'ಮಾರುಕಟ್ಟೆ' : 'Market'}</Text>
              </View>
              <View style={[styles.featurePill, { borderColor: '#EEEDFE' }]}>
                <Text style={styles.featurePillText}>🏛️ {language === 'kn' ? 'ಯೋಜನೆಗಳು' : 'Schemes'}</Text>
              </View>
            </View>
          )}
        </View>

        {/* Bottom Navigation & Indicator Dots */}
        <View style={styles.bottomSection}>
          {/* Slide Indicator Dots */}
          <View style={styles.dotsRow}>
            {slides.map((_, idx) => (
              <View
                key={idx}
                style={[
                  styles.dot,
                  idx === currentSlide && styles.dotActive,
                  idx === currentSlide && { backgroundColor: Colors.primary },
                ]}
              />
            ))}
          </View>

          {/* Primary Action Button */}
          <Button
            title={
              currentSlide === slides.length - 1
                ? (language === 'kn' ? 'ಪ್ರಾರಂಭಿಸಿ (Get Started)' : 'Get Started')
                : (language === 'kn' ? 'ಮುಂದುವರಿಸಿ' : 'Continue')
            }
            onPress={handleNext}
            size="large"
            icon={<ChevronRight size={20} color={Colors.textWhite} />}
          />
        </View>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  container: {
    flex: 1,
    paddingHorizontal: Spacing.xl,
    paddingTop: Spacing.md,
    paddingBottom: Spacing.md,
    justifyContent: 'space-between',
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: Spacing.xs,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  badgePill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: Colors.surface,
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  badgeText: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  skipButton: {
    paddingVertical: 6,
    paddingHorizontal: Spacing.sm,
  },
  skipText: {
    ...Typography.bodyLarge,
    color: Colors.textSecondary,
    fontWeight: '700',
  },
  centerSection: {
    alignItems: 'center',
    paddingHorizontal: Spacing.xs,
  },
  imageCircleWrapper: {
    width: 170,
    height: 170,
    borderRadius: 85,
    overflow: 'hidden',
    borderWidth: 4,
    backgroundColor: Colors.surface,
    marginBottom: Spacing.xl,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.16,
    shadowRadius: 12,
    elevation: 6,
  },
  heroImage: {
    width: '100%',
    height: '100%',
  },
  titleText: {
    ...Typography.display,
    fontSize: 26,
    lineHeight: 34,
    color: Colors.textPrimary,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: Spacing.sm,
  },
  descText: {
    ...Typography.bodyLarge,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 23,
    paddingHorizontal: Spacing.xs,
  },
  featurePillsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.xs,
    justifyContent: 'center',
    marginTop: Spacing.md,
  },
  featurePill: {
    backgroundColor: Colors.surface,
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    borderWidth: 1.5,
  },
  featurePillText: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  bottomSection: {
    gap: Spacing.lg,
    paddingBottom: Spacing.xs,
  },
  dotsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.borderDark,
  },
  dotActive: {
    width: 24,
    height: 8,
    borderRadius: 4,
  },
});
