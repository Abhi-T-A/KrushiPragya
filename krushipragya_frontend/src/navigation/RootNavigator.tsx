import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useLanguage } from '../context/LanguageContext';
import { useAuth, normalizeRole } from '../context/AuthContext';
import { Colors, Typography, BorderRadius, Spacing } from '../constants/theme';

// Screens
import { HomeScreen } from '../screens/home/HomeScreen';
import { ExpertDashboardScreen } from '../screens/expert/ExpertDashboardScreen';
import { ExpertQueueScreen } from '../screens/expert/ExpertQueueScreen';
import { ExpertHistoryScreen } from '../screens/expert/ExpertHistoryScreen';
import { GovtDashboardScreen } from '../screens/govt/GovtDashboardScreen';
import { GovtApplicationsScreen } from '../screens/govt/GovtApplicationsScreen';
import { GovtSchemesScreen } from '../screens/govt/GovtSchemesScreen';
import { GovtInsightsScreen } from '../screens/govt/GovtInsightsScreen';
import { GovtPortalScreen } from '../screens/govt/GovtPortalScreen';
import { TraderMarketScreen } from '../screens/market/TraderMarketScreen';
import { BuyerHomeScreen } from '../screens/buyer/BuyerHomeScreen';
import { BuyerProduceScreen } from '../screens/buyer/BuyerProduceScreen';
import { BuyerOffersScreen } from '../screens/buyer/BuyerOffersScreen';
import { BuyerTransactionsScreen } from '../screens/buyer/BuyerTransactionsScreen';
import { CommunityHomeScreen } from '../screens/community/CommunityHomeScreen';
import { CommunityReportsScreen } from '../screens/community/CommunityReportsScreen';
import { CommunityCorroborateScreen } from '../screens/community/CommunityCorroborateScreen';
import { CommunityAlertsScreen } from '../screens/community/CommunityAlertsScreen';
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
  LayoutDashboard,
  Microscope,
  ClipboardList,
  User as UserIcon,
  FileText,
  BarChart3,
  Store,
  Tag,
  Receipt,
  Package,
  Eye,
  HeartHandshake,
  AlertTriangle,
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



// Common KrushiPragya unified tab bar styling across ALL roles
const COMMON_TAB_OPTIONS = {
  headerShown: false,
  tabBarActiveTintColor: Colors.primary,
  tabBarInactiveTintColor: '#64748B',
  tabBarStyle: {
    backgroundColor: '#FFFFFF',
    borderTopColor: '#E2E8F0',
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
    fontSize: 10.5,
    fontWeight: '700' as const,
    marginTop: 2,
  },
};

