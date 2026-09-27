import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  TextInput,
  RefreshControl,
  Modal,
  Alert,
  Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  fetchProduceListings,
  submitBuyerOffer,
  ProduceListingItem,
} from '../../services/marketApi';
import { BuyerOfferModal } from '../../components/market/BuyerOfferModal';
import {
  Store,
  Search,
  Tag,
  MapPin,
  TrendingUp,
  ShieldCheck,
  CheckCircle2,
  Calendar,
  X,
  Send,
  Info,
  Layers,
  ArrowRight,
  Filter,
} from 'lucide-react-native';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const FILTER_TAGS = [
  { id: 'ALL', labelEn: 'All Produce', labelKn: 'ಎಲ್ಲವೂ' },
  { id: 'crop-arecanut', labelEn: 'Arecanut', labelKn: 'ಅಡಿಕೆ' },
  { id: 'crop-paddy', labelEn: 'Paddy', labelKn: 'ಭತ್ತ' },
  { id: 'crop-coconut', labelEn: 'Coconut', labelKn: 'ತೆಂಗು' },
  { id: 'crop-pepper', labelEn: 'Black Pepper', labelKn: 'ಕಾಳುಮೆಣಸು' },
  { id: 'crop-cardamom', labelEn: 'Cardamom', labelKn: 'ಏಲಕ್ಕಿ' },
];

interface BuyerProduceScreenProps {
  route?: any;
  navigation: any;
}

