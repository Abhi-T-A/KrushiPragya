import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { KARNATAKA_LOCATION_PRESETS, LocationPreset } from '../../constants/marketData';
import { X, MapPin, Navigation } from 'lucide-react-native';

interface LocationSelectorModalProps {
  visible: boolean;
  selectedLocation: LocationPreset | null;
  onSelect: (loc: LocationPreset) => void;
  onRequestGps: () => void;
  onClose: () => void;
}

export const LocationSelectorModal: React.FC<LocationSelectorModalProps> = ({
  visible,
  selectedLocation,
  onSelect,
  onRequestGps,
  onClose,
}) => {
  if (!visible) return null;

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          {/* Header */}
          <View style={styles.header}>
            <View>
              <Text style={styles.headerTitle}>ಸ್ಥಳವನ್ನು ಆಯ್ಕೆಮಾಡಿ</Text>
              <Text style={styles.headerSub}>ನಿಮ್ಮ ಸಮೀಪದ ಮಾರುಕಟ್ಟೆಗಳನ್ನು ಕಂಡುಹಿಡಿಯಲು</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
              <X size={20} color="#374151" />
            </TouchableOpacity>
          </View>

          {/* GPS Auto-detect CTA */}
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={() => {
              onRequestGps();
              onClose();
            }}
            style={styles.gpsDetectBtn}
          >
            <Navigation size={18} color="#114B32" />
            <View style={{ flex: 1 }}>
              <Text style={styles.gpsDetectTitle}>ಪ್ರಸ್ತುತ ಸ್ಥಳವನ್ನು ಬಳಸಿ (GPS)</Text>
              <Text style={styles.gpsDetectSub}>ನಿಮ್ಮ ನೈಜ ಸ್ಥಳವನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಪತ್ತೆಮಾಡಿ</Text>
            </View>
          </TouchableOpacity>

          <View style={styles.dividerRow}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>ಅಥವಾ ಜಿಲ್ಲೆ/ತಾಲೂಕು ಆರಿಸಿ</Text>
            <View style={styles.dividerLine} />
          </View>

          {/* Regional Presets List */}
          <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.presetsList}>
            {KARNATAKA_LOCATION_PRESETS.map((loc) => {
              const isSelected = selectedLocation?.id === loc.id;
              return (
                <TouchableOpacity
                  key={loc.id}
                  activeOpacity={0.7}
                  onPress={() => {
                    onSelect(loc);
                    onClose();
                  }}
                  style={[styles.presetItem, isSelected && styles.selectedPresetItem]}
                >
                  <MapPin size={16} color={isSelected ? '#114B32' : '#6B7280'} />
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.presetName, isSelected && styles.selectedPresetName]}>
                      {loc.nameKn}
                    </Text>
                    <Text style={styles.presetDistrict}>
                      {loc.districtKn} • {loc.nameEn}
                    </Text>
                  </View>
                  {isSelected && (
                    <View style={styles.currentBadge}>
                      <Text style={styles.currentBadgeText}>ಆಯ್ಕೆಮಾಡಲಾಗಿದೆ</Text>
                    </View>
                  )}
                </TouchableOpacity>
              );
            })}
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
    maxHeight: '80%',
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
  headerSub: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  closeBtn: {
    padding: 6,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
  },
  gpsDetectBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#EAF7EE',
    borderWidth: 1.5,
    borderColor: '#A7F3D0',
    borderRadius: 12,
    marginHorizontal: 16,
    marginTop: 14,
    padding: 12,
  },
  gpsDetectTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#114B32',
  },
  gpsDetectSub: {
    fontSize: 11,
    color: '#166534',
    marginTop: 2,
  },
  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    marginVertical: 14,
    gap: 10,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#E5E7EB',
  },
  dividerText: {
    fontSize: 11,
    color: '#9CA3AF',
    fontWeight: '600',
  },
  presetsList: {
    paddingHorizontal: 16,
    gap: 8,
  },
  presetItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 12,
    borderRadius: 10,
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  selectedPresetItem: {
    backgroundColor: '#EAF7EE',
    borderColor: '#114B32',
  },
  presetName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
  },
  selectedPresetName: {
    color: '#114B32',
  },
  presetDistrict: {
    fontSize: 11,
    color: '#6B7280',
    marginTop: 2,
  },
  currentBadge: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  currentBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#15803D',
  },
});
