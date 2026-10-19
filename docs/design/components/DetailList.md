# DetailList

Facts about one record as labelled rows: an icon, a small label, and the value under it.

Use on detail screens and in sheets wherever a person needs to read what something is: a staff member's contact details, an expense's fields, account details. You provide the rows. It is a `dl`: each row is a `rl-detail` with an icon chip, a `dt` and a `dd`. Rows are at least 64px tall, 56px inside a sheet.

- The label is `micro` in `ink-muted`; the value is `label` weight in `ink`. The label says what the value is in the reader's words: "Mobile number", not "Phone no."
- A long value wraps; it is never cut off.
- An empty value reads "Not added" or "Not set". Do not drop the row.
- Use `rl-facts` (label left, value right) only for short pairs inside a confirmation.

```html
<dl class="rl-card rl-details">
  <div class="rl-detail">
    <span class="rl-chipicon" aria-hidden="true"><!-- icon --></span>
    <dt>Mobile number</dt>
    <dd>+91 90000 30001</dd>
  </div>
</dl>
```

## Markup (from the design system preview)

```html
<div class="rl-root demo"><dl class="rl-card rl-details"><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Mobile number</dt><dd>+91 90000 30001</dd></div><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Email</dt><dd>arjun.rao@dumbelo.example</dd></div><div class="rl-detail"><span class="rl-chipicon" aria-hidden="true"><Icon class="rl-icon rl-icon--sm"/></span><dt>Started</dt><dd>12 Jan 2024</dd></div></dl></div>
```
