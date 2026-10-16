"use client";
import { Plus, ScanLine } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { useDevicesList } from "@/api/gen/devices/devices";
import type { Device, DeviceWithToken } from "@/api/gen/model";
import { PageBar } from "@/components/shell";
import { Empty, Icon, Section, SkeletonRows, Status } from "@/components/ui";
import { DeactivateSheet, DeviceSheet, RenameSheet, RotateSheet, TokenSheet } from "@/features/devices";
import { plural, seen } from "@/lib/format";

type Step = "device" | "rename" | "rotate" | "off" | null;

/** The gym's turnstiles and biometric readers, a section per branch. Admins only. */
export default function DevicesPage() {
  const q = useDevicesList({ limit: 100 }); // a gym has a handful of doors, so one page holds them all
  const [device, setDevice] = useState<Device | null>(null);
  const [step, setStep] = useState<Step>(null);
  const [fresh, setFresh] = useState<DeviceWithToken | null>(null);
  const close = () => setStep(null);

  // A section per branch, grouped from the rows themselves: the list arrives in branch order, and a device at a
  // branch you have closed still has to be visible so you can switch it off.
  const { rows, branches } = useMemo(() => {
    const rows = q.data?.data.results ?? [];
    const branches: { id: number; name: string; devices: Device[] }[] = [];
    for (const d of rows) {
      const group = branches.find((g) => g.id === d.branch);
      if (group) group.devices.push(d);
      else branches.push({ id: d.branch, name: d.branch_name, devices: [d] });
    }
    return { rows, branches };
  }, [q.data]);

  return (
    <div className="rl-app rl-root">
      <PageBar title="Devices" sub={rows.length ? plural(rows.length, "device") : undefined} back="/more" />
      <main className="rl-app__main">
        {rows.length > 0 && (
          <Section label="Add">
            <Link className="rl-button rl-button--block rl-addbtn" href="/devices/new"><Icon as={Plus} />Add Device</Link>
          </Section>
        )}
        {q.isLoading ? (
          <Section title="Devices"><SkeletonRows n={3} /></Section>
        ) : rows.length === 0 ? (
          <Section label="No devices">
            <Empty icon={ScanLine} title="No devices yet" text="Add a turnstile or biometric reader, and the punches it records become check-ins.">
              <Link className="rl-button" href="/devices/new">Add Device</Link>
            </Empty>
          </Section>
        ) : (
          branches.map((b) => (
            <Section key={b.id} title={b.name}>
              <ul className="rl-card rl-mlist rl-mlist--compact">
                {b.devices.map((d) => (
                  <li key={d.id}>
                    <button className="rl-mrow" type="button" aria-haspopup="dialog" onClick={() => { setDevice(d); setStep("device"); }}>
                      <span className="rl-chipicon rl-mrow__lead" aria-hidden="true"><Icon as={ScanLine} size="sm" /></span>
                      <span className="rl-row__title rl-mrow__name">{d.name}</span>
                      <span className="rl-row__meta rl-mrow__meta">{d.serial}</span>
                      {!d.is_active && <Status status="off" />}
                      <span className="rl-mrow__note">{seen(d.last_seen)}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </Section>
          ))
        )}
      </main>
      <DeviceSheet open={step === "device"} device={device} onClose={close} onPick={setStep} />
      <RenameSheet open={step === "rename"} device={device} onClose={close} />
      <RotateSheet open={step === "rotate"} device={device} onClose={close} onToken={(d) => { setStep(null); setFresh(d); }} />
      <DeactivateSheet open={step === "off"} device={device} onClose={close} />
      <TokenSheet open={!!fresh} name={fresh?.name ?? ""} token={fresh?.token ?? ""} onClose={() => setFresh(null)} />
    </div>
  );
}
