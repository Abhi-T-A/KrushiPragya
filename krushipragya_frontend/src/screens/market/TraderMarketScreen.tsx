import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Header } from '../../components/common/Header';
import { useLanguage } from '../../context/LanguageContext';
import { Colors, Spacing, BorderRadius } from '../../constants/theme';
import {
  Store,
  TrendingUp,
  MapPin,
  CheckCircle2,
  ShieldCheck,
} from 'lucide-react-native';

const INITIAL_LISTINGS = [
  { id: 'l1', farmer: 'Mallikarjuna G.', crop: 'Paddy Jyothi', qty: '40 Qtl', price: '₹2,400/Qtl', village: 'Ujire', certified: true, status: 'OPEN' },
  { id: 'l2', farmer: 'Anantha P.', crop: 'Arecanut Rashi', qty: '15 Qtl', price: '₹48,500/Qtl', village: 'Thirthahalli', certified: true, status: 'OPEN' },
];

export const TraderMarketScreen: React.FC = () => {
  const { language } = useLanguage();
  const isKn = language === 'kn';
  const [listings, setListings] = useState(INITIAL_LISTINGS);

  const handleBid = (id: string, farmer: string, crop: string) => {
    setListings(prev => prev.map(l => l.id === id ? { ...l, status: 'BID_PLACED' } : l));
    Alert.alert(
      isKn ? 'ಖರೀದಿ ಬಿಡ್ ಕಳುಹಿಸಲಾಗಿದೆ 📦' : 'Procurement Bid Placed 📦',
      isKn ? `${farmer} ಅವರ ${crop} ಖರೀದಿಗೆ ನಿಮ್ಮ ಬಿಡ್ ತಲುಪಿದೆ.` : `Your purchase offer sent to ${farmer}.`
    );
  };

  return (
    <View style={styles.container}>
      <Header />

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Banner */}
        <View style={styles.banner}>
          <Store size={22} color="#FFFFFF" />
          <View style={{ flex: 1 }}>
            <Text style={styles.bannerTitle}>{isKn ? 'ರಾಜೇಶ್ ಸೇಠ್ (APMC ವರ್ತಕ)' : 'Rajesh Seth (APMC Merchant)'}</Text>
            <Text style={styles.bannerSub}>{isKn ? 'ಮಂಗಳೂರು APMC • ನೇರ ಖರೀದಿ' : 'Mangalore APMC Trade Hub'}</Text>
          </View>
        </View>

        <Text style={styles.sectionTitle}>{isKn ? 'ದೃಢೀಕೃತ ಬೆಳೆ ಖರೀದಿ ಲಾಟ್‌ಗಳು' : 'Verified Disease-Free Lots'}</Text>

        <View style={styles.list}>
          {listings.map((item) => (
            <View key={item.id} style={[styles.card, item.status === 'BID_PLACED' && styles.cardBid]}>
              <View style={styles.cardTop}>
                <View>
                  <Text style={styles.cropText}>{item.crop} ({item.qty})</Text>
                  <Text style={styles.farmerText}>{item.farmer} • {item.village}</Text>
                </View>
                <Text style={styles.priceText}>{item.price}</Text>
              </View>

              <View style={styles.certBadge}>
                <ShieldCheck size={12} color="#166534" />
                <Text style={styles.certText}>{isKn ? 'ICAR ರೋಗ-ಮುಕ್ತ ಪ್ರಮಾಣಪತ್ರ' : 'KVK Disease-Free Certified'}</Text>
              </View>

              {item.status === 'OPEN' ? (
                <TouchableOpacity
                  style={styles.bidBtn}
                  onPress={() => handleBid(item.id, item.farmer, item.crop)}
                  activeOpacity={0.85}
                >
                  <Text style={styles.bidBtnText}>{isKn ? 'ಖರೀದಿ ಬಿಡ್ ಸಲ್ಲಿಸಿ' : 'Place Purchase Bid'}</Text>
                </TouchableOpacity>
              ) : (
                <View style={styles.bidSuccess}>
                  <CheckCircle2 size={13} color="#166534" />
                  <Text style={styles.bidSuccessText}>{isKn ? 'ಬಿಡ್ ಸಲ್ಲಿಸಲಾಗಿದೆ' : 'Bid Placed & Locked'}</Text>
                </View>
              )}
            </View>
          ))}
        </View>
      </ScrollView>
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
    padding: 12,
  },
  bannerTitle: { fontSize: 14, fontWeight: '800', color: '#FFFFFF' },
  bannerSub: { fontSize: 11, color: '#FEF3C7' },
  sectionTitle: { fontSize: 13, fontWeight: '800', color: Colors.textPrimary },
  list: { gap: 10 },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 8,
  },
  cardBid: { backgroundColor: '#F0FDF4', borderColor: '#BBF7D0' },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cropText: { fontSize: 13, fontWeight: '800', color: Colors.textPrimary },
  farmerText: { fontSize: 11, color: Colors.textSecondary, marginTop: 1 },
  priceText: { fontSize: 13, fontWeight: '800', color: '#D97706' },
  certBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#DCFCE7',
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: BorderRadius.sm,
    alignSelf: 'flex-start',
  },
  certText: { fontSize: 10, fontWeight: '700', color: '#166534' },
  bidBtn: {
    backgroundColor: '#D97706',
    paddingVertical: 9,
    borderRadius: BorderRadius.sm,
    alignItems: 'center',
  },
  bidBtnText: { fontSize: 11, fontWeight: '800', color: '#FFFFFF' },
  bidSuccess: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    backgroundColor: '#DCFCE7',
    paddingVertical: 6,
    borderRadius: BorderRadius.sm,
  },
  bidSuccessText: { fontSize: 11, fontWeight: '700', color: '#166534' },
});
