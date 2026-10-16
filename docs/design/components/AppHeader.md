# AppHeader

The header of an app screen: a sticky 56px bar with the logo mark, notifications and profile, above a greeting and the branch chip.

You provide the person's first name, the time-of-day greeting, the branch name, the unread count and the initials. The bar stays at the top; the greeting scrolls away. Once it has, add `is-condensed` to `rl-appbar`: the branch chip appears in the bar beside the logo and a hairline separates the bar from the content.

- The branch chip (`rl-chip` with a chevron) opens the branch switcher sheet. Show it only for admins with more than one branch.
- The bell is a 44px `rl-iconbtn`; its `rl-badge` shows the unread count in `ink`, and the button's `aria-label` says the count. Hide the badge at zero.
- The avatar is the person's initials on `ink` and opens their profile.
- Compact form, for a screen where something else must stay pinned (Receptionist Home): add `rl-appbar--scroll` and put the greeting and the branch name in the bar itself (`rl-appbar__who`), in one 56px row. This bar scrolls away; the SearchBar under it is what sticks. A role without a branch switcher sees the branch as plain text.

## Markup (from the design system preview)

```html
<div class="rl-root" style="margin:calc(var(--space-4) * -1)"><header class="rl-appbar" id="rl-appbar"><div class="rl-appbar__in">
  <a class="rl-logo" href="#" aria-label="Rackline home"><Mark/></a>
  <div class="rl-appbar__spacer"><button class="rl-chip rl-appbar__title" type="button" data-sheet="rl-sheet-branch" aria-haspopup="dialog" tabindex="-1">Indiranagar<Icon class="rl-icon rl-icon--xs"/></button></div>
  <button class="rl-iconbtn" type="button" aria-label="Notifications, 5 unread"><Icon class="rl-icon"/><span class="rl-badge" aria-hidden="true">5</span></button>
  <button class="rl-avatar rl-pressable" type="button" aria-label="Profile: Meera Nair">MN</button>
</div></header><div style="padding:0 var(--space-4)"><div class="rl-greeting" id="rl-greeting">
  <h1 class="rl-greeting__hello">Good evening, Meera</h1>
  <button class="rl-chip" type="button" data-sheet="rl-sheet-branch" aria-haspopup="dialog" aria-label="Branch: Indiranagar. Switch branch">Indiranagar<Icon class="rl-icon rl-icon--xs"/></button>
</div></div></div>
```
