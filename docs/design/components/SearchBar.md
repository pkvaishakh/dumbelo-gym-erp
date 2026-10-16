# SearchBar

The member search field: 48px tall, a search icon, the placeholder "Search name, phone or member ID", and one 44px button at the right end.

Two forms. On the home screen it is a button dressed as a field (`rl-searchfield__open`) with a QR scan button at the right; tapping it opens the full-screen search. Inside the search it holds the real input (`rl-searchfield__input`, 16px text) with a clear button at the right.

- Wrap the home form in `rl-searchbar` to pin it to the top while the screen scrolls; add `is-stuck` once the header has scrolled away to draw the hairline under it.
- The QR button opens the camera scanner. Give it an `aria-label`.
- Keep the placeholder wording: it tells staff the three things they can search by.

## Markup (from the design system preview)

```html
<div class="rl-root demo" style="display:grid;gap:var(--space-4)"><div class="rl-searchfield"><button class="rl-searchfield__open" type="button" aria-label="Search members"><Icon class="rl-icon rl-icon--sm"/><span>Search name, phone or member ID</span></button><button class="rl-searchfield__btn" type="button" aria-label="Scan a member’s QR code"><Icon class="rl-icon"/></button></div><div class="rl-searchfield"><Icon class="rl-icon rl-icon--sm rl-searchfield__lead"/><input class="rl-searchfield__input" type="search" value="ra" aria-label="Search name, phone or member ID"><button class="rl-searchfield__btn" type="button" aria-label="Clear search"><Icon class="rl-icon rl-icon--sm"/></button></div></div>
```
