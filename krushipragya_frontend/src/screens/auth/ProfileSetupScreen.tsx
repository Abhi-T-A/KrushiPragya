import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Location from 'expo-location';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/common/Button';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import {
  ArrowLeft,
  User,
  MapPin,
  Trees,
  Sprout,
  CheckCircle2,
  Circle,
  Search,
  ChevronRight,
  Navigation,
} from 'lucide-react-native';

const VILLAGES_LIST = [
  { id: 'v1', nameKn: 'ತೀರ್ಥಹಳ್ಳಿ (Thirthahalli)', nameEn: 'Thirthahalli', district: 'Shivamogga' },
  { id: 'v2', nameKn: 'ಉಜಿರೆ (Ujire)', nameEn: 'Ujire', district: 'Dakshina Kannada' },
  { id: 'v3', nameKn: 'ಬೆಳ್ತಂಗಡಿ (Belthangady)', nameEn: 'Belthangady', district: 'Dakshina Kannada' },
  { id: 'v4', nameKn: 'ಪುತ್ತೂರು (Puttur)', nameEn: 'Puttur', district: 'Dakshina Kannada' },
  { id: 'v5', nameKn: 'ಸುಳ್ಯ (Sullia)', nameEn: 'Sullia', district: 'Dakshina Kannada' },
  { id: 'v6', nameKn: 'ಶಿರಸಿ (Sirsi)', nameEn: 'Sirsi', district: 'Uttara Kannada' },
  { id: 'v7', nameKn: 'ಮಂಗಳೂರು (Mangalore)', nameEn: 'Mangalore', district: 'Dakshina Kannada' },
];

const CROPS_LIST = [
  { id: 'arecanut', emoji: '🌴', nameKn: 'ಅಡಿಕೆ', nameEn: 'Arecanut' },
  { id: 'paddy', emoji: '🌾', nameKn: 'ಭತ್ತ', nameEn: 'Paddy' },
  { id: 'coconut', emoji: '🥥', nameKn: 'ತೆಂಗು', nameEn: 'Coconut' },
  { id: 'pepper', emoji: '🌶', nameKn: 'ಕಾಳುಮೆಣಸು', nameEn: 'Black Pepper' },
  { id: 'cardamom', emoji: '🌿', nameKn: 'ಏಲಕ್ಕಿ', nameEn: 'Cardamom' },
  { id: 'turmeric', emoji: '🟡', nameKn: 'ಅರಿಶಿನ', nameEn: 'Turmeric' },
  { id: 'ginger', emoji: '🫚', nameKn: 'ಶುಂಠಿ', nameEn: 'Ginger' },
];

interface ProfileSetupScreenProps {
  onComplete: () => void;
  onBack: () => void;
}

