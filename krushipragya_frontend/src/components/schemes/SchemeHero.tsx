import React from 'react';
import { View, Text, StyleSheet, Image, Dimensions } from 'react-native';

const SCREEN_WIDTH = Dimensions.get('window').width;

export const SchemeHero: React.FC = () => {
  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <View style={styles.contentRow}>
          {/* Left Text Content */}
          <View style={styles.textContainer}>
            <View style={styles.pillBadge}>
              <Text style={styles.pillText}>ಕೃಷಿ ಕಲ್ಯಾಣ • Schemes</Text>
            </View>
            <Text style={styles.title}>
              {'ನಿಮಗಾಗಿ ಸರ್ಕಾರಿ\nಯೋಜನೆಗಳು'}
            </Text>
            <Text style={styles.subtitle}>
              {'ನಿಮ್ಮ ಬೆಳೆ, ಸ್ಥಳ ಮತ್ತು ಕೃಷಿ ಮಾಹಿತಿಗೆ ಸಂಬಂಧಿಸಿದ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಿ.'}
            </Text>
          </View>

          {/* Right Image */}
          <View style={styles.imageContainer}>
            <Image
              source={require('../../../assets/schemes_hero.jpg')}
              style={styles.heroImage}
              resizeMode="cover"
            />
          </View>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 6,
  },
  card: {
    backgroundColor: '#EAF7EE',
    borderRadius: 18,
    borderWidth: 1,
    borderColor: '#CDEBD7',
    padding: 16,
    shadowColor: '#0F6E56',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
    overflow: 'hidden',
  },
  contentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  textContainer: {
    flex: 1,
    paddingRight: 10,
  },
  pillBadge: {
    backgroundColor: '#D1F0DC',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  pillText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#0F6E56',
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#114B32',
    lineHeight: 26,
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 12.5,
    fontWeight: '400',
    color: '#374151',
    lineHeight: 18,
  },
  imageContainer: {
    width: 108,
    height: 108,
    borderRadius: 14,
    overflow: 'hidden',
    borderWidth: 1.5,
    borderColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  heroImage: {
    width: '100%',
    height: '100%',
  },
});
