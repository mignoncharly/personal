"use client";

import { useActionState } from "react";
import Link from "next/link";

import { login, type FormState } from "@/actions/auth";
import { SubmitButton } from "@/components/submit-button";
import { Alert, Field, Input } from "@/components/ui";

export function LoginForm({ next }: { next: string }) {
  const [state, formAction] = useActionState<FormState, FormData>(login, {});

  return (
    <form action={formAction} className="space-y-4">
      <input type="hidden" name="next" value={next} />
      {state.error && <Alert kind="error">{state.error}</Alert>}

      <Field label="E-Mail-Adresse" htmlFor="email">
        <Input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          autoFocus
        />
      </Field>

      <Field label="Passwort" htmlFor="password">
        <Input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
        />
      </Field>

      <SubmitButton pendingLabel="Anmeldung läuft …" className="w-full">
        Anmelden
      </SubmitButton>

      <p className="text-center text-sm text-slate-500 dark:text-slate-400">
        <Link
          href="/passwort-reset"
          className="font-medium text-indigo-600 hover:underline dark:text-indigo-400"
        >
          Passwort vergessen?
        </Link>
      </p>
    </form>
  );
}
