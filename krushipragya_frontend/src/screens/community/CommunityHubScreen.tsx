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
  Users,
  Camera,
  Plane,
  Tractor,
  Package,
  BellRing,
  CheckCircle2,
  Clock,
  Sparkles,
  PhoneCall,
} from 'lucide-react-native';

interface AssistedFarmer {
  id: string;
  name: string;
  crop: string;
  diagnosis: string;
  time: string;
  status: 'scanned' | 'kvk_verified';
}

const INITIAL_ASSISTED: AssistedFarmer[] = [
  {
    id: 'a1',
    name: 'Kariyappa (Elderly Farmer)',
    crop: 'Arecanut (2 Acres)',
    diagnosis: 'Koleroga / Rot (89%)',
    time: 'Today, 9:30 AM',
    status: 'kvk_verified',
  },
  {
    id: 'a2',
    name: 'Basavaraj (Feature Phone User)',
    crop: 'Paddy (1.5 Acres)',
    diagnosis: 'Blast Disease (92%)',
    time: 'Today, 11:15 AM',
    status: 'scanned',
  },
];

interface MachineryItem {
  id: string;
  name: string;
  rate: string;
  type: 'drone' | 'machinery';
  status: 'AVAILABLE' | 'IN_USE';
  bookedFarms: number;
}

const INITIAL_MACHINERY: MachineryItem[] = [
  {
    id: 'm1',
    name: '10L Agri Spraying Drone',
    rate: '₹450 / Acre',
    type: 'drone',
    status: 'IN_USE',
    bookedFarms: 3,
  },
  {
    id: 'm2',
    name: 'Kubota Mini Paddy Harvester',
    rate: '₹1,200 / Hour',
    type: 'machinery',
    status: 'AVAILABLE',
    bookedFarms: 0,
  },
];

