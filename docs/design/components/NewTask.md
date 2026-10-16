# NewTask

Giving a trainer or receptionist a task. A task screen: close, the title (New Task or Edit Task), the form, and Assign Task in the action bar.

- Task: one line, required ("Say what needs doing").
- Details: optional, three lines.
- Assign to: the branch's staff as ChoiceCards with their photo, trainers first, then receptionists. One person per task. Required ("Choose who does it").
- Due: a date (today or later) and an optional time. Without a time the task is due by the end of that day.
- Saving shows NewTaskDone. Assign Another clears the form; Done goes back where it was opened from.
- Edit Task is the same form filled in, with Save Changes. Changing the person moves the task to their My Tasks.
- Related: NewTaskErrors, NewTaskDone, Tasks.

## Markup (from the design system preview)

```html
<div class="rl-app rl-app--task rl-root" data-tkform data-static>
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-task-back aria-label="Close"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title" data-mode-word>New Task</h1>
</div></header>
<main class="rl-app__main"><form class="rl-form" novalidate onsubmit="return false">
<div class="rl-field">
  <label class="rl-field__label" for="tf-title">Task</label>
  <div class="rl-field__control"><input class="rl-field__input" id="tf-title" name="tf-title" type="text" autocomplete="off" autocapitalize="sentences" enterkeyhint="next" placeholder="For example, Restock the water cans"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span>Say what needs doing</span></p>
</div>
<div class="rl-field">
  <label class="rl-field__label" for="tf-note">Details <span class="rl-optional">(optional)</span></label>
  <div class="rl-field__control rl-field__control--area"><textarea class="rl-field__input" id="tf-note" name="tf-note" rows="3" placeholder="Anything they need to know"></textarea></div>
</div>
<fieldset class="rl-fieldset" data-tf-to><legend>Assign to</legend><p class="rl-sheet__label" style="margin:var(--space-2) 0 var(--space-1)">Trainers</p><div class="rl-choices"><label class="rl-choice"><input type="radio" name="tf-to" value="s1"><span class="rl-choice__box"><span class="rl-photo" aria-hidden="true">AR</span><span class="rl-choice__text"><span class="rl-row__title">Arjun Rao</span><span class="rl-row__meta">Trainer</span></span><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span></span></label><label class="rl-choice"><input type="radio" name="tf-to" value="s2"><span class="rl-choice__box"><span class="rl-photo" aria-hidden="true">KS</span><span class="rl-choice__text"><span class="rl-row__title">Kavya Shetty</span><span class="rl-row__meta">Trainer</span></span><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span></span></label><label class="rl-choice"><input type="radio" name="tf-to" value="s3"><span class="rl-choice__box"><span class="rl-photo" aria-hidden="true">NI</span><span class="rl-choice__text"><span class="rl-row__title">Neha Iyer</span><span class="rl-row__meta">Trainer</span></span><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span></span></label><label class="rl-choice"><input type="radio" name="tf-to" value="s4"><span class="rl-choice__box"><span class="rl-photo" aria-hidden="true">NP</span><span class="rl-choice__text"><span class="rl-row__title">Neeraj Pillai</span><span class="rl-row__meta">Trainer</span></span><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span></span></label></div><p class="rl-sheet__label" style="margin:var(--space-2) 0 var(--space-1)">Receptionists</p><div class="rl-choices"><label class="rl-choice"><input type="radio" name="tf-to" value="s5"><span class="rl-choice__box"><span class="rl-photo" aria-hidden="true">AD</span><span class="rl-choice__text"><span class="rl-row__title">Alex D’Souza</span><span class="rl-row__meta">Receptionist</span></span><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span></span></label><label class="rl-choice"><input type="radio" name="tf-to" value="s6"><span class="rl-choice__box"><span class="rl-photo" aria-hidden="true">IK</span><span class="rl-choice__text"><span class="rl-row__title">Imran Khan</span><span class="rl-row__meta">Receptionist</span></span><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span></span></label></div><p class="rl-field__error" role="alert" hidden><Icon/><span>Choose who does it</span></p><p class="rl-field__hint">Only staff at Indiranagar. They see it in My Tasks.</p></fieldset>
<fieldset class="rl-fieldset"><legend>Due</legend>
  <div class="rl-session__times"><label class="rl-mini"><span>Date</span><input type="date" name="tf-date" value="2026-10-05" min="2026-10-05"></label><label class="rl-mini"><span>Time <span class="rl-optional">(optional)</span></span><input type="time" name="tf-time" value="18:00"></label></div>
</fieldset>
</form></main>
<div class="rl-actionbar"><div class="rl-actionbar__in"><button class="rl-button" type="button" data-save><span data-save-add>Assign Task</span><span data-save-edit hidden>Save Changes</span></button></div></div>
<div class="rl-scrim"></div>
<div class="rl-sheet" id="tf-done" role="dialog" aria-modal="true" aria-labelledby="tf-done-title">
  <div class="rl-confirm"><span class="rl-confirm__mark" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="tf-done-title" data-r="title">Task assigned</h2><p class="rl-confirm__text">It is in their My Tasks now.</p></div>
  <div class="rl-tknote" style="margin-top:var(--space-4)"><dl class="rl-facts" style="margin:0;padding:0;border:0"><dt>To</dt><dd data-r="to">Imran Khan, receptionist</dd><dt>Due</dt><dd data-r="due">Today, 6 PM</dd></dl></div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-done>Done</button><button class="rl-button rl-button--secondary rl-button--block" type="button" data-again>Assign Another</button></div>
</div>
</div>
```
