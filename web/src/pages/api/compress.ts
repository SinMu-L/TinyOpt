import type { APIRoute } from 'astro';

function getApiKeys(): string[] {
  const keys = import.meta.env.TINYPNG_API_KEYS || import.meta.env.TINYPNG_API_KEY || '';
  return keys.split(',').map(k => k.trim()).filter(Boolean);
}

function makeAuth(key: string): string {
  return `Basic ${Buffer.from(`api:${key}`).toString('base64')}`;
}

export const post: APIRoute = async ({ request }) => {
  try {
    const keys = getApiKeys();
    if (keys.length === 0) {
      return new Response(JSON.stringify({
        error: 'API keys not configured. Set TINYPNG_API_KEYS in environment variables.',
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const formData = await request.formData();
    const imageFile = formData.get('image') as File;

    if (!imageFile || imageFile.size === 0) {
      return new Response(JSON.stringify({ error: 'No image provided' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    if (imageFile.size > 10 * 1024 * 1024) {
      return new Response(JSON.stringify({ error: 'File too large (max 10MB)' }), {
        status: 413,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const format = formData.get('format') as string || 'original';
    const resizeMethod = formData.get('resizeMethod') as string;
    const resizeWidth = parseInt(formData.get('resizeWidth') as string) || undefined;
    const resizeHeight = parseInt(formData.get('resizeHeight') as string) || undefined;

    const buffer = Buffer.from(await imageFile.arrayBuffer());

    // Try keys with rotation — skip exhausted keys (429)
    let originalInfo: any = null;
    let usedKey = '';
    let allExhausted = true;

    for (const key of keys) {
      const response = await fetch('https://api.tinify.com/shrink', {
        method: 'POST',
        headers: {
          'Authorization': makeAuth(key),
          'Content-Type': 'application/octet-stream',
        },
        body: buffer,
      });

      if (response.ok) {
        originalInfo = await response.json();
        usedKey = key;
        allExhausted = false;
        break;
      }

      if (response.status !== 429) {
        let detail = '';
        try { detail = await response.text(); } catch {}
        return new Response(JSON.stringify({
          error: `TinyPNG API error (${response.status})`,
          detail,
        }), {
          status: response.status === 429 ? 429 : 502,
          headers: { 'Content-Type': 'application/json' },
        });
      }
    }

    if (!originalInfo) {
      return new Response(JSON.stringify({
        error: allExhausted
          ? 'All API keys have exhausted their monthly quota. Please try again later or add more keys.'
          : 'No available API keys',
      }), {
        status: 429,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    let outputUrl = originalInfo.output.url;
    const originalSize = originalInfo.input.size;
    const auth = makeAuth(usedKey);

    const transforms: Record<string, any> = {};
    if (resizeMethod) {
      transforms.resize = {
        method: resizeMethod,
        ...(resizeWidth && { width: resizeWidth }),
        ...(resizeHeight && { height: resizeHeight }),
      };
    }
    if (format && format !== 'original') {
      transforms.convert = { type: `image/${format}` };
    }

    if (Object.keys(transforms).length > 0) {
      const transformResponse = await fetch(outputUrl, {
        method: 'POST',
        headers: {
          'Authorization': auth,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(transforms),
      });

      if (!transformResponse.ok) {
        return new Response(JSON.stringify({ error: 'Transform failed' }), {
          status: 502,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      const transformResult = await transformResponse.json();
      outputUrl = transformResult.output.url;
    }

    const compressedResponse = await fetch(outputUrl);
    if (!compressedResponse.ok) {
      return new Response(JSON.stringify({ error: 'Failed to download result' }), {
        status: 502,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const compressedBuffer = Buffer.from(await compressedResponse.arrayBuffer());
    const contentType = format && format !== 'original'
      ? `image/${format}`
      : (originalInfo.output.type || 'image/png');
    const ext = format && format !== 'original'
      ? format
      : (originalInfo.output.type?.split('/')[1] || 'png');

    return new Response(compressedBuffer, {
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': `attachment; filename="compressed.${ext}"`,
        'X-Original-Size': String(originalSize),
        'X-Compressed-Size': String(compressedBuffer.length),
      },
    });
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err.message || 'Internal error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
};
