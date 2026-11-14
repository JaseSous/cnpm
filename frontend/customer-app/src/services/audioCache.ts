/**
 * Dịch vụ bộ nhớ đệm âm thanh (Audio Cache API)
 * Lưu trữ các file âm thanh thuyết minh vào trình duyệt để tối ưu băng thông
 * và hỗ trợ phát mượt mà khi mạng yếu hoặc offline.
 */

const CACHE_NAME = 'linh-ung-audio-cache-v1';

export async function getCachedAudioUrl(audioUrl: string): Promise<string> {
  if (!('caches' in window) || !audioUrl) {
    return audioUrl;
  }

  try {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(audioUrl);

    if (cachedResponse) {
      const blob = await cachedResponse.blob();
      return URL.createObjectURL(blob);
    }

    // Không chặn luồng phát - tải ngầm vào Cache API khi có thể
    cacheAudioInBackground(audioUrl).catch(() => {});
    return audioUrl;
  } catch (err) {
    console.warn('Lỗi truy xuất Audio Cache API:', err);
    return audioUrl;
  }
}

export async function cacheAudioInBackground(audioUrl: string): Promise<void> {
  if (!('caches' in window) || !audioUrl || audioUrl.startsWith('blob:')) {
    return;
  }

  try {
    const cache = await caches.open(CACHE_NAME);
    const existing = await cache.match(audioUrl);
    if (!existing) {
      const res = await fetch(audioUrl, { mode: 'cors' });
      if (res.ok) {
        await cache.put(audioUrl, res);
      }
    }
  } catch (err) {
    // Tự động bỏ qua nếu offline hoặc CORS không hỗ trợ Cache API
  }
}
