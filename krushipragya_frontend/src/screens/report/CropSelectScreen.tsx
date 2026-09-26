import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Image,
  ActivityIndicator,
  Alert,
  RefreshControl,
  Dimensions,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { useReports } from '../../context/ReportContext';
import { StatusBadge } from '../../components/trust/StatusBadge';
import {
  fetchFarmerRegisteredCrops,
  BackendFarmerCropItem,
} from '../../services/cropHealthApi';
import {
  ArrowLeft,
  Camera,
  Image as ImageIcon,
  PlusCircle,
  Calendar,
  ChevronRight,
  FileSearch,
  Sprout,
} from 'lucide-react-native';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const GRID_GAP = 12;
const CARD_WIDTH = (SCREEN_WIDTH - 32 - GRID_GAP) / 2;

interface SupportedCrop {
  code: string;
  nameKn: string;
  nameEn: string;
  image: any;
}

const SUPPORTED_CROPS: SupportedCrop[] = [
  {
    code: 'arecanut',
    nameKn: 'ಅಡಿಕೆ',
    nameEn: 'Arecanut',
    image: require('../../../assets/crops/arecanut.jpg'),
  },
  {
    code: 'paddy',
    nameKn: 'ಭತ್ತ',
    nameEn: 'Paddy',
    image: require('../../../assets/crops/paddy.jpg'),
  },
  {
    code: 'coconut',
    nameKn: 'ತೆಂಗು',
    nameEn: 'Coconut',
    image: require('../../../assets/crops/coconut.jpg'),
  },
  {
    code: 'black_pepper',
    nameKn: 'ಕಾಳುಮೆಣಸು',
    nameEn: 'Black Pepper',
    image: require('../../../assets/crops/black_pepper.jpg'),
  },
  {
    code: 'cardamom',
    nameKn: 'ಏಲಕ್ಕಿ',
    nameEn: 'Cardamom',
    image: require('../../../assets/crops/cardamom.jpg'),
  },
  {
    code: 'turmeric',
    nameKn: 'ಅರಿಶಿನ',
    nameEn: 'Turmeric',
    image: require('../../../assets/crops/turmeric.jpg'),
  },
  {
    code: 'ginger',
    nameKn: 'ಶುಂಠಿ',
    nameEn: 'Ginger',
    image: require('../../../assets/crops/ginger.jpg'),
  },
];

const HERO_ILLUSTRATION = require('../../../assets/crops/crop_scan_hero.jpg');

