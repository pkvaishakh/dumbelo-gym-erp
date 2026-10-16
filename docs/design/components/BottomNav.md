# BottomNav

The fixed bottom navigation: Home, Attendance, a raised create button, Reports, More (the admin's bar).

You provide the four destinations and mark the current one with `aria-current="page"`: its icon sits on a `volt-soft` pill and its label turns `ink`. The centre button (`rl-fab`) is 60px, `volt` with an `ink` plus, raised above the bar; it opens the create sheet and its plus turns to a cross while the sheet is open.

- The destinations depend on the role: Home, Attendance, Reports, More for an admin, whose Members list lives in More; Home, Members, Attendance, More for a receptionist; Home, Schedule, Members, More for a trainer. The create sheet lists only what that role may create. Screens both roles share (Members, Attendance, a member's profile) show the bar of whoever is signed in: for the admin, Attendance is current on Attendance and More is current on Members and profiles.
- The member app has five equal tabs and no create button: Home, Workout, Diet, Progress, More.
- Always five slots, on every width; never a sidebar. The bar adds the bottom safe area below its 64px height.
- The create button is the only `volt` control on the screen. It has no text label, so give it `aria-label="Create"`.
- Give the screen bottom padding of `nav-height` plus `space-12` so the last section clears the bar.

## Markup (from the design system preview)

```html
<div class="rl-root"><nav class="rl-tabbar" aria-label="Main"><div class="rl-tabbar__in"><a class="rl-tab" href="#" aria-current="page"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Home</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Attendance</a><button class="rl-fab" type="button" data-sheet="rl-sheet-create" aria-haspopup="dialog" aria-expanded="false" aria-label="Create"><Icon class="rl-icon"/></button><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Reports</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>More</a></div></nav></div>
```