export const BuyerProduceScreen: React.FC<BuyerProduceScreenProps> = ({ route, navigation }) => {
  const insets = useSafeAreaInsets();
  const { language } = useLanguage();
  const { user } = useAuth();
  const isKn = language === 'kn';

  const initialCropId = route?.params?.cropId || 'ALL';
  const autoSelectListingId = route?.params?.selectListingId;
  const autoOpenOffer = route?.params?.openOffer;

  const [listings, setListings] = useState<ProduceListingItem[]>([]);
  const [selectedCropFilter, setSelectedCropFilter] = useState<string>(initialCropId);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Detail Modal
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [activeListing, setActiveListing] = useState<ProduceListingItem | null>(null);

  // Make Offer Modal
  const [offerModalVisible, setOfferModalVisible] = useState(false);

  const buyerId = user?.id || '11111111-1111-4111-8111-111111111114';

  const loadListings = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchProduceListings({ status: 'LISTED' });
      setListings(data);

      if (autoSelectListingId) {
        const found = data.find((l) => l.listing.id === autoSelectListingId);
        if (found) {
          setActiveListing(found);
          if (autoOpenOffer) {
            setOfferModalVisible(true);
          } else {
            setDetailModalVisible(true);
          }
        }
      }
    } catch (e) {
      console.warn('Failed to load listings:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [autoSelectListingId, autoOpenOffer]);

  useEffect(() => {
    loadListings();
  }, [loadListings]);

  const onRefresh = () => {
    setRefreshing(true);
    loadListings();
  };

  // Filter listings
  const filteredListings = listings.filter((item) => {
    if (selectedCropFilter !== 'ALL') {
      const match = item.listing.crop_id === selectedCropFilter || item.crop_name.toLowerCase().includes(selectedCropFilter.replace('crop-', ''));
      if (!match) return false;
    }
    if (searchQuery.trim().length > 0) {
      const q = searchQuery.toLowerCase().trim();
      const matchText =
        item.crop_name.toLowerCase().includes(q) ||
        item.listing.location.toLowerCase().includes(q) ||
        (item.farmer_name && item.farmer_name.toLowerCase().includes(q));
      if (!matchText) return false;
    }
    return true;
  });

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.iconCircle}>
            <Store size={20} color="#16A34A" />
          </View>
          <View>
            <Text style={styles.headerTitle}>
              {isKn ? 'ರೈತರ ಮಾರಾಟ ಲಾಟ್‌ಗಳು' : 'Farmer Produce Lots'}
            </Text>
            <Text style={styles.headerSub}>
              {isKn ? 'ನೇರ ರೈತ ಸಂಪರ್ಕ • ಎಪಿಎಂಸಿ ಪರಿಶೀಲಿತ ಬೆಲೆ' : 'Direct Farmer Produce Marketplace'}
            </Text>
          </View>
        </View>
      </View>

      {/* Search Input */}
      <View style={styles.searchBarWrap}>
        <View style={styles.searchInputRow}>
          <Search size={16} color="#94A3B8" />
          <TextInput
            style={styles.searchInput}
            placeholder={isKn ? 'ಬೆಳೆ ಅಥವಾ ಸ್ಥಳ ಹುಡುಕಿ (ಉದಾ: Arecanut, Ujire)...' : 'Search crop / location...'}
            placeholderTextColor="#94A3B8"
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <X size={16} color="#64748B" />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Filter Tags */}
      <View style={styles.filterTagsWrap}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterTagsScroll}>
          {FILTER_TAGS.map((tag) => {
            const isSelected = selectedCropFilter === tag.id;
            return (
              <TouchableOpacity
                key={tag.id}
                style={[styles.filterChip, isSelected && styles.filterChipActive]}
                onPress={() => setSelectedCropFilter(tag.id)}
                activeOpacity={0.7}
              >
                <Text style={[styles.filterChipText, isSelected && styles.filterChipTextActive]}>
                  {isKn ? tag.labelKn : tag.labelEn}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      {/* Produce List */}
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#D97706']} />}
      >
        {loading && !refreshing ? (
          <View style={styles.centerLoading}>
            <ActivityIndicator size="large" color="#D97706" />
            <Text style={styles.loadingText}>
              {isKn ? 'ದಾಸ್ತಾನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...' : 'Loading farmer produce lots...'}
            </Text>
          </View>
        ) : filteredListings.length === 0 ? (
          <View style={styles.emptyCard}>
            <Store size={40} color="#CBD5E1" />
            <Text style={styles.emptyTitle}>
              {isKn ? 'ಯಾವುದೇ ಬೆಳೆ ಲಾಟ್‌ಗಳು ಕಂಡುಬಂದಿಲ್ಲ' : 'No Produce Lots Found'}
            </Text>
            <Text style={styles.emptySub}>
              {isKn ? 'ಬೇರೆ ಹುಡುಕಾಟ ಶಬ್ದ ಅಥವಾ ಫಿಲ್ಟರ್ ಆಯ್ಕೆಮಾಡಿ.' : 'Try changing your search keyword or crop filter.'}
            </Text>
          </View>
        ) : (
          <View style={styles.listContainer}>
            {filteredListings.map((item) => {
              const { listing, crop_name, reference_mandi } = item;
              const mandiPrice = reference_mandi ? Math.round(parseFloat(reference_mandi.modal_price)) : null;

              return (
                <View key={listing.id} style={styles.lotCard}>
                  {/* Card Header */}
                  <View style={styles.lotCardHeader}>
                    <View style={{ flex: 1 }}>
                      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                        <Text style={styles.lotCropTitle}>{crop_name}</Text>
                        <View style={styles.statusBadge}>
                          <Text style={styles.statusBadgeText}>Available</Text>
                        </View>
                      </View>
                      <Text style={styles.lotFarmerSubtitle}>
                        👨‍🌾 {item.farmer_name || 'Demo Farmer'}
                      </Text>
                      <View style={styles.locationRow}>
                        <MapPin size={12} color="#64748B" />
                        <Text style={styles.locationText}>{listing.location}</Text>
                      </View>
                    </View>

                    <View style={styles.priceWrap}>
                      <Text style={styles.priceNum}>
                        ₹{Number(listing.expected_price).toLocaleString('en-IN')}
                      </Text>
                      <Text style={styles.priceQty}>
                        for {listing.quantity} {listing.unit}
                      </Text>
                      <Text style={styles.qualityGrade}>
                        {listing.quality_grade}
                      </Text>
                    </View>
                  </View>

                  {/* Mandi Intelligence Comparison (Section 11) */}
                  {mandiPrice && (
                    <View style={styles.mandiDiffRow}>
                      <TrendingUp size={13} color="#059669" />
                      <Text style={styles.mandiDiffText}>
                        Mandi Modal: ₹{mandiPrice.toLocaleString('en-IN')} • {reference_mandi?.mandi_name}
                      </Text>
                    </View>
                  )}

                  {/* Actions */}
                  <View style={styles.cardActionRow}>
                    <TouchableOpacity
                      style={styles.viewLotButton}
                      onPress={() => {
                        setActiveListing(item);
                        setDetailModalVisible(true);
                      }}
                      activeOpacity={0.8}
                    >
                      <Text style={styles.viewLotButtonText}>
                        {isKn ? 'ವಿವರ ನೋಡಿ' : 'View Lot'}
                      </Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                      style={styles.makeOfferButton}
                      onPress={() => {
                        setActiveListing(item);
                        setOfferModalVisible(true);
                      }}
                      activeOpacity={0.85}
                    >
                      <Tag size={13} color="#FFFFFF" />
                      <Text style={styles.makeOfferButtonText}>
                        {isKn ? 'ಆಫರ್ ನೀಡಿ' : 'Make Offer'}
                      </Text>
                    </TouchableOpacity>
                  </View>
                </View>
              );
            })}
          </View>
        )}
      </ScrollView>

      {/* ============================================================== */}
      {/* Produce Detail Modal (Section 4) */}
      {/* ============================================================== */}
      <Modal
        visible={detailModalVisible}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setDetailModalVisible(false)}
      >
        <View style={styles.modalBackdrop}>
          <View style={[styles.modalSheet, { paddingBottom: Math.max(insets.bottom, 20) }]}>
            <View style={styles.modalSheetHeader}>
              <View style={{ flex: 1 }}>
                <Text style={styles.modalSheetTitle}>
                  {activeListing?.crop_name}
                </Text>
                <Text style={styles.modalSheetSub}>
                  {isKn ? 'ರೈತರ ದಾಸ್ತಾನು ವಿವರಗಳು' : 'Produce Lot Specifications'}
                </Text>
              </View>
              <TouchableOpacity onPress={() => setDetailModalVisible(false)} style={styles.modalCloseBtn}>
                <X size={18} color="#64748B" />
              </TouchableOpacity>
            </View>

            {activeListing && (
              <ScrollView showsVerticalScrollIndicator={false} style={styles.modalSheetContent}>
                <View style={styles.specsGrid}>
                  <View style={styles.specItem}>
                    <Text style={styles.specLabel}>{isKn ? 'ಲಭ್ಯವಿರುವ ಪ್ರಮಾಣ' : 'Quantity'}</Text>
                    <Text style={styles.specValue}>{activeListing.listing.quantity} {activeListing.listing.unit}</Text>
                  </View>

                  <View style={styles.specItem}>
                    <Text style={styles.specLabel}>{isKn ? 'ರೈತರ ನಿರೀಕ್ಷಿತ ದರ' : 'Expected Price'}</Text>
                    <Text style={[styles.specValue, { color: '#B45309', fontWeight: '900' }]}>
                      ₹{Number(activeListing.listing.expected_price).toLocaleString('en-IN')}
                    </Text>
                  </View>

                  <View style={styles.specItem}>
                    <Text style={styles.specLabel}>{isKn ? 'ಸ್ಥಳ' : 'Location'}</Text>
                    <Text style={styles.specValue}>{activeListing.listing.location}</Text>
                  </View>

                  <View style={styles.specItem}>
                    <Text style={styles.specLabel}>{isKn ? 'ಕೊಯ್ಲು ಅವಧಿ' : 'Harvest'}</Text>
                    <Text style={styles.specValue}>September 2026</Text>
                  </View>

                  <View style={styles.specItem}>
                    <Text style={styles.specLabel}>{isKn ? 'ರೈತರು' : 'Farmer'}</Text>
                    <Text style={styles.specValue}>{activeListing.farmer_name || 'Demo Farmer'}</Text>
                  </View>

                  <View style={styles.specItem}>
                    <Text style={styles.specLabel}>{isKn ? 'ದಾಸ್ತಾನು ಸ್ಥಿತಿ' : 'Listing Status'}</Text>
                    <Text style={[styles.specValue, { color: '#16A34A', fontWeight: '800' }]}>AVAILABLE</Text>
                  </View>
                </View>

                {/* Crop condition */}
                <View style={styles.conditionCard}>
                  <Text style={styles.conditionTitle}>{isKn ? 'ಬೆಳೆ ಗುಣಮಟ್ಟ ಮತ್ತು ಸ್ಥಿತಿ:' : 'Crop Condition:'}</Text>
                  <Text style={styles.conditionText}>
                    {activeListing.listing.quality_grade} • {isKn ? 'ರೈತರು ದೃಢೀಕರಿಸಿದ ತಾಜಾ ಬೆಳೆ. ಯಾವುದೇ ಕೀಟಬಾಧೆ ಇಲ್ಲದೆ ಒಣಗಿಸಿ ದಾಸ್ತಾನು ಮಾಡಲಾಗಿದೆ.' : 'Farmer provided information: sun-dried, standard moisture level, ready for immediate yard collection.'}
                  </Text>
                </View>

                {/* Privacy Safeguard Note (Section 4) */}
                <View style={styles.privacyNoteBox}>
                  <Info size={14} color="#64748B" />
                  <Text style={styles.privacyNoteText}>
                    {isKn
                      ? 'ರೈತರ ಖಾಸಗಿ ಸಂಪರ್ಕ ವಿವರಗಳನ್ನು ಆಫರ್ ಅಂಗೀಕಾರವಾದ ನಂತರ ಮಾತ್ರ ಸುರಕ್ಷಿತವಾಗಿ ಅನ್‌ಲಾಕ್ ಮಾಡಲಾಗುತ್ತದೆ.'
                      : 'Farmer contact details are protected and will be securely unlocked upon offer acceptance.'}
                  </Text>
                </View>
              </ScrollView>
            )}

            <View style={styles.modalSheetActions}>
              <TouchableOpacity
                style={styles.sheetCancelBtn}
                onPress={() => setDetailModalVisible(false)}
                activeOpacity={0.7}
              >
                <Text style={styles.sheetCancelBtnText}>{isKn ? 'ಮುಚ್ಚಿ' : 'Close'}</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.sheetOfferBtn}
                onPress={() => {
                  setDetailModalVisible(false);
                  setOfferModalVisible(true);
                }}
                activeOpacity={0.85}
              >
                <Tag size={15} color="#FFFFFF" />
                <Text style={styles.sheetOfferBtnText}>{isKn ? 'ಆಫರ್ ಸಲ್ಲಿಸಿ' : 'MAKE OFFER'}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* ============================================================== */}
      {/* Make Offer Modal Component (Section 5) */}
      {/* ============================================================== */}
      <BuyerOfferModal
        visible={offerModalVisible}
        listingItem={activeListing}
        buyerId={buyerId}
        onClose={() => setOfferModalVisible(false)}
        onSuccess={() => {
          setOfferModalVisible(false);
          Alert.alert(
            isKn ? '✅ ಆಫರ್ ಯಶಸ್ವಿ!' : '✅ Offer Sent!',
            isKn
              ? 'ನಿಮ್ಮ ಖರೀದಿ ಆಫರ್ ರೈತರಿಗೆ ತಲುಪಿದೆ. ರೈತರು ಒಪ್ಪಿದ ನಂತರ ಪಾವತಿ ಮಾಡಬಹುದು.'
              : 'Your purchase offer has been dispatched to the farmer. You can track status in My Offers.',
            [
              {
                text: isKn ? 'ನನ್ನ ಆಫರ್‌ಗಳನ್ನು ನೋಡಿ' : 'View My Offers',
                onPress: () => navigation.navigate('BuyerOffersTab'),
              },
              { text: 'OK' },
            ]
          );
        }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  iconCircle: {
    width: 38,
    height: 38,
    borderRadius: 10,
    backgroundColor: '#DCFCE7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  headerSub: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '500',
    marginTop: 1,
  },
  searchBarWrap: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 6,
    backgroundColor: '#FFFFFF',
  },
  searchInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    paddingHorizontal: 12,
    paddingVertical: 8,
    gap: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 13,
    color: '#0F172A',
    padding: 0,
  },
  filterTagsWrap: {
    backgroundColor: '#FFFFFF',
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  filterTagsScroll: {
    paddingHorizontal: 16,
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#F1F5F9',
  },
  filterChipActive: {
    backgroundColor: '#0F6E56',
  },
  filterChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#475569',
  },
  filterChipTextActive: {
    color: '#FFFFFF',
    fontWeight: '800',
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 36,
  },
  centerLoading: {
    paddingVertical: 50,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  loadingText: {
    fontSize: 13,
    color: '#64748B',
  },
  emptyCard: {
    paddingVertical: 60,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#475569',
  },
  emptySub: {
    fontSize: 12,
    color: '#94A3B8',
  },
  listContainer: {
    gap: 12,
  },
  lotCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    gap: 10,
  },
  lotCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  lotCropTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  statusBadge: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  statusBadgeText: {
    fontSize: 9.5,
    fontWeight: '800',
    color: '#16A34A',
  },
  lotFarmerSubtitle: {
    fontSize: 12,
    color: '#475569',
    marginTop: 2,
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 2,
  },
  locationText: {
    fontSize: 11,
    color: '#64748B',
  },
  priceWrap: {
    alignItems: 'flex-end',
  },
  priceNum: {
    fontSize: 17,
    fontWeight: '900',
    color: '#B45309',
  },
  priceQty: {
    fontSize: 10.5,
    color: '#64748B',
    marginTop: 1,
  },
  qualityGrade: {
    fontSize: 10,
    fontWeight: '700',
    color: '#15803D',
    marginTop: 2,
  },
  mandiDiffRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#F0FDF4',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#DCFCE7',
  },
  mandiDiffText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#15803D',
  },
  cardActionRow: {
    flexDirection: 'row',
    gap: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
  },
  viewLotButton: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    backgroundColor: '#F8FAFC',
  },
  viewLotButtonText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#475569',
  },
  makeOfferButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#D97706',
  },
  makeOfferButtonText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalSheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '85%',
    padding: 18,
  },
  modalSheetHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  modalSheetTitle: {
    fontSize: 17,
    fontWeight: '900',
    color: '#0F172A',
  },
  modalSheetSub: {
    fontSize: 11.5,
    color: '#64748B',
    marginTop: 2,
  },
  modalCloseBtn: {
    padding: 4,
  },
  modalSheetContent: {
    marginTop: 14,
  },
  specsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 14,
  },
  specItem: {
    width: (SCREEN_WIDTH - 56) / 2,
    backgroundColor: '#F8FAFC',
    borderRadius: 8,
    padding: 10,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  specLabel: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '600',
  },
  specValue: {
    fontSize: 13,
    fontWeight: '700',
    color: '#1E293B',
    marginTop: 2,
  },
  conditionCard: {
    backgroundColor: '#FFFBEB',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#FEF3C7',
    marginBottom: 12,
  },
  conditionTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#92400E',
    marginBottom: 4,
  },
  conditionText: {
    fontSize: 12,
    color: '#78350F',
    lineHeight: 17,
  },
  privacyNoteBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F1F5F9',
    borderRadius: 8,
    padding: 10,
    marginBottom: 16,
  },
  privacyNoteText: {
    fontSize: 11,
    color: '#475569',
    flex: 1,
    lineHeight: 15,
  },
  modalSheetActions: {
    flexDirection: 'row',
    gap: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
  },
  sheetCancelBtn: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  sheetCancelBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#475569',
  },
  sheetOfferBtn: {
    flex: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: '#D97706',
  },
  sheetOfferBtnText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#FFFFFF',
  },
});
