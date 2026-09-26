import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image } from 'react-native';
import { Landmark, MapPin, ChevronRight } from 'lucide-react-native';
import { SchemeItem } from '../../types/schemes';
import { SchemeStatusBadge } from './SchemeStatusBadge';
import { SchemeBookmarkButton } from './SchemeBookmarkButton';

interface SchemeCardProps {
  scheme: SchemeItem;
  onPress: () => void;
  onToggleBookmark: () => Promise<void> | void;
}

export const SchemeCard: React.FC<SchemeCardProps> = ({
  scheme,
  onPress,
  onToggleBookmark,
}) => {
  // Support real backend image URL if present, otherwise fallback to clean authentic illustration
  const hasValidRemoteImage =
    typeof scheme.image_url === 'string' &&
    scheme.image_url.trim().startsWith('http');

  const imageSource = hasValidRemoteImage
    ? { uri: scheme.image_url }
    : require('../../../assets/scheme_fallback.jpg');

  return (
    <TouchableOpacity
      activeOpacity={0.88}
      onPress={onPress}
      style={styles.card}
      accessibilityRole="button"
      accessibilityLabel={`${scheme.name} - ${scheme.title_en}`}
    >
      {/* 1. Scheme Image Banner */}
      <View style={styles.imageWrapper}>
        <Image
          source={imageSource}
          style={styles.bannerImage}
          resizeMode="cover"
        />
        {/* Floating Bookmark Button over image */}
        <View style={styles.floatingBookmark}>
          <SchemeBookmarkButton
            isSaved={scheme.is_saved}
            onToggle={onToggleBookmark}
            size="small"
            showBackground={true}
          />
        </View>

        {/* Floating Category Badge */}
        {scheme.category ? (
          <View style={styles.floatingBadge}>
            <SchemeStatusBadge label={scheme.category} variant="success" />
          </View>
        ) : null}
      </View>

      {/* 2. Card Content */}
      <View style={styles.body}>
        {/* Title Block */}
        <View style={styles.titleContainer}>
          <Text style={styles.kannadaTitle} numberOfLines={2}>
            {scheme.title_kn || scheme.name}
          </Text>
          {scheme.title_en && scheme.title_en !== (scheme.title_kn || scheme.name) ? (
            <Text style={styles.englishSubtitle} numberOfLines={1}>
              {scheme.title_en}
            </Text>
          ) : null}
        </View>

        {/* Department & State Info Rows */}
        <View style={styles.metaContainer}>
          <View style={styles.metaRow}>
            <Landmark size={14} color="#0F6E56" style={styles.metaIcon} />
            <Text style={styles.metaText} numberOfLines={1}>
              {scheme.department || 'ಕೃಷಿ ಇಲಾಖೆ'}
            </Text>
          </View>

          <View style={styles.metaRow}>
            <MapPin size={14} color="#6B7280" style={styles.metaIcon} />
            <Text style={styles.metaTextMuted} numberOfLines={1}>
              {scheme.state === 'ಭಾರತ' ? 'ಕೇಂದ್ರ ಸರ್ಕಾರ (Central)' : scheme.state || 'ಕರ್ನಾಟಕ'}
            </Text>
          </View>
        </View>

        {/* Footer Row: Badge & Chevron */}
        <View style={styles.cardFooter}>
          <View style={styles.badgeRow}>
            <SchemeStatusBadge
              label="ಅರ್ಹ ಯೋಜನೆ • Verified"
              variant="neutral"
            />
          </View>

          <View style={styles.chevronBox}>
            <Text style={styles.viewDetailText}>ವಿವರ ನೋಡಿ</Text>
            <ChevronRight size={17} color="#0F6E56" />
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    marginHorizontal: 16,
    marginVertical: 7,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
    overflow: 'hidden',
  },
  imageWrapper: {
    width: '100%',
    height: 125,
    backgroundColor: '#EAF7EE',
    position: 'relative',
  },
  bannerImage: {
    width: '100%',
    height: '100%',
  },
  floatingBookmark: {
    position: 'absolute',
    top: 10,
    right: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.15,
    shadowRadius: 3,
    elevation: 3,
  },
  floatingBadge: {
    position: 'absolute',
    bottom: 10,
    left: 10,
  },
  body: {
    padding: 14,
  },
  titleContainer: {
    marginBottom: 8,
  },
  kannadaTitle: {
    fontSize: 16.5,
    fontWeight: '600',
    color: '#111827',
    lineHeight: 23,
    marginBottom: 2,
  },
  englishSubtitle: {
    fontSize: 13,
    fontWeight: '400',
    color: '#6B7280',
    lineHeight: 18,
  },
  metaContainer: {
    gap: 4,
    marginBottom: 12,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  metaIcon: {
    marginRight: 6,
  },
  metaText: {
    fontSize: 12.5,
    fontWeight: '500',
    color: '#1F2937',
    flex: 1,
  },
  metaTextMuted: {
    fontSize: 12,
    fontWeight: '400',
    color: '#6B7280',
    flex: 1,
  },
  cardFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  badgeRow: {
    flex: 1,
  },
  chevronBox: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingLeft: 6,
  },
  viewDetailText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#0F6E56',
    marginRight: 2,
  },
});