export const CropSelectScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const { language } = useLanguage();
  const { user } = useAuth();
  const { reports, isLoadingReports, refreshReports } = useReports();
  const isKn = language === 'kn';

  const [selectedCrop, setSelectedCrop] = useState<SupportedCrop>(SUPPORTED_CROPS[0]);
  const [registeredFarmerCrops, setRegisteredFarmerCrops] = useState<BackendFarmerCropItem[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const farmerId = user?.id || '11111111-1111-4111-8111-111111111111';
  const phone = user?.phone || '9876543210';

  const loadRegisteredCrops = useCallback(async () => {
    try {
      const data = await fetchFarmerRegisteredCrops(farmerId, phone);
      setRegisteredFarmerCrops(data);
    } catch {
      setRegisteredFarmerCrops([]);
    }
  }, [farmerId, phone]);

  useEffect(() => {
    loadRegisteredCrops();
  }, [loadRegisteredCrops]);

  const onRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([loadRegisteredCrops(), refreshReports()]);
    setIsRefreshing(false);
  };

  const getFarmerCropIdForCode = (code: string): string | undefined => {
    const matched = registeredFarmerCrops.find(
      (fc) => fc.crop?.code?.toLowerCase() === code.toLowerCase()
    );
    return matched?.id;
  };

  // Launch Camera with selected crop
  const handleTakePhotoForCrop = async (cropToUse: SupportedCrop) => {
    try {
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert(
          isKn ? 'ಕ್ಯಾಮೆರಾ ಅನುಮತಿ ಅಗತ್ಯವಿದೆ' : 'Camera Permission Required',
          isKn
            ? 'ಬೆಳೆ ರೋಗ ಪತ್ತೆ ಮಾಡಲು ಕ್ಯಾಮೆರಾ ಪ್ರವೇಶ ಅನುಮತಿಸಿ.'
            : 'Camera access is required to take crop leaf photos.'
        );
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.85,
      });

      if (!result.canceled && result.assets && result.assets[0].uri) {
        navigation.navigate('PreviewSubmit', {
          crop: cropToUse.code,
          cropNameKn: cropToUse.nameKn,
          cropNameEn: cropToUse.nameEn,
          farmerCropId: getFarmerCropIdForCode(cropToUse.code),
          farmerId,
          imageUri: result.assets[0].uri,
        });
      }
    } catch {
      Alert.alert(
        isKn ? 'ದೋಷ ಸಂಭವಿಸಿದೆ' : 'Camera Error',
        isKn
          ? 'ಕ್ಯಾಮೆರಾ ತೆರೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಪ್ರಯತ್ನಿಸಿ.'
          : 'Unable to open camera.'
      );
    }
  };

  // Launch Gallery with selected crop
  const handlePickGalleryForCrop = async (cropToUse: SupportedCrop) => {
    try {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert(
          isKn ? 'ಗ್ಯಾಲರಿ ಅನುಮತಿ ಅಗತ್ಯವಿದೆ' : 'Gallery Permission Required',
          isKn
            ? 'ಫೋಟೋ ಆಯ್ಕೆ ಮಾಡಲು ಗ್ಯಾಲರಿ ಪ್ರವೇಶ ಅನುಮತಿಸಿ.'
            : 'Gallery access is required to pick crop photos.'
        );
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.85,
      });

      if (!result.canceled && result.assets && result.assets[0].uri) {
        navigation.navigate('PreviewSubmit', {
          crop: cropToUse.code,
          cropNameKn: cropToUse.nameKn,
          cropNameEn: cropToUse.nameEn,
          farmerCropId: getFarmerCropIdForCode(cropToUse.code),
          farmerId,
          imageUri: result.assets[0].uri,
        });
      }
    } catch {
      Alert.alert(
        isKn ? 'ದೋಷ ಸಂಭವಿಸಿದೆ' : 'Gallery Error',
        isKn
          ? 'ಗ್ಯಾಲರಿ ತೆರೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಪ್ರಯತ್ನಿಸಿ.'
          : 'Unable to open gallery.'
      );
    }
  };

  // When farmer taps any crop card in the grid
  const handleCropCardPress = (cropItem: SupportedCrop) => {
    setSelectedCrop(cropItem);
    Alert.alert(
      `${cropItem.nameKn} (${cropItem.nameEn})`,
      isKn
        ? 'ಈ ಬೆಳೆಯ ರೋಗ ತಪಾಸಣೆಗಾಗಿ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ ಅಥವಾ ಗ್ಯಾಲರಿಯಿಂದ ಆಯ್ಕೆಮಾಡಿ:'
        : 'Take a photo or pick from gallery to inspect this crop:',
      [
        {
          text: isKn ? 'ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ' : 'Take Photo',
          onPress: () => handleTakePhotoForCrop(cropItem),
        },
        {
          text: isKn ? 'ಗ್ಯಾಲರಿಯಿಂದ ಆಯ್ಕೆ ಮಾಡಿ' : 'Pick from Gallery',
          onPress: () => handlePickGalleryForCrop(cropItem),
        },
        {
          text: isKn ? 'ರದ್ದು' : 'Cancel',
          style: 'cancel',
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      {/* 1. Header (Centered Title, Left Back, Absolutely NO Settings Icon) */}
      <View style={styles.header}>
        <TouchableOpacity
          activeOpacity={0.7}
          onPress={() => navigation.goBack()}
          style={styles.backBtn}
        >
          <ArrowLeft size={20} color="#1F2937" strokeWidth={2.2} />
        </TouchableOpacity>

        <View style={styles.headerTitleBox}>
          <Text style={styles.headerTitleKn}>ಬೆಳೆ ಆರೋಗ್ಯ</Text>
          <Text style={styles.headerTitleEn}>Crop Health</Text>
        </View>

        {/* Empty placeholder of equal size to keep title perfectly centered */}
        <View style={styles.headerPlaceholder} />
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={onRefresh} colors={['#114B32']} />
        }
      >
        {/* 2. Hero Card */}
        <View style={styles.heroCard}>
          {/* Top Row: Text on Left + Contained Illustration on Right */}
          <View style={styles.heroTopRow}>
            <View style={styles.heroTextCol}>
              <Text style={styles.heroTitle}>ನಿಮ್ಮ ಬೆಳೆಯನ್ನು{'\n'}ಪರಿಶೀಲಿಸಿ</Text>
              <Text style={styles.heroSubtitle}>
                ನಿಮ್ಮ ಬೆಳೆಯ ಫೋಟೋ ತೆಗೆದು{'\n'}ಸಂಭಾವ್ಯ ಸಮಸ್ಯೆಗಳನ್ನು ತಿಳಿಯಿರಿ.
              </Text>
            </View>

            <View style={styles.heroImageContainer}>
              <Image
                source={HERO_ILLUSTRATION}
                style={styles.heroImage}
                resizeMode="cover"
              />
            </View>
          </View>

          {/* Vertically Stacked Full-Width Buttons (10px spacing, no emojis) */}
          <View style={styles.heroButtonsStack}>
            <TouchableOpacity
              activeOpacity={0.88}
              onPress={() => handleTakePhotoForCrop(selectedCrop)}
              style={styles.primaryCta}
            >
              <Camera size={19} color="#FFFFFF" strokeWidth={2.2} style={styles.buttonIcon} />
              <Text style={styles.primaryCtaText}>ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ</Text>
            </TouchableOpacity>

            <TouchableOpacity
              activeOpacity={0.85}
              onPress={() => handlePickGalleryForCrop(selectedCrop)}
              style={styles.secondaryCta}
            >
              <ImageIcon size={19} color="#114B32" strokeWidth={2.2} style={styles.buttonIcon} />
              <Text style={styles.secondaryCtaText}>ಗ್ಯಾಲರಿಯಿಂದ ಆಯ್ಕೆ ಮಾಡಿ</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* 3. Section 2: My Crops (ನನ್ನ ಬೆಳೆ) */}
        <View style={styles.sectionHeaderRow}>
          <View style={styles.sectionTitleCol}>
            <Text style={styles.sectionTitle}>
              {isKn ? 'ನನ್ನ ಬೆಳೆ' : 'My Crops'}
            </Text>
            <Text style={styles.sectionSubtitle}>
              {isKn ? 'ಪರಿಶೀಲಿಸಲು ಬೆಳೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ' : 'Select crop to inspect'}
            </Text>
          </View>

          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => navigation.navigate('Profile')}
            style={styles.addCropChip}
          >
            <PlusCircle size={15} color="#114B32" strokeWidth={2} style={styles.addCropIcon} />
            <Text style={styles.addCropChipText}>
              {isKn ? 'ಬೆಳೆಗಳನ್ನು ಸೇರಿಸಿ' : 'Add Crops'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* 2-Column Crop Grid (Equal height cards, Ginger spans full width) */}
        <View style={styles.cropsGrid}>
          {SUPPORTED_CROPS.map((cropItem, index) => {
            const isSelected = selectedCrop.code === cropItem.code;
            const isLastSingle = index === 6; // Ginger (7th crop)

            return (
              <TouchableOpacity
                key={cropItem.code}
                activeOpacity={0.85}
                onPress={() => handleCropCardPress(cropItem)}
                style={[
                  styles.cropGridCard,
                  isLastSingle && styles.cropGridCardFull,
                  isSelected && styles.cropGridCardSelected,
                ]}
              >
                <Image source={cropItem.image} style={styles.cropThumb} resizeMode="cover" />

                <View style={styles.cropTextCol}>
                  <Text style={styles.cropNameKn} numberOfLines={1}>
                    {cropItem.nameKn}
                  </Text>
                  <Text style={styles.cropNameEn} numberOfLines={1}>
                    {cropItem.nameEn}
                  </Text>
                </View>

                <ChevronRight
                  size={16}
                  color={isSelected ? '#114B32' : '#9CA3AF'}
                  strokeWidth={2}
                  style={styles.cardArrow}
                />
              </TouchableOpacity>
            );
          })}
        </View>

        {/* 4. Section 3: Recent Crop Checks (ಇತ್ತೀಚಿನ ಬೆಳೆ ಪರಿಶೀಲನೆಗಳು) */}
        <View style={styles.recentSectionHeader}>
          <Text style={styles.sectionTitle}>ಇತ್ತೀಚಿನ ಬೆಳೆ ಪರಿಶೀಲನೆಗಳು</Text>
          <TouchableOpacity
            activeOpacity={0.7}
            onPress={() => navigation.navigate('ReportTab', { screen: 'ReportList' })}
            style={styles.viewAllRow}
          >
            <Text style={styles.viewAllText}>
              {isKn ? 'ಎಲ್ಲಾ ನೋಡಿ' : 'View All'}
            </Text>
            <ChevronRight size={15} color="#114B32" strokeWidth={2.4} />
          </TouchableOpacity>
        </View>

        {isLoadingReports ? (
          <View style={styles.loadingBox}>
            <ActivityIndicator size="small" color="#114B32" />
            <Text style={styles.loadingText}>
              {isKn ? 'ವರದಿಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...' : 'Loading recent scans...'}
            </Text>
          </View>
        ) : reports.length > 0 ? (
          <View style={styles.reportsContainer}>
            {reports.map((report) => {
              const matchedCrop = SUPPORTED_CROPS.find(
                (c) => c.code.toLowerCase() === report.crop.toLowerCase()
              );
              const cropImg = matchedCrop?.image || SUPPORTED_CROPS[0].image;

              return (
                <TouchableOpacity
                  key={report.id}
                  activeOpacity={0.88}
                  onPress={() => navigation.navigate('AIResult', { reportId: report.id })}
                  style={styles.reportCard}
                >
                  <View style={styles.reportTopRow}>
                    <View style={styles.reportCropBadge}>
                      <Image source={cropImg} style={styles.reportCropIcon} resizeMode="cover" />
                      <Text style={styles.reportCropName}>
                        {report.cropNameKn} ({report.cropNameEn})
                      </Text>
                    </View>
                    <StatusBadge status={report.status} />
                  </View>

                  <View style={styles.reportMainRow}>
                    {report.photoUri ? (
                      <Image source={{ uri: report.photoUri }} style={styles.reportThumb} />
                    ) : (
                      <View style={styles.reportThumbPlaceholder}>
                        <Sprout size={24} color="#114B32" />
                      </View>
                    )}

                    <View style={styles.reportDetailCol}>
                      <Text style={styles.reportDiagnosisLabel}>
                        {isKn ? 'ಪತ್ತೆಯಾದ ಸ್ಥಿತಿ:' : 'Diagnosis:'}
                      </Text>
                      <Text style={styles.reportDiagnosisName} numberOfLines={2}>
                        {report.predictedDiseaseKn || report.predictedDisease}
                      </Text>

                      {report.confidence > 0 && (
                        <Text style={styles.reportConfidenceText}>
                          {isKn ? 'AI ಖಚಿತತೆ' : 'AI Confidence'}: {Math.round(report.confidence * 100)}%
                        </Text>
                      )}

                      <View style={styles.reportDateRow}>
                        <Calendar size={12} color="#6B7280" />
                        <Text style={styles.reportDateText}>{report.createdAt}</Text>
                      </View>
                    </View>

                    <ChevronRight size={18} color="#9CA3AF" />
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        ) : (
          /* Clean Empty State */
          <View style={styles.emptyReportsCard}>
            <View style={styles.emptyIconCircle}>
              <FileSearch size={26} color="#114B32" strokeWidth={1.8} />
            </View>
            <Text style={styles.emptyReportsTitle}>ಇನ್ನೂ ಯಾವುದೇ ಬೆಳೆ ಪರಿಶೀಲನೆಗಳಿಲ್ಲ.</Text>
            <Text style={styles.emptyReportsSub}>
              {isKn
                ? 'ನಿಮ್ಮ ಮೊದಲ ಫೋಟೋ ತೆಗೆದು ಬೆಳೆ ಆರೋಗ್ಯ ಪರಿಶೀಲಿಸಿ.'
                : 'Capture your first photo to start crop health diagnosis.'}
            </Text>
            <TouchableOpacity
              activeOpacity={0.85}
              onPress={() => handleTakePhotoForCrop(selectedCrop)}
              style={styles.startScanBtn}
            >
              <Camera size={18} color="#FFFFFF" strokeWidth={2.2} style={styles.buttonIcon} />
              <Text style={styles.startScanBtnText}>
                {isKn ? 'ಮೊದಲ ಪರಿಶೀಲನೆ ಪ್ರಾರಂಭಿಸಿ' : 'Start First Inspection'}
              </Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F6F7F9',
  },
  // 1. Header Styles
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 48,
    paddingBottom: 12,
    backgroundColor: '#F6F7F9',
  },
  backBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 2,
  },
  headerTitleBox: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitleKn: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
  },
  headerTitleEn: {
    fontSize: 12,
    fontWeight: '400',
    color: '#6B7280',
    marginTop: 1,
  },
  headerPlaceholder: {
    width: 44,
    height: 44,
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 48,
  },
  // 2. Hero Card Styles
  heroCard: {
    backgroundColor: '#EBF7EE',
    borderRadius: 24,
    padding: 20,
    borderWidth: 1,
    borderColor: '#D3EEDA',
    shadowColor: '#114B32',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 1,
    marginBottom: 24,
  },
  heroTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 18,
  },
  heroTextCol: {
    flex: 1,
    paddingRight: 12,
  },
  heroTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#0F3E28',
    lineHeight: 28,
  },
  heroSubtitle: {
    fontSize: 13,
    fontWeight: '400',
    color: '#3E5C4E',
    lineHeight: 19,
    marginTop: 8,
  },
  heroImageContainer: {
    width: 96,
    height: 96,
    borderRadius: 18,
    overflow: 'hidden',
    backgroundColor: '#D7EFE0',
  },
  heroImage: {
    width: '100%',
    height: '100%',
  },
  heroButtonsStack: {
    width: '100%',
    gap: 10,
  },
  primaryCta: {
    width: '100%',
    height: 48,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#114B32',
    borderRadius: 14,
    shadowColor: '#114B32',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 2,
  },
  secondaryCta: {
    width: '100%',
    height: 48,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#34A853',
  },
  buttonIcon: {
    marginRight: 9,
  },
  primaryCtaText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
    includeFontPadding: false,
    textAlignVertical: 'center',
  },
  secondaryCtaText: {
    color: '#114B32',
    fontSize: 14,
    fontWeight: '600',
    includeFontPadding: false,
    textAlignVertical: 'center',
  },
  // 3. Section 2: My Crops Styles
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  sectionTitleCol: {
    flex: 1,
    paddingRight: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
  },
  sectionSubtitle: {
    fontSize: 13,
    fontWeight: '400',
    color: '#6B7280',
    marginTop: 2,
  },
  addCropChip: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#EAF7EE',
    borderWidth: 1,
    borderColor: '#BCE5C8',
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 7,
  },
  addCropIcon: {
    marginRight: 5,
  },
  addCropChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#114B32',
    includeFontPadding: false,
  },
  cropsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: GRID_GAP,
    marginBottom: 26,
  },
  cropGridCard: {
    width: CARD_WIDTH,
    height: 68,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderColor: '#EDF0F2',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 3,
    elevation: 1,
  },
  cropGridCardFull: {
    width: SCREEN_WIDTH - 32,
    height: 68,
  },
  cropGridCardSelected: {
    borderColor: '#114B32',
    backgroundColor: '#F4FAF6',
    borderWidth: 1.5,
  },
  cropThumb: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#F3F4F6',
  },
  cropTextCol: {
    flex: 1,
    marginLeft: 10,
    justifyContent: 'center',
  },
  cropNameKn: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
    includeFontPadding: false,
  },
  cropNameEn: {
    fontSize: 12,
    fontWeight: '400',
    color: '#6B7280',
    marginTop: 2,
    includeFontPadding: false,
  },
  cardArrow: {
    marginLeft: 4,
  },
  // 4. Section 3: Recent Crop Checks Styles
  recentSectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  viewAllRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    paddingVertical: 4,
  },
  viewAllText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#114B32',
    includeFontPadding: false,
  },
  loadingBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
    gap: 8,
    borderWidth: 1,
    borderColor: '#EDF0F2',
  },
  loadingText: {
    fontSize: 13,
    fontWeight: '400',
    color: '#6B7280',
  },
  reportsContainer: {
    gap: 10,
  },
  reportCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: '#EDF0F2',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 3,
    elevation: 1,
    gap: 8,
  },
  reportTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  reportCropBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  reportCropIcon: {
    width: 22,
    height: 22,
    borderRadius: 11,
  },
  reportCropName: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1F2937',
  },
  reportMainRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 4,
    gap: 12,
  },
  reportThumb: {
    width: 56,
    height: 56,
    borderRadius: 10,
    backgroundColor: '#F3F4F6',
  },
  reportThumbPlaceholder: {
    width: 56,
    height: 56,
    borderRadius: 10,
    backgroundColor: '#EAF7EE',
    alignItems: 'center',
    justifyContent: 'center',
  },
  reportDetailCol: {
    flex: 1,
    gap: 2,
  },
  reportDiagnosisLabel: {
    fontSize: 11,
    color: '#6B7280',
    fontWeight: '500',
  },
  reportDiagnosisName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  reportConfidenceText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#15803D',
  },
  reportDateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 2,
  },
  reportDateText: {
    fontSize: 11,
    color: '#9CA3AF',
  },
  emptyReportsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    paddingVertical: 28,
    paddingHorizontal: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#EDF0F2',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 4,
    elevation: 1,
  },
  emptyIconCircle: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: '#EAF7EE',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  emptyReportsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 6,
  },
  emptyReportsSub: {
    fontSize: 13,
    fontWeight: '400',
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: 18,
  },
  startScanBtn: {
    height: 46,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#114B32',
    paddingHorizontal: 22,
    borderRadius: 14,
    shadowColor: '#114B32',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 2,
  },
  startScanBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
    includeFontPadding: false,
    textAlignVertical: 'center',
  },
});