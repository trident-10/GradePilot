export const PLANNER_STRATEGIES = [
  {
    id: "min_courses",
    label: "En az ders",
    description:
      "Hedefe mümkün olan en az sayıda ders değişikliğiyle ulaşmayı dener.",
  },
  {
    id: "lowest_grades",
    label: "En düşük notlardan başla",
    description: "Önce düşük notlu dersleri değerlendirir.",
  },
  {
    id: "minimal_change",
    label: "En az not değişikliği",
    description: "Hedefi daha küçük not adımlarıyla yakalamaya çalışır.",
  },
] as const;

export type PlannerStrategyId = (typeof PLANNER_STRATEGIES)[number]["id"];
