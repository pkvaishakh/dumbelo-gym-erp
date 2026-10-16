# FilterChips

A row of chips that filters a list by one value, each with its count.

Use under a search field on a list screen. You provide the options, their counts and the input `name`. It is the ChipSelect control in one line: add `rl-chips--scroll` and the row scrolls sideways instead of wrapping, with a slice of the next chip showing at the edge. Chips are 36px tall with a 44px touch area.

- Exactly one chip is on. The first is always "All".
- The count is the total for that value, not the number loaded so far.
- Keep labels to one or two words. Put anything that needs more room in a Sort and filter sheet.

```html
<div class="rl-chips rl-chips--scroll" role="radiogroup" aria-label="Filter by status">
  <label class="rl-chipopt"><input type="radio" name="status" value="all" checked><span>All<small>655</small></span></label>
  <label class="rl-chipopt"><input type="radio" name="status" value="expiring"><span>Expiring<small>11</small></span></label>
</div>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo"><div class="rl-chips rl-chips--scroll" style="margin-top:0" role="radiogroup" aria-label="Filter by status"><label class="rl-chipopt"><input type="radio" name="fc-status" value="all" checked><span>All<small>655</small></span></label><label class="rl-chipopt"><input type="radio" name="fc-status" value="active"><span>Active<small>612</small></span></label><label class="rl-chipopt"><input type="radio" name="fc-status" value="expiring"><span>Expiring<small>11</small></span></label><label class="rl-chipopt"><input type="radio" name="fc-status" value="due"><span>Payment due<small>14</small></span></label><label class="rl-chipopt"><input type="radio" name="fc-status" value="expired"><span>Expired<small>35</small></span></label><label class="rl-chipopt"><input type="radio" name="fc-status" value="frozen"><span>Frozen<small>8</small></span></label></div></div>
```
