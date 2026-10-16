# AmountField

A large field for typing an amount of money, with the currency sign fixed in front.

You provide the starting amount and what is due. Pair it with a two-option SegmentedControl, "Full amount" and "Part payment": on Full the field is read-only and shows what is due; on Part it unlocks for typing.

- 72px tall, in the `figure` style, numeric keyboard.
- Under it, one line that says what will still be due after this payment.
- An amount of zero or more than is due adds `is-invalid` and a message under the field. Never correct the amount silently.

## Markup (from the design system preview)

```html
<div class="rl-root demo" style="gap:var(--space-2)"><div class="rl-seg rl-seg--block" role="group" aria-label="Amount"><button class="rl-seg__btn" type="button" aria-pressed="false">Full amount</button><button class="rl-seg__btn" type="button" aria-pressed="true">Part payment</button></div><label class="rl-amount"><span aria-hidden="true">₹</span><input type="number" inputmode="numeric" value="1000" aria-label="Amount in rupees"></label><p class="rl-field__hint" style="margin:0">₹500 stays due after this payment</p></div>
```
