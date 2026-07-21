import os
import re
import time
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from PyQt5.QtCore import QThread, pyqtSignal

from i18n import T

SITEMAP_PATHS = [
    "/sitemap.xml",
    "/sitemap_index.xml",
    "/sitemap-index.xml",
    "/wp-sitemap.xml",
]

IMG_SRC_RE = re.compile(
    r'<img[^>]+src\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE,
)

MAX_WORKERS = 10
REQUEST_TIMEOUT = 15
MAX_PAGES = 200

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
                    ".bmp", ".ico", ".tiff", ".tif", ".avif"}


class WebsiteWorker(QThread):
    progress = pyqtSignal(int, int)
    log = pyqtSignal(str, bool)
    image_info = pyqtSignal(str, int)
    image_downloaded = pyqtSignal(str, bool)
    finished_signal = pyqtSignal(dict)

    def __init__(self, domain_url, save_to_local=False, output_dir=""):
        super().__init__()
        self.domain_url = domain_url.strip()
        self.save_to_local = save_to_local
        self.output_dir = output_dir
        self._is_cancelled = False
        self._images = {}
        self._lock = Lock()
        self._session = None

    def cancel(self):
        self._is_cancelled = True

    def _normalize_url(self, url):
        parsed = urlparse(url)
        if not parsed.scheme:
            url = "https://" + url
        return url.rstrip("/")

    def _get_session(self):
        if self._session is None:
            session = requests.Session()
            session.headers.update({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            })
            self._session = session
        return self._session

    def _request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        try:
            return getattr(self._get_session(), method)(url, **kwargs)
        except Exception:
            return None

    def _find_sitemap(self, base_url):
        for path in SITEMAP_PATHS:
            if self._is_cancelled:
                return None
            sitemap_url = base_url + path
            self.log.emit(T("website.sitemap_trying", url=sitemap_url), False)
            resp = self._request("get", sitemap_url)
            if (resp and resp.status_code == 200
                    and "xml" in resp.headers.get("Content-Type", "").lower()):
                self.log.emit(T("website.sitemap_found", url=sitemap_url), False)
                return sitemap_url
        return None

    def _get_domain_root(self, url):
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _try_as_sitemap(self, url):
        resp = self._request("get", url)
        if not resp or resp.status_code != 200:
            return False
        if "xml" not in resp.headers.get("Content-Type", "").lower():
            return False
        try:
            root = ET.fromstring(resp.content)
            tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
            return tag in ("urlset", "sitemapindex")
        except Exception:
            return False

    def _parse_sitemap(self, sitemap_url):
        page_urls = []
        try:
            resp = self._request("get", sitemap_url)
            if not resp:
                return []
            root = ET.fromstring(resp.content)
            for loc in root.iter():
                tag = loc.tag.split("}")[-1] if "}" in loc.tag else loc.tag
                if tag == "loc" and loc.text and loc.text.strip():
                    page_urls.append(loc.text.strip())
            page_urls = list(dict.fromkeys(page_urls))
        except Exception as e:
            self.log.emit(T("website.sitemap_parse_error", error=str(e)), True)
        return page_urls[:MAX_PAGES]

    def _extract_images_from_page(self, page_url):
        images = []
        try:
            resp = self._request("get", page_url)
            if not resp or resp.status_code != 200:
                return images
            content_type = resp.headers.get("Content-Type", "").lower()
            if "html" not in content_type:
                return images
            html = resp.text
            matches = IMG_SRC_RE.findall(html)
            for src in matches:
                if self._is_cancelled:
                    break
                src = src.strip()
                if not src or src.startswith("data:"):
                    continue
                absolute_url = urljoin(page_url, src)
                if absolute_url.startswith("http"):
                    images.append(absolute_url)
        except Exception:
            pass
        return images

    def _is_image_url(self, url):
        ext = os.path.splitext(urlparse(url).path)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            return True
        return False

    def _get_image_size(self, image_url):
        try:
            resp = self._request("head", image_url)
            if resp and resp.status_code == 200:
                content_length = resp.headers.get("Content-Length")
                if content_length:
                    return int(content_length)
        except Exception:
            pass
        return -1

    def _download_image(self, image_url, output_dir):
        try:
            resp = self._request("get", image_url)
            if not resp or resp.status_code != 200:
                return False
            parsed = urlparse(image_url)
            filename = os.path.basename(parsed.path)
            if not filename or "." not in filename:
                filename = f"image_{abs(hash(image_url)) % 100000}.jpg"
            filepath = os.path.join(output_dir, filename)
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(filepath):
                filepath = os.path.join(output_dir, f"{base}_{counter}{ext}")
                counter += 1
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return True
        except Exception:
            return False

    def run(self):
        stats = {
            "total_images": 0,
            "total_size": 0,
            "downloaded": 0,
            "failed": 0,
        }

        base_url = self._normalize_url(self.domain_url)
        self.log.emit(T("website.checking_sitemap", url=base_url), False)

        sitemap_url = None
        if self._try_as_sitemap(base_url):
            sitemap_url = base_url
            self.log.emit(T("website.sitemap_found", url=base_url), False)
        else:
            domain_root = self._get_domain_root(base_url)
            sitemap_url = self._find_sitemap(domain_root)

        if self._is_cancelled:
            self.finished_signal.emit(stats)
            return

        if not sitemap_url:
            self.log.emit(T("website.sitemap_not_found"), True)
            self.finished_signal.emit(stats)
            return

        page_urls = self._parse_sitemap(sitemap_url)
        if self._is_cancelled:
            self.finished_signal.emit(stats)
            return

        self.log.emit(T("website.sitemap_page_count", count=len(page_urls)), False)

        if not page_urls:
            self.log.emit(T("website.no_pages_in_sitemap"), True)
            self.finished_signal.emit(stats)
            return

        all_images = set()
        self.log.emit(T("website.fetching_pages"), False)

        total_pages = len(page_urls)
        completed_pages = 0

        def fetch_page(url):
            if self._is_cancelled:
                return []
            time.sleep(0.05)
            return self._extract_images_from_page(url)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(fetch_page, url): url for url in page_urls}
            for future in as_completed(futures):
                if self._is_cancelled:
                    for f in futures:
                        f.cancel()
                    break
                try:
                    images = future.result(timeout=30)
                    all_images.update(images)
                except Exception:
                    pass
                completed_pages += 1
                self.progress.emit(completed_pages, total_pages)
                if completed_pages % 5 == 0 or completed_pages == total_pages:
                    self.log.emit(
                        T("website.page_progress",
                          done=completed_pages, total=total_pages), False,
                    )

        if self._is_cancelled:
            self.log.emit(T("website.worker_cancelled"), False)
            self.finished_signal.emit(stats)
            return

        image_list = [url for url in all_images if self._is_image_url(url)]
        total_images = len(image_list)
        self.log.emit(T("website.images_found", count=total_images), False)

        if not image_list:
            self.log.emit(T("website.no_images_found"), True)
            self.finished_signal.emit(stats)
            return

        self.log.emit(T("website.checking_sizes"), False)

        def check_image(url):
            if self._is_cancelled:
                return (url, -1)
            size = self._get_image_size(url)
            return (url, size)

        checked = 0
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(check_image, url): url for url in image_list}
            for future in as_completed(futures):
                if self._is_cancelled:
                    for f in futures:
                        f.cancel()
                    break
                try:
                    url, size = future.result(timeout=20)
                    if size > 0:
                        with self._lock:
                            self._images[url] = size
                    self.image_info.emit(url, size)
                except Exception:
                    pass
                checked += 1
                self.progress.emit(checked, total_images)

        if self._is_cancelled:
            self.log.emit(T("website.worker_cancelled"), False)
            self.finished_signal.emit(stats)
            return

        if self.save_to_local and self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)
            self.log.emit(T("website.downloading_start"), False)
            downloaded = 0

            def download_image(url):
                if self._is_cancelled:
                    return (url, False)
                success = self._download_image(url, self.output_dir)
                return (url, success)

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {executor.submit(download_image, url): url for url in image_list}
                for future in as_completed(futures):
                    if self._is_cancelled:
                        for f in futures:
                            f.cancel()
                        break
                    try:
                        url, success = future.result(timeout=30)
                        if success:
                            downloaded += 1
                        self.image_downloaded.emit(url, success)
                    except Exception:
                        pass

            if self._is_cancelled:
                self.log.emit(T("website.worker_cancelled"), False)
                stats["downloaded"] = downloaded
                self.finished_signal.emit(stats)
                return

            stats["downloaded"] = downloaded

        total_size = sum(s for s in self._images.values() if s > 0)
        stats["total_images"] = total_images
        stats["total_size"] = total_size
        stats["failed"] = total_images - len(self._images)

        self.log.emit(T("website.analysis_complete"), False)
        self.finished_signal.emit(stats)
