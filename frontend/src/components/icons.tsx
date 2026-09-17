import type { SVGProps } from 'react';

type P = SVGProps<SVGSVGElement>;

function I({ children, ...props }: P) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export const CloudSun = (p: P) => (
  <I {...p}>
    <path d="M6 16a4 4 0 1 1 2-7 5.5 5.5 0 0 1 10.5 2H19a3 3 0 0 1 0 6H6Z" />
    <path d="M7 4V2m-3 4L2 4m9 2 2-2" />
  </I>
);

export const Cloud = (p: P) => (
  <I {...p}>
    <path d="M5 18a4 4 0 1 1 2-7 5.5 5.5 0 0 1 10.5 0H19a3 3 0 0 1 0 6H5Z" />
  </I>
);

export const CloudRain = (p: P) => (
  <I {...p}>
    <path d="M5 15a4 4 0 1 1 2-7 5.5 5.5 0 0 1 10.5 0H19a3 3 0 0 1 0 6H5Z" />
    <path d="m8 18-1 3m5-3-1 3m5-3-1 3" />
  </I>
);

export const CloudLightning = (p: P) => (
  <I {...p}>
    <path d="M6 16a4 4 0 1 1 2-7 5.5 5.5 0 0 1 10.5 0H19a3 3 0 0 1 0 6H6Z" />
    <path d="m13 14-3 5h4l-2 5" />
  </I>
);

export const CloudSnow = (p: P) => (
  <I {...p}>
    <path d="M5 15a4 4 0 1 1 2-7 5.5 5.5 0 0 1 10.5 0H19a3 3 0 0 1 0 6H5Z" />
    <path d="M8 18h.01M8 21h.01M12 19h.01M12 22h.01M16 18h.01M16 21h.01" />
  </I>
);

export const CloudDrizzle = (p: P) => (
  <I {...p}>
    <path d="M5 15a4 4 0 1 1 2-7 5.5 5.5 0 0 1 10.5 0H19a3 3 0 0 1 0 6H5Z" />
    <path d="M8 19v1M8 14v1M12 21v1M12 16v1M16 19v1M16 14v1" />
  </I>
);

export const CloudFog = (p: P) => (
  <I {...p}>
    <path d="M5 15a4 4 0 1 1 2-7 5.5 5.5 0 0 1 10.5 0H19a3 3 0 0 1 0 6H5Z" />
    <path d="M4 19h16M7 22h10" />
  </I>
);

export const Sun = (p: P) => (
  <I {...p}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2m0 16v2M2 12h2m16 0h2" />
  </I>
);

export const Moon = (p: P) => (
  <I {...p}>
    <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
  </I>
);

export const Menu = (p: P) => (
  <I {...p}>
    <path d="M4 7h16M4 12h16M4 17h16" />
  </I>
);

export const X = (p: P) => (
  <I {...p}>
    <path d="m6 6 12 12M18 6 6 18" />
  </I>
);

export const UserRound = (p: P) => (
  <I {...p}>
    <circle cx="12" cy="8" r="3" />
    <path d="M5 21a7 7 0 0 1 14 0" />
  </I>
);

export const LogIn = (p: P) => (
  <I {...p}>
    <path d="m10 17 5-5-5-5M15 12H3M21 4v16" />
  </I>
);

export const LogOut = (p: P) => (
  <I {...p}>
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <polyline points="16 17 21 12 16 7" />
    <line x1="21" y1="12" x2="9" y2="12" />
  </I>
);

export const Settings = (p: P) => (
  <I {...p}>
    <circle cx="12" cy="12" r="3" />
    <path d="M12 2v3m0 14v3M2 12h3m14 0h3" />
  </I>
);

export const ArrowLeft = (p: P) => (
  <I {...p}>
    <path d="m15 18-6-6 6-6M9 12h11" />
  </I>
);

export const ArrowUp = (p: P) => (
  <I {...p}>
    <path d="m12 19V5m-6 6 6-6 6 6" />
  </I>
);

export const MapPin = (p: P) => (
  <I {...p}>
    <path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Z" />
    <circle cx="12" cy="10" r="2" />
  </I>
);

export const Mic = (p: P) => (
  <I {...p}>
    <rect x="9" y="3" width="6" height="11" rx="3" />
    <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
  </I>
);

export const Send = (p: P) => (
  <I {...p}>
    <path d="m21 3-7 18-3-8-8-3 18-7Z" />
  </I>
);

export const Droplets = (p: P) => (
  <I {...p}>
    <path d="M12 2S5 10 5 15a7 7 0 0 0 14 0c0-5-7-13-7-13Z" />
  </I>
);

export const Wind = (p: P) => (
  <I {...p}>
    <path d="M3 8h12a3 3 0 1 0-3-3M3 12h17M3 16h10a3 3 0 1 1-3 3" />
  </I>
);

export const Thermometer = (p: P) => (
  <I {...p}>
    <path d="M14 15V5a2 2 0 0 0-4 0v10a4 4 0 1 0 4 0Z" />
    <path d="M12 8v7" />
  </I>
);

export const Volume2 = (p: P) => (
  <I {...p}>
    <path d="M4 10v4h4l5 4V6l-5 4H4Zm12.5-2.5a5 5 0 0 1 0 9m2.5-12a9 9 0 0 1 0 15" />
  </I>
);

export const MessageSquare = (p: P) => (
  <I {...p}>
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </I>
);

export const MapIcon = (p: P) => (
  <I {...p}>
    <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" />
    <line x1="8" y1="2" x2="8" y2="18" />
    <line x1="16" y1="6" x2="16" y2="22" />
  </I>
);

export const HistoryIcon = (p: P) => (
  <I {...p}>
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 16 14" />
  </I>
);

export const Sparkles = (p: P) => (
  <I {...p}>
    <path d="m12 3 1.912 5.813a2 2 0 0 0 1.275 1.275L21 12l-5.813 1.912a2 2 0 0 0-1.275 1.275L12 21l-1.912-5.813a2 2 0 0 0-1.275-1.275L3 12l5.813-1.912a2 2 0 0 0 1.275-1.275L12 3Z" />
  </I>
);

export const Plus = (p: P) => (
  <I {...p}>
    <line x1="12" y1="5" x2="12" y2="19" />
    <line x1="5" y1="12" x2="19" y2="12" />
  </I>
);

export const Info = (p: P) => (
  <I {...p}>
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="16" x2="12" y2="12" />
    <line x1="12" y1="8" x2="12.01" y2="8" />
  </I>
);

export const ShieldAlert = (p: P) => (
  <I {...p}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </I>
);

export const Lightbulb = (p: P) => (
  <I {...p}>
    <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-1 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5" />
    <path d="M9 18h6" />
    <path d="M10 22h4" />
  </I>
);

export const AlertTriangle = (p: P) => (
  <I {...p}>
    <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </I>
);

export const BarChart2 = (p: P) => (
  <I {...p}>
    <line x1="18" y1="20" x2="18" y2="10" />
    <line x1="12" y1="20" x2="12" y2="4" />
    <line x1="6" y1="20" x2="6" y2="14" />
  </I>
);

export const Calendar = (p: P) => (
  <I {...p}>
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
    <line x1="16" y1="2" x2="16" y2="6" />
    <line x1="8" y1="2" x2="8" y2="6" />
    <line x1="3" y1="10" x2="21" y2="10" />
  </I>
);

export const CheckCircle2 = (p: P) => (
  <I {...p}>
    <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
    <path d="m9 12 2 2 4-4" />
  </I>
);

export const Compass = (p: P) => (
  <I {...p}>
    <circle cx="12" cy="12" r="10" />
    <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
  </I>
);


