export interface SEOProps {
  title: string;
  description: string;
  lang?: 'zh' | 'en';
  ogImage?: string;
  noindex?: boolean;
}

export const SITE_CONFIG = {
  zh: {
    url: 'https://seojeck.com',
    title: 'TinyOpt',
    description: '基于 TinyPNG API 的桌面图片批量压缩工具，支持水印添加、格式转换、批量重命名。免费、高效、安全。',
  },
  en: {
    url: 'https://seojeck.com/en',
    title: 'TinyOpt',
    description: 'A desktop batch image compression tool based on TinyPNG API, supporting watermark, format conversion, and batch renaming.',
  },
};
