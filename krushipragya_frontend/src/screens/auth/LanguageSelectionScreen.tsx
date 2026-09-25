import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { Button } from '../../components/common/Button';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { Globe2, CheckCircle2, Circle } from 'lucide-react-native';

interface LanguageSelectionScreenProps {
  onContinue: () => void;
}

export const LanguageSelectionScreen: React.FC<LanguageSelectionScreenProps> = ({
  onContinue,
}) => {
  const { language, setLanguage } = useLanguage();
  const [selectedLang, setSelectedLang] = useState<'kn' | 'en'>(language);

  const handleSelect = (lang: 'kn' | 'en') => {
    setSelectedLang(lang);
    setLanguage(lang);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        {/* Top Header Section */}
        <View style={styles.topSection}>
          <View style={styles.iconCircle}>
            <Globe2 size={40} color={Colors.primary} />
          </View>
          <Text style={styles.mainTitleKn}>ನಿಮ್ಮ ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ</Text>
          <Text style={styles.subTitleEn}>Choose your preferred language</Text>
        </View>

        {/* Big Language Choice Cards (Rural friendly 56dp+ targets) */}
        <View style={styles.optionsContainer}>
          {/* Kannada Option (Default & Recommended) */}
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={() => handleSelect('kn')}
            style={[
              styles.langCard,
              selectedLang === 'kn' && styles.langCardSelected,
            ]}
          >
            <View style={styles.langLeftCol}>
              <Text style={[styles.langPrimaryKn, selectedLang === 'kn' && styles.textSelected]}>
                ಕನ್ನಡ
              </Text>
              <Text style={styles.langSubKn}>
                ರೈತರಿಗೆ ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ (Recommended)
              </Text>
            </View>

            {selectedLang === 'kn' ? (
              <CheckCircle2 size={26} color={Colors.primary} />
            ) : (
              <Circle size={26} color={Colors.borderDark} />
            )}
          </TouchableOpacity>

          {/* English Option */}
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={() => handleSelect('en')}
            style={[
              styles.langCard,
              selectedLang === 'en' && styles.langCardSelected,
            ]}
          >
            <View style={styles.langLeftCol}>
              <Text style={[styles.langPrimaryEn, selectedLang === 'en' && styles.textSelected]}>
                English
              </Text>
              <Text style={styles.langSubEn}>
                Standard interface
              </Text>
            </View>

            {selectedLang === 'en' ? (
              <CheckCircle2 size={26} color={Colors.primary} />
            ) : (
              <Circle size={26} color={Colors.borderDark} />
            )}
          </TouchableOpacity>
        </View>

        {/* Bottom CTA Button */}
        <View style={styles.bottomSection}>
          <Button
            title={selectedLang === 'kn' ? 'ಮುಂದುವರಿಸಿ' : 'Continue'}
            onPress={onContinue}
            size="large"
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
    paddingVertical: Spacing.xxl,
    justifyContent: 'space-between',
  },
  topSection: {
    alignItems: 'center',
    marginTop: Spacing.xl,
  },
  iconCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.lg,
    borderWidth: 1.5,
    borderColor: '#BFE7D7',
  },
  mainTitleKn: {
    ...Typography.display,
    fontSize: 26,
    color: Colors.textPrimary,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 6,
  },
  subTitleEn: {
    ...Typography.bodyLarge,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  optionsContainer: {
    gap: Spacing.lg,
    marginVertical: Spacing.xl,
  },
  langCard: {
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.xl,
    padding: Spacing.lg + 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 2,
    borderColor: Colors.border,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
  },
  langCardSelected: {
    borderColor: Colors.primary,
    backgroundColor: Colors.primaryLight,
  },
  langLeftCol: {
    flex: 1,
    gap: 4,
  },
  langPrimaryKn: {
    fontSize: 24,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  langPrimaryEn: {
    fontSize: 22,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  textSelected: {
    color: Colors.primaryDark,
  },
  langSubKn: {
    ...Typography.caption,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  langSubEn: {
    ...Typography.caption,
    color: Colors.textSecondary,
  },
  bottomSection: {
    paddingBottom: Spacing.lg,
  },
});
