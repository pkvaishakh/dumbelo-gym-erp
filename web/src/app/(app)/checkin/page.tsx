"use client";
import { PageBar } from "@/components/shell";
import { SelfCheckIn } from "@/features/self-checkin";

export default function CheckInPage() {
  return (
    <div className="rl-app rl-root">
      <PageBar title="Check In" sub="Scan the code at the entrance" />
      <main className="rl-app__main"><section className="rl-section"><SelfCheckIn /></section></main>
    </div>
  );
}
