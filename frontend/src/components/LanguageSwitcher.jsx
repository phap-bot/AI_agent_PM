import React from 'react';
import { useTranslation } from 'react-i18next';

export default function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const isVi = i18n.language.startsWith('vi');

  const toggleLanguage = (lang) => {
    i18n.changeLanguage(lang);
  };

  return (
    <div className="flex bg-surface-container-high rounded-md p-1 w-[120px] relative border border-outline-variant/30">
      <div 
        className="absolute top-1 bottom-1 bg-white rounded-sm shadow-sm transition-all duration-300 ease-in-out z-0" 
        style={{ width: 'calc(50% - 4px)', transform: isVi ? 'translateX(0)' : 'translateX(100%)' }}
      ></div>
      <button
        onClick={() => toggleLanguage('vi')}
        className={`flex-1 flex justify-center items-center py-1 z-10 transition-colors rounded-sm ${isVi ? 'text-primary font-bold' : 'text-on-surface-variant hover:text-on-surface'}`}
      >
        <span className="text-xs font-bold tracking-wider">VI</span>
      </button>
      <button
        onClick={() => toggleLanguage('en')}
        className={`flex-1 flex justify-center items-center py-1 z-10 transition-colors rounded-sm ${!isVi ? 'text-primary font-bold' : 'text-on-surface-variant hover:text-on-surface'}`}
      >
        <span className="text-xs font-bold tracking-wider">EN</span>
      </button>
    </div>
  );
}
