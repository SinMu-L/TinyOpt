import os


def format_size(size_bytes):
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024*1024):.1f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes // 1024} KB"
    return f"{size_bytes} B"


def find_font_path(family_name):
    """Find font file path on Windows by family name."""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                if name.split('&')[0].strip().lower() == family_name.lower():
                    winreg.CloseKey(key)
                    fonts_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
                    return os.path.join(fonts_dir, value)
            except OSError:
                break
            i += 1
        winreg.CloseKey(key)
    except:
        pass
    fallback_map = {
        "Arial": "arial.ttf",
        "Tahoma": "tahoma.ttf",
        "Verdana": "verdana.ttf",
        "Times New Roman": "times.ttf",
        "Courier New": "cour.ttf",
        "微软雅黑": "msyh.ttc",
        "宋体": "simsun.ttc",
        "黑体": "simhei.ttf",
        "楷体": "simkai.ttf",
    }
    if family_name in fallback_map:
        fonts_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
        path = os.path.join(fonts_dir, fallback_map[family_name])
        if os.path.exists(path):
            return path
    return None


def calc_watermark_position(img_w, img_h, wm_w, wm_h, x_ratio, y_ratio, margin_x=20, margin_y=20):
    """Calculate watermark position from ratio (0-1) with margin clamping."""
    avail_w = max(1, img_w - wm_w)
    avail_h = max(1, img_h - wm_h)
    x = int(margin_x + (avail_w - 2 * margin_x) * x_ratio)
    y = int(margin_y + (avail_h - 2 * margin_y) * y_ratio)
    x = max(margin_x, min(img_w - wm_w - margin_x, x))
    y = max(margin_y, min(img_h - wm_h - margin_y, y))
    return (x, y)
