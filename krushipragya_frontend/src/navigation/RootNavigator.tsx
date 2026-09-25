import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useLanguage } from '../context/LanguageContext';
import { Colors, Typography, BorderRadius, Spacing } from '../constants/theme';

// Screens
import { HomeScreen } from '../screens/home/HomeScreen';
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

// 5 Bottom Tabs Navigator
const BottomTabs = () => {
  const { language } = useLanguage();

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
          height: 68,
          paddingBottom: 10,
          paddingTop: 8,
          elevation: 8,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: -2 },
          shadowOpacity: 0.08,
          shadowRadius: 6,
        },
        tabBarLabelStyle: {
          ...Typography.caption,
          fontSize: 11,
          fontWeight: '700',
        },
      }}
    >
      {/* 1. Home Tab */}
      <Tab.Screen
        name="HomeTab"
        component={HomeScreen}
        options={{
          tabBarLabel: language === 'kn' ? 'ಮುಖಪುಟ' : 'Home',
          tabBarIcon: ({ color, focused }) => (
            <HomeIcon color={color} size={focused ? 24 : 22} strokeWidth={focused ? 2.5 : 2} />
          ),
        }}
      />

      {/* 2. Weather Tab */}
      <Tab.Screen
        name="WeatherTab"
        component={WeatherScreen}
        options={{
          tabBarLabel: language === 'kn' ? 'ಹವಾಮಾನ' : 'Weather',
          tabBarIcon: ({ color, focused }) => (
            <WeatherIcon color={color} size={focused ? 24 : 22} strokeWidth={focused ? 2.5 : 2} />
          ),
        }}
      />

      {/* 3. CENTER CAMERA BUTTON (Report Problem) */}
      <Tab.Screen
        name="ReportTab"
        component={ReportStackNavigator}
        options={{
          tabBarLabel: '',
          tabBarIcon: () => (
            <View style={styles.centerCameraFab}>
              <CameraIcon color={Colors.textWhite} size={26} strokeWidth={2.4} />
            </View>
          ),
        }}
      />

      {/* 4. Status / Reports History Tab */}
      <Tab.Screen
        name="HistoryTab"
        component={HistoryStackNavigator}
        options={{
          tabBarLabel: language === 'kn' ? 'ಸ್ಥಿತಿ' : 'Status',
          tabBarIcon: ({ color, focused }) => (
            <HistoryIcon color={color} size={focused ? 24 : 22} strokeWidth={focused ? 2.5 : 2} />
          ),
        }}
      />

      {/* 5. Market & Schemes Tab */}
      <Tab.Screen
        name="MarketTab"
        component={MarketScreen}
        options={{
          tabBarLabel: language === 'kn' ? 'ಮಾರುಕಟ್ಟೆ' : 'Market',
          tabBarIcon: ({ color, focused }) => (
            <MarketIcon color={color} size={focused ? 24 : 22} strokeWidth={focused ? 2.5 : 2} />
          ),
        }}
      />
    </Tab.Navigator>
  );
};

// Root Stack connecting Bottom Tabs + Fullscreen Profile
export const RootNavigator = () => {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="MainTabs" component={BottomTabs} />
      <Stack.Screen name="Profile" component={ProfileScreen} />
    </Stack.Navigator>
  );
};

const styles = StyleSheet.create({
  centerCameraFab: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
    borderWidth: 4,
    borderColor: Colors.surface,
    shadowColor: Colors.primaryDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 6,
    elevation: 6,
  },
});
