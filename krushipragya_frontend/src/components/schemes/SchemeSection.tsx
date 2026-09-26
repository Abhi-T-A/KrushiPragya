import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Check } from 'lucide-react-native';

interface SchemeSectionProps {
  title: string;
  englishTitle?: string;
  items?: string[];
  description?: string;
  numbered?: boolean;
  children?: React.ReactNode;
}

export const SchemeSection: React.FC<SchemeSectionProps> = ({
  title,
  englishTitle,
  items,
  description,
  numbered = false,
  children,
}) => {
  const hasItems = items && items.length > 0;
  const hasDesc = description && description.trim().length > 0;
  const hasChildren = Boolean(children);

  // If no content provided, do not render an empty shell
  if (!hasItems && !hasDesc && !hasChildren) {
    return null;
  }

  return (
    <View style={styles.sectionCard}>
      {/* Section Header */}
      <View style={styles.headerRow}>
        <Text style={styles.sectionTitle}>{title}</Text>
        {englishTitle ? (
          <Text style={styles.englishTitle}>{englishTitle}</Text>
        ) : null}
      </View>

      {/* Content Area */}
      <View style={styles.contentBody}>
        {hasDesc && (
          <Text style={styles.descriptionText}>{description}</Text>
        )}

        {hasItems && (
          <View style={styles.itemsList}>
            {items!.map((item, idx) => (
              <View key={idx} style={styles.itemRow}>
                {numbered ? (
                  <View style={styles.numberBadge}>
                    <Text style={styles.numberText}>{idx + 1}</Text>
                  </View>
                ) : (
                  <View style={styles.bulletCheck}>
                    <Check size={12} color="#0F6E56" strokeWidth={2.6} />
                  </View>
                )}
                <Text style={styles.itemText}>{item}</Text>
              </View>
            ))}
          </View>
        )}

        {children}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  sectionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 6,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 4,
    elevation: 1,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  englishTitle: {
    fontSize: 12.5,
    fontWeight: '400',
    color: '#6B7280',
  },
  contentBody: {
    paddingTop: 2,
  },
  descriptionText: {
    fontSize: 14,
    fontWeight: '400',
    color: '#374151',
    lineHeight: 22,
  },
  itemsList: {
    gap: 10,
  },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  bulletCheck: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#EAF7EE',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
    marginTop: 2,
  },
  numberBadge: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#EAF7EE',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
    marginTop: 2,
  },
  numberText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#0F6E56',
  },
  itemText: {
    flex: 1,
    fontSize: 14,
    fontWeight: '400',
    color: '#374151',
    lineHeight: 21,
  },
});
