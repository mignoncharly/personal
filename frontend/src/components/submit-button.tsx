"use client";

import { useFormStatus } from "react-dom";

import { Button, cn } from "@/components/ui";

interface SubmitButtonProps {
  children: React.ReactNode;
  pendingLabel?: string;
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md";
  className?: string;
}

/** Submit-Button mit automatischem Lade-/Disabled-Zustand (useFormStatus). */
export function SubmitButton({
  children,
  pendingLabel,
  variant = "primary",
  size = "md",
  className,
}: SubmitButtonProps) {
  const { pending } = useFormStatus();
  return (
    <Button
      type="submit"
      variant={variant}
      size={size}
      disabled={pending}
      className={cn(className)}
    >
      {pending ? (pendingLabel ?? "Bitte warten …") : children}
    </Button>
  );
}
