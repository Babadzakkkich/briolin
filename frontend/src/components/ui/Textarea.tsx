import { forwardRef, type TextareaHTMLAttributes } from "react";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
    variant?: "outline" | "solid";
}

const VARIANTS = {
    outline: "border border-ash-blue bg-transparent placeholder:text-brown/50",
    solid: "bg-ash-blue/10 border-transparent placeholder:text-brown/50",
};

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
    ({ className = "", variant = "outline", ...props }, ref) => {
        return (
            <textarea
                ref={ref}
                className={`
          ${VARIANTS[variant]}
          w-full rounded-2xl px-4 py-3 text-base text-brown
          font-involve transition-all duration-200
          focus:outline-none focus:ring-2 focus:ring-ash-blue/50
          disabled:cursor-not-allowed disabled:opacity-50
          resize-none
          ${className}
        `}
                {...props}
            />
        );
    },
);

Textarea.displayName = "Textarea";
