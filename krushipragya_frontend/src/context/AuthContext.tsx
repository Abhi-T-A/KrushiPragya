import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export type UserRole = 'farmer' | 'expert' | 'officer' | 'buyer' | 'community' | 'village_node';

export interface UserProfile {
  id: string;
  name: string;
  nameKn: string;
  phone: string;
  role: UserRole;
  roleTitleEn: string;
  roleTitleKn: string;
  villageId: string;
  villageName: string;
  villageNameKn: string;
  district?: string;
  state?: string;
  farmSizeAcres?: string;
  mainCrop?: string;
  organization?: string;
}

export const ROLE_PROFILES: Record<UserRole, UserProfile> = {
  farmer: {
    id: '11111111-1111-4111-8111-111111111111',
    name: 'Farmer (ರೈತ)',
    nameKn: 'ರೈತರು',
    phone: '9876543210',
    role: 'farmer',
    roleTitleEn: 'Farmer',
    roleTitleKn: 'ಬೆಳೆಗಾರ / ರೈತ',
    villageId: 'v2',
    villageName: 'Ujire',
    villageNameKn: 'ಉಜಿರೆ',
    farmSizeAcres: '2.5 Acres',
    mainCrop: 'Paddy & Arecanut (ಭತ್ತ ಮತ್ತು ಅಡಿಕೆ)',
    organization: 'Ujire Raitha Sangha',
  },
  expert: {
    id: '11111111-1111-4111-8111-111111111112',
    name: 'Agriculture Expert',
    nameKn: 'ಕೃಷಿ ತಜ್ಞರು',
    phone: '+91 94481 23456',
    role: 'expert',
    roleTitleEn: 'Agri Expert / Scientist',
    roleTitleKn: 'ಕೃಷಿ ತಜ್ಞ / ವಿಜ್ಞಾನಿ',
    villageId: 'v1',
    villageName: 'Brahmavar KVK',
    villageNameKn: 'ಬ್ರಹ್ಮಾವರ ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರ',
    organization: 'ICAR - Krishi Vigyan Kendra',
  },
  officer: {
    id: '11111111-1111-4111-8111-111111111113',
    name: 'Government Officer',
    nameKn: 'ಕೃಷಿ ಅಧಿಕಾರಿ',
    phone: '+91 98450 11223',
    role: 'officer',
    roleTitleEn: 'Government Officer',
    roleTitleKn: 'ಕೃಷಿ ಇಲಾಖೆ ಅಧಿಕಾರಿ',
    villageId: 'v2',
    villageName: 'Belthangady Taluk',
    villageNameKn: 'ಬೆಳ್ತಂಗಡಿ ತಾಲೂಕು',
    organization: 'Department of Agriculture, Govt of Karnataka',
  },
  buyer: {
    id: '11111111-1111-4111-8111-111111111114',
    name: 'Buyer / Trader',
    nameKn: 'ಖರೀದಿದಾರ / ವರ್ತಕ',
    phone: '+91 99001 88776',
    role: 'buyer',
    roleTitleEn: 'Buyer & Trader',
    roleTitleKn: 'ಖರೀದಿದಾರ / ವರ್ತಕ',
    villageId: 'v2',
    villageName: 'Mangalore APMC',
    villageNameKn: 'ಮಂಗಳೂರು ಎಪಿಎಂಸಿ',
    organization: 'Karnataka APMC Trade Network',
  },
  community: {
    id: '11111111-1111-4111-8111-111111111115',
    name: 'Community / FPO',
    nameKn: 'ಗ್ರಾಮ ಸಮುದಾಯ & ಎಫ್‌ಪಿಒ',
    phone: '+91 97312 34567',
    role: 'community',
    roleTitleEn: 'Community & FPO Node',
    roleTitleKn: 'ಗ್ರಾಮ ಸಮುದಾಯ & ಎಫ್‌ಪಿಒ',
    villageId: 'v2',
    villageName: 'Ujire FPO Center',
    villageNameKn: 'ಉಜಿರೆ ಎಫ್‌ಪಿಒ ಕೇಂದ್ರ',
    organization: 'Ujire Farmers Producer Organization',
  },
  village_node: {
    id: '11111111-1111-4111-8111-111111111115',
    name: 'Community / FPO',
    nameKn: 'ಗ್ರಾಮ ಸಮುದಾಯ & ಎಫ್‌ಪಿಒ',
    phone: '+91 97312 34567',
    role: 'community',
    roleTitleEn: 'Community & FPO Node',
    roleTitleKn: 'ಗ್ರಾಮ ಸಮುದಾಯ & ಎಫ್‌ಪಿಒ',
    villageId: 'v2',
    villageName: 'Ujire FPO Center',
    villageNameKn: 'ಉಜಿರೆ ಎಫ್‌ಪಿಒ ಕೇಂದ್ರ',
    organization: 'Ujire Farmers Producer Organization',
  },
};

