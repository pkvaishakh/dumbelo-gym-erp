# AddBranch

Adding a branch.

A task screen. Branch name, address (three lines), phone with `+91` fixed in front, and opening hours as named sessions, with a choice of Every day or Monday to Saturday. Each field says who sees it. The action bar's button is Add Branch.

- A name already used by another branch is refused: "There is already a branch called Indiranagar".
- Opening hours are a list of sessions, each a name and a start and end time ("Morning, 5 to 10 AM", "Afternoon, 12 to 4 PM", "Evening, 5 to 10 PM"). A gap between sessions means the branch is closed then. A new branch starts with these three; Add Session adds another, the cross removes one, and any name works ("Ladies only", "All day").
- Each session needs a name, and must end after it starts. Two sessions cannot overlap or share a name; the error sits on the session at fault. At least one session is needed. Sessions are saved in time order.
- Attendance groups check-ins by these sessions: its filters, the Staff side and the Check-ins today card on Admin Home all use the branch's own session names.
- A new branch starts with no members and no staff. Add staff to it from Add Trainer and Add Receptionist.
- Related: AddBranchErrors, AddBranchDone, EditBranch.

## Markup (from the design system preview)

```html
<div class="rl-app rl-app--task rl-root" data-gscreen="branchform" data-static>
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-task-back aria-label="Close"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title"><span data-mode-word>Add</span> Branch</h1>
</div></header>
<main class="rl-app__main"><form class="rl-form" novalidate onsubmit="return false">
<div class="rl-field">
  <label class="rl-field__label" for="bf-name">Branch name</label>
  <div class="rl-field__control"><input class="rl-field__input" id="bf-name" name="bf-name" type="text" autocomplete="off" autocapitalize="words" enterkeyhint="next" placeholder="For example, Jayanagar"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span>Enter the branch name</span></p>
  <p class="rl-field__hint">Members and staff see this name.</p>
</div>
<div class="rl-field">
  <label class="rl-field__label" for="bf-address">Address</label>
  <div class="rl-field__control rl-field__control--area"><textarea class="rl-field__input" id="bf-address" name="bf-address" rows="3" autocomplete="street-address" placeholder="Street, area, city and PIN code"></textarea></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span>Enter the address</span></p>
</div>
<div class="rl-field">
  <label class="rl-field__label" for="bf-phone">Phone</label>
  <div class="rl-field__control"><span class="rl-field__prefix">+91</span><input class="rl-field__input" id="bf-phone" name="bf-phone" type="tel" inputmode="tel" autocomplete="off" enterkeyhint="done" placeholder="80 4120 1005"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span>Enter a 10-digit phone number</span></p>
  <p class="rl-field__hint">Members call this number. It shows in their app.</p>
</div>
<fieldset class="rl-fieldset" data-hours><legend>Opening hours</legend><p class="rl-field__hint" style="margin:0 0 var(--space-3)">Split the day into named sessions, with a break between them if the gym closes. Attendance groups check-ins by these sessions.</p><ul class="rl-sessions" data-sessions><li class="rl-session" data-session><div class="rl-session__top"><label class="rl-session__name"><span class="rl-visually-hidden">Session name</span><input class="rl-field__input" type="text" name="bf-sname" autocomplete="off" autocapitalize="words" placeholder="Name, for example Morning" value="Morning"></label><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-session-remove aria-label="Remove Morning"><Icon class="rl-icon rl-icon--sm"/></button></div><div class="rl-session__times"><label class="rl-mini"><span>Starts</span><input type="time" name="bf-sstart" value="05:00"></label><label class="rl-mini"><span>Ends</span><input type="time" name="bf-send" value="10:00"></label></div><p class="rl-field__error" role="alert" hidden><Icon/><span>Check this session</span></p></li><li class="rl-session" data-session><div class="rl-session__top"><label class="rl-session__name"><span class="rl-visually-hidden">Session name</span><input class="rl-field__input" type="text" name="bf-sname" autocomplete="off" autocapitalize="words" placeholder="Name, for example Morning" value="Afternoon"></label><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-session-remove aria-label="Remove Afternoon"><Icon class="rl-icon rl-icon--sm"/></button></div><div class="rl-session__times"><label class="rl-mini"><span>Starts</span><input type="time" name="bf-sstart" value="12:00"></label><label class="rl-mini"><span>Ends</span><input type="time" name="bf-send" value="16:00"></label></div><p class="rl-field__error" role="alert" hidden><Icon/><span>Check this session</span></p></li><li class="rl-session" data-session><div class="rl-session__top"><label class="rl-session__name"><span class="rl-visually-hidden">Session name</span><input class="rl-field__input" type="text" name="bf-sname" autocomplete="off" autocapitalize="words" placeholder="Name, for example Morning" value="Evening"></label><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-session-remove aria-label="Remove Evening"><Icon class="rl-icon rl-icon--sm"/></button></div><div class="rl-session__times"><label class="rl-mini"><span>Starts</span><input type="time" name="bf-sstart" value="17:00"></label><label class="rl-mini"><span>Ends</span><input type="time" name="bf-send" value="22:00"></label></div><p class="rl-field__error" role="alert" hidden><Icon/><span>Check this session</span></p></li></ul><button class="rl-button rl-button--secondary rl-button--block" type="button" data-session-add style="margin-top:var(--space-3)"><Icon class="rl-icon rl-icon--sm"/>Add Session</button><p class="rl-field__error" role="alert" data-sessions-error hidden><Icon/><span>Add at least one session</span></p><div class="rl-chips" style="margin-top:var(--space-4)"><label class="rl-chipopt"><input type="radio" name="bf-days" value="Every day" checked><span>Every day</span></label><label class="rl-chipopt"><input type="radio" name="bf-days" value="Monday to Saturday"><span>Monday to Saturday</span></label></div></fieldset>
</form></main>
<div class="rl-actionbar"><div class="rl-actionbar__in"><button class="rl-button" type="button" data-save><span data-save-add>Add Branch</span><span data-save-edit hidden>Save Changes</span></button></div></div>
<div class="rl-scrim"></div>
<div class="rl-sheet" id="bf-done" data-modal role="dialog" aria-modal="true" aria-labelledby="bf-done-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-confirm"><span class="rl-confirm__mark" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="bf-done-title" data-r="title">Jayanagar added</h2></div>
  <div class="rl-idcard"><dl class="rl-facts" style="margin:0;padding:0;border:0"><dt>Address</dt><dd data-r="address">11th Main Road, 4th Block…</dd><dt>Opening hours</dt><dd data-r="hours">Morning, 5 to 10 AM<br>Afternoon, 12 to 4 PM<br>Evening, 5 to 10 PM<br>Every day</dd><dt>Phone</dt><dd data-r="phone">+91 80 4120 1005</dd></dl></div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-done>Done</button><button class="rl-button rl-button--secondary rl-button--block" type="button" data-again>Add Another</button></div>
</div>
</div>
```
