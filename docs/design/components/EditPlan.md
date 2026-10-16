# EditPlan

Editing a plan, shown for Premium: Add Plan with its values filled in, the title "Edit Plan", the price note visible, and the button "Save Changes".

## Markup (from the design system preview)

```html
<div class="rl-app rl-app--task rl-root" data-gscreen="planform" data-static>
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-task-back aria-label="Close"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title"><span data-mode-word>Edit</span> Plan</h1>
</div></header>
<main class="rl-app__main"><form class="rl-form" novalidate onsubmit="return false">
<fieldset class="rl-fieldset"><legend>Type</legend><div class="rl-chips"><label class="rl-chipopt"><input type="radio" name="pf-kind" value="membership" checked><span>Membership</span></label><label class="rl-chipopt"><input type="radio" name="pf-kind" value="pt"><span>Personal training</span></label></div></fieldset>
<div class="rl-field">
  <label class="rl-field__label" for="pf-name">Plan name</label>
  <div class="rl-field__control"><input class="rl-field__input" id="pf-name" name="pf-name" type="text" autocomplete="off" autocapitalize="words" enterkeyhint="next" placeholder="For example, Half-yearly" value="Premium"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span>Enter the plan name</span></p>
  <p class="rl-field__hint">Staff pick plans by this name in Add Member.</p>
</div>
<fieldset class="rl-fieldset" data-for-kind="membership"><legend>Length</legend><div class="rl-chips"><label class="rl-chipopt"><input type="radio" name="pf-months" value="1"><span>1 month</span></label><label class="rl-chipopt"><input type="radio" name="pf-months" value="3" checked><span>3 months</span></label><label class="rl-chipopt"><input type="radio" name="pf-months" value="6"><span>6 months</span></label><label class="rl-chipopt"><input type="radio" name="pf-months" value="12"><span>12 months</span></label></div></fieldset>
<div class="rl-field" data-for-kind="pt" hidden>
  <label class="rl-field__label" for="pf-sessions">Sessions</label>
  <div class="rl-field__control"><input class="rl-field__input" id="pf-sessions" name="pf-sessions" type="number" inputmode="numeric" min="1" enterkeyhint="next" value="12"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span>Enter how many sessions</span></p>
</div>
<fieldset class="rl-fieldset"><legend>Price</legend>
    <label class="rl-amount"><span aria-hidden="true">₹</span><input name="pf-price" type="number" inputmode="numeric" min="1" aria-label="Price in rupees" placeholder="0" value="9000"></label>
    <p class="rl-field__error" role="alert" data-price-error hidden><Icon/><span>Enter the price</span></p>
    <p class="rl-field__hint" data-price-hint>Members already on this plan keep the price they paid.</p>
  </fieldset>
<div class="rl-field">
  <label class="rl-field__label" for="pf-includes">What it includes <span class="rl-optional">(optional)</span></label>
  <div class="rl-field__control"><input class="rl-field__input" id="pf-includes" name="pf-includes" type="text" autocomplete="off" enterkeyhint="done" placeholder="For example, classes and a diet plan" value="Classes and a diet plan"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span></span></p>
  <p class="rl-field__hint">The gym floor is always included. Add anything extra.</p>
</div>
</form></main>
<div class="rl-actionbar"><div class="rl-actionbar__in"><button class="rl-button" type="button" data-save><span data-save-add hidden>Add Plan</span><span data-save-edit>Save Changes</span></button></div></div>
<div class="rl-scrim"></div>
<div class="rl-sheet" id="pf-done" data-modal role="dialog" aria-modal="true" aria-labelledby="pf-done-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-confirm"><span class="rl-confirm__mark" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="pf-done-title" data-r="title">Changes saved</h2></div>
  <div class="rl-idcard"><dl class="rl-facts" style="margin:0;padding:0;border:0"><dt>Length</dt><dd data-r="length">6 months</dd><dt>Price</dt><dd data-r="price">₹10,500</dd><dt>Sold at</dt><dd>All 4 branches</dd></dl></div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-done>Done</button><button class="rl-button rl-button--secondary rl-button--block" type="button" data-again>Add Another</button></div>
</div>
</div>
```
