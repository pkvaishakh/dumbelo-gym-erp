"use client";
import { QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { makeQueryClient } from "@/lib/query";

export function Providers({ children }: { children: React.ReactNode }) {
  const [qc] = useState(makeQueryClient);
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}
