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
import { LoginScreen } from './src/screens/auth/LoginScreen';
import { OTPVerificationScreen } from './src/screens/auth/OTPVerificationScreen';
import { ProfileSetupScreen } from './src/screens/auth/ProfileSetupScreen';

export default function App() {
  const [currentStep, setCurrentStep] = useState<
    'splash' | 'language' | 'onboarding' | 'login' | 'otp' | 'profile_setup' | 'main'
  >('splash');

  const [phone, setPhone] = useState('+91 98765 43210');

  return (
    <SafeAreaProvider>
      <LanguageProvider>
        <AuthProvider>
          <ReportProvider>
            {currentStep === 'splash' && (
              <>
                <SplashScreen onFinish={() => setCurrentStep('language')} />
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
                  onFinish={() => setCurrentStep('login')}
                  onBack={() => setCurrentStep('language')}
                />
                <StatusBar style="dark" />
              </>
            )}

            {currentStep === 'login' && (
              <>
                <LoginScreen
                  onProceedToOTP={(p) => {
                    setPhone(p);
                    setCurrentStep('otp');
                  }}
                  onBack={() => setCurrentStep('onboarding')}
                />
                <StatusBar style="light" />
              </>
            )}

            {currentStep === 'otp' && (
              <>
                <OTPVerificationScreen
                  phone={phone}
                  onVerifySuccess={() => setCurrentStep('profile_setup')}
                  onBack={() => setCurrentStep('login')}
                />
                <StatusBar style="dark" />
              </>
            )}

            {currentStep === 'profile_setup' && (
              <>
                <ProfileSetupScreen
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

