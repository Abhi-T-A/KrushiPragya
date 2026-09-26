import React from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { ProduceListingItem } from '../../services/marketApi';
import { SUPPORTED_MARKET_CROPS } from '../../constants/marketData';
import { MapPin, Tag, ShieldCheck, UserCheck, MessageSquare } from 'lucide-react-native';

interface ProduceListingCardProps {
  item: ProduceListingItem;
  currentUserId: string;
  isBuyer: boolean;
  onPressDetails?: (item: ProduceListingItem) => void;
  onPressOffer?: (item: ProduceListingItem) => void;
  onPressViewOffers?: (item: ProduceListingItem) => void;
}

export const ProduceListingCard: React.FC<ProduceListingCardProps> = ({
  item,
  currentUserId,
  isBuyer,
  onPressDetails,
  onPressOffer,
  onPressViewOffers,
}) => {
  const { listing, crop_name, reference_mandi, offers_count } = item;
  const isOwnListing = listing.farmer_id === currentUserId;

  // Resolve crop image
  const cropCode = Object.keys(SUPPORTED_MARKET_CROPS).find((k) =>
    crop_name.toLowerCase().includes(k) ||
    crop_name.toLowerCase().includes(SUPPORTED_MARKET_CROPS[k].nameEn.toLowerCase())
  ) || 'arecanut';
  const cropMeta = SUPPORTED_MARKET_CROPS[cropCode] || SUPPORTED_MARKET_CROPS.arecanut;

  // Grade translation
  let gradeText = listing.quality_grade;
  if (gradeText === 'A' || gradeText === 'Premium') gradeText = 'ಉತ್ತಮ (Grade A)';
  else if (gradeText === 'B') gradeText = 'ಮಧ್ಯಮ (Grade B)';

  return (
    <View style={styles.card}>
      <View style={styles.topRow}>
        {/* Crop Thumbnail */}
        <Image source={cropMeta.image} style={styles.cropThumb} resizeMode="cover" />

        {/* Info Column */}
        <View style={styles.infoCol}>
          <View style={styles.titleRow}>
            <Text style={styles.cropTitle}>
              {cropMeta.nameKn} ({listing.quantity} {listing.unit})
            </Text>
            {isOwnListing && (
              <View style={styles.ownBadge}>
                <Text style={styles.ownBadgeText}>ನನ್ನ ಪಟ್ಟಿ</Text>
              </View>
            )}
          </View>

          <Text style={styles.gradeText}>ಗುಣಮಟ್ಟ: {gradeText}</Text>

          <View style={styles.priceRow}>
            <Text style={styles.priceText}>
              ₹{Number(listing.expected_price).toLocaleString('en-IN')}
            </Text>
            <Text style={styles.priceUnit}>/ {listing.unit}</Text>
          </View>
        </View>
      </View>

      {/* Location & Status Bar */}
      <View style={styles.metaRow}>
        <View style={styles.locationTag}>
          <MapPin size={12} color="#114B32" />
          <Text style={styles.locationText}>{listing.location}</Text>
          {reference_mandi?.distance_km !== undefined && (
            <Text style={styles.distanceText}>
              • {Math.round(reference_mandi.distance_km)} ಕಿಮೀ
            </Text>
          )}
        </View>

        <View style={[styles.statusBadge, listing.status === 'SOLD' ? styles.statusSold : styles.statusActive]}>
          <Text style={[styles.statusBadgeText, listing.status === 'SOLD' ? styles.statusSoldText : styles.statusActiveText]}>
            {listing.status === 'LISTED' ? 'ಮಾರಾಟಕ್ಕೆ ಲಭ್ಯ' : listing.status === 'OFFER_RECEIVED' ? 'ಆಫರ್ ಬಂದಿದೆ' : listing.status === 'SOLD' ? 'ಮಾರಾಟವಾಗಿದೆ' : listing.status}
          </Text>
        </View>
      </View>

      {/* Reference Mandi Benchmark if present */}
      {reference_mandi && (
        <View style={styles.refMandiBox}>
          <ShieldCheck size={12} color="#15803D" />
          <Text style={styles.refMandiText}>
            ಸಮೀಪದ {reference_mandi.mandi_name}: ₹{Math.round(parseFloat(reference_mandi.modal_price)).toLocaleString('en-IN')}/{reference_mandi.unit}
          </Text>
        </View>
      )}

      {/* Action Buttons */}
      <View style={styles.actionRow}>
        {isOwnListing ? (
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => onPressViewOffers && onPressViewOffers(item)}
            style={styles.offersBtn}
          >
            <MessageSquare size={14} color="#114B32" />
            <Text style={styles.offersBtnText}>
              ಆಫರ್‌ಗಳನ್ನು ಪರಿಶೀಲಿಸಿ ({offers_count || 0})
            </Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => onPressOffer && onPressOffer(item)}
            style={styles.offerBtn}
          >
            <Tag size={14} color="#FFFFFF" />
            <Text style={styles.offerBtnText}>ಆಫರ್ ಮಾಡಿ</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
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
    gap: 12,
  },
  cropThumb: {
    width: 64,
    height: 64,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
  },
  infoCol: {
    flex: 1,
    justifyContent: 'center',
  },
  titleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cropTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111827',
    flex: 1,
  },
  ownBadge: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  ownBadgeText: {
    fontSize: 10,
    color: '#15803D',
    fontWeight: '700',
  },
  gradeText: {
    fontSize: 12,
    color: '#4B5563',
    marginTop: 2,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 2,
    marginTop: 4,
  },
  priceText: {
    fontSize: 17,
    fontWeight: '800',
    color: '#114B32',
  },
  priceUnit: {
    fontSize: 11,
    color: '#6B7280',
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
    paddingTop: 8,
  },
  locationTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  locationText: {
    fontSize: 12,
    color: '#374151',
    fontWeight: '600',
  },
  distanceText: {
    fontSize: 11,
    color: '#6B7280',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  statusBadgeText: {
    fontSize: 11,
    fontWeight: '700',
  },
  statusActive: {
    backgroundColor: '#EAF7EE',
  },
  statusActiveText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#114B32',
  },
  statusSold: {
    backgroundColor: '#F3F4F6',
  },
  statusSoldText: {
    fontSize: 11,
    color: '#6B7280',
  },
  refMandiBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#F0FDF4',
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#BBF7D0',
  },
  refMandiText: {
    fontSize: 11,
    color: '#166534',
    fontWeight: '600',
    flex: 1,
  },
  actionRow: {
    marginTop: 4,
  },
  offerBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#114B32',
    paddingVertical: 10,
    borderRadius: 8,
  },
  offerBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  offersBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#EAF7EE',
    borderWidth: 1,
    borderColor: '#114B32',
    paddingVertical: 10,
    borderRadius: 8,
  },
  offersBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#114B32',
  },
});
