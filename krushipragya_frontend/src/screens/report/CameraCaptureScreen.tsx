import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  Alert,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useLanguage } from '../../context/LanguageContext';
import { Header } from '../../components/common/Header';
import { Button } from '../../components/common/Button';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { Camera, Image as ImageIcon, Sparkles } from 'lucide-react-native';

export const CameraCaptureScreen: React.FC<{ route: any; navigation: any }> = ({
  route,
  navigation,
}) => {
  const { crop } = route.params || { crop: 'arecanut' };
  const { t } = useLanguage();
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission Denied', 'Camera access is required to take crop photos.');
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0].uri) {
      setSelectedImage(result.assets[0].uri);
    }
  };

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0].uri) {
      setSelectedImage(result.assets[0].uri);
    }
  };

  const handleProceed = () => {
    if (!selectedImage) return;
    navigation.navigate('PreviewSubmit', { crop, imageUri: selectedImage });
  };

  return (
    <View style={styles.container}>
      <Header title={t.captureTitle} showVillage={false} />

      <View style={styles.content}>
        {/* Visual Viewfinder / Guidance Box */}
        <View style={styles.viewfinder}>
          {selectedImage ? (
            <Image source={{ uri: selectedImage }} style={styles.previewImage} />
          ) : (
            <View style={styles.emptyViewfinder}>
              <Camera size={54} color={Colors.primary} />
              <Text style={styles.guidanceText}>{t.captureInstruction}</Text>
              <View style={styles.tipsBox}>
                <Sparkles size={14} color={Colors.accentGold} />
                <Text style={styles.tipsText}>ಉತ್ತಮ ಬೆಳಕಿನಲ್ಲಿ ಹತ್ತಿರದಿಂದ ಫೋಟೋ ತೆಗೆಯಿರಿ</Text>
              </View>
            </View>
          )}
        </View>

        {/* Action Buttons */}
        <View style={styles.actionsBox}>
          {!selectedImage ? (
            <>
              <Button
                title={t.takePhoto}
                onPress={takePhoto}
                icon={<Camera size={20} color={Colors.textWhite} />}
              />
              <Button
                title={t.chooseGallery}
                variant="outline"
                onPress={pickImage}
                icon={<ImageIcon size={20} color={Colors.primary} />}
              />
            </>
          ) : (
            <>
              <Button
                title={t.continue}
                onPress={handleProceed}
              />
              <Button
                title="ಮತ್ತೆ ಫೋಟೋ ತೆಗೆಯಿರಿ (Retake)"
                variant="outline"
                onPress={() => setSelectedImage(null)}
              />
            </>
          )}
        </View>
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
    flex: 1,
    padding: Spacing.lg,
    justifyContent: 'space-between',
  },
  viewfinder: {
    flex: 1,
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.xl,
    borderWidth: 2,
    borderColor: Colors.border,
    borderStyle: 'dashed',
    overflow: 'hidden',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.lg,
  },
  emptyViewfinder: {
    alignItems: 'center',
    padding: Spacing.xl,
    gap: Spacing.md,
  },
  previewImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  guidanceText: {
    ...Typography.bodyLarge,
    fontWeight: '700',
    color: Colors.textPrimary,
    textAlign: 'center',
  },
  tipsBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: Colors.primaryLight,
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
  },
  tipsText: {
    ...Typography.caption,
    color: Colors.primaryDark,
    fontWeight: '600',
  },
  actionsBox: {
    gap: Spacing.md,
    paddingBottom: Spacing.lg,
  },
});
