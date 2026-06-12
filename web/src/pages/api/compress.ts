import type { APIRoute } from 'astro';

function corsHeaders(): Record<string, string> {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Format, X-Resize-Method, X-Resize-Width, X-Resize-Height, X-Filename',
  };
}

function getApiKeys(): string[] {
  const raw = process.env.TINYPNG_API_KEYS || process.env.TINYPNG_API_KEY || '';
  return raw.split(/[,;]/).map(k => k.trim()).filter(Boolean);
}

function makeAuth(key: string): string {
  return `Basic ${Buffer.from(`api:${key}`).toString('base64')}`;
}

function jsonError(message: string, status: number): Response {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: { 'Content-Type': 'application/json', ...corsHeaders() },
  });
}

export const OPTIONS: APIRoute = async () => {
  return new Response(null, { headers: corsHeaders() });
};

export const post: APIRoute = async ({ request }) => {
  try {
    const keys = getApiKeys();
    if (keys.length === 0) {
      return jsonError('API keys not configured. Set TINYPNG_API_KEYS in environment variables.', 500);
    }

    const buffer = Buffer.from(await request.arrayBuffer());

    if (!buffer || buffer.length === 0) {
      return jsonError('No image provided', 400);
    }

    if (buffer.length > 10 * 1024 * 1024) {
      return jsonError('File too large (max 10MB)', 413);
    }

    const format = request.headers.get('X-Format') || 'original';
    const resizeMethod = request.headers.get('X-Resize-Method');
    const resizeWidth = parseInt(request.headers.get('X-Resize-Width') || '') || undefined;
    const resizeHeight = parseInt(request.headers.get('X-Resize-Height') || '') || undefined;

    // Try keys with rotation — skip exhausted keys (429)
    let originalInfo: any = null;
    let usedKey = '';

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
        break;
      }

      if (response.status !== 429) {
        let detail = '';
        try { detail = await response.text(); } catch {}
        return jsonError(`TinyPNG API error (${response.status})${detail ? ': ' + detail : ''}`, 502);
      }
    }

    if (!originalInfo) {
      return jsonError(
        'All API keys have exhausted their monthly quota. Please try again later or add more keys.',
        429
      );
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
        return jsonError('Transform failed', 502);
      }

      const transformResult = await transformResponse.json();
      outputUrl = transformResult.output.url;
    }

    const compressedResponse = await fetch(outputUrl);
    if (!compressedResponse.ok) {
      return jsonError('Failed to download result', 502);
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
        ...corsHeaders(),
      },
    });
  } catch (err: any) {
    return jsonError(err.message || 'Internal error', 500);
  }
};
