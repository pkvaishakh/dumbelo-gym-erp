# SearchResult

One member in the search results: photo, name, member ID, status badge and an inline Check In button.

Use in a `rl-card rl-results` list inside the full-screen search. You provide the member and handle the button. The button is a small `ink` button (`rl-button rl-button--sm`), 44px tall, so a check-in is one tap from the result.

- Check In on an Active, Expiring or Payment due member confirms; on an Expired member it opens the blocked sheet. Do not hide the button for an expired member: staff need the path to renew.
- The row itself is not a link; the name can link to the profile if needed.

## Markup (from the design system preview)

```html
<div class="rl-root demo"><ul class="rl-card rl-results"><li><div class="rl-result"><span class="rl-photo" aria-hidden="true">RK</span><span class="rl-result__text"><span class="rl-row__title">Rahul Kumar</span><span class="rl-row__meta">RL-2041</span><span class="rl-status rl-status--active">Active</span></span><button class="rl-button rl-button--sm" type="button" data-checkin="RL-2041">Check In</button></div></li><li><div class="rl-result"><span class="rl-photo" aria-hidden="true">RP</span><span class="rl-result__text"><span class="rl-row__title">Rachana Pillai</span><span class="rl-row__meta">RL-1876</span><span class="rl-status rl-status--expiring">Expiring</span></span><button class="rl-button rl-button--sm" type="button" data-checkin="RL-1876">Check In</button></div></li><li><div class="rl-result"><span class="rl-photo" aria-hidden="true">RM</span><span class="rl-result__text"><span class="rl-row__title">Raghav Menon</span><span class="rl-row__meta">RL-1532</span><span class="rl-status rl-status--expired">Expired</span></span><button class="rl-button rl-button--sm" type="button" data-checkin="RL-1532">Check In</button></div></li></ul></div>
```
