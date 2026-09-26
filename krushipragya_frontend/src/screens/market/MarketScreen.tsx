import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  FlatList,
  ActivityIndicator,
  Share,
  Alert,
  RefreshControl,
} from 'react-native';
import * as Location from 'expo-location';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Header } from '../../components/common/Header';
import {
  MarketCrop,
  NearbyMandiItem,
  NearbyMandisResponse,
  ProduceListingItem,
  BuyerOfferItem,
  TransactionDetail,
  fetchMarketCrops,
  fetchNearbyMandis,
  fetchProduceListings,
  fetchFarmerListings,
  fetchBuyerOffers,
  fetchMyTransactions,
  fetchListingOffers,
} from '../../services/marketApi';
import {
  SUPPORTED_MARKET_CROPS,
  KARNATAKA_LOCATION_PRESETS,
  LocationPreset,
} from '../../constants/marketData';

// UI Components
import { CropSelector } from '../../components/market/CropSelector';
import { MandiCard } from '../../components/market/MandiCard';
import { MandiDetailModal } from '../../components/market/MandiDetailModal';
import { ProduceListingCard } from '../../components/market/ProduceListingCard';
import { CreateListingModal } from '../../components/market/CreateListingModal';
import { BuyerOfferModal } from '../../components/market/BuyerOfferModal';
import { OfferReviewModal } from '../../components/market/OfferReviewModal';
import { TransactionModal } from '../../components/market/TransactionModal';
import { LocationSelectorModal } from '../../components/market/LocationSelectorModal';

// Icons
import {
  TrendingUp,
  Store,
  Share2,
  MapPin,
  ArrowUpDown,
  Filter,
  PlusCircle,
  RefreshCw,
  AlertCircle,
  Inbox,
  ShoppingBag,
  ListOrdered,
  Tag,
  CheckCircle,
  Navigation,
} from 'lucide-react-native';

