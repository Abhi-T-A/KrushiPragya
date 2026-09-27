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
  ShieldAlert,
  Activity,
  Send,
  MapPin,
  CheckCircle2,
  AlertTriangle,
  Plane,
  Radio,
} from 'lucide-react-native';

interface OutbreakCluster {
  id: string;
  village: string;
  villageKn: string;
  crop: string;
  cropKn: string;
  disease: string;
  diseaseKn: string;
  affectedFarms: number;
  severity: 'HIGH' | 'MODERATE' | 'CONTAINED';
  actionTaken: boolean;
}

const INITIAL_CLUSTERS: OutbreakCluster[] = [
  {
    id: 'c1',
    village: 'Ujire Cluster',
    villageKn: 'ಉಜಿರೆ ಕ್ಲಸ್ಟರ್',
    crop: 'Arecanut (ಅಡಿಕೆ)',
    cropKn: 'ಅಡಿಕೆ',
    disease: 'Koleroga / Fruit Rot',
    diseaseKn: 'ಕೊಳೆರೋಗ',
    affectedFarms: 14,
    severity: 'HIGH',
    actionTaken: false,
  },
  {
    id: 'c2',
    village: 'Dharmasthala Sector',
    villageKn: 'ಧರ್ಮಸ್ಥಳ ಸೆಕ್ಟರ್',
    crop: 'Paddy (ಭತ್ತ)',
    cropKn: 'ಭತ್ತ',
    disease: 'Leaf Blast',
    diseaseKn: 'ಎಲೆ ಬ್ಲಾಸ್ಟ್',
    affectedFarms: 4,
    severity: 'MODERATE',
    actionTaken: false,
  },
  {
    id: 'c3',
    village: 'Kokkada Block',
    villageKn: 'ಕೊಕ್ಕಡ ಬ್ಲಾಕ್',
    crop: 'Black Pepper (ಕಾಳುಮೆಣಸು)',
    cropKn: 'ಕಾಳುಮೆಣಸು',
    disease: 'Quick Wilt',
    diseaseKn: 'ಶೀಘ್ರ ಸೊರಗು ರೋಗ',
    affectedFarms: 1,
    severity: 'CONTAINED',
    actionTaken: true,
  },
];

