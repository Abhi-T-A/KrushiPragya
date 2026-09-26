import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Linking,
} from 'react-native';
import {
  MandiDetailResponse,
  NearbyMandiItem,
  fetchMandiDetail,
  followMandi,
  unfollowMandi,
} from '../../services/marketApi';
import {
  X,
  MapPin,
  ExternalLink,
  Bookmark,
  BookmarkCheck,
  TrendingUp,
  TrendingDown,
  Minus,
  Calendar,
  ShieldCheck,
  ShieldAlert,
} from 'lucide-react-native';

interface MandiDetailModalProps {
  visible: boolean;
  mandi: NearbyMandiItem | null;
  cropId: string | null;
  cropNameKn: string;
  farmerId: string;
  onClose: () => void;
}

export const MandiDetailModal: React.FC<MandiDetailModalProps> = ({
  visible,
  mandi,
  cropId,
  cropNameKn,
  farmerId,
  onClose,
}) => {
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState<MandiDetailResponse | null>(null);
  const [isFollowed, setIsFollowed] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);

  useEffect(() => {
    if (visible && mandi && cropId) {
      loadDetail();
      setIsFollowed(mandi.is_followed);
    } else {
      setDetail(null);
    }
  }, [visible, mandi, cropId]);

  const loadDetail = async () => {
    if (!mandi || !cropId) return;
    try {
      setLoading(true);
      const res = await fetchMandiDetail(mandi.market_id, cropId);
      setDetail(res);
      setIsFollowed(res.is_followed);
    } catch (err) {
      console.warn('Failed to load mandi detail:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleFollow = async () => {
    if (!mandi || followLoading) return;
    try {
      setFollowLoading(true);
      if (isFollowed) {
        await unfollowMandi(mandi.market_id, farmerId);
        setIsFollowed(false);
      } else {
        await followMandi(mandi.market_id, farmerId);
        setIsFollowed(true);
      }
    } catch (err) {
      console.warn('Failed to toggle follow:', err);
    } finally {
      setFollowLoading(false);
    }
  };

  const handleOpenMap = () => {
    if (detail?.market.latitude && detail?.market.longitude) {
      const url = `https://www.google.com/maps/search/?api=1&query=${detail.market.latitude},${detail.market.longitude}`;
      Linking.openURL(url);
    }
  };

  if (!visible || !mandi) return null;

  const intel = detail?.intelligence;
  const history = intel?.history || [];
  const isDemo = intel?.is_seeded || intel?.data_mode === 'DEMO_SEEDED';

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          {/* Header */}
          <View style={styles.header}>
            <View style={{ flex: 1 }}>
              <Text style={styles.mandiTitle}>{mandi.name}</Text>
              <Text style={styles.mandiLocation}>
                {mandi.district}, {mandi.state} • {Math.round(mandi.distance_km)} ಕಿ.ಮೀ ದೂರ
              </Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
              <X size={20} color="#374151" />
            </TouchableOpacity>
          </View>

          {loading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#114B32" />
              <Text style={styles.loadingText}>ದರ ಮಾಹಿತಿ ಲೋಡ್ ಆಗುತ್ತಿದೆ...</Text>
            </View>
          ) : (
            <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollBody}>
              {/* Selected Crop Banner */}
              <View style={styles.cropBanner}>
                <View>
                  <Text style={styles.cropLabel}>ಆಯ್ಕೆಮಾಡಿದ ಬೆಳೆ</Text>
                  <Text style={styles.cropValue}>{cropNameKn}</Text>
                </View>

                <TouchableOpacity
                  activeOpacity={0.8}
                  onPress={handleToggleFollow}
                  disabled={followLoading}
                  style={[styles.followBtn, isFollowed && styles.followedBtn]}
                >
                  {isFollowed ? (
                    <>
                      <BookmarkCheck size={16} color="#114B32" />
                      <Text style={[styles.followBtnText, { color: '#114B32' }]}>ಫಾಲೋ ಮಾಡಲಾಗಿದೆ</Text>
                    </>
                  ) : (
                    <>
                      <Bookmark size={16} color="#4B5563" />
                      <Text style={styles.followBtnText}>ಫಾಲೋ ಮಾಡಿ</Text>
                    </>
                  )}
                </TouchableOpacity>
              </View>

              {/* Latest Price Summary Card */}
              {mandi.latest_price && (
                <View style={styles.priceHeroCard}>
                  <Text style={styles.priceHeroLabel}>ಇಂದಿನ ಅಧಿಕೃತ ದರ</Text>
                  <Text style={styles.priceHeroValue}>
                    ₹{Math.round(parseFloat(mandi.latest_price.min)).toLocaleString('en-IN')} – ₹{Math.round(parseFloat(mandi.latest_price.max)).toLocaleString('en-IN')}
                  </Text>
                  <Text style={styles.priceHeroUnit}>
                    ಪ್ರತಿ {mandi.latest_price.unit === 'quintal' ? '100 ಕೆಜಿ (ಕ್ವಿಂಟಾಲ್)' : mandi.latest_price.unit}
                  </Text>

                  <View style={styles.heroMetaRow}>
                    <View style={styles.metaPill}>
                      <Calendar size={12} color="#4B5563" />
                      <Text style={styles.metaPillText}>ಕೊನೆಯ ನವೀಕರಣ: {mandi.latest_price.date}</Text>
                    </View>

                    {intel?.trend_15d === 'UP' && (
                      <View style={[styles.metaPill, { backgroundColor: '#DCFCE7' }]}>
                        <TrendingUp size={12} color="#15803D" />
                        <Text style={[styles.metaPillText, { color: '#15803D', fontWeight: '700' }]}>
                          15 ದಿನಗಳ ಏರಿಕೆ ({intel.price_change_pct}%)
                        </Text>
                      </View>
                    )}
                    {intel?.trend_15d === 'DOWN' && (
                      <View style={[styles.metaPill, { backgroundColor: '#FEE2E2' }]}>
                        <TrendingDown size={12} color="#B91C1C" />
                        <Text style={[styles.metaPillText, { color: '#B91C1C', fontWeight: '700' }]}>
                          15 ದಿನಗಳ ಇಳಿಕೆ ({intel.price_change_pct}%)
                        </Text>
                      </View>
                    )}
                    {intel?.trend_15d === 'STABLE' && (
                      <View style={[styles.metaPill, { backgroundColor: '#F3F4F6' }]}>
                        <Minus size={12} color="#4B5563" />
                        <Text style={styles.metaPillText}>15 ದಿನಗಳಲ್ಲಿ ಸ್ಥಿರ</Text>
                      </View>
                    )}
                  </View>
                </View>
              )}

              {/* Provenance Notice */}
              {isDemo ? (
                <View style={styles.demoNoticeBox}>
                  <ShieldAlert size={16} color="#92400E" />
                  <Text style={styles.demoNoticeText}>
                    ಇದು ಅಧಿಕೃತ ದತ್ತಾಂಶ ಮಾದರಿಯನ್ನು ಆಧರಿಸಿದ ಡೆಮೊ ಬೆಂಚ್‌ಮಾರ್ಕ್ ದರವಾಗಿದೆ. ಇದು ಲೈವ್ ಸರ್ಕಾರಿ ದತ್ತಾಂಶವಲ್ಲ.
                  </Text>
                </View>
              ) : (
                <View style={styles.verifiedNoticeBox}>
                  <ShieldCheck size={16} color="#15803D" />
                  <Text style={styles.verifiedNoticeText}>
                    ಮೂಲ: {intel?.source_name || 'ಕರ್ನಾಟಕ ಎಪಿಎಂಸಿ ದೈನಂದಿನ ವರದಿ'} (ಪರಿಶೀಲಿತ)
                  </Text>
                </View>
              )}

              {/* 15 Days Price History Section */}
              <View style={styles.historySection}>
                <Text style={styles.historySectionTitle}>ಹಿಂದಿನ 15 ದಿನಗಳ ದರ ಇತಿಹಾಸ</Text>

                {history.length === 0 ? (
                  <Text style={styles.emptyHistoryText}>ಹಿಂದಿನ ದರಗಳು ಲಭ್ಯವಿಲ್ಲ</Text>
                ) : (
                  <View style={styles.historyTable}>
                    <View style={styles.tableHeaderRow}>
                      <Text style={[styles.tableHeaderCol, { flex: 1.2 }]}>ದಿನಾಂಕ</Text>
                      <Text style={[styles.tableHeaderCol, { flex: 1 }]}>ಕನಿಷ್ಠ</Text>
                      <Text style={[styles.tableHeaderCol, { flex: 1 }]}>ಮಾದರಿ</Text>
                      <Text style={[styles.tableHeaderCol, { flex: 1 }]}>ಗರಿಷ್ಠ</Text>
                    </View>

                    {history.map((record, index) => (
                      <View
                        key={record.date + index}
                        style={[styles.tableRow, index % 2 === 1 && styles.tableRowAlt]}
                      >
                        <Text style={[styles.tableCell, { flex: 1.2, fontWeight: '600' }]}>
                          {record.date}
                        </Text>
                        <Text style={[styles.tableCell, { flex: 1, color: '#4B5563' }]}>
                          ₹{Math.round(parseFloat(record.min_price)).toLocaleString('en-IN')}
                        </Text>
                        <Text style={[styles.tableCell, { flex: 1, fontWeight: '700', color: '#111827' }]}>
                          ₹{Math.round(parseFloat(record.modal_price)).toLocaleString('en-IN')}
                        </Text>
                        <Text style={[styles.tableCell, { flex: 1, color: '#166534', fontWeight: '600' }]}>
                          ₹{Math.round(parseFloat(record.max_price)).toLocaleString('en-IN')}
                        </Text>
                      </View>
                    ))}
                  </View>
                )}
              </View>

              {/* Map Action Button */}
              {detail?.market.latitude && detail?.market.longitude && (
                <TouchableOpacity
                  activeOpacity={0.85}
                  onPress={handleOpenMap}
                  style={styles.mapActionBtn}
                >
                  <MapPin size={16} color="#FFFFFF" />
                  <Text style={styles.mapActionBtnText}>ಗೂಗಲ್ ಮ್ಯಾಪ್ಸ್‌ನಲ್ಲಿ ಮಾರುಕಟ್ಟೆ ನೋಡಿ</Text>
                  <ExternalLink size={14} color="#FFFFFF" />
                </TouchableOpacity>
              )}
            </ScrollView>
          )}
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '85%',
    paddingBottom: 24,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  mandiTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  mandiLocation: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  closeBtn: {
    padding: 6,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
  },
  loadingContainer: {
    padding: 40,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 13,
    color: '#6B7280',
  },
  scrollBody: {
    padding: 16,
    gap: 14,
  },
  cropBanner: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  cropLabel: {
    fontSize: 11,
    color: '#6B7280',
  },
  cropValue: {
    fontSize: 16,
    fontWeight: '800',
    color: '#114B32',
    marginTop: 2,
  },
  followBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  followedBtn: {
    backgroundColor: '#EAF7EE',
    borderColor: '#114B32',
  },
  followBtnText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4B5563',
  },
  priceHeroCard: {
    backgroundColor: '#F0FDF4',
    borderWidth: 1.5,
    borderColor: '#BBF7D0',
    borderRadius: 14,
    padding: 16,
    alignItems: 'center',
  },
  priceHeroLabel: {
    fontSize: 12,
    color: '#166534',
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  priceHeroValue: {
    fontSize: 24,
    fontWeight: '800',
    color: '#114B32',
    marginVertical: 4,
  },
  priceHeroUnit: {
    fontSize: 12,
    color: '#166534',
  },
  heroMetaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 12,
    justifyContent: 'center',
  },
  metaPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  metaPillText: {
    fontSize: 11,
    color: '#4B5563',
  },
  demoNoticeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FEF3C7',
    borderWidth: 1,
    borderColor: '#FDE68A',
    borderRadius: 10,
    padding: 10,
  },
  demoNoticeText: {
    flex: 1,
    fontSize: 11,
    color: '#92400E',
    lineHeight: 16,
  },
  verifiedNoticeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F0FDF4',
    borderWidth: 1,
    borderColor: '#BBF7D0',
    borderRadius: 10,
    padding: 10,
  },
  verifiedNoticeText: {
    flex: 1,
    fontSize: 11,
    color: '#166534',
    lineHeight: 16,
  },
  historySection: {
    gap: 10,
    marginTop: 6,
  },
  historySectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111827',
  },
  emptyHistoryText: {
    fontSize: 12,
    color: '#6B7280',
    fontStyle: 'italic',
  },
  historyTable: {
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 10,
    overflow: 'hidden',
  },
  tableHeaderRow: {
    flexDirection: 'row',
    backgroundColor: '#F3F4F6',
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  tableHeaderCol: {
    fontSize: 11,
    fontWeight: '700',
    color: '#4B5563',
  },
  tableRow: {
    flexDirection: 'row',
    paddingVertical: 8,
    paddingHorizontal: 10,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  tableRowAlt: {
    backgroundColor: '#F9FAFB',
  },
  tableCell: {
    fontSize: 12,
    color: '#374151',
  },
  mapActionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#114B32',
    paddingVertical: 12,
    borderRadius: 10,
    marginTop: 6,
  },
  mapActionBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
