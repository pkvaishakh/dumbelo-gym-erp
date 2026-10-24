import { expect, test, type Page } from "@playwright/test";

async function signIn(page: Page, who: string) {
  await page.goto("/login");
  await page.getByLabel("Mobile number or email").fill(who);
  await page.getByLabel("Password", { exact: true }).fill("dumbelo-demo");
  await page.getByRole("button", { name: "Sign In" }).click();
  await page.waitForURL("**/home");
}

test("admin: home figures, a member's profile, and assigning a task", async ({ page }) => {
  await signIn(page, "meera@dumbelo.demo");
  await expect(page.getByRole("heading", { name: /Good (morning|afternoon|evening), Meera/ })).toBeVisible();
  await expect(page.getByText("Outstanding dues")).toBeVisible();
  await expect(page.getByText("Check-ins today").first()).toBeVisible();

  await page.getByRole("link", { name: /Pending payments/ }).click();
  await expect(page).toHaveURL(/status=due/);
  await page.locator("a.rl-mrow").first().click();
  await expect(page.getByRole("heading", { name: "Payments" })).toBeVisible();
  await expect(page.getByRole("link", { name: /^Collect ₹/ })).toBeVisible();

  await page.goto("/tasks");
  await page.getByRole("button", { name: "New Task" }).click();
  await page.getByRole("textbox", { name: "Task" }).fill("Check the treadmill belts");
  // The label adds their branches when the gym has more than one: "Arjun Rao (Receptionist, Indiranagar)".
  const assignTo = page.getByLabel("Assign to");
  await assignTo.selectOption((await assignTo.locator("option", { hasText: "Arjun Rao (Receptionist" }).getAttribute("value"))!);
  await page.getByRole("button", { name: "Assign Task" }).click();
  await expect(page.getByText("Task assigned")).toBeVisible();
});

