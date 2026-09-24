import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useLanguage } from '../context/LanguageContext';
import { Colors, Typography, BorderRadius } from '../constants/theme';

// Screens
import { HomeScreen } from '../screens/home/HomeScreen';
import { CropSelectScreen } from '../screens/report/CropSelectScreen';
import { CameraCaptureScreen } from '../screens/report/CameraCaptureScreen';
import { PreviewSubmitScreen } from '../screens/report/PreviewSubmitScreen';
import { AIResultScreen } from '../screens/report/AIResultScreen';
import { ReportListScreen } from '../screens/history/ReportListScreen';
import { WeatherScreen } from '../screens/weather/WeatherScreen';
import { MarketScreen } from '../screens/market/MarketScreen';

// Icons
import {
  Home as HomeIcon,
  Camera as CameraIcon,
  ClipboardList as HistoryIcon,
  CloudRain as WeatherIcon,
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

export const RootNavigator = () => {
  const { t } = useLanguage();

  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: Colors.primary,
        tabBarInactiveTintColor: Colors.textMuted,
        tabBarStyle: {
          backgroundColor: Colors.surface,
          borderTopColor: Colors.border,
          height: 64,
          paddingBottom: 8,
          paddingTop: 6,
        },
        tabBarLabelStyle: {
          ...Typography.caption,
          fontWeight: '700',
        },
      }}
    >
      <Tab.Screen
        name="HomeTab"
        component={HomeScreen}
        options={{
          tabBarLabel: t.tabHome,
          tabBarIcon: ({ color, size }) => <HomeIcon color={color} size={size} />,
        }}
      />

      <Tab.Screen
        name="ReportTab"
        component={ReportStackNavigator}
        options={{
          tabBarLabel: t.tabReport,
          tabBarIcon: ({ color, size }) => (
            <View style={styles.fabIcon}>
              <CameraIcon color={Colors.textWhite} size={22} />
            </View>
          ),
        }}
      />

      <Tab.Screen
        name="HistoryTab"
        component={ReportListScreen}
        options={{
          tabBarLabel: t.tabHistory,
          tabBarIcon: ({ color, size }) => <HistoryIcon color={color} size={size} />,
        }}
      />

      <Tab.Screen
        name="WeatherTab"
        component={WeatherScreen}
        options={{
          tabBarLabel: t.tabWeather,
          tabBarIcon: ({ color, size }) => <WeatherIcon color={color} size={size} />,
        }}
      />

      <Tab.Screen
        name="MarketTab"
        component={MarketScreen}
        options={{
          tabBarLabel: t.tabMarket,
          tabBarIcon: ({ color, size }) => <MarketIcon color={color} size={size} />,
        }}
      />
    </Tab.Navigator>
  );
};

const styles = StyleSheet.create({
  fabIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
    shadowColor: Colors.primaryDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
});
