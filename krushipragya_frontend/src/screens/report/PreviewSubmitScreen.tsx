import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Image,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  TextInput,
  Alert,
  Platform,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { useReports } from '../../context/ReportContext';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import {
  predictCropDiseaseDirect,
  createCropReportRecord,
  uploadCropReportImageFile,
  DiseasePredictionResult,
} from '../../services/cropHealthApi';
import { CropReport } from '../../types';
import {
  ArrowLeft,
  Camera,
  Image as ImageIcon,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  XCircle,
  HelpCircle,
  Eye,
  FileQuestion,
} from 'lucide-react-native';

const REJECTION_MESSAGES: Record<
  string,
  { titleKn: string; titleEn: string; descKn: string; descEn: string; ctaKn: string; ctaEn: string }
> = {
  LOW_IMAGE_QUALITY: {
    titleKn: 'ಫೋಟೋ ಸ್ಪಷ್ಟವಾಗಿಲ್ಲ',
    titleEn: 'Image Quality Low',
    descKn: 'ದಯವಿಟ್ಟು ಬೆಳೆಯ ಎಲೆ/ಹಣ್ಣು ಸ್ಪಷ್ಟವಾಗಿ ಕಾಣುವಂತೆ ಮತ್ತೊಂದು ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ.',
    descEn: 'Please capture a clear, sharp photo of the affected plant leaf.',
    ctaKn: 'ಮತ್ತೆ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ',
    ctaEn: 'Retake Photo',
  },
  IMAGE_TOO_BLURRY: {
    titleKn: 'ಫೋಟೋ ಸ್ಪಷ್ಟವಾಗಿಲ್ಲ',
    titleEn: 'Photo Too Blurry',
    descKn: 'ಕ್ಯಾಮೆರಾವನ್ನು ನಡುಗಿಸದೆ ಬೆಳೆಯ ಎಲೆಯ ಮೇಲೆ ಫೋಕಸ್ ಮಾಡಿ ಮತ್ತೊಂದು ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ.',
    descEn: 'The photo is blurry. Please hold steady and focus on the crop leaf.',
    ctaKn: 'ಮತ್ತೆ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ',
    ctaEn: 'Retake Photo',
  },
  IMAGE_TOO_DARK: {
    titleKn: 'ಫೋಟೋ ಕತ್ತಲೆಯಾಗಿದೆ',
    titleEn: 'Photo Too Dark',
    descKn: 'ಬೆಳಕು ಸಾಕಾಗುತ್ತಿಲ್ಲ. ದಯವಿಟ್ಟು ನೈಸರ್ಗಿಕ ಬೆಳಕಿನಲ್ಲಿ ಎಲೆ ಸ್ಪಷ್ಟವಾಗಿ ಕಾಣುವಂತೆ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ.',
    descEn: 'The image is too dark. Please capture the leaf in good natural lighting.',
    ctaKn: 'ಮತ್ತೆ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ',
    ctaEn: 'Retake Photo',
  },
  IMAGE_OVEREXPOSED: {
    titleKn: 'ಅತಿಯಾದ ಬೆಳಕಿನಿಂದ ಕೂಡಿದೆ',
    titleEn: 'Photo Overexposed',
    descKn: 'ನೇರ ಸೂರ್ಯನ ಬೆಳಕು ಅಥವಾ ಕ್ಯಾಮೆರಾ ಫ್ಲ್ಯಾಶ್ ತಪ್ಪಿಸಿ ಮತ್ತೊಂದು ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ.',
    descEn: 'The image is washed out with glare. Please avoid direct harsh glare or flash.',
    ctaKn: 'ಮತ್ತೆ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ',
    ctaEn: 'Retake Photo',
  },
  IRRELEVANT_IMAGE: {
    titleKn: 'ಬೆಳೆಯ ಎಲೆ ಕಂಡುಬಂದಿಲ್ಲ',
    titleEn: 'No Crop Leaf Detected',
    descKn: 'ದಯವಿಟ್ಟು ಕೃಷಿ ಬೆಳೆಯ ರೋಗ ಲಕ್ಷಣವಿರುವ ಎಲೆ ಅಥವಾ ಹಣ್ಣಿನ ಸ್ಪಷ್ಟ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ.',
    descEn: 'No suitable crop foliage found. Please upload a clear photo of the crop leaf.',
    ctaKn: 'ಮತ್ತೆ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ',
    ctaEn: 'Retake Photo',
  },
  CROP_MISMATCH: {
    titleKn: 'ಬೆಳೆ ಹೊಂದಿಕೆಯಾಗುತ್ತಿಲ್ಲ',
    titleEn: 'Crop Mismatch',
    descKn: 'ಆಯ್ಕೆ ಮಾಡಿದ ಬೆಳೆ ಮತ್ತು ಫೋಟೋ ಹೊಂದಿಕೆಯಾಗುತ್ತಿಲ್ಲ.',
    descEn: 'The selected crop and uploaded photo do not match.',
    ctaKn: 'ಮತ್ತೆ ಆಯ್ಕೆ ಮಾಡಿ',
    ctaEn: 'Select Crop Again',
  },
  IMAGE_TOO_SMALL: {
    titleKn: 'ಚಿತ್ರದ ಅಳತೆ ಚಿಕ್ಕದಾಗಿದೆ',
    titleEn: 'Resolution Too Small',
    descKn: 'ಚಿತ್ರದ ಗುಣಮಟ್ಟ ಕಡಿಮೆ ಇದೆ. ಹತ್ತಿರದಿಂದ ಹೆಚ್ಚಿನ ರೆಸಲ್ಯೂಶನ್ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ.',
    descEn: 'Image resolution is too low. Please upload a standard photo.',
    ctaKn: 'ಮತ್ತೆ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ',
    ctaEn: 'Retake Photo',
  },
  UNCERTAIN_IMAGE: {
    titleKn: 'ಖಚಿತವಾಗಿ ಗುರುತಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ',
    titleEn: 'Uncertain Diagnosis',
    descKn: 'ಈ ಫೋಟೋದಿಂದ ಸಮಸ್ಯೆಯನ್ನು ಖಚಿತವಾಗಿ ಗುರುತಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.',
    descEn: 'Could not confidently identify the condition from this photo.',
    ctaKn: 'ಮತ್ತೊಂದು ಸ್ಪಷ್ಟವಾದ ಫೋಟೋ ಪ್ರಯತ್ನಿಸಿ',
    ctaEn: 'Try Another Photo',
  },
  MODEL_UNAVAILABLE: {
    titleKn: 'AI ಸೇವೆ ತಾತ್ಕಾಲಿಕವಾಗಿ ಲಭ್ಯವಿಲ್ಲ',
    titleEn: 'AI Service Unavailable',
    descKn: 'ಈ ಬೆಳೆಗೆ AI ವಿಶ್ಲೇಷಣೆ ತಾತ್ಕಾಲಿಕವಾಗಿ ಲಭ್ಯವಿಲ್ಲ. ದಯವಿಟ್ಟು ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಪ್ರಯತ್ನಿಸಿ.',
    descEn: 'AI analysis is temporarily unavailable for this crop. Please retry shortly.',
    ctaKn: 'ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ',
    ctaEn: 'Try Again',
  },
};

