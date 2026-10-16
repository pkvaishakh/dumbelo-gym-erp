# Switch

A switch for a setting that takes effect the moment it is flipped.

Use in a list of settings, such as notifications. You provide the title, one line saying what it does, and the input's `name`. The whole row is the label, at least 64px tall, so a tap anywhere on it flips the switch. The switch is a checkbox with `role="switch"`.

- Off: a `field-line` track with a `ground` knob on the left. On: an `ink` track with a `volt` knob on the right. Position carries the state, not colour alone.
- Never pair a switch with a Save button. For a choice that needs saving, use a checkbox ChoiceCard in a form.
- Say what the setting does in the second line, not "Enable" or "Disable".

```html
<label class="rl-setting">
  <span class="rl-setting__text"><span class="rl-row__title">Daily summary</span><span class="rl-row__meta">Revenue and check-ins at 9:00 PM</span></span>
  <span class="rl-switch"><input type="checkbox" role="switch" name="daily"><span></span></span>
</label>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo"><div class="rl-card"><label class="rl-setting"><span class="rl-setting__text"><span class="rl-row__title">Payments received</span><span class="rl-row__meta">A notification for each payment collected</span></span><span class="rl-switch"><input type="checkbox" role="switch" name="s1" checked><span></span></span></label><label class="rl-setting"><span class="rl-setting__text"><span class="rl-row__title">Daily summary</span><span class="rl-row__meta">Revenue and check-ins at 9:00 PM</span></span><span class="rl-switch"><input type="checkbox" role="switch" name="s2"><span></span></span></label></div></div>
```
