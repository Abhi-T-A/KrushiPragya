import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  FlatList,
} from 'react-native';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { Card } from '../../components/common/Card';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { SEED_VILLAGE_NEIGHBORS, VillageNeighbor } from '../../constants/villageNeighbors';
import {
  Users,
  AlertTriangle,
  Award,
  Sparkles,
  ChevronDown,
  ChevronUp,
  User,
} from 'lucide-react-native';

export const VillageCropFeed: React.FC<{ onInspectIssue?: (issue: string) => void }> = ({
  onInspectIssue,
}) => {
  const { language } = useLanguage();
  const { user } = useAuth();
  const [showDirectory, setShowDirectory] = useState(false);

  const villageId = user?.villageId || 'v2';
  const villageName = user?.villageName ? user.villageName.split('(')[0].trim() : 'Ujire';
  const neighbors = SEED_VILLAGE_NEIGHBORS[villageId] || SEED_VILLAGE_NEIGHBORS.v2;

  // Filter neighbors who reported an active issue
  const activeIssues = neighbors.flatMap((n) =>
    n.crops
      .filter((c) => c.healthStatus !== 'healthy')
      .map((c) => ({
        farmer: language === 'kn' ? n.name.split('(')[0].trim() : (n.name.includes('(') ? n.name.split('(')[1].replace(')', '').trim() : n.name),
        role: n.role,
        crop: c,
      }))
  );

  return (
    <View style={styles.container}>
      {/* Sleek Header */}
      <View style={styles.sectionHeader}>
        <View style={styles.headerLeft}>
          <Users size={16} color={Colors.primary} />
          <Text style={styles.sectionTitle}>
            {language === 'kn'
              ? `ಗ್ರಾಮದ ಬೆಳೆ ಸ್ಥಿತಿ (${villageName})`
              : `Village Health Signals (${villageName})`}
          </Text>
        </View>

        {activeIssues.length > 0 && (
          <View style={styles.alertCountBadge}>
            <Text style={styles.alertCountText}>
              {activeIssues.length} {language === 'kn' ? 'ಎಚ್ಚರಿಕೆಗಳು' : 'Alerts'}
            </Text>
          </View>
        )}
      </View>

      {/* Horizontal Carousel for Active Disease Alerts (No vertical screen clutter!) */}
      {activeIssues.length > 0 && (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.horizontalAlertsContainer}
        >
          {activeIssues.map((item, idx) => (
            <Card key={idx} variant="alert" style={styles.compactAlertCard}>
              <View style={styles.alertCardHeader}>
                <View style={styles.farmerRow}>
                  <Text style={styles.farmerNameText} numberOfLines={1}>
                    {item.farmer}
                  </Text>
                  {item.role === 'lead_farmer' && (
                    <View style={styles.leadBadge}>
                      <Award size={10} color={Colors.primaryDark} />
                      <Text style={styles.leadBadgeText}>
                        {language === 'kn' ? 'ಸಹಾಯಕ' : 'Lead'}
                      </Text>
                    </View>
                  )}
                </View>
                <Text style={styles.timeAgoText}>
                  {language === 'kn' ? '2 ದಿನಗಳ ಹಿಂದೆ' : '2d ago'}
                </Text>
              </View>

              <View style={styles.issueRow}>
                <Text style={styles.cropEmoji}>{item.crop.emoji}</Text>
                <View style={styles.issueTextCol}>
                  <Text style={styles.cropNameSub}>
                    {language === 'kn' ? item.crop.nameKn : item.crop.nameEn} · {item.crop.acres} {language === 'kn' ? 'ಎಕರೆ' : 'Acres'}
                  </Text>
                  <Text style={styles.issueHeading} numberOfLines={1}>
                    ⚠️ {language === 'kn' ? item.crop.latestIssueKn : item.crop.latestIssueEn}
                  </Text>
                </View>
              </View>

              <View style={styles.warningStrip}>
                <Sparkles size={11} color={Colors.alertHigh} />
                <Text style={styles.warningStripText} numberOfLines={1}>
                  {language === 'kn'
                    ? 'ಸೋಂಕು ಹರಡದಂತೆ ನಿಮ್ಮ ತೋಟ ಪರೀಕ್ಷಿಸಿ'
                    : 'Check your nearby plots to avoid spread'}
                </Text>
              </View>
            </Card>
          ))}
        </ScrollView>
      )}

      {/* Compact Expandable Directory Bar */}
      <TouchableOpacity
        activeOpacity={0.75}
        onPress={() => setShowDirectory(!showDirectory)}
        style={styles.directoryBar}
      >
        <View style={styles.directoryBarLeft}>
          <User size={14} color={Colors.textSecondary} />
          <Text style={styles.directoryBarText}>
            {language === 'kn'
              ? `ಗ್ರಾಮದ ನೋಂದಾಯಿತ ರೈತರು (${neighbors.length} ಜನ)`
              : `Registered Village Farmers (${neighbors.length})`}
          </Text>
        </View>

        <View style={styles.directoryBarRight}>
          <Text style={styles.directoryToggleAction}>
            {showDirectory ? (language === 'kn' ? 'ಮುಚ್ಚಿ' : 'Hide') : (language === 'kn' ? 'ನೋಡಿ' : 'View')}
          </Text>
          {showDirectory ? (
            <ChevronUp size={16} color={Colors.primary} />
          ) : (
            <ChevronDown size={16} color={Colors.primary} />
          )}
        </View>
      </TouchableOpacity>

      {/* Compact Neighbor List (Only when farmer wants to see it) */}
      {showDirectory && (
        <View style={styles.directoryDropdown}>
          {neighbors.map((neighbor) => (
            <View key={neighbor.id} style={styles.neighborRowItem}>
              <View style={styles.neighborAvatarMini}>
                <Text style={styles.neighborAvatarEmoji}>
                  {neighbor.crops[0]?.emoji || '🌴'}
                </Text>
              </View>

              <View style={styles.neighborInfoCol}>
                <View style={styles.neighborNameAndRole}>
                  <Text style={styles.neighborNameMini} numberOfLines={1}>
                    {language === 'kn'
                      ? neighbor.name.split('(')[0].trim()
                      : (neighbor.name.includes('(') ? neighbor.name.split('(')[1].replace(')', '').trim() : neighbor.name)}
                  </Text>
                  {neighbor.role === 'lead_farmer' && (
                    <View style={styles.leadPillMini}>
                      <Text style={styles.leadPillMiniText}>
                        {language === 'kn' ? 'ಗ್ರಾಮ ಸಹಾಯಕ' : 'Node'}
                      </Text>
                    </View>
                  )}
                </View>
                <Text style={styles.neighborCropsMini} numberOfLines={1}>
                  {neighbor.crops
                    .map((c) => `${language === 'kn' ? c.nameKn : c.nameEn} (${c.acres}ac)`)
                    .join(' · ')}
                </Text>
              </View>

              {neighbor.crops.some((c) => c.healthStatus === 'issue_reported') ? (
                <View style={[styles.statusDot, { backgroundColor: Colors.alertHighBg }]}>
                  <Text style={[styles.statusDotText, { color: Colors.alertHigh }]}>
                    {language === 'kn' ? 'ಎಚ್ಚರಿಕೆ' : 'Alert'}
                  </Text>
                </View>
              ) : (
                <View style={[styles.statusDot, { backgroundColor: Colors.expertVerifiedBg }]}>
                  <Text style={[styles.statusDotText, { color: Colors.expertVerified }]}>
                    {language === 'kn' ? 'ಉತ್ತಮ' : 'Healthy'}
                  </Text>
                </View>
              )}
            </View>
          ))}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 4,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  sectionTitle: {
    ...Typography.title2,
    fontSize: 15,
    color: Colors.textPrimary,
    fontWeight: '800',
  },
  alertCountBadge: {
    backgroundColor: Colors.alertHighBg,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: BorderRadius.full,
  },
  alertCountText: {
    fontSize: 10,
    fontWeight: '800',
    color: Colors.alertHigh,
  },
  horizontalAlertsContainer: {
    paddingRight: Spacing.md,
    gap: Spacing.sm,
    paddingBottom: 4,
  },
  compactAlertCard: {
    width: 280,
    backgroundColor: '#FFFDF9',
    borderColor: '#FED7AA',
    borderLeftWidth: 4,
    borderLeftColor: Colors.alertHigh,
    padding: Spacing.sm + 2,
    borderRadius: BorderRadius.lg,
  },
  alertCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 2,
  },
  farmerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    flex: 1,
  },
  farmerNameText: {
    ...Typography.bodyLarge,
    fontSize: 13,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  leadBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
    backgroundColor: Colors.primaryLight,
    paddingHorizontal: 5,
    paddingVertical: 1,
    borderRadius: BorderRadius.full,
  },
  leadBadgeText: {
    fontSize: 9,
    fontWeight: '800',
    color: Colors.primaryDark,
  },
  timeAgoText: {
    ...Typography.caption,
    fontSize: 10,
    color: Colors.textMuted,
  },
  issueRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginVertical: 3,
  },
  cropEmoji: {
    fontSize: 22,
  },
  issueTextCol: {
    flex: 1,
  },
  cropNameSub: {
    ...Typography.caption,
    fontSize: 10,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  issueHeading: {
    ...Typography.bodyLarge,
    fontSize: 13,
    fontWeight: '800',
    color: Colors.alertHigh,
  },
  warningStrip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.alertHighBg,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
    marginTop: 2,
  },
  warningStripText: {
    ...Typography.caption,
    fontSize: 10,
    color: Colors.alertHigh,
    fontWeight: '600',
    flex: 1,
  },
  directoryBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.lg,
    borderWidth: 1,
    borderColor: Colors.border,
    marginTop: 6,
  },
  directoryBarLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  directoryBarText: {
    ...Typography.caption,
    fontSize: 12,
    fontWeight: '700',
    color: Colors.textSecondary,
  },
  directoryBarRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  directoryToggleAction: {
    ...Typography.caption,
    fontSize: 11,
    fontWeight: '700',
    color: Colors.primary,
  },
  directoryDropdown: {
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.lg,
    borderWidth: 1,
    borderColor: Colors.border,
    marginTop: 4,
    padding: Spacing.xs,
    gap: 2,
  },
  neighborRowItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
    gap: 8,
  },
  neighborAvatarMini: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.surfaceSubtle,
    alignItems: 'center',
    justifyContent: 'center',
  },
  neighborAvatarEmoji: {
    fontSize: 14,
  },
  neighborInfoCol: {
    flex: 1,
    gap: 1,
  },
  neighborNameAndRole: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  neighborNameMini: {
    ...Typography.caption,
    fontSize: 12,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  leadPillMini: {
    backgroundColor: Colors.trustPurpleLight,
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: BorderRadius.full,
  },
  leadPillMiniText: {
    fontSize: 8,
    fontWeight: '800',
    color: Colors.trustPurple,
  },
  neighborCropsMini: {
    ...Typography.caption,
    fontSize: 10,
    color: Colors.textSecondary,
  },
  statusDot: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: BorderRadius.full,
  },
  statusDotText: {
    fontSize: 9,
    fontWeight: '800',
  },
});
