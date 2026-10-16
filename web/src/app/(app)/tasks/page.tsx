"use client";
import { ClipboardList, Plus } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import type { Task } from "@/api/gen/model";
import { useStaffList } from "@/api/gen/staff/staff";
import { useTasksListInfinite, useTasksRetrieve } from "@/api/gen/tasks/tasks";
import type { TasksListState } from "@/api/gen/model";
import { PageBar } from "@/components/shell";
import { Chips, Confirm, Empty, ErrorText, Field, Icon, LoadMore, Photo, Section, Sheet, SkeletonRows, TaskStatus } from "@/components/ui";
import { ago, clock, day, isoDate, plural } from "@/lib/format";
import { paged, pages, useAction, useGet } from "@/lib/hooks";
import { useSession } from "@/lib/session";
import type { TaskCounts } from "@/lib/types";

function due(t: Task) {
  const today = isoDate(new Date());
  const tm = t.due_time ? `, ${clock(t.due_time)}` : "";
  return t.due_date === today ? `Due today${tm}` : `Due ${day(t.due_date)}${tm}`;
}

function TasksPage() {
  const params = useSearchParams();
  const router = useRouter();
  const { role } = useSession();
  const admin = role.role === "admin";
  const [filter, setFilter] = useState(params.get("filter") ?? "open");
  const [whoF, setWhoF] = useState("all");
  const [openId, setOpenId] = useState<number | null>(Number(params.get("open")) || null);
  const [creating, setCreating] = useState(params.get("new") === "1");
  const who = whoF === "all" ? undefined : (whoF as "trainer" | "receptionist");
  const q = useTasksListInfinite({ ...(filter !== "all" ? { state: filter as TasksListState } : {}), ...(who ? { role: who } : {}) }, { query: paged });
  const { rows: shown, count: total } = pages(q);
  const everyone = useGet<TaskCounts>("/api/tasks/counts/");
  const narrowed = useGet<TaskCounts>("/api/tasks/counts/", { role: who }, !!who);
  const counts = who ? narrowed.data : everyone.data;
  const current = useTasksRetrieve(openId ?? 0, { query: { enabled: !!openId } }).data?.data ?? null;

  return (
    <div className="rl-app rl-root">
      <PageBar title={admin ? "Tasks" : "My Tasks"} sub={everyone.data ? plural(everyone.data.open, "open task") : ""} back={admin ? "/more" : undefined} />
      <main className="rl-app__main">
        {admin && <Section label="New task"><button className="rl-button rl-button--block" type="button" onClick={() => setCreating(true)}><Icon as={Plus} />New Task</button></Section>}
        <Section label="Tasks">
          <Chips name="tk-filter" label="Filter tasks" value={filter} onChange={setFilter} style={{ marginTop: 0 }} options={[
            { value: "open", label: "Open", count: counts?.open }, { value: "overdue", label: "Overdue", count: counts?.overdue },
            { value: "done", label: "Done", count: counts?.done }, { value: "all", label: "All", count: counts?.all },
          ]} />
          {admin && (
            <Chips name="tk-who" label="Assigned to" value={whoF} onChange={setWhoF} style={{ marginTop: "var(--space-2)" }} options={[
              { value: "all", label: "Everyone", count: everyone.data?.by_role.all }, { value: "trainer", label: "Trainers", count: everyone.data?.by_role.trainer },
              { value: "receptionist", label: "Receptionists", count: everyone.data?.by_role.receptionist },
            ]} />
          )}
          <div className="rl-listmeta" style={{ marginTop: "var(--space-3)" }}><p role="status">{q.isLoading ? "Loading…" : `Showing ${plural(shown.length, "task")}${shown.length < total ? ` of ${total}` : ""}`}</p><p>Due first</p></div>
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
          ) : (
            <Empty icon={ClipboardList} title={filter === "done" ? "Nothing done yet" : "No open tasks"} text={admin ? "Give trainers and receptionists work with a due date, and follow it here." : "Tasks your admin gives you show up here."} />
          )}
        </Section>
      </main>
      <TaskSheet task={current} admin={admin} onClose={() => { setOpenId(null); router.replace("/tasks", { scroll: false }); }} />
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
            <Field label="Update" optional hint="Your admin sees every update.">
              {(id) => <textarea className="rl-field__input" id={id} rows={2} value={text} placeholder="Called 6 of 11 so far" onChange={(e) => setText(e.target.value)} />}
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
  const people = (staff.data?.data.results ?? []).filter((s) => s.role !== "admin");
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
      setDone(people.find((p) => p.id === f.assignee)?.name ?? "");
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
          <Field label="Assign to" error={errs.assignee}>{(id) => (
            <select className="rl-field__input" id={id} value={f.assignee || ""} onChange={(e) => setF({ ...f, assignee: Number(e.target.value) })}>
              <option value="">Choose a trainer or receptionist</option>
              {people.map((p) => <option key={p.id} value={p.id}>{p.name} ({p.role === "trainer" ? "Trainer" : "Receptionist"})</option>)}
            </select>
          )}</Field>
          <div className="rl-pair">
            <Field label="Due date">{(id) => <input className="rl-field__input" id={id} type="date" min={isoDate(new Date())} value={f.due_date} onChange={(e) => setF({ ...f, due_date: e.target.value })} />}</Field>
            <Field label="By" optional>{(id) => <input className="rl-field__input" id={id} type="time" value={f.due_time} onChange={(e) => setF({ ...f, due_time: e.target.value })} />}</Field>
          </div>
          <Field label="Details" optional>{(id) => <textarea className="rl-field__input" id={id} rows={3} value={f.details} onChange={(e) => setF({ ...f, details: e.target.value })} />}</Field>
          <ErrorText>{a.error?.message}</ErrorText>
          <div className="rl-sheet__actions"><button className="rl-button rl-button--block" type="button" disabled={a.busy} onClick={save}>{a.busy ? "Assigning…" : "Assign Task"}</button></div>
        </>
      )}
    </Sheet>
  );
}

export default function Page() { return <Suspense><TasksPage /></Suspense>; }
