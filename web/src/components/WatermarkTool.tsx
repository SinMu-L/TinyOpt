import { useState, useEffect, useRef, useCallback } from 'preact/hooks';
import { track } from '@/lib/analytics';

type WatermarkType = 'text' | 'image';

interface Position {
  label: string;
  x: number;
  y: number;
}

interface WatermarkedFile {
  name: string;
  origUrl: string;
  dataUrl: string;
  blob: Blob;
  width: number;
  height: number;
}

interface Translations {
  title: string;
  subtitle: string;
  uploadHint: string;
  uploadFormats: string;
  typeLabel: string;
  textType: string;
  imageType: string;
  textPlaceholder: string;
  fontSize: string;
  color: string;
  opacity: string;
  rotation: string;
  position: string;
  imageWatermarkHint: string;
  imageScale: string;
  preview: string;
  applyAll: string;
  applying: string;
  processing: string;
  results: string;
  viewImage: string;
  downloadSingle: string;
  downloadAllZip: string;
  backToSettings: string;
  clearAll: string;
  noImages: string;
  dragHint: string;
}

const POSITIONS: Position[] = [
  { label: '↖', x: 0.05, y: 0.05 },
  { label: '↑', x: 0.5, y: 0.05 },
  { label: '↗', x: 0.95, y: 0.05 },
  { label: '←', x: 0.05, y: 0.5 },
  { label: '●', x: 0.5, y: 0.5 },
  { label: '→', x: 0.95, y: 0.5 },
  { label: '↙', x: 0.05, y: 0.95 },
  { label: '↓', x: 0.5, y: 0.95 },
  { label: '↘', x: 0.95, y: 0.95 },
];

function renderWatermark(
  ctx: CanvasRenderingContext2D | OffscreenCanvasRenderingContext2D,
  imgWidth: number,
  imgHeight: number,
  config: {
    type: WatermarkType;
    text: string;
    fontSize: number;
    color: string;
    opacity: number;
    rotation: number;
    posX: number;
    posY: number;
    watermarkImg: HTMLImageElement | null;
    imageScale: number;
    imageOpacity: number;
  }
) {
  ctx.save();
  ctx.globalAlpha = config.type === 'text' ? config.opacity : config.imageOpacity;

  const centerX = imgWidth * config.posX;
  const centerY = imgHeight * config.posY;

  const angleRad = (config.rotation * Math.PI) / 180;
  ctx.translate(centerX, centerY);
  ctx.rotate(angleRad);

  if (config.type === 'text' && config.text) {
    const fontSize = Math.max(8, Math.min(config.fontSize, 500));
    const fontFamily = 'Arial, Helvetica, sans-serif';
    ctx.font = `bold ${fontSize}px ${fontFamily}`;
    ctx.fillStyle = config.color;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(config.text, 0, 0);
  } else if (config.type === 'image' && config.watermarkImg) {
    const scale = Math.max(0.01, Math.min(config.imageScale / 100, 2));
    const w = config.watermarkImg.width * scale;
    const h = config.watermarkImg.height * scale;
    ctx.drawImage(config.watermarkImg, -w / 2, -h / 2, w, h);
  }

  ctx.restore();
}

function drawPreview(
  canvas: HTMLCanvasElement,
  sourceImg: HTMLImageElement,
  config: {
    type: WatermarkType;
    text: string;
    fontSize: number;
    color: string;
    opacity: number;
    rotation: number;
    posX: number;
    posY: number;
    watermarkImg: HTMLImageElement | null;
    imageScale: number;
    imageOpacity: number;
  }
) {
  const maxW = 900;
  let w = sourceImg.naturalWidth;
  let h = sourceImg.naturalHeight;
  if (w > maxW) {
    h = Math.round((h * maxW) / w);
    w = maxW;
  }
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d')!;
  ctx.clearRect(0, 0, w, h);
  ctx.drawImage(sourceImg, 0, 0, w, h);
  renderWatermark(ctx, w, h, config);
}

