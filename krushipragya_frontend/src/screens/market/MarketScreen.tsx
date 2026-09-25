import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Linking,
  Alert,
} from 'react-native';
import { useLanguage } from '../../context/LanguageContext';
import { Header } from '../../components/common/Header';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { SEED_MARKET_PRICES, SEED_SCHEMES } from '../../constants/seedData';
import {
  TrendingUp,
  Landmark,
  ExternalLink,
  Clock,
  Building2,
  CheckCircle2,
  CreditCard,
  PhoneCall,
  ShieldCheck,
  Store,
  Sparkles,
} from 'lucide-react-native';

export const MarketScreen: React.FC<{ route: any }> = ({ route }) => {
  const { initialTab } = route?.params || { initialTab: 'market' };
  const { language } = useLanguage();
  const [activeTab, setActiveTab] = useState<'market' | 'schemes' | 'payments'>(initialTab);
  const [hasPaidSoilFee, setHasPaidSoilFee] = useState(false);

  const isKn = language === 'kn';

  const openUrl = (url: string) => {
    Linking.openURL(url);
  };

  const handleSimulateDigitalPayment = () => {
    Alert.alert(
      isKn ? 'ಡಿಜಿಟಲ್ ಪಾವತಿ ಗೇಟ್‌ವೇ (UPI / DBT)' : 'Digital Payment Gateway (UPI / DBT)',
      isKn
        ? 'ಸರ್ಕಾರಿ ಪ್ರಮಾಣೀಕೃತ ಮಣ್ಣು ಪರೀಕ್ಷೆ ಶುಲ್ಕ: ₹150\nಅಧಿಕಾರಿ: ರವಿಶಂಕರ್ (ID: AGRI-DK-402)\nಗ್ರಾಮ: ಉಜಿರೆ\nಸ್ವೀಕೃತಿದಾರರು: ಕೃಷಿ ಇಲಾಖೆ, ಕರ್ನಾಟಕ ಸರ್ಕಾರ\n\nಡಿಜಿಟಲ್ ರಶೀದಿಯೊಂದಿಗೆ ಪಾವತಿಸಲು ಮುಂದುವರಿಯಿರಿ?'
        : 'Govt Certified Soil Test Fee: ₹150\nOfficer: Ravi Shankar (ID: AGRI-DK-402)\nVillage: Ujire\nPayee: Dept of Agriculture, Govt of Karnataka\n\nProceed to pay with immutable digital receipt?',
      [
        { text: isKn ? 'ರದ್ದುಮಾಡಿ' : 'Cancel', style: 'cancel' },
        {
          text: isKn ? '₹150 ಪಾವತಿಸಿ (UPI)' : 'Pay ₹150 (UPI)',
          onPress: () => {
            setHasPaidSoilFee(true);
            Alert.alert(
              isKn ? 'ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆ ✅' : 'Payment Successful ✅',
              isKn
                ? 'ಡಿಜಿಟಲ್ ರಶೀದಿ ಸಂಖ್ಯೆ: #KP-2026-9812\nಅಧಿಕಾರಿ ಕೋಡ್: AGRI-DK-402\nಖಾತೆ: ರಾಜ್ಯ ಕೃಷಿ ಖಜಾನೆ\n\nಯಾವುದೇ ನಗದು ಅಗತ್ಯವಿಲ್ಲ. ನಿಮ್ಮ ರಶೀದಿಯನ್ನು ಖಾತೆಗೆ ದಾಖಲಿಸಲಾಗಿದೆ.'
                : 'Digital Receipt ID: #KP-2026-9812\nOfficer Code: AGRI-DK-402\nAccount: State Agriculture Treasury\n\nZero physical cash required. Your receipt is permanently logged.'
            );
          },
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      <Header
        title={isKn ? 'ಮಾರುಕಟ್ಟೆ & ಯೋಜನೆಗಳು' : 'Market & Schemes'}
      />

      {/* 3 Top Segment Tabs */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          activeOpacity={0.8}
          onPress={() => setActiveTab('market')}
          style={[styles.tabButton, activeTab === 'market' && styles.activeTabButton]}
        >
          <TrendingUp size={16} color={activeTab === 'market' ? '#FFFFFF' : '#64748B'} />
          <Text style={[styles.tabButtonText, activeTab === 'market' && styles.activeTabText]}>
            {isKn ? 'ಎಪಿಎಂಸಿ ದರಗಳು' : 'APMC Prices'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          activeOpacity={0.8}
          onPress={() => setActiveTab('schemes')}
          style={[styles.tabButton, activeTab === 'schemes' && styles.activeTabButton]}
        >
          <Landmark size={16} color={activeTab === 'schemes' ? '#FFFFFF' : '#64748B'} />
          <Text style={[styles.tabButtonText, activeTab === 'schemes' && styles.activeTabText]}>
            {isKn ? 'ಸರ್ಕಾರಿ ಸಬ್ಸಿಡಿ' : 'Govt Schemes'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          activeOpacity={0.8}
          onPress={() => setActiveTab('payments')}
          style={[styles.tabButton, activeTab === 'payments' && styles.activeTabButton]}
        >
          <CreditCard size={16} color={activeTab === 'payments' ? '#FFFFFF' : '#64748B'} />
          <Text style={[styles.tabButtonText, activeTab === 'payments' && styles.activeTabText]}>
            {isKn ? 'ಡಿಜಿಟಲ್ ರಶೀದಿ' : 'Govt Pay'}
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* TAB 1: APMC MARKET PRICES */}
        {activeTab === 'market' && (
          <View style={styles.tabContent}>
            <View style={styles.marketBanner}>
              <Sparkles size={16} color="#D97706" />
              <Text style={styles.marketBannerText}>
                {isKn
                  ? 'ದಕ್ಷಿಣ ಕನ್ನಡ ಮತ್ತು ಶಿವಮೊಗ್ಗ ಎಪಿಎಂಸಿ ಮಾರುಕಟ್ಟೆಗಳ ಇಂದಿನ ಅಧಿಕೃತ ದರಗಳು'
                  : 'Live daily APMC benchmark prices from Dakshina Kannada & Shivamogga mandis'}
              </Text>
            </View>

            {SEED_MARKET_PRICES.map((price) => (
              <Card key={price.id} variant="trust" style={styles.priceCard}>
                <View style={styles.priceCardRow}>
                  <View style={styles.cropInfoCol}>
                    <Text style={styles.cropName}>
                      {isKn ? price.cropKn : price.crop}
                    </Text>
                    <View style={styles.sourceTag}>
                      <Building2 size={12} color="#2563EB" />
                      <Text style={styles.sourceTagText}>{price.sourceLabel}</Text>
                    </View>
                  </View>

                  <View style={styles.priceCol}>
                    <Text style={styles.priceValue}>
                      ₹{price.pricePerQuintal.toLocaleString()}
                    </Text>
                    <Text style={styles.priceUnit}>
                      / {isKn ? 'ಕ್ವಿಂಟಾಲ್' : 'Quintal'}
                    </Text>
                  </View>
                </View>

                <View style={styles.priceFooterRow}>
                  <View style={styles.timeTag}>
                    <Clock size={11} color="#64748B" />
                    <Text style={styles.timeTagText}>{price.recordedAt}</Text>
                  </View>
                  <View style={styles.verifiedTag}>
                    <ShieldCheck size={12} color="#15803D" />
                    <Text style={styles.verifiedTagText}>
                      {isKn ? 'ಎಪಿಎಂಸಿ ಪರಿಶೀಲಿತ' : 'APMC Verified'}
                    </Text>
                  </View>
                </View>
              </Card>
            ))}
          </View>
        )}

        {/* TAB 2: GOVT SCHEMES */}
        {activeTab === 'schemes' && (
          <View style={styles.tabContent}>
            {SEED_SCHEMES.map((scheme) => (
              <Card key={scheme.id} variant="trust" style={styles.schemeCard}>
                <View style={styles.schemeHeader}>
                  <View style={styles.schemeBadge}>
                    <Landmark size={14} color="#7E22CE" />
                    <Text style={styles.schemeBadgeText}>{scheme.department}</Text>
                  </View>
                  <Text style={styles.cropTag}>{scheme.crop}</Text>
                </View>

                <Text style={styles.schemeTitle}>
                  {isKn ? scheme.nameKn : scheme.nameEn}
                </Text>

                {/* Eligibility Box */}
                <View style={styles.schemeInfoBox}>
                  <Text style={styles.schemeLabel}>
                    {isKn ? 'ಅರ್ಹತಾ ಮಾನದಂಡ:' : 'Eligibility:'}
                  </Text>
                  <Text style={styles.schemeText}>
                    {isKn ? scheme.eligibilityKn : scheme.eligibilityEn}
                  </Text>
                </View>

                {/* Benefit Box */}
                <View style={[styles.schemeInfoBox, { backgroundColor: '#F0FDF4', borderColor: '#BBF7D0' }]}>
                  <Text style={[styles.schemeLabel, { color: '#15803D' }]}>
                    {isKn ? 'ಲಭ್ಯವಿರುವ ಸಹಾಯಧನ:' : 'Direct Benefit:'}
                  </Text>
                  <Text style={[styles.schemeText, { color: '#166534', fontWeight: '700' }]}>
                    {isKn ? scheme.benefitKn : scheme.benefitEn}
                  </Text>
                </View>

                {/* Apply Button */}
                <TouchableOpacity
                  activeOpacity={0.85}
                  onPress={() => openUrl(scheme.officialSourceUrl)}
                  style={styles.applyButton}
                >
                  <Text style={styles.applyBtnText}>
                    {isKn ? 'ಅಧಿಕೃತ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ' : 'Apply on Official Govt Portal'}
                  </Text>
                  <ExternalLink size={14} color="#FFFFFF" />
                </TouchableOpacity>
              </Card>
            ))}
          </View>
        )}

        {/* TAB 3: DIGITAL PAYMENTS & ESCROW */}
        {activeTab === 'payments' && (
          <View style={styles.tabContent}>
            <View style={styles.paymentHeroCard}>
              <View style={styles.paymentIconBox}>
                <ShieldCheck size={28} color="#15803D" />
              </View>
              <Text style={styles.paymentHeroTitle}>
                {isKn ? 'ಭ್ರಷ್ಟಾಚಾರ ಮುಕ್ತ ಡಿಜಿಟಲ್ ಕೃಷಿ ಸೇವೆಗಳು' : 'Transparent Direct Govt Payments'}
              </Text>
              <Text style={styles.paymentHeroSub}>
                {isKn
                  ? 'ಯಾವುದೇ ನಗದು ಮಧ್ಯವರ್ತಿಗಳಿಲ್ಲದೆ ಅಧಿಕೃತ ಸರ್ಕಾರಿ ಶುಲ್ಕಗಳನ್ನು ನೇರವಾಗಿ ಪಾವತಿಸಿ'
                  : 'Zero cash, zero middlemen. Pay verified government fees directly via digital escrow.'}
              </Text>

              {hasPaidSoilFee ? (
                <View style={styles.paidSuccessCard}>
                  <CheckCircle2 size={20} color="#16A34A" />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.paidSuccessTitle}>
                      {isKn ? 'ಮಣ್ಣು ಪರೀಕ್ಷಾ ರಶೀದಿ ಸಕ್ರಿಯವಾಗಿದೆ' : 'Soil Test Receipt Active'}
                    </Text>
                    <Text style={styles.paidSuccessSub}>
                      #KP-2026-9812 • ₹150 • {isKn ? 'ಸರ್ಕಾರಿ ಖಜಾನೆ' : 'State Treasury'}
                    </Text>
                  </View>
                </View>
              ) : (
                <TouchableOpacity
                  activeOpacity={0.85}
                  onPress={handleSimulateDigitalPayment}
                  style={styles.payNowBtn}
                >
                  <CreditCard size={16} color="#FFFFFF" />
                  <Text style={styles.payNowBtnText}>
                    {isKn ? 'ಮಣ್ಣು ಪರೀಕ್ಷಾ ಶುಲ್ಕ ₹150 ಪಾವತಿಸಿ' : 'Pay Soil Test Fee ₹150 (Demo)'}
                  </Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: Spacing.md,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
    gap: 8,
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#F1F5F9',
  },
  activeTabButton: {
    backgroundColor: Colors.primary,
  },
  tabButtonText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#64748B',
  },
  activeTabText: {
    color: '#FFFFFF',
  },
  scrollContent: {
    padding: Spacing.md,
    paddingBottom: 40,
  },
  tabContent: {
    gap: Spacing.md,
  },
  marketBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FEF3C7',
    borderWidth: 1,
    borderColor: '#FDE68A',
    borderRadius: 10,
    padding: 12,
  },
  marketBannerText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#92400E',
    flex: 1,
  },
  priceCard: {
    gap: 10,
  },
  priceCardRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cropInfoCol: {
    flex: 1,
  },
  cropName: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  sourceTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 3,
  },
  sourceTagText: {
    fontSize: 12,
    color: '#2563EB',
    fontWeight: '600',
  },
  priceCol: {
    alignItems: 'flex-end',
  },
  priceValue: {
    fontSize: 20,
    fontWeight: '800',
    color: '#D97706',
  },
  priceUnit: {
    fontSize: 11,
    color: '#64748B',
  },
  priceFooterRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    paddingTop: 8,
  },
  timeTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  timeTagText: {
    fontSize: 11,
    color: '#94A3B8',
  },
  verifiedTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  verifiedTagText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#15803D',
  },
  schemeCard: {
    gap: 10,
  },
  schemeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  schemeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#F3E8FF',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  schemeBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#7E22CE',
  },
  cropTag: {
    fontSize: 12,
    fontWeight: '700',
    color: '#64748B',
  },
  schemeTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0F172A',
  },
  schemeInfoBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 10,
    gap: 2,
  },
  schemeLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#64748B',
    textTransform: 'uppercase',
  },
  schemeText: {
    fontSize: 13,
    color: '#334155',
    lineHeight: 18,
  },
  applyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.primary,
    paddingVertical: 10,
    borderRadius: 8,
  },
  applyBtnText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  paymentHeroCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 20,
    alignItems: 'center',
    gap: 10,
    marginTop: 10,
  },
  paymentIconBox: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#DCFCE7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  paymentHeroTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0F172A',
    textAlign: 'center',
  },
  paymentHeroSub: {
    fontSize: 13,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 19,
  },
  payNowBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#16A34A',
    paddingHorizontal: 18,
    paddingVertical: 12,
    borderRadius: 10,
    marginTop: 8,
  },
  payNowBtnText: {
    fontSize: 14,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  paidSuccessCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#F0FDF4',
    borderWidth: 1.5,
    borderColor: '#86EFAC',
    borderRadius: 10,
    padding: 14,
    width: '100%',
    marginTop: 8,
  },
  paidSuccessTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#15803D',
  },
  paidSuccessSub: {
    fontSize: 12,
    color: '#166534',
    marginTop: 2,
  },
});