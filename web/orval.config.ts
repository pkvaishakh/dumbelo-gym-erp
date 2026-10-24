import { defineConfig } from "orval";

// Regenerate the typed API client after the backend changes:
//   cd ../api && python manage.py spectacular --file ../web/openapi.yml && cd ../web && npm run api
export default defineConfig({
  dumbelo: {
    input: "./openapi.yml",
    output: {
      mode: "tags-split",
      target: "src/api/gen/endpoints.ts",
      schemas: "src/api/gen/model",
      client: "react-query",
      httpClient: "fetch",
      clean: true,
      override: {
        mutator: { path: "src/lib/api.ts", name: "apiFetch" },
        query: { useQuery: true, signal: true },
        // Long lists also get an infinite hook (useXxxListInfinite) for "Show more": pages by offset.
        operations: Object.fromEntries(
          ["members_list", "payments_list", "subscriptions_list", "expenses_list", "checkins_list", "tasks_list", "staff_list", "payslips_list", "expense_dues_list", "money_moves_list", "platform_gyms_list", "platform_branch_requests_list", "platform_prices_list", "platform_invoices_list", "platform_whatsapp_accounts_list", "platform_whatsapp_templates_list", "platform_messages_list", "platform_leads_list", "messages_list", "platform_whatsapp_usage_retrieve", "billing_invoices_list", "pt_sessions_list", "workout_plans_list", "diet_plans_list"].map((id) => [
            id,
            { query: { useQuery: true, useInfinite: true, useInfiniteQueryParam: "offset", signal: true } },
          ]),
        ),
      },
    },
  },
});
