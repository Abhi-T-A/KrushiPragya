import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { Header } from '../../components/common/Header';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  ProduceListingItem,
  fetchProduceListings,
  submitBuyerOffer,
} from '../../services/marketApi';
import { BuyerOfferModal } from '../../components/market/BuyerOfferModal';
import {
  Store,
  Tag,
  CheckCircle2,
  ShieldCheck,
  MapPin,
  RefreshCw,
  Inbox,
} from 'lucide-react-native';

export const TraderMarketScreen: React.FC = () => {
  const { language } = useLanguage();
  const { user } = useAuth();
  const isKn = language === 'kn';

  const [listings, setListings] = useState<ProduceListingItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedListing, setSelectedListing] = useState<ProduceListingItem | null>(null);
  const [offerModalVisible, setOfferModalVisible] = useState(false);

  const buyerId = user?.id || '11111111-1111-4111-8111-111111111114';

  useEffect(() => {
    loadListings();
  }, []);

  const loadListings = async () => {
    try {
      setLoading(true);
      const data = await fetchProduceListings({ status: 'LISTED' });
      setListings(data);
    } catch (err) {
      console.warn('Failed to load listings:', err);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadListings();
    setRefreshing(false);
  };

  return (
    <View style={styles.container}>
      <Header title={isKn ? 'ವರ್ತಕರ ಮಾರುಕಟ್ಟೆ' : 'Trader Market'} />

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#D97706']} />}
      >
        {/* Banner */}
        <View style={styles.banner}>
          <Store size={24} color="#FFFFFF" />
          <View style={{ flex: 1 }}>
            <Text style={styles.bannerTitle}>
              {user?.name || (isKn ? 'ಖರೀದಿದಾರ / ವರ್ತಕ' : 'Buyer & Trader')}
            </Text>
            <Text style={styles.bannerSub}>
              {isKn ? 'ಎಪಿಎಂಸಿ ದೃಢೀಕೃತ ವ್ಯಾಪಾರ ವೇದಿಕೆ' : 'APMC Verified Trade Network'}
            </Text>
          </View>
        </View>

        <Text style={styles.sectionTitle}>
          {isKn ? 'ರೈತರ ಮಾರಾಟ ಲಾಟ್‌ಗಳು' : 'Farmer Produce Lots Available'}
        </Text>

        {loading && !refreshing ? (
          <View style={styles.centerBox}>
            <ActivityIndicator size="large" color="#D97706" />
            <Text style={styles.loadingText}>ದಾಸ್ತಾನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...</Text>
          </View>
        ) : listings.length === 0 ? (
          <View style={styles.emptyCard}>
            <Inbox size={36} color="#9CA3AF" />
            <Text style={styles.emptyTitle}>
              {isKn ? 'ಈಗ ಯಾವುದೇ ರೈತರ ಬೆಳೆ ಲಭ್ಯವಿಲ್ಲ' : 'No produce lots available currently'}
            </Text>
            <Text style={styles.emptySub}>
              {isKn ? 'ರೈತರು ಹೊಸ ಬೆಳೆಗಳನ್ನು ಪಟ್ಟಿ ಮಾಡಿದಾಗ ಇಲ್ಲಿ ಕಾಣಿಸುತ್ತವೆ.' : 'When farmers list crops, they appear here.'}
            </Text>
          </View>
        ) : (
          <View style={styles.list}>
            {listings.map((item) => {
              const { listing, crop_name, reference_mandi } = item;
              return (
                <View key={listing.id} style={styles.card}>
                  <View style={styles.cardTop}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.cropText}>
                        {crop_name} ({listing.quantity} {listing.unit})
                      </Text>
                      <Text style={styles.farmerText}>
                        {item.farmer_name || 'ರೈತರು'} • {listing.location}
                      </Text>
                    </View>
                    <View style={{ alignItems: 'flex-end' }}>
                      <Text style={styles.priceText}>
                        ₹{Number(listing.expected_price).toLocaleString('en-IN')}
                      </Text>
                      <Text style={styles.priceUnitText}>/ {listing.unit}</Text>
                    </View>
                  </View>

                  {/* Quality & APMC Reference */}
                  <View style={styles.metaRow}>
                    <View style={styles.certBadge}>
                      <ShieldCheck size={12} color="#166534" />
                      <Text style={styles.certText}>
                        ಗುಣಮಟ್ಟ: {listing.quality_grade}
                      </Text>
                    </View>

                    {reference_mandi && (
                      <Text style={styles.refPriceText}>
                        ಎಪಿಎಂಸಿ ದರ: ₹{Math.round(parseFloat(reference_mandi.modal_price)).toLocaleString('en-IN')}
                      </Text>
                    )}
                  </View>

                  <TouchableOpacity
                    style={styles.bidBtn}
                    onPress={() => {
                      setSelectedListing(item);
                      setOfferModalVisible(true);
                    }}
                    activeOpacity={0.85}
                  >
                    <Tag size={14} color="#FFFFFF" />
                    <Text style={styles.bidBtnText}>
                      {isKn ? 'ಖರೀದಿ ಆಫರ್ ಸಲ್ಲಿಸಿ' : 'Place Purchase Offer'}
                    </Text>
                  </TouchableOpacity>
                </View>
              );
            })}
          </View>
        )}
      </ScrollView>

      {/* Buyer Offer Modal */}
      <BuyerOfferModal
        visible={offerModalVisible}
        listingItem={selectedListing}
        buyerId={buyerId}
        onClose={() => setOfferModalVisible(false)}
        onSuccess={loadListings}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC' },
  scrollContent: { padding: Spacing.md, paddingBottom: 40, gap: 12 },
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#D97706',
    borderRadius: BorderRadius.md,
    padding: 14,
  },
  bannerTitle: { fontSize: 15, fontWeight: '800', color: '#FFFFFF' },
  bannerSub: { fontSize: 11, color: '#FEF3C7', marginTop: 2 },
  sectionTitle: { fontSize: 14, fontWeight: '800', color: Colors.textPrimary },
  centerBox: { padding: 40, alignItems: 'center', gap: 10 },
  loadingText: { fontSize: 13, color: '#6B7280' },
  emptyCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    padding: 30,
    alignItems: 'center',
    gap: 8,
  },
  emptyTitle: { fontSize: 14, fontWeight: '700', color: '#374151' },
  emptySub: { fontSize: 12, color: '#9CA3AF', textAlign: 'center' },
  list: { gap: 10 },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 10,
  },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  cropText: { fontSize: 15, fontWeight: '800', color: Colors.textPrimary },
  farmerText: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
  priceText: { fontSize: 16, fontWeight: '800', color: '#D97706' },
  priceUnitText: { fontSize: 10, color: '#6B7280' },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  certBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#DCFCE7',
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: BorderRadius.sm,
  },
  certText: { fontSize: 11, fontWeight: '700', color: '#166534' },
  refPriceText: { fontSize: 11, color: '#6B7280' },
  bidBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#D97706',
    paddingVertical: 10,
    borderRadius: BorderRadius.sm,
  },
  bidBtnText: { fontSize: 13, fontWeight: '800', color: '#FFFFFF' },
});
