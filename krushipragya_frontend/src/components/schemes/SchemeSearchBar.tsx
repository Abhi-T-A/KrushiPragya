import React from 'react';
import { View, TextInput, TouchableOpacity, StyleSheet } from 'react-native';
import { Search, X } from 'lucide-react-native';

interface SchemeSearchBarProps {
  value: string;
  onChangeText: (text: string) => void;
  onClear?: () => void;
  placeholder?: string;
}

export const SchemeSearchBar: React.FC<SchemeSearchBarProps> = ({
  value,
  onChangeText,
  onClear,
  placeholder = 'ಯೋಜನೆ ಹುಡುಕಿ...',
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.searchBox}>
        <Search size={19} color="#6B7280" style={styles.searchIcon} />
        <TextInput
          style={styles.input}
          placeholder={placeholder}
          placeholderTextColor="#9CA3AF"
          value={value}
          onChangeText={onChangeText}
          returnKeyType="search"
          autoCorrect={false}
          autoCapitalize="none"
        />
        {value.length > 0 && (
          <TouchableOpacity
            style={styles.clearButton}
            onPress={() => {
              onChangeText('');
              if (onClear) onClear();
            }}
            accessibilityRole="button"
            accessibilityLabel="ಹುಡುಕಾಟ ತೆರವುಗೊಳಿಸಿ"
          >
            <X size={16} color="#6B7280" />
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  searchBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    paddingHorizontal: 12,
    height: 46,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  searchIcon: {
    marginRight: 8,
  },
  input: {
    flex: 1,
    fontSize: 14.5,
    color: '#1F2937',
    fontWeight: '400',
    paddingVertical: 0,
  },
  clearButton: {
    padding: 6,
    marginLeft: 4,
  },
});
