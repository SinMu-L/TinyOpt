export interface AffiliateLink {
  name: string;
  url: string;
  description: string;
}

export const AFFILIATE_LINKS: Record<string, AffiliateLink> = {
  shopify: {
    name: 'Shopify',
    url: 'https://shopify.pxf.io/YOUR_ID',
    description: 'E-commerce platform',
  },
  cloudways: {
    name: 'Cloudways',
    url: 'https://www.cloudways.com/en/?id=YOUR_ID',
    description: 'Managed cloud hosting',
  },
  bunnyCdn: {
    name: 'BunnyCDN',
    url: 'https://bunny.net/?ref=YOUR_ID',
    description: 'Content delivery network',
  },
};

export function getAffiliateUrl(key: string): string {
  const link = AFFILIATE_LINKS[key];
  if (!link) {
    console.warn(`[affiliates] Unknown affiliate key: ${key}`);
    return '#';
  }
  return link.url;
}

export function isAffiliateLink(url: string): boolean {
  return url.includes('YOUR_ID') === false;
}
