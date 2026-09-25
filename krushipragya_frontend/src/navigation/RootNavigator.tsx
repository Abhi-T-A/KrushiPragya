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

// Icons
import {
  Home as HomeIcon,
  Camera as CameraIcon,
  ClipboardList as HistoryIcon,
  CloudSun as WeatherIcon,
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
    </Stack.Navigator>
  );
};

// Nested History Stack
const HistoryStackNavigator = () => {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="ReportList" component={ReportListScreen} />
      <Stack.Screen name="AIResult" component={AIResultScreen} />
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
        tabBarActiveTintColor: Colors.primary,
        tabBarInactiveTintColor: Colors.textSecondary,
        tabBarStyle: {
          backgroundColor: Colors.surface,
          borderTopColor: Colors.border,
          borderTopWidth: 1.5,
          height: 64,
          paddingBottom: 8,
          paddingTop: 6,
          elevation: 8,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: -2 },
          shadowOpacity: 0.08,
          shadowRadius: 6,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '700',
        },
      }}
    >
      {/* 1. Dynamic Home Tab (Adapts to Active Role) */}
      <Tab.Screen
        name="HomeTab"
        component={DynamicHomeScreen}
        options={{
          tabBarLabel: isKn ? 'ಮುಖಪುಟ' : 'Home',
          tabBarIcon: ({ color, focused }) => (
            <HomeIcon size={focused ? 22 : 20} color={color} strokeWidth={focused ? 2.5 : 2} />
          ),
        }}
      />

      {/* 2. Crop Health & AI Scan Tab */}
      <Tab.Screen
        name="ReportTab"
        component={ReportStackNavigator}
        options={{
          tabBarLabel: isKn ? 'ರೋಗ ತಪಾಸಣೆ' : 'AI Health',
          tabBarIcon: ({ color, focused }) => (
            <View style={focused ? styles.activeCamCircle : styles.camCircle}>
              <CameraIcon size={20} color={focused ? '#FFFFFF' : Colors.primary} strokeWidth={2.4} />
            </View>
          ),
        }}
      />

      {/* 3. History & Evidence Ladder Tab */}
      <Tab.Screen
        name="HistoryTab"
        component={HistoryStackNavigator}
        options={{
          tabBarLabel: isKn ? 'ಇತಿಹಾಸ' : 'Reports',
          tabBarIcon: ({ color, focused }) => (
            <HistoryIcon size={focused ? 22 : 20} color={color} strokeWidth={focused ? 2.5 : 2} />
          ),
        }}
      />

      {/* 4. Weather & Spray Advisory Tab */}
      <Tab.Screen
        name="WeatherTab"
        component={WeatherScreen}
        options={{
          tabBarLabel: isKn ? 'ಹವಾಮಾನ' : 'Weather',
          tabBarIcon: ({ color, focused }) => (
            <WeatherIcon size={focused ? 22 : 20} color={color} strokeWidth={focused ? 2.5 : 2} />
          ),
        }}
      />

      {/* 5. Market & Schemes Tab */}
      <Tab.Screen
        name="MarketTab"
        component={MarketScreen}
        options={{
          tabBarLabel: isKn ? 'ಮಾರುಕಟ್ಟೆ' : 'Market',
          tabBarIcon: ({ color, focused }) => (
            <MarketIcon size={focused ? 22 : 20} color={color} strokeWidth={focused ? 2.5 : 2} />
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
    </Stack.Navigator>
  );
};

const styles = StyleSheet.create({
  camCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  activeCamCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
});