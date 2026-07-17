const KEY = '830dc57cc28647e2ad21c32e0d53e29f';
const HOST = 'seojeck.com';
const URLS = [
  `https://${HOST}/`,
  `https://${HOST}/download/`,
  `https://${HOST}/about/`,
  `https://${HOST}/blog/`,
  `https://${HOST}/zh/`,
  `https://${HOST}/zh/download/`,
];

async function main() {
  const body = {
    host: HOST,
    key: KEY,
    keyLocation: `https://${HOST}/${KEY}.txt`,
    urlList: URLS,
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
