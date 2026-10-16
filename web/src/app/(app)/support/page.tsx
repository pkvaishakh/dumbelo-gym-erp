"use client";
import { LifeBuoy, ShieldCheck } from "lucide-react";
import { useState } from "react";

import { useSupportAccessList } from "@/api/gen/support-access/support-access";
import { PageBar } from "@/components/shell";
import { Choices, Empty, ErrorText, Icon, Section, Sheet, SkeletonRows } from "@/components/ui";
import { day, until } from "@/lib/format";
import { useAction } from "@/lib/hooks";

const REFRESH = ["/api/support-access/"];
const LENGTHS = [
  { value: 2, title: "2 hours", meta: "Long enough for one call" },
  { value: 24, title: "24 hours", meta: "A problem that takes a day" },
  { value: 72, title: "3 days", meta: "The longest Rackline can ask for" },
];

/** Whether Rackline's team can see this gym right now, and the record of every time they could. */
export default function SupportAccessPage() {
  const q = useSupportAccessList({ limit: 50 });
  const rows = q.data?.data.results ?? [];
  const open = rows.find((r) => r.open);
  const [give, setGive] = useState(false);
  const [end, setEnd] = useState(false);

  return (
    <div className="rl-app rl-root">
      <PageBar title="Support access" back="/more" />
      <main className="rl-app__main">
        <Section label="Now">
          <div className="rl-card rl-card--pad">
            {q.isLoading ? (
              <p className="rl-statusline rl-statusline--muted">Checking…</p>
            ) : open ? (
              <>
                <p className="rl-statusline"><span className="rl-tag rl-tag--now">On</span></p>
                <p className="rl-lede">Rackline&apos;s team can see your gym, but can&apos;t change anything, until {until(open.ends)}.</p>
                <button className="rl-button rl-button--danger-quiet rl-button--block" type="button" style={{ marginTop: "var(--space-4)" }}
                  aria-haspopup="dialog" onClick={() => setEnd(true)}>End Access</button>
              </>
            ) : (
              <>
                <p className="rl-statusline"><Icon as={ShieldCheck} size="sm" />No one at Rackline can see your gym</p>
                <p className="rl-lede">They can look only while you allow it, they can never change anything, and every look is recorded.</p>
                <button className="rl-button rl-button--block" type="button" style={{ marginTop: "var(--space-4)" }}
                  aria-haspopup="dialog" onClick={() => setGive(true)}>Give Access</button>
              </>
            )}
          </div>
        </Section>

        <Section title="Access you've given">
          {q.isLoading ? <SkeletonRows n={3} /> : rows.length === 0 ? (
            <Empty icon={LifeBuoy} title="You haven't given access yet" text="When Rackline asks to look at a problem, you can let them in from here." />
          ) : (
            <ul className="rl-card rl-mlist rl-mlist--compact">
              {rows.map((r) => (
                <li key={r.id}><div className="rl-mrow">
                  <span className="rl-chipicon rl-mrow__lead" aria-hidden="true"><Icon as={LifeBuoy} size="sm" /></span>
                  <span className="rl-row__title rl-mrow__name">{day(r.starts)}</span>
                  <span className="rl-row__meta rl-mrow__meta">{until(r.starts, new Date(r.starts))} to {until(r.ends, new Date(r.starts))}</span>
                  {r.open && <span className="rl-tag rl-tag--now">On</span>}
                  <span className="rl-mrow__note">{r.granted_by_name}</span>
                </div></li>
              ))}
            </ul>
          )}
        </Section>
      </main>

      <GiveSheet open={give} onClose={() => setGive(false)} />
      <EndSheet open={end} id={open?.id} ends={open?.ends} onClose={() => setEnd(false)} />
    </div>
  );
}

function GiveSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [hours, setHours] = useState(2);
  const a = useAction();
  async function give() {
    try {
      await a.run("/api/support-access/", { hours }, { refresh: REFRESH });
      onClose();
    } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={onClose} title="Give Rackline access">
      <p className="rl-row__meta">They can read your members, payments and check-ins to help with a problem. They can&apos;t change anything, and the access ends on its own.</p>
      <Choices name="hours" value={hours} onChange={setHours} options={LENGTHS} />
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={give}>{a.busy ? "Giving access…" : "Give Access"}</button>
        <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={onClose}>Cancel</button>
      </div>
    </Sheet>
  );
}

function EndSheet({ open, id, ends, onClose }: { open: boolean; id?: number; ends?: string; onClose: () => void }) {
  const a = useAction();
  async function stop() {
    try {
      await a.run(`/api/support-access/${id}/end/`, undefined, { refresh: REFRESH });
      onClose();
    } catch { /* shown */ }
  }
  return (
    <Sheet open={open} onClose={onClose} title="End Rackline's access?">
      <p className="rl-row__meta">
        They lose your gym straight away, instead of at {ends ? until(ends) : "the end of the window"}. You can give access again whenever you need to.
      </p>
      <ErrorText>{a.error?.message}</ErrorText>
      <div className="rl-sheet__actions">
        <button className="rl-button rl-button--danger rl-button--block" type="button" disabled={a.busy} onClick={stop}>{a.busy ? "Ending…" : "End Access"}</button>
        <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={onClose}>Keep Access On</button>
      </div>
    </Sheet>
  );
}
