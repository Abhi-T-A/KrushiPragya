import React from 'react';
import {
  ScrollView,
  TouchableOpacity,
  Text,
  Image,
  StyleSheet,
  View,
} from 'react-native';
import { MarketCrop } from '../../services/marketApi';
import { SUPPORTED_MARKET_CROPS } from '../../constants/marketData';
import { Colors } from '../../constants/theme';

interface CropSelectorProps {
  crops: MarketCrop[];
  selectedCropId: string | null;
  onSelectCrop: (crop: MarketCrop) => void;
}

export const CropSelector: React.FC<CropSelectorProps> = ({
  crops,
  selectedCropId,
  onSelectCrop,
}) => {
  return (
    <View style={styles.container}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {crops.map((crop) => {
          const isSelected = crop.id === selectedCropId;
          const meta = SUPPORTED_MARKET_CROPS[crop.code] || SUPPORTED_MARKET_CROPS.arecanut;

          return (
            <TouchableOpacity
              key={crop.id}
              activeOpacity={0.8}
              onPress={() => onSelectCrop(crop)}
              style={[
                styles.cropItem,
                isSelected && styles.selectedCropItem,
              ]}
            >
              <View style={[styles.imageWrapper, isSelected && styles.selectedImageWrapper]}>
                <Image source={meta.image} style={styles.cropImage} resizeMode="cover" />
              </View>
              <Text
                style={[
                  styles.cropName,
                  isSelected && styles.selectedCropName,
                ]}
                numberOfLines={1}
              >
                {crop.name_kn || meta.nameKn}
              </Text>
              <Text
                style={[
                  styles.cropSubName,
                  isSelected && styles.selectedCropSubName,
                ]}
                numberOfLines={1}
              >
                {crop.name_en || meta.nameEn}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    paddingVertical: 10,
  },
  scrollContent: {
    paddingHorizontal: 12,
    gap: 12,
    flexDirection: 'row',
    alignItems: 'center',
  },
  cropItem: {
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: 8,
    borderRadius: 12,
    backgroundColor: '#F9FAFB',
    borderWidth: 1.5,
    borderColor: '#E5E7EB',
    minWidth: 80,
  },
  selectedCropItem: {
    backgroundColor: '#EAF7EE',
    borderColor: '#114B32',
  },
  imageWrapper: {
    width: 48,
    height: 48,
    borderRadius: 24,
    overflow: 'hidden',
    backgroundColor: '#E5E7EB',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    marginBottom: 6,
  },
  selectedImageWrapper: {
    borderColor: '#114B32',
    borderWidth: 2,
  },
  cropImage: {
    width: '100%',
    height: '100%',
  },
  cropName: {
    fontSize: 13,
    fontWeight: '700',
    color: '#374151',
    textAlign: 'center',
  },
  selectedCropName: {
    color: '#114B32',
    fontWeight: '800',
  },
  cropSubName: {
    fontSize: 10,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 1,
  },
  selectedCropSubName: {
    color: '#166534',
    fontWeight: '600',
  },
});
