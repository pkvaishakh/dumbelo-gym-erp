# SelectField

A choice from a list too long for chips, as a native select in the TextField's shell.

Use for a branch, a trainer, or any list of more than about six. You provide the label, the options and a first option that reads as a prompt ("Choose your branch") with an empty value. Add `required` so the prompt shows in `ink-muted` until something is chosen. A chevron sits on the right.

- The phone's own picker opens; do not build a custom list.
- A dropdown is the last resort. Prefer chips or ChoiceCards when the options are few.

```html
<div class="rl-field">
  <label class="rl-field__label" for="branch">Branch</label>
  <div class="rl-field__control">
    <select class="rl-field__input" id="branch" name="branch" required>
      <option value="" selected>Choose your branch</option>
      <option>Indiranagar</option>
    </select>
    <!-- chevron-down icon, rl-icon rl-icon--sm -->
  </div>
</div>
```

## Markup (from the design system preview)

```html
<form class="rl-root col" onsubmit="return false"><div class="rl-field"><label class="rl-field__label" for="sf-branch">Branch</label><div class="rl-field__control"><select class="rl-field__input" id="sf-branch" required><option value="" selected>Choose your branch</option><option>Indiranagar</option><option>Koramangala</option><option>HSR Layout</option><option>Whitefield</option></select><Icon class="rl-icon rl-icon--sm"/></div></div></form>
```
