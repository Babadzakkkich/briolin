import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant: 'outline' | 'solid';
  children: ReactNode;
}

const BUTTON_STYLES = {
  outline:
    'bg-transparent border border-brown/40 text-brown hover:bg-brown hover:text-beige hover:border-brown active:bg-brown/90 disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-brown disabled:hover:border-brown/40',
  solid: 'bg-ash-blue hover:bg-ash-blue/80 text-white',
};

export function Button({ variant, children, className = '', ...props }: Props) {
  return (
    <button
      {...props}
      className={`${BUTTON_STYLES[variant]} font-involve cursor-pointer rounded-full px-6 py-3 text-sm tracking-wide transition-all duration-200 disabled:cursor-not-allowed ${className}`}
    >
      {children}
    </button>
  );
}
