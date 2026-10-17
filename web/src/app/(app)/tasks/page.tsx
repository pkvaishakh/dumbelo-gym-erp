"use client";
import { ClipboardList, SearchX } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import type { Task } from "@/api/gen/model";
import { useStaffList } from "@/api/gen/staff/staff";
import { useTasksListInfinite, useTasksRetrieve } from "@/api/gen/tasks/tasks";
import type { TasksListRole, TasksListState } from "@/api/gen/model";
import { PageBar } from "@/components/shell";
import { AddButton, Chips, Confirm, Empty, ErrorText, Field, Icon, LoadMore, Photo, SearchField, Sheet, SkeletonRows, TaskStatus } from "@/components/ui";
import { ago, clock, day, isoDate, plural } from "@/lib/format";
import { paged, pages, useAction, useGet, useSearch } from "@/lib/hooks";
import { useSession } from "@/lib/session";
import type { TaskCounts } from "@/lib/types";

function due(t: Task) {
  const today = isoDate(new Date());
  const tm = t.due_time ? `, ${clock(t.due_time)}` : "";
  return t.due_date === today ? `Due today${tm}` : `Due ${day(t.due_date)}${tm}`;
}

type Filters = { state: string; role: string; staff: string; branch: string };

/** Status, role, staff and branch live in the address, so a link (or coming back) keeps the list as it was. */
function listUrl(f: Filters) {
  const p = new URLSearchParams();
  if (f.state !== "open") p.set("filter", f.state);
  if (f.role !== "all") p.set("role", f.role);
  if (f.staff !== "all") p.set("staff", f.staff);
  if (f.branch !== "all") p.set("branch", f.branch);
  const s = p.toString();
  return s ? `/tasks?${s}` : "/tasks";
}

