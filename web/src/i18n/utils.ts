import zh from './zh.json';
import en from './en.json';

const translations = { zh, en } as const;

export type Lang = 'zh' | 'en';

export function t(lang: Lang) {
  return (key: string) => {
    const keys = key.split('.');
    let value: any = translations[lang];
    for (const k of keys) {
      value = value?.[k];
    }
    return value ?? key;
  };
}

// Convenience: returns the full translation object for a given language
export function translation(lang: Lang) {
  return translations[lang];
}
