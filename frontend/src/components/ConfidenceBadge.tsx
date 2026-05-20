import { useLanguage } from '../contexts/LanguageContext';

interface Props {
  level: 'verified' | 'estimated' | 'district';
}

const CONFIG = {
  verified: {
    en: '✓ Verified',
    zh: '✓ 已验证',
    classes: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  },
  estimated: {
    en: '~ Estimated',
    zh: '〜 估算值',
    classes: 'border-amber-200 bg-amber-50 text-amber-700',
  },
  district: {
    en: '~ District-level',
    zh: '〜 区级数据',
    classes: 'border-amber-200 bg-amber-50 text-amber-700',
  },
};

export default function ConfidenceBadge({ level }: Props) {
  const { lang } = useLanguage();
  const cfg = CONFIG[level];
  const label = lang === 'zh' ? cfg.zh : cfg.en;

  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border whitespace-nowrap ${cfg.classes}`}>
      {label}
    </span>
  );
}
