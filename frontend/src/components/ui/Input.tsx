import { forwardRef, type InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    variant?: "outline" | "solid";
}

const VARIANTS = {
    outline: "border-b border-brown bg-transparent placeholder:text-brown/50",
    solid: "bg-ash-blue/10 border-transparent placeholder:text-brown/50",
};

export const Input = forwardRef<HTMLInputElement, InputProps>(
    ({ className = "", variant = "outline", ...props }, ref) => {
        return (
            <input
                ref={ref}
                className={`
          ${VARIANTS[variant]}
          w-full py-3 text-base text-brown
          font-involve transition-all duration-200
          focus:outline-none disabled:cursor-not-allowed disabled:opacity-50
          ${className}
        `}
                {...props}
            />
        );
    },
);

Input.displayName = "Input";