async function processImage(
  sourceImg: HTMLImageElement,
  config: {
    type: WatermarkType;
    text: string;
    fontSize: number;
    color: string;
    opacity: number;
    rotation: number;
    posX: number;
    posY: number;
    watermarkImg: HTMLImageElement | null;
    imageScale: number;
    imageOpacity: number;
  }
): Promise<{ blob: Blob; dataUrl: string }> {
  const w = sourceImg.naturalWidth;
  const h = sourceImg.naturalHeight;
  const offscreen = new OffscreenCanvas(w, h);
  const ctx = offscreen.getContext('2d')!;
  ctx.drawImage(sourceImg, 0, 0, w, h);
  renderWatermark(ctx as any, w, h, config);
  const blob = await offscreen.convertToBlob({ type: 'image/png' });
  const dataUrl = await blobToDataUrl(blob);
  return { blob, dataUrl };
}

function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.readAsDataURL(blob);
  });
}

function ImageModal({ src, name, onClose }: { src: string; name: string; onClose: () => void }) {
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => {
      document.body.style.overflow = '';
      document.removeEventListener('keydown', handler);
    };
  }, [onClose]);

  return (
    <div class="fixed inset-0 z-50 bg-black/90 flex flex-col items-center justify-center" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div class="flex items-center justify-between w-full px-4 py-3 shrink-0">
        <span class="text-white/70 text-sm truncate max-w-[70%]">{name}</span>
        <button onClick={onClose} class="text-white/70 hover:text-white text-2xl leading-none px-2 py-1">&times;</button>
      </div>
      <div class="flex-1 flex items-center justify-center p-4 overflow-auto">
        <img src={src} alt={name} class="max-w-full max-h-full object-contain" />
      </div>
    </div>
  );
}

