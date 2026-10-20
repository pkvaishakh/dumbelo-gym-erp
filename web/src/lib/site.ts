/* The public website's settings: where it lives, and how gym owners reach Dumbelo's sales. */

/** The address the landing page is served at, for canonical links, the sitemap and share previews. */
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || "https://app.dumbelo.com").replace(/\/$/, "");

/** Sales' email, shown in the footer. */
export const CONTACT_EMAIL = process.env.NEXT_PUBLIC_CONTACT_EMAIL || "hello@dumbelo.com";

/** WhatsApp wants the number with its country code and nothing else: "+91 98765 43210", "919876543210" and a bare
 *  Indian "98765 43210" all become 919876543210. */
export function whatsappNumber(text: string) {
  const digits = text.replace(/\D/g, "");
  return digits.length === 10 ? `91${digits}` : digits;
}

/** Sales' WhatsApp number. Unset hides every WhatsApp button. */
export const SALES_WHATSAPP = whatsappNumber(process.env.NEXT_PUBLIC_SALES_WHATSAPP || "");

/** A chat with sales, opened with `text` already typed so the visitor only has to press send. */
export const whatsappLink = (text: string) => `https://wa.me/${SALES_WHATSAPP}?text=${encodeURIComponent(text)}`;

/** What each WhatsApp button types for the visitor, by where it sits. */
export const CHAT_TEXT = {
  general: "Hi, I'd like to know more about Dumbelo for my gym.",
  prices: "Hi, what would Dumbelo cost for my gym?",
};
