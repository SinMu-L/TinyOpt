const KEY = '830dc57cc28647e2ad21c32e0d53e29f';
const HOST = 'seojeck.com';

async function fetchSitemapUrls() {
  const res = await fetch(`https://${HOST}/sitemap.xml`);
  const xml = await res.text();
  const urls = [...xml.matchAll(/<loc>(https:\/\/[^<]+)<\/loc>/g)].map((m) => m[1]);
  return urls;
}

async function main() {
  const urlList = await fetchSitemapUrls();
  console.log(`[IndexNow] Found ${urlList.length} URLs from sitemap`);

  const body = {
    host: HOST,
    key: KEY,
    keyLocation: `https://${HOST}/${KEY}.txt`,
    urlList,
  };

  const endpoints = [
    'https://www.bing.com/indexnow',
    'https://api.indexnow.org/indexnow',
  ];

  for (const url of endpoints) {
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      console.log(`[IndexNow] ${url} -> ${res.status} ${res.statusText}`);
    } catch (err) {
      console.error(`[IndexNow] ${url} -> error: ${err.message}`);
    }
  }
}

main();
