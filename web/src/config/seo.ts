export interface SEOProps {
  title: string;
  description: string;
  lang?: 'zh' | 'en';
  ogImage?: string;
  noindex?: boolean;
}

export const SITE_CONFIG = {
  zh: {
    url: 'https://tinyjpg-compressor.com',
    title: 'TinyJPG 批量压缩助手',
    description: '基于 TinyPNG API 的桌面图片批量压缩工具，支持水印添加、格式转换、批量重命名。免费、高效、安全。',
  },
  en: {
    url: 'https://tinyjpg-compressor.com/en',
    title: 'TinyJPG Compressor',
    description: 'A desktop batch image compression tool based on TinyPNG API, supporting watermark, format conversion, and batch renaming.',
  },
};
