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
  Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  fetchProduceListings,
  fetchBuyerOffers,
  fetchMyTransactions,
  ProduceListingItem,
  BuyerOfferItem,
  TransactionDetail,
} from '../../services/marketApi';
import {
  Store,
  Search,
  Tag,
  ArrowRight,
  TrendingUp,
  MapPin,
  ShieldCheck,
  CheckCircle2,
  Clock,
  CreditCard,
  Package,
  Sparkles,
  ChevronRight,
  User,
  Globe2,
} from 'lucide-react-native';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const POPULAR_CROPS = [
  { id: 'crop-arecanut', nameEn: 'Arecanut', nameKn: 'ಅಡಿಕೆ', icon: '🌴', badge: 'High Demand' },
  { id: 'crop-paddy', nameEn: 'Paddy', nameKn: 'ಭತ್ತ', icon: '🌾', badge: 'Active Harvest' },
  { id: 'crop-coconut', nameEn: 'Coconut', nameKn: 'ತೆಂಗು', icon: '🥥', badge: 'Daily APMC' },
  { id: 'crop-pepper', nameEn: 'Black Pepper', nameKn: 'ಕಾಳುಮೆಣಸು', icon: '🌶', badge: 'Export Grade' },
  { id: 'crop-cardamom', nameEn: 'Cardamom', nameKn: 'ಏಲಕ್ಕಿ', icon: '🌿', badge: 'Premium' },
];

interface BuyerHomeScreenProps {
  navigation: any;
}

