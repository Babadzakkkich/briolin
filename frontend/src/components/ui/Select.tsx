import { forwardRef, type SelectHTMLAttributes } from "react";
import { ChevronDown } from "lucide-react";

export interface Option {
    label: string;
    value: string;
}

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
    variant?: "outline" | "solid";
    options: Option[];
    placeholder?: string;
}

const VARIANTS = {
    outline: "border-b border-brown bg-transparent placeholder:text-brown/50",
    solid: "bg-ash-blue/10 border-transparent placeholder:text-brown/50",
};

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
    ({ className = "", variant = "outline", options, ...props }, ref) => {
        return (
            <div className="relative w-full">
                <select
                    ref={ref}
                    className={`
                        ${VARIANTS[variant]}
                        w-full py-3 text-base text-brown
                        font-involve transition-all duration-200
                        appearance-none focus:outline-none disabled:cursor-not-allowed disabled:opacity-50
                        ${!props.value ? "text-brown/50" : ""}
                        ${className}
                    `}
                    {...props}
                >
                    {props.placeholder && (
                        <option value="" disabled hidden>
                            {props.placeholder}
                        </option>
                    )}
                    {options.map((option) => (
                        <option key={option.value} value={option.value}>
                            {option.label}
                        </option>
                    ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2 text-brown">
                    <ChevronDown size={20} className="stroke-[1.5]" />
                </div>
            </div>
        );
    }
);

Select.displayName = "Select";