export const normalizeRole = (role: string): UserRole => {
  const r = (role || '').toLowerCase().trim();
  if (r === 'expert' || r === 'agriculture_expert' || r === 'agri_expert') return 'expert';
  if (r === 'officer' || r === 'government_officer' || r === 'govt_officer') return 'officer';
  if (r === 'buyer' || r === 'trader' || r === 'buyer_trader') return 'buyer';
  if (r === 'community' || r === 'community_member' || r === 'village_node') return 'community';
  return 'farmer';
};

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  login: (phone: string, role: UserRole | string, villageId: string, name?: string) => void;
  saveCompleteProfile: (data: {
    name: string;
    phone: string;
    role: UserRole | string;
    villageName: string;
    villageId?: string;
    district?: string;
    state?: string;
  }) => Promise<void>;
  restoreUser: (savedUser: UserProfile) => void;
  logout: () => void;
  setRole: (role: UserRole | string) => void;
  toggleRole: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: ROLE_PROFILES.farmer,
  isAuthenticated: true,
  login: () => {},
  saveCompleteProfile: async () => {},
  restoreUser: () => {},
  logout: () => {},
  setRole: () => {},
  toggleRole: () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(ROLE_PROFILES.farmer);

  // Restore persistent profile on launch for returning users
  useEffect(() => {
    const loadSavedSession = async () => {
      try {
        const isDone = await AsyncStorage.getItem('krushi_profile_setup_done');
        const savedData = await AsyncStorage.getItem('krushi_auth_user');
        if (isDone === 'true' && savedData) {
          const parsed = JSON.parse(savedData);
          setUser(parsed);
        }
      } catch (e) {
        console.log('[AuthContext] Failed to load saved session:', e);
      }
    };
    loadSavedSession();
  }, []);

  const login = (phone: string, role: UserRole | string, villageId: string, name?: string) => {
    const normalizedRole = normalizeRole(role);
    const profile = ROLE_PROFILES[normalizedRole] || ROLE_PROFILES.farmer;
    const updated = {
      ...profile,
      phone: phone || profile.phone,
      name: name || profile.name,
      nameKn: profile.nameKn,
      villageId: villageId || profile.villageId,
    };
    setUser(updated);
  };

  const saveCompleteProfile = async (data: {
    name: string;
    phone: string;
    role: UserRole | string;
    villageName: string;
    villageId?: string;
    district?: string;
    state?: string;
  }) => {
    const normalizedRole = normalizeRole(data.role);
    const baseProfile = ROLE_PROFILES[normalizedRole] || ROLE_PROFILES.farmer;
    const completedUser: UserProfile = {
      ...baseProfile,
      name: data.name.trim() || baseProfile.name,
      nameKn: data.name.trim() || baseProfile.nameKn,
      phone: data.phone.trim() || baseProfile.phone,
      villageId: data.villageId || baseProfile.villageId,
      villageName: data.villageName.trim() || baseProfile.villageName,
      villageNameKn: data.villageName.trim() || baseProfile.villageNameKn,
      district: data.district?.trim() || 'Dakshina Kannada',
      state: data.state?.trim() || 'Karnataka',
    };
    setUser(completedUser);
    try {
      await AsyncStorage.setItem('krushi_profile_setup_done', 'true');
      await AsyncStorage.setItem('krushi_auth_user', JSON.stringify(completedUser));
    } catch (e) {
      console.log('[AuthContext] Failed to cache profile:', e);
    }
  };

  const restoreUser = (savedUser: UserProfile) => {
    setUser(savedUser);
  };

  const logout = async () => {
    setUser(null);
    try {
      await AsyncStorage.removeItem('krushi_profile_setup_done');
      await AsyncStorage.removeItem('krushi_auth_user');
    } catch (e) {
      console.log('[AuthContext] Failed to clear storage on logout:', e);
    }
  };

  const setRole = (role: UserRole | string) => {
    const normalizedRole = normalizeRole(role);
    const updated = ROLE_PROFILES[normalizedRole] || ROLE_PROFILES.farmer;
    setUser(updated);
    try {
      AsyncStorage.setItem('krushi_auth_user', JSON.stringify(updated));
    } catch {
      // ignore
    }
  };

  const toggleRole = () => {
    if (!user) return;
    const roles: UserRole[] = ['farmer', 'expert', 'officer', 'buyer', 'community'];
    const currentIndex = roles.indexOf(user.role);
    const nextRole = roles[(currentIndex + 1) % roles.length];
    setRole(nextRole);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        saveCompleteProfile,
        restoreUser,
        logout,
        setRole,
        toggleRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);