test("admin: add a member with a plan and part payment", async ({ page }) => {
  await signIn(page, "meera@dumbelo.demo");
  await page.goto("/members/new");
  const phone = "9" + String(Date.now()).slice(-9);
  await page.getByLabel("Full name").fill("Test Member");
  await page.getByLabel("Mobile number").fill(phone);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.locator(".rl-choice", { hasText: "Monthly" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Part", exact: true }).click();
  await page.getByLabel("Amount in rupees").fill("500");
  await page.getByRole("button", { name: "Collect ₹500" }).click();
  await expect(page.getByText("Test Member is now a member")).toBeVisible();
  await expect(page.getByText("₹1,000 is still due.")).toBeVisible();
});

test("receptionist: check a member in from home, once a day", async ({ page }) => {
  await signIn(page, "arjun@dumbelo.demo");
  await page.getByRole("button", { name: /Check In Member/ }).click();
  const search = page.getByLabel("Search members to check in");
  await search.fill("RF-10");
  await search.press("Enter");  // searches on Enter only, not while typing
  const row = page.locator(".rl-result").filter({ has: page.getByRole("button", { name: "Check In" }) }).first();
  await row.getByRole("button", { name: "Check In" }).click();
  const sheet = page.locator(".rl-sheet.is-open").filter({ has: page.locator(".rl-confirm") });
  await expect(sheet.locator(".rl-confirm__title")).toHaveText(/is checked in|Already checked in|Check-in blocked/);
  await sheet.getByRole("button", { name: "Done" }).click();
  await expect(search).toBeFocused();  // the check-in sheet stays open, ready for the next member
});

test("trainer: sees own members without amounts", async ({ page }) => {
  await signIn(page, "neha@dumbelo.demo");
  await page.goto("/members");
  await expect(page.getByRole("heading", { name: "My Members" })).toBeVisible();
  await page.locator("a.rl-mrow").first().click();
  await expect(page.getByRole("heading", { name: "Payments" })).toHaveCount(0);
  await expect(page.getByText(/₹/)).toHaveCount(0);
});

test("member: home shows the membership and visits", async ({ page }) => {
  await signIn(page, "9800000001");
  await expect(page.locator(".rl-pass")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Recent visits" })).toBeVisible();
  await page.goto("/more");
  await page.getByRole("button", { name: "Sign Out" }).click();
  await page.waitForURL("**/login");
});

test("admin: long lists load a page at a time, and the other list screens load", async ({ page }) => {
  await signIn(page, "meera@dumbelo.demo");
  await page.goto("/members");
  await expect(page.getByText(/^Showing 50 members of \d+$/)).toBeVisible();  // the demo gym has more than one page
  await page.getByRole("button", { name: "Load More" }).click();
  await expect(page.getByText(/^Showing \d+ members$/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Load More" })).toHaveCount(0);

  for (const [path, heading] of [["/attendance", "Check-ins"], ["/tasks", "Tasks"], ["/collection", "Payments"], ["/expenses", "Expenses"]]) {
    await page.goto(path);
    await expect(page.getByRole("heading", { name: heading }).first()).toBeVisible();
    await expect(page.locator('[aria-busy="true"]')).toHaveCount(0);
    await expect(page.getByText("Something went wrong")).toHaveCount(0);
  }
});

test("admin: pauses and resumes a message, and sees what a member was sent", async ({ page }) => {
  await signIn(page, "meera@dumbelo.demo");
  await page.goto("/more");
  await page.getByRole("link", { name: "Settings" }).click();
  await expect(page.getByRole("heading", { name: "Messages" })).toBeVisible();

  const setting = page.locator("label.rl-setting").filter({ has: page.locator('input[name="message-plan_ending"]') });
  await expect(setting.getByRole("switch")).toBeChecked();
  await setting.click();
  await expect(setting.getByRole("switch")).not.toBeChecked();
  await expect(setting.getByText(/• Paused$/)).toBeVisible();
  await setting.click();  // and Resume, so the demo gym is left as it was
  await expect(setting.getByRole("switch")).toBeChecked();

  // a member who owes money has been messaged about it, and can be taken off the list
  await page.goto("/members?status=due");
  await page.locator("a.rl-mrow").first().click();
  const card = page.locator("section").filter({ has: page.getByRole("heading", { name: "Reminders" }) });
  await expect(card.getByText("Payment due").first()).toBeVisible();
  await expect(card.getByText(/is still to pay on your/).first()).toBeVisible();
  const theirs = card.locator("label.rl-setting");
  await theirs.click();
  await expect(theirs.getByRole("switch")).not.toBeChecked();
  await theirs.click();
  await expect(theirs.getByRole("switch")).toBeChecked();
});

test("admin: work out payroll, approve and pay a salary, then pay a bill from Dues", async ({ page }) => {
  await signIn(page, "meera@dumbelo.demo");
  await page.goto("/payroll");
  await page.getByRole("button", { name: /^(Update|Work Out) Payroll$/ }).first().click();
  await page.locator("a.rl-mrow", { hasText: "Imran Khan" }).click();
  await expect(page.getByText("Take-home pay").first()).toBeVisible();
  if (await page.getByRole("button", { name: /^Approve ₹/ }).isVisible()) await page.getByRole("button", { name: /^Approve ₹/ }).click();
  await page.getByRole("button", { name: /^Pay (Salary|More)$/ }).click();
  await page.getByRole("button", { name: /^Pay ₹/ }).click();
  await expect(page.getByRole("heading", { name: /₹[\d,]+ paid/ })).toBeVisible();
  await page.getByRole("button", { name: "Done" }).click();
  await expect(page.locator(".rl-status", { hasText: "Paid" }).first()).toBeVisible();

  await page.goto("/expenses/dues");
  await page.locator("section[aria-label=Bills] button.rl-activity__row").first().click();
  await page.getByRole("button", { name: /^Pay ₹/ }).click();
  await page.getByRole("dialog").getByRole("button", { name: /^Pay ₹/ }).click();
  await expect(page.getByRole("heading", { name: /₹[\d,]+ paid/ })).toBeVisible();
});

test("admin: cash and bank, a shared account, and banking a branch's cash", async ({ page }) => {
  await signIn(page, "meera@dumbelo.demo");
  await page.goto("/more");
  await page.getByRole("link", { name: /Cash and bank/ }).click();
  await expect(page.getByText("Total funds")).toBeVisible();
  // HDFC is shared by two branches: each says so, and the totals count it once.
  await expect(page.getByRole("button", { name: /Indiranagar.*HDFC current.*shared with Koramangala/ })).toBeVisible();
  await page.getByRole("button", { name: /^Koramangala/ }).click();
  await expect(page.getByRole("dialog", { name: "Koramangala" }).getByText("Also used by Indiranagar")).toBeVisible();
  await page.getByRole("dialog", { name: "Koramangala" }).getByRole("button", { name: "Close" }).click();

  await page.getByRole("link", { name: "Move Money" }).click();
  // Each option reads "Indiranagar cash • ₹5,000": pick by the account's name, whatever it holds.
  for (const [field, name] of [["From", "Indiranagar cash"], ["To", "HDFC current"]]) {
    const select = page.getByRole("combobox", { name: field, exact: true });
    await select.selectOption((await select.locator("option", { hasText: name }).getAttribute("value"))!);
  }
  await page.getByLabel("Amount in rupees").fill("1000");
  await page.getByRole("button", { name: "Move ₹1,000" }).click();
  await expect(page.getByText("₹1,000 moved")).toBeVisible();
  await expect(page.getByText("It isn't counted as income or spending.")).toBeVisible();
  await page.getByRole("link", { name: "Done" }).click();
  await expect(page.getByRole("button", { name: /Cash to bank.*Indiranagar cash to HDFC current/ }).first()).toBeVisible();
  // HDFC's statement lists the banked cash with the balance after it.
  await page.getByRole("link", { name: /^HDFC current/ }).click();
  await page.getByRole("link", { name: "Statement" }).click();
  await expect(page.getByRole("heading", { name: "Statement" })).toBeVisible();
  await expect(page.getByText("From Indiranagar cash").first()).toBeVisible();
  // Ticking an entry as on the bank's statement too, and unticking it again.
  const first = page.getByRole("button", { name: /on the bank's statement/ }).first();
  await first.click();
  await expect(first).toHaveAttribute("aria-pressed", "true");
  await first.click();
  await expect(first).toHaveAttribute("aria-pressed", "false");
  await expect(page.getByRole("heading", { name: "Check against the bank" })).toBeVisible();
  // The month as a CSV for the accountant, and as a page to print or save as a PDF.
  const [file] = await Promise.all([page.waitForEvent("download"), page.getByRole("button", { name: "Download CSV" }).click()]);
  expect(file.suggestedFilename()).toMatch(/^HDFC current \d{4}-\d{2}\.csv$/);
  await page.getByRole("link", { name: "Print or PDF" }).click();
  await expect(page.getByText(/^Closing balance/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Print Statement" })).toBeVisible();
});

test("receptionist counts the cash short, and an admin settles it", async ({ page }) => {
  await signIn(page, "arjun@dumbelo.demo");
  // Home shows the drawers' cash; More leads to each drawer, then Count Cash.
  await expect(page.getByRole("link", { name: /Cash in hand/ })).toBeVisible();
  await page.goto("/more");
  await page.getByRole("link", { name: /Cash in hand/ }).click();
  await expect(page.getByText("Should be in the drawer").first()).toBeVisible();
  await page.getByRole("link", { name: /^Count (Cash|Again)$/ }).first().click();
  await page.getByRole("radio", { name: "Indiranagar" }).check();
  const expected = (await page.getByText(/Should be in Indiranagar's drawer/).locator("..").locator(".rl-stat__value").textContent())!;
  const short = Number(expected.replace(/[^\d]/g, "")) - 100; // ₹100 short
  await page.getByLabel("Cash counted in rupees").fill(String(short));
  await expect(page.getByText("₹100 short: an admin settles the difference.")).toBeVisible();
  await page.getByRole("button", { name: "Save Count" }).click();
  await expect(page.getByText("Cash counted: ₹100 short")).toBeVisible();

  await page.getByRole("link", { name: "Done" }).click();
  await page.evaluate(() => localStorage.clear());
  await signIn(page, "meera@dumbelo.demo");
  await page.goto("/money");
  await page.getByRole("button", { name: /Indiranagar cash.*₹100 short/ }).click();
  await page.getByLabel("What happened").fill("Change given twice");
  await page.getByRole("button", { name: "Settle ₹100" }).click();
  await expect(page.getByText("Nothing to settle.")).toBeVisible();
  await expect(page.getByRole("button", { name: /Withdrawal.*Cash count/ }).first()).toBeVisible();
});

test("admin: refunds part of a plan, and the member owes nothing because of it", async ({ page }) => {
  await signIn(page, "meera@dumbelo.demo");
  await page.goto("/members?status=active");
  await page.locator("a.rl-mrow").first().click();
  await page.getByRole("button", { name: "More actions" }).click();
  await page.getByRole("button", { name: "Refund Money" }).click();
  const sheet = page.getByRole("dialog", { name: "Refund Money" });
  await sheet.locator("input[name=refund-plan]").first().check({ force: true });
  await sheet.getByLabel("Amount to refund in rupees").fill("100");
  await sheet.getByLabel("Reason").fill("Goodwill");
  await sheet.getByRole("button", { name: "Refund ₹100" }).click();
  await expect(page.getByText("₹100 refunded")).toBeVisible();
  await page.getByRole("button", { name: "Done" }).click();
  await expect(page.getByText("−₹100 by CASH")).toBeVisible();
  await expect(page.getByRole("link", { name: /^Collect/ })).toHaveCount(0);
});

test("trainer: no cash and bank in More", async ({ page }) => {
  await signIn(page, "neha@dumbelo.demo");
  await page.goto("/more");
  await expect(page.getByRole("heading", { name: "Your work" })).toBeVisible();
  await expect(page.getByRole("link", { name: /Cash and bank/ })).toHaveCount(0);
});

test("admin: reports by category, yesterday, a custom range over 3 months, and downloads", async ({ page }) => {
  await signIn(page, "meera@dumbelo.demo");
  await page.getByRole("navigation", { name: "Main" }).getByRole("link", { name: "Reports" }).click();
  await expect(page.getByRole("heading", { name: "Reports" })).toBeVisible();
  for (const name of ["Revenue", "Expenses", "Members", "Attendance", "Tasks"]) await expect(page.getByRole("main").getByRole("link", { name: new RegExp(`^${name}`) })).toBeVisible();

  await page.getByRole("main").getByRole("link", { name: /^Cash and bank/ }).click();
  await expect(page).toHaveURL(/\/reports\/money/);
  await expect(page.getByRole("heading", { name: "Total funds" })).toBeVisible();
  await page.getByRole("button", { name: "Yesterday", exact: true }).click();
  await expect(page).toHaveURL(/period=yesterday/);
  await expect(page.getByRole("heading", { name: "Accounts" })).toBeVisible();

  // Four months back is more than 3: the API's words, under From, before anything is asked for.
  await page.getByRole("button", { name: "Custom", exact: true }).click();
  const back = new Date();
  back.setMonth(back.getMonth() - 4);
  await page.getByLabel("From", { exact: true }).fill(back.toISOString().slice(0, 10));
  await page.getByRole("button", { name: "Show Report" }).click();
  await expect(page.getByText("Pick a range of 3 months or less")).toBeVisible();

  await page.getByRole("button", { name: "This month", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Accounts" })).toBeVisible();
  await page.getByRole("button", { name: "Download", exact: true }).click();
  const [file] = await Promise.all([page.waitForEvent("download"), page.getByRole("button", { name: "Download CSV" }).click()]);
  expect(file.suggestedFilename()).toMatch(/^Cash and bank \d{4}-\d{2}-\d{2} to \d{4}-\d{2}-\d{2}\.csv$/);
  await page.getByRole("button", { name: "Download", exact: true }).click();
  await page.getByRole("link", { name: "Print or PDF" }).click();
  await expect(page.getByRole("heading", { name: "Accounts" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Print Report" })).toBeVisible();
});

test("receptionist: no Reports", async ({ page }) => {
  await signIn(page, "arjun@dumbelo.demo");
  await expect(page.getByRole("navigation", { name: "Main" }).getByRole("link", { name: "Reports" })).toHaveCount(0);
  await page.goto("/reports");
  await expect(page.getByText("Reports are for admins")).toBeVisible();
});

test("dumbelo admin: lands on Console Home, and reaches the gyms that owe, Gyms and Prices", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Mobile number or email").fill("dumbelo@dumbelo.demo");
  await page.getByLabel("Password", { exact: true }).fill("dumbelo-demo");
  await page.getByRole("button", { name: "Sign In" }).click();
  await page.waitForURL(/\/console$/);
  const tabs = page.getByRole("navigation", { name: "Console" });
  await expect(tabs.getByRole("link")).toHaveText(["Home", "Gyms", "Server", "More"]);
  await expect(tabs.getByRole("link", { name: "Home" })).toHaveAttribute("aria-current", "page");
  await expect(page.getByText("Owed to Dumbelo")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Needs attention" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Server" })).toBeVisible();

  await page.getByRole("link", { name: /Overdue/ }).first().click();
  await expect(page).toHaveURL(/\/console\/gyms\?owes=overdue$/);
  await expect(page.getByRole("radio", { name: "Overdue" })).toBeChecked();

  await tabs.getByRole("link", { name: "Gyms" }).click();
  await expect(page).toHaveURL(/\/console\/gyms$/);
  await page.locator("a.rl-mrow").first().click();
  await expect(page).toHaveURL(/\/console\/gyms\/\d+$/);
  await expect(tabs.getByRole("link", { name: "Gyms" })).toHaveAttribute("aria-current", "page");

  await tabs.getByRole("link", { name: "More" }).click();
  await page.getByRole("link", { name: /Prices/ }).click();
  await expect(page).toHaveURL(/\/console\/prices$/);
  await expect(tabs.getByRole("link", { name: "More" })).toHaveAttribute("aria-current", "page");
});

async function signInToConsole(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Mobile number or email").fill("dumbelo@dumbelo.demo");
  await page.getByLabel("Password", { exact: true }).fill("dumbelo-demo");
  await page.getByRole("button", { name: "Sign In" }).click();
  await page.waitForURL(/\/console$/);
}

test("admin: More → Messages, with filters, why a message failed, and this billing month on Dumbelo's number", async ({ page }) => {
  await signIn(page, "meera@dumbelo.demo");
  await page.goto("/more");
  await page.getByRole("link", { name: "Messages", exact: true }).click();
  await expect(page).toHaveURL(/\/messages$/);
  await expect(page.getByText("So far this billing month")).toBeVisible();
  await expect(page.getByText("Goes on the invoice of")).toBeVisible();
  await expect(page.locator("button.rl-mrow").first()).toBeVisible();

  // The demo has two failed reminders: Meta turned one away (Retry is offered) and never answered about the other.
  await page.getByRole("radio", { name: "Failed" }).click();
  await expect(page).toHaveURL(/status=failed/);
  const rows = page.locator("button.rl-mrow");
  await expect(rows).toHaveCount(2);
  const seen: string[] = [];
  for (const i of [0, 1]) {
    await rows.nth(i).click();
    const sheet = page.locator(".rl-sheet.is-open");
    await expect(sheet.getByText("Why it failed")).toBeVisible();
    const mayHaveGone = (await sheet.getByText(/didn't answer/).count()) > 0;
    await expect(sheet.getByRole("button", { name: "Retry" })).toHaveCount(mayHaveGone ? 0 : 1);
    seen.push(mayHaveGone ? "may have gone" : "turned away");
    await sheet.getByRole("button", { name: "Close" }).click();
  }
  expect(seen.sort()).toEqual(["may have gone", "turned away"]);

  await page.getByRole("button", { name: /^Filters/ }).click();
  const filters = page.locator(".rl-sheet.is-open");
  await filters.getByLabel("Message").selectOption("payment_due");
  await filters.getByRole("button", { name: "Members" }).click();
  await expect(page).toHaveURL(/kind=payment_due/);
  await expect(page).toHaveURL(/recipient=member/);
  await filters.getByRole("button", { name: "Show 2 messages" }).click();
  await expect(page.getByText(/payment due, members$/)).toBeVisible();
});

// Dumbelo's side from start to end, on a gym opened for this run: Dumbelo opens it and sets its quota, its admin
// fills the plan and asks for room, Dumbelo approves, changes its reminder time and suspends it, and its desk is paused.
test.describe.serial("dumbelo: from a new gym to a paused one", () => {
  const stamp = Date.now().toString(36);
  const gym = { name: `E2E Gym ${stamp}`, slug: `e2e-${stamp}`, owner: `owner-${stamp}@dumbelo.demo`, desk: `desk-${stamp}@dumbelo.demo` };
  const password = "dumbelo-e2e-1";
  let gymUrl = "";

  async function signInAs(page: Page, email: string) {
    await page.goto("/login");
    await page.getByLabel("Mobile number or email").fill(email);
    await page.getByLabel("Password", { exact: true }).fill(password);
    await page.getByRole("button", { name: "Sign In" }).click();
    await page.waitForURL("**/home");
  }

  test("dumbelo admin: opens a gym and gives it room for 2 branches", async ({ page }) => {
    await signInToConsole(page);
    await page.goto("/console/gyms/new");
    await page.getByLabel("Gym name").fill(gym.name);
    await page.getByLabel("Short name").fill(gym.slug);
    await page.getByLabel("First branch").fill("Main");
    await page.getByLabel("Owner's email").fill(gym.owner);
    await page.getByLabel("Owner's name").fill("Esha Owner");
    await page.getByLabel("First password").fill(password);
    await page.getByRole("button", { name: "Create Gym" }).click();
    await expect(page.getByText(`${gym.name} is ready`)).toBeVisible();
    await page.getByRole("button", { name: "Open Gym" }).click();
    await page.waitForURL(/\/console\/gyms\/\d+$/);
    gymUrl = new URL(page.url()).pathname;

    await page.goto(`${gymUrl}/plan`);
    await page.getByRole("button", { name: "Edit Plan" }).click();
    const sheet = page.locator(".rl-sheet.is-open");
    await sheet.getByLabel("Branches it has room for").fill("2");
    await sheet.getByRole("button", { name: "Save Changes" }).click();
    await expect(sheet).toHaveCount(0);
    await expect(page.getByText("1 of 2", { exact: true })).toBeVisible();
    await expect(page.getByText("Room for 1 more branch")).toBeVisible();
  });

  test("its admin: adds a receptionist and a branch, finds the plan full, and asks Dumbelo for one more", async ({ page }) => {
    await signInAs(page, gym.owner);
    await page.goto("/staff/new?role=receptionist");
    await page.getByLabel("Full name").fill("Dev Desk");
    await page.getByLabel("Work email").fill(gym.desk);
    await page.getByLabel("First password").fill(password);
    await page.getByRole("checkbox", { name: "Main" }).check();
    await page.getByRole("button", { name: "Add Receptionist" }).click();
    await expect(page.getByRole("link", { name: "Done" })).toBeVisible();

    await page.goto("/branches");
    await page.getByRole("link", { name: "Add Branch" }).click();
    await page.getByLabel("Branch name").fill("Second");
    await page.getByRole("button", { name: "Add Branch" }).click();
    await page.waitForURL(/\/branches$/);
    await expect(page.getByText("Your plan has room for 2 branches")).toBeVisible();
    await expect(page.getByRole("link", { name: "Add Branch", exact: true })).toHaveCount(0);

    await page.getByRole("link", { name: "Add Branch to My Plan" }).click();
    await page.waitForURL(/\/dumbelo-plan$/);
    await page.getByRole("button", { name: "Add Branch to My Plan" }).click();
    await page.getByRole("button", { name: "Ask Dumbelo" }).click();
    await expect(page.getByText("Request sent")).toBeVisible();
    await page.getByRole("button", { name: "Done" }).click();
    await expect(page.getByText("Your last request")).toBeVisible();
  });

  test("dumbelo admin: approves it, changes the gym's reminder time, suspends it, and opens Server", async ({ page }) => {
    await signInToConsole(page);
    await page.goto(`${gymUrl}/plan`);
    await page.locator("button.rl-mrow", { hasText: "Asked" }).first().click();
    await page.getByRole("button", { name: "Approve" }).click();
    await expect(page.locator(".rl-sheet.is-open")).toHaveCount(0);
    await expect(page.getByText("2 of 3", { exact: true })).toBeVisible();

    await page.goto(gymUrl);
    await page.getByRole("button", { name: /^Plan ending soon/ }).click();
    const times = page.locator(".rl-sheet.is-open");
    await times.getByLabel("Goes out at").selectOption("8");
    await times.getByRole("button", { name: "Save Times" }).click();
    await expect(page.getByRole("button", { name: /^Plan ending soon.*8 AM, own time/ })).toBeVisible();

    await page.getByRole("button", { name: "Suspend Gym" }).click();
    const suspend = page.locator(".rl-sheet.is-open");
    await suspend.getByLabel("Reason").fill("End-to-end check");
    await suspend.getByRole("button", { name: "Suspend Gym" }).click();
    await expect(page.getByRole("button", { name: "Activate Gym" })).toBeVisible();

    await page.goto("/console/more");
    await page.getByRole("link", { name: /WhatsApp usage/ }).click();
    await expect(page.getByRole("heading", { name: "By gym" })).toBeVisible();
    const month = page.getByLabel("Month");
    await month.selectOption({ index: 1 });  // last month
    await expect(page).toHaveURL(/\/console\/usage\?month=\d{4}-\d{2}$/);
    await expect(page.getByText("Billed", { exact: true })).toBeVisible();

    await page.getByRole("navigation", { name: "Console" }).getByRole("link", { name: "Server" }).click();
    await expect(page.getByRole("heading", { name: "Health" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Webhook" })).toBeVisible();
  });

  test("its desk: sees the paused screen, wherever it goes", async ({ page }) => {
    await signInAs(page, gym.desk);
    await expect(page.getByRole("heading", { name: `${gym.name} is paused` })).toBeVisible();
    await expect(page.getByText("The app is paused for this gym.")).toBeVisible();
    await page.goto("/members");
    await expect(page.getByRole("heading", { name: `${gym.name} is paused` })).toBeVisible();
  });
});

test("dumbelo admin: records a payment on the demo gym's invoice, and its admin sees the invoice and the receipt", async ({ page }) => {
  await signInToConsole(page);
  await page.goto("/console/gyms");
  await page.locator("a.rl-mrow", { hasText: "Dumbelo Fitness" }).first().click();
  await page.waitForURL(/\/console\/gyms\/\d+$/);
  await page.getByRole("link", { name: "Invoices and payments" }).click();
  await page.locator("a.rl-mrow", { hasText: "to pay" }).first().click();
  await page.waitForURL(/\/console\/invoices\/\d+$/);
  const number = (await page.getByRole("region", { name: "Invoice total" }).getByText(/^RL\//).textContent())?.trim() ?? "";
  expect(number).toMatch(/^RL\//);
  await page.getByRole("button", { name: "Record Payment" }).click();
  const sheet = page.locator(".rl-sheet.is-open");
  await sheet.getByLabel("Amount in rupees").fill("100");
  await sheet.getByRole("button", { name: "Record ₹100" }).click();
  await expect(sheet.getByText("₹100 recorded")).toBeVisible();
  await sheet.getByRole("button", { name: "Done" }).click();

  await page.evaluate(() => localStorage.clear()); // sign out of the Console, so the login page asks again
  await signIn(page, "meera@dumbelo.demo");
  await page.goto("/dumbelo-plan");
  await page.locator("a.rl-mrow", { hasText: number }).click();
  await expect(page.getByRole("region", { name: "Invoice total" }).getByText(number, { exact: true })).toBeVisible();
  await page.locator("a.rl-mrow", { hasText: "₹100" }).first().click();
  await expect(page.getByRole("heading", { name: /^Receipt RLR\// })).toBeVisible();
});
