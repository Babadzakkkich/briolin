import type React from 'react';

type Variant = 'h1' | 'h2' | 'h3' | 'h4' | 'p' | 'p-sm' | 'caption' | 'overline';

type ElementTag = keyof HTMLElementTagNameMap;

interface TextProps extends React.HTMLAttributes<HTMLElement> {
    variant: Variant;
    as?: ElementTag;
    children: React.ReactNode;
}

const VARIANT_ELEMENT: Record<Variant, ElementTag> = {
    h1: 'h1',
    h2: 'h2',
    h3: 'h3',
    h4: 'h4',
    p: 'p',
    'p-sm': 'p',
    caption: 'p',
    overline: 'p',
};

const VARIANT_CLASSES: Record<Variant, string> = {
    h1: 'font-onest text-[32px] font-medium leading-[1.2]',
    h2: 'font-onest text-[26px] font-medium leading-[1.2]',
    h3: 'font-onest text-[24px] font-medium leading-[1.2]',
    h4: 'font-onest text-[20px] font-medium leading-[1.2]',
    p: 'font-raleway text-[18px] text-primary font-medium leading-[1.6]',
    'p-sm': 'font-inter text-[14px] text-muted font-semibold leading-[1.6]',
    caption: 'font-raleway text-[12px] text-primary font-medium leading-[1.5]',
    overline:
        'font-raleway text-[10px] text-secondary font-semibold uppercase tracking-[0.5px] leading-[1.4]',
};

export function Text({ variant, as, className, children, ...rest }: TextProps) {
    const Component = as ?? VARIANT_ELEMENT[variant];
    const classes = [VARIANT_CLASSES[variant], className].filter(Boolean).join(' ');

    return (
        <Component className={classes} {...rest}>
            {children}
        </Component>
    );
}