export const MarketScreen: React.FC<{ route?: any }> = ({ route }) => {
  const { language } = useLanguage();
  const { user } = useAuth();
  const isKn = language === 'kn';

  // Section Switch: 'mandi_prices' (ಮಾರುಕಟ್ಟೆ ದರ) vs 'farmer_marketplace' (ರೈತರ ಮಾರುಕಟ್ಟೆ)
  const [activeSection, setActiveSection] = useState<'mandi_prices' | 'farmer_marketplace'>('mandi_prices');

  // Shared Crop Catalog
  const [crops, setCrops] = useState<MarketCrop[]>([]);
  const [selectedCrop, setSelectedCrop] = useState<MarketCrop | null>(null);

  // Mandi Price Discovery State
  const [nearbyData, setNearbyData] = useState<NearbyMandisResponse | null>(null);
  const [mandiLoading, setMandiLoading] = useState(false);
  const [mandiError, setMandiError] = useState<string | null>(null);
  const [selectedMandiForDetail, setSelectedMandiForDetail] = useState<NearbyMandiItem | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);

  // Location & Geolocation State
  const [locationPreset, setLocationPreset] = useState<LocationPreset>(KARNATAKA_LOCATION_PRESETS[0]);
  const [userCoords, setUserCoords] = useState<{ latitude: number; longitude: number } | null>(null);
  const [locationPermissionDenied, setLocationPermissionDenied] = useState(false);
  const [locationModalVisible, setLocationModalVisible] = useState(false);
  const [searchRadiusKm, setSearchRadiusKm] = useState(500);

  // Mandi Filters & Sorting
  const [sortOption, setSortOption] = useState<'distance' | 'price'>('distance');
  const [priceSortOrder, setPriceSortOrder] = useState<'asc' | 'desc'>('desc');

  // Farmer Marketplace State
  const [marketplaceSubTab, setMarketplaceSubTab] = useState<'browse' | 'my_market'>('browse');
  const [myMarketTab, setMyMarketTab] = useState<'listings' | 'offers' | 'purchases' | 'sales'>('listings');
  const [produceListings, setProduceListings] = useState<ProduceListingItem[]>([]);
  const [farmerOwnListings, setFarmerOwnListings] = useState<ProduceListingItem[]>([]);
  const [buyerSubmittedOffers, setBuyerSubmittedOffers] = useState<BuyerOfferItem[]>([]);
  const [myTransactions, setMyTransactions] = useState<TransactionDetail[]>([]);
  const [marketplaceLoading, setMarketplaceLoading] = useState(false);
  const [marketplaceError, setMarketplaceError] = useState<string | null>(null);

  // Marketplace Modals State
  const [createListingModalVisible, setCreateListingModalVisible] = useState(false);
  const [selectedListingForOffer, setSelectedListingForOffer] = useState<ProduceListingItem | null>(null);
  const [buyerOfferModalVisible, setBuyerOfferModalVisible] = useState(false);
  const [selectedListingOffers, setSelectedListingOffers] = useState<BuyerOfferItem[]>([]);
  const [offerReviewModalVisible, setOfferReviewModalVisible] = useState(false);
  const [selectedOfferForTransaction, setSelectedOfferForTransaction] = useState<BuyerOfferItem | null>(null);
  const [transactionModalVisible, setTransactionModalVisible] = useState(false);

  const [refreshing, setRefreshing] = useState(false);

  // Active user ID and role
  const currentUserId = user?.id || '11111111-1111-4111-8111-111111111111';
  const isBuyerRole = user?.role === 'buyer';

  // ============================================================================
  // 1. Initial Data Loading & GPS Setup
  // ============================================================================

  useEffect(() => {
    loadInitialCrops();
    requestGpsLocation();
  }, []);

  const loadInitialCrops = async () => {
    try {
      const data = await fetchMarketCrops();
      if (data && data.length > 0) {
        setCrops(data);
        setSelectedCrop(data[0]);
      } else {
        // Fallback from static constant if network empty
        const fallbackList: MarketCrop[] = Object.values(SUPPORTED_MARKET_CROPS).map((c, idx) => ({
          id: `c0000000-0000-4000-8000-00000000000${idx + 1}`,
          code: c.code,
          name_en: c.nameEn,
          name_kn: c.nameKn,
        }));
        setCrops(fallbackList);
        setSelectedCrop(fallbackList[0]);
      }
    } catch {
      const fallbackList: MarketCrop[] = Object.values(SUPPORTED_MARKET_CROPS).map((c, idx) => ({
        id: `c0000000-0000-4000-8000-00000000000${idx + 1}`,
        code: c.code,
        name_en: c.nameEn,
        name_kn: c.nameKn,
      }));
      setCrops(fallbackList);
      setSelectedCrop(fallbackList[0]);
    }
  };

  const requestGpsLocation = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setLocationPermissionDenied(true);
        return;
      }
      setLocationPermissionDenied(false);
      const loc = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });
      setUserCoords({
        latitude: loc.coords.latitude,
        longitude: loc.coords.longitude,
      });
    } catch (err) {
      console.warn('GPS location request failed:', err);
      setLocationPermissionDenied(true);
    }
  };

  // ============================================================================
  // 2. Fetch Mandi Price Discovery Data
  // ============================================================================

  const loadNearbyMandis = useCallback(async () => {
    if (!selectedCrop) return;
    try {
      setMandiLoading(true);
      setMandiError(null);

      const lat = userCoords?.latitude ?? locationPreset.latitude;
      const lon = userCoords?.longitude ?? locationPreset.longitude;

      console.log('[MARKET] latitude:', lat);
      console.log('[MARKET] longitude:', lon);
      console.log('[MARKET] crop:', selectedCrop.name_en);
      console.log('[MARKET] crop_id:', selectedCrop.id);

      const data = await fetchNearbyMandis({
        crop_id: selectedCrop.id,
        latitude: lat,
        longitude: lon,
        radius_km: searchRadiusKm,
        sort: sortOption,
      });

      setNearbyData(data);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'ಮಾರುಕಟ್ಟೆ ಮಾಹಿತಿ ಲೋಡ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.';
      setMandiError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setMandiLoading(false);
    }
  }, [selectedCrop, userCoords, locationPreset, searchRadiusKm, sortOption]);

  useEffect(() => {
    if (activeSection === 'mandi_prices' && selectedCrop) {
      loadNearbyMandis();
    }
  }, [activeSection, selectedCrop, loadNearbyMandis]);

  // ============================================================================
  // 3. Fetch Farmer Marketplace Data
  // ============================================================================

  const loadMarketplaceData = useCallback(async () => {
    try {
      setMarketplaceLoading(true);
      setMarketplaceError(null);

      if (marketplaceSubTab === 'browse') {
        const listings = await fetchProduceListings({
          crop_id: selectedCrop?.id,
          status: 'LISTED',
        });
        setProduceListings(listings);
      } else {
        // My Marketplace Sub-Tab
        if (myMarketTab === 'listings') {
          const own = await fetchFarmerListings(currentUserId);
          setFarmerOwnListings(own);
        } else if (myMarketTab === 'offers') {
          const buyerOffers = await fetchBuyerOffers(currentUserId);
          setBuyerSubmittedOffers(buyerOffers);
        } else if (myMarketTab === 'purchases' || myMarketTab === 'sales') {
          const txs = await fetchMyTransactions(currentUserId);
          setMyTransactions(txs);
        }
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'ಮಾರುಕಟ್ಟೆ ದತ್ತಾಂಶ ಲೋಡ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.';
      setMarketplaceError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setMarketplaceLoading(false);
    }
  }, [marketplaceSubTab, myMarketTab, selectedCrop, currentUserId]);

  useEffect(() => {
    if (activeSection === 'farmer_marketplace') {
      loadMarketplaceData();
    }
  }, [activeSection, marketplaceSubTab, myMarketTab, loadMarketplaceData]);

  // Handle pull to refresh
  const onRefresh = async () => {
    setRefreshing(true);
    if (activeSection === 'mandi_prices') {
      await loadNearbyMandis();
    } else {
      await loadMarketplaceData();
    }
    setRefreshing(false);
  };

  // Share market rates
  const handleShare = async () => {
    try {
      const cropName = selectedCrop?.name_kn || 'ಕೃಷಿ ಬೆಳೆಗಳು';
      const mandiCount = nearbyData?.total_mandis || 0;
      await Share.share({
        message: `ಕೃಷಿಪ್ರಜ್ಞಾ ಮಾರುಕಟ್ಟೆ ದರಗಳು: ${cropName} ಗೆ ಸಂಬಂಧಿಸಿದಂತೆ ${mandiCount} ಸಮೀಪದ ಎಪಿಎಂಸಿ ಮಾರುಕಟ್ಟೆ ದರಗಳನ್ನು ಪರಿಶೀಲಿಸಿ. KrushiPragya - ರೈತರ ಡಿಜಿಟಲ್ ಕೃಷಿ ವೇದಿಕೆ.`,
      });
    } catch {
      // User cancelled
    }
  };

  // View offers on farmer's own listing
  const handleViewOffersOnListing = async (item: ProduceListingItem) => {
    try {
      const offers = await fetchListingOffers(item.listing.id, currentUserId);
      setSelectedListingOffers(offers);
      setOfferReviewModalVisible(true);
    } catch (err: any) {
      Alert.alert('ಆಫರ್‌ಗಳು', 'ಆಫರ್‌ಗಳನ್ನು ಲೋಡ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.');
    }
  };

  // Sort mandis locally if price sort is toggled
  const getSortedMandis = (): NearbyMandiItem[] => {
    if (!nearbyData?.mandis) return [];
    const list = [...nearbyData.mandis];

    if (sortOption === 'price') {
      return list.sort((a, b) => {
        const priceA = parseFloat(a.latest_price?.modal || a.latest_price?.max || '0');
        const priceB = parseFloat(b.latest_price?.modal || b.latest_price?.max || '0');
        return priceSortOrder === 'desc' ? priceB - priceA : priceA - priceB;
      });
    }

    return list.sort((a, b) => a.distance_km - b.distance_km);
  };

  const sortedMandis = getSortedMandis();

  // ============================================================================
  // RENDER UI
  // ============================================================================

  return (
    <View style={styles.container}>
      {/* 1. Header with Share Action */}
      <Header
        title={isKn ? 'ಮಾರುಕಟ್ಟೆ' : 'Market'}
        rightAction={
          <TouchableOpacity activeOpacity={0.8} onPress={handleShare} style={styles.shareBtn}>
            <Share2 size={18} color="#114B32" />
            <Text style={styles.shareBtnText}>{isKn ? 'ಶೇರ್' : 'Share'}</Text>
          </TouchableOpacity>
        }
      />

      {/* 2. Top Segment: Mandi Price Discovery vs Farmer Marketplace */}
      <View style={styles.topSegmentBar}>
        <TouchableOpacity
          activeOpacity={0.85}
          onPress={() => setActiveSection('mandi_prices')}
          style={[styles.segmentBtn, activeSection === 'mandi_prices' && styles.segmentBtnActive]}
        >
          <TrendingUp size={16} color={activeSection === 'mandi_prices' ? '#114B32' : '#6B7280'} />
          <Text style={[styles.segmentBtnText, activeSection === 'mandi_prices' && styles.segmentBtnTextActive]}>
            {isKn ? 'ಮಾರುಕಟ್ಟೆ ದರ' : 'Mandi Prices'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          activeOpacity={0.85}
          onPress={() => setActiveSection('farmer_marketplace')}
          style={[styles.segmentBtn, activeSection === 'farmer_marketplace' && styles.segmentBtnActive]}
        >
          <Store size={16} color={activeSection === 'farmer_marketplace' ? '#114B32' : '#6B7280'} />
          <Text style={[styles.segmentBtnText, activeSection === 'farmer_marketplace' && styles.segmentBtnTextActive]}>
            {isKn ? 'ರೈತರ ಮಾರುಕಟ್ಟೆ' : 'Farmer Marketplace'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* 3. Horizontally Scrollable 7-Crop Selector */}
      <CropSelector
        crops={crops}
        selectedCropId={selectedCrop?.id || null}
        onSelectCrop={(c) => setSelectedCrop(c)}
      />

      {/* ====================================================================== */}
      {/* SECTION A: MANDI PRICE DISCOVERY                                      */}
      {/* ====================================================================== */}
      {activeSection === 'mandi_prices' && (
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollBody}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#114B32']} />}
        >
          {/* Location & Radius Banner */}
          <View style={styles.locationBar}>
            <View style={styles.locationInfo}>
              <MapPin size={15} color="#114B32" />
              <Text style={styles.locationText} numberOfLines={1}>
                {userCoords ? 'ನನ್ನ ಪ್ರಸ್ತುತ ಸ್ಥಳ (GPS)' : locationPreset.nameKn}
              </Text>
            </View>

            <TouchableOpacity
              activeOpacity={0.8}
              onPress={() => setLocationModalVisible(true)}
              style={styles.changeLocBtn}
            >
              <Text style={styles.changeLocText}>ಸ್ಥಳ ಬದಲಿಸಿ</Text>
            </TouchableOpacity>
          </View>

          {/* Location Permission Denied Warning Banner with Manual Selector Fallback */}
          {locationPermissionDenied && !userCoords && (
            <View style={styles.locWarningBox}>
              <AlertCircle size={16} color="#92400E" />
              <View style={{ flex: 1 }}>
                <Text style={styles.locWarningTitle}>ನಿಮ್ಮ ಸ್ಥಳವನ್ನು ಬಳಸಲು ಅನುಮತಿ ನೀಡಿ</Text>
                <Text style={styles.locWarningSub}>
                  ಹತ್ತಿರದ ಮಾರುಕಟ್ಟೆಗಳನ್ನು ಕಂಡುಹಿಡಿಯಲು ಸ್ಥಳ ಅಗತ್ಯ. ಅಥವಾ ಕೈಯಾರೆ ಆಯ್ಕೆಮಾಡಿ:
                </Text>
              </View>
              <TouchableOpacity
                onPress={() => setLocationModalVisible(true)}
                style={styles.locFallbackBtn}
              >
                <Text style={styles.locFallbackBtnText}>ಸ್ಥಳ ಆಯ್ಕೆ</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Real Backend Count & Filter Controls */}
          <View style={styles.controlsBar}>
            <View style={{ flex: 1 }}>
              <Text style={styles.mandisFoundText}>
                {nearbyData
                  ? `${nearbyData.total_mandis} ಮಾರುಕಟ್ಟೆಗಳು ${nearbyData.radius_km} ಕಿಮೀ ಒಳಗೆ`
                  : 'ಮಾರುಕಟ್ಟೆಗಳನ್ನು ಶೋಧಿಸಲಾಗುತ್ತಿದೆ...'}
              </Text>
            </View>

            {/* Sorting Buttons */}
            <View style={styles.sortButtonsRow}>
              <TouchableOpacity
                activeOpacity={0.8}
                onPress={() => setSortOption('distance')}
                style={[styles.sortBtn, sortOption === 'distance' && styles.sortBtnActive]}
              >
                <MapPin size={12} color={sortOption === 'distance' ? '#FFFFFF' : '#374151'} />
                <Text style={[styles.sortBtnText, sortOption === 'distance' && styles.sortBtnTextActive]}>
                  ಅಂತರ
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                activeOpacity={0.8}
                onPress={() => {
                  if (sortOption === 'price') {
                    setPriceSortOrder(priceSortOrder === 'desc' ? 'asc' : 'desc');
                  } else {
                    setSortOption('price');
                    setPriceSortOrder('desc');
                  }
                }}
                style={[styles.sortBtn, sortOption === 'price' && styles.sortBtnActive]}
              >
                <ArrowUpDown size={12} color={sortOption === 'price' ? '#FFFFFF' : '#374151'} />
                <Text style={[styles.sortBtnText, sortOption === 'price' && styles.sortBtnTextActive]}>
                  {sortOption === 'price'
                    ? priceSortOrder === 'desc'
                      ? 'ಬೆಲೆ (ಹೆಚ್ಚು)'
                      : 'ಬೆಲೆ (ಕಡಿಮೆ)'
                    : 'ಬೆಲೆ'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Loading Skeleton */}
          {mandiLoading && !refreshing && (
            <View style={styles.loadingBox}>
              <ActivityIndicator size="large" color="#114B32" />
              <Text style={styles.loadingText}>ಸಮೀಪದ ಎಪಿಎಂಸಿ ದರಗಳನ್ನು ಪಡೆಯಲಾಗುತ್ತಿದೆ...</Text>
            </View>
          )}

          {/* Error State */}
          {mandiError && !mandiLoading && (
            <View style={styles.errorCard}>
              <AlertCircle size={28} color="#B91C1C" />
              <Text style={styles.errorCardTitle}>ಮಾಹಿತಿ ಲೋಡ್ ಮಾಡಲು ವಿಫಲವಾಗಿದೆ</Text>
              <Text style={styles.errorCardSub}>{mandiError}</Text>
              <TouchableOpacity onPress={loadNearbyMandis} style={styles.retryBtn}>
                <RefreshCw size={14} color="#FFFFFF" />
                <Text style={styles.retryBtnText}>ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Empty State: No Nearby Mandis */}
          {!mandiLoading && !mandiError && sortedMandis.length === 0 && (
            <View style={styles.emptyCard}>
              <Inbox size={36} color="#9CA3AF" />
              <Text style={styles.emptyTitle}>ನಿಮ್ಮ ಸುತ್ತಮುತ್ತ ಮಾರುಕಟ್ಟೆಗಳು ಕಂಡುಬಂದಿಲ್ಲ.</Text>
              <Text style={styles.emptySub}>
                ಆಯ್ಕೆಮಾಡಿದ ಬೆಳೆಗಾಗಿ {searchRadiusKm} ಕಿ.ಮೀ ವ್ಯಾಪ್ತಿಯಲ್ಲಿ ಯಾವುದೇ ಎಪಿಎಂಸಿ ಮಾರುಕಟ್ಟೆ ವರದಿಗಳಿಲ್ಲ.
              </Text>
              <TouchableOpacity
                onPress={() => setSearchRadiusKm(1500)}
                style={styles.expandRadiusBtn}
              >
                <Text style={styles.expandRadiusBtnText}>500 ಕಿಮೀ ಮೀರಿದ ಮಾರುಕಟ್ಟೆಗಳನ್ನು ನೋಡಿ</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Mandi Cards List */}
          {!mandiLoading && !mandiError && (
            <View style={styles.cardsList}>
              {sortedMandis.map((mandi) => (
                <MandiCard
                  key={mandi.market_id}
                  mandi={mandi}
                  commodityNameKn={selectedCrop?.name_kn || 'ಬೆಳೆ'}
                  onPress={(item) => {
                    setSelectedMandiForDetail(item);
                    setDetailModalVisible(true);
                  }}
                />
              ))}
            </View>
          )}
        </ScrollView>
      )}

      {/* ====================================================================== */}
      {/* SECTION B: FARMER MARKETPLACE (TRANSACTIONAL)                          */}
      {/* ====================================================================== */}
      {activeSection === 'farmer_marketplace' && (
        <View style={{ flex: 1 }}>
          {/* Sub Navigation Bar */}
          <View style={styles.marketplaceSubNavBar}>
            <TouchableOpacity
              onPress={() => setMarketplaceSubTab('browse')}
              style={[styles.subTabBtn, marketplaceSubTab === 'browse' && styles.subTabBtnActive]}
            >
              <ShoppingBag size={14} color={marketplaceSubTab === 'browse' ? '#114B32' : '#6B7280'} />
              <Text style={[styles.subTabBtnText, marketplaceSubTab === 'browse' && styles.subTabBtnTextActive]}>
                ಎಲ್ಲಾ ಬೆಳೆಗಳು (ಖರೀದಿ)
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={() => setMarketplaceSubTab('my_market')}
              style={[styles.subTabBtn, marketplaceSubTab === 'my_market' && styles.subTabBtnActive]}
            >
              <ListOrdered size={14} color={marketplaceSubTab === 'my_market' ? '#114B32' : '#6B7280'} />
              <Text style={[styles.subTabBtnText, marketplaceSubTab === 'my_market' && styles.subTabBtnTextActive]}>
                ನನ್ನ ಮಾರುಕಟ್ಟೆ
              </Text>
            </TouchableOpacity>
          </View>

          {/* TAB 1: BROWSE PRODUCE */}
          {marketplaceSubTab === 'browse' && (
            <ScrollView
              showsVerticalScrollIndicator={false}
              contentContainerStyle={styles.scrollBody}
              refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#114B32']} />}
            >
              {/* Create Listing Banner Button */}
              <TouchableOpacity
                activeOpacity={0.88}
                onPress={() => setCreateListingModalVisible(true)}
                style={styles.createListingBanner}
              >
                <PlusCircle size={20} color="#FFFFFF" />
                <View style={{ flex: 1 }}>
                  <Text style={styles.createListingTitle}>ನಿಮ್ಮ ಬೆಳೆ ಮಾರಾಟಕ್ಕೆ ಹಾಕಿ</Text>
                  <Text style={styles.createListingSub}>ನೇರವಾಗಿ ವರ್ತಕರು ಮತ್ತು ಖರೀದಿದಾರರಿಗೆ ಮಾರಾಟ ಮಾಡಿ</Text>
                </View>
              </TouchableOpacity>

              {/* Loading */}
              {marketplaceLoading && !refreshing && (
                <View style={styles.loadingBox}>
                  <ActivityIndicator size="large" color="#114B32" />
                  <Text style={styles.loadingText}>ರೈತರ ಬೆಳೆಗಳನ್ನು ಹುಡುಕಲಾಗುತ್ತಿದೆ...</Text>
                </View>
              )}

              {/* Error */}
              {marketplaceError && (
                <View style={styles.errorCard}>
                  <AlertCircle size={28} color="#B91C1C" />
                  <Text style={styles.errorCardTitle}>ಮಾಹಿತಿ ಲೋಡ್ ಮಾಡಲು ವಿಫಲವಾಗಿದೆ</Text>
                  <Text style={styles.errorCardSub}>{marketplaceError}</Text>
                </View>
              )}

              {/* Empty State */}
              {!marketplaceLoading && produceListings.length === 0 && (
                <View style={styles.emptyCard}>
                  <Store size={36} color="#9CA3AF" />
                  <Text style={styles.emptyTitle}>ಈಗ ಯಾವುದೇ ರೈತರ ಬೆಳೆ ಮಾರಾಟಕ್ಕೆ ಲಭ್ಯವಿಲ್ಲ.</Text>
                  <Text style={styles.emptySub}>ನಿಮ್ಮ ಉತ್ಪನ್ನವನ್ನು ಪಟ್ಟಿ ಮಾಡುವ ಮೊದಲ ರೈತರಾಗಿರಿ.</Text>
                  <TouchableOpacity
                    onPress={() => setCreateListingModalVisible(true)}
                    style={styles.expandRadiusBtn}
                  >
                    <Text style={styles.expandRadiusBtnText}>ನಿಮ್ಮ ಬೆಳೆ ಪಟ್ಟಿ ಮಾಡಿ</Text>
                  </TouchableOpacity>
                </View>
              )}

              {/* Listings Cards */}
              {!marketplaceLoading && (
                <View style={styles.cardsList}>
                  {produceListings.map((item) => (
                    <ProduceListingCard
                      key={item.listing.id}
                      item={item}
                      currentUserId={currentUserId}
                      isBuyer={isBuyerRole}
                      onPressOffer={(target) => {
                        setSelectedListingForOffer(target);
                        setBuyerOfferModalVisible(true);
                      }}
                      onPressViewOffers={(target) => handleViewOffersOnListing(target)}
                    />
                  ))}
                </View>
              )}
            </ScrollView>
          )}

          {/* TAB 2: MY MARKETPLACE */}
          {marketplaceSubTab === 'my_market' && (
            <View style={{ flex: 1 }}>
              {/* Secondary Tabs for My Marketplace */}
              <View style={styles.myMarketFilterBar}>
                <TouchableOpacity
                  onPress={() => setMyMarketTab('listings')}
                  style={[styles.myMarketTabBtn, myMarketTab === 'listings' && styles.myMarketTabBtnActive]}
                >
                  <Text style={[styles.myMarketTabBtnText, myMarketTab === 'listings' && styles.myMarketTabBtnTextActive]}>
                    ನನ್ನ ಪಟ್ಟಿಗಳು
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={() => setMyMarketTab('offers')}
                  style={[styles.myMarketTabBtn, myMarketTab === 'offers' && styles.myMarketTabBtnActive]}
                >
                  <Text style={[styles.myMarketTabBtnText, myMarketTab === 'offers' && styles.myMarketTabBtnTextActive]}>
                    ನನ್ನ ಆಫರ್ಗಳು
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={() => setMyMarketTab('purchases')}
                  style={[styles.myMarketTabBtn, myMarketTab === 'purchases' && styles.myMarketTabBtnActive]}
                >
                  <Text style={[styles.myMarketTabBtnText, myMarketTab === 'purchases' && styles.myMarketTabBtnTextActive]}>
                    ವಹಿವಾಟುಗಳು
                  </Text>
                </TouchableOpacity>
              </View>

              <ScrollView
                showsVerticalScrollIndicator={false}
                contentContainerStyle={styles.scrollBody}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#114B32']} />}
              >
                {/* 1. Farmer Own Listings */}
                {myMarketTab === 'listings' && (
                  <>
                    {farmerOwnListings.length === 0 ? (
                      <View style={styles.emptyCard}>
                        <Inbox size={32} color="#9CA3AF" />
                        <Text style={styles.emptyTitle}>ನೀವು ಇನ್ನೂ ಯಾವುದೇ ಬೆಳೆಯನ್ನು ಪಟ್ಟಿ ಮಾಡಿಲ್ಲ.</Text>
                        <TouchableOpacity
                          onPress={() => setCreateListingModalVisible(true)}
                          style={styles.expandRadiusBtn}
                        >
                          <Text style={styles.expandRadiusBtnText}>ನಿಮ್ಮ ಬೆಳೆ ಪಟ್ಟಿ ಮಾಡಿ</Text>
                        </TouchableOpacity>
                      </View>
                    ) : (
                      farmerOwnListings.map((item) => (
                        <ProduceListingCard
                          key={item.listing.id}
                          item={item}
                          currentUserId={currentUserId}
                          isBuyer={isBuyerRole}
                          onPressViewOffers={(target) => handleViewOffersOnListing(target)}
                        />
                      ))
                    )}
                  </>
                )}

                {/* 2. Buyer Submitted Offers */}
                {myMarketTab === 'offers' && (
                  <>
                    {buyerSubmittedOffers.length === 0 ? (
                      <View style={styles.emptyCard}>
                        <Tag size={32} color="#9CA3AF" />
                        <Text style={styles.emptyTitle}>ಇನ್ನೂ ಯಾವುದೇ ಆಫರ್ ಸಲ್ಲಿಸಿಲ್ಲ.</Text>
                      </View>
                    ) : (
                      buyerSubmittedOffers.map((item) => (
                        <View key={item.offer.id} style={styles.myOfferCard}>
                          <View style={styles.myOfferHeader}>
                            <Text style={styles.myOfferCropTitle}>{item.listing.location} ಉತ್ಪನ್ನ</Text>
                            <View
                              style={[
                                styles.statusBadge,
                                item.offer.status === 'ACCEPTED'
                                  ? styles.statusBadgeGreen
                                  : item.offer.status === 'REJECTED'
                                  ? styles.statusBadgeRed
                                  : styles.statusBadgeYellow,
                              ]}
                            >
                              <Text style={styles.statusBadgeText}>
                                {item.offer.status === 'ACCEPTED' ? 'ಸ್ವೀಕರಿಸಲಾಗಿದೆ' : item.offer.status === 'REJECTED' ? 'ತಿರಸ್ಕರಿಸಲಾಗಿದೆ' : 'ಬಾಕಿ ಇದೆ'}
                              </Text>
                            </View>
                          </View>

                          <View style={styles.myOfferBody}>
                            <Text style={styles.myOfferText}>ಆಫರ್ ಬೆಲೆ: ₹{item.offer.offered_price}</Text>
                            <Text style={styles.myOfferText}>ಪ್ರಮಾಣ: {item.offer.quantity} {item.listing.unit}</Text>
                            <Text style={styles.myOfferTotal}>
                              ಒಟ್ಟು: ₹{Number(item.offer.offered_price) * Number(item.offer.quantity)}
                            </Text>
                          </View>

                          {/* If accepted, show transaction / payment CTA */}
                          {item.offer.status === 'ACCEPTED' && (
                            <TouchableOpacity
                              activeOpacity={0.85}
                              onPress={() => {
                                setSelectedOfferForTransaction(item);
                                setTransactionModalVisible(true);
                              }}
                              style={styles.payOrderBtn}
                            >
                              <CheckCircle size={14} color="#FFFFFF" />
                              <Text style={styles.payOrderBtnText}>ಪಾವತಿ & ಸಂಪರ್ಕ ವಿವರಗಳು</Text>
                            </TouchableOpacity>
                          )}
                        </View>
                      ))
                    )}
                  </>
                )}

                {/* 3. My Transactions / Purchases */}
                {myMarketTab === 'purchases' && (
                  <>
                    {myTransactions.length === 0 ? (
                      <View style={styles.emptyCard}>
                        <Inbox size={32} color="#9CA3AF" />
                        <Text style={styles.emptyTitle}>ಯಾವುದೇ ವಹಿವಾಟುಗಳು ದಾಖಲಾಗಿಲ್ಲ.</Text>
                      </View>
                    ) : (
                      myTransactions.map((tx) => (
                        <View key={tx.id} style={styles.txCard}>
                          <View style={styles.txHeader}>
                            <Text style={styles.txCropName}>{tx.crop_name || 'ಬೆಳೆ ವ್ಯಾಪಾರ'}</Text>
                            <Text style={styles.txAmount}>₹{Number(tx.amount).toLocaleString('en-IN')}</Text>
                          </View>
                          <Text style={styles.txMeta}>
                            ಸ್ಥಿತಿ: {tx.payment_status} • {tx.order_status}
                          </Text>
                          <Text style={styles.txDate}>{new Date(tx.created_at).toLocaleDateString()}</Text>
                        </View>
                      ))
                    )}
                  </>
                )}
              </ScrollView>
            </View>
          )}
        </View>
      )}

      {/* ====================================================================== */}
      {/* MODALS                                                                 */}
      {/* ====================================================================== */}

      {/* 1. Mandi Details Modal */}
      <MandiDetailModal
        visible={detailModalVisible}
        mandi={selectedMandiForDetail}
        cropId={selectedCrop?.id || null}
        cropNameKn={selectedCrop?.name_kn || 'ಬೆಳೆ'}
        farmerId={currentUserId}
        onClose={() => setDetailModalVisible(false)}
      />

      {/* 2. Location Preset Selector Modal */}
      <LocationSelectorModal
        visible={locationModalVisible}
        selectedLocation={locationPreset}
        onSelect={(loc) => {
          setLocationPreset(loc);
          setUserCoords(null);
        }}
        onRequestGps={requestGpsLocation}
        onClose={() => setLocationModalVisible(false)}
      />

      {/* 3. Create Produce Listing Modal */}
      <CreateListingModal
        visible={createListingModalVisible}
        crops={crops}
        farmerId={currentUserId}
        defaultLocation={locationPreset.nameKn}
        onClose={() => setCreateListingModalVisible(false)}
        onSuccess={loadMarketplaceData}
      />

      {/* 4. Buyer Offer Submission Modal */}
      <BuyerOfferModal
        visible={buyerOfferModalVisible}
        listingItem={selectedListingForOffer}
        buyerId={currentUserId}
        onClose={() => setBuyerOfferModalVisible(false)}
        onSuccess={loadMarketplaceData}
      />

      {/* 5. Farmer Offer Review Modal */}
      <OfferReviewModal
        visible={offerReviewModalVisible}
        offers={selectedListingOffers}
        farmerId={currentUserId}
        onClose={() => setOfferReviewModalVisible(false)}
        onRefresh={loadMarketplaceData}
      />

      {/* 6. Transaction & Payment Modal */}
      <TransactionModal
        visible={transactionModalVisible}
        offerItem={selectedOfferForTransaction}
        buyerId={currentUserId}
        onClose={() => setTransactionModalVisible(false)}
        onSuccess={loadMarketplaceData}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  shareBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#EAF7EE',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  shareBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#114B32',
  },
  topSegmentBar: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    gap: 10,
  },
  segmentBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: '#F3F4F6',
  },
  segmentBtnActive: {
    backgroundColor: '#EAF7EE',
    borderWidth: 1.5,
    borderColor: '#114B32',
  },
  segmentBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#6B7280',
  },
  segmentBtnTextActive: {
    color: '#114B32',
    fontWeight: '800',
  },
  scrollBody: {
    padding: 12,
    paddingBottom: 40,
    gap: 12,
  },
  locationBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  locationInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flex: 1,
  },
  locationText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#111827',
  },
  changeLocBtn: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: '#F3F4F6',
  },
  changeLocText: {
    fontSize: 11,
    color: '#114B32',
    fontWeight: '700',
  },
  locWarningBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FEF3C7',
    borderWidth: 1,
    borderColor: '#FDE68A',
    borderRadius: 10,
    padding: 10,
  },
  locWarningTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#92400E',
  },
  locWarningSub: {
    fontSize: 11,
    color: '#B45309',
    marginTop: 1,
  },
  locFallbackBtn: {
    backgroundColor: '#92400E',
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderRadius: 6,
  },
  locFallbackBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  controlsBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  mandisFoundText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#111827',
  },
  sortButtonsRow: {
    flexDirection: 'row',
    gap: 6,
  },
  sortBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 6,
  },
  sortBtnActive: {
    backgroundColor: '#114B32',
    borderColor: '#114B32',
  },
  sortBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#374151',
  },
  sortBtnTextActive: {
    color: '#FFFFFF',
  },
  loadingBox: {
    padding: 40,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 13,
    color: '#6B7280',
  },
  errorCard: {
    backgroundColor: '#FEE2E2',
    borderWidth: 1,
    borderColor: '#FCA5A5',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    gap: 8,
  },
  errorCardTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#991B1B',
  },
  errorCardSub: {
    fontSize: 12,
    color: '#B91C1C',
    textAlign: 'center',
  },
  retryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#991B1B',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
    marginTop: 6,
  },
  retryBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  emptyCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    padding: 30,
    alignItems: 'center',
    gap: 10,
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#111827',
    textAlign: 'center',
  },
  emptySub: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 18,
    paddingHorizontal: 10,
  },
  expandRadiusBtn: {
    backgroundColor: '#114B32',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    marginTop: 6,
  },
  expandRadiusBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  cardsList: {
    gap: 2,
  },
  marketplaceSubNavBar: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  subTabBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  subTabBtnActive: {
    borderBottomColor: '#114B32',
  },
  subTabBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#6B7280',
  },
  subTabBtnTextActive: {
    color: '#114B32',
    fontWeight: '800',
  },
  createListingBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#114B32',
    borderRadius: 12,
    padding: 14,
    marginBottom: 4,
  },
  createListingTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  createListingSub: {
    fontSize: 11,
    color: '#A7F3D0',
    marginTop: 2,
  },
  myMarketFilterBar: {
    flexDirection: 'row',
    backgroundColor: '#F3F4F6',
    padding: 4,
    marginHorizontal: 12,
    marginTop: 8,
    borderRadius: 10,
    gap: 4,
  },
  myMarketTabBtn: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 8,
    borderRadius: 8,
  },
  myMarketTabBtnActive: {
    backgroundColor: '#FFFFFF',
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 1,
  },
  myMarketTabBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#6B7280',
  },
  myMarketTabBtnTextActive: {
    color: '#114B32',
  },
  myOfferCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    padding: 12,
    gap: 8,
  },
  myOfferHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  myOfferCropTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
  },
  myOfferBody: {
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    padding: 8,
    gap: 2,
  },
  myOfferText: {
    fontSize: 12,
    color: '#4B5563',
  },
  myOfferTotal: {
    fontSize: 14,
    fontWeight: '800',
    color: '#114B32',
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  statusBadgeGreen: {
    backgroundColor: '#DCFCE7',
  },
  statusBadgeYellow: {
    backgroundColor: '#FEF3C7',
  },
  statusBadgeRed: {
    backgroundColor: '#FEE2E2',
  },
  statusBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#111827',
  },
  payOrderBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#114B32',
    paddingVertical: 10,
    borderRadius: 8,
    marginTop: 4,
  },
  payOrderBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  txCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    padding: 12,
    gap: 4,
  },
  txHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  txCropName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
  },
  txAmount: {
    fontSize: 15,
    fontWeight: '800',
    color: '#114B32',
  },
  txMeta: {
    fontSize: 11,
    color: '#6B7280',
  },
  txDate: {
    fontSize: 10,
    color: '#9CA3AF',
  },
});