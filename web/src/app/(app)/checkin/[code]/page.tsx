"use client";
import { useParams } from "next/navigation";

import { PageBar } from "@/components/shell";
import { SelfCheckIn } from "@/features/self-checkin";

/** Opened by scanning the wall QR with the phone's own camera: /checkin/<branch code>. */
export default function CheckInByLink() {
  const { code } = useParams<{ code: string }>();
  return (
    <div className="rl-app rl-root">
      <PageBar title="Check In" />
      <main className="rl-app__main"><section className="rl-section"><SelfCheckIn code={code} /></section></main>
    </div>
  );
}
