# Dumbelo design system

The source of truth for how Dumbelo looks, reads and behaves. The CSS lives in `web/src/styles/`
(`tokens.css`, `dumbelo.css`); this folder explains it. Each component in `components/` has its rules and the
exact markup the CSS expects. Icons in the markup are shown as `<Icon class="…"/>`: in the app use
`<Icon as={LucideIcon} />` from `web/src/components/ui.tsx`.

**Project decisions that override older text below:** the gym records check-in time only. There is no
check-out, no "who is still inside" and no time spent anywhere (ignore any mention of checking out).
Branch opening hours are named sessions (Morning, Afternoon, Evening…) and attendance is grouped by them.
The admin's bottom navigation is Home, Members, Create, Reports, More (Attendance lives in More).
The front desk sees its own branches' cash in hand (what each drawer should hold, today's cash in and out) on
Receptionist Home and in More, and counts it at close (Count Cash). That is not a revenue total; the bank stays
admin-only.

## Components

- [AccountDetails](components/AccountDetails.md): Account Details: the signed-in person's own account.
- [AccountDetailsMember](components/AccountDetailsMember.md): Account Details for a member.
- [AccountDetailsReceptionist](components/AccountDetailsReceptionist.md): Account Details for a receptionist.
- [AccountDetailsWide](components/AccountDetailsWide.md): Account Details from 768px.
- [ActionBar](components/ActionBar.md): The sticky bar at the bottom of a task screen: an optional total and the one button that moves the task on.
- [ActionTile](components/ActionTile.md): A quick-action tile: an icon and a title-case label, at least 64px tall.
- [ActivityList](components/ActivityList.md): The latest things that happened in the gym: an avatar or icon, one line, and a relative time.
- [AddBranch](components/AddBranch.md): Adding a branch.
- [AddBranchDone](components/AddBranchDone.md): The sheet after a branch is added: its name in the title, then the address, the sessions one per line, and the phone to check. Done returns to Branches with the new row; Add Another clears the form.
- [AddBranchErrors](components/AddBranchErrors.md): Add Branch with nothing filled in and a short phone number: each field says what to do, and the first one takes focus. The third session has no name and ends before it starts, so its card is outlined in `danger` with one line saying what to fix.
- [AddExpense](components/AddExpense.md): Add Expense: money the gym spent.
- [AddExpenseDone](components/AddExpenseDone.md): The sheet that confirms an expense.
- [AddExpenseErrors](components/AddExpenseErrors.md): Add Expense after pressing the button with nothing entered.
- [AddMember](components/AddMember.md): Add Member, step 1 of 3: the new member's details.
- [AddMemberDone](components/AddMemberDone.md): The sheet that ends Add Member.
- [AddMemberErrors](components/AddMemberErrors.md): Add Member, step 1, after Continue is tapped with the required fields empty.
- [AddMemberPlan](components/AddMemberPlan.md): Add Member, step 2 of 3: the plan, the start date and any add-on.
- [AddMemberReview](components/AddMemberReview.md): Add Member, step 3 of 3: review before saving.
- [AddMemberWide](components/AddMemberWide.md): Add Member from 768px.
- [AddNoteSheet](components/AddNoteSheet.md): Adding a note to a member, from the ⋮ menu or the Add note link on their profile.
- [AddNoteSheetError](components/AddNoteSheetError.md): Save Note with nothing written: "Write the note first" under the field, and the field keeps focus.
- [AddPlan](components/AddPlan.md): Adding a plan.
- [AddPlanDone](components/AddPlanDone.md): The sheet after a plan is added: its name in the title, then its length, price and where it is sold. Done returns to Plans and Pricing; Add Another clears the form.
- [AddPlanErrors](components/AddPlanErrors.md): Add Plan with no name and no price: both say what to do, and the name takes focus.
- [AddReceptionist](components/AddReceptionist.md): Add Receptionist: a new receptionist under a branch.
- [AddStaffDone](components/AddStaffDone.md): The sheet that confirms a new trainer or receptionist.
- [AddStaffErrors](components/AddStaffErrors.md): Add Trainer after pressing the button with the form incomplete.
- [AddTrainer](components/AddTrainer.md): Add Trainer: a new trainer under a branch.
- [AdminHome](components/AdminHome.md): The Admin Home screen at phone width, shown at its full scroll length: what an owner or manager opens many times a day.
- [AdminHomeBranchSheet](components/AdminHomeBranchSheet.md): Admin Home with the branch switcher open, after tapping the branch chip.
- [AdminHomeCreateSheet](components/AdminHomeCreateSheet.md): Admin Home with the create sheet open, after tapping the "+" in the bottom navigation.
- [AdminHomeLoading](components/AdminHomeLoading.md): Admin Home while the overview figures load.
- [AdminHomeWide](components/AdminHomeWide.md): Admin Home from 768px: the same screen in a centred 960px container, with no sidebar.
- [AdminMore](components/AdminMore.md): The Admin's More tab: everything that is not one of the four tabs.
- [AmountField](components/AmountField.md): A large field for typing an amount of money, with the currency sign fixed in front.
- [AppHeader](components/AppHeader.md): The header of an app screen: a sticky 56px bar with the logo mark, notifications and profile, above a greeting and the branch chip.
- [AssignPlanSheet](components/AssignPlanSheet.md): A trainer assigning a workout plan: the plans as ChoiceCards with how many workouts a week, and when it starts. Saving changes the Plan line on the Training card.
- [Attendance](components/Attendance.md): The Attendance tab as the front desk sees it, at phone width and full scroll length.
- [AttendanceByTime](components/AttendanceByTime.md): Attendance filtered by session. The chips under Check-ins are All, then one per session of the branch's opening hours (set on Add or Edit Branch), each with its count: for Indiranagar, Morning (5 to 10 AM), Afternoon (12 to 4 PM) and Evening (5 to 10 PM). The counts always add up to All.
- [AttendanceCalendar](components/AttendanceCalendar.md): Four weeks of check-ins as a calendar of dots.
- [AttendanceCheckedIn](components/AttendanceCheckedIn.md): The confirmation after a check-in from the Attendance tab.
- [AttendanceEmpty](components/AttendanceEmpty.md): Today before anyone has checked in.
- [AttendanceLoading](components/AttendanceLoading.md): Attendance while the day's data loads.
- [AttendancePastDay](components/AttendancePastDay.md): An earlier day, chosen on the DayStrip.
- [AttendanceRemove](components/AttendanceRemove.md): Confirming the removal of a check-in.
- [AttendanceSearch](components/AttendanceSearch.md): Checking a member in from the Attendance tab.
- [AttendanceStaff](components/AttendanceStaff.md): The Staff side of Attendance: the trainers and receptionists of this branch, for the day chosen in the DayStrip.
- [AttendanceStaffShift](components/AttendanceStaffShift.md): One person's day on Attendance, opened from their row on the Staff side.
- [AttendanceVisit](components/AttendanceVisit.md): A visit opened from its row.
- [AttendanceWide](components/AttendanceWide.md): Attendance from 768px.
- [AttentionList](components/AttentionList.md): The Needs attention card: up to three rows, each a count, a label, a detail line and a chevron.
- [BarList](components/BarList.md): A short ranked comparison: one bar per row, with the name on the left and the value in words on the right.
- [Barbell](components/Barbell.md): The brand's one picture: a loaded barbell end whose bar runs off the right edge.
- [BookSession](components/BookSession.md): A member booking a session. Shown for personal training on a Monday.
- [BookSessionClass](components/BookSessionClass.md): Booking a class: each class that day as a ChoiceCard with its time, coach and spots left.
- [BookSessionDayOff](components/BookSessionDayOff.md): Wednesday, the trainer's day off: no times, and one line asking for another day.
- [BookSessionDone](components/BookSessionDone.md): The sheet after booking: when, with whom, where, and the sessions left in the pack. Done returns to Member Home.
- [BookSessionErrors](components/BookSessionErrors.md): Book Session with no time picked: "Choose a time" under the times, and the first free time takes focus.
- [BottomNav](components/BottomNav.md): The fixed bottom navigation: Home, Attendance, a raised create button, Reports, More (the admin's bar).
- [BranchSheet](components/BranchSheet.md): One branch, opened from its row.
- [Branches](components/Branches.md): Every branch of the gym, for owners and managers.
- [Button](components/Button.md): The action button: 56px tall, `radius-md`, `ink` with `on-ink` text.
- [ChangePassword](components/ChangePassword.md): Change Password, from Account Details.
- [ChangePasswordErrors](components/ChangePasswordErrors.md): Change Password with both fields wrong.
- [CheckInCode](components/CheckInCode.md): A member's QR code for checking in, with their name, member ID and plan under it.
- [CheckInSheet](components/CheckInSheet.md): The sheet that answers a check-in: confirmed, or blocked.
- [CheckinsByShift](components/CheckinsByShift.md): Who checked in today, split by shift: one row each for members, trainers and receptionists, and one column each for morning, afternoon and evening.
- [ChipSelect](components/ChipSelect.md): One option from a few single words, as a row of chips.
- [ChoiceCard](components/ChoiceCard.md): One option in a choice, as a card: a mark, a name, a line of detail and, where there is one, a price.
- [CodeField](components/CodeField.md): A one-time code as six cells that fill as it is typed.
- [CollectPayment](components/CollectPayment.md): Collect Payment: who is paying, what for, how much, and how.
- [CollectPaymentDone](components/CollectPaymentDone.md): The receipt sheet that ends Collect Payment.
- [CollectPaymentPart](components/CollectPaymentPart.md): Collect Payment with a part payment.
- [Cover](components/Cover.md): 
- [DayStrip](components/DayStrip.md): Seven days in a row, one selected. It chooses the day a screen is showing.
- [DetailList](components/DetailList.md): Facts about one record as labelled rows: an icon, a small label, and the value under it.
- [EditAccount](components/EditAccount.md): Edit Details: changing your own name, mobile number or email.
- [EditAccountErrors](components/EditAccountErrors.md): Edit Details with all three fields wrong.
- [EditAccountSaved](components/EditAccountSaved.md): The sheet that confirms saved account details.
- [EditBranch](components/EditBranch.md): Editing a branch: Add Branch with the branch's values filled in, the title "Edit Branch" and the button "Save Changes". It ends in a sheet that says "Changes saved".
- [EditExpense](components/EditExpense.md): Edit Expense: the Add Expense task with an expense already filled in.
- [EditMemberSheet](components/EditMemberSheet.md): Editing a member's contact details: full name, mobile number (with `+91` fixed in front) and email, which is optional. Saving updates the profile's name, Details, and the number behind Call and Message.
- [EditPlan](components/EditPlan.md): Editing a plan, shown for Premium: Add Plan with its values filled in, the title "Edit Plan", the price note visible, and the button "Save Changes".
- [EditStaff](components/EditStaff.md): Edit Trainer: the Add Trainer task with a person already filled in.
- [EmptyState](components/EmptyState.md): What a list shows when there is nothing to list: an icon, one line saying why, one line saying what to try, and the way out.
- [ExerciseEntry](components/ExerciseEntry.md): One exercise being written down: its name, then sets, reps and weight side by side.
- [ExerciseList](components/ExerciseList.md): The exercises of a workout as a numbered list: name, sets and reps, and the load.
- [ExpenseDelete](components/ExpenseDelete.md): Confirming a delete.
- [ExpenseDetail](components/ExpenseDetail.md): One expense, opened from its row.
- [Expenses](components/Expenses.md): Expenses for one branch this month.
- [ExpensesFiltered](components/ExpensesFiltered.md): Expenses filtered to one category.
- [FilterChips](components/FilterChips.md): A row of chips that filters a list by one value, each with its count.
- [ForgotPassword](components/ForgotPassword.md): Forgot password, step 1: where to send the code.
- [ForgotPasswordCode](components/ForgotPasswordCode.md): Forgot password, step 2: the 6-digit code.
- [ForgotPasswordCodeError](components/ForgotPasswordCodeError.md): Forgot password, step 2, after a wrong code.
- [ForgotPasswordDone](components/ForgotPasswordDone.md): Forgot password, step 4: done.
- [ForgotPasswordNew](components/ForgotPasswordNew.md): Forgot password, step 3: the new password, here with one that is too short.
- [FreezeSheet](components/FreezeSheet.md): Freezing a membership: a reason (Travel, Illness or injury, Exams, Other) and how long (1, 2 or 4 weeks). One line spells out the result before anything is saved: "Check-in is paused from today until 19 Oct. The plan will now end on 17 Mar 2027."
- [GoalCard](components/GoalCard.md): The member's goal and how far along it they are.
- [LiveSession](components/LiveSession.md): A personal-training session in progress, as the trainer runs it.
- [LiveSessionComplete](components/LiveSessionComplete.md): The sheet that ends a live session.
- [LiveSessionLoad](components/LiveSessionLoad.md): The live session with the Change load sheet open.
- [LogWorkout](components/LogWorkout.md): Log Workout: a workout written down for a member after the fact.
- [LogWorkoutDone](components/LogWorkoutDone.md): The sheet that confirms a logged workout.
- [LogWorkoutErrors](components/LogWorkoutErrors.md): Log Workout after Save Workout with entries missing.
- [LoginScreen](components/LoginScreen.md): The sign-in screen shared by every role, at phone width; the reference for every auth screen.
- [LoginScreenDesktop](components/LoginScreenDesktop.md): The sign-in screen on a desktop: the phone column on the right, an `ink` brand panel on the left.
- [LoginScreenTablet](components/LoginScreenTablet.md): The sign-in screen on a tablet: the same phone column, centred at `column-max`.
- [Logo](components/Logo.md): The Dumbelo lockup: the plate mark and the name.
- [MealList](components/MealList.md): The day's meals, each with a tick to mark it eaten.
- [MeasurementList](components/MeasurementList.md): Body measurements as a list: the part, the latest value and the change since the start.
- [MemberCard](components/MemberCard.md): A compact card for one member: photo, name, status badge and their last check-in time.
- [MemberCheckInCode](components/MemberCheckInCode.md): The member's check-in code, open as a sheet over More.
- [MemberDiet](components/MemberDiet.md): The member's Diet tab, at phone width and full scroll length.
- [MemberDietDone](components/MemberDietDone.md): The Diet tab once every meal is ticked.
- [MemberDietWide](components/MemberDietWide.md): The Diet tab from 768px.
- [MemberHome](components/MemberHome.md): The Member Home screen at phone width, shown at its full scroll length: what a member sees when they open the gym's app.
- [MemberHomeWide](components/MemberHomeWide.md): Member Home from 768px: the same screen in a centred 960px container, with no sidebar.
- [MemberMore](components/MemberMore.md): The member's More tab.
- [MemberPickerSheet](components/MemberPickerSheet.md): Which member? When a trainer starts Add Note, Record Measurements or Assign Plan from Trainer Home or the create sheet, there is no member yet, so this sheet lists only their own members first. Choosing one opens the action for them.
- [MemberProfile](components/MemberProfile.md): The Member Profile as the front desk and admins see it, at phone width and full scroll length.
- [MemberProfileActions](components/MemberProfileActions.md): The Member Profile with the more-actions sheet open, after tapping the three dots in the top bar.
- [MemberProfileExpired](components/MemberProfileExpired.md): The Member Profile for a member whose membership has expired.
- [MemberProfileExpiring](components/MemberProfileExpiring.md): The Member Profile for any member, filled from their record. Shown for a membership that ends today.
- [MemberProfileFrozen](components/MemberProfileFrozen.md): A frozen membership. Check In is replaced by one line saying check-in is paused, with Unfreeze and Collect Payment. The card reads "Frozen until 20 Oct", and Attendance says there are no check-ins while frozen.
- [MemberProfileNoTrainer](components/MemberProfileNoTrainer.md): A member without personal training: no training bar on the card, no next session, and Trainer reads "None assigned".
- [MemberProfilePaymentDue](components/MemberProfilePaymentDue.md): A member with a payment due. The Payments card leads with the amount due in `attention`, and the unpaid period is listed as "Unpaid" rather than with an amount paid. Collect Payment opens with that amount.
- [MemberProfileTrainer](components/MemberProfileTrainer.md): The Member Profile as the member's trainer sees it.
- [MemberProfileTrainerAttention](components/MemberProfileTrainerAttention.md): The trainer's view of one of their members who needs attention. Log Workout and Schedule in place of Check In and payments; the Training card ends with the reason in `attention` ("Missed 2 sessions this week"). No payments, email or prices.
- [MemberProfileWide](components/MemberProfileWide.md): The Member Profile from 768px: the same screen in a centred 960px container.
- [MemberProgress](components/MemberProgress.md): The member's Progress tab, at phone width and full scroll length.
- [MemberProgressLogWeight](components/MemberProgressLogWeight.md): The Progress tab with the Log weight sheet open.
- [MemberProgressWide](components/MemberProgressWide.md): The Progress tab from 768px.
- [MemberRenewal](components/MemberRenewal.md): Member Home with the membership card in its renewal state, five days before the plan ends.
- [MemberRow](components/MemberRow.md): One member in a list: photo, name, member ID and plan, status badge, and the date that matters.
- [MemberWaterSheet](components/MemberWaterSheet.md): Member Home with the water quick-log sheet open, after tapping the "+" beside Water.
- [MemberWorkout](components/MemberWorkout.md): The member's Workout tab before today's workout, at phone width and full scroll length.
- [MemberWorkoutActive](components/MemberWorkoutActive.md): A workout in progress: every exercise with its sets, ticked off as they are done.
- [MemberWorkoutComplete](components/MemberWorkoutComplete.md): The sheet that ends a workout.
- [MemberWorkoutDone](components/MemberWorkoutDone.md): Today's plan and today's progress after the workout is finished.
- [MemberWorkoutFinished](components/MemberWorkoutFinished.md): The Workout tab after today's workout.
- [MemberWorkoutWide](components/MemberWorkoutWide.md): The Workout tab from 768px.
- [MembersList](components/MembersList.md): The Members list as the front desk and admins see it, at phone width and full scroll length.
- [MembersListEmpty](components/MembersListEmpty.md): The Members list when a search matches no one.
- [MembersListFiltered](components/MembersListFiltered.md): The Members list filtered to Expiring.
- [MembersListLoading](components/MembersListLoading.md): The Members list while the first page loads.
- [MembersListSearch](components/MembersListSearch.md): The Members list while searching, "ra" typed and three matches.
- [MembersListSort](components/MembersListSort.md): The Members list with the Sort and filter sheet open.
- [MembersListWide](components/MembersListWide.md): The Members list from 768px.
- [MembershipCard](components/MembershipCard.md): The member's membership at a glance: status, plan, days remaining, and a thin bar for the plan period.
- [MoreWide](components/MoreWide.md): More from 768px, shown for the front desk.
- [MyTaskSheet](components/MyTaskSheet.md): A receptionist opens a task that is still To do: Start Task first, Mark Done as the secondary button, and the box to post an update. See TaskSheet.
- [MyTasks](components/MyTasks.md): A trainer's or receptionist's own tasks, from More → My Tasks. Shown for Alex D’Souza at the front desk.
- [MyTasksTrainer](components/MyTasksTrainer.md): My Tasks for a trainer, Arjun Rao: one task in progress with an update already posted. See MyTasks.
- [NewSubscription](components/NewSubscription.md): Selling a plan to someone who is already a member: renewing, upgrading or adding personal training.
- [NewSubscriptionErrors](components/NewSubscriptionErrors.md): Continue to Payment with no member: "Choose a member" under the search field, which turns `danger` and takes focus.
- [NewSubscriptionMember](components/NewSubscriptionMember.md): A member chosen: their card with their current plan and end date, and Change. Starting when the current plan ends is the default, so no days are lost.
- [NewTask](components/NewTask.md): Giving a trainer or receptionist a task. A task screen: close, the title (New Task or Edit Task), the form, and Assign Task in the action bar.
- [NewTaskDone](components/NewTaskDone.md): The sheet after a task is assigned: "Task assigned", who has it and when it is due. Done and Assign Another.
- [NewTaskErrors](components/NewTaskErrors.md): New Task with nothing filled in: the task and the person each say what is missing, and the first one takes focus.
- [NextSession](components/NextSession.md): The hero card of Trainer Home: who the trainer is about to train, and the one button that starts it.
- [Notifications](components/Notifications.md): What the bell on a home screen opens. Shown for an admin.
- [NotificationsAllRead](components/NotificationsAllRead.md): After Mark All as Read: no dots, the subtitle says "All read", and the bell on the home screen has no badge.
- [NotificationsMember](components/NotificationsMember.md): A member's notifications, the same as the reminders on Member Home: a new workout plan, measurements to record, next week's diet plan, the membership ending. Each leads to the matching tab.
- [NotificationsReceptionist](components/NotificationsReceptionist.md): The front desk's notifications: a booked member who hasn't arrived, a member who checked in with money due, a membership ending today. Each leads to Attendance, Collect Payment or the filtered Members list.
- [NotificationsTrainer](components/NotificationsTrainer.md): A trainer's notifications, about their own members only: who checked in for a session, who missed sessions, whose measurements are due.
- [NutritionSummary](components/NutritionSummary.md): The day's eating in one card: a large ring of calories eaten against the target, and a bar for each macro.
- [PerformanceChart](components/PerformanceChart.md): A compact chart card: a measure toggle, a period selector, a headline total with its change, and a 180px chart.
- [PlanSheet](components/PlanSheet.md): One plan, opened from its row.
- [PlanStopSelling](components/PlanStopSelling.md): Confirming Stop Selling. A sheet that must be answered: it says the plan will not be offered in Add Member or at renewal, and that the members on it keep it until it ends. "Stop Selling" in `danger`, and "Keep Selling". After stopping, the plan moves to No longer sold.
- [PlansPricing](components/PlansPricing.md): Membership plans and add-ons, with their prices.
- [PlansPricingWide](components/PlansPricingWide.md): Plans and Pricing from 768px. The groups stay in one column of rows, centred in the container; the rows keep their two-line layout.
- [PrivacyPolicy](components/PrivacyPolicy.md): The Privacy Policy, the same page switched to Privacy Policy: what the gym keeps, why, who can see it, how long, and the member's choices. Sample text to replace.
- [ProfileHeader](components/ProfileHeader.md): The top of a profile: a large photo, the name, the member ID with a status badge, and the actions for this member.
- [ProgressGrid](components/ProgressGrid.md): Today's progress in one compact card: four equal items, each a ring with an icon and a value in words.
- [ReceptionCheckInBlocked](components/ReceptionCheckInBlocked.md): The sheet shown when check-in is refused because the membership has expired.
- [ReceptionCheckedIn](components/ReceptionCheckedIn.md): The confirmation after a successful check-in: a `volt` check, "Checked in at 8:41 AM", and the member's card.
- [ReceptionCreateSheet](components/ReceptionCreateSheet.md): Receptionist Home with the create sheet open, after tapping the "+" in the bottom navigation.
- [ReceptionHome](components/ReceptionHome.md): The Receptionist Home screen at phone width, shown at its full scroll length: what the front desk uses through a busy shift.
- [ReceptionHomeWide](components/ReceptionHomeWide.md): Receptionist Home from 768px: the same screen in a centred 960px container, with no sidebar.
- [ReceptionMore](components/ReceptionMore.md): The front desk's More tab: what is not on the other four tabs.
- [ReceptionSearch](components/ReceptionSearch.md): Receptionist Home with the full-screen search open, "ra" typed and three results.
- [RecordMeasurementsSheet](components/RecordMeasurementsSheet.md): A trainer recording measurements: weight, waist, chest and arms side by side, any of them. Saving adds "Measured today: 82.5 kg, waist 91 cm" to the Training card. At least one is needed.
- [ReminderList](components/ReminderList.md): Up to three reminders: an icon, one line, and a relative time.
- [RenewalReminderSent](components/RenewalReminderSent.md): After sending: a `volt` tick, "Reminder sent", and the channels and number it went to. Done closes the sheet.
- [RenewalReminderSheet](components/RenewalReminderSheet.md): Sending a renewal reminder. The exact message the member will get, written to them by first name with their plan and end date, and the channels to send it on (the gym's defaults from Settings are picked). At least one channel must be picked.
- [Reports](components/Reports.md): The Admin's Reports tab for the last 7 days, at phone width and full scroll length.
- [Reports30Days](components/Reports30Days.md): Reports for the last 30 days.
- [Reports3Months](components/Reports3Months.md): Reports for the last 3 months.
- [ReportsWide](components/ReportsWide.md): Reports from 768px.
- [RequestAccess](components/RequestAccess.md): Request access: how someone without an account asks their gym for one.
- [RequestAccessDesktop](components/RequestAccessDesktop.md): Request access at 1280 wide.
- [RequestAccessErrors](components/RequestAccessErrors.md): Request access after pressing the button with the form incomplete.
- [RequestAccessSent](components/RequestAccessSent.md): Request access, sent.
- [ScheduleList](components/ScheduleList.md): The next sessions today: time, a type tag, a title, and who is involved.
- [SearchBar](components/SearchBar.md): The member search field: 48px tall, a search icon, the placeholder "Search name, phone or member ID", and one 44px button at the right end.
- [SearchResult](components/SearchResult.md): One member in the search results: photo, name, member ID, status badge and an inline Check In button.
- [SegmentedControl](components/SegmentedControl.md): A small set of exclusive choices: a `surface` track with the chosen option on a `ground` pill.
- [SelectField](components/SelectField.md): A choice from a list too long for chips, as a native select in the TextField's shell.
- [SessionCard](components/SessionCard.md): The member's next booked session: time, type and length, a countdown, the trainer and the focus.
- [SetTracker](components/SetTracker.md): One exercise during a workout, with a chip to tick for each set.
- [Settings](components/Settings.md): The gym's own rules, for owners and managers.
- [SettingsGracePeriod](components/SettingsGracePeriod.md): Picking the grace period: a sheet with three options, each with one line saying what happens at the door. The current one has a `volt` tick. Tapping one applies it and closes the sheet.
- [SettingsReminderChannels](components/SettingsReminderChannels.md): Picking reminder channels: chips for SMS, WhatsApp and Email, any number, then Done. With none picked, Done says "Choose at least one".
- [SettingsWide](components/SettingsWide.md): Settings from 768px: Gym and Check-in on the left, Reminders and Payments on the right.
- [Sheet](components/Sheet.md): A bottom sheet: a panel that slides up over a `scrim` for a short list of choices.
- [SignedInDevices](components/SignedInDevices.md): Every device signed in to the person's account.
- [SignedInDevicesConfirm](components/SignedInDevicesConfirm.md): Confirming a sign-out: names the device, says it will need the password to sign in again, then "Sign Out" in `danger` and "Cancel". For all other devices at once the title and button say so.
- [SignedInDevicesNone](components/SignedInDevicesNone.md): Only this phone is signed in: the other devices list is replaced by one line, and Sign Out All Other Devices is gone.
- [StaffDeactivate](components/StaffDeactivate.md): Confirming a deactivation.
- [StaffList](components/StaffList.md): Staff: every trainer and receptionist the admin manages, grouped under their branch.
- [StaffListReceptionists](components/StaffListReceptionists.md): Staff filtered to Receptionists.
- [StaffListWide](components/StaffListWide.md): Staff from 768px.
- [StaffMoveBranch](components/StaffMoveBranch.md): Moving a person to another branch, from their Staff Profile.
- [StaffProfile](components/StaffProfile.md): Staff Profile: one trainer, and everything the admin can do about them.
- [StaffProfileDeactivated](components/StaffProfileDeactivated.md): Staff Profile for a deactivated account.
- [StaffProfileReceptionist](components/StaffProfileReceptionist.md): Staff Profile for a receptionist.
- [StaffProfileWide](components/StaffProfileWide.md): Staff Profile from 768px.
- [StatCard](components/StatCard.md): One figure for today: an icon, a large number, a short label and a trend.
- [StatusBadge](components/StatusBadge.md): A membership's status as a small pill: a coloured dot and the word.
- [StreakCard](components/StreakCard.md): The attendance streak: a headline, one warm sentence, and the week from Monday to Sunday.
- [Switch](components/Switch.md): A switch for a setting that takes effect the moment it is flipped.
- [TaskDelete](components/TaskDelete.md): Deleting a task asks first: the task's title, and that it disappears for the person too, with its updates. Delete Task (`danger`) or Keep It, which goes back to the task.
- [TaskSheet](components/TaskSheet.md): One task, opened from its row. The admin and the person doing it see the same sheet, with different buttons.
- [Tasks](components/Tasks.md): The admin's Tasks: work given to trainers and receptionists, and how far each has got. Opened from More → Tasks, or from Assign Task in the create sheet.
- [TasksDone](components/TasksDone.md): The admin's Tasks filtered to Done, latest first. Each row says "Done" in place of the due date.
- [TasksEmpty](components/TasksEmpty.md): Tasks before any have been set: the EmptyState says what tasks are for, under New Task. A filter that leaves nothing says "Nothing here" instead.
- [TermsOfService](components/TermsOfService.md): The Terms of Service, opened from the sign-in screen.
- [TextArea](components/TextArea.md): A field for a few lines of free text, such as a note.
- [TextField](components/TextField.md): A labelled text input, 56px tall, with an optional show/hide button and an error line.
- [TodayPlan](components/TodayPlan.md): The two things to do today, side by side: the workout and the diet.
- [TrainerCreateSheet](components/TrainerCreateSheet.md): Trainer Home with the create sheet open, after tapping the "+" in the bottom navigation.
- [TrainerHome](components/TrainerHome.md): The Trainer Home screen at phone width, shown at its full scroll length: what a trainer opens between sessions on the gym floor.
- [TrainerHomeWide](components/TrainerHomeWide.md): Trainer Home from 768px: the same screen in a centred 960px container, with no sidebar.
- [TrainerMembers](components/TrainerMembers.md): The trainer's Members tab: only the members assigned to them.
- [TrainerMembersAttention](components/TrainerMembersAttention.md): My Members filtered to Needs attention: the four members Trainer Home counts, each with the reason in `attention`.
- [TrainerMembersSearch](components/TrainerMembersSearch.md): A search with no match. The empty state reminds the trainer that only their own members are listed, and offers Clear Search.
- [TrainerMore](components/TrainerMore.md): The trainer's More tab.
- [TrainerProfileMenu](components/TrainerProfileMenu.md): Trainer Home with the profile menu open, after tapping the avatar.
- [TrainerSchedule](components/TrainerSchedule.md): The trainer's Schedule tab: their week, one day at a time.
- [TrainerScheduleDay](components/TrainerScheduleDay.md): Another day on the trainer's schedule, shown for Monday: no done or next states, just what is booked.
- [TrainerScheduleDayOff](components/TrainerScheduleDayOff.md): The trainer's day off: an empty state that says so and that members cannot book them that day.
- [TrainerScheduleItem](components/TrainerScheduleItem.md): One session, opened from the schedule. A DetailList of when, focus, length and status, then what can be done about it:
- [TrainerScheduleWide](components/TrainerScheduleWide.md): The trainer's schedule from 768px. One column, centred; the DayStrip stops at `column-max`.
- [TrainerSessionLive](components/TrainerSessionLive.md): Trainer Home once a session has started.
- [UnfreezeSheet](components/UnfreezeSheet.md): Ending a freeze. A sheet that must be answered: check-in works again from today and the unused days stay on the end of the plan. "Unfreeze" and "Keep Frozen".
- [VisitRow](components/VisitRow.md): One check-in in the day's attendance: who, and when they checked in.
- [VisitSheet](components/VisitSheet.md): The sheet for one check-in: the member, when they checked in, and what can be done about it.
- [WeightCard](components/WeightCard.md): Recent progress: current weight as the large figure, the change since the start, and a small line chart of the last eight weeks.
- [WorkoutWeek](components/WorkoutWeek.md): The week's workouts at a glance: how many are done, and a dot for each day.

---

Dumbelo is a gym ERP app with one sign-in for every role: owners, managers, front desk, trainers and anyone else with an account. People use it on their phones, standing up, often one-handed. Build every screen as a phone app first. A tablet or desktop gets the same phone layout widened, never a desktop ERP with a sidebar.

There are two kinds of screen. Auth screens (sign-in, and the Forgot password and Request access flows behind it) sit on `ground` with no cards. App screens sit on a `surface` canvas with `ground` cards, a header and a fixed bottom navigation. Admins also manage the gym itself: the staff under each branch and what each branch spends. Each role gets its own home: Admin Home for owners and managers, Receptionist Home for the front desk, Trainer Home for trainers, Member Home for the gym's members.

Behind the homes are detail screens, such as the Member Profile, the Staff Profile and Account Details: a top bar with a back arrow and a title in place of the greeting, an identity block, the actions for that record, then cards. The bottom navigation stays, with the tab the record belongs to marked as current.

List screens (Members) are the other tabs of the bottom navigation; for the admin, Attendance takes the Members tab's place and Members moves into More. A title with the branch under it takes the place of the greeting, then a search field and a row of filter chips that stay pinned while the list scrolls, a line saying how many are shown, and one row per record in a single card. A row is a link to the record and carries no buttons. When nothing matches, an empty state says why and offers the way out.

Tasks are how the admin gives work to trainers and receptionists and follows it: the admin assigns a task with a due date from More or the create sheet; the person sees it in My Tasks, starts it, posts updates and marks it done; the admin sees each step and can reopen, edit or delete it.

Attendance is the front desk's third tab and shows one day at a time. The gym records only who checked in and when; nothing on any screen says who is still inside, when anyone left or how long they stayed. A strip of the last seven days takes the place of the search field and stays pinned; under it are the Check In Member action, the day's two figures, check-ins by hour, and the day's visits with the newest first. Today can be changed (check in, check out, remove a wrong check-in). Earlier days are a record and offer no actions.

A trainer's other tabs are Schedule (their own week, one day at a time, today matching Trainer Home; a member's booking appears there at once, and the trainer marks sessions attended from it) and My Members (only the members assigned to them). Every role's last tab is More: what is not on the other tabs, then Account Details and Sign Out. The front desk's starts with shortcuts into filtered member lists and their shift; the trainer's with their work; the member's with their check-in code and membership. Admins' More also holds Staff, Expenses, Branches, Plans and Pricing, and Settings (the gym's rules for check-in, reminders and payments, applied at once at every branch). A plan or a branch is never deleted: a plan is stopped, so the members on it keep it until it ends.

