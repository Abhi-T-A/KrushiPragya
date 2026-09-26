import React from 'react';
import { ScrollView, TouchableOpacity, Text, StyleSheet, View } from 'react-native';

export type SchemeCategoryKey = 'all' | 'state' | 'agriculture' | 'crop' | 'subsidy' | 'insurance';

export interface CategoryChipItem {
  key: SchemeCategoryKey;
  labelKn: string;
  labelEn: string;
}

export const SCHEME_CATEGORIES: CategoryChipItem[] = [
  { key: 'all', labelKn: 'ಎಲ್ಲಾ', labelEn: 'All' },
  { key: 'state', labelKn: 'ನನ್ನ ರಾಜ್ಯ', labelEn: 'My State' },
  { key: 'agriculture', labelKn: 'ಕೃಷಿ', labelEn: 'Agri' },
  { key: 'crop', labelKn: 'ಬೆಳೆ', labelEn: 'Crop' },
  { key: 'subsidy', labelKn: 'ಸಬ್ಸಿಡಿ', labelEn: 'Subsidy' },
  { key: 'insurance', labelKn: 'ವಿಮೆ', labelEn: 'Insurance' },
];

interface SchemeCategoryChipsProps {
  selectedKey: SchemeCategoryKey;
  onSelect: (key: SchemeCategoryKey) => void;
}

export const SchemeCategoryChips: React.FC<SchemeCategoryChipsProps> = ({
  selectedKey,
  onSelect,
}) => {
  return (
    <View style={styles.container}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {SCHEME_CATEGORIES.map((chip) => {
          const isSelected = selectedKey === chip.key;
          return (
            <TouchableOpacity
              key={chip.key}
              activeOpacity={0.7}
              onPress={() => onSelect(chip.key)}
              style={[
                styles.chip,
                isSelected ? styles.selectedChip : styles.unselectedChip,
              ]}
            >
              <Text
                style={[
                  styles.chipText,
                  isSelected ? styles.selectedText : styles.unselectedText,
                ]}
              >
                {chip.labelKn}
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
    paddingVertical: 6,
  },
  scrollContent: {
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
  },
  chip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
    borderWidth: 1,
    minHeight: 38,
    justifyContent: 'center',
    alignItems: 'center',
  },
  unselectedChip: {
    backgroundColor: '#FFFFFF',
    borderColor: '#E5E7EB',
  },
  selectedChip: {
    backgroundColor: '#0F6E56',
    borderColor: '#0F6E56',
  },
  chipText: {
    fontSize: 13.5,
    fontWeight: '500',
  },
  unselectedText: {
    color: '#4B5563',
  },
  selectedText: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
});
