import { expect, test, type Page } from "@playwright/test";

async function signIn(page: Page, who: string) {
  await page.goto("/login");
  await page.getByLabel("Mobile number or email").fill(who);
  await page.getByLabel("Password", { exact: true }).fill("rackline-demo");
  await page.getByRole("button", { name: "Sign In" }).click();
  await page.waitForURL("**/home");
}

test("admin: home figures, a member's profile, and assigning a task", async ({ page }) => {
  await signIn(page, "meera@rackline.demo");
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
  await page.getByLabel("Assign to").selectOption({ label: "Arjun Rao (Receptionist)" });
  await page.getByRole("button", { name: "Assign Task" }).click();
  await expect(page.getByText("Task assigned")).toBeVisible();
});

test("admin: add a member with a plan and part payment", async ({ page }) => {
  await signIn(page, "meera@rackline.demo");
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
  await signIn(page, "arjun@rackline.demo");
  const search = page.getByLabel("Search members to check in");
  await search.fill("RF-10");
  const row = page.locator(".rl-result").filter({ has: page.getByRole("button", { name: "Check In" }) }).first();
  await row.getByRole("button", { name: "Check In" }).click();
  const sheet = page.locator(".rl-sheet.is-open");
  await expect(sheet.locator(".rl-confirm__title")).toHaveText(/is checked in|Already checked in|Check-in blocked/);
  await sheet.getByRole("button", { name: "Done" }).click();
});

test("trainer: sees own members without amounts", async ({ page }) => {
  await signIn(page, "neha@rackline.demo");
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
  await signIn(page, "meera@rackline.demo");
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

test("admin: turns the gym's reminders off and on, and sees what a member was sent", async ({ page }) => {
  await signIn(page, "meera@rackline.demo");
  await page.goto("/more");
  await page.getByRole("link", { name: "Settings" }).click();
  await expect(page.getByRole("heading", { name: "Reminders to members" })).toBeVisible();

  const setting = page.locator("label.rl-setting");
  await expect(setting.getByRole("switch")).toBeChecked();
  await setting.click();
  await expect(setting.getByRole("switch")).not.toBeChecked();
  await expect(setting.getByText(/^Off: no one is messaged/)).toBeVisible();
  await setting.click();  // and back on, so the demo gym is left as it was
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
