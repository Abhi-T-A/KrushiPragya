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
import { useAuth, UserRole } from '../../context/AuthContext';
import { Button } from '../../components/common/Button';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { saveUserProfileSetup } from '../../services/api';
import {
  ArrowLeft,
  MapPin,
  Navigation,
  CheckCircle2,
  Sparkles,
  Building2,
  Compass,
  AlertCircle,
  Sprout,
  Check,
  Globe2,
} from 'lucide-react-native';

interface LocationSetupScreenProps {
  onComplete: (role: UserRole) => void;
  onBack: () => void;
}

const POPULAR_VILLAGES = [
  { en: 'Ujire', kn: 'ಉಜಿರೆ', districtEn: 'Dakshina Kannada', districtKn: 'ದಕ್ಷಿಣ ಕನ್ನಡ' },
  { en: 'Brahmavar', kn: 'ಬ್ರಹ್ಮಾವರ', districtEn: 'Udupi', districtKn: 'ಉಡುಪಿ' },
  { en: 'Thirthahalli', kn: 'ತೀರ್ಥಹಳ್ಳಿ', districtEn: 'Shivamogga', districtKn: 'ಶಿವಮೊಗ್ಗ' },
  { en: 'Sirsi', kn: 'ಶಿರಸಿ', districtEn: 'Uttara Kannada', districtKn: 'ಉತ್ತರ ಕನ್ನಡ' },
  { en: 'Belthangady', kn: 'ಬೆಳ್ತಂಗಡಿ', districtEn: 'Dakshina Kannada', districtKn: 'ದಕ್ಷಿಣ ಕನ್ನಡ' },
  { en: 'Puttur', kn: 'ಪುತ್ತೂರು', districtEn: 'Dakshina Kannada', districtKn: 'ದಕ್ಷಿಣ ಕನ್ನಡ' },
  { en: 'Channagiri', kn: 'ಚನ್ನಗಿರಿ', districtEn: 'Davanagere', districtKn: 'ದಾವಣಗೆರೆ' },
  { en: 'Mudigere', kn: 'ಮೂಡಿಗೆರೆ', districtEn: 'Chikkamagaluru', districtKn: 'ಚಿಕ್ಕಮಗಳೂರು' },
];

const POPULAR_DISTRICTS = [
  { en: 'Dakshina Kannada', kn: 'ದಕ್ಷಿಣ ಕನ್ನಡ' },
  { en: 'Udupi', kn: 'ಉಡುಪಿ' },
  { en: 'Shivamogga', kn: 'ಶಿವಮೊಗ್ಗ' },
  { en: 'Uttara Kannada', kn: 'ಉತ್ತರ ಕನ್ನಡ' },
  { en: 'Chikkamagaluru', kn: 'ಚಿಕ್ಕಮಗಳೂರು' },
  { en: 'Hassan', kn: 'ಹಾಸನ' },
  { en: 'Davanagere', kn: 'ದಾವಣಗೆರೆ' },
  { en: 'Mandya', kn: 'ಮಂಡ್ಯ' },
];

