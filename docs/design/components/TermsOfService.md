# TermsOfService

The Terms of Service, opened from the sign-in screen.

A reading page on `ground`: back arrow and title, a switch between Terms of Service and Privacy Policy, a note that this is sample text to replace, then short sections with a heading and a paragraph each. Lines stop at 64 characters for reading.

- Sample text only. The gym must replace it with its own terms before launch.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root rl-app--legal" data-legal>
<header class="rl-appbar"><div class="rl-appbar__in">
  <button class="rl-iconbtn rl-iconbtn--plain" type="button" data-back aria-label="Back"><Icon class="rl-icon"/></button>
  <h1 class="rl-topbar__title" data-legal-title>Terms of Service</h1>
</div></header>
<main class="rl-app__main">
<div class="rl-seg rl-seg--block rl-seg--onsurface" role="group" aria-label="Document"><button class="rl-seg__btn" type="button" data-doc="terms" aria-pressed="true">Terms of Service</button><button class="rl-seg__btn" type="button" data-doc="privacy" aria-pressed="false">Privacy Policy</button></div>
<p class="rl-legal__note"><Icon class="rl-icon rl-icon--sm"/>Sample text. Replace it with your gym’s own terms and policy before launch. Last updated 1 Oct 2026.</p>
<article class="rl-legal" data-doc-body="terms"><h2 class="rl-legal__h">Your membership</h2><p class="rl-legal__p">A membership lets you use the gym floor at your home branch during opening hours, and any classes or personal training your plan includes. It is for you only and cannot be shared.</p><h2 class="rl-legal__h">Payments and renewals</h2><p class="rl-legal__p">Plans are paid in advance. We send a reminder before your plan ends; it does not renew on its own. Prices can change, but never for a plan you have already paid for.</p><h2 class="rl-legal__h">Freezing and refunds</h2><p class="rl-legal__p">You can freeze your membership for up to four weeks at a time, and the days you do not use are added to the end. Refunds follow the policy shown at the front desk.</p><h2 class="rl-legal__h">Using the gym</h2><p class="rl-legal__p">Check in each visit, follow staff instructions, and put equipment back. We may pause a membership for behaviour that puts others at risk.</p><h2 class="rl-legal__h">Your health</h2><p class="rl-legal__p">Tell a trainer about any injury or condition before you train. Use the equipment at your own risk and stop if you feel unwell.</p></article><article class="rl-legal" data-doc-body="privacy" hidden><h2 class="rl-legal__h">What we keep</h2><p class="rl-legal__p">Your name, mobile number and email; your plan and payments; when you check in; and, if you train with us, your workouts, measurements and notes your trainer writes.</p><h2 class="rl-legal__h">Why we keep it</h2><p class="rl-legal__p">To run your membership, let you in, take payments, remind you before your plan ends, and help your trainer plan your sessions.</p><h2 class="rl-legal__h">Who can see it</h2><p class="rl-legal__p">Staff at your gym, each only what their job needs: the front desk sees payments, trainers see training. We do not sell your details.</p><h2 class="rl-legal__h">How long we keep it</h2><p class="rl-legal__p">While you are a member, and for up to two years after, unless the law asks us to keep it longer.</p><h2 class="rl-legal__h">Your choices</h2><p class="rl-legal__p">You can see and change your details in Account Details, turn reminders off in Notifications, or ask the front desk for a copy of everything we hold.</p></article>
<p class="rl-row__meta" style="margin-top:var(--space-6)">Questions? Ask at the front desk of your branch.</p>
</main>
</div>
```
