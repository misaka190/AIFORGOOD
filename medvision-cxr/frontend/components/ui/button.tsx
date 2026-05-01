import { ButtonHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = "primary", ...props },
  ref
) {
  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-full px-5 py-3 text-sm font-semibold transition focus:outline-none focus:ring-0 disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "bg-primary text-primaryInk hover:opacity-95",
        variant === "secondary" && "border border-border bg-surface text-text hover:bg-surfaceMuted",
        variant === "ghost" && "bg-transparent text-text hover:bg-surfaceMuted",
        variant === "danger" && "bg-danger text-white hover:opacity-90",
        className
      )}
      {...props}
    />
  );
});
