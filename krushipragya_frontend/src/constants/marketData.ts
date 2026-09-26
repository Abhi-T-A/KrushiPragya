/**
 * Market Constants: Supported 7 crops with local images, regional location presets, and units.
 */
import { ImageSourcePropType } from 'react-native';

export interface CropMeta {
  code: string;
  nameKn: string;
  nameEn: string;
  image: ImageSourcePropType;
  defaultUnit: string;
}

export const SUPPORTED_MARKET_CROPS: Record<string, CropMeta> = {
  arecanut: {
    code: 'arecanut',
    nameKn: 'ಅಡಿಕೆ',
    nameEn: 'Arecanut',
    image: require('../../assets/crops/arecanut.jpg'),
    defaultUnit: 'quintal',
  },
  paddy: {
    code: 'paddy',
    nameKn: 'ಭತ್ತ',
    nameEn: 'Paddy',
    image: require('../../assets/crops/paddy.jpg'),
    defaultUnit: 'quintal',
  },
  coconut: {
    code: 'coconut',
    nameKn: 'ತೆಂಗು',
    nameEn: 'Coconut',
    image: require('../../assets/crops/coconut.jpg'),
    defaultUnit: '1000 nuts',
  },
  black_pepper: {
    code: 'black_pepper',
    nameKn: 'ಕಾಳುಮೆಣಸು',
    nameEn: 'Black Pepper',
    image: require('../../assets/crops/black_pepper.jpg'),
    defaultUnit: 'kg',
  },
  cardamom: {
    code: 'cardamom',
    nameKn: 'ಏಲಕ್ಕಿ',
    nameEn: 'Cardamom',
    image: require('../../assets/crops/cardamom.jpg'),
    defaultUnit: 'kg',
  },
  turmeric: {
    code: 'turmeric',
    nameKn: 'ಅರಿಶಿನ',
    nameEn: 'Turmeric',
    image: require('../../assets/crops/turmeric.jpg'),
    defaultUnit: 'quintal',
  },
  ginger: {
    code: 'ginger',
    nameKn: 'ಶುಂಠಿ',
    nameEn: 'Ginger',
    image: require('../../assets/crops/ginger.jpg'),
    defaultUnit: 'quintal',
  },
};

export interface LocationPreset {
  id: string;
  nameKn: string;
  nameEn: string;
  latitude: number;
  longitude: number;
  districtKn: string;
}

export const KARNATAKA_LOCATION_PRESETS: LocationPreset[] = [
  { id: 'ujire', nameKn: 'ಉಜಿರೆ (ಬೆಳ್ತಂಗಡಿ)', nameEn: 'Ujire (Belthangady)', latitude: 13.0039, longitude: 75.3216, districtKn: 'ದಕ್ಷಿಣ ಕನ್ನಡ' },
  { id: 'mangalore', nameKn: 'ಮಂಗಳೂರು', nameEn: 'Mangalore', latitude: 12.9141, longitude: 74.8560, districtKn: 'ದಕ್ಷಿಣ ಕನ್ನಡ' },
  { id: 'puttur', nameKn: 'ಪುತ್ತೂರು', nameEn: 'Puttur', latitude: 12.7667, longitude: 75.2000, districtKn: 'ದಕ್ಷಿಣ ಕನ್ನಡ' },
  { id: 'shivamogga', nameKn: 'ಶಿವಮೊಗ್ಗ', nameEn: 'Shivamogga', latitude: 13.9299, longitude: 75.5681, districtKn: 'ಶಿವಮೊಗ್ಗ' },
  { id: 'sagar', nameKn: 'ಸಾಗರ', nameEn: 'Sagar', latitude: 14.1667, longitude: 75.0333, districtKn: 'ಶಿವಮೊಗ್ಗ' },
  { id: 'sirsi', nameKn: 'ಶಿರಸಿ', nameEn: 'Sirsi', latitude: 14.6195, longitude: 74.8510, districtKn: 'ಉತ್ತರ ಕನ್ನಡ' },
  { id: 'bengaluru', nameKn: 'ಬೆಂಗಳೂರು', nameEn: 'Bengaluru', latitude: 12.9716, longitude: 77.5946, districtKn: 'ಬೆಂಗಳೂರು' },
  { id: 'ballari', nameKn: 'ಬಳ್ಳಾರಿ', nameEn: 'Ballari', latitude: 15.1394, longitude: 76.9214, districtKn: 'ಬಳ್ಳಾರಿ' },
];