export const ProfileSetupScreen: React.FC<ProfileSetupScreenProps> = ({
  onComplete,
  onBack,
}) => {
  const { language } = useLanguage();
  const { login } = useAuth();

  // Wizard Steps: 1 = Name, 2 = Village, 3 = Land Acres, 4 = Crops
  const [step, setStep] = useState<number>(1);

  // Form states
  const [name, setName] = useState('ಅಭಿ ಗೌಡ');
  const [villageSearch, setVillageSearch] = useState('');
  const [selectedVillage, setSelectedVillage] = useState(VILLAGES_LIST[1]); // Ujire default
  const [landAcres, setLandAcres] = useState('2.5');
  const [selectedCrops, setSelectedCrops] = useState<string[]>(['arecanut', 'paddy']);
  const [isDetectingLocation, setIsDetectingLocation] = useState(false);

  const filteredVillages = VILLAGES_LIST.filter(
    (v) =>
      v.nameKn.toLowerCase().includes(villageSearch.toLowerCase()) ||
      v.nameEn.toLowerCase().includes(villageSearch.toLowerCase()) ||
      v.district.toLowerCase().includes(villageSearch.toLowerCase())
  );

  const toggleCrop = (cropId: string) => {
    if (selectedCrops.includes(cropId)) {
      if (selectedCrops.length > 1) {
        setSelectedCrops(selectedCrops.filter((c) => c !== cropId));
      }
    } else {
      setSelectedCrops([...selectedCrops, cropId]);
    }
  };

  // 1-Tap Current GPS Location Detection
  const handleUseCurrentLocation = async () => {
    setIsDetectingLocation(true);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        alert(
          language === 'kn'
            ? 'ಸ್ಥಳದ ಅನುಮತಿ ಅಗತ್ಯವಿದೆ'
            : 'Location permission is required to detect your village.'
        );
        setIsDetectingLocation(false);
        return;
      }

      await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      // Simulate/Match closest Malnad village (Ujire)
      setSelectedVillage(VILLAGES_LIST[1]);
      setVillageSearch('');
    } catch {
      // Fallback
      setSelectedVillage(VILLAGES_LIST[1]);
    } finally {
      setIsDetectingLocation(false);
    }
  };

  const handleNext = () => {
    if (step < 4) {
      setStep(step + 1);
    } else {
      // Finish profile setup and save to context
      login(
        '+91 98765 43210',
        'farmer',
        selectedVillage.id,
        name.trim() || 'ಅಭಿ ಗೌಡ'
      );
      onComplete();
    }
  };

  const handleStepBack = () => {
    if (step > 1) {
      setStep(step - 1);
    } else {
      onBack();
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.container}
      >
        {/* Top Header Bar */}
        <View style={styles.topBar}>
          <TouchableOpacity activeOpacity={0.7} onPress={handleStepBack} style={styles.backButton}>
            <ArrowLeft size={22} color={Colors.textPrimary} />
          </TouchableOpacity>

          <View style={styles.stepBadge}>
            <Text style={styles.stepBadgeText}>
              {language === 'kn' ? `ಹಂತ ${step} / 4` : `Step ${step} of 4`}
            </Text>
          </View>

          <View style={{ width: 40 }} />
        </View>

        {/* Dynamic Step Content */}
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* ==================== STEP 1: NAME ==================== */}
          {step === 1 && (
            <View style={styles.stepContainer}>
              <View style={styles.iconCircle}>
                <User size={40} color={Colors.primary} />
              </View>

              <Text style={styles.title}>
                {language === 'kn' ? 'ನಿಮ್ಮ ಹೆಸರು ನಮೂದಿಸಿ' : 'What is your Name?'}
              </Text>
              <Text style={styles.subtitle}>
                {language === 'kn'
                  ? 'ನಿಮ್ಮ ಕೃಷಿ ಖಾತೆಗೆ ಹೆಸರು ಸೇರಿಸಿ'
                  : 'Enter your name to personalize your farm dashboard'}
              </Text>

              <View style={styles.inputCard}>
                <Text style={styles.inputLabel}>
                  {language === 'kn' ? 'ಪೂರ್ಣ ಹೆಸರು (Full Name)' : 'Full Name'}
                </Text>
                <TextInput
                  style={styles.textInput}
                  value={name}
                  onChangeText={setName}
                  placeholder={language === 'kn' ? 'ಉದಾ: ಅಭಿ ಗೌಡ' : 'e.g. Abhi Gowda'}
                  placeholderTextColor={Colors.textMuted}
                />
              </View>
            </View>
          )}

          {/* ==================== STEP 2: VILLAGE WITH CURRENT LOCATION ==================== */}
          {step === 2 && (
            <View style={styles.stepContainer}>
              <View style={[styles.iconCircle, { backgroundColor: '#FEF3C7', borderColor: '#FED7AA' }]}>
                <MapPin size={40} color={Colors.accentGold} />
              </View>

              <Text style={styles.title}>
                {language === 'kn' ? 'ನಿಮ್ಮ ಗ್ರಾಮ ಆಯ್ಕೆಮಾಡಿ' : 'Select Your Village'}
              </Text>
              <Text style={styles.subtitle}>
                {language === 'kn'
                  ? 'ಸ್ಥಳೀಯ ಹವಾಮಾನ ಮತ್ತು ಮಾರುಕಟ್ಟೆ ಮಾಹಿತಿಗಾಗಿ'
                  : 'For hyper-local weather alerts and market price insights'}
              </Text>

              {/* 1-Tap Use Current GPS Location Button */}
              <TouchableOpacity
                activeOpacity={0.85}
                onPress={handleUseCurrentLocation}
                disabled={isDetectingLocation}
                style={styles.currentLocationBtn}
              >
                {isDetectingLocation ? (
                  <ActivityIndicator size="small" color={Colors.primary} />
                ) : (
                  <Navigation size={18} color={Colors.primary} />
                )}
                <Text style={styles.currentLocationText}>
                  {language === 'kn'
                    ? '📍 ಪ್ರಸ್ತುತ ಸ್ಥಳವನ್ನು ಬಳಸಿ (Use Current Location)'
                    : '📍 Use Current Location'}
                </Text>
              </TouchableOpacity>

              {/* Village Search Bar */}
              <View style={styles.searchBox}>
                <Search size={18} color={Colors.textMuted} />
                <TextInput
                  style={styles.searchInput}
                  placeholder={language === 'kn' ? '🔍 ಗ್ರಾಮ ಅಥವಾ ತಾಲೂಕು ಹುಡುಕಿ...' : 'Search village or district...'}
                  placeholderTextColor={Colors.textMuted}
                  value={villageSearch}
                  onChangeText={setVillageSearch}
                />
              </View>

              {/* Village List */}
              <View style={styles.listContainer}>
                {filteredVillages.map((v) => {
                  const isSelected = selectedVillage.id === v.id;
                  return (
                    <TouchableOpacity
                      key={v.id}
                      activeOpacity={0.8}
                      onPress={() => setSelectedVillage(v)}
                      style={[
                        styles.villageItem,
                        isSelected && styles.villageItemSelected,
                      ]}
                    >
                      <View style={styles.villageTextCol}>
                        <Text style={[styles.villageName, isSelected && styles.villageNameSelected]}>
                          {language === 'kn' ? v.nameKn : v.nameEn}
                        </Text>
                        <Text style={styles.districtName}>{v.district} District</Text>
                      </View>

                      {isSelected ? (
                        <CheckCircle2 size={24} color={Colors.primary} />
                      ) : (
                        <Circle size={24} color={Colors.borderDark} />
                      )}
                    </TouchableOpacity>
                  );
                })}
              </View>
            </View>
          )}

          {/* ==================== STEP 3: LAND ACRES ==================== */}
          {step === 3 && (
            <View style={styles.stepContainer}>
              <View style={[styles.iconCircle, { backgroundColor: Colors.trustPurpleLight, borderColor: '#D8D5FB' }]}>
                <Trees size={40} color={Colors.trustPurple} />
              </View>

              <Text style={styles.title}>
                {language === 'kn' ? 'ನಿಮ್ಮ ಕೃಷಿ ಜಮೀನು' : 'Farm Land Size'}
              </Text>
              <Text style={styles.subtitle}>
                {language === 'kn'
                  ? 'ನಿಮ್ಮ ತೋಟ ಅಥವಾ ಗದ್ದೆಯ ಒಟ್ಟು ವಿಸ್ತೀರ್ಣ'
                  : 'Total cultivated agricultural land in acres'}
              </Text>

              <View style={styles.landCard}>
                <Text style={styles.landLabel}>
                  {language === 'kn' ? 'ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ (Acres)' : 'Total Land (Acres)'}
                </Text>
                <View style={styles.landInputRow}>
                  <TextInput
                    style={styles.landInput}
                    value={landAcres}
                    onChangeText={setLandAcres}
                    keyboardType="decimal-pad"
                    maxLength={5}
                  />
                  <View style={styles.acreUnitBox}>
                    <Text style={styles.acreUnitText}>
                      {language === 'kn' ? 'ಎಕರೆ (Acres)' : 'Acres'}
                    </Text>
                  </View>
                </View>
              </View>
            </View>
          )}

          {/* ==================== STEP 4: CROP SELECTION ==================== */}
          {step === 4 && (
            <View style={styles.stepContainer}>
              <View style={styles.iconCircle}>
                <Sprout size={40} color={Colors.primary} />
              </View>

              <Text style={styles.title}>
                {language === 'kn' ? 'ನೀವು ಯಾವ ಬೆಳೆಗಳನ್ನು ಬೆಳೆಯುತ್ತೀರಿ?' : 'Which Crops Do You Grow?'}
              </Text>
              <Text style={styles.subtitle}>
                {language === 'kn'
                  ? 'ನಿಮ್ಮ ಮುಖ್ಯ ಬೆಳೆಗಳನ್ನು ಆಯ್ಕೆಮಾಡಿ (Multi-select)'
                  : 'Select the crops grown on your farm'}
              </Text>

              <View style={styles.cropsGrid}>
                {CROPS_LIST.map((crop) => {
                  const isSelected = selectedCrops.includes(crop.id);
                  return (
                    <TouchableOpacity
                      key={crop.id}
                      activeOpacity={0.85}
                      onPress={() => toggleCrop(crop.id)}
                      style={[
                        styles.cropCardItem,
                        isSelected && styles.cropCardItemSelected,
                      ]}
                    >
                      <Text style={styles.cropEmoji}>{crop.emoji}</Text>
                      <View style={styles.cropTextCol}>
                        <Text style={[styles.cropName, isSelected && styles.cropNameSelected]}>
                          {language === 'kn' ? crop.nameKn : crop.nameEn}
                        </Text>
                        <Text style={styles.cropSubName}>
                          {language === 'kn' ? crop.nameEn : crop.nameKn}
                        </Text>
                      </View>

                      {isSelected ? (
                        <CheckCircle2 size={22} color={Colors.primary} />
                      ) : (
                        <Circle size={22} color={Colors.borderDark} />
                      )}
                    </TouchableOpacity>
                  );
                })}
              </View>
            </View>
          )}
        </ScrollView>

        {/* Bottom CTA Button */}
        <View style={styles.bottomSection}>
          <Button
            title={
              step === 4
                ? (language === 'kn' ? 'ಪ್ರಾರಂಭಿಸಿ (Done)' : 'Finish Setup')
                : (language === 'kn' ? 'ಮುಂದುವರಿಸಿ (Next)' : 'Continue')
            }
            onPress={handleNext}
            size="large"
            icon={<ChevronRight size={20} color={Colors.textWhite} />}
          />
        </View>
      </KeyboardAvoidingView>
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
    justifyContent: 'space-between',
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.xl,
    paddingVertical: Spacing.sm,
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
  stepBadge: {
    backgroundColor: Colors.surface,
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  stepBadgeText: {
    ...Typography.caption,
    fontWeight: '800',
    color: Colors.primaryDark,
  },
  scrollContent: {
    paddingHorizontal: Spacing.xl,
    paddingTop: Spacing.xs,
    paddingBottom: Spacing.xl,
  },
  stepContainer: {
    alignItems: 'center',
  },
  iconCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.md,
    borderWidth: 1.5,
    borderColor: '#BFE7D7',
  },
  title: {
    ...Typography.display,
    fontSize: 24,
    color: Colors.textPrimary,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 4,
  },
  subtitle: {
    ...Typography.bodyLarge,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: Spacing.lg,
    paddingHorizontal: Spacing.sm,
  },
  currentLocationBtn: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.xs,
    backgroundColor: Colors.primaryLight,
    borderWidth: 1.5,
    borderColor: Colors.primary,
    borderRadius: BorderRadius.lg,
    paddingVertical: Spacing.md,
    marginBottom: Spacing.md,
  },
  currentLocationText: {
    ...Typography.bodyLarge,
    fontWeight: '800',
    color: Colors.primaryDark,
  },
  inputCard: {
    width: '100%',
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.xl,
    padding: Spacing.lg,
    borderWidth: 1.5,
    borderColor: Colors.border,
    gap: Spacing.xs,
  },
  inputLabel: {
    ...Typography.bodyLarge,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  textInput: {
    height: 52,
    backgroundColor: Colors.surfaceSubtle,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: BorderRadius.lg,
    paddingHorizontal: Spacing.md,
    ...Typography.title2,
    color: Colors.textPrimary,
    fontWeight: '700',
  },
  searchBox: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: BorderRadius.lg,
    paddingHorizontal: Spacing.md,
    height: 50,
    marginBottom: Spacing.md,
  },
  searchInput: {
    flex: 1,
    ...Typography.bodyLarge,
    color: Colors.textPrimary,
  },
  listContainer: {
    width: '100%',
    gap: Spacing.xs,
  },
  villageItem: {
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1.5,
    borderColor: Colors.border,
  },
  villageItemSelected: {
    borderColor: Colors.primary,
    backgroundColor: Colors.primaryLight,
  },
  villageTextCol: {
    flex: 1,
  },
  villageName: {
    ...Typography.bodyLarge,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  villageNameSelected: {
    color: Colors.primaryDark,
  },
  districtName: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  landCard: {
    width: '100%',
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.xl,
    padding: Spacing.lg,
    borderWidth: 1.5,
    borderColor: Colors.border,
    gap: Spacing.sm,
  },
  landLabel: {
    ...Typography.bodyLarge,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  landInputRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
  },
  landInput: {
    flex: 1,
    height: 56,
    backgroundColor: Colors.surfaceSubtle,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: BorderRadius.lg,
    paddingHorizontal: Spacing.md,
    fontSize: 24,
    fontWeight: '900',
    color: Colors.textPrimary,
    textAlign: 'center',
  },
  acreUnitBox: {
    backgroundColor: Colors.primaryLight,
    paddingHorizontal: Spacing.lg,
    borderRadius: BorderRadius.lg,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: '#BFE7D7',
  },
  acreUnitText: {
    ...Typography.bodyLarge,
    fontWeight: '800',
    color: Colors.primaryDark,
  },
  cropsGrid: {
    width: '100%',
    gap: Spacing.xs,
  },
  cropCardItem: {
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
    borderWidth: 1.5,
    borderColor: Colors.border,
  },
  cropCardItemSelected: {
    borderColor: Colors.primary,
    backgroundColor: Colors.primaryLight,
  },
  cropEmoji: {
    fontSize: 28,
  },
  cropTextCol: {
    flex: 1,
  },
  cropName: {
    ...Typography.bodyLarge,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  cropNameSelected: {
    color: Colors.primaryDark,
  },
  cropSubName: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 1,
  },
  bottomSection: {
    paddingHorizontal: Spacing.xl,
    paddingBottom: Spacing.lg,
    paddingTop: Spacing.xs,
  },
});
