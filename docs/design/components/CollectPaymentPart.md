# CollectPaymentPart

Collect Payment with a part payment.

Choosing "Part payment" unlocks the amount for typing. The line under it says what will stay due, and the button follows the amount: "Collect ₹1,000". An amount of zero, or more than is due, shows a message under the field when Collect is tapped.

## Markup (from the design system preview)

```html
<div class="rl-app rl-app--task rl-root" data-flow="collect" data-due="1500" data-static>
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-task-back aria-label="Close"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title">Collect Payment</h1>
</div></header>
<main class="rl-app__main">
<form class="rl-form" novalidate>
  <section class="rl-section" aria-label="Member"><div class="rl-card rl-card--pad"><div class="rl-idcard__who"><span class="rl-photo rl-photo--lg" aria-hidden="true" data-p="initials" style="background:var(--surface)">FA</span><span><span class="rl-row__title" data-p="name">Farhan Ali</span><span class="rl-row__meta" data-p="id">RL-1723</span><span class="rl-status rl-status--due">Payment due</span></span></div></div></section>
  <fieldset class="rl-fieldset"><legend>Paying for</legend><div class="rl-card rl-card--pad" style="display:flex;align-items:center;gap:var(--space-3)"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><span style="flex:1;min-width:0"><span class="rl-row__title" data-p="item">Monthly Plan</span><span class="rl-row__meta" data-p="period">1 Oct 2026 to 31 Oct 2026</span></span><span class="rl-choice__price" data-p="price">₹1,500</span></div></fieldset>
  <fieldset class="rl-fieldset"><legend>Amount</legend>
    <div class="rl-seg rl-seg--block" role="group" aria-label="Amount"><button class="rl-seg__btn" type="button" data-mode="full" aria-pressed="false">Full amount</button><button class="rl-seg__btn" type="button" data-mode="part" aria-pressed="true">Part payment</button></div>
    <label class="rl-amount" style="margin-top:var(--space-2)"><span aria-hidden="true">₹</span><input name="cp-amount" id="cp-amount" type="number" inputmode="numeric" min="1" aria-label="Amount in rupees" value="1000"></label>
    <p class="rl-field__error" role="alert" data-amount-error hidden><Icon/><span></span></p>
    <p class="rl-field__hint" data-balance>₹500 stays due after this payment</p>
  </fieldset>
  <fieldset class="rl-fieldset"><legend>Paid by</legend><div class="rl-choices rl-choices--2"><label class="rl-choice"><input type="radio" name="cp-method" value="UPI" checked><span class="rl-choice__box"><Icon class="rl-icon"/><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">UPI</span></span></span></label><label class="rl-choice"><input type="radio" name="cp-method" value="Cash"><span class="rl-choice__box"><Icon class="rl-icon"/><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Cash</span></span></span></label><label class="rl-choice"><input type="radio" name="cp-method" value="Card"><span class="rl-choice__box"><Icon class="rl-icon"/><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Card</span></span></span></label><label class="rl-choice"><input type="radio" name="cp-method" value="Bank transfer"><span class="rl-choice__box"><Icon class="rl-icon"/><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Bank transfer</span></span></span></label></div></fieldset>
  <div class="rl-field" data-ref-field>
  <label class="rl-field__label" for="cp-ref"><span data-ref-label>UPI reference</span> <span class="rl-optional">(optional)</span></label>
  <div class="rl-field__control"><input class="rl-field__input" id="cp-ref" name="cp-ref" type="text" inputmode="text" autocapitalize="characters" autocomplete="off" enterkeyhint="done" placeholder="From the payment app"></div>
  <p class="rl-field__error" role="alert" hidden><Icon/><span></span></p>
</div>
</form>
</main>
<div class="rl-actionbar"><div class="rl-actionbar__in"><button class="rl-button" type="button" data-collect>Collect ₹1,000</button></div></div>
<div class="rl-scrim"></div>
<div class="rl-sheet" id="rl-sheet-paid" role="dialog" aria-modal="true" aria-labelledby="rl-sheet-paid-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-confirm"><span class="rl-confirm__mark" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-confirm__title" id="rl-sheet-paid-title" data-paid="title">₹1,000 received</h2></div>
  <div class="rl-idcard">
    <div class="rl-idcard__who"><span class="rl-photo rl-photo--lg" aria-hidden="true">FA</span><span><span class="rl-row__title" data-p="name">Farhan Ali</span><span class="rl-row__meta">Receipt R-10482</span><span class="rl-status rl-status--due" data-paid="status">Payment due</span></span></div>
    <dl class="rl-facts"><dt>Paid by</dt><dd data-paid="by">UPI</dd><dt>Balance</dt><dd data-paid="balance">₹500 due</dd></dl>
  </div>
  <div class="rl-sheet__actions"><button class="rl-button rl-button--block" type="button" data-paid-done>Done</button><button class="rl-button rl-button--secondary rl-button--block" type="button"><Icon class="rl-icon rl-icon--sm"/>Share Receipt</button></div>
</div>
</div>
```
