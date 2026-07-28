export type TrackParams = Record<string, string | number | boolean | undefined>;

declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
    dataLayer?: IArguments[];
    __gaLoaded?: boolean;
    __loadGA?: () => void;
  }
}

/** Send a GA4 event only after cookie consent. Never send PII or file contents. */
export function track(event: string, params?: TrackParams): void {
  if (typeof window === 'undefined') return;
  try {
    if (localStorage.getItem('cookie_consent') !== 'accepted') return;
  } catch {
    return;
  }

  const payload = params
    ? Object.fromEntries(
        Object.entries(params).filter(([, v]) => v !== undefined)
      )
    : undefined;

  window.dataLayer = window.dataLayer || [];
  if (typeof window.gtag !== 'function') {
    window.gtag = function gtag(this: void) {
      window.dataLayer!.push(arguments as unknown as IArguments);
    };
  }

  if (payload && Object.keys(payload).length > 0) {
    window.gtag('event', event, payload);
  } else {
    window.gtag('event', event);
  }
}
