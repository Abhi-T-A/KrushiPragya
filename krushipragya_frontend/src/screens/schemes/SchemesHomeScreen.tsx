import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { ArrowLeft, Bookmark } from 'lucide-react-native';
import { useAuth } from '../../context/AuthContext';
import { SchemeItem } from '../../types/schemes';
import { fetchSchemesList, saveScheme, unsaveScheme, API_BASE_URL } from '../../services/schemesApi';
import { checkApiHealth } from '../../services/api';
import { SchemeHero } from '../../components/schemes/SchemeHero';
import { SchemeSearchBar } from '../../components/schemes/SchemeSearchBar';
import {
  SchemeCategoryChips,
  SchemeCategoryKey,
} from '../../components/schemes/SchemeCategoryChips';
import { SchemeCard } from '../../components/schemes/SchemeCard';
import { SchemeLoadingState } from '../../components/schemes/SchemeLoadingState';
import { SchemeErrorState } from '../../components/schemes/SchemeErrorState';
import { SchemeEmptyState } from '../../components/schemes/SchemeEmptyState';

export const SchemesHomeScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const { user } = useAuth();

  const [schemes, setSchemes] = useState<SchemeItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<SchemeCategoryKey>('all');

  const loadSchemes = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setErrorMessage(null);
    console.log('[SCHEMES] loading:', true);

    try {
      const data = await fetchSchemesList(
        {
          state: 'all',
          language: 'kn',
          limit: 50,
        },
        user
      );
      const items = Array.isArray(data?.items)
        ? data.items
        : Array.isArray(data)
        ? (data as any)
        : [];
      console.log('[SCHEMES] schemes count:', items.length);
      setSchemes(items);
    } catch (err: any) {
      console.log('[SCHEMES] error:', err?.message || String(err));
      setErrorMessage('ಯೋಜನೆಗಳನ್ನು ಲೋಡ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ');
    } finally {
      setLoading(false);
      setRefreshing(false);
      console.log('[SCHEMES] loading:', false);
    }
  }, [user]);

  useEffect(() => {
    console.log('[SCHEMES] screen mounted');
    console.log('[SCHEMES] API base URL:', API_BASE_URL);
    checkApiHealth();
    loadSchemes();
  }, [loadSchemes]);

  // Handle bookmark toggle with optimistic state update and backend persistence
  const handleToggleBookmark = async (schemeId: string, currentSaved: boolean) => {
    // Optimistic update
    setSchemes((prev) =>
      prev.map((s) => (s.id === schemeId ? { ...s, is_saved: !currentSaved } : s))
    );

    try {
      if (currentSaved) {
        await unsaveScheme(schemeId, user);
      } else {
        await saveScheme(schemeId, user);
      }
    } catch {
      // Rollback on failure
      setSchemes((prev) =>
        prev.map((s) => (s.id === schemeId ? { ...s, is_saved: currentSaved } : s))
      );
    }
  };

  // Saved schemes count for header badge
  const savedCount = useMemo(() => {
    return schemes.filter((s) => s.is_saved).length;
  }, [schemes]);

  // Filter schemes based on search query and category chips
  const filteredSchemes = useMemo(() => {
    let result = [...schemes];

    // Category filter
    if (selectedCategory !== 'all') {
      result = result.filter((item) => {
        const catLower = (item.category || '').toLowerCase();
        const deptLower = (item.department || '').toLowerCase();
        const titleEnLower = (item.title_en || '').toLowerCase();
        const titleKnLower = (item.title_kn || item.name || '').toLowerCase();
        const descLower = (item.description || '').toLowerCase();

        switch (selectedCategory) {
          case 'state':
            return (
              item.state?.toLowerCase().includes('karnataka') ||
              item.state?.includes('ಕರ್ನಾಟಕ') ||
              deptLower.includes('ಕರ್ನಾಟಕ')
            );
          case 'agriculture':
            return (
              catLower.includes('ಕೃಷಿ') ||
              deptLower.includes('ಕೃಷಿ') ||
              titleEnLower.includes('krishi') ||
              titleEnLower.includes('kisan') ||
              titleKnLower.includes('ಕೃಷಿ')
            );
          case 'crop':
            return (
              catLower.includes('ಬೆಳೆ') ||
              catLower.includes('ಆದಾಯ') ||
              descLower.includes('ಬೆಳೆ') ||
              titleEnLower.includes('crop') ||
              titleKnLower.includes('ಬೆಳೆ')
            );
          case 'subsidy':
            return (
              catLower.includes('ಸಬ್ಸಿಡಿ') ||
              catLower.includes('ಸಿಂಚಾಯಿ') ||
              catLower.includes('ಸೌರ') ||
              descLower.includes('ಸಬ್ಸಿಡಿ') ||
              (item.benefits_summary || '').includes('ಸಬ್ಸಿಡಿ')
            );
          case 'insurance':
            return (
              catLower.includes('ವಿಮೆ') ||
              titleEnLower.includes('bima') ||
              titleKnLower.includes('ವಿಮೆ') ||
              descLower.includes('ವಿಮೆ')
            );
          default:
            return true;
        }
      });
    }

    // Search filter
    if (searchQuery.trim().length > 0) {
      const q = searchQuery.trim().toLowerCase();
      result = result.filter((item) => {
        const name = (item.name || '').toLowerCase();
        const titleKn = (item.title_kn || '').toLowerCase();
        const titleEn = (item.title_en || '').toLowerCase();
        const dept = (item.department || '').toLowerCase();
        const cat = (item.category || '').toLowerCase();
        const desc = (item.description || '').toLowerCase();

        return (
          name.includes(q) ||
          titleKn.includes(q) ||
          titleEn.includes(q) ||
          dept.includes(q) ||
          cat.includes(q) ||
          desc.includes(q)
        );
      });
    }

    return result;
  }, [schemes, selectedCategory, searchQuery]);

  const renderHeader = () => (
    <View>
      {/* Hero Card */}
      <SchemeHero />

      {/* Search Input */}
      <SchemeSearchBar
        value={searchQuery}
        onChangeText={setSearchQuery}
        placeholder="ಯೋಜನೆ ಹುಡುಕಿ..."
      />

      {/* Category Chips */}
      <SchemeCategoryChips
        selectedKey={selectedCategory}
        onSelect={setSelectedCategory}
      />

      {/* Results Count Header */}
      {!loading && !errorMessage && (
        <View style={styles.resultsHeaderRow}>
          <Text style={styles.resultsCountText}>
            ಲಭ್ಯವಿರುವ ಯೋಜನೆಗಳು ({filteredSchemes.length})
          </Text>
        </View>
      )}
    </View>
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />

      {/* Screen Top Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="ಹಿಂದೆ ಹೋಗಿ"
          onPress={() => {
            if (navigation.canGoBack()) {
              navigation.goBack();
            } else {
              navigation.navigate('HomeTab');
            }
          }}
          style={styles.backButton}
        >
          <ArrowLeft size={22} color="#1F2937" />
        </TouchableOpacity>

        <View style={styles.headerTitleBox}>
          <Text style={styles.headerTitle}>ಯೋಜನೆಗಳು</Text>
          <Text style={styles.headerSubtitle}>Government Schemes</Text>
        </View>

        {/* Right Saved Schemes Button */}
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="ನಾನು ಉಳಿಸಿದ ಯೋಜನೆಗಳು"
          onPress={() => navigation.navigate('SavedSchemes')}
          style={styles.savedNavButton}
        >
          <Bookmark size={20} color="#0F6E56" strokeWidth={2} />
          {savedCount > 0 && (
            <View style={styles.savedBadge}>
              <Text style={styles.savedBadgeText}>{savedCount}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      {/* Main Content Area */}
      {loading ? (
        <ScrollView contentContainerStyle={styles.listContent} showsVerticalScrollIndicator={false}>
          {renderHeader()}
          <SchemeLoadingState message="ಸರ್ಕಾರಿ ಯೋಜನೆಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ..." />
        </ScrollView>
      ) : errorMessage ? (
        <ScrollView contentContainerStyle={styles.listContent} showsVerticalScrollIndicator={false}>
          {renderHeader()}
          <SchemeErrorState
            title={errorMessage}
            subtitle="ದಯವಿಟ್ಟು ನಿಮ್ಮ ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕವನ್ನು ಪರಿಶೀಲಿಸಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ."
            onRetry={() => loadSchemes(false)}
          />
        </ScrollView>
      ) : (
        <FlatList
          data={filteredSchemes}
          keyExtractor={(item) => item.id}
          ListHeaderComponent={renderHeader}
          renderItem={({ item }) => (
            <SchemeCard
              scheme={item}
              onPress={() => navigation.navigate('SchemeDetails', { schemeId: item.id })}
              onToggleBookmark={() => handleToggleBookmark(item.id, item.is_saved)}
            />
          )}
          ListEmptyComponent={
            <SchemeEmptyState
              type={searchQuery.length > 0 || selectedCategory !== 'all' ? 'search' : 'default'}
              onButtonPress={() => {
                setSearchQuery('');
                setSelectedCategory('all');
              }}
            />
          }
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => loadSchemes(true)}
              colors={['#0F6E56']}
              tintColor="#0F6E56"
            />
          }
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
        />
      )}
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
    marginRight: 6,
    borderRadius: 8,
  },
  headerTitleBox: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  headerSubtitle: {
    fontSize: 12,
    fontWeight: '400',
    color: '#6B7280',
    marginTop: 1,
  },
  savedNavButton: {
    padding: 8,
    borderRadius: 10,
    backgroundColor: '#EAF7EE',
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  savedBadge: {
    position: 'absolute',
    top: -4,
    right: -4,
    backgroundColor: '#0F6E56',
    borderRadius: 9,
    minWidth: 18,
    height: 18,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
    borderWidth: 1.5,
    borderColor: '#FFFFFF',
  },
  savedBadgeText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '700',
  },
  mainContainer: {
    flex: 1,
  },
  listContent: {
    paddingBottom: 24,
  },
  resultsHeaderRow: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 4,
  },
  resultsCountText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#4B5563',
  },
});
