# ChoiceCard

One option in a choice, as a card: a mark, a name, a line of detail and, where there is one, a price.

Use when picking one of a few things that each need explaining: a plan, an add-on, a payment method. You provide the input's `name` and `value`, the name, the detail and the price. Wrap the cards in `rl-choices`.

- Radio cards for one of several (always start with one selected); a checkbox card (`rl-choice__mark--box`) for something that can be added or left out.
- The selected card has a 2px `ink` edge and a `volt` mark with a check: two signals, not colour alone.
- `rl-choices--2` lays cards out two across with an icon above the name, for short options such as payment methods.
- The whole card is the tap target, at least 64px tall. The real input sits invisibly over it, so it works with a keyboard and a screen reader.

```html
<div class="rl-choices">
  <label class="rl-choice"><input type="radio" name="plan" value="4500" checked>
    <span class="rl-choice__box"><span class="rl-choice__mark"><!-- check icon --></span>
      <span class="rl-choice__text"><span class="rl-row__title">Quarterly</span><span class="rl-row__meta">3 months</span></span>
      <span class="rl-choice__price">₹4,500</span></span></label>
</div>
```

## Markup (from the design system preview)

```html
<div class="rl-root rl-app demo" style="min-height:0;padding-bottom:0;background:none"><div class="rl-choices"><label class="rl-choice"><input type="radio" name="demo-plan" value="1500"><span class="rl-choice__box"><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Monthly</span><span class="rl-row__meta">1 month</span></span><span class="rl-choice__price">₹1,500</span></span></label><label class="rl-choice"><input type="radio" name="demo-plan" value="4500" checked><span class="rl-choice__box"><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Quarterly</span><span class="rl-row__meta">3 months</span></span><span class="rl-choice__price">₹4,500</span></span></label><label class="rl-choice"><input type="radio" name="demo-plan" value="9000"><span class="rl-choice__box"><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Premium</span><span class="rl-row__meta">3 months, with classes and a diet plan</span></span><span class="rl-choice__price">₹9,000</span></span></label></div><div class="rl-choices"><label class="rl-choice"><input type="checkbox" name="demo-pt" value="1" checked><span class="rl-choice__box"><span class="rl-choice__mark rl-choice__mark--box"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Personal training</span><span class="rl-row__meta">12 sessions with a trainer</span></span><span class="rl-choice__price">₹6,000</span></span></label></div><div class="rl-choices rl-choices--2"><label class="rl-choice"><input type="radio" name="demo-m" value="UPI" checked><span class="rl-choice__box"><Icon class="rl-icon"/><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">UPI</span></span></span></label><label class="rl-choice"><input type="radio" name="demo-m" value="Cash"><span class="rl-choice__box"><Icon class="rl-icon"/><span class="rl-choice__mark"><Icon class="rl-icon rl-icon--xs"/></span><span class="rl-choice__text"><span class="rl-row__title">Cash</span></span></span></label></div></div>
```
