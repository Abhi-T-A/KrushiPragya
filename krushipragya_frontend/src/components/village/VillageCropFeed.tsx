import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Card } from '../../components/common/Card';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { SEED_VILLAGE_NEIGHBORS, VillageNeighbor } from '../../constants/villageNeighbors';
import {
  Users,
  AlertTriangle,
  CheckCircle2,
  Award,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from 'lucide-react-native';

export const VillageCropFeed: React.FC<{ onInspectIssue?: (issue: string) => void }> = ({
  onInspectIssue,
}) => {
  const { language } = useLanguage();
  const { user } = useAuth();
  const [isExpanded, setIsExpanded] = useState(true);

  const villageId = user?.villageId || 'v2';
  const villageName = user?.villageName ? user.villageName.split('(')[0].trim() : 'Ujire';
  const neighbors = SEED_VILLAGE_NEIGHBORS[villageId] || SEED_VILLAGE_NEIGHBORS.v2;

  // Filter neighbors who reported an issue or are monitoring
  const activeIssues = neighbors.flatMap((n) =>
    n.crops
      .filter((c) => c.healthStatus !== 'healthy')
      .map((c) => ({ farmer: n.name, role: n.role, crop: c }))
  );

  return (
    <View style={styles.container}>
      {/* Feed Section Title */}
      <View style={styles.headerRow}>
        <View style={styles.headerLeft}>
          <Users size={18} color={Colors.primary} />
          <Text style={styles.headerTitle}>
            {language === 'kn'
              ? `ನಮ್ಮ ಗ್ರಾಮದ ಬೆಳೆ ವರದಿಗಳು (${villageName})`
              : `Village Crop Health Activity (${villageName})`}
          </Text>
        </View>

        <TouchableOpacity
          onPress={() => setIsExpanded(!isExpanded)}
          style={styles.toggleBtn}
        >
          {isExpanded ? (
            <ChevronUp size={18} color={Colors.textSecondary} />
          ) : (
            <ChevronDown size={18} color={Colors.textSecondary} />
          )}
        </TouchableOpacity>
      </View>

      <Text style={styles.headerSubtitle}>
        {language === 'kn'
          ? 'ಗ್ರಾಮದ ಇತರ ರೈತರು ವರದಿ ಮಾಡಿದ ರೋಗಲಕ್ಷಣಗಳು ಮತ್ತು ತೋಟದ ಸ್ಥಿತಿ'
          : 'Live disease reports & crop status shared by fellow village farmers'}
      </Text>

      {/* Active Peer Issue Alerts (The Core Social Early Warning) */}
      {activeIssues.length > 0 && (
        <View style={styles.activeAlertsBox}>
          {activeIssues.map((item, idx) => (
            <Card key={idx} variant="alert" style={styles.alertCard}>
              <View style={styles.alertTopRow}>
                <View style={styles.farmerTag}>
                  <Text style={styles.farmerName}>{item.farmer}</Text>
                  {item.role === 'lead_farmer' && (
                    <View style={styles.leadBadge}>
                      <Award size={10} color={Colors.primaryDark} />
                      <Text style={styles.leadBadgeText}>
                        {language === 'kn' ? 'ಗ್ರಾಮ ಸಹಾಯಕ' : 'Lead Farmer'}
                      </Text>
                    </View>
                  )}
                </View>

                <Text style={styles.timeAgo}>{item.crop.reportedDaysAgo}</Text>
              </View>

              <View style={styles.issueRow}>
                <Text style={styles.cropEmoji}>{item.crop.emoji}</Text>
                <View style={styles.issueTextCol}>
                  <Text style={styles.cropName}>
                    {language === 'kn' ? item.crop.nameKn : item.crop.nameEn} ({item.crop.acres} {language === 'kn' ? 'ಎಕರೆ' : 'Acres'})
                  </Text>
                  <Text style={styles.issueName}>
                    ⚠️ {language === 'kn' ? item.crop.latestIssueKn : item.crop.latestIssueEn}
                  </Text>
                </View>
              </View>

              <View style={styles.warningHint}>
                <Sparkles size={12} color={Colors.alertHigh} />
                <Text style={styles.warningHintText}>
                  {language === 'kn'
                    ? 'ಗ್ರಾಮದಲ್ಲಿ ಸೋಂಕು ಹರಡದಂತೆ ನಿಮ್ಮ ತೋಟವನ್ನೂ ತಕ್ಷಣ ಪರೀಕ್ಷಿಸಿ.'
                    : 'Check your nearby plots to prevent localized disease spread.'}
                </Text>
              </View>
            </Card>
          ))}
        </View>
      )}

      {/* Expandable Village Directory: Showing all 5 registered farmers and what they cultivate */}
      {isExpanded && (
        <View style={styles.directorySection}>
          <Text style={styles.directoryTitle}>
            {language === 'kn'
              ? `ಗ್ರಾಮದ ನೋಂದಾಯಿತ ರೈತರು (${neighbors.length} ಜನ)`
              : `Registered Village Farmers (${neighbors.length})`}
          </Text>

          {neighbors.map((neighbor) => (
            <Card key={neighbor.id} style={styles.neighborCard}>
              <View style={styles.neighborTop}>
                <View style={styles.neighborNameCol}>
                  <Text style={styles.neighborName}>{neighbor.name}</Text>
                  {neighbor.role === 'lead_farmer' && (
                    <View style={styles.leadPill}>
                      <Award size={12} color={Colors.trustPurple} />
                      <Text style={styles.leadPillText}>
                        {language === 'kn' ? '⭐ ಗ್ರಾಮ ಸಹಾಯಕ / ಸಲಹೆಗಾರ' : '⭐ Village Node (Expert)'}
                      </Text>
                    </View>
                  )}
                </View>

                {/* Overall status */}
                {neighbor.crops.some((c) => c.healthStatus === 'issue_reported') ? (
                  <View style={[styles.statusPill, { backgroundColor: Colors.alertHighBg }]}>
                    <Text style={[styles.statusPillText, { color: Colors.alertHigh }]}>
                      {language === 'kn' ? '● ರೋಗ ವರದಿಯಾಗಿದೆ' : '● Alert'}
                    </Text>
                  </View>
                ) : (
                  <View style={[styles.statusPill, { backgroundColor: Colors.expertVerifiedBg }]}>
                    <Text style={[styles.statusPillText, { color: Colors.expertVerified }]}>
                      {language === 'kn' ? '● ತೋಟ ಆರೋಗ್ಯಕರ' : '● Healthy'}
                    </Text>
                  </View>
                )}
              </View>

              {/* Crops cultivated */}
              <View style={styles.cropPillsRow}>
                {neighbor.crops.map((c, i) => (
                  <View key={i} style={styles.cropPill}>
                    <Text style={styles.cropPillEmoji}>{c.emoji}</Text>
                    <Text style={styles.cropPillText}>
                      {language === 'kn' ? c.nameKn : c.nameEn} ({c.acres} {language === 'kn' ? 'ಎಕರೆ' : 'Acres'})
                    </Text>
                  </View>
                ))}
              </View>
            </Card>
          ))}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: Spacing.sm,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flex: 1,
  },
  headerTitle: {
    ...Typography.title2,
    fontSize: 17,
    color: Colors.textPrimary,
    fontWeight: '800',
  },
  toggleBtn: {
    padding: 4,
  },
  headerSubtitle: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
    marginBottom: Spacing.sm,
  },
  activeAlertsBox: {
    gap: Spacing.xs,
    marginBottom: Spacing.sm,
  },
  alertCard: {
    backgroundColor: '#FFFDF9',
    borderColor: '#FED7AA',
    borderLeftWidth: 4,
    borderLeftColor: Colors.alertHigh,
    padding: Spacing.md,
    marginBottom: Spacing.xs,
  },
  alertTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  farmerTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  farmerName: {
    ...Typography.bodyLarge,
    fontSize: 14,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  leadBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
    backgroundColor: Colors.primaryLight,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: BorderRadius.full,
  },
  leadBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.primaryDark,
  },
  timeAgo: {
    ...Typography.caption,
    fontSize: 11,
    color: Colors.textMuted,
  },
  issueRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    marginVertical: 4,
  },
  cropEmoji: {
    fontSize: 26,
  },
  issueTextCol: {
    flex: 1,
  },
  cropName: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.textSecondary,
  },
  issueName: {
    ...Typography.bodyLarge,
    fontSize: 15,
    fontWeight: '800',
    color: Colors.alertHigh,
    marginTop: 1,
  },
  warningHint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.alertHighBg,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: BorderRadius.sm,
    marginTop: 6,
  },
  warningHintText: {
    ...Typography.caption,
    fontSize: 11,
    color: Colors.alertHigh,
    fontWeight: '600',
    flex: 1,
  },
  directorySection: {
    gap: Spacing.xs,
    marginTop: Spacing.xs,
  },
  directoryTitle: {
    ...Typography.label,
    fontSize: 13,
    color: Colors.textSecondary,
    fontWeight: '700',
    marginBottom: 4,
  },
  neighborCard: {
    padding: Spacing.md,
    marginBottom: Spacing.xs,
    backgroundColor: Colors.surface,
  },
  neighborTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: Spacing.xs,
  },
  neighborNameCol: {
    gap: 2,
    flex: 1,
  },
  neighborName: {
    ...Typography.bodyLarge,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  leadPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    alignSelf: 'flex-start',
    backgroundColor: Colors.trustPurpleLight,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
    marginTop: 2,
  },
  leadPillText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.trustPurple,
  },
  statusPill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: BorderRadius.full,
  },
  statusPillText: {
    fontSize: 10,
    fontWeight: '800',
  },
  cropPillsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 4,
  },
  cropPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.surfaceSubtle,
    borderWidth: 1,
    borderColor: Colors.border,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: BorderRadius.full,
  },
  cropPillEmoji: {
    fontSize: 13,
  },
  cropPillText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
});
