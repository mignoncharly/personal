"use client";

import { useActionState } from "react";
import Link from "next/link";

import {
  confirmPasswordReset,
  requestPasswordReset,
  type FormState,
} from "@/actions/auth";
import { SubmitButton } from "@/components/submit-button";
import { Alert, Field, Input } from "@/components/ui";

function BackToLogin() {
  return (
    <p className="text-center text-sm text-slate-500 dark:text-slate-400">
      <Link
        href="/login"
        className="font-medium text-indigo-600 hover:underline dark:text-indigo-400"
      >
        Zurück zur Anmeldung
      </Link>
    </p>
  );
}

export function RequestResetForm() {
  const [state, formAction] = useActionState<FormState, FormData>(
    requestPasswordReset,
    {},
  );
  return (
    <form action={formAction} className="space-y-4">
      {state.error && <Alert kind="error">{state.error}</Alert>}
      {state.success && <Alert kind="success">{state.success}</Alert>}
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Geben Sie Ihre E-Mail-Adresse ein. Sie erhalten einen Link zum
        Zurücksetzen Ihres Passworts.
      </p>
      <Field label="E-Mail-Adresse" htmlFor="email">
        <Input id="email" name="email" type="email" required autoFocus />
      </Field>
      <SubmitButton pendingLabel="Wird gesendet …" className="w-full">
        Link anfordern
      </SubmitButton>
      <BackToLogin />
    </form>
  );
}

export function ConfirmResetForm({
  uid,
  token,
}: {
  uid: string;
  token: string;
}) {
  const [state, formAction] = useActionState<FormState, FormData>(
    confirmPasswordReset,
    {},
  );
  return (
    <form action={formAction} className="space-y-4">
      <input type="hidden" name="uid" value={uid} />
      <input type="hidden" name="token" value={token} />
      {state.error && <Alert kind="error">{state.error}</Alert>}
      {state.success ? (
        <>
          <Alert kind="success">{state.success}</Alert>
          <BackToLogin />
        </>
      ) : (
        <>
          <Field label="Neues Passwort" htmlFor="new_password">
            <Input
              id="new_password"
              name="new_password"
              type="password"
              autoComplete="new-password"
              required
            />
          </Field>
          <Field label="Passwort wiederholen" htmlFor="confirm_password">
            <Input
              id="confirm_password"
              name="confirm_password"
              type="password"
              autoComplete="new-password"
              required
            />
          </Field>
          <SubmitButton pendingLabel="Wird gespeichert …" className="w-full">
            Passwort setzen
          </SubmitButton>
        </>
      )}
    </form>
  );
}
