/* The landing page's demo form, without its UI: what makes it complete, in the same words the API uses. */
import type { LeadBranchesEnum } from "@/api/gen/model";

export type LeadForm = { name: string; phone: string; gym_name: string; city: string; branches: LeadBranchesEnum | ""; email: string };
export type LeadField = keyof LeadForm;

export const EMPTY_LEAD: LeadForm = { name: "", phone: "", gym_name: "", city: "", branches: "", email: "" };
/** The form's fields in the order they appear, so the first wrong one can take focus. */
export const LEAD_FIELDS: LeadField[] = ["name", "phone", "gym_name", "city", "branches", "email"];

/** Ten digits, after dropping spaces, dashes and a leading +91 or 91. */
export function mobileDigits(text: string) {
  const d = text.replace(/\D/g, "");
  return d.length === 12 && d.startsWith("91") ? d.slice(2) : d;
}

/** What to fix, field by field. Empty when the form can be sent. */
export function checkLead(f: LeadForm): Partial<Record<LeadField, string>> {
  const e: Partial<Record<LeadField, string>> = {};
  if (!f.name.trim()) e.name = "Enter your name";
  if (!f.phone.trim()) e.phone = "Enter your mobile number";
  else if (mobileDigits(f.phone).length !== 10) e.phone = "Enter a 10-digit mobile number";
  if (!f.gym_name.trim()) e.gym_name = "Enter your gym’s name";
  if (!f.city.trim()) e.city = "Enter your city";
  if (!f.branches) e.branches = "Choose how many branches";
  if (f.email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email.trim())) e.email = "Enter an email like you@gym.com, or leave it empty";
  return e;
}

/** The utm_ tags of the address a visitor arrived at, so Dumbelo knows which campaign brought them. */
export function campaignTags(search: string) {
  const p = new URLSearchParams(search);
  const tag = (k: string) => (p.get(k) ?? "").trim().slice(0, 100);
  return { utm_source: tag("utm_source"), utm_medium: tag("utm_medium"), utm_campaign: tag("utm_campaign") };
}
