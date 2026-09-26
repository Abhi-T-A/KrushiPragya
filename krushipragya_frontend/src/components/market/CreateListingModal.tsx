import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { MarketCrop, createProduceListing } from '../../services/marketApi';
import { SUPPORTED_MARKET_CROPS } from '../../constants/marketData';
import { X, Check, Camera, MapPin } from 'lucide-react-native';

interface CreateListingModalProps {
  visible: boolean;
  crops: MarketCrop[];
  farmerId: string;
  defaultLocation?: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const CreateListingModal: React.FC<CreateListingModalProps> = ({
  visible,
  crops,
  farmerId,
  defaultLocation = 'ಉಜಿರೆ, ದಕ್ಷಿಣ ಕನ್ನಡ',
  onClose,
  onSuccess,
}) => {
  const [selectedCrop, setSelectedCrop] = useState<MarketCrop | null>(crops[0] || null);
  const [quantity, setQuantity] = useState('');
  const [unit, setUnit] = useState('kg');
  const [qualityGrade, setQualityGrade] = useState('A');
  const [expectedPrice, setExpectedPrice] = useState('');
  const [location, setLocation] = useState(defaultLocation);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const units = [
    { labelKn: 'ಕೆಜಿ', val: 'kg' },
    { labelKn: 'ಕ್ವಿಂಟಾಲ್', val: 'quintal' },
    { labelKn: 'ಬ್ಯಾಗ್', val: 'bag' },
    { labelKn: 'ಟನ್', val: 'tonne' },
  ];

  const grades = [
    { labelKn: 'ಉತ್ತಮ (Grade A)', val: 'A' },
    { labelKn: 'ಮಧ್ಯಮ (Grade B)', val: 'B' },
    { labelKn: 'ಪ್ರೀಮಿಯಂ', val: 'Premium' },
  ];

  const handleSubmit = async () => {
    setErrorMessage(null);

    const cropToUse = selectedCrop || crops[0];
    if (!cropToUse) {
      setErrorMessage('ದಯವಿಟ್ಟು ಬೆಳೆ ಆಯ್ಕೆಮಾಡಿ.');
      return;
    }

    const qtyNum = parseFloat(quantity);
    if (!qtyNum || isNaN(qtyNum) || qtyNum <= 0) {
      setErrorMessage('ದಯವಿಟ್ಟು ಮಾನ್ಯವಾದ ಪ್ರಮಾಣವನ್ನು ನಮೂದಿಸಿ (0 ಕ್ಕಿಂತ ಹೆಚ್ಚು).');
      return;
    }

    const priceNum = parseFloat(expectedPrice);
    if (!priceNum || isNaN(priceNum) || priceNum <= 0) {
      setErrorMessage('ದಯವಿಟ್ಟು ಮಾನ್ಯವಾದ ಬೆಲೆಯನ್ನು ನಮೂದಿಸಿ (0 ಕ್ಕಿಂತ ಹೆಚ್ಚು).');
      return;
    }

    if (!location.trim()) {
      setErrorMessage('ದಯವಿಟ್ಟು ಸ್ಥಳವನ್ನು ನಮೂದಿಸಿ.');
      return;
    }

    try {
      setLoading(true);
      await createProduceListing(farmerId, {
        crop_id: cropToUse.id,
        quantity: qtyNum,
        unit,
        quality_grade: qualityGrade,
        expected_price: priceNum,
        location: location.trim(),
      });

      Alert.alert(
        'ಪಟ್ಟಿಯನ್ನು ರಚಿಸಲಾಗಿದೆ ✅',
        'ನಿಮ್ಮ ಬೆಳೆ ಈಗ ಮಾರುಕಟ್ಟೆಯಲ್ಲಿ ಖರೀದಿದಾರರಿಗೆ ಲಭ್ಯವಿದೆ.'
      );

      // Reset form
      setQuantity('');
      setExpectedPrice('');
      setDescription('');
      onSuccess();
      onClose();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'ಪಟ್ಟಿ ರಚಿಸಲು ವಿಫಲವಾಗಿದೆ.';
      setErrorMessage(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  if (!visible) return null;

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.headerTitle}>ನಿಮ್ಮ ಬೆಳೆ ಮಾರಾಟಕ್ಕೆ ಹಾಕಿ</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
              <X size={20} color="#374151" />
            </TouchableOpacity>
          </View>

          <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.formScroll}>
            {errorMessage && (
              <View style={styles.errorBox}>
                <Text style={styles.errorText}>{errorMessage}</Text>
              </View>
            )}

            {/* 1. Crop Picker */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>ಬೆಳೆ ಆಯ್ಕೆಮಾಡಿ *</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.cropChipsRow}>
                {crops.map((c) => {
                  const isSelected = selectedCrop?.id === c.id;
                  const meta = SUPPORTED_MARKET_CROPS[c.code];
                  return (
                    <TouchableOpacity
                      key={c.id}
                      activeOpacity={0.8}
                      onPress={() => setSelectedCrop(c)}
                      style={[styles.cropChip, isSelected && styles.selectedCropChip]}
                    >
                      <Text style={[styles.cropChipText, isSelected && styles.selectedCropChipText]}>
                        {c.name_kn || meta?.nameKn || c.name_en}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </ScrollView>
            </View>

            {/* 2. Quantity & Unit */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>ಪ್ರಮಾಣ ಮತ್ತು ಘಟಕ *</Text>
              <View style={styles.qtyRow}>
                <TextInput
                  style={[styles.input, { flex: 1.5 }]}
                  placeholder="ಉದಾ: 500"
                  keyboardType="numeric"
                  value={quantity}
                  onChangeText={setQuantity}
                />
                <View style={styles.unitButtonsRow}>
                  {units.map((u) => (
                    <TouchableOpacity
                      key={u.val}
                      onPress={() => setUnit(u.val)}
                      style={[styles.unitBtn, unit === u.val && styles.selectedUnitBtn]}
                    >
                      <Text style={[styles.unitBtnText, unit === u.val && styles.selectedUnitBtnText]}>
                        {u.labelKn}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            </View>

            {/* 3. Quality Grade */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>ಗುಣಮಟ್ಟದ ದರ್ಜೆ *</Text>
              <View style={styles.gradesRow}>
                {grades.map((g) => (
                  <TouchableOpacity
                    key={g.val}
                    onPress={() => setQualityGrade(g.val)}
                    style={[styles.gradeBtn, qualityGrade === g.val && styles.selectedGradeBtn]}
                  >
                    <Text style={[styles.gradeBtnText, qualityGrade === g.val && styles.selectedGradeBtnText]}>
                      {g.labelKn}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {/* 4. Expected Price */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>ನಿರೀಕ್ಷಿತ ಬೆಲೆ (₹ ಪ್ರತಿ {unit}) *</Text>
              <View style={styles.priceInputWrapper}>
                <Text style={styles.rupeeSymbol}>₹</Text>
                <TextInput
                  style={styles.priceInput}
                  placeholder="ಉದಾ: 450"
                  keyboardType="numeric"
                  value={expectedPrice}
                  onChangeText={setExpectedPrice}
                />
              </View>
            </View>

            {/* 5. Location */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>ಸ್ಥಳ (ಗ್ರಾಮ / ತಾಲೂಕು) *</Text>
              <View style={styles.locationInputWrapper}>
                <MapPin size={16} color="#6B7280" />
                <TextInput
                  style={styles.locationInput}
                  placeholder="ಸ್ಥಳ ನಮೂದಿಸಿ"
                  value={location}
                  onChangeText={setLocation}
                />
              </View>
            </View>

            {/* 6. Description (Optional) */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>ವಿವರಣೆ (ಐಚ್ಛಿಕ)</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                placeholder="ಬೆಳೆಯ ವೈಶಿಷ್ಟ್ಯ, ಒಣಗಿಸಿದ ವಿಧಾನ, ಇತ್ಯಾದಿ"
                multiline
                numberOfLines={3}
                value={description}
                onChangeText={setDescription}
              />
            </View>

            {/* Submit Button */}
            <TouchableOpacity
              activeOpacity={0.85}
              onPress={handleSubmit}
              disabled={loading}
              style={styles.submitBtn}
            >
              {loading ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <>
                  <Check size={18} color="#FFFFFF" />
                  <Text style={styles.submitBtnText}>ಮಾರಾಟಕ್ಕೆ ಪಟ್ಟಿ ಮಾಡಿ</Text>
                </>
              )}
            </TouchableOpacity>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
    paddingBottom: 24,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: '#111827',
  },
  closeBtn: {
    padding: 6,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
  },
  formScroll: {
    padding: 16,
    gap: 16,
  },
  errorBox: {
    backgroundColor: '#FEE2E2',
    borderWidth: 1,
    borderColor: '#FCA5A5',
    borderRadius: 8,
    padding: 10,
  },
  errorText: {
    fontSize: 12,
    color: '#B91C1C',
    fontWeight: '600',
  },
  inputGroup: {
    gap: 6,
  },
  label: {
    fontSize: 13,
    fontWeight: '700',
    color: '#374151',
  },
  cropChipsRow: {
    gap: 8,
    paddingVertical: 4,
  },
  cropChip: {
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  selectedCropChip: {
    backgroundColor: '#EAF7EE',
    borderColor: '#114B32',
  },
  cropChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4B5563',
  },
  selectedCropChipText: {
    color: '#114B32',
    fontWeight: '800',
  },
  qtyRow: {
    flexDirection: 'row',
    gap: 10,
    alignItems: 'center',
  },
  input: {
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: '#111827',
  },
  unitButtonsRow: {
    flexDirection: 'row',
    gap: 4,
    flex: 2,
  },
  unitBtn: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  selectedUnitBtn: {
    backgroundColor: '#114B32',
    borderColor: '#114B32',
  },
  unitBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#4B5563',
  },
  selectedUnitBtnText: {
    color: '#FFFFFF',
  },
  gradesRow: {
    flexDirection: 'row',
    gap: 8,
  },
  gradeBtn: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 9,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  selectedGradeBtn: {
    backgroundColor: '#EAF7EE',
    borderColor: '#114B32',
  },
  gradeBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#4B5563',
  },
  selectedGradeBtnText: {
    color: '#114B32',
  },
  priceInputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 10,
    paddingHorizontal: 12,
  },
  rupeeSymbol: {
    fontSize: 16,
    fontWeight: '700',
    color: '#114B32',
    marginRight: 6,
  },
  priceInput: {
    flex: 1,
    paddingVertical: 10,
    fontSize: 15,
    color: '#111827',
    fontWeight: '700',
  },
  locationInputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 10,
    paddingHorizontal: 12,
  },
  locationInput: {
    flex: 1,
    paddingVertical: 10,
    fontSize: 13,
    color: '#111827',
  },
  textArea: {
    minHeight: 70,
    textAlignVertical: 'top',
  },
  submitBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#114B32',
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 8,
  },
  submitBtnText: {
    fontSize: 15,
    fontWeight: '800',
    color: '#FFFFFF',
  },
});
