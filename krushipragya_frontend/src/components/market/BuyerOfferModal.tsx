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
import { ProduceListingItem, submitBuyerOffer } from '../../services/marketApi';
import { X, Send, Tag, Calculator } from 'lucide-react-native';

interface BuyerOfferModalProps {
  visible: boolean;
  listingItem: ProduceListingItem | null;
  buyerId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const BuyerOfferModal: React.FC<BuyerOfferModalProps> = ({
  visible,
  listingItem,
  buyerId,
  onClose,
  onSuccess,
}) => {
  const [offerPrice, setOfferPrice] = useState('');
  const [quantity, setQuantity] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!visible || !listingItem) return null;

  const { listing, crop_name } = listingItem;

  const priceNum = parseFloat(offerPrice) || 0;
  const qtyNum = parseFloat(quantity) || 0;
  const totalAmount = priceNum * qtyNum;

  const handleSubmitOffer = async () => {
    setErrorMsg(null);

    if (priceNum <= 0) {
      setErrorMsg('ದಯವಿಟ್ಟು ಮಾನ್ಯವಾದ ಆಫರ್ ಬೆಲೆಯನ್ನು ನಮೂದಿಸಿ.');
      return;
    }

    if (qtyNum <= 0) {
      setErrorMsg('ದಯವಿಟ್ಟು ಖರೀದಿಸಲು ಬಯಸುವ ಪ್ರಮಾಣವನ್ನು ನಮೂದಿಸಿ.');
      return;
    }

    const availableQty = parseFloat(String(listing.quantity));
    if (qtyNum > availableQty) {
      setErrorMsg(`ಲಭ್ಯವಿರುವ ಗರಿಷ್ಠ ಪ್ರಮಾಣ ${availableQty} ${listing.unit} ಮಾತ್ರ.`);
      return;
    }

    try {
      setLoading(true);
      await submitBuyerOffer(listing.id, buyerId, {
        offered_price: priceNum,
        quantity: qtyNum,
        message: message.trim() || undefined,
      });

      Alert.alert(
        'ಆಫರ್ ಕಳುಹಿಸಲಾಗಿದೆ ✅',
        'ನಿಮ್ಮ ಖರೀದಿ ಆಫರ್ ರೈತರಿಗೆ ತಲುಪಿದೆ. ಅವರು ಸ್ವೀಕರಿಸಿದ ನಂತರ ಸಂಪರ್ಕ ಮತ್ತು ಪಾವತಿ ವಿವರಗಳು ಲಭ್ಯವಾಗುತ್ತವೆ.'
      );

      setOfferPrice('');
      setQuantity('');
      setMessage('');
      onSuccess();
      onClose();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'ಆಫರ್ ಕಳುಹಿಸಲು ವಿಫಲವಾಗಿದೆ.';
      setErrorMsg(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          {/* Header */}
          <View style={styles.header}>
            <View>
              <Text style={styles.headerTitle}>ಖರೀದಿ ಆಫರ್ ಮಾಡಿ</Text>
              <Text style={styles.headerSubTitle}>
                {crop_name} • ಲಭ್ಯ: {listing.quantity} {listing.unit}
              </Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
              <X size={20} color="#374151" />
            </TouchableOpacity>
          </View>

          <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollBody}>
            {errorMsg && (
              <View style={styles.errorBox}>
                <Text style={styles.errorText}>{errorMsg}</Text>
              </View>
            )}

            {/* Target Listing Summary */}
            <View style={styles.listingSummaryCard}>
              <Text style={styles.summaryLabel}>ರೈತರ ನಿರೀಕ್ಷಿತ ಬೆಲೆ</Text>
              <Text style={styles.summaryPrice}>
                ₹{Number(listing.expected_price).toLocaleString('en-IN')}{' '}
                <Text style={styles.summaryUnit}>/ {listing.unit}</Text>
              </Text>
            </View>

            {/* Offer Price Input */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>
                ನಿಮ್ಮ ಆಫರ್ ಬೆಲೆ (₹ ಪ್ರತಿ {listing.unit}) *
              </Text>
              <View style={styles.inputWrapper}>
                <Text style={styles.rupeePrefix}>₹</Text>
                <TextInput
                  style={styles.textInput}
                  placeholder={`ಉದಾ: ${listing.expected_price}`}
                  keyboardType="numeric"
                  value={offerPrice}
                  onChangeText={setOfferPrice}
                />
              </View>
            </View>

            {/* Desired Quantity Input */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>
                ಖರೀದಿಸಬೇಕಾದ ಪ್ರಮಾಣ ({listing.unit}) *
              </Text>
              <TextInput
                style={styles.textInputRegular}
                placeholder={`ಗರಿಷ್ಠ ${listing.quantity} ${listing.unit}`}
                keyboardType="numeric"
                value={quantity}
                onChangeText={setQuantity}
              />
            </View>

            {/* Total Estimated Amount */}
            {totalAmount > 0 && (
              <View style={styles.totalAmountBox}>
                <Calculator size={16} color="#114B32" />
                <View style={{ flex: 1 }}>
                  <Text style={styles.totalAmountLabel}>ಅಂದಾಜು ಒಟ್ಟು ಮೊತ್ತ</Text>
                  <Text style={styles.totalAmountValue}>
                    ₹{Math.round(totalAmount).toLocaleString('en-IN')}
                  </Text>
                </View>
              </View>
            )}

            {/* Optional Message */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>ಸಂದೇಶ (ಐಚ್ಛಿಕ)</Text>
              <TextInput
                style={[styles.textInputRegular, styles.textArea]}
                placeholder="ಪಾವತಿ ಅಥವಾ ಸಾಗಣೆ ಕುರಿತು ನಿಮ್ಮ ಷರತ್ತುಗಳು"
                multiline
                numberOfLines={3}
                value={message}
                onChangeText={setMessage}
              />
            </View>

            {/* Submit CTA */}
            <TouchableOpacity
              activeOpacity={0.85}
              onPress={handleSubmitOffer}
              disabled={loading}
              style={styles.submitBtn}
            >
              {loading ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <>
                  <Send size={16} color="#FFFFFF" />
                  <Text style={styles.submitBtnText}>ಆಫರ್ ಕಳುಹಿಸಿ</Text>
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
    maxHeight: '85%',
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
  headerSubTitle: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  closeBtn: {
    padding: 6,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
  },
  scrollBody: {
    padding: 16,
    gap: 14,
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
  listingSummaryCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    alignItems: 'center',
  },
  summaryLabel: {
    fontSize: 11,
    color: '#6B7280',
    textTransform: 'uppercase',
  },
  summaryPrice: {
    fontSize: 20,
    fontWeight: '800',
    color: '#114B32',
    marginTop: 2,
  },
  summaryUnit: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: 'normal',
  },
  inputGroup: {
    gap: 6,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: '#374151',
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 10,
    paddingHorizontal: 12,
  },
  rupeePrefix: {
    fontSize: 16,
    fontWeight: '700',
    color: '#114B32',
    marginRight: 6,
  },
  textInput: {
    flex: 1,
    paddingVertical: 10,
    fontSize: 15,
    fontWeight: '700',
    color: '#111827',
  },
  textInputRegular: {
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: '#111827',
  },
  textArea: {
    minHeight: 65,
    textAlignVertical: 'top',
  },
  totalAmountBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#EAF7EE',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    borderRadius: 10,
    padding: 12,
  },
  totalAmountLabel: {
    fontSize: 11,
    color: '#166534',
    fontWeight: '600',
  },
  totalAmountValue: {
    fontSize: 18,
    fontWeight: '800',
    color: '#114B32',
    marginTop: 1,
  },
  submitBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#114B32',
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 6,
  },
  submitBtnText: {
    fontSize: 15,
    fontWeight: '800',
    color: '#FFFFFF',
  },
});