export default function WatermarkTool({ t }: { t: Translations }) {
  const [files, setFiles] = useState<{ file: File; url: string }[]>([]);
  const [previewIdx, setPreviewIdx] = useState(0);
  const [previewImg, setPreviewImg] = useState<HTMLImageElement | null>(null);

  const [wmType, setWmType] = useState<WatermarkType>('text');
  const [wmText, setWmText] = useState('Watermark');
  const [wmFontSize, setWmFontSize] = useState(48);
  const [wmColor, setWmColor] = useState('#ff0000');
  const [wmOpacity, setWmOpacity] = useState(0.6);
  const [wmRotation, setWmRotation] = useState(0);
  const [wmPosX, setWmPosX] = useState(0.5);
  const [wmPosY, setWmPosY] = useState(0.5);

  const [wmImage, setWmImage] = useState<HTMLImageElement | null>(null);
  const [wmImageUrl, setWmImageUrl] = useState('');
  const [wmImageScale, setWmImageScale] = useState(30);
  const [wmImageOpacity, setWmImageOpacity] = useState(0.8);

  const [results, setResults] = useState<WatermarkedFile[]>([]);
  const [isApplying, setIsApplying] = useState(false);
  const [applyProgress, setApplyProgress] = useState(0);
  const [enlargedIdx, setEnlargedIdx] = useState<number | null>(null);

  const previewCanvasRef = useRef<HTMLCanvasElement>(null);
  const isDragging = useRef(false);

  const config = {
    type: wmType,
    text: wmText,
    fontSize: wmFontSize,
    color: wmColor,
    opacity: wmOpacity,
    rotation: wmRotation,
    posX: wmPosX,
    posY: wmPosY,
    watermarkImg: wmImage,
    imageScale: wmImageScale,
    imageOpacity: wmImageOpacity,
  };

  const loadPreviewImage = useCallback((url: string) => {
    const img = new Image();
    img.onload = () => setPreviewImg(img);
    img.src = url;
  }, []);

  const getCanvasCoords = (canvas: HTMLCanvasElement, clientX: number, clientY: number) => {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
      x: (clientX - rect.left) * scaleX,
      y: (clientY - rect.top) * scaleY,
    };
  };

  const handleCanvasDown = (clientX: number, clientY: number) => {
    const canvas = previewCanvasRef.current;
    if (!canvas) return;
    const { x, y } = getCanvasCoords(canvas, clientX, clientY);
    const dist = Math.hypot(x - canvas.width * wmPosX, y - canvas.height * wmPosY);
    if (dist < 50) {
      isDragging.current = true;
    }
  };

  const handleCanvasMouseDown = (e: MouseEvent) => {
    handleCanvasDown(e.clientX, e.clientY);
  };

  const handleCanvasMouseMove = (e: MouseEvent) => {
    const canvas = previewCanvasRef.current;
    if (!canvas) return;
    const { x, y } = getCanvasCoords(canvas, e.clientX, e.clientY);
    if (isDragging.current) {
      setWmPosX(Math.max(0, Math.min(1, x / canvas.width)));
      setWmPosY(Math.max(0, Math.min(1, y / canvas.height)));
      canvas.style.cursor = 'grabbing';
    } else {
      const dist = Math.hypot(x - canvas.width * wmPosX, y - canvas.height * wmPosY);
      canvas.style.cursor = dist < 50 ? 'grab' : 'crosshair';
    }
  };

  const handleCanvasMouseUp = () => {
    isDragging.current = false;
    const canvas = previewCanvasRef.current;
    if (canvas) canvas.style.cursor = 'crosshair';
  };

  const handleCanvasTouchStart = (e: TouchEvent) => {
    if (e.touches.length !== 1) return;
    handleCanvasDown(e.touches[0].clientX, e.touches[0].clientY);
    if (isDragging.current) e.preventDefault();
  };

  const handleCanvasTouchMove = (e: TouchEvent) => {
    const canvas = previewCanvasRef.current;
    if (!canvas || !isDragging.current || e.touches.length !== 1) return;
    e.preventDefault();
    const touch = e.touches[0];
    const { x, y } = getCanvasCoords(canvas, touch.clientX, touch.clientY);
    setWmPosX(Math.max(0, Math.min(1, x / canvas.width)));
    setWmPosY(Math.max(0, Math.min(1, y / canvas.height)));
  };

  const handleCanvasTouchEnd = () => {
    isDragging.current = false;
  };

  useEffect(() => {
    const up = () => { isDragging.current = false; };
    window.addEventListener('mouseup', up);
    window.addEventListener('touchend', up);
    return () => {
      window.removeEventListener('mouseup', up);
      window.removeEventListener('touchend', up);
    };
  }, []);

  useEffect(() => {
    if (files.length > 0 && previewIdx < files.length) {
      loadPreviewImage(files[previewIdx].url);
    }
  }, [files, previewIdx]);

  // Draw preview whenever config or preview image changes
  useEffect(() => {
    const canvas = previewCanvasRef.current;
    if (!canvas || !previewImg) return;
    drawPreview(canvas, previewImg, config);
  }, [previewImg, wmText, wmFontSize, wmColor, wmOpacity, wmRotation, wmPosX, wmPosY, wmImage, wmImageScale, wmImageOpacity, wmType]);

  const handleFiles = (fileList: FileList | null) => {
    if (!fileList) return;
    const newFiles: { file: File; url: string }[] = [];
    for (let i = 0; i < fileList.length; i++) {
      const f = fileList[i];
      if (!f.type.startsWith('image/')) continue;
      newFiles.push({ file: f, url: URL.createObjectURL(f) });
    }
    if (newFiles.length > 0) {
      setFiles((prev) => [...prev, ...newFiles]);
      setResults([]);
    }
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    handleFiles(e.dataTransfer?.files ?? null);
  };

  const handleInput = (e: Event) => {
    const input = e.target as HTMLInputElement;
    handleFiles(input.files);
    input.value = '';
  };

  const handleWmImageUpload = (e: Event) => {
    const input = e.target as HTMLInputElement;
    const f = input.files?.[0];
    if (!f) return;
    const url = URL.createObjectURL(f);
    const img = new Image();
    img.onload = () => {
      setWmImage(img);
      setWmImageUrl(url);
    };
    img.src = url;
    input.value = '';
  };

  const handleApplyAll = async () => {
    if (files.length === 0 || isApplying) return;
    setIsApplying(true);
    setApplyProgress(0);
    const processed: WatermarkedFile[] = [];
    track('tool_watermark_start', {
      file_count: files.length,
      watermark_type: config.type,
    });

    // Preload all images
    const imgs: HTMLImageElement[] = [];
    for (const f of files) {
      const img = await new Promise<HTMLImageElement>((resolve) => {
        const el = new Image();
        el.onload = () => resolve(el);
        el.src = f.url;
      });
      imgs.push(img);
    }

    for (let i = 0; i < imgs.length; i++) {
      const img = imgs[i];
      const { blob, dataUrl } = await processImage(img, config);
      const origName = files[i].file.name;
      const dotIdx = origName.lastIndexOf('.');
      const baseName = dotIdx > 0 ? origName.substring(0, dotIdx) : origName;
      processed.push({
        name: `${baseName}_watermarked.png`,
        origUrl: files[i].url,
        dataUrl,
        blob,
        width: img.naturalWidth,
        height: img.naturalHeight,
      });
      setApplyProgress(Math.round(((i + 1) / imgs.length) * 100));
    }

    setResults(processed);
    setIsApplying(false);
    track('tool_watermark_done', {
      file_count: processed.length,
      watermark_type: config.type,
    });
  };

  const handleDownloadSingle = (item: WatermarkedFile) => {
    const url = URL.createObjectURL(item.blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = item.name;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadZip = async () => {
    if (results.length === 0) return;
    const JSZip = (await import('jszip')).default;
    const zip = new JSZip();
    for (const item of results) {
      zip.file(item.name, item.blob);
    }
    const zipBlob = await zip.generateAsync({ type: 'blob' });
    const url = URL.createObjectURL(zipBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'watermarked_images.zip';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClearAll = () => {
    for (const f of files) URL.revokeObjectURL(f.url);
    for (const r of results) URL.revokeObjectURL(r.origUrl);
    setFiles([]);
    setResults([]);
    setPreviewImg(null);
    setPreviewIdx(0);
  };

  return (
    <div class="w-full max-w-6xl mx-auto px-4 py-8">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">{t.title}</h1>
        <p class="text-gray-500">{t.subtitle}</p>
      </div>

      {/* Upload Area */}
      {files.length === 0 && (
        <div
          class="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center cursor-pointer hover:border-primary-500 hover:bg-primary-50/30 transition-colors"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => document.getElementById('wm-file-input')?.click()}
        >
          <div class="text-4xl mb-3 text-gray-400">&#128444;</div>
          <p class="text-gray-600 font-medium">{t.uploadHint}</p>
          <p class="text-gray-400 text-sm mt-1">{t.uploadFormats}</p>
          <input id="wm-file-input" type="file" accept="image/*" multiple class="hidden" onChange={handleInput} />
        </div>
      )}

      {files.length > 0 && (
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: File list */}
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-gray-800">{files.length} {files.length === 1 ? 'image' : 'images'}</h3>
              <div class="flex gap-2">
                <button
                  class="text-sm text-gray-400 hover:text-primary-600"
                  onClick={() => document.getElementById('wm-file-input')?.click()}
                >
                  + Add
                </button>
                <button class="text-sm text-gray-400 hover:text-red-500" onClick={handleClearAll}>{t.clearAll}</button>
              </div>
              <input id="wm-file-input" type="file" accept="image/*" multiple class="hidden" onChange={handleInput} />
            </div>
            <div class="space-y-2 max-h-[400px] overflow-y-auto">
              {files.map((f, i) => (
                <div
                  key={f.url}
                  class={`flex items-center gap-3 p-2 rounded-lg cursor-pointer border transition-colors ${i === previewIdx ? 'border-primary-500 bg-primary-50' : 'border-gray-100 hover:border-gray-200'}`}
                  onClick={() => setPreviewIdx(i)}
                >
                  <img src={f.url} alt="" class="w-10 h-10 rounded object-cover shrink-0" />
                  <span class="text-sm text-gray-700 truncate flex-1">{f.file.name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Center: Preview */}
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <h3 class="font-semibold text-gray-800 mb-3">{t.preview}</h3>
            <div class="aspect-square bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center">
              {previewImg ? (
                <canvas ref={previewCanvasRef} class="max-w-full max-h-full object-contain cursor-crosshair" onMouseDown={handleCanvasMouseDown} onMouseMove={handleCanvasMouseMove} onMouseUp={handleCanvasMouseUp} onMouseLeave={handleCanvasMouseUp} onTouchStart={handleCanvasTouchStart} onTouchMove={handleCanvasTouchMove} onTouchEnd={handleCanvasTouchEnd} />
              ) : (
                <p class="text-gray-400 text-sm">{t.noImages}</p>
              )}
            </div>
            {previewImg && (
              <p class="text-center text-xs text-primary-600 font-medium mt-2 bg-primary-50 rounded-lg py-1.5">{t.dragHint}</p>
            )}
          </div>

          {/* Right: Controls */}
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <h3 class="font-semibold text-gray-800 mb-4">{t.typeLabel}</h3>

            {/* Type toggle */}
            <div class="flex gap-2 mb-4">
              <button
                class={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${wmType === 'text' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                onClick={() => setWmType('text')}
              >
                {t.textType}
              </button>
              <button
                class={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${wmType === 'image' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                onClick={() => setWmType('image')}
              >
                {t.imageType}
              </button>
            </div>

            {/* Text watermark settings */}
            {wmType === 'text' && (
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Text</label>
                  <input
                    type="text"
                    value={wmText}
                    onInput={(e) => setWmText((e.target as HTMLInputElement).value)}
                    placeholder={t.textPlaceholder}
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">{t.fontSize}</label>
                  <div class="flex items-center gap-2">
                    <input
                      type="range" min="8" max="200" value={wmFontSize}
                      onInput={(e) => setWmFontSize(parseInt((e.target as HTMLInputElement).value))}
                      class="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                    />
                    <span class="text-sm font-mono text-gray-600 w-10 text-right">{wmFontSize}</span>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <label class="text-sm font-medium text-gray-700">{t.color}</label>
                  <input
                    type="color" value={wmColor}
                    onInput={(e) => setWmColor((e.target as HTMLInputElement).value)}
                    class="w-8 h-8 rounded cursor-pointer border border-gray-300"
                  />
                </div>
              </div>
            )}

            {/* Image watermark settings */}
            {wmType === 'image' && (
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Logo</label>
                  {wmImageUrl ? (
                    <div class="flex items-center gap-3">
                      <img src={wmImageUrl} alt="watermark" class="w-12 h-12 object-contain rounded border border-gray-200" />
                      <button
                        class="text-sm text-gray-400 hover:text-red-500"
                        onClick={() => { setWmImage(null); setWmImageUrl(''); }}
                      >
                        Remove
                      </button>
                    </div>
                  ) : (
                    <div
                      class="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center cursor-pointer hover:border-primary-500 transition-colors"
                      onClick={() => document.getElementById('wm-img-input')?.click()}
                    >
                      <span class="text-sm text-gray-400">{t.imageWatermarkHint}</span>
                    </div>
                  )}
                  <input id="wm-img-input" type="file" accept="image/*" class="hidden" onChange={handleWmImageUpload} />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">{t.imageScale}</label>
                  <div class="flex items-center gap-2">
                    <input
                      type="range" min="5" max="100" value={wmImageScale}
                      onInput={(e) => setWmImageScale(parseInt((e.target as HTMLInputElement).value))}
                      class="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                    />
                    <span class="text-sm font-mono text-gray-600 w-10 text-right">{wmImageScale}%</span>
                  </div>
                </div>
              </div>
            )}

            {/* Shared controls: opacity, rotation, position */}
            <div class="space-y-4 mt-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">{t.opacity}</label>
                <div class="flex items-center gap-2">
                  <input
                    type="range" min="1" max="100" value={Math.round((wmType === 'text' ? wmOpacity : wmImageOpacity) * 100)}
                    onInput={(e) => {
                      const v = parseInt((e.target as HTMLInputElement).value) / 100;
                      if (wmType === 'text') setWmOpacity(v); else setWmImageOpacity(v);
                    }}
                    class="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                  />
                  <span class="text-sm font-mono text-gray-600 w-10 text-right">{Math.round((wmType === 'text' ? wmOpacity : wmImageOpacity) * 100)}%</span>
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">{t.rotation}</label>
                <div class="flex items-center gap-2">
                  <input
                    type="range" min="-180" max="180" value={wmRotation}
                    onInput={(e) => setWmRotation(parseInt((e.target as HTMLInputElement).value))}
                    class="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                  />
                  <span class="text-sm font-mono text-gray-600 w-10 text-right">{wmRotation}&deg;</span>
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">{t.position}</label>
                <div class="grid grid-cols-3 gap-1">
                  {POSITIONS.map((pos, i) => {
                    const active = Math.abs(pos.x - wmPosX) < 0.005 && Math.abs(pos.y - wmPosY) < 0.005;
                    return (
                      <button
                        key={i}
                        class={`py-2 rounded text-sm font-medium transition-colors ${active ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
                        onClick={() => { setWmPosX(pos.x); setWmPosY(pos.y); }}
                      >
                        {pos.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Apply button */}
            <button
              class={`mt-6 w-full py-3 rounded-lg font-semibold text-white transition-colors ${isApplying ? 'bg-gray-400 cursor-not-allowed' : 'bg-primary-600 hover:bg-primary-700'}`}
              onClick={handleApplyAll}
              disabled={isApplying}
            >
              {isApplying ? `${t.applying} ${applyProgress}%` : t.applyAll}
            </button>
          </div>
        </div>
      )}

      {/* Results Gallery */}
      {results.length > 0 && (
        <div class="mt-8 bg-white rounded-xl border border-gray-200 p-4">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold text-gray-800">{t.results} ({results.length})</h3>
            <button
              class="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-5 py-2 text-sm font-semibold text-white hover:bg-primary-700 transition-colors"
              onClick={handleDownloadZip}
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {t.downloadAllZip}
            </button>
          </div>

          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
            {results.map((item, i) => (
              <div key={i} class="group relative rounded-lg border border-gray-200 overflow-hidden bg-gray-50">
                <img
                  src={item.dataUrl}
                  alt={item.name}
                  class="w-full aspect-square object-cover cursor-pointer"
                  onClick={() => setEnlargedIdx(i)}
                  title={t.viewImage}
                />
                <div class="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100">
                  <button
                    class="bg-white/90 rounded-full p-1.5 hover:bg-white transition-colors"
                    onClick={() => setEnlargedIdx(i)}
                    title={t.viewImage}
                  >
                    <svg class="h-4 w-4 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                    </svg>
                  </button>
                  <button
                    class="bg-white/90 rounded-full p-1.5 hover:bg-white transition-colors"
                    onClick={() => handleDownloadSingle(item)}
                    title={t.downloadSingle}
                  >
                    <svg class="h-4 w-4 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  </button>
                </div>
                <p class="px-2 py-1 text-xs text-gray-500 truncate">{item.name}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Image Modal */}
      {enlargedIdx !== null && results[enlargedIdx] && (
        <ImageModal
          src={results[enlargedIdx].dataUrl}
          name={results[enlargedIdx].name}
          onClose={() => setEnlargedIdx(null)}
        />
      )}
    </div>
  );
}
