import React, { createContext, useContext, useState } from 'react';
import { KN_STRINGS, EN_STRINGS } from '../i18n/translations';

type Language = 'kn' | 'en';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: typeof KN_STRINGS;
}

const LanguageContext = createContext<LanguageContextType>({
  language: 'kn',
  setLanguage: () => {},
  t: KN_STRINGS,
});

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguage] = useState<Language>('kn');

  const t = language === 'kn' ? KN_STRINGS : EN_STRINGS;

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);
