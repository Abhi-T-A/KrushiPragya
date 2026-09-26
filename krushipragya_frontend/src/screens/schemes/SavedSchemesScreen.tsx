import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { ArrowLeft, BookmarkCheck } from 'lucide-react-native';
import { useAuth } from '../../context/AuthContext';
import { SchemeItem } from '../../types/schemes';
import { fetchSavedSchemes, unsaveScheme } from '../../services/schemesApi';
import { SchemeCard } from '../../components/schemes/SchemeCard';
import { SchemeEmptyState } from '../../components/schemes/SchemeEmptyState';
import { SchemeLoadingState } from '../../components/schemes/SchemeLoadingState';
import { SchemeErrorState } from '../../components/schemes/SchemeErrorState';

export const SavedSchemesScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const { user } = useAuth();

  const [savedSchemes, setSavedSchemes] = useState<SchemeItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadSavedSchemes = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setErrorMessage(null);

    try {
      const items = await fetchSavedSchemes(user, 'kn');
      setSavedSchemes(items);
    } catch {
      setErrorMessage('ಉಳಿಸಿದ ಯೋಜನೆಗಳನ್ನು ಲೋಡ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user]);

  useEffect(() => {
    loadSavedSchemes();
  }, [loadSavedSchemes]);

  // When returning to this screen, re-sync with backend
  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      loadSavedSchemes(true);
    });
    return unsubscribe;
  }, [navigation, loadSavedSchemes]);

  const handleUnsave = async (schemeId: string) => {
    // Optimistic removal from list
    const previous = [...savedSchemes];
    setSavedSchemes((prev) => prev.filter((s) => s.id !== schemeId));

    try {
      await unsaveScheme(schemeId, user);
    } catch {
      // Rollback on failure
      setSavedSchemes(previous);
    }
  };

  const renderHeader = () => (
    <View style={styles.explanatoryCard}>
      <View style={styles.explanatoryIconBox}>
        <BookmarkCheck size={24} color="#0F6E56" strokeWidth={2.2} />
      </View>
      <View style={styles.explanatoryTextBox}>
        <Text style={styles.explanatoryTitle}>ನೀವು ಉಳಿಸಿದ ಯೋಜನೆಗಳು</Text>
        <Text style={styles.explanatorySubtitle}>
          ನಿಮಗೆ ಅಗತ್ಯವಿರುವ ಯೋಜನೆಗಳನ್ನು ಇಲ್ಲಿ ಮತ್ತೆ ನೋಡಬಹುದು.
        </Text>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />

      {/* Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity
          onPress={() => navigation.goBack()}
          style={styles.backButton}
          accessibilityRole="button"
          accessibilityLabel="ಹಿಂದೆ ಹೋಗಿ"
        >
          <ArrowLeft size={22} color="#1F2937" />
        </TouchableOpacity>

        <View style={styles.headerTitleBox}>
          <Text style={styles.headerTitle}>ನಾನು ಉಳಿಸಿದ ಯೋಜನೆಗಳು</Text>
          <Text style={styles.headerSubtitle}>Saved Schemes</Text>
        </View>

        <View style={{ width: 36 }} />
      </View>

      {/* Content */}
      {loading ? (
        <View style={styles.mainContainer}>
          {renderHeader()}
          <SchemeLoadingState message="ಉಳಿಸಿದ ಯೋಜನೆಗಳನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ..." />
        </View>
      ) : errorMessage ? (
        <View style={styles.mainContainer}>
          {renderHeader()}
          <SchemeErrorState
            title={errorMessage}
            subtitle="ದಯವಿಟ್ಟು ನಿಮ್ಮ ನೆಟ್‌ವರ್ಕ್ ಪರಿಶೀಲಿಸಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ."
            onRetry={() => loadSavedSchemes(false)}
          />
        </View>
      ) : (
        <FlatList
          data={savedSchemes}
          keyExtractor={(item) => item.id}
          ListHeaderComponent={savedSchemes.length > 0 ? renderHeader : null}
          renderItem={({ item }) => (
            <SchemeCard
              scheme={item}
              onPress={() => navigation.navigate('SchemeDetails', { schemeId: item.id })}
              onToggleBookmark={() => handleUnsave(item.id)}
            />
          )}
          ListEmptyComponent={
            <SchemeEmptyState
              type="saved"
              onButtonPress={() => navigation.navigate('SchemesHome')}
            />
          }
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => loadSavedSchemes(true)}
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
    borderRadius: 8,
  },
  headerTitleBox: {
    flex: 1,
    marginLeft: 6,
  },
  headerTitle: {
    fontSize: 17.5,
    fontWeight: '700',
    color: '#111827',
  },
  headerSubtitle: {
    fontSize: 12,
    fontWeight: '400',
    color: '#6B7280',
    marginTop: 1,
  },
  mainContainer: {
    flex: 1,
  },
  listContent: {
    paddingBottom: 24,
  },
  explanatoryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#EAF7EE',
    borderRadius: 14,
    marginHorizontal: 16,
    marginTop: 14,
    marginBottom: 8,
    padding: 14,
    borderWidth: 1,
    borderColor: '#CDEBD7',
  },
  explanatoryIconBox: {
    width: 44,
    height: 44,
    borderRadius: 10,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  explanatoryTextBox: {
    flex: 1,
  },
  explanatoryTitle: {
    fontSize: 15.5,
    fontWeight: '600',
    color: '#114B32',
    marginBottom: 2,
  },
  explanatorySubtitle: {
    fontSize: 12.5,
    fontWeight: '400',
    color: '#374151',
    lineHeight: 18,
  },
});
