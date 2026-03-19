import type React from 'react';

type Variant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
type Size = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: Variant;
    size?: Size;
}

const VARIANT_CLASSES: Record<Variant, string> = {
    primary: 'bg-accent text-white hover:bg-accent-hover',
    secondary: 'bg-surface-secondary text-primary hover:bg-border',
    outline: 'border border-accent text-accent bg-accent/15! hover:bg-accent/25!',
    ghost: 'text-primary hover:bg-surface-secondary',
    destructive: 'bg-destructive text-white hover:bg-[#c03030]',
};

const SIZE_CLASSES: Record<Size, string> = {
    sm: 'py-2 px-4 text-[12px]',
    md: 'py-3 px-6 text-[14px]',
    lg: 'py-4 px-8 text-[16px]',
};

export function Button({
    variant = 'primary',
    size = 'md',
    className,
    children,
    ...rest
}: ButtonProps) {
    return (
        <button
            className={[
                'inline-flex items-center justify-center gap-2 rounded-xl',
                'font-inter cursor-pointer font-medium transition-colors',
                'disabled:cursor-not-allowed disabled:opacity-40',
                VARIANT_CLASSES[variant],
                SIZE_CLASSES[size],
                className ?? '',
            ]
                .filter(Boolean)
                .join(' ')}
            {...rest}
        >
            {children}
        </button>
    );
}
