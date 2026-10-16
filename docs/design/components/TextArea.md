# TextArea

A field for a few lines of free text, such as a note.

The TextField with a taller control. You provide the label, the placeholder and the value. Add `rl-field__control--area` to the control and use a `textarea` with the `rl-field__input` class. It starts three lines tall and does not resize by hand.

- Notes are optional: say so in the label.
- Use the hint under the field to say who will read it.

```html
<div class="rl-field">
  <label class="rl-field__label" for="note">Note for Rahul <span class="rl-optional">(optional)</span></label>
  <div class="rl-field__control rl-field__control--area"><textarea class="rl-field__input" id="note" rows="3" placeholder="How it went, what to change next time"></textarea></div>
  <p class="rl-field__hint">Rahul sees this on the Workout tab.</p>
</div>
```

## Markup (from the design system preview)

```html
<div class="rl-root rl-app demo" style="min-height:0;padding-bottom:0;background:none"><div class="rl-field"><label class="rl-field__label" for="ta-note">Note for Rahul <span class="rl-optional">(optional)</span></label>
  <div class="rl-field__control rl-field__control--area"><textarea class="rl-field__input" id="ta-note" name="ta-note" rows="3" placeholder="How it went, what to change next time"></textarea></div>
  <p class="rl-field__hint">Rahul sees this on the Workout tab.</p></div></div>
```
