def make(w, **kw):
    data = {"title": "Restock towels", "assignee": w.desk.id, "due_date": str(w.today), **kw}
    r = w.client(w.admin).post("/api/tasks/", data, format="json")
    assert r.status_code == 201, r.json()
    return r.json()["id"]


def test_flow(w):
    t = make(w)
    c = w.client(w.desk)
    assert c.post(f"/api/tasks/{t}/start/").json()["status"] == "doing"
    assert c.post(f"/api/tasks/{t}/updates/", {"text": "Half done"}, format="json").status_code == 201
    r = c.post(f"/api/tasks/{t}/done/", {"note": "All stocked"}, format="json").json()
    assert r["status"] == "done"
    assert [u["text"] for u in r["updates"]] == ["Started", "Half done", "All stocked", "Marked done"]
    assert w.client(w.admin).post(f"/api/tasks/{t}/reopen/").json()["status"] == "todo"


def test_staff_see_only_their_tasks_and_cannot_create(w):
    make(w)
    make(w, assignee=w.trainer.id, title="Plan class")
    assert [t["title"] for t in w.client(w.trainer).get("/api/tasks/").json()["results"]] == ["Plan class"]
    assert w.client(w.trainer).post("/api/tasks/", {}, format="json").status_code == 403


def test_cannot_assign_to_member_or_admin(w):
    r = w.client(w.admin).post("/api/tasks/", {"title": "x", "assignee": w.admin.id, "due_date": str(w.today)}, format="json")
    assert r.status_code == 400


def test_filters_counts_and_open_first(w):
    from datetime import timedelta

    late = make(w, title="Late", due_date=str(w.today - timedelta(days=2)))
    finished = make(w, title="Finished", due_date=str(w.today - timedelta(days=5)))
    w.client(w.desk).post(f"/api/tasks/{finished}/done/", {}, format="json")
    make(w, title="Trainer job", assignee=w.trainer.id, due_date=str(w.today + timedelta(days=1)))
    c = w.client(w.admin)
    titles = lambda url: [t["title"] for t in c.get(url).json()["results"]]  # noqa: E731
    assert titles("/api/tasks/") == ["Late", "Trainer job", "Finished"]  # open by due date, done last
    assert titles("/api/tasks/?state=overdue") == ["Late"] == titles("/api/tasks/?overdue=true")
    assert titles("/api/tasks/?state=done") == ["Finished"]
    assert titles("/api/tasks/?state=open&role=trainer") == ["Trainer job"]
    assert c.get("/api/tasks/counts/").json() == {"all": 3, "done": 1, "overdue": 1, "open": 2, "by_role": {"all": 3, "trainer": 1, "receptionist": 2}}
    assert c.get("/api/tasks/counts/?role=receptionist").json()["open"] == 1
    assert w.client(w.trainer).get("/api/tasks/counts/").json()["all"] == 1  # staff count only their own
    assert late
