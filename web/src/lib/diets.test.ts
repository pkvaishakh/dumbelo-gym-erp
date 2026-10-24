import { describe, expect, it } from "vitest";

import { dietSummary, grams, macrosLine, toMealRows, toMeals } from "./diets";

describe("diet plans", () => {
  const meals = [{ name: "Breakfast", food: "Oats", kcal: 400 }, { name: "Lunch", food: "Dal rice" }];
  it("sums a plan up and says its targets", () => {
    expect(dietSummary({ kcal: 1800, meals })).toBe("2 meals • 1,800 kcal a day");
    expect(dietSummary({ meals })).toBe("2 meals");
    expect(macrosLine({ protein_g: 110, carbs_g: null, fat_g: 55 })).toBe("Protein 110 g • Fat 55 g");
    expect(macrosLine({})).toBe("");
  });
  it("turns the form's rows into meals, dropping ones with nothing in them", () => {
    const rows = [{ name: " Breakfast ", time: " 7 AM ", food: " Oats ", kcal: "400" }, { name: "Lunch", time: "", food: " ", kcal: "" }];
    expect(toMeals(rows)).toEqual([{ name: "Breakfast", time: "7 AM", food: "Oats", kcal: 400 }]);
    expect(toMealRows(meals)[1]).toEqual({ name: "Lunch", time: "", food: "Dal rice", kcal: "" });
    expect([grams(""), grams("120")]).toEqual([null, 120]);
  });
});
