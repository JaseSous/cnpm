import React from 'react';
import { LANGUAGES } from '../types';

interface Props {
  selectedLang: string;
  onSelectLang: (langCode: string) => void;
}

export const LanguageSelector: React.FC<Props> = ({ selectedLang, onSelectLang }) => {
  return (
    <div className="relative inline-block text-left">
      <select
        value={selectedLang}
        onChange={(e) => onSelectLang(e.target.value)}
        className="bg-white/90 backdrop-blur border border-amber-300 text-slate-800 text-xs font-medium rounded-full px-3 py-1.5 shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500 cursor-pointer"
      >
        {LANGUAGES.map((l) => (
          <option key={l.code} value={l.code}>
            {l.flag} {l.name}
          </option>
        ))}
      </select>
    </div>
  );
};
