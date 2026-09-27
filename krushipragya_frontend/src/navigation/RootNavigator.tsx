import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useLanguage } from '../context/LanguageContext';
import { useAuth } from '../context/AuthContext';
import { Colors, Typography, BorderRadius, Spacing } from '../constants/theme';

// Screens
import { HomeScreen } from '../screens/home/HomeScreen';
import { ExpertQueueScreen } from '../screens/expert/ExpertQueueScreen';
import { GovtPortalScreen } from '../screens/govt/GovtPortalScreen';
import { TraderMarketScreen } from '../screens/market/TraderMarketScreen';
import { CommunityHubScreen } from '../screens/community/CommunityHubScreen';

import { CropSelectScreen } from '../screens/report/CropSelectScreen';
import { CameraCaptureScreen } from '../screens/report/CameraCaptureScreen';
import { PreviewSubmitScreen } from '../screens/report/PreviewSubmitScreen';
import { AIResultScreen } from '../screens/report/AIResultScreen';
import { ReportListScreen } from '../screens/history/ReportListScreen';
import { WeatherScreen } from '../screens/weather/WeatherScreen';
import { MarketScreen } from '../screens/market/MarketScreen';
import { ProfileScreen } from '../screens/profile/ProfileScreen';
import { AdvisoryScreen } from '../screens/advisory/AdvisoryScreen';

// Government Schemes Screens
import { SchemesHomeScreen } from '../screens/schemes/SchemesHomeScreen';
import { SchemeDetailsScreen } from '../screens/schemes/SchemeDetailsScreen';
import { SavedSchemesScreen } from '../screens/schemes/SavedSchemesScreen';

// Icons
import {
  Home as HomeIcon,
  Camera as CameraIcon,
  Landmark as SchemesIcon,
  Sprout as AdvisoryIcon,
  TrendingUp as MarketIcon,
} from 'lucide-react-native';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

// Nested Report Stack
const ReportStackNavigator = () => {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="CropSelect" component={CropSelectScreen} />
      <Stack.Screen name="CameraCapture" component={CameraCaptureScreen} />
      <Stack.Screen name="PreviewSubmit" component={PreviewSubmitScreen} />
      <Stack.Screen name="AIResult" component={AIResultScreen} />
      <Stack.Screen name="ReportList" component={ReportListScreen} />
    </Stack.Navigator>
  );
};

// Nested Schemes Stack (Government Schemes / ಯೋಜನೆಗಳು)
const SchemesStackNavigator = () => {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }} initialRouteName="SchemesHome">
      <Stack.Screen name="SchemesHome" component={SchemesHomeScreen} />
      <Stack.Screen name="SchemeDetails" component={SchemeDetailsScreen} />
      <Stack.Screen name="SavedSchemes" component={SavedSchemesScreen} />
    </Stack.Navigator>
  );
};

// Dynamic Home Screen Resolver based on active demo role
const DynamicHomeScreen = (props: any) => {
  const { user } = useAuth();

  switch (user?.role) {
    case 'expert':
      return <ExpertQueueScreen {...props} />;
    case 'officer':
      return <GovtPortalScreen {...props} />;
    case 'buyer':
      return <TraderMarketScreen {...props} />;
    case 'community':
    case 'village_node':
      return <CommunityHubScreen {...props} />;
    case 'farmer':
    default:
      return <HomeScreen {...props} />;
  }
};

// 5 Bottom Tabs Navigator
const BottomTabs = () => {
  const { language } = useLanguage();
  const isKn = language === 'kn';

  return (
    <Tab.Navigator
      initialRouteName="HomeTab"
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: '#114B32',
        tabBarInactiveTintColor: '#4B5563',
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
          borderTopColor: '#E5E7EB',
          borderTopWidth: 1,
          height: 64,
          paddingBottom: 8,
          paddingTop: 6,
          elevation: 6,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: -2 },
          shadowOpacity: 0.05,
          shadowRadius: 5,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
          marginTop: 2,
        },
      }}
    >
      {/* 1. Home Tab */}
      <Tab.Screen
        name="HomeTab"
        component={DynamicHomeScreen}
        options={{
          tabBarLabel: isKn ? 'ಮುಖಪುಟ' : 'Home',
          tabBarIcon: ({ color, focused }) => (
            <HomeIcon size={20} color={color} strokeWidth={focused ? 2.3 : 1.8} />
          ),
        }}
      />

      {/* 2. Market Tab */}
      <Tab.Screen
        name="MarketTab"
        component={MarketScreen}
        options={{
          tabBarLabel: isKn ? 'ಮಾರುಕಟ್ಟೆ' : 'Market',
          tabBarIcon: ({ color, focused }) => (
            <MarketIcon size={20} color={color} strokeWidth={focused ? 2.3 : 1.8} />
          ),
        }}
      />

      {/* 3. Crop Health & AI Scan Tab (Center) */}
      <Tab.Screen
        name="ReportTab"
        component={ReportStackNavigator}
        options={{
          tabBarLabel: isKn ? 'ಬೆಳೆ ಆರೋಗ್ಯ' : 'Crop Health',
          tabBarIcon: ({ color, focused }) => (
            <View style={focused ? styles.activeCamPill : styles.camPill}>
              <CameraIcon size={19} color={focused ? '#114B32' : '#4B5563'} strokeWidth={focused ? 2.3 : 1.8} />
            </View>
          ),
        }}
      />

      {/* 4. Advisory Tab (ಸಲಹೆ) */}
      <Tab.Screen
        name="AdvisoryTab"
        component={AdvisoryScreen}
        options={{
          tabBarLabel: isKn ? 'ಸಲಹೆ' : 'Advisory',
          tabBarIcon: ({ color, focused }) => (
            <AdvisoryIcon size={20} color={color} strokeWidth={focused ? 2.3 : 1.8} />
          ),
        }}
      />

      {/* 5. Government Schemes Tab */}
      <Tab.Screen
        name="SchemesTab"
        component={SchemesStackNavigator}
        options={{
          tabBarLabel: isKn ? 'ಯೋಜನೆಗಳು' : 'Schemes',
          tabBarIcon: ({ color, focused }) => (
            <SchemesIcon size={20} color={color} strokeWidth={focused ? 2.3 : 1.8} />
          ),
        }}
      />
    </Tab.Navigator>
  );
};

// Root Stack Navigator
export const RootNavigator = () => {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="MainTabs" component={BottomTabs} />
      <Stack.Screen name="Profile" component={ProfileScreen} />
      <Stack.Screen name="WeatherDetails" component={WeatherScreen} />
      <Stack.Screen name="WeatherTab" component={AdvisoryScreen} />
      <Stack.Screen name="AdvisoryTab" component={AdvisoryScreen} />
      <Stack.Screen name="HistoryTab" component={SchemesStackNavigator} />
    </Stack.Navigator>
  );
};

const styles = StyleSheet.create({
  camPill: {
    width: 48,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  activeCamPill: {
    width: 48,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#EAF7EE',
    alignItems: 'center',
    justifyContent: 'center',
  },
});