function TasksPage() {
  const params = useSearchParams();
  const router = useRouter();
  const { role } = useSession();
  const admin = role.role === "admin";
  const [f, setF] = useState<Filters>({
    state: params.get("filter") ?? "open", role: params.get("role") ?? "all", staff: params.get("staff") ?? "all", branch: params.get("branch") ?? "all",
  });
  const [sheet, setSheet] = useState(false);
  const [text, setText] = useState("");
  const dq = useSearch(text);
  const [openId, setOpenId] = useState<number | null>(Number(params.get("open")) || null);
  const [creating, setCreating] = useState(params.get("new") === "1");

  // Only admins see other people's tasks, so only they get the staff and branch filters.
  const staff = useStaffList({ is_active: true, limit: 100 }, { query: { enabled: admin } });
  const allStaff = (staff.data?.data.results ?? []).filter((s) => s.role !== "admin");
  const fits = (s: (typeof allStaff)[number], v: Filters) => (v.role === "all" || s.role === v.role) && (v.branch === "all" || s.branches.includes(Number(v.branch)));
  const people = allStaff.filter((s) => fits(s, f));
  const personName = people.find((s) => String(s.id) === f.staff)?.name;

  const narrow = {
    ...(f.role !== "all" ? { role: f.role as TasksListRole } : {}), ...(f.staff !== "all" ? { assignee: Number(f.staff) } : {}),
    ...(f.branch !== "all" ? { branch: Number(f.branch) } : {}), ...(dq ? { q: dq } : {}),
  };
  const q = useTasksListInfinite({ ...(f.state !== "all" ? { state: f.state as TasksListState } : {}), ...narrow }, { query: paged });
  const { rows: shown, count: total } = pages(q);
  const everyone = useGet<TaskCounts>("/api/tasks/counts/");
  const counts = useGet<TaskCounts>("/api/tasks/counts/", narrow).data;
  const current = useTasksRetrieve(openId ?? 0, { query: { enabled: !!openId } }).data?.data ?? null;

  const set = (next: Partial<Filters>) => {
    const v = { ...f, ...next };
    // A person picked under another role or branch would leave the list empty for no visible reason.
    const picked = allStaff.find((s) => String(s.id) === v.staff);
    if (v.staff !== "all" && (!picked || !fits(picked, v))) v.staff = "all";
    setF(v); router.replace(listUrl(v), { scroll: false });
  };
  const filtered = f.role !== "all" || f.staff !== "all" || f.branch !== "all";
  const resetFilters = () => set({ role: "all", staff: "all", branch: "all" });

  return (
    <div className="rl-app rl-root">
      <PageBar title={admin ? "Tasks" : "My Tasks"} sub={everyone.data ? plural(everyone.data.open, "open task") : ""} back={admin ? "/more" : undefined}
        action={admin ? <AddButton label="New Task" onClick={() => setCreating(true)} /> : undefined} />
      <main className="rl-app__main">
        <div className="rl-searchbar rl-searchbar--filters">
          <SearchField value={text} onChange={setText} placeholder={admin ? "Task or staff name" : "Search your tasks"} label={admin ? "Search tasks or staff name" : "Search your tasks"}
            filter={admin ? { on: filtered, onClick: () => setSheet(true) } : undefined} />
          <Chips name="tk-filter" label="Filter tasks" value={f.state} onChange={(v) => set({ state: v })} options={[
            { value: "open", label: "Open", count: counts?.open }, { value: "overdue", label: "Overdue", count: counts?.overdue },
            { value: "done", label: "Done", count: counts?.done }, { value: "all", label: "All", count: counts?.all },
          ]} />
        </div>
        <section className="rl-section" aria-label="Tasks">
          <div className="rl-listmeta">
            <p role="status">{q.isLoading ? "Loading…" : `Showing ${plural(shown.length, "task")}${shown.length < total ? ` of ${total}` : ""}${personName ? ` for ${personName}` : ""}`}</p>
            <p>Due first</p>
          </div>
          {q.isLoading ? <SkeletonRows /> : shown.length ? (
            <><ul className="rl-card rl-mlist rl-mlist--compact">
              {shown.map((t) => (
                <li key={t.id}><button className="rl-mrow rl-tkrow" type="button" aria-haspopup="dialog" onClick={() => setOpenId(t.id)}>
                  {admin ? <Photo name={t.assignee_name} /> : <span className="rl-chipicon" aria-hidden="true"><Icon as={ClipboardList} size="sm" /></span>}
                  <span className="rl-row__title rl-mrow__name">{t.title}</span>
                  <span className="rl-row__meta rl-mrow__meta">{admin ? `${t.assignee_name} • ` : ""}{due(t)}</span>
                  <TaskStatus status={t.status} overdue={t.is_overdue} />
                </button></li>
              ))}
            </ul>
            <LoadMore q={q} /></>
          ) : dq ? (
            <Empty icon={SearchX} title={`No task matches “${dq}”`} text={admin ? "Check the spelling, or try the name of who it's for." : "Check the spelling, or try another word."}>
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setText("")}>Clear Search</button>
            </Empty>
          ) : filtered ? (
            <Empty icon={ClipboardList} title="No tasks match these filters" text="Try someone else, or a different branch.">
              <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={resetFilters}>Clear Filters</button>
            </Empty>
          ) : (
            <Empty icon={ClipboardList} title={f.state === "done" ? "Nothing done yet" : f.state === "overdue" ? "Nothing overdue" : "No open tasks"}
              text={admin ? "Give trainers and receptionists work with a due date, and follow it here." : "Tasks your admin gives you show up here."}>
              {admin && <button className="rl-button rl-button--block" type="button" onClick={() => setCreating(true)}>New Task</button>}
            </Empty>
          )}
        </section>
      </main>
      {admin && (
        <Sheet open={sheet} onClose={() => setSheet(false)} title="Filter tasks">
          <p className="rl-sheet__label" style={{ marginTop: 0, marginBottom: "var(--space-2)" }}>Assigned to</p>
          <Chips name="tk-role" label="Filter by role" scroll={false} value={f.role} onChange={(v) => set({ role: v })} options={[
            { value: "all", label: "Everyone", count: counts?.by_role.all }, { value: "trainer", label: "Trainers", count: counts?.by_role.trainer },
            { value: "receptionist", label: "Receptionists", count: counts?.by_role.receptionist },
          ]} />
          {role.branches.length > 1 && (
            <>
              <p className="rl-sheet__label" style={{ marginBottom: "var(--space-2)" }}>Branch</p>
              <Chips name="tk-branch" label="Filter by branch" scroll={false} value={f.branch} onChange={(v) => set({ branch: v })}
                options={[{ value: "all", label: "All branches" }, ...role.branches.map((b) => ({ value: String(b.id), label: b.name }))]} />
            </>
          )}
          <p className="rl-sheet__label" style={{ marginBottom: "var(--space-2)" }}>Staff</p>
          <Chips name="tk-staff" label="Filter by staff" scroll={false} value={f.staff} onChange={(v) => set({ staff: v })}
            options={[{ value: "all", label: "Anyone" }, ...people.map((s) => ({ value: String(s.id), label: s.name }))]} />
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--block" type="button" onClick={() => setSheet(false)}>{q.isLoading ? "Done" : `Show ${plural(total, "task")}`}</button>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" disabled={!filtered} onClick={resetFilters}>Reset</button>
          </div>
        </Sheet>
      )}
      <TaskSheet task={current} admin={admin} onClose={() => { setOpenId(null); router.replace(listUrl(f), { scroll: false }); }} />
      {admin && <NewTaskSheet open={creating} onClose={() => setCreating(false)} />}
    </div>
  );
}

