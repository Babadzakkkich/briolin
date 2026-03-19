import type React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
}

export function Input({ label, error, id, disabled, className, ...rest }: InputProps) {
    return (
        <div className='flex flex-col gap-1.5'>
            {label && (
                <label htmlFor={id} className='font-inter text-primary text-[12px] font-medium'>
                    {label}
                </label>
            )}
            <input
                id={id}
                disabled={disabled}
                className={[
                    'w-full rounded-xl px-2 py-2',
                    'font-inter text-primary placeholder:text-muted text-[14px] font-normal',
                    'transition-colors outline-none',
                    'border',
                    error ? 'border-destructive' : 'border-border',
                    'focus:border-accent',
                    disabled ? 'bg-surface-secondary cursor-not-allowed opacity-50' : 'bg-white',
                    className ?? '',
                ]
                    .filter(Boolean)
                    .join(' ')}
                {...rest}
            />
            {error && (
                <span className='font-inter text-destructive text-[11px] font-normal'>{error}</span>
            )}
        </div>
    );
}
