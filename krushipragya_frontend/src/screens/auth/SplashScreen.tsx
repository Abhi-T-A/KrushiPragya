import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  ImageBackground,
  Dimensions,
} from 'react-native';
import Svg, { Path } from 'react-native-svg';
import { Colors, Spacing, Typography } from '../../constants/theme';

const { width, height } = Dimensions.get('window');

interface SplashScreenProps {
  onFinish?: () => void;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ onFinish }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      if (onFinish) {
        onFinish();
      }
    }, 4000); // 4 full seconds

    return () => clearTimeout(timer);
  }, []);

  return (
    <View style={styles.container}>
      <ImageBackground
        source={require('../../../assets/splash_bg.jpg')}
        style={styles.backgroundImage}
        resizeMode="cover"
      >
        {/* Soft top gradient overlay for text clarity */}
        <View style={styles.gradientOverlay}>
          {/* Top Brand Section */}
          <View style={styles.contentContainer}>
            {/* Custom Clean Dual-Leaf Logo (SVG) */}
            <View style={styles.logoContainer}>
              <Svg width={72} height={72} viewBox="0 0 100 100" fill="none">
                {/* Left Leaf */}
                <Path
                  d="M48 20 C30 25, 15 45, 20 70 C35 75, 52 60, 48 20 Z"
                  fill="#1B8755"
                />
                <Path
                  d="M20 70 Q35 50 48 20"
                  stroke="#A7F3D0"
                  strokeWidth="2.5"
                  fill="none"
                />
                {/* Right Leaf */}
                <Path
                  d="M52 10 C75 18, 88 42, 80 72 C62 76, 46 55, 52 10 Z"
                  fill="#0F6E56"
                />
                <Path
                  d="M80 72 Q64 45 52 10"
                  stroke="#A7F3D0"
                  strokeWidth="2.5"
                  fill="none"
                />
              </Svg>
            </View>

            {/* Title */}
            <Text style={styles.brandTitle}>KRUSHIPRAGYA</Text>

            {/* Kannada Tagline matching reference */}
            <Text style={styles.kannadaLine1}>ನಿಮ್ಮ ಬೆಳೆಗಾಗಿ</Text>
            <Text style={styles.kannadaLine2}>ಬುದ್ಧಿವಂತ ಸಹಾಯಕ</Text>
          </View>

          {/* Bottom Spinner matching reference */}
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
    backgroundColor: 'rgba(255, 255, 255, 0.45)',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: Spacing.xxxl * 1.6,
  },
  contentContainer: {
    alignItems: 'center',
    marginTop: Spacing.xxxl,
    paddingHorizontal: Spacing.lg,
  },
  logoContainer: {
    width: 90,
    height: 90,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.sm,
  },
  brandTitle: {
    fontSize: 26,
    fontWeight: '900',
    color: '#0A4A3A',
    letterSpacing: 2,
    marginBottom: Spacing.xs,
  },
  kannadaLine1: {
    fontSize: 22,
    fontWeight: '700',
    color: '#0F6E56',
    marginTop: 2,
  },
  kannadaLine2: {
    fontSize: 24,
    fontWeight: '800',
    color: '#064E3B',
    marginTop: 2,
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
