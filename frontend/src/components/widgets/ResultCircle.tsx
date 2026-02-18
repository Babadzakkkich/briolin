import { Percent } from 'lucide-react';

export interface ResultCircleProps {
  percentage: number;
  color?: string;
}

export function ResultCircle({
  percentage,
  color = '#4B6B56',
}: ResultCircleProps) {
  const radius = 160;
  const stroke = 15;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="relative flex items-center justify-center">
      <svg height={radius * 2} width={radius * 2} className="rotate-[-90deg]">
        <circle
          stroke="#e5e2db"
          strokeWidth={stroke}
          fill="transparent"
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
        <circle
          stroke={color}
          strokeWidth={stroke}
          strokeDasharray={circumference + ' ' + circumference}
          style={{
            strokeDashoffset,
            transition: 'stroke-dashoffset 0.5s ease-in-out',
          }}
          strokeLinecap="round"
          fill="transparent"
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
      </svg>
      <div className="absolute flex items-center justify-center text-7xl font-light text-[#BEB8AC]">
        {percentage}
        <Percent />
      </div>
    </div>
  );
}
