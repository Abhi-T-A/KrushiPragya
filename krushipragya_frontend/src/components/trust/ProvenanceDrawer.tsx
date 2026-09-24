import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { useLanguage } from '../../context/LanguageContext';
import { CropReport } from '../../types';
import { ShieldCheck, X, Building2, Calendar, User, Info } from 'lucide-react-native';
import { StatusBadge } from './StatusBadge';

interface ProvenanceDrawerProps {
  visible: boolean;
  onClose: () => void;
  report: CropReport;
}

export const ProvenanceDrawer: React.FC<ProvenanceDrawerProps> = ({
  visible,
  onClose,
  report,
}) => {
  const { t } = useLanguage();
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.content}>
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.titleRow}>
              <ShieldCheck size={20} color={Colors.trustPurple} />
              <Text style={styles.headerTitle}>ಸಾಕ್ಷ್ಯ ಮತ್ತು ಮೂಲ ಮಾಹಿತಿ (Provenance)</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
              <X size={20} color={Colors.textPrimary} />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.body} showsVerticalScrollIndicator={false}>
            {/* Primary Farmer-Friendly Details */}
            <View style={styles.section}>
              <View style={styles.itemRow}>
                <Building2 size={16} color={Colors.primary} />
                <View style={styles.itemTextCol}>
                  <Text style={styles.itemLabel}>ಸಲಹೆ ಮೂಲ ಸಂಸ್ಥೆ (Research Source)</Text>
                  <Text style={styles.itemValue}>{report.sourceInstitution || 'ICAR-CPCRI Kasaragod'}</Text>
                </View>
              </View>

              <View style={styles.itemRow}>
                <Calendar size={16} color={Colors.primary} />
                <View style={styles.itemTextCol}>
                  <Text style={styles.itemLabel}>ವರದಿ ದಾಖಲಾದ ಸಮಯ</Text>
                  <Text style={styles.itemValue}>{report.createdAt}</Text>
                </View>
              </View>

              <View style={styles.itemRow}>
                <User size={16} color={Colors.primary} />
                <View style={styles.itemTextCol}>
                  <Text style={styles.itemLabel}>ದಾಖಲಿಸಿದವರು</Text>
                  <Text style={styles.itemValue}>
                    {report.reporterRole === 'village_node'
                      ? `ಗ್ರಾಮ ಸಹಾಯಕ (${report.proxyFor ? `ರೈತ: ${report.proxyFor}` : 'ಪ್ರತಿನಿಧಿ'})`
                      : 'ರೈತರು (ಸ್ವತಃ)'}
                  </Text>
                </View>
              </View>

              <View style={styles.itemRow}>
                <Info size={16} color={Colors.primary} />
                <View style={styles.itemTextCol}>
                  <Text style={styles.itemLabel}>ಪ್ರಸ್ತುತ ಪರಿಶೀಲನೆ ಸ್ಥಿತಿ</Text>
                  <View style={{ marginTop: 4 }}>
                    <StatusBadge status={report.status} />
                  </View>
                </View>
              </View>
            </View>

            {/* Expandable Technical Details (Tucked away from normal farmers) */}
            <TouchableOpacity
              onPress={() => setShowTechnicalDetails(!showTechnicalDetails)}
              style={styles.expandToggle}
            >
              <Text style={styles.expandToggleText}>
                {showTechnicalDetails ? '▲ ತಾಂತ್ರಿಕ ವಿವರ ಮರೆಮಾಡಿ' : '▼ ತಾಂತ್ರಿಕ ವಿವರ ನೋಡಿ (Technical Details)'}
              </Text>
            </TouchableOpacity>

            {showTechnicalDetails && (
              <View style={styles.technicalBox}>
                <Text style={styles.techText}>• Report ID: {report.id}</Text>
                <Text style={styles.techText}>• Model: EfficientNet-B0 (Edge PyTorch)</Text>
                <Text style={styles.techText}>• AI Confidence: {(report.confidence * 100).toFixed(1)}%</Text>
                <Text style={styles.techText}>• Scientific Name: {report.scientificName || 'N/A'}</Text>
                <Text style={styles.techText}>• Village ID: {report.villageId}</Text>
              </View>
            )}

            <View style={styles.disclaimerBox}>
              <Text style={styles.disclaimerText}>
                ⚠️ ಈ ಶಿಫಾರಸು ಐಸಿಎಆರ್ ಅನುಮೋದಿತ ಕೃಷಿ ಮಾರ್ಗಸೂಚಿಯನ್ನು ಆಧರಿಸಿದೆ. ಯಾವುದೇ ಅಧಿಕೃತ ತೀರ್ಮಾನಕ್ಕೆ ಗ್ರಾಮ ಕೃಷಿ ಅಧಿಕಾರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ.
              </Text>
            </View>
          </ScrollView>

          <TouchableOpacity onPress={onClose} style={styles.doneButton}>
            <Text style={styles.doneButtonText}>{t.close}</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  content: {
    backgroundColor: Colors.surface,
    borderTopLeftRadius: BorderRadius.xl,
    borderTopRightRadius: BorderRadius.xl,
    padding: Spacing.lg,
    maxHeight: '80%',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
    flex: 1,
  },
  headerTitle: {
    ...Typography.title2,
    color: Colors.trustPurple,
  },
  closeBtn: {
    padding: 4,
  },
  body: {
    marginVertical: Spacing.md,
  },
  section: {
    backgroundColor: Colors.trustPurpleLight,
    padding: Spacing.md,
    borderRadius: BorderRadius.lg,
    gap: Spacing.md,
  },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: Spacing.sm,
  },
  itemTextCol: {
    flex: 1,
  },
  itemLabel: {
    ...Typography.caption,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  itemValue: {
    ...Typography.bodyLarge,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginTop: 2,
  },
  expandToggle: {
    paddingVertical: Spacing.sm,
    alignItems: 'center',
    marginTop: Spacing.sm,
  },
  expandToggleText: {
    ...Typography.label,
    color: Colors.trustPurple,
    fontWeight: '700',
  },
  technicalBox: {
    backgroundColor: Colors.surfaceSubtle,
    padding: Spacing.sm,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    gap: 4,
  },
  techText: {
    ...Typography.caption,
    color: Colors.textSecondary,
    fontFamily: 'monospace',
  },
  disclaimerBox: {
    backgroundColor: Colors.unverifiedBg,
    padding: Spacing.sm,
    borderRadius: BorderRadius.md,
    marginTop: Spacing.md,
  },
  disclaimerText: {
    ...Typography.caption,
    color: Colors.unverified,
    fontWeight: '600',
    lineHeight: 16,
  },
  doneButton: {
    backgroundColor: Colors.primary,
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.lg,
    alignItems: 'center',
    marginTop: Spacing.xs,
  },
  doneButtonText: {
    ...Typography.title2,
    color: Colors.textWhite,
  },
});
