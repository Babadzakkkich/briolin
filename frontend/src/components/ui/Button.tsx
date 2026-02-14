import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant: 'outline' | 'solid';
  children: ReactNode;
}

const BUTTON_STYLES = {
  outline: 'bg-ash-blue',
  solid: 'bg-ash-blue hover:bg-ash-blue/80',
};

export function Button({ variant, children, className = '', ...props }: Props) {
  return (
    <button
      {...props}
      className={`${BUTTON_STYLES[variant]} font-involve cursor-pointer rounded-full py-3 text-white transition-colors disabled:cursor-not-allowed disabled:bg-ash-blue/70 ${className}`}
    >
      {children}
    </button>
  );
}
