export const Colors = {
  // Brand
  primary: '#0F6E56', // Teal - Rural friendly primary
  primaryLight: '#E1F5EE', // Subtle green tint
  primaryDark: '#0A4A3A',
  
  // Trust & Provenance
  trustPurple: '#534AB7', // Core Trust layer purple
  trustPurpleLight: '#EEEDFE', // Provenance drawer background
  
  // Status & Alerts
  unverified: '#993C1D',
  unverifiedBg: '#FAECE7',
  
  aiAnalysed: '#854F0B', // Amber
  aiAnalysedBg: '#FAEEDA',
  
  corroborated: '#185FA5', // Blue
  corroboratedBg: '#E6F1FB',
  
  expertVerified: '#3B6D11', // Green
  expertVerifiedBg: '#EAF3DE',
  
  alertHigh: '#A32D2D',
  alertHighBg: '#FCEBEB',
  
  alertMedium: '#854F0B',
  alertMediumBg: '#FAEEDA',
  
  alertLow: '#3B6D11',
  alertLowBg: '#EAF3DE',
  
  // Neutrals
  background: '#F1EFE8', // Soft eye-friendly background
  surface: '#FFFFFF',
  surfaceSubtle: '#F8F7F4',
  border: '#E3E0D8',
  borderDark: '#CCC8BD',
  
  textPrimary: '#2C2C2A',
  textSecondary: '#5F5E5A',
  textMuted: '#888680',
  textWhite: '#FFFFFF',
  
  // Accent & Actions
  accentGold: '#D97706',
};

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
};

export const BorderRadius = {
  sm: 6,
  md: 10,
  lg: 14,
  xl: 20,
  full: 9999,
};

export const Typography = {
  display: {
    fontSize: 24,
    fontWeight: '700' as const,
    lineHeight: 32,
  },
  title1: {
    fontSize: 20,
    fontWeight: '700' as const,
    lineHeight: 28,
  },
  title2: {
    fontSize: 17,
    fontWeight: '600' as const,
    lineHeight: 24,
  },
  bodyLarge: {
    fontSize: 15,
    fontWeight: '500' as const,
    lineHeight: 22,
  },
  body: {
    fontSize: 14,
    fontWeight: '400' as const,
    lineHeight: 20,
  },
  label: {
    fontSize: 12,
    fontWeight: '600' as const,
    lineHeight: 16,
  },
  caption: {
    fontSize: 11,
    fontWeight: '400' as const,
    lineHeight: 14,
  },
};