export const CommunityHubScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const { language } = useLanguage();
  const isKn = language === 'kn';
  const [assistedList, setAssistedList] = useState(INITIAL_ASSISTED);
  const [machineryList, setMachineryList] = useState(INITIAL_MACHINERY);
  const [bulkJoined, setBulkJoined] = useState(false);

  const handleScanForFarmer = () => {
    navigation.navigate('ReportTab', { screen: 'CropSelect' });
  };

  const handleBookMachinery = (name: string, rate: string) => {
    Alert.alert(
      isKn ? 'ಯಂತ್ರೋಪಕರಣ ಬುಕಿಂಗ್ ದೃಢಪಟ್ಟಿದೆ 🚜' : 'Machinery Slot Reserved 🚜',
      isKn
        ? `${name} (${rate}) ಬುಕಿಂಗ್ ಅನ್ನು ಗ್ರಾಮದ ಪಟ್ಟಿಗೆ ಸೇರಿಸಲಾಗಿದೆ.`
        : `${name} (${rate}) scheduled for village farm cluster.`
    );
  };

  const handleBulkOrder = () => {
    setBulkJoined(true);
    Alert.alert(
      isKn ? 'ಸಗಟು ಖರೀದಿಗೆ ನೋಂದಾಯಿಸಲಾಗಿದೆ 📦' : 'Joined Village Bulk Group Buy 📦',
      isKn
        ? 'ಬೋರ್ಡೋ ಮಿಶ್ರಣದ 50 ಕೆಜಿ ಸಗಟು ಆದೇಶಕ್ಕೆ 17 ರೈತರು ಸೇರಿದ್ದಾರೆ (30% ರಿಯಾಯಿತಿ).'
        : '17th farmer added to wholesale Bordeaux mixture batch (30% discount applied).'
    );
  };

  const handleBroadcastAlert = () => {
    Alert.alert(
      isKn ? 'ಗ್ರಾಮ ಎಚ್ಚರಿಕೆ ಪ್ರಸಾರವಾಗಿದೆ 📢' : 'Village Pest Alert Broadcasted 📢',
      isKn
        ? 'ಉಜಿರೆ ಗ್ರಾಮದ ಎಲ್ಲಾ 28 ನೋಂದಾಯಿತ ರೈತರಿಗೆ ಧ್ವನಿ/SMS ಎಚ್ಚರಿಕೆ ರವಾನಿಸಲಾಗಿದೆ.'
        : 'Voice & SMS spray alert dispatched to all 28 registered farmers in Ujire.'
    );
  };

  return (
    <View style={styles.container}>
      <Header />

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Banner */}
        <View style={styles.banner}>
          <Users size={22} color="#FFFFFF" />
          <View style={{ flex: 1 }}>
            <Text style={styles.bannerTitle}>
              {isKn ? 'ಸುರೇಶ್ ಗೌಡ (ಗ್ರಾಮ ಸಂಯೋಜಕ)' : 'Suresh Gowda (Village Node / FPO)'}
            </Text>
            <Text style={styles.bannerSub}>
              {isKn ? 'ಉಜಿರೆ ಗ್ರಾಮ ಸಮುದಾಯ ಕೇಂದ್ರ • ಕೃಷಿ ಸಹಾಯವಾಣಿ' : 'Ujire Village Grassroots Center • Agri Node'}
            </Text>
          </View>
        </View>

        {/* 1-Tap Village Broadcast Alert */}
        <TouchableOpacity style={styles.alertCard} onPress={handleBroadcastAlert} activeOpacity={0.85}>
          <BellRing size={18} color="#FFFFFF" />
          <View style={{ flex: 1 }}>
            <Text style={styles.alertTitle}>
              {isKn ? 'ಗ್ರಾಮಕ್ಕೆ ತುರ್ತು ಕೀಟ ಎಚ್ಚರಿಕೆ ಕಳುಹಿಸಿ' : 'Broadcast Pest Alert to Village'}
            </Text>
            <Text style={styles.alertSub}>
              {isKn ? 'ಉಜಿರೆ ಗ್ರಾಮದ 28 ರೈತರಿಗೆ ಧ್ವನಿ & SMS ಸಂದೇಶ' : 'Send voice & SMS alert to all 28 local farms'}
            </Text>
          </View>
        </TouchableOpacity>

        {/* FEATURE 1: ASSISTED AI SCANNING FOR ELDERLY FARMERS */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            {isKn ? 'ಹಿರಿಯ ರೈತರಿಗೆ ಉಚಿತ AI ತಪಾಸಣೆ' : 'Assisted AI Scanning for Village Farmers'}
          </Text>
        </View>

        <TouchableOpacity style={styles.scanForFarmerBtn} onPress={handleScanForFarmer} activeOpacity={0.85}>
          <Camera size={18} color="#FFFFFF" strokeWidth={2.2} />
          <View style={{ flex: 1 }}>
            <Text style={styles.scanBtnTitle}>
              {isKn ? 'ನೆರೆಹೊರೆಯ ರೈತರಿಗಾಗಿ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ' : 'Scan Leaf for Neighbor Farmer'}
            </Text>
            <Text style={styles.scanBtnSub}>
              {isKn ? 'ಸ್ಮಾರ್ಟ್‌ಫೋನ್ ಇಲ್ಲದ ರೈತರಿಗೆ ರೋಗ ಪತ್ತೆ ಸಹಾಯ' : 'Help elderly farmers without smartphones diagnose crops'}
            </Text>
          </View>
          <Sparkles size={16} color="#FDE68A" />
        </TouchableOpacity>

        {/* Recent Assisted Scans List */}
        <View style={styles.cardList}>
          {assistedList.map((item) => (
            <View key={item.id} style={styles.assistedCard}>
              <View style={styles.assistedTop}>
                <View>
                  <Text style={styles.farmerName}>{item.name}</Text>
                  <Text style={styles.farmerCrop}>{item.crop} • {item.time}</Text>
                </View>
                <View style={styles.verifiedChip}>
                  <CheckCircle2 size={11} color="#166534" />
                  <Text style={styles.verifiedChipText}>
                    {item.status === 'kvk_verified' ? 'KVK Verified' : 'AI Analysed'}
                  </Text>
                </View>
              </View>
              <Text style={styles.diagnosisText}>Diagnosis: {item.diagnosis}</Text>
            </View>
          ))}
        </View>

        {/* FEATURE 2: SHARED CUSTOM HIRING CENTER (CHC) MACHINERY */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            {isKn ? 'ಬಾಡಿಗೆ ಕೃಷಿ ಯಂತ್ರೋಪಕರಣಗಳು (CHC)' : 'Custom Hiring Machinery (CHC Hub)'}
          </Text>
        </View>

        <View style={styles.cardList}>
          {machineryList.map((m) => (
            <View key={m.id} style={styles.machineryCard}>
              <View style={styles.machineryIconBox}>
                {m.type === 'drone' ? <Plane size={20} color="#16A34A" /> : <Tractor size={20} color="#2563EB" />}
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.mName}>{m.name}</Text>
                <Text style={styles.mRate}>{m.rate} • {m.status === 'IN_USE' ? `${m.bookedFarms} Farms Active` : 'Ready to Rent'}</Text>
              </View>
              <TouchableOpacity
                style={styles.bookBtn}
                onPress={() => handleBookMachinery(m.name, m.rate)}
                activeOpacity={0.85}
              >
                <Text style={styles.bookBtnText}>{isKn ? 'ಸ್ಲಾಟ್ ಬುಕ್ ಮಾಡಿ' : 'Book Slot'}</Text>
              </TouchableOpacity>
            </View>
          ))}
        </View>

        {/* FEATURE 3: VILLAGE BULK GROUP BUY (30% DISCOUNT) */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            {isKn ? 'ಗ್ರಾಮ ಸಗಟು ರಸಗೊಬ್ಬರ ಖರೀದಿ (30% ರಿಯಾಯಿತಿ)' : 'Village Bulk Chemical Group Buy (-30%)'}
          </Text>
        </View>

        <View style={styles.bulkCard}>
          <View style={styles.bulkTop}>
            <View style={styles.bulkIconBox}>
              <Package size={20} color="#D97706" />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.bulkTitle}>1% Bordeaux Mixture Batch (50 kg)</Text>
              <Text style={styles.bulkSub}>
                {bulkJoined ? '17/20 Farmers Joined • ₹120/kg (Saved ₹50/kg)' : '16/20 Farmers Joined • Wholesale Rate'}
              </Text>
            </View>
          </View>
          <TouchableOpacity
            style={[styles.bulkBtn, bulkJoined && styles.bulkBtnJoined]}
            onPress={handleBulkOrder}
            activeOpacity={0.85}
          >
            <Text style={styles.bulkBtnText}>
              {bulkJoined
                ? (isKn ? 'ಗುಂಪಿಗೆ ಸೇರಿಸಲಾಗಿದೆ (-30% ರಿಯಾಯಿತಿ) ✅' : 'Joined Batch (-30% Discount) ✅')
                : (isKn ? 'ಗುಂಪು ಖರೀದಿಗೆ ಸೇರಿ (Join Group Buy)' : 'Join Bulk Batch (Save ₹50/kg)')}
            </Text>
          </TouchableOpacity>
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
    backgroundColor: '#16A34A',
    borderRadius: BorderRadius.md,
    padding: 12,
  },
  bannerTitle: { fontSize: 14, fontWeight: '800', color: '#FFFFFF' },
  bannerSub: { fontSize: 11, color: '#DCFCE7', marginTop: 1 },
  alertCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#DC2626',
    borderRadius: BorderRadius.md,
    padding: 12,
  },
  alertTitle: { fontSize: 12, fontWeight: '800', color: '#FFFFFF' },
  alertSub: { fontSize: 10, color: 'rgba(255,255,255,0.9)', marginTop: 1 },
  sectionHeader: { marginTop: 2 },
  sectionTitle: { fontSize: 13, fontWeight: '800', color: Colors.textPrimary },
  scanForFarmerBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#0F766E',
    borderRadius: BorderRadius.md,
    padding: 12,
  },
  scanBtnTitle: { fontSize: 13, fontWeight: '800', color: '#FFFFFF' },
  scanBtnSub: { fontSize: 10, color: '#CCFBF1', marginTop: 1 },
  cardList: { gap: 8 },
  assistedCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 10,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 4,
  },
  assistedTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  farmerName: { fontSize: 12, fontWeight: '800', color: Colors.textPrimary },
  farmerCrop: { fontSize: 10, color: Colors.textSecondary, marginTop: 1 },
  verifiedChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  verifiedChipText: { fontSize: 9, fontWeight: '800', color: '#166534' },
  diagnosisText: { fontSize: 11, fontWeight: '700', color: '#DC2626' },
  machineryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 10,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  machineryIconBox: {
    width: 38,
    height: 38,
    borderRadius: BorderRadius.sm,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  mName: { fontSize: 12, fontWeight: '800', color: Colors.textPrimary },
  mRate: { fontSize: 10, color: Colors.textSecondary, marginTop: 1 },
  bookBtn: {
    backgroundColor: '#16A34A',
    paddingVertical: 7,
    paddingHorizontal: 12,
    borderRadius: BorderRadius.sm,
  },
  bookBtnText: { fontSize: 11, fontWeight: '800', color: '#FFFFFF' },
  bulkCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 10,
  },
  bulkTop: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  bulkIconBox: {
    width: 38,
    height: 38,
    borderRadius: BorderRadius.sm,
    backgroundColor: '#FEF3C7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  bulkTitle: { fontSize: 12, fontWeight: '800', color: Colors.textPrimary },
  bulkSub: { fontSize: 10, color: '#92400E', marginTop: 1 },
  bulkBtn: {
    backgroundColor: '#D97706',
    paddingVertical: 8,
    borderRadius: BorderRadius.sm,
    alignItems: 'center',
  },
  bulkBtnJoined: {
    backgroundColor: '#16A34A',
  },
  bulkBtnText: { fontSize: 11, fontWeight: '800', color: '#FFFFFF' },
});
