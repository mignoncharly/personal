/**
 * TypeScript-Typen, die die DRF-Serializer des Backends spiegeln.
 * Quelle: die DRF-Serializer unter backend/apps/<app>/serializers.py
 */

export type Role = "admin" | "employee";

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Report {
  from: string;
  to: string;
  totals: { net: string; gross: string; count: number };
  by_month: { month: string; net: string; gross: string; count: number }[];
  by_customer: {
    customer: string;
    net: string;
    gross: string;
    count: number;
  }[];
  by_employee: { employee: string; hours: string; shifts: number }[];
  receivables: {
    open_count: number;
    open_total: string;
    overdue_count: number;
    overdue_total: string;
  };
}

export interface AuditEntry {
  id: number;
  created_at: string;
  actor_name: string;
  action: string;
  action_display: string;
  entity_type: string;
  entity_id: string;
  summary: string;
}

export interface SessionUser {
  id: number;
  email: string;
  role: Role;
  full_name: string;
  is_admin: boolean;
}

/** Antwort von POST /auth/token/ (MouvinTokenObtainPairSerializer). */
export interface TokenResponse {
  access: string;
  refresh: string;
  user: SessionUser;
}

/** GET/PATCH /auth/me/ (MeSerializer). */
export interface Organization {
  id: number;
  name: string;
  slug: string;
}

export interface Me {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: Role;
  is_admin: boolean;
  phone: string;
  organization: Organization | null;
}

/** GET/PATCH /organization/ (OrganizationSerializer) – eigene Org des Admins. */
export interface OrganizationSettings {
  id: number;
  name: string;
  slug: string;
  is_active: boolean;
  legal_name: string;
  street: string;
  zip_code: string;
  city: string;
  phone: string;
  email: string;
  vat_id: string;
  tax_number: string;
  is_small_business: boolean;
  bank_name: string;
  iban: string;
  bic: string;
  logo: string | null;
  invoice_number_prefix: string;
}

// --- Kunden -------------------------------------------------------------

export type Bundesland = "HE" | "RP";
export type InvoiceRhythm = "weekly" | "monthly" | "flexible";

export interface SurchargeRule {
  id: number;
  contract: number;
  label: string;
  percent: string;
  is_active: boolean;
}

export interface TravelCostRule {
  id: number;
  contract: number;
  enabled: boolean;
  rate_per_km: string;
  round_trip: boolean;
  min_amount: string | null;
  max_amount: string | null;
  show_on_invoice: boolean;
}

export interface CustomerContract {
  id: number;
  customer: number;
  valid_from: string;
  is_active: boolean;
  base_hourly_rate: string;
  night_surcharge_pct: string;
  saturday_surcharge_pct: string;
  sunday_surcharge_pct: string;
  holiday_surcharge_pct: string;
  cumulative_surcharges: boolean;
  night_start: string;
  night_end: string;
  invoice_rhythm: InvoiceRhythm;
  payment_term_days: number;
  vat_rate: string;
  surcharge_rules: SurchargeRule[];
  travel_cost_rule: TravelCostRule | null;
}

export interface Customer {
  id: number;
  name: string;
  customer_number: string;
  contact_person: string;
  street: string;
  zip_code: string;
  city: string;
  bundesland: Bundesland;
  phone: string;
  fax: string;
  email: string;
  is_active: boolean;
  active_contract: CustomerContract | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerChoice {
  id: number;
  name: string;
  city: string;
  bundesland: Bundesland;
}

// --- Mitarbeiter --------------------------------------------------------

export type Qualification = "pflegehilfskraft" | "pflegefachkraft";

export interface Employee {
  id: number;
  user_id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  full_name: string;
  qualification: Qualification;
  street: string;
  zip_code: string;
  city: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// --- Schichten ----------------------------------------------------------

export type ShiftType = "frueh" | "spaet" | "nacht";
export type ShiftStatus =
  | "draft"
  | "submitted"
  | "approved"
  | "rejected"
  | "invoiced";

export interface ShiftCalculation {
  total_hours: string;
  break_hours: string;
  paid_hours: string;
  night_hours: string;
  saturday_hours: string;
  sunday_hours: string;
  holiday_hours: string;
  is_holiday: boolean;
  holiday_name: string;
  base_amount: string;
  night_amount: string;
  saturday_amount: string;
  sunday_amount: string;
  holiday_amount: string;
  special_amount: string;
  travel_amount: string;
  net_total: string;
  calculated_at: string | null;
}

export interface Shift {
  id: number;
  employee: number;
  employee_name: string;
  customer: number;
  customer_name: string;
  shift_type: ShiftType;
  shift_type_display: string;
  date: string;
  start_time: string;
  end_time: string;
  break_minutes: number;
  note: string;
  status: ShiftStatus;
  status_display: string;
  created_by: number | null;
  submitted_at: string | null;
  reviewed_by: number | null;
  reviewed_at: string | null;
  correction_reason: string;
  calculation: ShiftCalculation | null;
  created_at: string;
  updated_at: string;
}

export interface ShiftSummary {
  anzahl_schichten: number;
  gesamtpersonal: number;
  gesamtkunden: number;
  gesamtstunden: string;
  zahlbare_stunden: string;
  pausenzeit_minuten: number;
  netto_summe: string;
  status_counts: Partial<Record<ShiftStatus, number>>;
}

export interface InvoiceSummary {
  open_count: number;
  open_total: string;
  overdue_count: number;
  overdue_total: string;
}

// --- Rechnungen ---------------------------------------------------------

export type InvoiceStatus =
  | "draft"
  | "finalized"
  | "sent"
  | "paid"
  | "cancelled";
export type InvoiceLineType =
  | "base_hours"
  | "night"
  | "saturday"
  | "sunday"
  | "holiday"
  | "special"
  | "travel";

export interface InvoiceLine {
  id: number;
  position: number;
  line_type: InvoiceLineType;
  line_type_display: string;
  description: string;
  quantity_hours: string | null;
  factor: string | null;
  amount: string;
}

export interface Invoice {
  id: number;
  number: string;
  sequence: number;
  customer: number;
  customer_name: string;
  invoice_date: string;
  period_start: string;
  period_end: string;
  due_date: string;
  status: InvoiceStatus;
  status_display: string;
  sent_at: string | null;
  paid_at: string | null;
  last_reminded_at: string | null;
  is_overdue: boolean;
  subtotal_net: string;
  vat_rate: string;
  vat_amount: string;
  total_gross: string;
  payment_term_days: number;
  pdf_file: string | null;
  shift_count: number;
  lines: InvoiceLine[];
  created_at: string;
}
