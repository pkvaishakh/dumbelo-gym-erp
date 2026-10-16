# AddExpenseDone

The sheet that confirms an expense.

A tick, "₹12,000 expense added", then the category, branch, date and how it was paid. Done returns to where the task was opened; Add Another clears the form.

## Markup (from the design system preview)

```html
<div class="rl-app rl-app--task rl-root" data-ascreen="addexpense" data-static>
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-task-back aria-label="Close"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title"><span data-mode-word>Add</span> Expense</h1>
</div></header>
<main class="rl-app__main">
<form class="rl-form" novalidate>
  <fieldset class="rl-fieldset"><legend>Amount</legend>
    <label class="rl-amount"><span aria-hidden="true">₹</span><input name="ex-amount" type="number" inputmode="decimal" min="1" aria-label="Amount in rupees" placeholder="0" value="12000"></label>
    <p class="rl-field__error" role="alert" data-amount-error hidden><Icon/><span>Enter the amount</span></p>
  </fieldset>
  <fieldset class="rl-fieldset"><legend>Category</legend><div class="rl-chips"><label class="rl-chipopt"><input type="radio" name="ex-cat" value="Rent"><span>Rent</span></label><label class="rl-chipopt"><input type="radio" name="ex-cat" value="Salaries"><span>Salaries</span></label><label class="rl-chipopt"><input type="radio" name="ex-cat" value="Utilities"><span>Utilities</span></label><label class="rl-chipopt"><input type="radio" name="ex-cat" value="Equipment" checked><span>Equipment</span></label><label class="rl-chipopt"><input type="radio" name="ex-cat" value="Maintenance"><span>Maintenance</span></label><label class="rl-chipopt"><input type="radio" name="ex-cat" value="Supplies"><span>Supplies</span></label><label class="rl-chipopt"><input type="radio" name="ex-cat" value="Marketing"><span>Marketing</span></label><label class="rl-chipopt"><input type="radio" name="ex-cat" value="Other"><span>Other</span></label></div>
    <p class="rl-field__error" role="alert" data-cat-error hidden><Icon/><span>Choose a category</span></p>
  </fieldset>
  <div class="rl-field">
  <label class="rl-field__label" for="ex-note">What it was for <span class="rl-optional">(optional)</span></label>
  <div class="rl-field__control"><input class="rl-field__input" id="ex-note" name="ex-note" type="text" autocomplete="off" enterkeyhint="next" placeholder="For example, treadmill belt replacement"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span></span></p>
</div>
  <fieldset class="rl-fieldset"><legend>Branch</legend><div class="rl-chips"><label class="rl-chipopt"><input type="radio" name="ex-branch" value="Indiranagar" data-label="Indiranagar" checked><span>Indiranagar</span></label><label class="rl-chipopt"><input type="radio" name="ex-branch" value="Koramangala" data-label="Koramangala"><span>Koramangala</span></label><label class="rl-chipopt"><input type="radio" name="ex-branch" value="HSR Layout" data-label="HSR Layout"><span>HSR Layout</span></label><label class="rl-chipopt"><input type="radio" name="ex-branch" value="Whitefield" data-label="Whitefield"><span>Whitefield</span></label></div></fieldset>
  <fieldset class="rl-fieldset"><legend>Date paid</legend><div class="rl-chips"><label class="rl-chipopt"><input type="radio" name="ex-when" value="today" data-label="Today" checked><span>Today</span></label><label class="rl-chipopt"><input type="radio" name="ex-when" value="yesterday" data-label="Yesterday"><span>Yesterday</span></label><label class="rl-chipopt"><input type="radio" name="ex-when" value="other" data-label="Another day"><span>Another day</span></label></div>
    <div class="rl-field" data-date-field style="margin-top:var(--space-2)" hidden><div class="rl-field__control"><input class="rl-field__input" type="date" name="ex-date" aria-label="Date of the expense" max="2026-10-04" value="2026-10-02"></div></div>
  </fieldset>
  <fieldset class="rl-fieldset"><legend>Paid by</legend><div class="rl-choices rl-choices--2"><label class="rl-choice"><input type="radio" name="ex-method" value="UPI" checked><span class="rl-choice__box"><Icon class="rl-icon"/><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">UPI</span></span></span></label><label class="rl-choice"><input type="radio" name="ex-method" value="Cash"><span class="rl-choice__box"><Icon class="rl-icon"/><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Cash</span></span></span></label><label class="rl-choice"><input type="radio" name="ex-method" value="Card"><span class="rl-choice__box"><Icon class="rl-icon"/><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Card</span></span></span></label><label class="rl-choice"><input type="radio" name="ex-method" value="Bank transfer"><span class="rl-choice__box"><Icon class="rl-icon"/><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Bank transfer</span></span></span></label></div></fieldset>
  <div class="rl-field">
  <label class="rl-field__label" for="ex-to">Paid to <span class="rl-optional">(optional)</span></label>
  <div class="rl-field__control"><input class="rl-field__input" id="ex-to" name="ex-to" type="text" autocomplete="off" autocapitalize="words" enterkeyhint="done" placeholder="Shop, company or person"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span></span></p>
</div>
</form>
</main>
<div class="rl-actionbar"><div class="rl-actionbar__in"><button class="rl-button" type="button" data-save-expense><span data-save-label>Add Expense</span><span data-save-edit hidden>Save Changes</span></button></div></div>
<div class="rl-scrim is-open"></div>
<div class="rl-sheet is-open" id="ex-done" data-modal role="dialog" aria-modal="true" aria-labelledby="ex-done-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-confirm"><span class="rl-confirm__mark" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="ex-done-title" data-r="title">₹12,000 expense added</h2></div>
  <div class="rl-idcard"><dl class="rl-facts" style="margin:0;padding:0;border:0"><dt>Category</dt><dd data-r="cat">Equipment</dd><dt>Branch</dt><dd data-r="branch">Indiranagar</dd><dt>Date</dt><dd data-r="when">Today</dd><dt>Paid by</dt><dd data-r="method">UPI</dd></dl></div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-done="close">Done</button><button class="rl-button rl-button--secondary rl-button--block" type="button" data-done="again">Add Another</button></div>
</div>
</div>
```
