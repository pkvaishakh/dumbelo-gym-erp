# TasksEmpty

Tasks before any have been set: the EmptyState says what tasks are for, under New Task. A filter that leaves nothing says "Nothing here" instead.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root" data-tkscreen="admin">
<header class="rl-appbar rl-appbar--scroll"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-back aria-label="Back"><Icon class="rl-icon"/></button>
  <div class="rl-appbar__who"><h1 class="rl-pagetitle">Tasks</h1><p class="rl-appbar__branch" data-tk-sub>Indiranagar • 0 open</p></div>
</div></header>
<main class="rl-app__main">
<section class="rl-section" aria-label="New task"><button class="rl-button rl-button--block" type="button" data-tk-new><Icon class="rl-icon rl-icon--sm"/>New Task</button></section>
<section class="rl-section" aria-label="Tasks">
  <div class="rl-chips rl-chips--scroll" role="radiogroup" aria-label="Filter tasks" style="margin-top:0"><label class="rl-chipopt"><input type="radio" name="tk-filter" value="open" checked><span>Open<small data-tcount="open">0</small></span></label><label class="rl-chipopt"><input type="radio" name="tk-filter" value="overdue"><span>Overdue<small data-tcount="overdue">0</small></span></label><label class="rl-chipopt"><input type="radio" name="tk-filter" value="done"><span>Done<small data-tcount="done">0</small></span></label><label class="rl-chipopt"><input type="radio" name="tk-filter" value="all"><span>All<small data-tcount="all">0</small></span></label></div>
  <div class="rl-chips rl-chips--scroll" role="radiogroup" aria-label="Assigned to" style="margin-top:var(--space-2)"><label class="rl-chipopt"><input type="radio" name="tk-who" value="all" checked><span>Everyone<small data-wcount="all">0</small></span></label><label class="rl-chipopt"><input type="radio" name="tk-who" value="trainer"><span>Trainers<small data-wcount="trainer">0</small></span></label><label class="rl-chipopt"><input type="radio" name="tk-who" value="receptionist"><span>Receptionists<small data-wcount="receptionist">0</small></span></label></div>
  <div class="rl-listmeta" style="margin-top:var(--space-3)"><p data-tk-count role="status">0 tasks</p><p data-tk-order>Due first</p></div>
  <ul class="rl-card rl-mlist rl-mlist--compact" data-tk-list hidden></ul>
  <div class="rl-empty" data-tk-empty><span class="rl-empty__icon" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-empty__title">No tasks yet</h2><p class="rl-empty__text">Give a trainer or receptionist something to do, with a due date. You can follow it here.</p></div>
</section>
</main>
<div class="rl-scrim" data-close></div>
<div class="rl-sheet" id="tk-sheet-admin" role="dialog" aria-modal="true" aria-labelledby="tk-sheet-admin-title" data-tk-sheet>
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="tk-sheet-admin-title">Task</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <div class="rl-tkhead"><p class="rl-tkhead__title" data-tf="title">Call members whose plan ends this week</p><span data-tf="badge"><span class="rl-status rl-status--tk-todo">To do</span></span></div>
  <dl class="rl-details"><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Assigned to</dt><dd data-tf="to">Alex D’Souza, receptionist</dd></div><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Due</dt><dd data-tf="due">Today, 12 PM</dd></div><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Set by</dt><dd data-tf="created">Meera Nair, Yesterday, 5:45 PM</dd></div></dl>
  <p class="rl-tknote" data-tf="note">11 members are on the Expiring list. Offer the Quarterly renewal and note who wants a call back.</p>
  <div class="rl-tkupdates"><h3 class="rl-sheet__label">Updates</h3><ol class="rl-tklog" data-tf="log"></ol><p class="rl-row__meta" data-tf="nolog">No updates yet.</p>
    <div class="rl-tkpost"><label class="rl-visually-hidden" for="tk-sheet-admin-text">Add an update</label><textarea class="rl-field__input" id="tk-sheet-admin-text" rows="2" placeholder="Add an update" data-tk-text></textarea><button class="rl-button rl-button--secondary rl-button--sm" type="button" data-tk-post>Post</button></div>
    <p class="rl-field__error" role="alert" data-tk-posterr hidden><Icon/><span>Write something first</span></p></div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-tk-start>Start Task</button><button class="rl-button rl-button--secondary rl-button--block" type="button" data-tk-done>Mark Done</button><button class="rl-button rl-button--secondary rl-button--block" type="button" data-tk-reopen hidden>Reopen</button><button class="rl-button rl-button--secondary rl-button--block" type="button" data-tk-edit>Edit Task</button><button class="rl-button rl-button--danger-quiet rl-button--block" type="button" data-tk-delete-open aria-haspopup="dialog">Delete Task</button></div>
</div>
<div class="rl-sheet" id="tk-confirm" data-modal role="alertdialog" aria-modal="true" aria-labelledby="tk-confirm-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-confirm"><span class="rl-confirm__mark rl-confirm__mark--blocked" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="tk-confirm-title">Delete this task?</h2><p class="rl-confirm__text" data-tf="deltext">It disappears for Alex D’Souza too, with its updates. This cannot be undone.</p></div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--danger rl-button--block" type="button" data-tk-delete>Delete Task</button><button class="rl-button rl-button--secondary rl-button--block" type="button" data-tk-keep>Keep It</button></div>
</div>
<script type="application/json" data-tk-store>{"now": "2026-10-05T08:40", "me": "admin", "role": "admin", "staff": [{"id": "s1", "name": "Arjun Rao", "initials": "AR", "role": "trainer", "roleLabel": "Trainer"}, {"id": "s2", "name": "Kavya Shetty", "initials": "KS", "role": "trainer", "roleLabel": "Trainer"}, {"id": "s3", "name": "Neha Iyer", "initials": "NI", "role": "trainer", "roleLabel": "Trainer"}, {"id": "s4", "name": "Neeraj Pillai", "initials": "NP", "role": "trainer", "roleLabel": "Trainer"}, {"id": "s5", "name": "Alex D’Souza", "initials": "AD", "role": "receptionist", "roleLabel": "Receptionist"}, {"id": "s6", "name": "Imran Khan", "initials": "IK", "role": "receptionist", "roleLabel": "Receptionist"}], "admin": {"id": "admin", "name": "Meera Nair", "initials": "MN", "roleLabel": "Admin"}, "tasks": []}</script>
</div>
```
