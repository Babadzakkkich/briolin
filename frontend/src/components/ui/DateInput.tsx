import { forwardRef, type InputHTMLAttributes, useState } from "react";

export interface DateInputProps extends InputHTMLAttributes<HTMLInputElement> {
    variant?: "outline" | "solid";
}

const VARIANTS = {
    outline: "border-b border-brown bg-transparent placeholder:text-brown/50",
    solid: "bg-ash-blue/10 border-transparent placeholder:text-brown/50",
};

export const DateInput = forwardRef<HTMLInputElement, DateInputProps>(
    ({ className = "", variant = "outline", placeholder = "Дата рождения", ...props }, ref) => {
        const [isFocused, setIsFocused] = useState(false);
        const hasValue = Boolean(props.value);
        const isDateType = isFocused || hasValue;

        return (
            <div className="relative w-full">
                <input
                    ref={ref}
                    type={isDateType ? "date" : "text"}
                    placeholder={placeholder}
                    className={`
                        ${VARIANTS[variant]}
                        w-full py-3 text-base font-involve transition-all duration-200 text-brown
                        focus:outline-none disabled:cursor-not-allowed disabled:opacity-50
                        [&::-webkit-calendar-picker-indicator]:absolute
                        [&::-webkit-calendar-picker-indicator]:right-0
                        [&::-webkit-calendar-picker-indicator]:h-full
                        [&::-webkit-calendar-picker-indicator]:w-full
                        [&::-webkit-calendar-picker-indicator]:cursor-pointer
                        [&::-webkit-calendar-picker-indicator]:opacity-0
                        ${className}
                    `}
                    onFocus={(e) => {
                        setIsFocused(true);
                        props.onFocus?.(e);
                    }}
                    onBlur={(e) => {
                        setIsFocused(false);
                        props.onBlur?.(e);
                    }}
                    {...props}
                />
            </div>
        );
    }
);

DateInput.displayName = "DateInput";
