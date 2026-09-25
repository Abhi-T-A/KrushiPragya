import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
} from 'react-native';
import { useLanguage } from '../../context/LanguageContext';
import { useReports } from '../../context/ReportContext';
import { Header } from '../../components/common/Header';
import { Card } from '../../components/common/Card';
import { StatusBadge } from '../../components/trust/StatusBadge';
import { Colors, Spacing, Typography, BorderRadius } from '../../constants/theme';
import { ChevronRight, Calendar, Building2 } from 'lucide-react-native';

export const ReportListScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const { language } = useLanguage();
  const { reports } = useReports();

  return (
    <View style={styles.container}>
      <Header title={language === 'kn' ? 'ವರದಿಗಳ ಸ್ಥಿತಿ' : 'Report Verification Status'} />

      <FlatList
        data={reports}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => (
          <Card
            onPress={() => navigation.navigate('AIResult', { reportId: item.id })}
            style={styles.card}
          >
            <View style={styles.cardTop}>
              <StatusBadge status={item.status} />
              <Text style={styles.cropTag}>
                {language === 'kn' ? item.cropNameKn : item.cropNameEn}
              </Text>
            </View>

            <View style={styles.middleRow}>
              <Text style={styles.diseaseName}>
                {language === 'kn' ? item.predictedDiseaseKn : item.predictedDisease}
              </Text>
              <Text style={styles.confidenceText}>
                {language === 'kn' ? 'ವಿಶ್ವಾಸ ಮಟ್ಟ: ' : 'AI Confidence: '}
                {(item.confidence * 100).toFixed(0)}%
              </Text>
            </View>

            <View style={styles.metaRow}>
              <View style={styles.metaItem}>
                <Calendar size={12} color={Colors.textMuted} />
                <Text style={styles.metaText}>{item.createdAt}</Text>
              </View>
              <View style={styles.metaItem}>
                <Building2 size={12} color={Colors.textMuted} />
                <Text style={styles.metaText}>{item.villageName}</Text>
              </View>
              <ChevronRight size={16} color={Colors.textSecondary} />
            </View>
          </Card>
        )}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  listContent: {
    padding: Spacing.lg,
    paddingBottom: Spacing.xxxl,
    gap: Spacing.sm,
  },
  card: {
    padding: Spacing.md,
  },
  cardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  cropTag: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.textSecondary,
  },
  middleRow: {
    marginVertical: Spacing.xs,
  },
  diseaseName: {
    ...Typography.title2,
    color: Colors.textPrimary,
    fontWeight: '800',
  },
  confidenceText: {
    ...Typography.caption,
    color: Colors.textMuted,
    marginTop: 2,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: Spacing.sm,
    paddingTop: Spacing.xs,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaText: {
    ...Typography.caption,
    color: Colors.textSecondary,
  },
});
