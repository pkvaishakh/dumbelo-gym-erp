"use client";
import { AdminHome, MemberHome, ReceptionHome, TrainerHome } from "@/features/homes";
import { useSession } from "@/lib/session";

export default function HomePage() {
  const { role } = useSession();
  if (role.role === "admin") return <AdminHome />;
  if (role.role === "receptionist") return <ReceptionHome />;
  if (role.role === "trainer") return <TrainerHome />;
  return <MemberHome />;
}
