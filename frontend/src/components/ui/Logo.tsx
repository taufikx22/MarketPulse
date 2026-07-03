'use client';

export default function Logo({ className = '', size = 20 }: { className?: string; size?: number }) {
  return (
    <svg
      className={className}
      style={{ height: `${size}px`, width: 'auto', display: 'inline-block', verticalAlign: 'middle' }}
      viewBox="0 0 200 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <clipPath id="flat-cut">
          <polygon points="0,0 200,0 200,120 88,120 0,32" />
        </clipPath>
      </defs>

      {/* M Shape - Inherits current text color */}
      <path d="M 16,110 L 16,18 L 64,74 L 108,30 L 108,48 L 64,92 L 31,54 L 31,110 Z" fill="currentColor" />

      {/* Pulse Shape - Lime Green */}
      <path
        d="M 76,108 L 115,64 L 134,92 L 174,30"
        stroke="#82C31E"
        strokeWidth="15"
        strokeLinecap="round"
        strokeLinejoin="round"
        clipPath="url(#flat-cut)"
      />
    </svg>
  );
}
