import React, { createContext, useContext, useState } from 'react';

export type UserRole = 'farmer' | 'village_node';

interface UserProfile {
  name: string;
  phone: string;
  role: UserRole;
  villageId: string;
  villageName: string;
  farmSizeAcres: string;
  mainCrop: string;
}

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  login: (phone: string, role: UserRole, villageId: string, name?: string) => void;
  logout: () => void;
  toggleRole: () => void;
}

const DEFAULT_USER: UserProfile = {
  name: 'ಅಭಿ ಗೌಡ (Abhi)',
  phone: '+91 98765 43210',
  role: 'farmer',
  villageId: 'v2',
  villageName: 'Ujire (ಉಜಿರೆ)',
  farmSizeAcres: '2.5',
  mainCrop: 'ಅಡಿಕೆ (Arecanut)',
};

const AuthContext = createContext<AuthContextType>({
  user: DEFAULT_USER,
  isAuthenticated: true,
  login: () => {},
  logout: () => {},
  toggleRole: () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(DEFAULT_USER);

  const login = (phone: string, role: UserRole, villageId: string, name: string = 'ಅಭಿ ಗೌಡ') => {
    setUser({
      name,
      phone,
      role,
      villageId,
      villageName: villageId === 'v1' ? 'Thirthahalli (ತೀರ್ಥಹಳ್ಳಿ)' : 'Ujire (ಉಜಿರೆ)',
      farmSizeAcres: '2.5',
      mainCrop: 'ಅಡಿಕೆ (Arecanut)',
    });
  };

  const logout = () => {
    setUser(null);
  };

  const toggleRole = () => {
    if (!user) return;
    setUser({
      ...user,
      role: user.role === 'farmer' ? 'village_node' : 'farmer',
    });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        logout,
        toggleRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