Task screens (Add Member, Collect Payment, Log Workout, a live session, Add Trainer, Add Receptionist, Add Expense) are where staff enter something. They open over the app: a top bar with a close button and the task's name, a form in one column, and a sticky action bar at the bottom in place of the bottom navigation. A long task is split into steps of one subject each, with "Step 1 of 3" in the top bar and a bar under it. Every task ends in a sheet that says what happened and offers the next step.

Smaller actions on a member (a note, a freeze, a reminder, an edit, measurements, a plan) are sheets over their profile, not task screens. Each sheet opens with the member's card, says the result before it is saved, and changes the profile in place.

The member app is the same brand turned up, by four means only: larger numbers (`figure`), progress rings and bars, more of the accent on the main cards, and warmer copy. It adds no colours and no fonts. Its other tabs (Workout, Diet, Progress) each take one subject from Member Home and give it the whole screen, with the same figures. A workout in progress is a task screen: sets are ticked off one tap at a time, and it ends in a summary sheet.

## Voice and copy

- Write to one person as "you", whatever their role. Plain verbs, short lines: "Sign in to manage your gym", "Forgot password?", "Request access".
- Sign-in is shared by every role. Never name a role on it or ask the person to pick one: the account decides where they land.
- Action labels are title case: "Sign In", "Add Member", "Collect Payment". Everything else is sentence case: "Needs attention", "Today's schedule".
- A button says what happens and keeps that word through the flow: "Sign In" → "Signing in…" → "Signed in".
- Errors say what to do, without apology: "Enter your mobile number or email". Never "Invalid input".
- On the auth flows the heading names the step in plain words: "Reset your password", "Enter the code", "Choose a new password", "Request access". The line under it says what will happen or where something was sent.
- The screen heading is a short greeting: "Let's get moving" on sign-in, "Good evening, Meera" on Admin Home, "Good morning, Alex 👋" on Receptionist Home, "Good morning, Arjun 👋" on Trainer Home, "Good morning, Rahul 👋" on Member Home. The greeting must agree with the clock. Emoji appear in two places only: the wave after a home greeting, and the flame on the member's streak card. None in buttons, labels, badges, errors or legal text.
- To a member, write warmly and in the second person, about what they did and what comes next: "You've checked in 8 days in a row. Check in today to make it 9." Motivational but adult: no exclamation marks, no badges, no confetti.
- Say "gym", "staff", "members", "classes". Never "ERP", "tenant" or "portal" in the interface.
- Money uses the gym's currency with its own grouping: "₹3,05,340". Compact forms only on chart axes: "₹30k", "₹2L".
- A trend is an arrow plus signed text naming what it compares to: "+12% vs yesterday". Never colour alone.
- Timestamps are relative and short: "12 min ago". Schedule times are clock times: "6:30 PM".
- The same session reads the same to everyone: the trainer's next session and the member's upcoming session share one time, length, workout and weight, and the trainer's live session lists the same exercises, sets and loads as the member's Workout tab.
- A figure shown twice must match: the count on a stat card equals the count in Needs attention and the last bar of the chart. People shown twice must match too: the check-ins in Today's activity are the first cards in Recent members, with the same times.
- One record, different views: the Member Profile shows payments to the front desk and admins, and progress and training to trainers. Never show a role a section it cannot act on.
- Trainers and receptionists belong to one branch each. Only admins see the Staff list, add or move staff, or see and add expenses.
- A role sees only what it may act on. Receptionist Home shows no revenue totals, reports, staff data or branch switcher; a single payment in the activity feed is fine. Trainer Home shows only that trainer's own sessions and members: no payments, revenue, other trainers' data or branch switcher. Member Home shows only that member's own data and no staff features. Attendance shows who came and when, never what they paid or owe.
- The bell on every home screen opens that role's Notifications. Its badge is the unread count there, and each notification is one sentence the reader can act on.
- Member Home has three primary actions and no more: Start Workout, View Diet, Book Session. Everything else is a text link, a small secondary button, or lives in a bottom sheet.

