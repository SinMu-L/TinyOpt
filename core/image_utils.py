import os
from datetime import datetime
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core.config import FORMATS, SUPPORTED_EXTENSIONS, LOCAL_JPEG_QUALITY
from core.utils import calc_watermark_position


def render_text_watermark(text, font_path, font_size, font_color):
    """Render text as RGBA PIL Image with anti-aliasing."""
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    dummy = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    bbox = dummy.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0] + 20
    th = bbox[3] - bbox[1] + 20
    wm = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    draw = ImageDraw.Draw(wm)
    draw.text((-bbox[0] + 10, -bbox[1] + 10), text, font=font,
              fill=(*font_color[:3], 255))
    return wm


def apply_watermark_to_image(image, watermark_type, watermark_img=None,
                              watermark_text="", font_path=None, font_size=48,
                              font_color=(255, 255, 255), x_ratio=0.85, y_ratio=0.85,
                              opacity=80, scale=15, margin_x=20, margin_y=20):
    """Apply watermark to a PIL Image, return watermarked Image."""
    if watermark_type not in ("image", "text", "both"):
        return image
    img = image.convert('RGBA') if image.mode != 'RGBA' else image.copy()
    img_w, img_h = img.size

    wm = None
    if watermark_type == "image" and watermark_img is not None:
        wm = watermark_img.copy()
        if wm.mode != 'RGBA':
            wm = wm.convert('RGBA')
        wm_w = max(1, int(img_w * scale / 100))
        wm_h = max(1, int(wm.height * wm_w / wm.width))
        wm = wm.resize((wm_w, wm_h), Image.LANCZOS)

    elif watermark_type == "text" and watermark_text:
        wm = render_text_watermark(watermark_text, font_path, font_size, font_color)

    elif watermark_type == "both" and watermark_img is not None and watermark_text:
        wm_img = watermark_img.copy()
        if wm_img.mode != 'RGBA':
            wm_img = wm_img.convert('RGBA')
        wm_w = max(1, int(img_w * scale / 100))
        wm_h = max(1, int(wm_img.height * wm_w / wm_img.width))
        wm_img = wm_img.resize((wm_w, wm_h), Image.LANCZOS)
        wm_txt = render_text_watermark(watermark_text, font_path, font_size, font_color)
        combined_w = max(wm_img.width, wm_txt.width)
        combined_h = wm_img.height + 5 + wm_txt.height
        wm = Image.new('RGBA', (combined_w, combined_h), (0, 0, 0, 0))
        wm.paste(wm_img, ((combined_w - wm_img.width) // 2, 0), wm_img)
        wm.paste(wm_txt, ((combined_w - wm_txt.width) // 2, wm_img.height + 5), wm_txt)

    if wm is None:
        return image

    if opacity < 100 and wm.mode == 'RGBA':
        r, g, b, a = wm.split()
        a = a.point(lambda x: int(x * opacity / 100))
        wm = Image.merge('RGBA', (r, g, b, a))

    result = Image.new('RGBA', img.size, (0, 0, 0, 0))
    result.paste(img, (0, 0))

    pos = calc_watermark_position(img_w, img_h, wm.width, wm.height,
                                   x_ratio, y_ratio, margin_x, margin_y)
    result.paste(wm, pos, wm)

    if image.mode != 'RGBA':
        result = result.convert(image.mode)
    return result


def generate_rename_preview(file_paths, pattern, start_index=1, pad_digits=3, date_format="%Y%m%d"):
    """Generate preview of renamed files. Returns list of (old_path, new_name)."""
    results = []
    today = datetime.now().strftime(date_format)
    for i, fp in enumerate(file_paths):
        p = Path(fp)
        name = p.stem
        ext = p.suffix
        new_name = pattern
        new_name = new_name.replace("{name}", name)
        new_name = new_name.replace("{index}", str(start_index + i).zfill(pad_digits))
        new_name = new_name.replace("{date}", today)
        new_name += ext
        results.append((fp, new_name))
    return results


def adjust_aspect_ratio(image, target_w, target_h, mode="crop", anchor="center",
                         fill_color=(255, 255, 255)):
    """Adjust image aspect ratio using PIL. Returns the adjusted PIL Image."""
    target_ratio = target_w / target_h
    orig_w, orig_h = image.size
    orig_ratio = orig_w / orig_h

    if mode == "crop":
        if abs(orig_ratio - target_ratio) < 0.001:
            return image.copy()

        if orig_ratio > target_ratio:
            crop_w = int(orig_h * target_ratio)
            crop_h = orig_h
        else:
            crop_w = orig_w
            crop_h = int(orig_w / target_ratio)

        ox = {"center": (orig_w - crop_w) // 2, "top_left": 0,
              "top_center": (orig_w - crop_w) // 2, "top_right": orig_w - crop_w,
              "center_left": 0, "center_right": orig_w - crop_w,
              "bottom_left": 0, "bottom_center": (orig_w - crop_w) // 2,
              "bottom_right": orig_w - crop_w}.get(anchor, (orig_w - crop_w) // 2)

        oy = {"center": (orig_h - crop_h) // 2, "top_left": 0,
              "top_center": 0, "top_right": 0,
              "center_left": (orig_h - crop_h) // 2,
              "center_right": (orig_h - crop_h) // 2,
              "bottom_left": orig_h - crop_h, "bottom_center": orig_h - crop_h,
              "bottom_right": orig_h - crop_h}.get(anchor, (orig_h - crop_h) // 2)

        return image.crop((ox, oy, ox + crop_w, oy + crop_h))

    elif mode == "pad":
        if abs(orig_ratio - target_ratio) < 0.001:
            return image.copy()

        if orig_w / orig_h > target_ratio:
            new_w = orig_w
            new_h = int(orig_w / target_ratio)
        else:
            new_h = orig_h
            new_w = int(orig_h * target_ratio)

        canvas = Image.new("RGB", (new_w, new_h), fill_color)
        img_to_paste = image.copy()
        if img_to_paste.mode == "RGBA":
            canvas = canvas.convert("RGBA")
        offset_x = (new_w - orig_w) // 2
        offset_y = (new_h - orig_h) // 2
        if img_to_paste.mode in ("RGBA", "LA", "P"):
            canvas.paste(img_to_paste, (offset_x, offset_y), img_to_paste)
        else:
            canvas.paste(img_to_paste, (offset_x, offset_y))
        return canvas

    elif mode == "stretch":
        if abs(orig_ratio - target_ratio) < 0.001:
            return image.copy()
        return image.resize((target_w, target_h), Image.LANCZOS)

    return image.copy()


def local_compress_image(image_data, source_ext, target_format="", resize_params=None, quality=LOCAL_JPEG_QUALITY):
    """Compress image locally using PIL. Returns (success, compressed_data, error)."""
    try:
        from PIL import Image as PILImg
        from io import BytesIO as ImgBytesIO

        img = PILImg.open(ImgBytesIO(image_data))

        fmt = target_format if target_format else source_ext.lstrip(".")
        fmt = fmt.lower()
        if fmt in ("jpg", "jpeg"):
            fmt = "jpeg"
        elif fmt == "tif":
            fmt = "tiff"

        if resize_params:
            method = resize_params.get("method", "fit")
            w = resize_params.get("width", 0)
            h = resize_params.get("height", 0)
            if method == "scale" and w > 0:
                pct = w / 100.0
                img = img.resize((max(1, int(img.width * pct)), max(1, int(img.height * pct))), PILImg.LANCZOS)
            elif method == "fit" and (w > 0 or h > 0):
                img.thumbnail((w if w > 0 else img.width, h if h > 0 else img.height), PILImg.LANCZOS)
            elif method == "cover" and w > 0 and h > 0:
                ratio = max(w / img.width, h / img.height)
                nw, nh = int(img.width * ratio), int(img.height * ratio)
                img = img.resize((nw, nh), PILImg.LANCZOS)
                img = img.crop(((nw - w) // 2, (nh - h) // 2, (nw - w) // 2 + w, (nh - h) // 2 + h))
            elif method == "thumb" and w > 0 and h > 0:
                img = img.resize((w, h), PILImg.LANCZOS)

        output = ImgBytesIO()

        if fmt == "jpeg":
            if img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")
            img.save(output, format="JPEG", quality=quality, optimize=True)
        elif fmt == "png":
            if img.mode not in ("RGBA", "RGB", "L", "LA", "P"):
                img = img.convert("RGBA")
            img.save(output, format="PNG", optimize=True)
        elif fmt == "webp":
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")
            img.save(output, format="WebP", quality=quality)
        elif fmt == "gif":
            img.save(output, format="GIF", optimize=True)
        elif fmt == "tiff":
            img.save(output, format="TIFF", compression="tiff_lzw")
        elif fmt == "bmp":
            img.save(output, format="BMP")
        elif fmt == "ico":
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img.save(output, format="ICO", sizes=[(256, 256)])
        else:
            return False, None, f"Unsupported local format: {fmt}"

        return True, output.getvalue(), None
    except Exception as e:
        return False, None, str(e)