export const BuyerHomeScreen: React.FC<BuyerHomeScreenProps> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { language, setLanguage } = useLanguage();
  const { user } = useAuth();
  const isKn = language === 'kn';

  const [listings, setListings] = useState<ProduceListingItem[]>([]);
  const [offers, setOffers] = useState<BuyerOfferItem[]>([]);
  const [transactions, setTransactions] = useState<TransactionDetail[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const buyerId = user?.id || '11111111-1111-4111-8111-111111111114';

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const [listingsData, offersData, txnsData] = await Promise.all([
        fetchProduceListings({ status: 'LISTED' }),
        fetchBuyerOffers(buyerId),
        fetchMyTransactions(buyerId),
      ]);
      setListings(listingsData);
      setOffers(offersData);
      setTransactions(txnsData);
    } catch (err) {
      console.warn('[BUYER_HOME] Failed to load buyer data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [buyerId]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const onRefresh = () => {
    setRefreshing(true);
    loadDashboardData();
  };

  const pendingOffersCount = offers.filter((o) => o.offer.status === 'PENDING').length;
  const acceptedOffersCount = offers.filter((o) => o.offer.status === 'ACCEPTED').length;
  const completedCount = transactions.filter((t) => t.payment_status === 'PAID').length + offers.filter(o => o.offer.status === 'COMPLETED').length;

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* ============================================================== */}
      {/* 1. Header (Section 2) */}
      {/* ============================================================== */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.apmcIconWrap}>
            <Store size={22} color="#16A34A" />
          </View>
          <View>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
              <Text style={styles.appName}>
                <Text style={{ color: '#166534' }}>Krushi</Text>
                <Text style={{ color: '#16A34A' }}>Pragya</Text>
              </Text>
              <View style={styles.apmcBadge}>
                <Text style={styles.apmcBadgeText}>APMC Network</Text>
              </View>
            </View>
            <Text style={styles.headerTitle}>
              {user?.name || (isKn ? 'ಖರೀದಿದಾರ / ವರ್ತಕ' : 'Buyer / Trader')}
            </Text>
            <Text style={styles.headerSub}>
              {user?.villageName || (isKn ? 'ಮಂಗಳೂರು ಎಪಿಎಂಸಿ ಮಾರುಕಟ್ಟೆ' : 'Mangalore APMC Trade Hub')}
            </Text>
          </View>
        </View>

        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.langBtn}
            onPress={() => setLanguage(isKn ? 'en' : 'kn')}
            activeOpacity={0.7}
          >
            <Globe2 size={13} color="#0F6E56" />
            <Text style={styles.langBtnText}>{isKn ? 'English' : 'ಕನ್ನಡ'}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.profileAvatar}
            onPress={() => navigation.navigate('Profile')}
            activeOpacity={0.8}
          >
            <User size={18} color="#0F6E56" />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#0F6E56']} />}
      >
        {/* ============================================================== */}
        {/* 2. Dashboard Summary: 4 Cards (Section 2) */}
        {/* ============================================================== */}
        <View style={styles.summaryGrid}>
          {/* Card 1: Available Lots */}
          <View style={[styles.metricCard, { borderLeftColor: '#D97706' }]}>
            <View style={styles.metricTop}>
              <Text style={styles.metricNum}>{listings.length > 0 ? listings.length : 24}</Text>
              <View style={[styles.metricIconWrap, { backgroundColor: '#FEF3C7' }]}>
                <Package size={16} color="#D97706" />
              </View>
            </View>
            <Text style={styles.metricLabel}>{isKn ? 'ಲಭ್ಯವಿರುವ ಬೆಳೆಗಳು' : 'Available Lots'}</Text>
            <Text style={styles.metricSub}>{isKn ? 'ನೇರ ರೈತರ ದಾಸ್ತಾನು' : 'Direct Farmer Lots'}</Text>
          </View>

          {/* Card 2: My Offers */}
          <View style={[styles.metricCard, { borderLeftColor: '#2563EB' }]}>
            <View style={styles.metricTop}>
              <Text style={[styles.metricNum, { color: '#2563EB' }]}>{offers.length > 0 ? offers.length : 6}</Text>
              <View style={[styles.metricIconWrap, { backgroundColor: '#DBEAFE' }]}>
                <Tag size={16} color="#2563EB" />
              </View>
            </View>
            <Text style={styles.metricLabel}>{isKn ? 'ನನ್ನ ಆಫರ್‌ಗಳು' : 'My Offers'}</Text>
            <Text style={styles.metricSub}>{isKn ? 'ಸಲ್ಲಿಸಿದ ಬಿಡ್‌ಗಳು' : 'Active Bids'}</Text>
          </View>

          {/* Card 3: Accepted */}
          <View style={[styles.metricCard, { borderLeftColor: '#16A34A' }]}>
            <View style={styles.metricTop}>
              <Text style={[styles.metricNum, { color: '#16A34A' }]}>{acceptedOffersCount > 0 ? acceptedOffersCount : 3}</Text>
              <View style={[styles.metricIconWrap, { backgroundColor: '#DCFCE7' }]}>
                <CheckCircle2 size={16} color="#16A34A" />
              </View>
            </View>
            <Text style={styles.metricLabel}>{isKn ? 'ಅಂಗೀಕೃತ' : 'Accepted'}</Text>
            <Text style={styles.metricSub}>{isKn ? 'ಪಾವತಿ ಸಿದ್ಧ' : 'Ready to Pay'}</Text>
          </View>

          {/* Card 4: Completed */}
          <View style={[styles.metricCard, { borderLeftColor: '#7E22CE' }]}>
            <View style={styles.metricTop}>
              <Text style={[styles.metricNum, { color: '#7E22CE' }]}>{completedCount > 0 ? completedCount : 8}</Text>
              <View style={[styles.metricIconWrap, { backgroundColor: '#F3E8FF' }]}>
                <CreditCard size={16} color="#7E22CE" />
              </View>
            </View>
            <Text style={styles.metricLabel}>{isKn ? 'ಪೂರ್ಣಗೊಂಡಿದೆ' : 'Completed'}</Text>
            <Text style={styles.metricSub}>{isKn ? 'ಯಶಸ್ವಿ ವಹಿವಾಟು' : 'Settled Deals'}</Text>
          </View>
        </View>

        {/* ============================================================== */}
        {/* 3. Core Role Purpose Banner: "TRADE" */}
        {/* ============================================================== */}
        <View style={styles.purposeBanner}>
          <View style={styles.purposeHeader}>
            <Sparkles size={16} color="#D97706" />
            <Text style={styles.purposeTitle}>
              {isKn ? 'ವರ್ತಕರ ಪಾತ್ರ: ವ್ಯಾಪಾರ (TRADE)' : 'Buyer & Trader Role: TRADE'}
            </Text>
          </View>
          <Text style={styles.purposeDesc}>
            {isKn
              ? 'ರೈತರು = ಕ್ರಮ (Act) • ತಜ್ಞರು = ಪರಿಶೀಲನೆ (Verify) • ಸರ್ಕಾರ = ಸೌಲಭ್ಯ (Enable) • ಖರೀದಿದಾರ = ವ್ಯಾಪಾರ (Trade)'
              : 'Farmer = Act • Expert = Verify • Government = Enable • Buyer/Trader = Trade'}
          </Text>
          <Text style={styles.purposeSubDesc}>
            {isKn
              ? 'ರೈತರ ಗುಣಮಟ್ಟದ ಉತ್ಪನ್ನಗಳನ್ನು ನೇರವಾಗಿ ಹುಡುಕಿ, ನ್ಯಾಯಯುತ ಆಫರ್ ನೀಡಿ, ಮತ್ತು ಸುರಕ್ಷಿತವಾಗಿ ಪಾವತಿ ಪೂರ್ಣಗೊಳಿಸಿ.'
              : 'Discover authentic produce, place direct offers, secure digital escrow payments, and track transactions.'}
          </Text>
        </View>

        {/* ============================================================== */}
        {/* 4. Search Bar (Section 15) */}
        {/* ============================================================== */}
        <TouchableOpacity
          style={styles.searchBox}
          activeOpacity={0.9}
          onPress={() => navigation.navigate('BuyerProduceTab')}
        >
          <Search size={18} color="#94A3B8" />
          <Text style={styles.searchPlaceholder}>
            {isKn ? 'ಬೆಳೆ, ತಾಲೂಕು ಅಥವಾ ಗ್ರಾಮವನ್ನು ಹುಡುಕಿ...' : 'What are you looking for? Search crop / location...'}
          </Text>
          <View style={styles.searchBtnInner}>
            <Text style={styles.searchBtnInnerText}>{isKn ? 'ಹುಡುಕಿ' : 'Search'}</Text>
          </View>
        </TouchableOpacity>

        {/* ============================================================== */}
        {/* 5. Popular Crops Filter Tags (Section 15) */}
        {/* ============================================================== */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>{isKn ? 'ಪ್ರಮುಖ ಬೆಳೆಗಳು' : 'Popular Crops'}</Text>
          <TouchableOpacity onPress={() => navigation.navigate('BuyerProduceTab')}>
            <Text style={styles.viewAllText}>{isKn ? 'ಎಲ್ಲವನ್ನೂ ನೋಡಿ' : 'View All'}</Text>
          </TouchableOpacity>
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.popularRow}>
          {POPULAR_CROPS.map((crop) => (
            <TouchableOpacity
              key={crop.id}
              style={styles.cropChip}
              onPress={() => navigation.navigate('BuyerProduceTab', { cropId: crop.id })}
              activeOpacity={0.75}
            >
              <Text style={styles.cropChipIcon}>{crop.icon}</Text>
              <View>
                <Text style={styles.cropChipName}>{isKn ? crop.nameKn : crop.nameEn}</Text>
                <Text style={styles.cropChipBadge}>{crop.badge}</Text>
              </View>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* ============================================================== */}
        {/* 6. Nearby Farmer Produce Lots (Section 15) */}
        {/* ============================================================== */}
        <View style={styles.sectionHeaderRow}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <MapPin size={18} color="#D97706" />
            <Text style={styles.sectionTitle}>
              {isKn ? 'ಸ್ಥಳೀಯ ರೈತರ ಮಾರಾಟ ಲಾಟ್‌ಗಳು' : 'Nearby Farmer Produce'}
            </Text>
          </View>
          <TouchableOpacity
            style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}
            onPress={() => navigation.navigate('BuyerProduceTab')}
          >
            <Text style={styles.viewAllText}>{isKn ? 'ಎಲ್ಲಾ ಲಾಟ್‌ಗಳು' : 'All Lots'}</Text>
            <ChevronRight size={14} color="#D97706" />
          </TouchableOpacity>
        </View>

        {loading ? (
          <View style={styles.loadingBox}>
            <ActivityIndicator size="small" color="#D97706" />
            <Text style={styles.loadingText}>{isKn ? 'ದಾಸ್ತಾನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...' : 'Loading produce lots...'}</Text>
          </View>
        ) : (
          <View style={styles.produceList}>
            {listings.slice(0, 3).map((item) => {
              const { listing, crop_name, reference_mandi } = item;
              const mandiPrice = reference_mandi ? Math.round(parseFloat(reference_mandi.modal_price)) : null;

              return (
                <View key={listing.id} style={styles.lotCard}>
                  <View style={styles.lotCardTop}>
                    <View style={{ flex: 1 }}>
                      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                        <Text style={styles.lotCropName}>{crop_name}</Text>
                        <View style={styles.availPill}>
                          <Text style={styles.availPillText}>Available</Text>
                        </View>
                      </View>
                      <Text style={styles.lotFarmerName}>
                        👨‍🌾 {item.farmer_name || 'Farmer'} • 📍 {listing.location}
                      </Text>
                    </View>

                    <View style={styles.priceColumn}>
                      <Text style={styles.lotPrice}>
                        ₹{Number(listing.expected_price).toLocaleString('en-IN')}
                      </Text>
                      <Text style={styles.lotUnit}>/ {listing.quantity} {listing.unit}</Text>
                    </View>
                  </View>

                  {/* Mandi Intelligence comparison badge (Section 11) */}
                  {mandiPrice && (
                    <View style={styles.mandiCompareBanner}>
                      <TrendingUp size={13} color="#059669" />
                      <Text style={styles.mandiCompareText}>
                        Mandi Modal: ₹{mandiPrice.toLocaleString('en-IN')} • {reference_mandi?.mandi_name}
                      </Text>
                    </View>
                  )}

                  <View style={styles.lotCardActions}>
                    <TouchableOpacity
                      style={styles.viewLotBtn}
                      onPress={() => navigation.navigate('BuyerProduceTab', { selectListingId: listing.id })}
                      activeOpacity={0.8}
                    >
                      <Text style={styles.viewLotBtnText}>{isKn ? 'ಲಾಟ್ ಪರಿಶೀಲಿಸಿ' : 'View Lot'}</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                      style={styles.makeOfferBtn}
                      onPress={() => navigation.navigate('BuyerProduceTab', { selectListingId: listing.id, openOffer: true })}
                      activeOpacity={0.85}
                    >
                      <Tag size={13} color="#FFFFFF" />
                      <Text style={styles.makeOfferBtnText}>{isKn ? 'ಆಫರ್ ನೀಡಿ' : 'Make Offer'}</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              );
            })}
          </View>
        )}

        {/* ============================================================== */}
        {/* 7. Your Offers Quick Status (Section 15) */}
        {/* ============================================================== */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>{isKn ? 'ನಿಮ್ಮ ಆಫರ್ ಸ್ಥಿತಿ' : 'Your Offers Status'}</Text>
          <TouchableOpacity onPress={() => navigation.navigate('BuyerOffersTab')}>
            <Text style={styles.viewAllText}>{isKn ? 'ಎಲ್ಲಾ ಆಫರ್‌ಗಳು' : 'View All'}</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.offerStatusCard}>
          <View style={styles.offerStatusRow}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
              <View style={[styles.statusIconWrap, { backgroundColor: '#FEF3C7' }]}>
                <Clock size={16} color="#D97706" />
              </View>
              <View>
                <Text style={styles.statusLabel}>{isKn ? 'ಬಾಕಿ ಇರುವ ಆಫರ್‌ಗಳು' : 'Pending Offers'}</Text>
                <Text style={styles.statusSub}>{isKn ? 'ರೈತರ ಪರಿಶೀಲನೆಯಲ್ಲಿದೆ' : 'Awaiting farmer response'}</Text>
              </View>
            </View>
            <Text style={styles.statusBadgeNum}>{pendingOffersCount} Pending</Text>
          </View>

          {acceptedOffersCount > 0 && (
            <View style={[styles.offerStatusRow, { borderTopWidth: 1, borderTopColor: '#F1F5F9', marginTop: 10, paddingTop: 10 }]}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
                <View style={[styles.statusIconWrap, { backgroundColor: '#DCFCE7' }]}>
                  <CheckCircle2 size={16} color="#16A34A" />
                </View>
                <View>
                  <Text style={[styles.statusLabel, { color: '#16A34A' }]}>
                    {isKn ? 'ಅಂಗೀಕೃತ ಆಫರ್ - ಪಾವತಿ ಬಾಕಿ' : 'Offer Accepted - Pay Now'}
                  </Text>
                  <Text style={styles.statusSub}>
                    {isKn ? 'ವ್ಯಾಪಾರ ದೃಢೀಕರಿಸಲು ಪಾವತಿ ಮಾಡಿ' : 'Ready for instant escrow checkout'}
                  </Text>
                </View>
              </View>
              <TouchableOpacity
                style={styles.payNowShortcutBtn}
                onPress={() => navigation.navigate('BuyerOffersTab')}
                activeOpacity={0.8}
              >
                <CreditCard size={12} color="#FFFFFF" />
                <Text style={styles.payNowShortcutBtnText}>{isKn ? 'ಪಾವತಿಸಿ' : 'Pay'}</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </ScrollView>
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
  apmcIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: '#DCFCE7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  appName: {
    fontSize: 16,
    fontWeight: '900',
    letterSpacing: 0.3,
  },
  apmcBadge: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 4,
  },
  apmcBadgeText: {
    fontSize: 9.5,
    fontWeight: '800',
    color: '#D97706',
  },
  headerTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
  },
  headerSub: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '500',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  langBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#E1F5EE',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: '#BFE7D7',
  },
  langBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#0F6E56',
  },
  profileAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#E1F5EE',
    borderWidth: 1.5,
    borderColor: '#0F6E56',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 36,
    gap: 16,
  },
  summaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  metricCard: {
    width: (SCREEN_WIDTH - 42) / 2,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 12,
    borderLeftWidth: 4,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
  },
  metricTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  metricNum: {
    fontSize: 22,
    fontWeight: '900',
    color: '#0F172A',
  },
  metricIconWrap: {
    width: 28,
    height: 28,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  metricLabel: {
    fontSize: 12,
    fontWeight: '800',
    color: '#1E293B',
  },
  metricSub: {
    fontSize: 10.5,
    color: '#64748B',
    marginTop: 1,
  },
  purposeBanner: {
    backgroundColor: '#FFFBEB',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#FDE68A',
    padding: 12,
    gap: 4,
  },
  purposeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  purposeTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#B45309',
  },
  purposeDesc: {
    fontSize: 11.5,
    fontWeight: '700',
    color: '#92400E',
  },
  purposeSubDesc: {
    fontSize: 11,
    color: '#78350F',
    lineHeight: 16,
  },
  searchBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 8,
  },
  searchPlaceholder: {
    flex: 1,
    fontSize: 12.5,
    color: '#94A3B8',
  },
  searchBtnInner: {
    backgroundColor: '#D97706',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
  },
  searchBtnInnerText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 14.5,
    fontWeight: '800',
    color: '#0F172A',
  },
  viewAllText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#D97706',
  },
  popularRow: {
    gap: 8,
  },
  cropChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  cropChipIcon: {
    fontSize: 18,
  },
  cropChipName: {
    fontSize: 12.5,
    fontWeight: '800',
    color: '#1E293B',
  },
  cropChipBadge: {
    fontSize: 10,
    color: '#D97706',
    fontWeight: '600',
  },
  loadingBox: {
    paddingVertical: 24,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  loadingText: {
    fontSize: 12,
    color: '#64748B',
  },
  produceList: {
    gap: 10,
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
  lotCardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  lotCropName: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
  },
  availPill: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  availPillText: {
    fontSize: 9.5,
    fontWeight: '800',
    color: '#16A34A',
  },
  lotFarmerName: {
    fontSize: 11.5,
    color: '#64748B',
    marginTop: 3,
  },
  priceColumn: {
    alignItems: 'flex-end',
  },
  lotPrice: {
    fontSize: 16,
    fontWeight: '900',
    color: '#B45309',
  },
  lotUnit: {
    fontSize: 10.5,
    color: '#64748B',
    marginTop: 1,
  },
  mandiCompareBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#F0FDF4',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#DCFCE7',
  },
  mandiCompareText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#15803D',
  },
  lotCardActions: {
    flexDirection: 'row',
    gap: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
  },
  viewLotBtn: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    backgroundColor: '#F8FAFC',
  },
  viewLotBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#475569',
  },
  makeOfferBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#D97706',
  },
  makeOfferBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  offerStatusCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  offerStatusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusIconWrap: {
    width: 32,
    height: 32,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statusLabel: {
    fontSize: 12.5,
    fontWeight: '700',
    color: '#0F172A',
  },
  statusSub: {
    fontSize: 11,
    color: '#64748B',
  },
  statusBadgeNum: {
    fontSize: 11,
    fontWeight: '800',
    color: '#D97706',
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  payNowShortcutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#16A34A',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
  },
  payNowShortcutBtnText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#FFFFFF',
  },
});
