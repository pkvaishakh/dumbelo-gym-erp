# MembershipCard

The member's membership at a glance: status, plan, days remaining, and a thin bar for the plan period.

Use at the top of Member Home, about 120px tall so today's plan stays above the fold. You provide the status, the plan name, the days remaining, the fraction of the period used (`--v` on `rl-bar__fill`), and the start and end dates. The whole card links to the membership page; "View Membership" names that link.

- The large figure is the days remaining, never the percentage.
- Renewal state, at seven days or fewer: add `rl-pass--renew`, change the badge to "Expiring soon" and add a "Renew Now" button. The card is then a container, with the link and the button as separate targets.
- Use the StatusBadge wording and colours; do not restyle the badge for this card.

## Markup (from the design system preview)

```html
<div class="rl-root demo"><a class="rl-pass rl-pressable" href="#" aria-label="Premium Plan, active, 24 days remaining. View membership">
  <span class="rl-pass__top"><span class="rl-status rl-status--active">Active</span><span class="rl-pass__plan">Premium Plan</span><span class="rl-pass__link">View Membership<Icon class="rl-icon rl-icon--xs"/></span></span>
  <p class="rl-figure">24 <small>days remaining</small></p>
  <span class="rl-bar" role="img" aria-label="67 of 91 days used"><span class="rl-bar__fill" style="--v:0.736"></span></span>
  <span class="rl-pass__dates"><span>29 Jul 2026</span><span>Expires 28 Oct 2026</span></span>
</a><div class="rl-pass rl-pass--renew">
  <div class="rl-pass__top"><span class="rl-status rl-status--expiring">Expiring soon</span><span class="rl-pass__plan">Premium Plan</span><a class="rl-pass__link" href="#">View Membership<Icon class="rl-icon rl-icon--xs"/></a></div>
  <p class="rl-figure">5 <small>days remaining</small></p>
  <span class="rl-bar" role="img" aria-label="86 of 91 days used"><span class="rl-bar__fill" style="--v:0.945"></span></span>
  <div class="rl-pass__dates"><span>10 Jul 2026</span><span>Expires 9 Oct 2026</span></div>
  <button class="rl-button rl-button--sm rl-button--block" type="button">Renew Now</button>
</div></div>
```
