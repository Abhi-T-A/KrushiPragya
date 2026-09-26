import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { NearbyMandiItem } from '../../services/marketApi';
import {
  MapPin,
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronRight,
  ShieldAlert,
  Clock,
} from 'lucide-react-native';

interface MandiCardProps {
  mandi: NearbyMandiItem;
  commodityNameKn: string;
  onPress: (mandi: NearbyMandiItem) => void;
}

export const MandiCard: React.FC<MandiCardProps> = ({
  mandi,
  commodityNameKn,
  onPress,
}) => {
  const price = mandi.latest_price;

  // Format price string: range if min and max available, or modal
  let priceDisplay = 'ದರ ಲಭ್ಯವಿಲ್ಲ';
  if (price) {
    const minVal = parseFloat(price.min);
    const maxVal = parseFloat(price.max);
    const modalVal = parseFloat(price.modal);

    if (minVal && maxVal && minVal !== maxVal) {
      priceDisplay = `₹${Math.round(minVal).toLocaleString('en-IN')} – ₹${Math.round(maxVal).toLocaleString('en-IN')}`;
    } else if (modalVal) {
      priceDisplay = `₹${Math.round(modalVal).toLocaleString('en-IN')}`;
    }
  }

  // Format date
  let dateDisplay = 'ಇಂದು';
  if (price?.date) {
    try {
      const d = new Date(price.date);
      const monthsKn = ['ಜನ', 'ಫೆಬ್ರ', 'ಮಾರ್ಚ್', 'ಏಪ್ರಿಲ್', 'ಮೇ', 'ಜೂನ್', 'ಜುಲೈ', 'ಆಗ', 'ಸೆಪ್ಟೆಂ', 'ಅಕ್ಟೋ', 'ನವೆಂ', 'ಡಿಸೆಂ'];
      dateDisplay = `${d.getDate()} ${monthsKn[d.getMonth()]}`;
    } catch {
      dateDisplay = price.date;
    }
  }

  const isDemo = price?.is_seeded || price?.data_mode === 'DEMO_SEEDED';

  return (
    <TouchableOpacity
      activeOpacity={0.88}
      onPress={() => onPress(mandi)}
      style={styles.card}
    >
      {/* Top Row: Mandi Name & Distance */}
      <View style={styles.topRow}>
        <View style={styles.nameBlock}>
          <Text style={styles.mandiName} numberOfLines={1}>
            {mandi.name}
          </Text>
          <Text style={styles.districtName}>
            {mandi.district}, {mandi.state}
          </Text>
        </View>

        <View style={styles.distanceBadge}>
          <MapPin size={12} color="#114B32" />
          <Text style={styles.distanceText}>
            {mandi.distance_km < 1 ? '1 ಕಿ.ಮೀ ಗಿಂತ ಕಡಿಮೆ' : `${Math.round(mandi.distance_km)} ಕಿ.ಮೀ`}
          </Text>
        </View>
      </View>

      {/* Price & Trend Row */}
      <View style={styles.priceRow}>
        <View style={styles.priceInfo}>
          <Text style={styles.priceValue}>{priceDisplay}</Text>
          <Text style={styles.priceMeta}>
            {dateDisplay} • {price?.unit === 'quintal' ? '100 ಕೆಜಿ (ಕ್ವಿಂಟಾಲ್)' : price?.unit || 'ಪ್ರತಿ ಘಟಕ'}
          </Text>
        </View>

        {/* Trend Indicator */}
        <View style={styles.trendBlock}>
          {mandi.trend === 'UP' && (
            <View style={[styles.trendBadge, styles.trendUp]}>
              <TrendingUp size={13} color="#15803D" />
              <Text style={[styles.trendText, { color: '#15803D' }]}>ಏರಿಕೆ</Text>
            </View>
          )}
          {mandi.trend === 'DOWN' && (
            <View style={[styles.trendBadge, styles.trendDown]}>
              <TrendingDown size={13} color="#B91C1C" />
              <Text style={[styles.trendText, { color: '#B91C1C' }]}>ಇಳಿಕೆ</Text>
            </View>
          )}
          {mandi.trend === 'STABLE' && (
            <View style={[styles.trendBadge, styles.trendStable]}>
              <Minus size={13} color="#4B5563" />
              <Text style={[styles.trendText, { color: '#4B5563' }]}>ಸ್ಥಿರ</Text>
            </View>
          )}
        </View>
      </View>

      {/* Footer Row: Demo notice & Details CTA */}
      <View style={styles.footerRow}>
        {isDemo ? (
          <View style={styles.demoBadge}>
            <ShieldAlert size={11} color="#92400E" />
            <Text style={styles.demoBadgeText}>ಬೆಂಚ್‌ಮಾರ್ಕ್ ದತ್ತಾಂಶ</Text>
          </View>
        ) : (
          <View style={styles.verifiedBadge}>
            <Clock size={11} color="#15803D" />
            <Text style={styles.verifiedText}>ಅಧಿಕೃತ ಎಪಿಎಂಸಿ ವರದಿ</Text>
          </View>
        )}

        <View style={styles.ctaButton}>
          <Text style={styles.ctaText}>ಹಿಂದಿನ ಬೆಲೆಗಳು</Text>
          <ChevronRight size={14} color="#114B32" />
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    padding: 14,
    marginBottom: 10,
    elevation: 1,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    gap: 10,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  nameBlock: {
    flex: 1,
    marginRight: 8,
  },
  mandiName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  districtName: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  distanceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#EAF7EE',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  distanceText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#114B32',
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderRadius: 10,
    padding: 10,
  },
  priceInfo: {
    flex: 1,
  },
  priceValue: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  priceMeta: {
    fontSize: 11,
    color: '#6B7280',
    marginTop: 3,
  },
  trendBlock: {
    alignItems: 'flex-end',
  },
  trendBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  trendUp: {
    backgroundColor: '#DCFCE7',
  },
  trendDown: {
    backgroundColor: '#FEE2E2',
  },
  trendStable: {
    backgroundColor: '#F3F4F6',
  },
  trendText: {
    fontSize: 11,
    fontWeight: '700',
  },
  footerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
    paddingTop: 8,
  },
  demoBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  demoBadgeText: {
    fontSize: 10,
    color: '#92400E',
    fontWeight: '600',
  },
  verifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  verifiedText: {
    fontSize: 10,
    color: '#15803D',
    fontWeight: '600',
  },
  ctaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  ctaText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#114B32',
  },
});