export const GovtPortalScreen: React.FC = () => {
  const { language } = useLanguage();
  const isKn = language === 'kn';
  const [clusters, setClusters] = useState<OutbreakCluster[]>(INITIAL_CLUSTERS);
  const [talukAlertSent, setTalukAlertSent] = useState(false);

  const handleDeploySquad = (id: string, village: string, crop: string) => {
    setClusters((prev) =>
      prev.map((c) => (c.id === id ? { ...c, actionTaken: true, severity: 'CONTAINED' } : c))
    );
    Alert.alert(
      isKn ? 'ಡ್ರೋನ್ ತಂಡ ನಿಯೋಜಿಸಲಾಗಿದೆ 🚁' : 'Drone Containment Squad Deployed 🚁',
      isKn
        ? `${village} ವ್ಯಾಪ್ತಿಯಲ್ಲಿ ${crop} ಬೆಳೆಗಳ ರಕ್ಷಣೆಗೆ ಕೃಷಿ ಇಲಾಖೆಯ ಡ್ರೋನ್ ತಂಡವನ್ನು ರವಾನಿಸಲಾಗಿದೆ.`
        : `Emergency FPO drone spraying unit dispatched to ${village} for ${crop} containment.`
    );
  };

  const handleBroadcastTalukAlert = () => {
    setTalukAlertSent(true);
    Alert.alert(
      isKn ? 'ತಾಲ್ಲೂಕು ಎಚ್ಚರಿಕೆ ರವಾನೆಯಾಗಿದೆ 📢' : 'Taluk Biosecurity Alert Broadcasted 📢',
      isKn
        ? 'ಬೆಳ್ತಂಗಡಿ ತಾಲ್ಲೂಕಿನ ಎಲ್ಲಾ 450+ ನೋಂದಾಯಿತ ರೈತರಿಗೆ ರೋಗ ನಿಯಂತ್ರಣ ಮಾರ್ಗಸೂಚಿ ಸಂದೇಶ ತಲುಪಿದೆ.'
        : 'Official advisory pushed to all 450+ registered farmers across Belthangady Taluk.'
    );
  };

  return (
    <View style={styles.container}>
      <Header />

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Surveillance Header Banner */}
        <View style={styles.banner}>
          <ShieldAlert size={22} color="#FFFFFF" />
          <View style={{ flex: 1 }}>
            <Text style={styles.bannerTitle}>
              {isKn ? 'ಕೃಷಿ ಇಲಾಖೆ ಅಧಿಕಾರಿ' : 'Department of Agriculture Officer'}
            </Text>
            <Text style={styles.bannerSub}>
              {isKn ? 'ತಾಲ್ಲೂಕು ಬೆಳೆ ರೋಗ ನಿಗಾ ಪೋರ್ಟಲ್ • ಬೆಳ್ತಂಗಡಿ' : 'Taluk Crop Disease Surveillance • Belthangady'}
            </Text>
          </View>
        </View>

        {/* 3 Quick Micro-Metrics */}
        <View style={styles.metricsRow}>
          <View style={styles.metricBox}>
            <Text style={styles.metricNum}>142</Text>
            <Text style={styles.metricLabel}>{isKn ? 'ಇಂದಿನ ಸ್ಕ್ಯಾನ್‌ಗಳು' : 'Scans Today'}</Text>
          </View>
          <View style={styles.metricDivider} />
          <View style={styles.metricBox}>
            <Text style={[styles.metricNum, { color: '#DC2626' }]}>2</Text>
            <Text style={styles.metricLabel}>{isKn ? 'ಸಕ್ರಿಯ ಕ್ಲಸ್ಟರ್‌ಗಳು' : 'Active Clusters'}</Text>
          </View>
          <View style={styles.metricDivider} />
          <View style={styles.metricBox}>
            <Text style={[styles.metricNum, { color: '#16A34A' }]}>88%</Text>
            <Text style={styles.metricLabel}>{isKn ? 'ನಿಯಂತ್ರಣ ದರ' : 'Contained'}</Text>
          </View>
        </View>

        {/* 1-Tap Emergency Broadcast Button */}
        <TouchableOpacity
          style={[styles.broadcastCard, talukAlertSent && styles.broadcastSentCard]}
          onPress={handleBroadcastTalukAlert}
          activeOpacity={0.85}
        >
          <Radio size={18} color="#FFFFFF" />
          <View style={{ flex: 1 }}>
            <Text style={styles.broadcastTitle}>
              {talukAlertSent
                ? (isKn ? 'ಎಚ್ಚರಿಕೆ ಸಂದೇಶ ಪ್ರಸಾರವಾಗಿದೆ (450+ ರೈತರು)' : 'Advisory Active (450+ Farmers Alerted)')
                : (isKn ? 'ತಾಲ್ಲೂಕು ತುರ್ತು ಎಚ್ಚರಿಕೆ ಪ್ರಸಾರ ಮಾಡಿ' : 'Broadcast Taluk Emergency Advisory')}
            </Text>
            <Text style={styles.broadcastSub}>
              {isKn ? 'ಕೊಳೆರೋಗ & ಬ್ಲಾಸ್ಟ್ ತಡೆಗಟ್ಟುವ ಮಾರ್ಗಸೂಚಿ ಕಳುಹಿಸಿ' : 'Push spray guidelines to all registered farms in taluk'}
            </Text>
          </View>
          <Send size={15} color="#FFFFFF" />
        </TouchableOpacity>

        {/* Village Outbreak Clusters List */}
        <Text style={styles.sectionTitle}>
          {isKn ? 'ಗ್ರಾಮ ಮಟ್ಟದ ರೋಗ ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗಳು' : 'Village Outbreak Clusters & Containment'}
        </Text>

        <View style={styles.list}>
          {clusters.map((c) => (
            <View key={c.id} style={[styles.clusterCard, c.severity === 'CONTAINED' && styles.clusterContained]}>
              <View style={styles.clusterTop}>
                <View style={{ flex: 1 }}>
                  <View style={styles.locRow}>
                    <MapPin size={12} color={Colors.textSecondary} />
                    <Text style={styles.clusterVillage}>{isKn ? c.villageKn : c.village}</Text>
                  </View>
                  <Text style={styles.clusterDisease}>
                    {isKn ? c.cropKn : c.crop} • {isKn ? c.diseaseKn : c.disease}
                  </Text>
                </View>

                {c.severity === 'HIGH' && (
                  <View style={[styles.severityBadge, styles.badgeHigh]}>
                    <AlertTriangle size={11} color="#DC2626" />
                    <Text style={styles.badgeHighText}>{c.affectedFarms} {isKn ? 'ಜಮೀನುಗಳು' : 'Farms'}</Text>
                  </View>
                )}
                {c.severity === 'MODERATE' && (
                  <View style={[styles.severityBadge, styles.badgeMod]}>
                    <Text style={styles.badgeModText}>{c.affectedFarms} {isKn ? 'ಜಮೀನುಗಳು' : 'Farms'}</Text>
                  </View>
                )}
                {c.severity === 'CONTAINED' && (
                  <View style={[styles.severityBadge, styles.badgeContained]}>
                    <CheckCircle2 size={11} color="#16A34A" />
                    <Text style={styles.badgeContainedText}>{isKn ? 'ನಿಯಂತ್ರಿಸಲಾಗಿದೆ' : 'Contained'}</Text>
                  </View>
                )}
              </View>

              {!c.actionTaken ? (
                <TouchableOpacity
                  style={styles.deployBtn}
                  onPress={() => handleDeploySquad(c.id, isKn ? c.villageKn : c.village, isKn ? c.cropKn : c.crop)}
                  activeOpacity={0.85}
                >
                  <Plane size={14} color="#FFFFFF" />
                  <Text style={styles.deployBtnText}>
                    {isKn ? 'ಡ್ರೋನ್ ಸಿಂಪರಣಾ ತಂಡ ನಿಯೋಜಿಸಿ' : 'Deploy Drone Containment Squad'}
                  </Text>
                </TouchableOpacity>
              ) : (
                <View style={styles.deployedRow}>
                  <CheckCircle2 size={12} color="#16A34A" />
                  <Text style={styles.deployedText}>
                    {isKn ? 'ಡ್ರೋನ್ ತಂಡ ನಿಯೋಜಿಸಲಾಗಿದೆ • ಮೇಲ್ವಿಚಾರಣೆಯಲ್ಲಿದೆ' : 'Squad Active • Buffer Zone Protected'}
                  </Text>
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
    backgroundColor: '#1E3A8A',
    borderRadius: BorderRadius.md,
    padding: 12,
  },
  bannerTitle: { fontSize: 14, fontWeight: '800', color: '#FFFFFF' },
  bannerSub: { fontSize: 11, color: '#BFDBFE', marginTop: 1 },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  metricBox: { alignItems: 'center', flex: 1 },
  metricNum: { fontSize: 18, fontWeight: '800', color: Colors.textPrimary },
  metricLabel: { fontSize: 10, color: Colors.textSecondary, fontWeight: '600', marginTop: 2 },
  metricDivider: { width: 1, height: 24, backgroundColor: '#E2E8F0' },
  broadcastCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#DC2626',
    borderRadius: BorderRadius.md,
    padding: 12,
  },
  broadcastSentCard: {
    backgroundColor: '#16A34A',
  },
  broadcastTitle: { fontSize: 12, fontWeight: '800', color: '#FFFFFF' },
  broadcastSub: { fontSize: 10, color: 'rgba(255,255,255,0.9)', marginTop: 1 },
  sectionTitle: { fontSize: 13, fontWeight: '800', color: Colors.textPrimary, marginTop: 2 },
  list: { gap: 10 },
  clusterCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    gap: 8,
  },
  clusterContained: { backgroundColor: '#F0FDF4', borderColor: '#BBF7D0' },
  clusterTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  locRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  clusterVillage: { fontSize: 13, fontWeight: '800', color: Colors.textPrimary },
  clusterDisease: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },
  severityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: BorderRadius.full,
  },
  badgeHigh: { backgroundColor: '#FEE2E2' },
  badgeHighText: { fontSize: 10, fontWeight: '800', color: '#DC2626' },
  badgeMod: { backgroundColor: '#FEF3C7' },
  badgeModText: { fontSize: 10, fontWeight: '800', color: '#D97706' },
  badgeContained: { backgroundColor: '#DCFCE7' },
  badgeContainedText: { fontSize: 10, fontWeight: '800', color: '#166534' },
  deployBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#1E3A8A',
    paddingVertical: 9,
    borderRadius: BorderRadius.sm,
  },
  deployBtnText: { fontSize: 11, fontWeight: '800', color: '#FFFFFF' },
  deployedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    backgroundColor: '#DCFCE7',
    paddingVertical: 6,
    borderRadius: BorderRadius.sm,
  },
  deployedText: { fontSize: 10, fontWeight: '700', color: '#166534' },
});
