// Shapes of the JSON data files.

// allergen key -> keywords that indicate it (e.g. "dairy" -> ["milk", "whey"]).
export type AllergenMap = Record<string, string[]>;

// ambiguous ingredient -> allergens it might hide (e.g. "lecithin" -> ["soy"]).
export type AliasMap = Record<string, string[]>;

// non-allergen dietary trigger -> keywords (e.g. "gerd_lpr" -> ["caffeine"]).
export type ConcernMap = Record<string, string[]>;
