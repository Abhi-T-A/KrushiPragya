import React, { createContext, useContext, useState } from 'react';

export type UserRole = 'farmer' | 'expert' | 'officer' | 'buyer' | 'community' | 'village_node';

export interface UserProfile {
  name: string;
  nameKn: string;
  phone: string;
  role: UserRole;
  roleTitleEn: string;
  roleTitleKn: string;
  villageId: string;
  villageName: string;
  villageNameKn: string;
  farmSizeAcres?: string;
  mainCrop?: string;
  organization?: string;
}

export const ROLE_PROFILES: Record<UserRole, UserProfile> = {
  farmer: {
    name: 'Mallikarjuna Gowda',
    nameKn: 'ಮಲ್ಲಿಕಾರ್ಜುನ ಗೌಡ',
    phone: '+91 98765 43210',
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
    name: 'Dr. Ramesh K (Agronomist)',
    nameKn: 'ಡಾ. ರಮೇಶ್ (ಕೃಷಿ ತಜ್ಞ)',
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
    name: 'Sunitha IAS (Agri Dept)',
    nameKn: 'ಶ್ರೀಮತಿ ಸುನಿತಾ (ಕೃಷಿ ಅಧಿಕಾರಿ)',
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
    name: 'Rajesh Seth (APMC Merchant)',
    nameKn: 'ರಾಜೇಶ್ ಸೇಠ್ (ವರ್ತಕ)',
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
    name: 'Suresh Gowda (FPO Lead)',
    nameKn: 'ಸುರೇಶ್ ಗೌಡ (ಗ್ರಾಮ ಸಮುದಾಯ)',
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
    name: 'Suresh Gowda (FPO Lead)',
    nameKn: 'ಸುರೇಶ್ ಗೌಡ (ಗ್ರಾಮ ಸಮುದಾಯ)',
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

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  login: (phone: string, role: UserRole, villageId: string, name?: string) => void;
  logout: () => void;
  setRole: (role: UserRole) => void;
  toggleRole: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: ROLE_PROFILES.farmer,
  isAuthenticated: true,
  login: () => {},
  logout: () => {},
  setRole: () => {},
  toggleRole: () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(ROLE_PROFILES.farmer);

  const login = (phone: string, role: UserRole, villageId: string, name: string = 'Mallikarjuna Gowda') => {
    const profile = ROLE_PROFILES[role] || ROLE_PROFILES.farmer;
    setUser({
      ...profile,
      phone: phone || profile.phone,
      name: name || profile.name,
      villageId: villageId || profile.villageId,
    });
  };

  const logout = () => {
    setUser(null);
  };

  const setRole = (role: UserRole) => {
    const normalizedRole = role === 'village_node' ? 'community' : role;
    setUser(ROLE_PROFILES[normalizedRole] || ROLE_PROFILES.farmer);
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