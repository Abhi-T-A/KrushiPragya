import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Image,
  TextInput,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { useReports } from '../../context/ReportContext';
import { Header } from '../../components/common/Header';
import { Button } from '../../components/common/Button';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { diseaseService } from '../../services/api';
import { CropReport } from '../../types';
import { Sparkles } from 'lucide-react-native';

export const PreviewSubmitScreen: React.FC<{ route: any; navigation: any }> = ({
  route,
  navigation,
}) => {
  const { crop, imageUri } = route.params;
  const { t } = useLanguage();
  const { user } = useAuth();
  const { addReport } = useReports();

  const [proxyName, setProxyName] = useState('');
  const [symptoms, setSymptoms] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleSubmit = async () => {
    setIsAnalyzing(true); try {

    // Call service (with backend or seed fallback)
    const cropKey = typeof crop === 'string' ? crop : (crop?.id || 'arecanut');
    let result = null;
    try {
      if (diseaseService && typeof diseaseService.predict === 'function') {
        result = await diseaseService.predict(cropKey, imageUri);
      }
    } catch (e) {
      console.log('Prediction fallback applied');
    }

    const newReport: CropReport = {
      id: `rep_${Date.now()}`,
      crop,
      cropNameKn: crop === 'arecanut' ? 'ಅಡಿಕೆ' : 'ಭತ್ತ',
      cropNameEn: crop === 'arecanut' ? 'Arecanut' : 'Paddy',
      photoUri: imageUri,
      symptoms,
      predictedDisease: result?.predictedDisease || 'Koleroga (Mahali)',
      predictedDiseaseKn: result?.predictedDiseaseKn || 'ಕೊಳೆ ರೋಗ (ಮಹಾಳಿ)',
      scientificName: result?.scientificName || 'Phytophthora meadii',
      confidence: result?.confidence || 0.88,
      status: 'ai_analysed',
      villageId: user?.villageId || 'v2',
      villageName: user?.villageName || 'Ujire',
      reporterRole: user?.role || 'farmer',
      proxyFor: user?.role === 'village_node' ? proxyName : undefined,
      createdAt: 'ಇಂದು, ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      remedyKn: result?.remedyKn,
      remedyEn: result?.remedyEn,
      sourceInstitution: result?.sourceInstitution || 'ICAR-CPCRI Kasaragod',
      evidenceFarmsCount: 1,
    };

    addReport(newReport);
    setIsAnalyzing(false);
    navigation.navigate('AIResult', { reportId: newReport.id });
    } catch (err) {
      console.error('Submit error:', err);
      setIsAnalyzing(false);
    }
  };

  if (isAnalyzing) {
    return (
      <View style={styles.loadingContainer}>
        <View style={styles.loadingCard}>
          <ActivityIndicator size="large" color={Colors.primary} />
          <Text style={styles.loadingTitle}>{t.aiChecking}</Text>
          <Text style={styles.loadingSubtitle}>{t.aiSubChecking}</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Header title={t.previewTitle} showVillage={false} />

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Photo Preview */}
        <View style={styles.imageContainer}>
          <Image source={{ uri: imageUri }} style={styles.previewImg} />
          <View style={styles.cropTag}>
            <Text style={styles.cropTagText}>
              {crop === 'arecanut' ? '🌴 ಅಡಿಕೆ (Arecanut)' : '🌾 ಭತ್ತ (Paddy)'}
            </Text>
          </View>
        </View>

        {/* If logged in as Village Node: show Proxy Farmer Name field */}
        {user?.role === 'village_node' && (
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>{t.proxyLabel}</Text>
            <TextInput
              style={styles.input}
              placeholder={t.proxyPlaceholder}
              placeholderTextColor={Colors.textMuted}
              value={proxyName}
              onChangeText={setProxyName}
            />
          </View>
        )}

        {/* Symptoms Note */}
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>{t.symptomsLabel}</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            placeholder={t.symptomsPlaceholder}
            placeholderTextColor={Colors.textMuted}
            value={symptoms}
            onChangeText={setSymptoms}
            multiline
            numberOfLines={3}
          />
        </View>

        {/* Submit & Analyze Button */}
        <Button
          title={t.submit}
          onPress={handleSubmit}
          icon={<Sparkles size={20} color={Colors.textWhite} />}
        />
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
    gap: Spacing.md,
  },
  imageContainer: {
    width: '100%',
    height: 220,
    borderRadius: BorderRadius.xl,
    overflow: 'hidden',
    position: 'relative',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  previewImg: {
    width: '100%',
    height: '100%',
  },
  cropTag: {
    position: 'absolute',
    bottom: Spacing.sm,
    left: Spacing.sm,
    backgroundColor: 'rgba(0,0,0,0.7)',
    paddingHorizontal: Spacing.md,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
  },
  cropTagText: {
    ...Typography.caption,
    color: Colors.textWhite,
    fontWeight: '700',
  },
  inputGroup: {
    gap: Spacing.xs,
  },
  inputLabel: {
    ...Typography.bodyLarge,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  input: {
    minHeight: 48,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: BorderRadius.md,
    paddingHorizontal: Spacing.md,
    ...Typography.bodyLarge,
    color: Colors.textPrimary,
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
    paddingTop: Spacing.sm,
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: Colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.xl,
  },
  loadingCard: {
    backgroundColor: Colors.surface,
    padding: Spacing.xxl,
    borderRadius: BorderRadius.xl,
    alignItems: 'center',
    gap: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
    width: '100%',
  },
  loadingTitle: {
    ...Typography.title1,
    color: Colors.textPrimary,
    textAlign: 'center',
  },
  loadingSubtitle: {
    ...Typography.caption,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
});
