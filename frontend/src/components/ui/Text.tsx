import type { HTMLAttributes, ReactNode } from 'react';

interface Props extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'base' | 'heading';
  size?: 'md' | 'lg' | 'xl';
  children: ReactNode;
}

const TEXT_VARIANTS = {
  base: 'font-involve text-brown font-extralight',
  heading: 'font-comediant text-brown select-none',
};

const SIZE_VARIANTS = {
  md: 'text-lg',
  lg: 'text-4xl md:text-5xl',
  xl: 'text-7xl md:text-8xl',
};

export function Text({
  variant = 'base',
  size = 'md',
  children,
  className = '',
  ...props
}: Props) {
  return (
    <span
      className={`${TEXT_VARIANTS[variant]} ${SIZE_VARIANTS[size]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}