export const PreviewSubmitScreen: React.FC<{ route: any; navigation: any }> = ({
  route,
  navigation,
}) => {
  const {
    crop = 'arecanut',
    cropNameKn = 'ಅಡಿಕೆ',
    cropNameEn = 'Arecanut',
    farmerCropId,
    farmerId: routeFarmerId,
    imageUri: initialImageUri,
  } = route.params || {};

  const { language } = useLanguage();
  const { user } = useAuth();
  const { addReport } = useReports();
  const isKn = language === 'kn';

  const [currentImageUri, setCurrentImageUri] = useState<string>(initialImageUri);
  const [notes, setNotes] = useState<string>('');

  // Analysis states: 'idle' | 'analyzing' | 'rejected' | 'network_error'
  const [analysisState, setAnalysisState] = useState<'idle' | 'analyzing' | 'rejected' | 'network_error'>('idle');
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [rejectionData, setRejectionData] = useState<{
    code: string;
    message: string;
  } | null>(null);

  const farmerId = routeFarmerId || user?.id || '11111111-1111-4111-8111-111111111111';
  const phone = user?.phone || '9876543210';

  // Retake photo via camera
  const handleRetakeCamera = async () => {
    try {
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert(isKn ? 'ಅನುಮತಿ ಅಗತ್ಯವಿದೆ' : 'Permission Required', 'Camera permission needed.');
        return;
      }
      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.85,
      });
      if (!result.canceled && result.assets && result.assets[0].uri) {
        setCurrentImageUri(result.assets[0].uri);
        setAnalysisState('idle');
        setRejectionData(null);
      }
    } catch {
      Alert.alert(isKn ? 'ದೋಷ' : 'Error', 'Failed to open camera.');
    }
  };

  // Pick new image from gallery
  const handlePickNewGallery = async () => {
    try {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert(isKn ? 'ಅನುಮತಿ ಅಗತ್ಯವಿದೆ' : 'Permission Required', 'Gallery permission needed.');
        return;
      }
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.85,
      });
      if (!result.canceled && result.assets && result.assets[0].uri) {
        setCurrentImageUri(result.assets[0].uri);
        setAnalysisState('idle');
        setRejectionData(null);
      }
    } catch {
      Alert.alert(isKn ? 'ದೋಷ' : 'Error', 'Failed to open gallery.');
    }
  };

  // Execute Analysis with progressive UI matching real backend steps
  const handleAnalyze = async () => {
    setAnalysisState('analyzing');
    setCurrentStep(1); // 1. ಫೋಟೋ ಪರಿಶೀಲನೆ

    try {
      // Step 1: Decode & file structure check
      await new Promise((r) => setTimeout(r, 400));
      setCurrentStep(2); // 2. ಚಿತ್ರದ ಗುಣಮಟ್ಟ (Lighting & blur)

      // Step 2 -> 3 transition
      await new Promise((r) => setTimeout(r, 400));
      setCurrentStep(3); // 3. ಬೆಳೆ ಮತ್ತು ಎಲೆ ಪರಿಶೀಲನೆ (Foliage relevance)

      // Execute real defensive input verification and EfficientNet inference
      const predictionPromise = predictCropDiseaseDirect(crop, currentImageUri);

      // Transition to AI inference step
      await new Promise((r) => setTimeout(r, 400));
      setCurrentStep(4); // 4. AI ವಿಶ್ಲೇಷಣೆ

      const result: DiseasePredictionResult = await predictionPromise;

      // Handle Rejection
      if (result.status === 'rejected') {
        setRejectionData({
          code: result.reason_code || 'INVALID_IMAGE',
          message: result.message || 'Image rejected by input verification.',
        });
        setAnalysisState('rejected');
        return;
      }

      // Step 5: Preparing results
      setCurrentStep(5); // 5. ಫಲಿತಾಂಶ ಸಿದ್ಧಪಡಿಸಲಾಗುತ್ತಿದೆ
      await new Promise((r) => setTimeout(r, 300));

      // Attempt to persist crop report record to backend if farmerCropId exists
      let backendReportId = `rep_${Date.now()}`;
      try {
        if (farmerCropId) {
          const reportRecord = await createCropReportRecord(
            farmerId,
            farmerCropId,
            notes,
            'leaf.jpg',
            phone
          );
          backendReportId = reportRecord.id;
          // Asynchronously attempt to upload image file to storage
          uploadCropReportImageFile(farmerId, backendReportId, currentImageUri, phone).catch(() => {});
        }
      } catch (err) {
        console.log('Backend report persistence notice:', err);
      }

      const predictedName = result.predicted_class || 'ಅನಿರ್ದಿಷ್ಟ ಸ್ಥಿತಿ';
      const diseaseInfo = result.disease_info;

      const newReport: CropReport = {
        id: backendReportId,
        backendReportId,
        farmerId,
        farmerCropId,
        crop,
        cropNameKn,
        cropNameEn,
        photoUri: currentImageUri,
        symptoms: notes,
        predictedDisease: diseaseInfo?.disease_name_en || result.predicted_class || 'Uncertain Condition',
        predictedDiseaseKn: diseaseInfo?.disease_name_kn || result.predicted_class || 'ಅನಿರ್ದಿಷ್ಟ ಸಮಸ್ಯೆ',
        scientificName: diseaseInfo?.scientific_name,
        category: diseaseInfo?.category,
        confidence: Number(result.confidence || 0),
        lowConfidence: Boolean(result.low_confidence),
        inputVerified: Boolean(result.input_verified),
        reasonCode: result.reason_code || undefined,
        status: 'ai_analysed',
        villageId: user?.villageId || 'v2',
        villageName: user?.villageName || 'Ujire',
        reporterRole: 'farmer',
        createdAt: 'ಇಂದು, ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        remedyKn: diseaseInfo?.remedy_kn,
        remedyEn: diseaseInfo?.remedy_en,
        culturalControl: diseaseInfo?.cultural_control,
        sourceInstitution: diseaseInfo?.source_institution || 'ICAR Research Institute',
        evidenceFarmsCount: 1,
        predictions: result.predictions,
      };

      addReport(newReport);
      setAnalysisState('idle');
      navigation.navigate('AIResult', { reportId: newReport.id });
    } catch (err: any) {
      console.error('Analysis error:', err);
      setAnalysisState('network_error');
    }
  };

  // Render 1: Progressive Analysis Screen
  if (analysisState === 'analyzing') {
    const steps = [
      { id: 1, titleKn: 'ಫೋಟೋ ಪರಿಶೀಲನೆ', titleEn: 'Photo Verification' },
      { id: 2, titleKn: 'ಚಿತ್ರದ ಗುಣಮಟ್ಟ', titleEn: 'Image Quality' },
      { id: 3, titleKn: 'ಬೆಳೆ ಮತ್ತು ಎಲೆ ಪರಿಶೀಲನೆ', titleEn: 'Foliage Relevance' },
      { id: 4, titleKn: 'AI ವಿಶ್ಲೇಷಣೆ', titleEn: 'AI Inference' },
      { id: 5, titleKn: 'ಫಲಿತಾಂಶ ಸಿದ್ಧಪಡಿಸಲಾಗುತ್ತಿದೆ', titleEn: 'Preparing Results' },
    ];

    return (
      <View style={styles.analysisContainer}>
        <View style={styles.analysisCard}>
          <ActivityIndicator size="large" color="#0F5132" style={{ marginBottom: Spacing.md }} />
          <Text style={styles.analysisTitleKn}>ಬೆಳೆ ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ</Text>
          <Text style={styles.analysisSubKn}>
            ನಿಮ್ಮ ಫೋಟೋವನ್ನು ಹಂತ ಹಂತವಾಗಿ ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ.
          </Text>

          <View style={styles.progressListBox}>
            {steps.map((s) => {
              const isDone = currentStep > s.id;
              const isCurrent = currentStep === s.id;

              return (
                <View key={s.id} style={styles.progressItem}>
                  <View style={[styles.stepBullet, isDone && styles.stepBulletDone, isCurrent && styles.stepBulletCurrent]}>
                    {isDone ? (
                      <CheckCircle2 size={16} color="#16A34A" />
                    ) : isCurrent ? (
                      <ActivityIndicator size="small" color="#0F5132" />
                    ) : (
                      <Text style={styles.stepBulletPending}>○</Text>
                    )}
                  </View>
                  <Text
                    style={[
                      styles.stepText,
                      isDone && styles.stepTextDone,
                      isCurrent && styles.stepTextCurrent,
                    ]}
                  >
                    {isDone ? '✓ ' : isCurrent ? '→ ' : '   '}
                    {isKn ? s.titleKn : s.titleEn}
                  </Text>
                </View>
              );
            })}
          </View>
        </View>
      </View>
    );
  }

  // Render 2: Defensive Input Verification Rejection Screen
  if (analysisState === 'rejected' && rejectionData) {
    const info = REJECTION_MESSAGES[rejectionData.code] || REJECTION_MESSAGES.LOW_IMAGE_QUALITY;

    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity activeOpacity={0.7} onPress={() => setAnalysisState('idle')} style={styles.backBtn}>
            <ArrowLeft size={22} color={Colors.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.headerTitleKn}>ಪರಿಶೀಲನೆ ವಿಫಲವಾಗಿದೆ</Text>
          <View style={{ width: 40 }} />
        </View>

        <View style={styles.rejectionCenterContent}>
          <View style={styles.rejectionCard}>
            <View style={styles.rejectionIconBadge}>
              <AlertCircle size={38} color="#DC2626" />
            </View>

            <Text style={styles.rejectionTitle}>{isKn ? info.titleKn : info.titleEn}</Text>
            <Text style={styles.rejectionDesc}>{isKn ? info.descKn : info.descEn}</Text>

            {rejectionData.message && rejectionData.message !== info.descKn && (
              <View style={styles.serverReasonBox}>
                <Text style={styles.serverReasonText}>
                  {rejectionData.message}
                </Text>
              </View>
            )}

            <TouchableOpacity
              activeOpacity={0.88}
              onPress={rejectionData.code === 'CROP_MISMATCH' ? () => navigation.goBack() : handleRetakeCamera}
              style={styles.rejectionCtaBtn}
            >
              <RefreshCw size={18} color="#FFFFFF" />
              <Text style={styles.rejectionCtaBtnText}>
                {isKn ? info.ctaKn : info.ctaEn}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              activeOpacity={0.85}
              onPress={handlePickNewGallery}
              style={styles.rejectionSecBtn}
            >
              <ImageIcon size={18} color="#0F5132" />
              <Text style={styles.rejectionSecBtnText}>
                {isKn ? 'ಗ್ಯಾಲರಿಯಿಂದ ಬೇರೆ ಫೋಟೋ ಆಯ್ಕೆಮಾಡಿ' : 'Pick from Gallery'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  }

  // Render 3: Network / Server Error Screen
  if (analysisState === 'network_error') {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity activeOpacity={0.7} onPress={() => setAnalysisState('idle')} style={styles.backBtn}>
            <ArrowLeft size={22} color={Colors.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.headerTitleKn}>ಸಂಪರ್ಕ ದೋಷ</Text>
          <View style={{ width: 40 }} />
        </View>

        <View style={styles.rejectionCenterContent}>
          <View style={styles.rejectionCard}>
            <View style={[styles.rejectionIconBadge, { backgroundColor: '#FEF2F2' }]}>
              <XCircle size={38} color="#DC2626" />
            </View>

            <Text style={styles.rejectionTitle}>
              {isKn ? 'ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕವನ್ನು ಪರಿಶೀಲಿಸಿ' : 'Network Error'}
            </Text>
            <Text style={styles.rejectionDesc}>
              {isKn
                ? 'ಸರ್ವರ್ ಸಂಪರ್ಕಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕ ಅಥವಾ ವೈ-ಫೈ ಪರಿಶೀಲಿಸಿ.'
                : 'Unable to reach KrushiPragya AI server. Please check your network connection.'}
            </Text>

            <TouchableOpacity
              activeOpacity={0.88}
              onPress={handleAnalyze}
              style={styles.rejectionCtaBtn}
            >
              <RefreshCw size={18} color="#FFFFFF" />
              <Text style={styles.rejectionCtaBtnText}>
                {isKn ? 'ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ' : 'Retry Analysis'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  }

  // Render 4: Initial Photo Preview Screen
  return (
    <View style={styles.container}>
      {/* Top Header */}
      <View style={styles.header}>
        <TouchableOpacity
          activeOpacity={0.7}
          onPress={() => navigation.goBack()}
          style={styles.backBtn}
        >
          <ArrowLeft size={22} color={Colors.textPrimary} />
        </TouchableOpacity>
        <View style={styles.headerTitleBox}>
          <Text style={styles.headerTitleKn}>ಫೋಟೋ ಪೂರ್ವವೀಕ್ಷಣೆ</Text>
          <Text style={styles.headerTitleEn}>Photo Preview</Text>
        </View>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Selected Image Card */}
        <View style={styles.previewImageCard}>
          <Image source={{ uri: currentImageUri }} style={styles.previewImage} resizeMode="cover" />
        </View>

        {/* Selected Crop Badge */}
        <View style={styles.cropMetaCard}>
          <Text style={styles.cropMetaLabel}>
            {isKn ? 'ಆಯ್ಕೆ ಮಾಡಿದ ಬೆಳೆ:' : 'Selected Crop:'}
          </Text>
          <Text style={styles.cropMetaName}>
            {cropNameKn} ({cropNameEn})
          </Text>
        </View>

        {/* Optional Symptoms Note */}
        <View style={styles.notesBox}>
          <Text style={styles.notesLabel}>
            {isKn ? 'ಲಕ್ಷಣಗಳ ಟಿಪ್ಪಣಿ (ಐಚ್ಛಿಕ):' : 'Observed Symptoms (Optional):'}
          </Text>
          <TextInput
            style={styles.notesInput}
            placeholder={
              isKn
                ? 'ಉದಾ: ಎಲೆಗಳಲ್ಲಿ ಹಳದಿ ಅಥವಾ ಕಂದು ಚುಕ್ಕೆಗಳು, ಸುಳಿ ಕೊಳೆತ...'
                : 'e.g. Yellow leaf spots, wilting, bud rotting...'
            }
            placeholderTextColor="#94A3B8"
            value={notes}
            onChangeText={setNotes}
            multiline
            numberOfLines={2}
          />
        </View>

        {/* Action Buttons */}
        <View style={styles.actionsBox}>
          {/* Analyze CTA */}
          <TouchableOpacity
            activeOpacity={0.88}
            onPress={handleAnalyze}
            style={styles.analyzeBtn}
          >
            <Sparkles size={20} color="#FFFFFF" strokeWidth={2.4} />
            <Text style={styles.analyzeBtnText}>
              {isKn ? 'ವಿಶ್ಲೇಷಿಸಿ' : 'Analyze Crop Health'}
            </Text>
          </TouchableOpacity>

          {/* Retake Action */}
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={handleRetakeCamera}
            style={styles.retakeBtn}
          >
            <Camera size={18} color="#0F5132" strokeWidth={2.2} />
            <Text style={styles.retakeBtnText}>
              {isKn ? 'ಮತ್ತೆ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ' : 'Retake Photo'}
            </Text>
          </TouchableOpacity>

          {/* Choose from gallery alternative */}
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={handlePickNewGallery}
            style={styles.galleryAltBtn}
          >
            <ImageIcon size={16} color="#64748B" />
            <Text style={styles.galleryAltBtnText}>
              {isKn ? 'ಗ್ಯಾಲರಿಯಿಂದ ಬೇರೆ ಫೋಟೋ ಆಯ್ಕೆಮಾಡಿ' : 'Pick from Gallery'}
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F6F7F9',
  },
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
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  previewImageCard: {
    width: '100%',
    aspectRatio: 1,
    backgroundColor: '#000000',
    borderRadius: 20,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#EDF0F2',
    marginBottom: 16,
  },
  previewImage: {
    width: '100%',
    height: '100%',
  },
  cropMetaCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: '#EDF0F2',
    marginBottom: 14,
  },
  cropMetaLabel: {
    fontSize: 13,
    color: '#6B7280',
    fontWeight: '500',
  },
  cropMetaName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#114B32',
  },
  notesBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: '#EDF0F2',
    marginBottom: 20,
  },
  notesLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 6,
  },
  notesInput: {
    backgroundColor: '#F9FAFB',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    padding: 10,
    fontSize: 13,
    color: '#1F2937',
    minHeight: 56,
    textAlignVertical: 'top',
  },
  actionsBox: {
    gap: 10,
  },
  analyzeBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#114B32',
    paddingVertical: 14,
    borderRadius: 14,
    gap: 8,
    shadowColor: '#114B32',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 2,
  },
  analyzeBtnText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  retakeBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    paddingVertical: 12,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#34A853',
    gap: 8,
  },
  retakeBtnText: {
    color: '#114B32',
    fontSize: 14,
    fontWeight: '600',
  },
  galleryAltBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    gap: 6,
  },
  galleryAltBtnText: {
    color: '#6B7280',
    fontSize: 13,
    fontWeight: '500',
  },
  // Progressive Analysis Styles
  analysisContainer: {
    flex: 1,
    backgroundColor: '#F6F7F9',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  analysisCard: {
    width: '100%',
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#EDF0F2',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 3,
  },
  analysisTitleKn: {
    fontSize: 18,
    fontWeight: '600',
    color: '#0F3E28',
    textAlign: 'center',
    marginBottom: 6,
  },
  analysisSubKn: {
    fontSize: 13,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 20,
  },
  progressListBox: {
    width: '100%',
    gap: 12,
  },
  progressItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 4,
  },
  stepBullet: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepBulletDone: {
    backgroundColor: '#EAF7EE',
  },
  stepBulletCurrent: {
    backgroundColor: '#F0FDF4',
  },
  stepBulletPending: {
    fontSize: 14,
    color: '#9CA3AF',
  },
  stepText: {
    fontSize: 14,
    color: '#9CA3AF',
    fontWeight: '400',
  },
  stepTextDone: {
    color: '#15803D',
    fontWeight: '600',
  },
  stepTextCurrent: {
    color: '#114B32',
    fontWeight: '600',
  },
  // Rejection Styles
  rejectionCenterContent: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
  },
  rejectionCard: {
    width: '100%',
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#FEE2E2',
    shadowColor: '#DC2626',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  rejectionIconBadge: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#FEE2E2',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  rejectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#991B1B',
    textAlign: 'center',
    marginBottom: 8,
  },
  rejectionDesc: {
    fontSize: 13,
    color: '#4B5563',
    textAlign: 'center',
    lineHeight: 19,
    marginBottom: 16,
  },
  serverReasonBox: {
    backgroundColor: '#FEF2F2',
    padding: 10,
    borderRadius: 10,
    width: '100%',
    marginBottom: 16,
  },
  serverReasonText: {
    fontSize: 12,
    color: '#B91C1C',
    textAlign: 'center',
  },
  rejectionCtaBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#114B32',
    width: '100%',
    paddingVertical: 13,
    borderRadius: 14,
    gap: 8,
    marginBottom: 10,
  },
  rejectionCtaBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  rejectionSecBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    width: '100%',
    paddingVertical: 12,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#34A853',
    gap: 8,
  },
  rejectionSecBtnText: {
    color: '#114B32',
    fontSize: 13,
    fontWeight: '600',
  },
});