// Dedicated Expert Bottom Tabs Navigator (Dashboard | ಪರಿಶೀಲನೆ | History | Profile)
const ExpertBottomTabs = () => {
  const { language } = useLanguage();
  const isKn = language === 'kn';

  return (
    <Tab.Navigator
      initialRouteName="ExpertDashboardTab"
      screenOptions={COMMON_TAB_OPTIONS}
    >
      {/* 1. Dashboard Tab */}
      <Tab.Screen
        name="ExpertDashboardTab"
        component={ExpertDashboardScreen}
        options={{
          tabBarLabel: isKn ? 'ಮುಖಪುಟ' : 'Dashboard',
          tabBarIcon: ({ color, focused }) => (
            <LayoutDashboard size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />

      {/* 2. Verification Queue Tab */}
      <Tab.Screen
        name="ExpertQueueTab"
        component={ExpertQueueScreen}
        options={{
          tabBarLabel: isKn ? 'ಪರಿಶೀಲನೆ' : 'Verification',
          tabBarIcon: ({ color, focused }) => (
            <Microscope size={21} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />

      {/* 3. History Tab */}
      <Tab.Screen
        name="ExpertHistoryTab"
        component={ExpertHistoryScreen}
        options={{
          tabBarLabel: isKn ? 'ಇತಿಹಾಸ' : 'History',
          tabBarIcon: ({ color, focused }) => (
            <ClipboardList size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />

      {/* 4. Profile Tab */}
      <Tab.Screen
        name="ExpertProfileTab"
        component={ProfileScreen}
        options={{
          tabBarLabel: isKn ? 'ಪ್ರೊಫೈಲ್' : 'Profile',
          tabBarIcon: ({ color, focused }) => (
            <UserIcon size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />
    </Tab.Navigator>
  );
};

// Dedicated Government Officer 5-Bottom Tabs Navigator (Dashboard | Applications | Schemes | Insights | Profile)
const GovernmentBottomTabs = () => {
  const { language } = useLanguage();
  const isKn = language === 'kn';

  return (
    <Tab.Navigator
      initialRouteName="GovtDashboardTab"
      screenOptions={COMMON_TAB_OPTIONS}
    >
      {/* 1. Dashboard Tab */}
      <Tab.Screen
        name="GovtDashboardTab"
        component={GovtDashboardScreen}
        options={{
          tabBarLabel: isKn ? 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್' : 'Dashboard',
          tabBarIcon: ({ color, focused }) => (
            <LayoutDashboard size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />

      {/* 2. Applications Tab */}
      <Tab.Screen
        name="GovtApplicationsTab"
        component={GovtApplicationsScreen}
        options={{
          tabBarLabel: isKn ? 'ಅರ್ಜಿಗಳು' : 'Applications',
          tabBarIcon: ({ color, focused }) => (
            <FileText size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />

      {/* 3. Schemes Tab */}
      <Tab.Screen
        name="GovtSchemesTab"
        component={GovtSchemesScreen}
        options={{
          tabBarLabel: isKn ? 'ಯೋಜನೆಗಳು' : 'Schemes',
          tabBarIcon: ({ color, focused }) => (
            <SchemesIcon size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />

      {/* 4. Agricultural Insights Tab */}
      <Tab.Screen
        name="GovtInsightsTab"
        component={GovtInsightsScreen}
        options={{
          tabBarLabel: isKn ? 'ಕೃಷಿ ಸ್ಥಿತಿ' : 'Insights',
          tabBarIcon: ({ color, focused }) => (
            <BarChart3 size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />

      {/* 5. Profile Tab */}
      <Tab.Screen
        name="GovtProfileTab"
        component={ProfileScreen}
        options={{
          tabBarLabel: isKn ? 'ಪ್ರೊಫೈಲ್' : 'Profile',
          tabBarIcon: ({ color, focused }) => (
            <UserIcon size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />
    </Tab.Navigator>
  );
};

// Dedicated Buyer & Trader 5-Bottom Tabs Navigator (Home | Produce | Offers | Transactions | Profile)
const BuyerBottomTabs = () => {
  const { language } = useLanguage();
  const isKn = language === 'kn';

  return (
    <Tab.Navigator
      initialRouteName="BuyerHomeTab"
      screenOptions={COMMON_TAB_OPTIONS}
    >
      {/* 1. Home Tab */}
      <Tab.Screen
        name="BuyerHomeTab"
        component={BuyerHomeScreen}
        options={{
          tabBarLabel: isKn ? 'ಮುಖಪುಟ' : 'Home',
          tabBarIcon: ({ color, focused }) => (
            <Store size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />

      {/* 2. Produce Tab */}
      <Tab.Screen
        name="BuyerProduceTab"
        component={BuyerProduceScreen}
        options={{
          tabBarLabel: isKn ? 'ಬೆಳೆಗಳು' : 'Produce',
          tabBarIcon: ({ color, focused }) => (
            <Package size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />

      {/* 3. Offers Tab */}
      <Tab.Screen
        name="BuyerOffersTab"
        component={BuyerOffersScreen}
        options={{
          tabBarLabel: isKn ? 'ಆಫರ್‌ಗಳು' : 'Offers',
          tabBarIcon: ({ color, focused }) => (
            <Tag size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />

      {/* 4. Transactions Tab */}
      <Tab.Screen
        name="BuyerTransactionsTab"
        component={BuyerTransactionsScreen}
        options={{
          tabBarLabel: isKn ? 'ವಹಿವಾಟು' : 'Transactions',
          tabBarIcon: ({ color, focused }) => (
            <Receipt size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />

      {/* 5. Profile Tab */}
      <Tab.Screen
        name="BuyerProfileTab"
        component={ProfileScreen}
        options={{
          tabBarLabel: isKn ? 'ಪ್ರೊಫೈಲ್' : 'Profile',
          tabBarIcon: ({ color, focused }) => (
            <UserIcon size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />
    </Tab.Navigator>
  );
};

// Dedicated Community Member 5-Bottom Tabs Navigator (Home | Reports | Corroborate | Alerts | Profile)
const CommunityBottomTabs = () => {
  const { language } = useLanguage();
  const isKn = language === 'kn';

  return (
    <Tab.Navigator
      initialRouteName="CommunityHomeTab"
      screenOptions={COMMON_TAB_OPTIONS}
    >
      {/* 1. Home Tab */}
      <Tab.Screen
        name="CommunityHomeTab"
        component={CommunityHomeScreen}
        options={{
          tabBarLabel: isKn ? 'ಮುಖಪುಟ' : 'Home',
          tabBarIcon: ({ color, focused }) => (
            <HomeIcon size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />

      {/* 2. Local Reports Tab */}
      <Tab.Screen
        name="CommunityReportsTab"
        component={CommunityReportsScreen}
        options={{
          tabBarLabel: isKn ? 'ವರದಿಗಳು' : 'Reports',
          tabBarIcon: ({ color, focused }) => (
            <Eye size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />

      {/* 3. Corroborate Tab */}
      <Tab.Screen
        name="CommunityCorroborateTab"
        component={CommunityCorroborateScreen}
        options={{
          tabBarLabel: isKn ? 'ದೃಢೀಕರಣ' : 'Corroborate',
          tabBarIcon: ({ color, focused }) => (
            <HeartHandshake size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />

      {/* 4. Alerts Tab */}
      <Tab.Screen
        name="CommunityAlertsTab"
        component={CommunityAlertsScreen}
        options={{
          tabBarLabel: isKn ? 'ಎಚ್ಚರಿಕೆ' : 'Alerts',
          tabBarIcon: ({ color, focused }) => (
            <AlertTriangle size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />

      {/* 5. Profile Tab */}
      <Tab.Screen
        name="CommunityProfileTab"
        component={ProfileScreen}
        options={{
          tabBarLabel: isKn ? 'ಪ್ರೊಫೈಲ್' : 'Profile',
          tabBarIcon: ({ color, focused }) => (
            <UserIcon size={20} color={color} strokeWidth={focused ? 2.4 : 1.8} />
          ),
        }}
      />
    </Tab.Navigator>
  );
};

// Standard Farmer 5-Bottom Tabs Navigator
const FarmerBottomTabs = () => {
  const { language } = useLanguage();
  const isKn = language === 'kn';

  return (
    <Tab.Navigator
      initialRouteName="HomeTab"
      screenOptions={COMMON_TAB_OPTIONS}
    >
      {/* 1. Home Tab */}
      <Tab.Screen
        name="HomeTab"
        component={HomeScreen}
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

// Role-based Root Tab Navigator: mounts the dedicated navigator for the active authenticated role
const MainRoleTabs = () => {
  const { user } = useAuth();
  const role = normalizeRole(user?.role || 'farmer');

  switch (role) {
    case 'expert':
      return <ExpertBottomTabs key="expert-tabs" />;
    case 'officer':
      return <GovernmentBottomTabs key="officer-tabs" />;
    case 'buyer':
      return <BuyerBottomTabs key="buyer-tabs" />;
    case 'community':
    case 'village_node':
      return <CommunityBottomTabs key="community-tabs" />;
    case 'farmer':
    default:
      return <FarmerBottomTabs key="farmer-tabs" />;
  }
};

// Root Stack Navigator
export const RootNavigator = () => {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen
        name="MainTabs"
        component={MainRoleTabs}
      />
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