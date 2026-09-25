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
  ShieldAlert,
  CreditCard,
  FileCheck2,
  PhoneCall,
  Lock,
  ArrowDownLeft,
  UserCheck,
  QrCode,
  AlertOctagon,
  Sparkles,
} from 'lucide-react-native';

export const MarketScreen: React.FC<{ route: any }> = ({ route }) => {
  const { initialTab } = route?.params || { initialTab: 'market' };
  const { language } = useLanguage();
  const [activeTab, setActiveTab] = useState<'market' | 'schemes' | 'payments'>(initialTab);
  const [hasPaidSoilFee, setHasPaidSoilFee] = useState(false);

  const openUrl = (url: string) => {
    Linking.openURL(url);
  };

  const handleSimulateDigitalPayment = () => {
    Alert.alert(
      language === 'kn' ? 'ಡಿಜಿಟಲ್ ಪಾವತಿ ಗೇಟ್‌ವೇ (UPI / Escrow)' : 'Digital Payment Gateway (UPI / Escrow)',
      language === 'kn'
        ? 'ಸರ್ಕಾರಿ ಮಣ್ಣು ಪರೀಕ್ಷಾ ಶುಲ್ಕ: ₹150\nಅಧಿಕಾರಿ: ರವಿಶಂಕರ್ (ID: AGRI-DK-402)\nಗ್ರಾಮ: ಉಜಿರೆ (Ujire)\nಖಾತೆ: ಕರ್ನಾಟಕ ಕೃಷಿ ಇಲಾಖೆ (Govt of Karnataka)\n\nಡಿಜಿಟಲ್ ರಸೀದಿಯೊಂದಿಗೆ ನೇರವಾಗಿ ಜಮೆ ಮಾಡಲು ಬಯಸುವಿರಾ?'
        : 'Govt Certified Soil Test Fee: ₹150\nOfficer: Ravi Shankar (ID: AGRI-DK-402)\nVillage: Ujire\nPayee: Dept of Agriculture, Govt of Karnataka\n\nProceed to pay with immutable digital receipt?',
      [
        { text: language === 'kn' ? 'ರದ್ದುಮಾಡಿ' : 'Cancel', style: 'cancel' },
        {
          text: language === 'kn' ? '₹150 ಪಾವತಿಸಿ (UPI)' : 'Pay ₹150 (UPI)',
          onPress: () => {
            setHasPaidSoilFee(true);
            Alert.alert(
              language === 'kn' ? '✅ ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆ' : '✅ Payment Successful',
              language === 'kn'
                ? 'ಡಿಜಿಟಲ್ ರಸೀದಿ ಸಂಖ್ಯೆ: #KP-2026-9812\nಅಧಿಕಾರಿ ಕೋಡ್: AGRI-DK-402\nಖಾತೆ: ರಾಜ್ಯ ಕೃಷಿ ಖಜಾನೆ\n\nಯಾವುದೇ ನಗದು ನೀಡಬೇಕಾಗಿಲ್ಲ. ನಿಮ್ಮ ರಸೀದಿ ಆಪ್‌ನಲ್ಲಿ ಶಾಶ್ವತವಾಗಿ ದಾಖಲಾಗಿದೆ.'
                : 'Digital Receipt ID: #KP-2026-9812\nOfficer Code: AGRI-DK-402\nAccount: State Agriculture Treasury\n\nZero physical cash required. Your receipt is permanently logged in the app.'
            );
          },
        },
      ]
    );
  };

  const handleReportBribe = () => {
    Alert.alert(
      language === 'kn' ? '🚫 ಭ್ರಷ್ಟಾಚಾರ / ನಗದು ಬೇಡಿಕೆ ವರದಿ' : '🚫 Report Illegal Cash Demand',
      language === 'kn'
        ? 'ಯಾವುದೇ ಅಧಿಕಾರಿ ಅಥವಾ ಮಧ್ಯವರ್ತಿ ನಗದು ಹಣ ಕೇಳಿದರೆ:\n\n1. ಕರ್ನಾಟಕ ಲೋಕಾಯುಕ್ತ ಸಹಾಯವಾಣಿ: 1800-425-3553\n2. ಕೃಷಿ ಇಲಾಖೆ ಜಾಗೃತ ಕೋಶ: 080-22212804\n\nಅಧಿಕಾರಿ ಕೋಡ್: AGRI-DK-402\nನಿಮ್ಮ ದೂರು 100% ಗೌಪ್ಯವಾಗಿರುತ್ತದೆ.'
        : 'If any officer or agent demands physical cash:\n\n1. Karnataka Lokayukta Toll-Free: 1800-425-3553\n2. Agriculture Vigilance Cell: 080-22212804\n\nOfficer Code: AGRI-DK-402\nYour grievance is 100% confidential.',
      [{ text: language === 'kn' ? 'ಸರಿ' : 'OK' }]
    );
  };

  return (
    <View style={styles.container}>
      <Header />

      {/* Top Segmented Control with 3 Tabs */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          onPress={() => setActiveTab('market')}
          style={[styles.tabButton, activeTab === 'market' && styles.tabButtonActive]}
        >
          <TrendingUp size={15} color={activeTab === 'market' ? Colors.textWhite : Colors.textSecondary} />
          <Text style={[styles.tabButtonText, activeTab === 'market' && styles.tabButtonTextActive]}>
            {language === 'kn' ? 'ದರಗಳು' : 'Prices'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => setActiveTab('schemes')}
          style={[styles.tabButton, activeTab === 'schemes' && styles.tabButtonActive]}
        >
          <Landmark size={15} color={activeTab === 'schemes' ? Colors.textWhite : Colors.textSecondary} />
          <Text style={[styles.tabButtonText, activeTab === 'schemes' && styles.tabButtonTextActive]}>
            {language === 'kn' ? 'ಯೋಜನೆಗಳು' : 'Schemes'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => setActiveTab('payments')}
          style={[styles.tabButton, activeTab === 'payments' && styles.tabButtonActive]}
        >
          <CreditCard size={15} color={activeTab === 'payments' ? Colors.textWhite : Colors.textSecondary} />
          <Text style={[styles.tabButtonText, activeTab === 'payments' && styles.tabButtonTextActive]}>
            {language === 'kn' ? 'ಪಾವತಿ & ರಕ್ಷಣೆ' : 'Zero-Cash'}
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* TAB 1: MARKET PRICES */}
        {activeTab === 'market' && (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                {language === 'kn' ? 'ಮಾರುಕಟ್ಟೆ ದರಗಳ ಪಾರದರ್ಶಕತೆ' : 'Market Price Transparency'}
              </Text>
              <Text style={styles.sectionSubtitle}>
                {language === 'kn'
                  ? 'ಹೋಲಿಕೆಗಾಗಿ ಮಾತ್ರ — ಮಾರಾಟ ಮಾಡುವ ಮುನ್ನ ಪರಿಶೀಲಿಸಿ'
                  : 'Prices shown for comparison only. Verify before selling.'}
              </Text>
            </View>

            {SEED_MARKET_PRICES.map((item) => (
              <Card key={item.id} style={styles.priceCard}>
                <View style={styles.priceHeader}>
                  <Text style={styles.cropTitle}>
                    {language === 'kn' ? item.cropKn : item.crop}
                  </Text>
                  <View style={styles.sourceTag}>
                    <Text style={styles.sourceTagText}>{item.sourceType}</Text>
                  </View>
                </View>

                <View style={styles.priceRow}>
                  <Text style={styles.priceAmount}>₹{item.pricePerQuintal.toLocaleString()}</Text>
                  <Text style={styles.priceUnit}>
                    / {language === 'kn' ? 'ಕ್ವಿಂಟಾಲ್' : 'Quintal'}
                  </Text>
                </View>

                <View style={styles.sourceFooter}>
                  <Building2 size={12} color={Colors.textSecondary} />
                  <Text style={styles.sourceLabel}>{item.sourceLabel}</Text>
                  <View style={styles.timeTag}>
                    <Clock size={12} color={Colors.textMuted} />
                    <Text style={styles.timeText}>{item.recordedAt}</Text>
                  </View>
                </View>
              </Card>
            ))}

            <View style={styles.disclaimerBox}>
              <Text style={styles.disclaimerText}>
                {language === 'kn'
                  ? '⚠️ ಸೂಚನೆ: ಈ ಬೆಲೆಗಳು ಹೋಲಿಕೆಗಾಗಿ ಮಾತ್ರ. ಯಾವುದೇ ನೇರ ಖರೀದಿ/ಮಾರಾಟ ಒಪ್ಪಂದ ಮಾಡುವ ಮುನ್ನ ಮಂಡಿ ಅಥವಾ ವ್ಯಾಪಾರಿಗಳೊಂದಿಗೆ ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ.'
                  : '⚠️ Disclaimer: Prices are for information only. Confirm terms directly with mandi or buyers before transaction.'}
              </Text>
            </View>
          </>
        )}

        {/* TAB 2: GOVT SCHEMES */}
        {activeTab === 'schemes' && (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                {language === 'kn' ? 'ಕರ್ನಾಟಕ ಸರ್ಕಾರಿ ಕೃಷಿ ಯೋಜನೆಗಳು' : 'Karnataka Agriculture Schemes'}
              </Text>
              <Text style={styles.sectionSubtitle}>
                {language === 'kn' ? 'ಅಧಿಕೃತ ಇಲಾಖೆಗಳಿಂದ ಪರಿಶೀಲಿಸಿದ ಮಾಹಿತಿ' : 'Verified from official departments'}
              </Text>
            </View>

            {SEED_SCHEMES.map((scheme) => (
              <Card key={scheme.id} variant="trust" style={styles.schemeCard}>
                <Text style={styles.schemeTitle}>
                  {language === 'kn' ? scheme.nameKn : scheme.nameEn}
                </Text>
                <Text style={styles.schemeDept}>{scheme.department}</Text>

                <View style={styles.benefitBox}>
                  <CheckCircle2 size={16} color={Colors.primary} />
                  <Text style={styles.benefitText}>
                    {language === 'kn' ? scheme.benefitKn : scheme.benefitEn}
                  </Text>
                </View>

                <View style={styles.eligibilityRow}>
                  <Text style={styles.eligibilityLabel}>
                    {language === 'kn' ? 'ಅರ್ಹತೆ:' : 'Eligibility:'}
                  </Text>
                  <Text style={styles.eligibilityText}>
                    {language === 'kn' ? scheme.eligibilityKn : scheme.eligibilityEn}
                  </Text>
                </View>

                <Button
                  title={language === 'kn' ? 'ಅಧಿಕೃತ ತಾಣ ತೆರೆಯಿರಿ (Official Portal)' : 'Open Official Portal'}
                  variant="outline"
                  size="normal"
                  onPress={() => openUrl(scheme.officialSourceUrl)}
                  icon={<ExternalLink size={16} color={Colors.primary} />}
                  style={{ marginTop: Spacing.sm }}
                />
              </Card>
            ))}
          </>
        )}

        {/* TAB 3: ZERO-CASH ANTI-BRIBERY, DIGITAL VISIT PASS & PAYMENT GATEWAY */}
        {activeTab === 'payments' && (
          <>
            {/* MANDATORY ZERO-CASH ANTI-BRIBERY DISCLAIMER */}
            <Card variant="alert" style={styles.antiBriberyCard}>
              <View style={styles.antiBriberyHeader}>
                <ShieldAlert size={22} color={Colors.alertHigh} />
                <Text style={styles.antiBriberyTitle}>
                  {language === 'kn' ? '🚫 ಶೂನ್ಯ ನಗದು ನೀತಿ (Zero Cash Policy)' : '🚫 Zero Cash Anti-Bribery Policy'}
                </Text>
              </View>

              <Text style={styles.antiBriberyDesc}>
                {language === 'kn'
                  ? 'ಯಾವುದೇ ಕೃಷಿ ಅಧಿಕಾರಿ, ಸಲಹೆಗಾರ ಅಥವಾ ಮಧ್ಯವರ್ತಿಗೆ ನಗದು ಹಣ ನೀಡಬೇಡಿ. ಸರ್ಕಾರದ ಎಲ್ಲಾ ಅಧಿಕೃತ ಸೇವೆಗಳು ಮತ್ತು ಶುಲ್ಕಗಳು ಕೇವಲ ಆಪ್‌ನಲ್ಲಿ ಡಿಜಿಟಲ್ ರಸೀದಿಯೊಂದಿಗೆ ಮಾತ್ರ ದಾಖಲಾಗಬೇಕು.'
                  : 'Never pay cash to any officer or agent. All legitimate fees and subsidies must be processed digitally with an immutable in-app receipt.'}
              </Text>

              <View style={styles.disclaimerPillsRow}>
                <View style={styles.disclaimerPill}>
                  <Lock size={12} color={Colors.primaryDark} />
                  <Text style={styles.disclaimerPillText}>
                    {language === 'kn' ? '100% ಡಿಜಿಟಲ್ ಲೆಡ್ಜರ್' : '100% Digital Audit Trail'}
                  </Text>
                </View>
                <View style={styles.disclaimerPill}>
                  <FileCheck2 size={12} color={Colors.primaryDark} />
                  <Text style={styles.disclaimerPillText}>
                    {language === 'kn' ? 'ಸರ್ಕಾರಿ ಅಧಿಕೃತ ರಸೀದಿ' : 'Govt Certified Receipts'}
                  </Text>
                </View>
              </View>
            </Card>

            {/* 📍 LIVE DIGITAL FIELD VISIT PASS WITH PRE-FIXED TARIFF */}
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                {language === 'kn' ? 'ಅಧಿಕೃತ ಭೇಟಿ ಪಾಸ್ & ನಿಗದಿತ ದರ ಪಟ್ಟಿ' : 'Digital Visit Pass & Pre-Fixed Tariff'}
              </Text>
              <Text style={styles.sectionSubtitle}>
                {language === 'kn' ? 'ನಿಮ್ಮ ತೋಟಕ್ಕೆ ಭೇಟಿ ನೀಡುತ್ತಿರುವ ಅಧಿಕೃತ ಅಧಿಕಾರಿ ವಿವರ' : 'Verified government officer visiting your farm'}
              </Text>
            </View>

            <Card variant="trust" style={styles.visitPassCard}>
              {/* Officer Header */}
              <View style={styles.visitPassTop}>
                <View style={styles.officerAvatar}>
                  <UserCheck size={26} color={Colors.primary} />
                </View>
                <View style={styles.officerDetailsCol}>
                  <View style={styles.officerBadgeRow}>
                    <Text style={styles.officerName}>
                      {language === 'kn' ? 'ರವಿಶಂಕರ್ (Ravi Shankar)' : 'Ravi Shankar'}
                    </Text>
                    <View style={styles.govtBadge}>
                      <Text style={styles.govtBadgeText}>GOVT OFFICER</Text>
                    </View>
                  </View>
                  <Text style={styles.officerCodeText}>
                    {language === 'kn' ? 'ಉದ್ಯೋಗಿ ಕೋಡ್:' : 'Employee ID:'} <Text style={{ fontWeight: '800', color: Colors.primaryDark }}>AGRI-DK-402</Text>
                  </Text>
                  <Text style={styles.officerHobliText}>
                    {language === 'kn' ? 'ಉಜಿರೆ ಹೋಬಳಿ · ಕೃಷಿ ಇಲಾಖೆ' : 'Ujire Hobli · Dept of Agriculture'}
                  </Text>
                </View>
              </View>

              {/* Purpose & Pre-fixed Tariff Table */}
              <View style={styles.tariffBox}>
                <Text style={styles.tariffTitle}>
                  {language === 'kn' ? 'ಸರ್ಕಾರ ನಿಗದಿಪಡಿಸಿದ ದರ ಪಟ್ಟಿ (Pre-Fixed Tariff):' : 'Government Authorized Fee Breakdown:'}
                </Text>

                <View style={styles.tariffRow}>
                  <Text style={styles.tariffItem}>
                    🌱 {language === 'kn' ? 'ಬೆಳೆ ಪರಿಶೀಲನೆ & AI ಸಲಹೆ' : 'Crop Inspection & AI Advisory'}
                  </Text>
                  <Text style={styles.tariffPriceFree}>₹0.00 (FREE)</Text>
                </View>

                <View style={styles.tariffRow}>
                  <Text style={styles.tariffItem}>
                    🧪 {language === 'kn' ? 'ಕೆವಿಕೆ ಅಧಿಕೃತ ಮಣ್ಣು ಪರೀಕ್ಷೆ' : 'KVK Certified Soil Test'}
                  </Text>
                  <Text style={styles.tariffPriceFixed}>₹150.00</Text>
                </View>

                <View style={styles.tariffRow}>
                  <Text style={styles.tariffItem}>
                    🚗 {language === 'kn' ? 'ಅಧಿಕಾರಿ ಪ್ರಯಾಣ ಶುಲ್ಕ' : 'Travel / Visit Charges'}
                  </Text>
                  <Text style={styles.tariffPriceFree}>₹0.00 (FREE)</Text>
                </View>

                <View style={styles.tariffTotalDivider} />

                <View style={styles.tariffTotalRow}>
                  <Text style={styles.tariffTotalLabel}>
                    {language === 'kn' ? 'ರೈತರು ಪಾವತಿಸಬೇಕಾದ ಒಟ್ಟು ಮೊತ್ತ:' : 'Maximum Payable by Farmer:'}
                  </Text>
                  <Text style={styles.tariffTotalAmount}>₹150.00 ONLY</Text>
                </View>
              </View>

              {/* Payment Action or Receipt */}
              {!hasPaidSoilFee ? (
                <View style={{ gap: Spacing.xs, marginTop: Spacing.xs }}>
                  <Button
                    title={language === 'kn' ? '₹150 ಪಾವತಿಸಿ (UPI / Gateway)' : 'Pay ₹150 (In-App UPI Gateway)'}
                    onPress={handleSimulateDigitalPayment}
                    icon={<CreditCard size={18} color={Colors.textWhite} />}
                  />
                  <Text style={styles.paymentNoticeText}>
                    {language === 'kn'
                      ? '⚠️ ಅಧಿಕಾರಿಗೆ ನಗದು ನೀಡಬೇಡಿ. ಆಪ್ ಮೂಲಕ ಪಾವತಿಸಿ ರಸೀದಿ ಪಡೆಯಿರಿ.'
                      : '⚠️ Do not hand cash to officer. Pay strictly inside app.'}
                  </Text>
                </View>
              ) : (
                <View style={styles.paidReceiptBox}>
                  <CheckCircle2 size={20} color={Colors.expertVerified} />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.receiptIdText}>
                      {language === 'kn' ? '✅ ಪಾವತಿಸಲಾಗಿದೆ — ರಸೀದಿ #KP-2026-9812' : '✅ Paid — Receipt #KP-2026-9812'}
                    </Text>
                    <Text style={styles.receiptSubText}>
                      {language === 'kn' ? 'ಅಧಿಕಾರಿ ID: AGRI-DK-402 · ಖಜಾನೆ ಜಮೆ ದಾಖಲಾಗಿದೆ' : 'Officer ID: AGRI-DK-402 · Logged to Treasury'}
                    </Text>
                  </View>
                  <QrCode size={26} color={Colors.expertVerified} />
                </View>
              )}

              {/* Whistleblower Action */}
              <TouchableOpacity
                activeOpacity={0.8}
                onPress={handleReportBribe}
                style={styles.whistleblowerBtn}
              >
                <AlertOctagon size={16} color={Colors.alertHigh} />
                <Text style={styles.whistleblowerBtnText}>
                  {language === 'kn'
                    ? 'ಅಧಿಕಾರಿ ಹೆಚ್ಚು ಹಣ/ನಗದು ಕೇಳಿದರೆ ದೂರು ನೀಡಿ (Helpline)'
                    : 'Report Extra Cash Demand / Officer Grievance'}
                </Text>
              </TouchableOpacity>
            </Card>

            {/* DIRECT DBT & TRANSACTION AUDIT LEDGER */}
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                {language === 'kn' ? 'ಖಾತೆ ಜಮೆ ಮತ್ತು ಪಾವತಿ ಇತಿಹಾಸ (Audit Ledger)' : 'Direct DBT & Transaction History'}
              </Text>
            </View>

            {/* Ledger Item 1: Govt Subsidy Inflow */}
            <Card style={styles.ledgerCard}>
              <View style={styles.ledgerRow}>
                <View style={[styles.ledgerBadge, { backgroundColor: Colors.expertVerifiedBg }]}>
                  <ArrowDownLeft size={18} color={Colors.expertVerified} />
                </View>
                <View style={styles.ledgerCol}>
                  <Text style={styles.ledgerTitle}>
                    {language === 'kn' ? 'ರೈತ ಸಿರಿ - ಪೋಷಕಾಂಶ ಸಬ್ಸಿಡಿ (DBT)' : 'Raitha Siri Nutrient Subsidy (DBT)'}
                  </Text>
                  <Text style={styles.ledgerMeta}>
                    SBI A/c •••• 4321 · 18 Sep 2026
                  </Text>
                </View>
                <Text style={styles.ledgerCredit}>+₹2,500</Text>
              </View>
            </Card>

            {/* Ledger Item 2: Free Crop Advisory Inflow */}
            <Card style={styles.ledgerCard}>
              <View style={styles.ledgerRow}>
                <View style={[styles.ledgerBadge, { backgroundColor: Colors.primaryLight }]}>
                  <CheckCircle2 size={18} color={Colors.primaryDark} />
                </View>
                <View style={styles.ledgerCol}>
                  <Text style={styles.ledgerTitle}>
                    {language === 'kn' ? 'AI ಬೆಳೆ ರೋಗ ಸಲಹೆ (ICAR CPCRI)' : 'AI Crop Advisory (ICAR CPCRI)'}
                  </Text>
                  <Text style={styles.ledgerMeta}>
                    {language === 'kn' ? '100% ಉಚಿತ ಸರ್ಕಾರಿ ಸೇವೆ' : '100% Free Public Service'}
                  </Text>
                </View>
                <Text style={styles.ledgerFree}>₹0 (FREE)</Text>
              </View>
            </Card>
          </>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  tabBar: {
    flexDirection: 'row',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    gap: 6,
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: Spacing.sm + 2,
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  tabButtonActive: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },
  tabButtonText: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.textSecondary,
    fontSize: 12,
  },
  tabButtonTextActive: {
    color: Colors.textWhite,
  },
  scrollContent: {
    padding: Spacing.lg,
    paddingBottom: Spacing.xxxl,
    gap: Spacing.sm,
  },
  sectionHeader: {
    marginBottom: Spacing.xs,
    marginTop: Spacing.xs,
  },
  sectionTitle: {
    ...Typography.title2,
    color: Colors.textPrimary,
    fontWeight: '800',
  },
  sectionSubtitle: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  priceCard: {
    padding: Spacing.md,
  },
  priceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cropTitle: {
    ...Typography.title2,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  sourceTag: {
    backgroundColor: Colors.surfaceSubtle,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  sourceTagText: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.textSecondary,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: Spacing.xs,
    marginVertical: Spacing.xs,
  },
  priceAmount: {
    ...Typography.display,
    color: Colors.primaryDark,
    fontWeight: '800',
  },
  priceUnit: {
    ...Typography.caption,
    color: Colors.textSecondary,
  },
  sourceFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: Spacing.xs,
    paddingTop: Spacing.xs,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  sourceLabel: {
    ...Typography.caption,
    color: Colors.textSecondary,
    flex: 1,
  },
  timeTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  timeText: {
    ...Typography.caption,
    color: Colors.textMuted,
  },
  disclaimerBox: {
    backgroundColor: Colors.surfaceSubtle,
    padding: Spacing.sm,
    borderRadius: BorderRadius.md,
    marginTop: Spacing.sm,
  },
  disclaimerText: {
    ...Typography.caption,
    color: Colors.textSecondary,
    lineHeight: 16,
  },
  schemeCard: {
    padding: Spacing.md,
    gap: Spacing.xs,
  },
  schemeTitle: {
    ...Typography.title2,
    color: Colors.textPrimary,
    fontWeight: '800',
  },
  schemeDept: {
    ...Typography.caption,
    color: Colors.textMuted,
  },
  benefitBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: Colors.primaryLight,
    padding: Spacing.xs + 2,
    borderRadius: BorderRadius.sm,
    marginVertical: 4,
  },
  benefitText: {
    ...Typography.label,
    color: Colors.primaryDark,
    flex: 1,
  },
  eligibilityRow: {
    marginVertical: 2,
  },
  eligibilityLabel: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.textSecondary,
  },
  eligibilityText: {
    ...Typography.caption,
    color: Colors.textPrimary,
  },
  antiBriberyCard: {
    backgroundColor: '#FFF7ED',
    borderColor: '#FDBA74',
    borderLeftWidth: 4,
    borderLeftColor: Colors.alertHigh,
    padding: Spacing.md,
    gap: Spacing.xs,
  },
  antiBriberyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  antiBriberyTitle: {
    ...Typography.title2,
    fontSize: 16,
    fontWeight: '800',
    color: Colors.alertHigh,
  },
  antiBriberyDesc: {
    ...Typography.bodyLarge,
    fontSize: 13,
    lineHeight: 19,
    color: Colors.textPrimary,
    fontWeight: '600',
    marginTop: 2,
  },
  disclaimerPillsRow: {
    flexDirection: 'row',
    gap: Spacing.xs,
    marginTop: 4,
  },
  disclaimerPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FED7AA',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: BorderRadius.full,
  },
  disclaimerPillText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.primaryDark,
  },
  visitPassCard: {
    padding: Spacing.md,
    backgroundColor: Colors.surface,
    gap: Spacing.sm,
  },
  visitPassTop: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
  },
  officerAvatar: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: Colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: '#BFE7D7',
  },
  officerDetailsCol: {
    flex: 1,
    gap: 2,
  },
  officerBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  officerName: {
    ...Typography.bodyLarge,
    fontWeight: '800',
    color: Colors.textPrimary,
    fontSize: 15,
  },
  govtBadge: {
    backgroundColor: Colors.expertVerifiedBg,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  govtBadgeText: {
    fontSize: 9,
    fontWeight: '900',
    color: Colors.expertVerified,
  },
  officerCodeText: {
    ...Typography.caption,
    color: Colors.textSecondary,
    fontSize: 12,
  },
  officerHobliText: {
    ...Typography.caption,
    fontSize: 11,
    color: Colors.textMuted,
  },
  tariffBox: {
    backgroundColor: Colors.surfaceSubtle,
    padding: Spacing.sm + 2,
    borderRadius: BorderRadius.md,
    gap: 6,
    marginVertical: 2,
  },
  tariffTitle: {
    ...Typography.caption,
    fontWeight: '800',
    color: Colors.textSecondary,
    marginBottom: 2,
  },
  tariffRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  tariffItem: {
    ...Typography.caption,
    color: Colors.textPrimary,
    fontWeight: '600',
    fontSize: 12,
  },
  tariffPriceFree: {
    ...Typography.caption,
    fontWeight: '800',
    color: Colors.expertVerified,
    fontSize: 12,
  },
  tariffPriceFixed: {
    ...Typography.bodyLarge,
    fontWeight: '800',
    color: Colors.primaryDark,
    fontSize: 13,
  },
  tariffTotalDivider: {
    height: 1,
    backgroundColor: Colors.border,
    marginVertical: 2,
  },
  tariffTotalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 2,
  },
  tariffTotalLabel: {
    ...Typography.caption,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  tariffTotalAmount: {
    ...Typography.title2,
    fontSize: 16,
    fontWeight: '900',
    color: Colors.alertHigh,
  },
  paymentNoticeText: {
    ...Typography.caption,
    fontSize: 11,
    color: Colors.textMuted,
    textAlign: 'center',
    marginTop: 2,
  },
  paidReceiptBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    backgroundColor: Colors.expertVerifiedBg,
    padding: Spacing.sm + 2,
    borderRadius: BorderRadius.md,
    borderWidth: 1.5,
    borderColor: '#A7F3D0',
    marginTop: Spacing.xs,
  },
  receiptIdText: {
    ...Typography.caption,
    fontWeight: '800',
    color: Colors.expertVerified,
  },
  receiptSubText: {
    ...Typography.caption,
    fontSize: 11,
    color: Colors.textSecondary,
    marginTop: 1,
  },
  whistleblowerBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#FEE2E2',
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: '#FECDD3',
    marginTop: Spacing.xs,
  },
  whistleblowerBtnText: {
    ...Typography.caption,
    fontWeight: '800',
    color: Colors.alertHigh,
    fontSize: 11,
  },
  ledgerCard: {
    padding: Spacing.md,
    backgroundColor: Colors.surface,
    marginBottom: Spacing.xs,
  },
  ledgerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
  },
  ledgerBadge: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ledgerCol: {
    flex: 1,
  },
  ledgerTitle: {
    ...Typography.bodyLarge,
    fontSize: 14,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  ledgerMeta: {
    ...Typography.caption,
    fontSize: 11,
    color: Colors.textSecondary,
    marginTop: 1,
  },
  ledgerCredit: {
    ...Typography.title2,
    fontSize: 16,
    fontWeight: '900',
    color: Colors.expertVerified,
  },
  ledgerFree: {
    ...Typography.label,
    fontSize: 12,
    fontWeight: '800',
    color: Colors.primaryDark,
  },
});
