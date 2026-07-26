import type React from 'react';
import { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
}

export function Input({ label, error, id, disabled, className, type, ...rest }: InputProps) {
    const [showPassword, setShowPassword] = useState(false);
    const isPassword = type === 'password';

    return (
        <div className='flex flex-col gap-1.5'>
            {label && (
                <label htmlFor={id} className='font-inter text-primary text-[12px] font-medium'>
                    {label}
                </label>
            )}
            <div className='relative'>
                <input
                    id={id}
                    type={isPassword ? (showPassword ? 'text' : 'password') : type}
                    disabled={disabled}
                    className={[
                        'w-full rounded-xl px-2 py-2',
                        isPassword ? 'pr-9' : '',
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
                {isPassword && (
                    <button
                        type='button'
                        tabIndex={-1}
                        onClick={() => setShowPassword((v) => !v)}
                        className='text-muted hover:text-secondary absolute inset-y-0 right-0 flex items-center px-2.5 transition-colors'
                    >
                        {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                )}
            </div>
            {error && (
                <span className='font-inter text-destructive text-[11px] font-normal'>{error}</span>
            )}
        </div>
    );
}
