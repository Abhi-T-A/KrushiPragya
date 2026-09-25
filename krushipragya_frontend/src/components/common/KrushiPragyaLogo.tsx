import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Path, Circle } from 'react-native-svg';

interface KrushiPragyaLogoProps {
  size?: number;
  showText?: boolean;
}

export const KrushiPragyaLogo: React.FC<KrushiPragyaLogoProps> = ({
  size = 100,
  showText = true,
}) => {
  const scale = size / 100;

  return (
    <View style={styles.container}>
      {/* Exact Vector Emblem of your Logo */}
      <Svg width={size} height={size * 0.85} viewBox="0 0 100 85" fill="none">
        {/* Golden Ochre / Tan Sun Circle at Top Center */}
        <Circle cx="50" cy="18" r="10.5" fill="#D49A58" />

        {/* Left Dark Emerald Leaf */}
        <Path
          d="M48 37 C42 48 33 58 19 60 C18 43 27 28 41 23 C48 20 49 26 48 37 Z"
          fill="#1C4B38"
        />

        {/* Right Olive Green Leaf */}
        <Path
          d="M52 37 C58 48 67 58 81 60 C82 43 73 28 59 23 C52 20 51 26 52 37 Z"
          fill="#5B8749"
        />
      </Svg>

      {/* Official Typography & Tagline */}
      {showText && (
        <View style={styles.textContainer}>
          <Text style={[styles.title, { fontSize: 28 * scale }]}>
            <Text style={{ color: '#1C4B38' }}>Krushi</Text>
            <Text style={{ color: '#5B8749' }}>Pragya</Text>
          </Text>
          <Text style={[styles.tagline, { fontSize: 10 * scale }]} numberOfLines={1}>
            FARM  •  LEARN  •  GROW
          </Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
  },
  textContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
    width: '100%',
  },
  title: {
    fontWeight: '800',
    letterSpacing: 0.5,
    textAlign: 'center',
  },
  tagline: {
    fontWeight: '700',
    color: '#3B4E43',
    letterSpacing: 2,
    marginTop: 4,
    textAlign: 'center',
  },
});