export const LocationSetupScreen: React.FC<LocationSetupScreenProps> = ({
  onComplete,
  onBack,
}) => {
  const { language } = useLanguage();
  const { user, saveCompleteProfile } = useAuth();
  const isKn = language === 'kn';

  const [villageName, setVillageName] = useState(user?.villageName || 'Ujire');
  const [district, setDistrict] = useState(user?.district || 'Dakshina Kannada');
  const [stateName, setStateName] = useState(user?.state || 'Karnataka');

  const [isLocating, setIsLocating] = useState(false);
  const [locationSuccess, setLocationSuccess] = useState(false);
  const [locationNotice, setLocationNotice] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Request location ONLY when button is clicked
  const handleUseCurrentLocation = async () => {
    setErrorMessage('');
    setLocationNotice('');
    setIsLocating(true);

    try {
      // 1. Request permission dynamically
      const { status } = await Location.requestForegroundPermissionsAsync();

      if (status !== 'granted') {
        setLocationNotice(
          isKn
            ? 'ಸ್ಥಳ ಅನುಮತಿ ನಿರಾಕರಿಸಲಾಗಿದೆ. ದಯವಿಟ್ಟು ಹಳ್ಳಿಯನ್ನು ಕೆಳಗೆ ಹಸ್ತಚಾಲಿತವಾಗಿ ಆಯ್ಕೆಮಾಡಿ.'
            : 'Location permission denied. Please select your village manually below.'
        );
        setIsLocating(false);
        return;
      }

      // 2. Fetch current coordinate
      const position = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });

      if (position && position.coords) {
        // 3. Reverse geocode to find locality & district
        const geocodeResults = await Location.reverseGeocodeAsync({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });

        if (geocodeResults && geocodeResults.length > 0) {
          const item = geocodeResults[0];
          const detectedVillage =
            item.district ||
            item.subregion ||
            item.city ||
            item.name ||
            'Ujire';

          const detectedDistrict =
            item.subregion ||
            item.district ||
            item.city ||
            'Dakshina Kannada';

          const detectedState = item.region || 'Karnataka';

          setVillageName(detectedVillage);
          setDistrict(detectedDistrict);
          setStateName(detectedState);
          setLocationSuccess(true);
          setLocationNotice(
            isKn
              ? `✓ ಸ್ಥಳ ಪತ್ತೆಯಾಗಿದೆ: ${detectedVillage}, ${detectedDistrict}`
              : `✓ Detected location: ${detectedVillage}, ${detectedDistrict}`
          );
        } else {
          setLocationNotice(
            isKn
              ? 'ನಿಖರ ವಿಳಾಸ ಲಭ್ಯವಿಲ್ಲ. ದಯವಿಟ್ಟು ಹಳ್ಳಿಯನ್ನು ಕೆಳಗೆ ನಮೂದಿಸಿ.'
              : 'Detailed address not found. Please type village name manually.'
          );
        }
      }
    } catch (err: any) {
      console.log('[LocationSetup] GPS error:', err?.message || err);
      setLocationNotice(
        isKn
          ? 'ಸ್ಥಳ ಪತ್ತೆಹಚ್ಚಲು ವಿಫಲವಾಗಿದೆ. ದಯವಿಟ್ಟು ಕೆಳಗೆ ಹಸ್ತಚಾಲಿತವಾಗಿ ಆಯ್ಕೆಮಾಡಿ.'
          : 'Could not fetch GPS location. Please select manually below.'
      );
    } finally {
      setIsLocating(false);
    }
  };

  const handleSelectPresetVillage = (v: typeof POPULAR_VILLAGES[0]) => {
    setVillageName(isKn ? v.kn : v.en);
    setDistrict(isKn ? v.districtKn : v.districtEn);
    setErrorMessage('');
    setLocationNotice('');
  };

  const handleSelectPresetDistrict = (d: typeof POPULAR_DISTRICTS[0]) => {
    setDistrict(isKn ? d.kn : d.en);
    setErrorMessage('');
  };

  const handleFinishSetup = async () => {
    setErrorMessage('');
    const cleanVillage = villageName.trim();
    const cleanDistrict = district.trim();
    const cleanState = stateName.trim();

    if (!cleanVillage) {
      setErrorMessage(
        isKn
          ? 'ದಯವಿಟ್ಟು ನಿಮ್ಮ ಗ್ರಾಮ/ಪಟ್ಟಣದ ಹೆಸರನ್ನು ನಮೂದಿಸಿ.'
          : 'Please enter your village or town name.'
      );
      return;
    }

    if (!cleanDistrict) {
      setErrorMessage(
        isKn
          ? 'ದಯವಿಟ್ಟು ನಿಮ್ಮ ಜಿಲ್ಲೆಯನ್ನು ನಮೂದಿಸಿ.'
          : 'Please enter your district.'
      );
      return;
    }

    setIsSubmitting(true);
    const activeRole = user?.role || 'farmer';
    const activePhone = user?.phone || '9876543210';
    const activeName = user?.name || 'Farmer';

    try {
      // 1. Persist to existing backend user profile and RBAC
      await saveUserProfileSetup({
        fullName: activeName,
        phone: activePhone,
        role: activeRole,
        villageName: cleanVillage,
        district: cleanDistrict,
        state: cleanState,
        language: language,
        userId: user?.id,
      });

      // 2. Persist to local AuthContext & AsyncStorage
      await saveCompleteProfile({
        name: activeName,
        phone: activePhone,
        role: activeRole,
        villageName: cleanVillage,
        district: cleanDistrict,
        state: cleanState,
      });

      // 3. Transition directly to role dashboard
      onComplete(activeRole);
    } catch (err: any) {
      console.log('[LocationSetup] save error:', err);
      // Still persist locally to avoid blocking farmer
      await saveCompleteProfile({
        name: activeName,
        phone: activePhone,
        role: activeRole,
        villageName: cleanVillage,
        district: cleanDistrict,
        state: cleanState,
      });
      onComplete(activeRole);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.container}
      >
        {/* Top Header */}
        <View style={styles.topBar}>
          <TouchableOpacity activeOpacity={0.7} onPress={onBack} style={styles.backButton}>
            <ArrowLeft size={20} color={Colors.textPrimary} />
          </TouchableOpacity>

          <View style={styles.headerStepPill}>
            <Sparkles size={13} color={Colors.primary} />
            <Text style={styles.headerStepText}>
              {isKn ? 'ಹಂತ 3: ಸ್ಥಳ' : 'Step 3: Location'}
            </Text>
          </View>

          <View style={{ width: 36 }} />
        </View>

        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Title Section */}
          <View style={styles.titleSection}>
            <Text style={styles.screenTitle}>
              {isKn ? 'ನಿಮ್ಮ ಸ್ಥಳವನ್ನು ಆಯ್ಕೆಮಾಡಿ' : 'Select Your Location'}
            </Text>
            <Text style={styles.screenSubtitle}>
              {isKn
                ? 'ನಿಖರ ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ, ಸ್ಥಳೀಯ ಎಪಿಎಂಸಿ ದರಗಳು ಮತ್ತು ಕೃಷಿ ಸಲಹೆಗಳಿಗಾಗಿ ನಿಮ್ಮ ಗ್ರಾಮ/ನಗರವನ್ನು ಆಯ್ಕೆಮಾಡಿ.'
                : 'Select your village/city for accurate weather alerts, mandi rates, and local agricultural advisory.'}
            </Text>
          </View>

          {/* GPS Auto-Detect Button Card */}
          <View style={styles.gpsCard}>
            <View style={styles.gpsCardHeader}>
              <View style={styles.gpsIconCircle}>
                <Navigation size={20} color={Colors.primary} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.gpsCardTitle}>
                  {isKn ? 'ಪ್ರಸ್ತುತ ಸ್ಥಳ ಬಳಸಿ' : 'Use Current Location'}
                </Text>
                <Text style={styles.gpsCardSub}>
                  {isKn
                    ? 'ಜಿಪಿಎಸ್ ಮೂಲಕ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಗ್ರಾಮ ಪತ್ತೆಮಾಡಿ'
                    : 'Auto-detect village & district via GPS'}
                </Text>
              </View>
            </View>

            <TouchableOpacity
              activeOpacity={0.85}
              style={[styles.gpsActionBtn, isLocating && styles.gpsActionBtnDisabled]}
              onPress={handleUseCurrentLocation}
              disabled={isLocating}
            >
              {isLocating ? (
                <View style={styles.loadingRow}>
                  <ActivityIndicator size="small" color="#FFFFFF" />
                  <Text style={styles.gpsBtnText}>
                    {isKn ? 'ಸ್ಥಳ ಪತ್ತೆಹಚ್ಚಲಾಗುತ್ತಿದೆ...' : 'Detecting GPS Location...'}
                  </Text>
                </View>
              ) : (
                <View style={styles.loadingRow}>
                  <Compass size={18} color="#FFFFFF" />
                  <Text style={styles.gpsBtnText}>
                    {locationSuccess
                      ? (isKn ? 'ಸ್ಥಳ ನವೀಕರಿಸಿ (Re-detect)' : 'Re-detect Location')
                      : (isKn ? 'ಜಿಪಿಎಸ್ ಸ್ಥಳ ಪತ್ತೆಮಾಡಿ (Auto-Detect)' : 'Detect Current Location')}
                  </Text>
                </View>
              )}
            </TouchableOpacity>

            {/* GPS Feedback Notice */}
            {locationNotice ? (
              <View
                style={[
                  styles.noticeBox,
                  locationSuccess ? styles.noticeBoxSuccess : styles.noticeBoxWarn,
                ]}
              >
                {locationSuccess ? (
                  <CheckCircle2 size={15} color="#15803D" />
                ) : (
                  <AlertCircle size={15} color="#B45309" />
                )}
                <Text
                  style={[
                    styles.noticeText,
                    locationSuccess ? styles.noticeTextSuccess : styles.noticeTextWarn,
                  ]}
                >
                  {locationNotice}
                </Text>
              </View>
            ) : null}
          </View>

          {/* Divider */}
          <View style={styles.dividerRow}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>
              {isKn ? 'ಅಥವಾ ಹಸ್ತಚಾಲಿತವಾಗಿ ಆಯ್ಕೆಮಾಡಿ' : 'OR SELECT MANUALLY'}
            </Text>
            <View style={styles.dividerLine} />
          </View>

          {/* Error Message */}
          {errorMessage ? (
            <View style={styles.errorBox}>
              <AlertCircle size={16} color="#DC2626" />
              <Text style={styles.errorText}>{errorMessage}</Text>
            </View>
          ) : null}

          {/* Manual Selection Form Card */}
          <View style={styles.formCard}>
            {/* 1. Village / Town */}
            <View style={styles.inputGroup}>
              <View style={styles.labelRow}>
                <Building2 size={15} color={Colors.primary} />
                <Text style={styles.inputLabel}>
                  {isKn ? 'ಗ್ರಾಮ / ಪಟ್ಟಣ (Village / Town)' : 'Village / Town'}
                </Text>
              </View>

              <View style={styles.inputBox}>
                <MapPin size={17} color={Colors.primary} />
                <TextInput
                  style={styles.textInput}
                  placeholder={isKn ? 'ಗ್ರಾಮ/ಪಟ್ಟಣದ ಹೆಸರು ನಮೂದಿಸಿ' : 'Enter village or town name'}
                  placeholderTextColor={Colors.textMuted}
                  value={villageName}
                  onChangeText={(t) => {
                    setVillageName(t);
                    if (errorMessage) setErrorMessage('');
                  }}
                />
                {villageName.trim().length > 0 && (
                  <Check size={16} color="#16A34A" />
                )}
              </View>

              {/* Popular Village Quick Chips */}
              <View style={styles.chipsSection}>
                <Text style={styles.chipsLabel}>
                  {isKn ? 'ಜನಪ್ರಿಯ ಕೃಷಿ ಪ್ರದೇಶಗಳು:' : 'Quick Select:'}
                </Text>
                <View style={styles.chipsWrap}>
                  {POPULAR_VILLAGES.map((v) => {
                    const isSelected =
                      villageName.toLowerCase() === v.en.toLowerCase() ||
                      villageName === v.kn;
                    return (
                      <TouchableOpacity
                        key={v.en}
                        activeOpacity={0.75}
                        onPress={() => handleSelectPresetVillage(v)}
                        style={[
                          styles.chip,
                          isSelected && styles.chipActive,
                        ]}
                      >
                        <Text
                          style={[
                            styles.chipText,
                            isSelected && styles.chipTextActive,
                          ]}
                        >
                          {isKn ? v.kn : v.en}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              </View>
            </View>

            {/* 2. District */}
            <View style={styles.inputGroup}>
              <View style={styles.labelRow}>
                <MapPin size={15} color={Colors.primary} />
                <Text style={styles.inputLabel}>
                  {isKn ? 'ಜಿಲ್ಲೆ (District)' : 'District'}
                </Text>
              </View>

              <View style={styles.inputBox}>
                <TextInput
                  style={styles.textInput}
                  placeholder={isKn ? 'ಜಿಲ್ಲೆಯ ಹೆಸರು ನಮೂದಿಸಿ' : 'Enter district name'}
                  placeholderTextColor={Colors.textMuted}
                  value={district}
                  onChangeText={(t) => {
                    setDistrict(t);
                    if (errorMessage) setErrorMessage('');
                  }}
                />
              </View>

              {/* Popular Districts Quick Chips */}
              <View style={styles.chipsSection}>
                <View style={styles.chipsWrap}>
                  {POPULAR_DISTRICTS.map((d) => {
                    const isSelected =
                      district.toLowerCase() === d.en.toLowerCase() ||
                      district === d.kn;
                    return (
                      <TouchableOpacity
                        key={d.en}
                        activeOpacity={0.75}
                        onPress={() => handleSelectPresetDistrict(d)}
                        style={[
                          styles.chip,
                          isSelected && styles.chipActive,
                        ]}
                      >
                        <Text
                          style={[
                            styles.chipText,
                            isSelected && styles.chipTextActive,
                          ]}
                        >
                          {isKn ? d.kn : d.en}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              </View>
            </View>

            {/* 3. State */}
            <View style={styles.inputGroup}>
              <View style={styles.labelRow}>
                <Globe2 size={15} color={Colors.primary} />
                <Text style={styles.inputLabel}>
                  {isKn ? 'ರಾಜ್ಯ (State)' : 'State'}
                </Text>
              </View>

              <View style={styles.inputBox}>
                <TextInput
                  style={styles.textInput}
                  placeholder="Karnataka"
                  placeholderTextColor={Colors.textMuted}
                  value={stateName}
                  onChangeText={setStateName}
                />
              </View>
            </View>
          </View>
        </ScrollView>

        {/* Bottom Sticky Action Button */}
        <View style={styles.bottomBar}>
          <Button
            title={
              isSubmitting
                ? (isKn ? 'ಉಳಿಸಲಾಗುತ್ತಿದೆ...' : 'Saving Profile...')
                : (isKn ? 'ಪ್ರೊಫೈಲ್ ಪೂರ್ಣಗೊಳಿಸಿ (Finish Setup)' : 'Complete Setup & Enter App')
            }
            onPress={handleFinishSetup}
            disabled={isSubmitting}
            size="large"
            icon={
              isSubmitting ? (
                <ActivityIndicator size="small" color="#FFFFFF" />
              ) : (
                <CheckCircle2 size={20} color={Colors.textWhite} />
              )
            }
            style={styles.finishBtn}
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
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
    backgroundColor: Colors.surface,
  },
  backButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  headerStepPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: '#BBF7D0',
  },
  headerStepText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#166534',
  },
  scrollContent: {
    padding: Spacing.md,
    gap: Spacing.md,
  },
  titleSection: {
    gap: 4,
  },
  screenTitle: {
    ...Typography.display,
    fontSize: 22,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  screenSubtitle: {
    ...Typography.bodyLarge,
    fontSize: 13,
    color: Colors.textSecondary,
    lineHeight: 18,
  },
  gpsCard: {
    backgroundColor: '#F0FDF4',
    borderWidth: 1.5,
    borderColor: '#BBF7D0',
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    gap: 12,
  },
  gpsCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  gpsIconCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#DCFCE7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  gpsCardTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#14532D',
  },
  gpsCardSub: {
    fontSize: 11,
    color: '#166534',
    marginTop: 1,
  },
  gpsActionBtn: {
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.md,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 2,
  },
  gpsActionBtnDisabled: {
    opacity: 0.7,
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  gpsBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  noticeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    padding: 8,
    borderRadius: BorderRadius.sm,
    borderWidth: 1,
  },
  noticeBoxSuccess: {
    backgroundColor: '#DCFCE7',
    borderColor: '#86EFAC',
  },
  noticeBoxWarn: {
    backgroundColor: '#FEF3C7',
    borderColor: '#FDE68A',
  },
  noticeText: {
    fontSize: 11.5,
    fontWeight: '600',
    flex: 1,
  },
  noticeTextSuccess: {
    color: '#166534',
  },
  noticeTextWarn: {
    color: '#92400E',
  },
  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginVertical: 2,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#E2E8F0',
  },
  dividerText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#94A3B8',
    letterSpacing: 0.5,
  },
  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FEE2E2',
    borderWidth: 1,
    borderColor: '#FCA5A5',
    padding: 10,
    borderRadius: BorderRadius.sm,
  },
  errorText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#B91C1C',
    flex: 1,
  },
  formCard: {
    backgroundColor: Colors.surface,
    padding: Spacing.md,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    gap: Spacing.md,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  inputGroup: {
    gap: 6,
  },
  labelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  inputBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    borderRadius: BorderRadius.sm,
    paddingHorizontal: 12,
    height: 48,
    gap: 8,
  },
  textInput: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: '#0F172A',
  },
  chipsSection: {
    gap: 5,
    marginTop: 2,
  },
  chipsLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#64748B',
  },
  chipsWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: BorderRadius.full,
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  chipActive: {
    backgroundColor: '#DCFCE7',
    borderColor: '#16A34A',
  },
  chipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#475569',
  },
  chipTextActive: {
    color: '#166534',
    fontWeight: '700',
  },
  bottomBar: {
    padding: Spacing.md,
    backgroundColor: Colors.surface,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
  },
  finishBtn: {
    width: '100%',
  },
});
