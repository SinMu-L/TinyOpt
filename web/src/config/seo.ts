export interface SEOProps {
  title: string;
  description: string;
  lang?: 'zh' | 'en';
  ogImage?: string;
  noindex?: boolean;
}

export const SITE_CONFIG = {
  zh: {
    url: 'https://seojeck.com/zh',
    title: '免费批量图片压缩工具 TinyOpt — PNG/JPEG/WebP 优化',
    description: '免费 Windows 批量图片压缩工具。基于 TinyPNG API 批量压缩 PNG、JPEG、WebP、AVIF，支持水印、格式转换与批量重命名，无上传体积限制。',
  },
  en: {
    url: 'https://seojeck.com',
    title: 'Free Batch Image Compressor — TinyOpt | PNG JPEG WebP',
    description: 'Free batch image compressor for Windows. Bulk compress PNG, JPEG, WebP & AVIF with TinyPNG API — plus watermark, format conversion, and batch rename. No upload caps.',
  },
};