function TaskSheet({ task, admin, onClose }: { task: Task | null; admin: boolean; onClose: () => void }) {
  const [text, setText] = useState("");
  const a = useAction();
  const act = async (path: string, body?: unknown) => { try { await a.run(`/api/tasks/${task!.id}/${path}/`, body, { refresh: ["/api/tasks/"] }); setText(""); } catch { /* shown */ } };
  const del = async () => { try { await a.run(`/api/tasks/${task!.id}/`, undefined, { method: "DELETE", refresh: ["/api/tasks/"] }); onClose(); } catch { /* shown */ } };
  return (
    <Sheet open={!!task} onClose={() => { a.clearError(); onClose(); }} title={task?.title}>
      {task && (
        <>
          <p className="rl-row__meta" style={{ marginTop: 0 }}>{task.assignee_name} • {due(task)} • <TaskStatus status={task.status} overdue={task.is_overdue} /></p>
          {task.details && <p style={{ margin: "var(--space-2) 0" }}>{task.details}</p>}
          <ol className="rl-tklog" style={{ listStyle: "none", padding: 0, margin: "var(--space-3) 0" }}>
            <li className="rl-row__meta">Assigned by {task.created_by_name} {ago(task.created_at)}</li>
            {task.updates.map((u) => (
              <li key={u.id} style={{ marginTop: "var(--space-2)" }}>
                {u.kind === "status" ? <span className="rl-row__meta">{u.text} by {u.author}, {ago(u.created_at)}</span>
                  : <><p style={{ margin: 0 }}>{u.text}</p><span className="rl-row__meta">{u.author}, {ago(u.created_at)}</span></>}
              </li>
            ))}
          </ol>
          {task.status !== "done" && (
            <Field label="Update" optional area hint="Your admin sees every update.">
              {(id) => <textarea className="rl-field__input" id={id} rows={2} value={text} onChange={(e) => setText(e.target.value)} />}
            </Field>
          )}
          <ErrorText>{a.error?.message}</ErrorText>
          <div className="rl-sheet__actions">
            {task.status === "todo" && !admin && <button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={() => act("start")}>Start Task</button>}
            {task.status !== "done" && text.trim() && <button className="rl-button rl-button--secondary rl-button--block" type="button" disabled={a.busy} onClick={() => act("updates", { text: text.trim() })}>Post Update</button>}
            {task.status !== "done" && <button className={`rl-button rl-button--block${task.status === "todo" && !admin ? " rl-button--secondary" : ""}`} type="button" disabled={a.busy} onClick={() => act("done", { note: text.trim() })}>Mark Done</button>}
            {task.status === "done" && <button className="rl-button rl-button--secondary rl-button--block" type="button" disabled={a.busy} onClick={() => act("reopen")}>Reopen</button>}
            {admin && <button className="rl-button rl-button--danger-quiet rl-button--block" type="button" disabled={a.busy} onClick={del}>Delete Task</button>}
          </div>
        </>
      )}
    </Sheet>
  );
}

function NewTaskSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const staff = useStaffList({ is_active: true, limit: 100 });
  const { role } = useSession();
  const branches = role.branches;
  const [branch, setBranch] = useState("all");
  const everyone = (staff.data?.data.results ?? []).filter((s) => s.role !== "admin");
  // The branch only narrows who you can pick; it isn't saved on the task.
  const people = everyone.filter((s) => branch === "all" || s.branches.includes(Number(branch)));
  const branchNames = (ids: number[]) => ids.map((id) => branches.find((b) => b.id === id)?.name).filter(Boolean).join(", ");
  const [f, setF] = useState({ title: "", details: "", assignee: 0, due_date: isoDate(new Date()), due_time: "" });
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [done, setDone] = useState<string | null>(null);
  const a = useAction();
  async function save() {
    const e: Record<string, string> = {};
    if (!f.title.trim()) e.title = "Say what needs doing";
    if (!f.assignee) e.assignee = "Choose who does it";
    setErrs(e);
    if (Object.keys(e).length) return;
    try {
      await a.run("/api/tasks/", { ...f, title: f.title.trim(), due_time: f.due_time || null }, { refresh: ["/api/tasks/"] });
      setDone(everyone.find((p) => p.id === f.assignee)?.name ?? "");
      setF({ title: "", details: "", assignee: 0, due_date: isoDate(new Date()), due_time: "" });
    } catch { /* shown */ }
  }
  const close = () => { setDone(null); onClose(); };
  return (
    <Sheet open={open} onClose={close} title={done === null ? "New Task" : undefined}>
      {done !== null ? (
        <>
          <Confirm title="Task assigned" text={`${done} sees it in My Tasks now.`} />
          <div className="rl-sheet__actions">
            <button className="rl-button rl-button--block" type="button" onClick={close}>Done</button>
            <button className="rl-button rl-button--secondary rl-button--block" type="button" onClick={() => setDone(null)}>Assign Another</button>
          </div>
        </>
      ) : (
        <>
          <Field label="Task" error={errs.title}>{(id) => <input className="rl-field__input" id={id} value={f.title} placeholder="Restock towels at the desk" onChange={(e) => setF({ ...f, title: e.target.value })} />}</Field>
          {branches.length > 1 && (
            <Field label="Branch" optional hint="Shows only the staff who work there.">{(id) => (
              <select className="rl-field__input" id={id} value={branch} onChange={(e) => {
                const v = e.target.value;
                setBranch(v);
                const picked = everyone.find((p) => p.id === f.assignee);
                if (picked && v !== "all" && !picked.branches.includes(Number(v))) setF({ ...f, assignee: 0 });
              }}>
                <option value="all">All branches</option>
                {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            )}</Field>
          )}
          <Field label="Assign to" error={errs.assignee}>{(id) => (
            <select className="rl-field__input" id={id} value={f.assignee || ""} onChange={(e) => setF({ ...f, assignee: Number(e.target.value) })}>
              <option value="">Choose a trainer or receptionist</option>
              {people.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.role === "trainer" ? "Trainer" : "Receptionist"}{branches.length > 1 && branch === "all" && p.branches.length ? `, ${branchNames(p.branches)}` : ""})
                </option>
              ))}
            </select>
          )}</Field>
          <div className="rl-pair">
            <Field label="Due date">{(id) => <input className="rl-field__input" id={id} type="date" min={isoDate(new Date())} value={f.due_date} onChange={(e) => setF({ ...f, due_date: e.target.value })} />}</Field>
            <Field label="By" optional>{(id) => <input className="rl-field__input" id={id} type="time" value={f.due_time} onChange={(e) => setF({ ...f, due_time: e.target.value })} />}</Field>
          </div>
          <Field label="Details" optional area>{(id) => <textarea className="rl-field__input" id={id} rows={3} value={f.details} onChange={(e) => setF({ ...f, details: e.target.value })} />}</Field>
          <ErrorText>{a.error?.message}</ErrorText>
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={save}>{a.busy ? "Assigning…" : "Assign Task"}</button></div>
        </>
      )}
    </Sheet>
  );
}

export default function Page() { return <Suspense><TasksPage /></Suspense>; }
