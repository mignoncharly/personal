"use client";

import { useActionState } from "react";

import { rejectShift, type ActionState } from "@/actions/shifts";
import { SubmitButton } from "@/components/submit-button";
import { Alert, Field, Textarea } from "@/components/ui";

export function RejectShiftForm({ shiftId }: { shiftId: number }) {
  const [state, formAction] = useActionState<ActionState, FormData>(
    rejectShift,
    {},
  );
  return (
    <form action={formAction} className="space-y-3">
      <input type="hidden" name="id" value={shiftId} />
      {state.error && <Alert kind="error">{state.error}</Alert>}
      <Field label="Ablehnungsgrund" htmlFor="reason">
        <Textarea
          id="reason"
          name="reason"
          rows={2}
          required
          placeholder="z. B. Endzeit unplausibel – bitte korrigieren."
        />
      </Field>
      <SubmitButton variant="danger" pendingLabel="Wird abgelehnt …">
        Ablehnen
      </SubmitButton>
    </form>
  );
}