## Colour

- Auth screens are `ground` (white). App screens are `surface` with `ground` cards. Text is `ink`; secondary text is `ink-muted`. Both read on `ground`, `surface`, `volt-soft` and `attention-soft`.
- `volt` is the only accent and it is always a fill, with `ink` on or beside it: the inner plate of the barbell, the logo glyph, the highlighter under a link, the focus halo, the signed-in button, the create button in the bottom navigation, today's bar in a chart, the Now tag. On an `ink` fill it may colour an icon. Never set text or an icon in `volt` on `ground`: it does not read.
- The primary action is `ink` with `on-ink` text: the Sign In button, the primary action tiles, the Check In button on a search result, the first action on a profile. Secondary actions are `ground` or `surface` with a 1px `field-line` edge.
- One action per screen may be `volt` with `ink` text when it is the reason the screen exists: the Check In Member tile on Receptionist Home, the Start Session button on Trainer Home, the Start Workout button on Member Home and on the Workout tab.
- On Member Home the accent is used more freely: the workout card is `ink` with a `volt` button, the streak card is `volt-soft`, and every progress ring and bar fills in `volt`. A progress ring or bar always sits beside its value in words; the fill never carries the meaning alone.
- Something a member has ticked off (a set, a meal, a day's workout, a check-in) is a `volt` fill with an `ink` tick or number on it.
- `volt-soft` marks the current thing: the session happening now, the active tab.
- `attention-soft` fills the Needs attention card and nothing else; its counts are `attention`. It is a calm prompt, not an alarm.
- `danger` marks an error, an expired membership or a deactivated account, and always comes with a written message or label; `danger-soft` is its tint. Do not use it for counts or trends.
- A destructive action (deactivate, delete) is a `danger` outline button that opens a sheet which must be answered. Only that sheet's confirming button is filled `danger`, and it sits above a plain button that backs out.
- The membership card follows the status: `ground` when Active, `attention-soft` when Expiring, `danger-soft` when Expired.
- Membership status is a StatusBadge, the same everywhere: Active (`volt-soft`), Expiring (`attention-soft`), Expired (`danger-soft`), Frozen (`surface`), Payment due (outlined in `attention`). Always a colour and the word, never the colour alone.
- On the desktop sign-in panel the ground is `ink`, text is `on-ink`, and the one `volt` plate stays `volt`.

## Type

- One family, Archivo (`--font-sans`), loaded from `fonts/Archivo-Variable.woff2`.
- Set `display`, `headline` and `title` wide with `font-variation-settings: "wdth" 112`; everything else at normal width.
- Auth screens: one `display` heading with one `body-lg` line under it in `ink-muted`.
- App screens use three styles for content: `metric` for every large number, `title` for every section title, `body-sm` for row text (with `label` for the emphasised part and `caption` for the second line). The greeting is `headline`. Tags, tab labels, trends and chart axes are `micro`.
- Inputs use `body` (16px) and never smaller, so iOS does not zoom on focus.
- Left-align headings, labels, fields and rows. Only the sign-in footer and tab labels are centred.

## Layout and touch

- Design at 390px wide; everything must work from 360 to 430px.
- Nothing tappable is smaller than `touch-min` (44px) in either direction. Fields and buttons are `control-height` (56px) tall.
- Auth screens: one column on `ground`, gutter `space-6`, in this order: logo, barbell, heading, form, footer. No card around the form. A flow behind sign-in adds a back arrow before the logo and moves through its steps on the same screen, one heading and one form at a time; its last step is a `volt` tick, a heading, one line and a single button back to sign-in. From 600px centre the column at `column-max`; from 1024px add the `ink` brand panel on the left.
- App screens: gutter `space-4`, `space-6` between sections, `space-3` between cards and tiles. Order on Admin Home: header, overview, quick actions, needs attention, schedule, performance, recent activity. Order on Receptionist Home: header, member search, quick actions, overview, needs attention, schedule, activity, recent members. Order on Trainer Home: header, next session, quick actions, overview, schedule, needs attention, members' activity. Order on Member Home: header, membership card, today's plan, upcoming session, today's progress, attendance streak, recent progress, reminders.
- Order on Attendance: header, day strip, Check In Member, the day's figures, check-ins by hour, expected soon, check-ins.
- Order on the Workout tab: today's workout, exercises, this week, the trainer's note, coming up. On the Diet tab: the day's summary, water, meals, the trainer's note. On the Progress tab: goal, weight, measurements, attendance, training.
- On Member Home the membership card and the Start Workout button are visible without scrolling. Its bottom navigation has five equal tabs and no create button.
- On Receptionist Home the search field and the Check In Member tile are visible without scrolling at every phone size, and the search field stays pinned to the top while the rest scrolls. Checking a member in takes two taps: the tile or the search field, then Check In on the result.
- A row of cards that scrolls sideways shows a slice of the next card to signal the scroll.
- No tables on a phone. Use cards, lists, bottom sheets and sideways scroll.
- A list row is two lines on a phone: what it is and its status on the first, its ID and the date that matters on the second. From 768px the row may spread into columns under a header row.
- The bottom navigation is fixed and respects the bottom safe area. Give the screen `nav-height` plus `space-12` of bottom padding so the last section clears it.
- From 768px: no sidebar, keep the bottom navigation. Overview cards become four across (five on Admin Home) and sections flow into two columns inside a centred container of `container-max` (960px).
- Respect the safe areas with `env(safe-area-inset-*)` on the header, the bottom navigation and sheets.

## Shape, depth and motion

- Corners: `radius-md` on fields, buttons, cards and tiles; `radius-sm` on the logo tile, icon chips and segmented controls; `radius-xs` on plates and tooltips; `radius-lg` on the top of a sheet; `radius-pill` on chips, tags, avatars and round buttons.
- Shadows: `shadow-button` under primary actions, `shadow-card` under cards on the `surface` canvas, `shadow-raised` under the bottom navigation and sheets. Fields and the Needs attention card are flat.
- Focus is a 2px `ink` edge; on fields it also carries `shadow-focus` (a 4px `volt` halo).
- Every tappable element has a pressed state: buttons, tiles and cards scale to 97–98%, rows and chips darken or fade.
- Progress rings and bars draw in once on load, from empty to their value.
- Motion answers a touch: a sheet slides up over a `scrim`, the create button's plus turns to a cross, a segmented control slides its selection. The only motion on load is the plates sliding onto the bar on sign-in, and skeleton blocks pulsing while data loads. Honour `prefers-reduced-motion`.

## Charts

- One series per chart. Bars and lines are `ink`; the current period (today's bar, the line's end point) is `volt`. Gridlines are `line` hairlines; axis text is `micro` in `ink-muted`.
- Bars for a week, a line for longer periods. Bars are at most 24px wide with a 4px rounded top; lines are 2px.
- A measure that never nears zero (body weight) uses a line on a trimmed axis with no area fill, so the slope is not exaggerated by a filled shape.
- Label only the current value on the chart. Every other value shows in a tooltip on tap, hover or keyboard focus: the value in bold, then the day.
- Text on a chart is never coloured.
- A chart of a day still in progress (Attendance by hour) keeps the whole day on the axis. The current hour is the `volt` mark, and hours still to come are left empty and cannot be tapped.
- To compare parts (plans, categories, trainers, hours) use a BarList: one `ink` bar per row, scaled to the largest, with the value printed beside the name. No pies or donuts.
- A report has one period control and one branch for the whole screen, above everything it changes. No chart carries its own filter.
- A headline figure is a number in `metric` with its label under it and its change against the period before, in words.

## Imagery and icons

- The barbell is the brand's one picture: plates stepping up to a `volt` inner plate, with the bar running off the right edge of the screen. Use it once on auth screens, above the heading. On app screens it appears in one place only, the member's workout card (on Member Home and the Workout tab), in its `on-ink` form; elsewhere the chart's one `volt` bar echoes it. No illustrations, no gradients. Member Home may carry at most one photo, on the workout card, in place of the barbell.
- Icons are Lucide, inline SVG on a 24px grid at 1.75px stroke with round caps and joins, in `currentColor`. Sizes: 24px in tiles and navigation, 20px in chips and rows, 16px in trends. Use no other icon set and no filled icons.
- The app mark is `assets/Logos/dumbelo-mark.svg`.
- A member's photo sits in a round `rl-photo`. When there is no photo, show their initials there; never a stock picture.

## Forms and keyboards

- Always a visible label above the field. The placeholder is an example, never the label.
- Ask only for what the task needs. Mark the fields that can be skipped with "(optional)"; never mark the required ones with an asterisk.
- On app and task screens a field is `ground` with a 1px `field-line` edge, so it stands out from the `surface` canvas.
- A choice of one from a few uses ChoiceCards when each option needs a line of detail or a price, and chips when the options are single words. A dropdown is the last resort, for long lists.
- Numbers that belong together (sets, reps, weight) sit side by side in small fields with a label above each, never in a table.
- A note is a TextArea, three lines tall, marked optional, with a hint saying who will read it.
- On a detail screen every value sits under its label in a DetailList. Write the label in the reader's words ("Mobile number", "Day off", "Paid to"); an empty value reads "Not added" or "Not set".
- A setting that takes effect at once is a Switch, with no Save button. Anything that needs saving is a task with a form.
- Editing reuses the task that added the record: same fields and order, the title "Edit…", the button "Save Changes", and a sheet that says "Changes saved".
- Money is typed in an AmountField, large, with the currency sign fixed in front. Say under it what will still be due.
- The action bar's button names the action and, for a payment, the amount: "Collect ₹1,500". It stays enabled; if something is missing, say what under the field.
- Give every input its `autocomplete`, `inputmode` and `enterkeyhint`: the sign-in identifier is `autocomplete="username" inputmode="email" enterkeyhint="next"`, the password is `autocomplete="current-password" enterkeyhint="go"`. Turn off `autocapitalize`, `autocorrect` and `spellcheck` on both.
- Return on the first field moves to the next; return on the last submits.
- Set the viewport to `width=device-width, initial-scale=1, viewport-fit=cover, interactive-widget=resizes-content` so the layout shrinks with the keyboard.
- A one-time code is a CodeField: six cells, numeric keyboard, filled from the phone's autofill when it offers.
- Validate on submit, show the message under the field, focus the first invalid field, and clear the error as soon as the person types.
