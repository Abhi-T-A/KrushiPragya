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
  Microscope,
  CheckCircle2,
  Clock,
  MapPin,
  ShieldCheck,
  FileCheck,
} from 'lucide-react-native';

const INITIAL_QUEUE = [
  {
    id: 'rep-01',
    farmer: 'Mallikarjuna G.',
    crop: 'Paddy',
    disease: 'Blast Disease (94%)',
    remedy: 'Tricyclazole 75% WP (0.6g/L)',
    village: 'Ujire',
    feePaid: true,
    status: 'pending',
  },
  {
    id: 'rep-02',
    farmer: 'Shankar Bhat',
    crop: 'Arecanut',
    disease: 'Koleroga / Rot (89%)',
    remedy: '1% Bordeaux Mixture',
    village: 'Thirthahalli',
    feePaid: true,
    status: 'pending',
  },
];

export const ExpertQueueScreen: React.FC = () => {
  const { language } = useLanguage();
  const isKn = language === 'kn';
  const [queue, setQueue] = useState(INITIAL_QUEUE);

  const handleVerify = (id: string, farmer: string) => {
    setQueue((prev) => prev.map((item) => (item.id === id ? { ...item, status: 'verified' } : item)));
    Alert.alert(
      isKn ? 'ದೃಢೀಕರಣ ಮುಗಿದಿದೆ ✅' : 'Prescription Signed ✅',
      isKn ? `${farmer} ಅವರಿಗೆ ಅಧಿಕೃತ ಶಿಫಾರಸು ಕಳುಹಿಸಲಾಗಿದೆ.` : `Official remedy issued for ${farmer}.`
    );
  };

  return (
    <View style={styles.container}>
      <Header />

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Compact Header */}
        <View style={styles.topCard}>
          <View style={styles.iconBox}>
            <Microscope size={20} color="#FFFFFF" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.topTitle}>{isKn ? 'ಡಾ. ರಮೇಶ್ (ಕೃಷಿ ವಿಜ್ಞಾನಿ)' : 'Dr. Ramesh K (Agri Expert)'}</Text>
            <Text style={styles.topSub}>{isKn ? 'ICAR - KVK ಬ್ರಹ್ಮಾವರ' : 'ICAR - KVK Brahmavar'}</Text>
          </View>
          <View style={styles.counterBadge}>
            <Text style={styles.counterText}>{queue.filter(q => q.status === 'pending').length} Pending</Text>
          </View>
        </View>

        {/* Inbound Cases List */}
        <Text style={styles.sectionTitle}>{isKn ? 'ತಪಾಸಣಾ ವಿನಂತಿಗಳು (ಶುಲ್ಕ ಪಾವತಿಸಲಾಗಿದೆ)' : 'Paid Inbound Cases (₹120 Direct KVK)'}</Text>

        <View style={styles.list}>
          {queue.map((item) => (
            <View key={item.id} style={[styles.card, item.status === 'verified' && styles.cardVerified]}>
              <View style={styles.cardTop}>
                <View>
                  <Text style={styles.nameText}>{item.farmer} • {item.crop}</Text>
                  <Text style={styles.locText}><MapPin size={10} color={Colors.textSecondary} /> {item.village}</Text>
                </View>
                <View style={styles.feeBadge}>
                  <ShieldCheck size={11} color="#166534" />
                  <Text style={styles.feeText}>₹120 Paid</Text>
                </View>
              </View>

              <View style={styles.findingBox}>
                <Text style={styles.diseaseText}>Diagnosis: {item.disease}</Text>
                <Text style={styles.remedyText}>Prescription: {item.remedy}</Text>
              </View>

              {item.status === 'pending' ? (
                <TouchableOpacity
                  style={styles.actionBtn}
                  onPress={() => handleVerify(item.id, item.farmer)}
                  activeOpacity={0.85}
                >
                  <FileCheck size={14} color="#FFFFFF" />
                  <Text style={styles.actionBtnText}>{isKn ? 'ಡಿಜಿಟಲ್ ಸಹಿ ನೀಡಿ' : 'Sign & Issue Prescription'}</Text>
                </TouchableOpacity>
              ) : (
                <View style={styles.signedBadge}>
                  <CheckCircle2 size={13} color="#166534" />
                  <Text style={styles.signedText}>{isKn ? 'ದೃಢೀಕರಿಸಲಾಗಿದೆ' : 'Certified & Dispatched'}</Text>
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
  topCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#0F766E',
    borderRadius: BorderRadius.md,
    padding: 12,
  },
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: BorderRadius.sm,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  topTitle: { fontSize: 14, fontWeight: '800', color: '#FFFFFF' },
  topSub: { fontSize: 11, color: '#CCFBF1' },
  counterBadge: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
  },
  counterText: { fontSize: 10, fontWeight: '800', color: '#FFFFFF' },
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
  cardVerified: { backgroundColor: '#F0FDF4', borderColor: '#BBF7D0' },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  nameText: { fontSize: 13, fontWeight: '800', color: Colors.textPrimary },
  locText: { fontSize: 11, color: Colors.textSecondary, marginTop: 1 },
  feeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  feeText: { fontSize: 10, fontWeight: '800', color: '#166534' },
  findingBox: { backgroundColor: '#F8FAFC', padding: 8, borderRadius: BorderRadius.sm, gap: 2 },
  diseaseText: { fontSize: 11, fontWeight: '700', color: '#DC2626' },
  remedyText: { fontSize: 11, color: '#334155' },
  actionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#0F766E',
    paddingVertical: 10,
    borderRadius: BorderRadius.sm,
  },
  actionBtnText: { fontSize: 11, fontWeight: '800', color: '#FFFFFF' },
  signedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    backgroundColor: '#DCFCE7',
    paddingVertical: 6,
    borderRadius: BorderRadius.sm,
  },
  signedText: { fontSize: 11, fontWeight: '700', color: '#166534' },
});
