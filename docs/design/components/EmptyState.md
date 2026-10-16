# EmptyState

What a list shows when there is nothing to list: an icon, one line saying why, one line saying what to try, and the way out.

Use in place of the list card, never inside it. You provide the icon, the two lines and up to two buttons, the primary one first.

- Say what happened in the person's own terms: "No member matches “zoya”", not "No results".
- Always offer an action: clear the search, clear the filters, or add the thing they were looking for.
- Do not use it while loading; show skeleton rows instead.

```html
<div class="rl-empty">
  <span class="rl-empty__icon" aria-hidden="true"><!-- icon --></span>
  <h2 class="rl-empty__title">No member matches “zoya”</h2>
  <p class="rl-empty__text">Check the spelling, or add them as a new member.</p>
  <div class="rl-empty__actions">
    <button class="rl-button rl-button--block" type="button">Add Member</button>
    <button class="rl-button rl-button--secondary rl-button--block" type="button">Clear Search</button>
  </div>
</div>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo"><div class="rl-empty">
  <span class="rl-empty__icon" aria-hidden="true"><Icon class="rl-icon"/></span>
  <h2 class="rl-empty__title">No member matches “zoya”</h2>
  <p class="rl-empty__text">Check the spelling, or add them as a new member.</p>
  <div class="rl-empty__actions"><button class="rl-button rl-button--block" type="button" data-empty-add>Add Member</button><button class="rl-button rl-button--secondary rl-button--block" type="button" data-empty-clear>Clear Search</button></div>
</div></div>
```
