import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  ImageBackground,
  Dimensions,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { KrushiPragyaLogo } from '../../components/common/KrushiPragyaLogo';
import { Colors, Spacing, Typography } from '../../constants/theme';

const { width, height } = Dimensions.get('window');

interface SplashScreenProps {
  onFinish?: () => void;
  onReturningUser?: () => void;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ onFinish, onReturningUser }) => {
  useEffect(() => {
    let isMounted = true;
    const checkUserStatus = async () => {
      try {
        const isDone = await AsyncStorage.getItem('krushi_profile_setup_done');
        const timer = setTimeout(() => {
          if (!isMounted) return;
          if (isDone === 'true' && onReturningUser) {
            onReturningUser();
          } else if (onFinish) {
            onFinish();
          }
        }, 2800);
        return () => clearTimeout(timer);
      } catch {
        const timer = setTimeout(() => {
          if (!isMounted) return;
          if (onFinish) {
            onFinish();
          }
        }, 2800);
        return () => clearTimeout(timer);
      }
    };

    checkUserStatus();

    return () => {
      isMounted = false;
    };
  }, [onFinish, onReturningUser]);

  return (
    <View style={styles.container}>
      <ImageBackground
        source={require('../../../assets/splash_bg.jpg')}
        style={styles.backgroundImage}
        resizeMode="cover"
      >
        {/* Soft elegant overlay */}
        <View style={styles.gradientOverlay}>
          {/* Top Brand Section with EXACT Logo */}
          <View style={styles.contentContainer}>
            <View style={styles.logoCard}>
              <KrushiPragyaLogo size={130} showText={true} />
            </View>

            {/* Kannada Taglines */}
            <View style={styles.taglineBox}>
              <Text style={styles.kannadaLine1}>ನಿಮ್ಮ ಬೆಳೆಗಾಗಿ</Text>
              <Text style={styles.kannadaLine2}>ಬುದ್ಧಿವಂತ ಸಹಾಯಕ</Text>
            </View>
          </View>

          {/* Bottom Spinner */}
          <View style={styles.bottomContainer}>
            <ActivityIndicator size="large" color="#FFFFFF" />
            <Text style={styles.loadingText}>Loading...</Text>
          </View>
        </View>
      </ImageBackground>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F6E56',
  },
  backgroundImage: {
    width: width,
    height: height,
    flex: 1,
  },
  gradientOverlay: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.48)',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: Spacing.xxxl * 1.5,
  },
  contentContainer: {
    alignItems: 'center',
    marginTop: Spacing.xxxl,
    paddingHorizontal: Spacing.lg,
  },
  logoCard: {
    backgroundColor: '#FBF9F4',
    paddingVertical: Spacing.xl,
    paddingHorizontal: Spacing.xxl + 4,
    borderRadius: 28,
    borderWidth: 1.5,
    borderColor: '#E3DFC8',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 4,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 280,
  },
  taglineBox: {
    alignItems: 'center',
    marginTop: Spacing.lg,
  },
  kannadaLine1: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1C4B38',
    marginTop: 2,
    textShadowColor: 'rgba(255, 255, 255, 0.8)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  kannadaLine2: {
    fontSize: 25,
    fontWeight: '900',
    color: '#064E3B',
    marginTop: 2,
    textShadowColor: 'rgba(255, 255, 255, 0.8)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  bottomContainer: {
    alignItems: 'center',
    gap: Spacing.xs,
    marginBottom: Spacing.xl,
  },
  loadingText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 1.5,
    textShadowColor: 'rgba(0, 0, 0, 0.7)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
});
