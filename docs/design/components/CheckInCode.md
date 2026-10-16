# CheckInCode

A member's QR code for checking in, with their name, member ID and plan under it.

Use in a sheet opened from the member's More tab. You provide the code to encode (the member ID or a token for it). The code is 200px square, black modules on white with a quiet zone, inside a `surface` panel, so it scans at any screen brightness.

- Always black on white. Never colour, tint or put a logo inside the code.
- Say under it where to use it, in one line.
- The member's name sits under the code so the front desk can match it to the person in front of them.

## Markup (from the design system preview)

```html
<div class="rl-root demo"><div class="rl-card rl-card--pad"><div class="rl-checkcode" style="margin:0"><Icon class="rl-qr"/><p class="rl-row__title">Rahul Kumar</p><p class="rl-row__meta">RL-2041 • Premium Plan</p></div></div></div>
```
