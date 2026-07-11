import * as React from "react";
import { cn } from "@/lib/utils";

const Button = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: "default" | "outline" | "secondary" | "ghost" | "destructive" | "link";
    size?: "default" | "sm" | "lg" | "icon" | "icon-xs";
    asChild?: boolean;
  }
>(({ className, variant = "default", size = "default", asChild = false, ...props }, ref) => {
  const Comp = asChild ? React.Slot : "button";
  return (
    <Comp
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:opacity-50",
        {
          "bg-primary text-primary-foreground hover:bg-primary/90": variant === "default",
          "border border-input bg-background hover:bg-accent hover:text-accent-foreground": variant === "outline",
          "bg-secondary text-secondary-foreground hover:bg-secondary/80": variant === "secondary",
          "hover:bg-accent hover:text-accent-foreground": variant === "ghost",
          "bg-destructive text-white hover:bg-destructive/90": variant === "destructive",
          "text-primary underline-offset-4 hover:underline": variant === "link",
        },
        {
          "h-8 px-3": size === "default",
          "h-7 px-2.5 text-xs": size === "sm",
          "h-9 px-3": size === "lg",
          "size-8": size === "icon",
          "size-6": size === "icon-xs",
        },
        className
      )}
      {...props}
    />
  );
});
Button.displayName = "Button";

export { Button };
