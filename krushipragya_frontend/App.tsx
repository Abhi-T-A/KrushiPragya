import React, { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { LanguageProvider } from './src/context/LanguageContext';
import { AuthProvider } from './src/context/AuthContext';
import { ReportProvider } from './src/context/ReportContext';
import { RootNavigator } from './src/navigation/RootNavigator';
import { SplashScreen } from './src/screens/auth/SplashScreen';
import { LanguageSelectionScreen } from './src/screens/auth/LanguageSelectionScreen';
import { OnboardingScreen } from './src/screens/auth/OnboardingScreen';
import { RoleSelectionScreen } from './src/screens/auth/RoleSelectionScreen';
import { ProfileSetupScreen } from './src/screens/auth/ProfileSetupScreen';
import { OTPVerificationScreen } from './src/screens/auth/OTPVerificationScreen';
import { LocationSetupScreen } from './src/screens/auth/LocationSetupScreen';

export default function App() {
  const [currentStep, setCurrentStep] = useState<
    | 'splash'
    | 'language'
    | 'onboarding'
    | 'role_selection'
    | 'profile_setup'
    | 'otp'
    | 'location'
    | 'main'
  >('splash');

  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('+91 98765 43210');

  return (
    <SafeAreaProvider>
      <LanguageProvider>
        <AuthProvider>
          <ReportProvider>
            {currentStep === 'splash' && (
              <>
                <SplashScreen
                  onFinish={() => setCurrentStep('language')}
                  onReturningUser={() => setCurrentStep('main')}
                />
                <StatusBar style="light" />
              </>
            )}

            {currentStep === 'language' && (
              <>
                <LanguageSelectionScreen onContinue={() => setCurrentStep('onboarding')} />
                <StatusBar style="dark" />
              </>
            )}

            {currentStep === 'onboarding' && (
              <>
                <OnboardingScreen
                  onFinish={() => setCurrentStep('role_selection')}
                  onBack={() => setCurrentStep('language')}
                />
                <StatusBar style="dark" />
              </>
            )}

            {currentStep === 'role_selection' && (
              <>
                <RoleSelectionScreen
                  onContinue={() => setCurrentStep('profile_setup')}
                  onBack={() => setCurrentStep('onboarding')}
                />
                <StatusBar style="light" />
              </>
            )}

            {currentStep === 'profile_setup' && (
              <>
                <ProfileSetupScreen
                  initialName={fullName}
                  initialPhone={phone}
                  onProceedToOTP={(data) => {
                    setFullName(data.fullName);
                    setPhone(data.phone);
                    setCurrentStep('otp');
                  }}
                  onBack={() => setCurrentStep('role_selection')}
                />
                <StatusBar style="dark" />
              </>
            )}

            {currentStep === 'otp' && (
              <>
                <OTPVerificationScreen
                  phone={phone}
                  onVerifySuccess={() => setCurrentStep('location')}
                  onBack={() => setCurrentStep('profile_setup')}
                />
                <StatusBar style="dark" />
              </>
            )}

            {currentStep === 'location' && (
              <>
                <LocationSetupScreen
                  onComplete={() => setCurrentStep('main')}
                  onBack={() => setCurrentStep('otp')}
                />
                <StatusBar style="dark" />
              </>
            )}

            {currentStep === 'main' && (
              <NavigationContainer>
                <RootNavigator />
                <StatusBar style="dark" />
              </NavigationContainer>
            )}
          </ReportProvider>
        </AuthProvider>
      </LanguageProvider>
    </SafeAreaProvider>
  );
}
// Root entry updated for Advisory UI

