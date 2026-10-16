# ChipSelect

One option from a few single words, as a row of chips.

Use for short, optional choices such as gender or goal. You provide the legend, the input `name` and the options. Chips are 44px tall and wrap onto more lines when they need to.

- The chosen chip is `ink` with `on-ink` text; the others are `ground` with a `field-line` edge.
- Put the group in a `rl-fieldset` with a `legend`, and add "(optional)" when it can be skipped.
- To filter a list, use the one-line version with counts: FilterChips.
- More than about six options, or options that need explaining, belong in ChoiceCards or a list.

```html
<fieldset class="rl-fieldset"><legend>Goal <span class="rl-optional">(optional)</span></legend>
  <div class="rl-chips">
    <label class="rl-chipopt"><input type="radio" name="goal" value="Fat Loss"><span>Fat Loss</span></label>
  </div>
</fieldset>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo"><fieldset class="rl-fieldset"><legend>Goal <span class="rl-optional">(optional)</span></legend><div class="rl-chips"><label class="rl-chipopt"><input type="radio" name="demo-goal" value="Fat Loss"><span>Fat Loss</span></label><label class="rl-chipopt"><input type="radio" name="demo-goal" value="Muscle Gain" checked><span>Muscle Gain</span></label><label class="rl-chipopt"><input type="radio" name="demo-goal" value="General Fitness"><span>General Fitness</span></label><label class="rl-chipopt"><input type="radio" name="demo-goal" value="Strength"><span>Strength</span></label></div></fieldset></div>
```
