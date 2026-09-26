import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  Image,
  Linking,
  StatusBar,
  Alert,
} from 'react-native';
import {
  ArrowLeft,
  Landmark,
  MapPin,
  ExternalLink,
  ShieldCheck,
  Calendar,
  Globe,
  Receipt,
  Sparkles,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react-native';
import { useAuth } from '../../context/AuthContext';
import { SchemeDetail, SchemeApplication } from '../../types/schemes';
import {
  fetchSchemeDetail,
  saveScheme,
  unsaveScheme,
  markSchemeRead,
} from '../../services/schemesApi';
import { SchemeSection } from '../../components/schemes/SchemeSection';
import { SchemeStatusBadge } from '../../components/schemes/SchemeStatusBadge';
import { SchemeBookmarkButton } from '../../components/schemes/SchemeBookmarkButton';
import { SchemeLoadingState } from '../../components/schemes/SchemeLoadingState';
import { SchemeErrorState } from '../../components/schemes/SchemeErrorState';
import { SchemePaymentModal } from '../../components/schemes/SchemePaymentModal';

export const SchemeDetailsScreen: React.FC<{ route: any; navigation: any }> = ({
  route,
  navigation,
}) => {
  const { schemeId } = route.params || {};
  const { user } = useAuth();

  const [scheme, setScheme] = useState<SchemeDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [paymentModalVisible, setPaymentModalVisible] = useState<boolean>(false);

  const loadDetail = useCallback(async () => {
    if (!schemeId) {
      setErrorMessage('ಯೋಜನೆ ಐಡಿ ಅಮಾನ್ಯವಾಗಿದೆ');
      setLoading(false);
      return;
    }

    setLoading(true);
    setErrorMessage(null);

    try {
      const data = await fetchSchemeDetail(schemeId, 'kn', user);
      setScheme(data);

      // Silently mark as read in backend
      markSchemeRead(schemeId, user).catch(() => {});
    } catch {
      setErrorMessage('ಯೋಜನೆಯ ವಿವರಗಳನ್ನು ಲೋಡ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ');
    } finally {
      setLoading(false);
    }
  }, [schemeId, user]);

  useEffect(() => {
    loadDetail();
  }, [loadDetail]);

  const handleToggleBookmark = async () => {
    if (!scheme) return;
    const currentSaved = scheme.is_saved;

    // Optimistic UI update
    setScheme((prev) => (prev ? { ...prev, is_saved: !currentSaved } : prev));

    try {
      if (currentSaved) {
        await unsaveScheme(scheme.id, user);
      } else {
        await saveScheme(scheme.id, user);
      }
    } catch {
      // Rollback
      setScheme((prev) => (prev ? { ...prev, is_saved: currentSaved } : prev));
      Alert.alert('ದೋಷ', 'ಬುಕ್‌ಮಾರ್ಕ್ ನವೀಕರಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.');
    }
  };

  const handleOpenApplicationUrl = async () => {
    const targetUrl = scheme?.application_url || scheme?.source?.url;
    if (!targetUrl) {
      Alert.alert('ಮಾಹಿತಿ', 'ಅಧಿಕೃತ ವೆಬ್ಸೈಟ್ ಲಿಂಕ್ ಲಭ್ಯವಿಲ್ಲ.');
      return;
    }

    try {
      const supported = await Linking.canOpenURL(targetUrl);
      if (supported) {
        await Linking.openURL(targetUrl);
      } else {
        Alert.alert('ದೋಷ', 'ಈ ಲಿಂಕ್ ತೆರೆಯಲು ಸಾಧ್ಯವಿಲ್ಲ.');
      }
    } catch {
      Alert.alert('ದೋಷ', 'ವೆಬ್ಸೈಟ್ ತೆರೆಯುವಾಗ ಸಮಸ್ಯೆ ಉಂಟಾಗಿದೆ.');
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
        <View style={styles.topHeader}>
          <TouchableOpacity
            onPress={() => navigation.goBack()}
            style={styles.backButton}
            accessibilityRole="button"
            accessibilityLabel="ಹಿಂದೆ ಹೋಗಿ"
          >
            <ArrowLeft size={22} color="#1F2937" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>ಯೋಜನೆ ವಿವರ</Text>
          <View style={{ width: 36 }} />
        </View>
        <SchemeLoadingState message="ಯೋಜನೆ ವಿವರಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ..." />
      </SafeAreaView>
    );
  }

  if (errorMessage || !scheme) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
        <View style={styles.topHeader}>
          <TouchableOpacity
            onPress={() => navigation.goBack()}
            style={styles.backButton}
            accessibilityRole="button"
            accessibilityLabel="ಹಿಂದೆ ಹೋಗಿ"
          >
            <ArrowLeft size={22} color="#1F2937" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>ಯೋಜನೆ ವಿವರ</Text>
          <View style={{ width: 36 }} />
        </View>
        <SchemeErrorState
          title={errorMessage || 'ಯೋಜನೆ ಲಭ್ಯವಿಲ್ಲ'}
          subtitle="ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ ಅಥವಾ ಹಿಂದಿನ ಪುಟಕ್ಕೆ ಹಿಂತಿರುಗಿ."
          onBack={() => navigation.goBack()}
          onRetry={loadDetail}
        />
      </SafeAreaView>
    );
  }

  const hasValidRemoteImage =
    typeof scheme.image_url === 'string' &&
    scheme.image_url.trim().startsWith('http');

  const imageSource = hasValidRemoteImage
    ? { uri: scheme.image_url }
    : require('../../../assets/scheme_fallback.jpg');

  const officialUrlAvailable = Boolean(scheme.application_url || scheme.source?.url);

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />

      {/* Screen Top Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity
          onPress={() => navigation.goBack()}
          style={styles.backButton}
          accessibilityRole="button"
          accessibilityLabel="ಹಿಂದೆ ಹೋಗಿ"
        >
          <ArrowLeft size={22} color="#1F2937" />
        </TouchableOpacity>

        <Text style={styles.headerTitle}>ಯೋಜನೆ ವಿವರ</Text>

        {/* Header Bookmark Action */}
        <SchemeBookmarkButton
          isSaved={scheme.is_saved}
          onToggle={handleToggleBookmark}
          size="medium"
          showBackground={true}
        />
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Large Scheme Banner Image */}
        <View style={styles.imageContainer}>
          <Image
            source={imageSource}
            style={styles.bannerImage}
            resizeMode="cover"
          />
          <View style={styles.imageGradientOverlay}>
            <View style={styles.badgeRow}>
              <SchemeStatusBadge
                label={scheme.category || 'ಸರ್ಕಾರಿ ಯೋಜನೆ'}
                variant="success"
              />
              <SchemeStatusBadge
                label={scheme.status === 'ACTIVE' ? 'ಸಕ್ರಿಯ • Active' : scheme.status}
                variant="primary"
              />
            </View>
          </View>
        </View>

        {/* Title & Department Card */}
        <View style={styles.introCard}>
          <Text style={styles.kannadaTitle}>{scheme.title_kn || scheme.name}</Text>
          {scheme.title_en && scheme.title_en !== (scheme.title_kn || scheme.name) && (
            <Text style={styles.englishTitle}>{scheme.title_en}</Text>
          )}

          <View style={styles.metaBox}>
            <View style={styles.metaRow}>
              <Landmark size={15} color="#0F6E56" style={styles.metaIcon} />
              <Text style={styles.metaText}>{scheme.department || 'ಕೃಷಿ ಇಲಾಖೆ'}</Text>
            </View>

            <View style={styles.metaRow}>
              <MapPin size={15} color="#6B7280" style={styles.metaIcon} />
              <Text style={styles.metaTextMuted}>
                {scheme.state === 'ಭಾರತ' ? 'ಕೇಂದ್ರ ಸರ್ಕಾರ (All India / Central)' : scheme.state}
              </Text>
            </View>
          </View>
        </View>

        {/* 1. 📋 ಯೋಜನೆಯ ಬಗ್ಗೆ (Description) */}
        <SchemeSection
          title="📋 ಯೋಜನೆಯ ಬಗ್ಗೆ"
          englishTitle="About the Scheme"
          description={scheme.description}
        />

        {/* 2. 🎁 ಪ್ರಯೋಜನಗಳು (Benefits) */}
        <SchemeSection
          title="🎁 ಪ್ರಯೋಜನಗಳು"
          englishTitle="Key Benefits"
          items={scheme.benefits}
        />

        {/* 3. 👨🌾 ಯಾರು ಅರ್ಹರು? (Eligibility) */}
        <SchemeSection
          title="👨‍🌾 ಯಾರು ಅರ್ಹರು?"
          englishTitle="Eligibility Criteria"
          items={scheme.eligibility}
        />

        {/* 4. 📄 ಬೇಕಾಗುವ ದಾಖಲೆಗಳು (Documents Required) */}
        <SchemeSection
          title="📄 ಬೇಕಾಗುವ ದಾಖಲೆಗಳು"
          englishTitle="Documents Required"
          items={scheme.documents_required}
        />

        {/* 5. 📝 ಹೇಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು? (Application Process) */}
        <SchemeSection
          title="📝 ಹೇಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು?"
          englishTitle="How to Apply"
          items={scheme.application_process}
          numbered={true}
        />

        {/* 6. 🏛️ ಅಧಿಕೃತ ಮೂಲ (Source / Provenance) */}
        <View style={styles.provenanceCard}>
          <View style={styles.provenanceHeader}>
            <ShieldCheck size={18} color="#0F6E56" />
            <Text style={styles.provenanceTitle}>🏛️ ಅಧಿಕೃತ ಮೂಲ & ಪರಿಶೀಲನೆ</Text>
          </View>
          <Text style={styles.provenanceSubtitle}>Source Provenance & Government Trust</Text>

          <View style={styles.provenanceBody}>
            <View style={styles.provRow}>
              <Globe size={14} color="#6B7280" />
              <Text style={styles.provLabel}>ಮೂಲ ಪೋರ್ಟಲ್:</Text>
              <Text style={styles.provValue}>{scheme.source?.name || 'ಅಧಿಕೃತ ಸರ್ಕಾರಿ ಪೋರ್ಟಲ್'}</Text>
            </View>

            {scheme.source?.last_verified_at && (
              <View style={styles.provRow}>
                <Calendar size={14} color="#6B7280" />
                <Text style={styles.provLabel}>ದೃಢೀಕರಣ ದಿನಾಂಕ:</Text>
                <Text style={styles.provValue}>
                  {new Date(scheme.source.last_verified_at).toLocaleDateString('kn-IN', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                  })}
                </Text>
              </View>
            )}

            <View style={styles.provRow}>
              <ShieldCheck size={14} color="#0F6E56" />
              <Text style={styles.provLabel}>ಸ್ಥಿತಿ:</Text>
              <Text style={styles.provStatusVerified}>
                {scheme.source?.crawler_status === 'VERIFIED'
                  ? 'ದೃಢೀಕರಿಸಲಾಗಿದೆ (Verified)'
                  : scheme.source?.crawler_status || 'ಸಕ್ರಿಯ'}
              </Text>
            </View>
          </View>
        </View>

        {/* 7. 💳 ಪಾವತಿ & ಶುಲ್ಕ ವಿವರ (Fee & Payment Transparency) */}
        <View style={styles.feeCard}>
          <View style={styles.feeCardHeader}>
            <Receipt size={18} color="#0F6E56" />
            <Text style={styles.feeCardTitle}>ಪಾವತಿ & ಶುಲ್ಕ ವಿವರ</Text>
          </View>
          <Text style={styles.feeCardSubtitle}>Payment Breakdown & Transparency</Text>

          {scheme.fee_info?.fee_type === 'UNKNOWN' ? (
            <View style={styles.feeUnknownBox}>
              <AlertCircle size={18} color="#D97706" />
              <View style={{ flex: 1 }}>
                <Text style={styles.feeUnknownTitle}>ಶುಲ್ಕದ ವಿವರ ಪರಿಶೀಲನೆಯಲ್ಲಿದೆ</Text>
                <Text style={styles.feeUnknownText}>
                  ಈ ಯೋಜನೆಯ ನಿಖರವಾದ ಶುಲ್ಕ ಮಾಹಿತಿ ಪರಿಶೀಲನೆಯಾಗುವವರೆಗೆ ಆನ್‌ಲೈನ್ ಪಾವತಿ ಲಭ್ಯವಿರುವುದಿಲ್ಲ.
                </Text>
              </View>
            </View>
          ) : (
            <View style={styles.feeTableBox}>
              <View style={styles.feeRow}>
                <Text style={styles.feeLabel}>ಸರ್ಕಾರದ ಅಧಿಕೃತ ಅರ್ಜಿ ಶುಲ್ಕ:</Text>
                <Text style={styles.feeValue}>
                  ₹{scheme.fee_info?.official_fee ?? 0}
                  {scheme.fee_info?.fee_type === 'GOVERNMENT_BORNE' && ' (ಸರ್ಕಾರ ಭರಿಸಿದೆ)'}
                </Text>
              </View>

              <View style={styles.feeRow}>
                <Text style={styles.feeLabel}>KrushiPragya ಸೇವಾ ಶುಲ್ಕ:</Text>
                <Text style={styles.feeValue}>
                  ₹{scheme.fee_info?.krushipragya_service_fee ?? 0}
                </Text>
              </View>

              <View style={styles.feeDivider} />

              <View style={styles.feeRowTotal}>
                <Text style={styles.feeTotalLabel}>ಒಟ್ಟು ಪಾವತಿ (Total):</Text>
                <Text style={styles.feeTotalValue}>
                  ₹{scheme.fee_info?.total_payable ?? scheme.fee_info?.total_amount ?? 0}
                </Text>
              </View>

              <Text style={styles.feeTransparencyNotice}>
                ℹ️ ಪಾರದರ್ಶಕತೆಗಾಗಿ ಶುಲ್ಕಗಳನ್ನು ಪ್ರತ್ಯೇಕವಾಗಿ ತೋರಿಸಲಾಗಿದೆ.
              </Text>

              {scheme.fee_info?.fee_type === 'FREE' && (
                <View style={styles.freeBadgeBox}>
                  <CheckCircle2 size={15} color="#0F6E56" />
                  <Text style={styles.freeBadgeText}>ಈ ಯೋಜನೆಗೆ ಯಾವುದೇ ಪಾವತಿ ಅಗತ್ಯವಿಲ್ಲ.</Text>
                </View>
              )}

              {scheme.fee_info?.fee_source && (
                <Text style={styles.feeSourceNote}>
                  ಶುಲ್ಕ ಮೂಲ: {scheme.fee_info.fee_source}
                </Text>
              )}
            </View>
          )}
        </View>

        <View style={{ height: 110 }} />
      </ScrollView>

      {/* Bottom Sticky CTA */}
      <View style={styles.stickyBottomBar}>
        <TouchableOpacity
          activeOpacity={0.88}
          onPress={() => setPaymentModalVisible(true)}
          disabled={scheme.fee_info?.fee_type === 'UNKNOWN'}
          style={[
            styles.ctaButton,
            scheme.fee_info?.fee_type === 'UNKNOWN' && styles.ctaButtonDisabled,
          ]}
          accessibilityRole="button"
          accessibilityLabel="ಕೃಷಿಪ್ರಜ್ಞಾ ಮೂಲಕ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ"
        >
          <Sparkles size={18} color="#FFFFFF" style={{ marginRight: 8 }} />
          <Text style={styles.ctaButtonText}>
            {scheme.fee_info?.fee_type === 'UNKNOWN'
              ? 'ಶುಲ್ಕ ಪರಿಶೀಲನೆ ಬಾಕಿ ಇದೆ'
              : 'ಕೃಷಿಪ್ರಜ್ಞಾ ಮೂಲಕ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ'}
          </Text>
        </TouchableOpacity>

        {officialUrlAvailable && (
          <TouchableOpacity
            activeOpacity={0.7}
            onPress={handleOpenApplicationUrl}
            style={styles.portalLinkButton}
            accessibilityRole="button"
            accessibilityLabel="ಅಧಿಕೃತ ವೆಬ್ಸೈಟ್ ತೆರೆಯಿರಿ"
          >
            <Text style={styles.portalLinkText}>ಅಥವಾ ಅಧಿಕೃತ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ನೀವೇ ಸಲ್ಲಿಸಿ</Text>
            <ExternalLink size={13} color="#0F6E56" style={{ marginLeft: 4 }} />
          </TouchableOpacity>
        )}
      </View>

      {/* Scheme Application & Payment Modal */}
      <SchemePaymentModal
        visible={paymentModalVisible}
        scheme={scheme}
        user={user}
        onClose={() => setPaymentModalVisible(false)}
        onApplicationCompleted={(app: SchemeApplication) => {
          Alert.alert(
            'ಅರ್ಜಿ ಸಲ್ಲಿಸಲಾಗಿದೆ',
            `ನಿಮ್ಮ ಅರ್ಜಿ ಐಡಿ #${app.id.slice(0, 8)} ಯಶಸ್ವಿಯಾಗಿ ನೋಂದಣಿಯಾಗಿದೆ.`
          );
        }}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  topHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    padding: 6,
    borderRadius: 8,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#111827',
  },
  scrollContent: {
    paddingBottom: 24,
  },
  imageContainer: {
    width: '100%',
    height: 180,
    backgroundColor: '#EAF7EE',
    position: 'relative',
  },
  bannerImage: {
    width: '100%',
    height: '100%',
  },
  imageGradientOverlay: {
    position: 'absolute',
    bottom: 12,
    left: 16,
    right: 16,
  },
  badgeRow: {
    flexDirection: 'row',
    gap: 8,
  },
  introCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginHorizontal: 16,
    marginTop: -12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 5,
    elevation: 2,
  },
  kannadaTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    lineHeight: 26,
    marginBottom: 4,
  },
  englishTitle: {
    fontSize: 13.5,
    fontWeight: '400',
    color: '#6B7280',
    marginBottom: 12,
  },
  metaBox: {
    gap: 6,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  metaIcon: {
    marginRight: 6,
  },
  metaText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#1F2937',
    flex: 1,
  },
  metaTextMuted: {
    fontSize: 12.5,
    fontWeight: '400',
    color: '#6B7280',
    flex: 1,
  },
  provenanceCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 6,
    borderWidth: 1,
    borderColor: '#CDEBD7',
  },
  provenanceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  provenanceTitle: {
    fontSize: 15.5,
    fontWeight: '600',
    color: '#0F6E56',
  },
  provenanceSubtitle: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
    marginBottom: 10,
  },
  provenanceBody: {
    backgroundColor: '#F9FAFB',
    borderRadius: 10,
    padding: 10,
    gap: 8,
  },
  provRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  provLabel: {
    fontSize: 12.5,
    color: '#4B5563',
    fontWeight: '500',
  },
  provValue: {
    fontSize: 12.5,
    color: '#111827',
    fontWeight: '500',
    flex: 1,
  },
  provStatusVerified: {
    fontSize: 12.5,
    color: '#0F6E56',
    fontWeight: '600',
  },
  stickyBottomBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 14,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 8,
    alignItems: 'center',
  },
  ctaButton: {
    backgroundColor: '#0F6E56',
    borderRadius: 12,
    height: 48,
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#0F6E56',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  ctaButtonDisabled: {
    backgroundColor: '#9CA3AF',
  },
  ctaButtonText: {
    color: '#FFFFFF',
    fontSize: 15.5,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  portalLinkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
    paddingVertical: 2,
  },
  portalLinkText: {
    fontSize: 12.5,
    color: '#0F6E56',
    fontWeight: '600',
  },
  feeCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 6,
    borderWidth: 1,
    borderColor: '#CDEBD7',
  },
  feeCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  feeCardTitle: {
    fontSize: 15.5,
    fontWeight: '600',
    color: '#0F6E56',
  },
  feeCardSubtitle: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
    marginBottom: 10,
  },
  feeUnknownBox: {
    backgroundColor: '#FFFBEB',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#FDE68A',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  feeUnknownTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#92400E',
  },
  feeUnknownText: {
    fontSize: 12,
    color: '#B45309',
    marginTop: 2,
    lineHeight: 17,
  },
  feeTableBox: {
    backgroundColor: '#F9FAFB',
    borderRadius: 10,
    padding: 12,
    gap: 8,
  },
  feeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  feeLabel: {
    fontSize: 13,
    color: '#4B5563',
    fontWeight: '500',
  },
  feeValue: {
    fontSize: 13.5,
    color: '#111827',
    fontWeight: '600',
  },
  feeDivider: {
    height: 1,
    backgroundColor: '#E5E7EB',
    marginVertical: 4,
  },
  feeRowTotal: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  feeTotalLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
  },
  feeTotalValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0F6E56',
  },
  feeTransparencyNotice: {
    fontSize: 11,
    color: '#6B7280',
    fontStyle: 'italic',
    marginTop: 4,
  },
  freeBadgeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#EAF7EE',
    padding: 8,
    borderRadius: 8,
    gap: 6,
    marginTop: 4,
  },
  freeBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#0F6E56',
  },
  feeSourceNote: {
    fontSize: 10.5,
    color: '#9CA3AF',
    marginTop: 2,
  },
});
