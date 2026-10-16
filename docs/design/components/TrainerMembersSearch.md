# TrainerMembersSearch

A search with no match. The empty state reminds the trainer that only their own members are listed, and offers Clear Search.

## Markup (from the design system preview)

```html
<div class="rl-app rl-root" data-ttscreen="members">
<header class="rl-appbar rl-appbar--scroll"><div class="rl-appbar__in">
  <div class="rl-appbar__who"><h1 class="rl-pagetitle">My Members</h1><p class="rl-appbar__branch">Assigned to Arjun Rao • Indiranagar</p></div>
  <button class="rl-avatar rl-pressable" type="button" aria-label="Profile: Arjun Rao">AR</button>
</div></header>
<main class="rl-app__main">
<div class="rl-searchbar rl-searchbar--filters">
  <div class="rl-searchfield"><Icon class="rl-icon rl-icon--sm rl-searchfield__lead"/><input class="rl-searchfield__input" type="search" inputmode="search" enterkeyhint="search" autocomplete="off" autocapitalize="none" autocorrect="off" spellcheck="false" placeholder="Name" aria-label="Search your members by name" value="zoya"><button class="rl-searchfield__btn" type="button" data-search-clear aria-label="Clear search"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <div class="rl-chips rl-chips--scroll" role="radiogroup" aria-label="Filter members"><label class="rl-chipopt"><input type="radio" name="tm-filter" value="all" checked><span>All<small>18</small></span></label><label class="rl-chipopt"><input type="radio" name="tm-filter" value="pt"><span>Personal training<small>14</small></span></label><label class="rl-chipopt"><input type="radio" name="tm-filter" value="attention"><span>Needs attention<small>4</small></span></label></div>
</div>
<section class="rl-section" aria-label="Members">
  <div class="rl-listmeta"><p data-list-count role="status">0 members</p><p>Next session first</p></div>
  <ul class="rl-card rl-mlist rl-mlist--compact" hidden></ul>
  <div class="rl-empty"><span class="rl-empty__icon" aria-hidden="true"><Icon class="rl-icon"/></span><h2 class="rl-empty__title">No member matches</h2><p class="rl-empty__text">Only members assigned to you are listed here.</p><div class="rl-empty__actions"><button class="rl-button rl-button--secondary rl-button--block" type="button" data-empty-clear>Clear Search</button></div></div>
  <button class="rl-button rl-button--secondary rl-button--block rl-listmore" type="button" data-list-more hidden>Load More</button>
</section>
</main>
<nav class="rl-tabbar" aria-label="Main"><div class="rl-tabbar__in"><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Home</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Schedule</a><button class="rl-fab" type="button" data-sheet="tm-create" aria-haspopup="dialog" aria-expanded="false" aria-label="Create"><Icon class="rl-icon"/></button><a class="rl-tab" href="#" aria-current="page"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>Members</a><a class="rl-tab" href="#"><span class="rl-tab__icon"><Icon class="rl-icon"/></span>More</a></div></nav>
<div class="rl-scrim" data-close></div>
<div class="rl-sheet" id="tm-create" role="dialog" aria-modal="true" aria-labelledby="tm-create-title">
  <span class="rl-sheet__grab" aria-hidden="true"></span>
  <div class="rl-sheet__head"><h2 class="rl-section__title" id="tm-create-title">Create</h2><button class="rl-iconbtn rl-iconbtn--plain" type="button" data-close aria-label="Close"><Icon class="rl-icon rl-icon--sm"/></button></div>
  <ul class="rl-sheet__list"><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Log Workout</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Add Note</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Record Measurements</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Assign Plan</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li><li><button class="rl-sheet__item" type="button"><span class="rl-chipicon"><Icon class="rl-icon rl-icon--sm"/></span><span class="rl-sheet__text">Book Session</span><Icon class="rl-icon rl-icon--sm rl-chev"/></button></li></ul>
</div>
<script type="application/json">{"members": [{"id": "RL-2041", "name": "Rahul Kumar", "initials": "RK", "plan": "Premium + PT", "goal": "Fat loss", "used": 8, "next": "Today, 11:00 AM", "flag": "", "pt": true}, {"id": "RL-1990", "name": "Anjali Nair", "initials": "AN", "plan": "Quarterly + PT", "goal": "Strength", "used": 5, "next": "Today, 12:30 PM", "flag": "Measurements due this week", "pt": true}, {"id": "RL-1688", "name": "Karthik Iyer", "initials": "KI", "plan": "Monthly + PT", "goal": "Mobility", "used": 10, "next": "Today, 5:00 PM", "flag": "Membership ends tomorrow", "pt": true}, {"id": "RL-1723", "name": "Farhan Ali", "initials": "FA", "plan": "Monthly + PT", "goal": "Weight loss", "used": 7, "next": "Mon, 11:00 AM", "flag": "Missed 2 sessions this week", "pt": true}, {"id": "RL-1744", "name": "Deepa Menon", "initials": "DM", "plan": "Monthly + PT", "goal": "Weight loss", "used": 2, "next": "Sat, 12:00 PM", "flag": "No check-in for 9 days", "pt": true}, {"id": "RL-1904", "name": "Vikram Shetty", "initials": "VS", "plan": "Quarterly + PT", "goal": "Muscle gain", "used": 6, "next": "Tue, 9:30 AM", "flag": "", "pt": true}, {"id": "RL-2155", "name": "Meenal Shah", "initials": "MS", "plan": "Annual + PT", "goal": "General fitness", "used": 3, "next": "Thu, 6:00 PM", "flag": "", "pt": true}, {"id": "RL-2087", "name": "Tara Bose", "initials": "TB", "plan": "Annual", "goal": "General fitness", "used": null, "next": "Workout plan only", "flag": "", "pt": false}, {"id": "RL-2012", "name": "Aditya Verma", "initials": "AV", "plan": "Quarterly", "goal": "Muscle gain", "used": null, "next": "Workout plan only", "flag": "", "pt": false}], "totals": {"all": 18, "pt": 14, "attention": 4}}</script>
</div>
```
