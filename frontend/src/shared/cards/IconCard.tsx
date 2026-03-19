import { Mail } from 'lucide-react';
import type { ComponentPropsWithoutRef } from 'react';

type Size = '24' | '36' | '48';
type Icon = 'mail';

interface Props extends ComponentPropsWithoutRef<'div'> {
    size?: Size;
    icon: Icon;
}

const SIZE_CLASS: Record<Size, string> = {
    '24': 'size-6',
    '36': 'size-9',
    '48': 'size-12',
};

const ICON_SIZE: Record<Size, number> = {
    '24': 16,
    '36': 20,
    '48': 24,
};

export function IconCard({ size = '48', icon, className, ...rest }: Props) {
    const containerSize = SIZE_CLASS[size];
    const iconSize = ICON_SIZE[size];

    const iconElement =
        icon === 'mail' ? <Mail size={iconSize} strokeWidth={1.5} className='text-accent' /> : null;

    return (
        <div
            className={[
                'border-border bg-accent/15 inline-flex items-center justify-center rounded-lg',
                containerSize,
                className,
            ]
                .filter(Boolean)
                .join(' ')}
            {...rest}
        >
            {iconElement}
        </div>
    );
}
