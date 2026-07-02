// Browser build of the AllergyLens engine — runs fully client-side so it works
// on GitHub Pages (no server). Mirrors the logic in lib/*.ts and
// ../allergylens_engine/*.py, and reads the same data/*.json files.
//
// Exposes window.AllergyEngine:
//   await AllergyEngine.ready                 -> resolves once data is loaded
//   await AllergyEngine.scanText(text)        -> { rawText, ingredients, detectedAllergens }
//   await AllergyEngine.scanImage(fileOrUrl)  -> same, after running OCR
//   AllergyEngine.ENGINE_TO_UI                -> maps engine allergen keys to UI ids
(function () {
  "use strict";

  const DATA = { allergens: null, aliases: null, concerns: null };

  // Engine allergen key -> the id used by the UI's allergy-profile chips.
  const ENGINE_TO_UI = {
    wheat: "gluten",
    dairy: "dairy",
    tree_nut: "treenuts",
    shellfish: "shellfish",
    peanut: "peanuts",
    soy: "soy",
    egg: "eggs",
    fish: "fish",
    sesame: "sesame",
  };

  const LABELS = { gerd_lpr: "GERD/LPR", histamine: "Histamine" };
  const displayName = (k) =>
    LABELS[k] || k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  // Word-boundary match with a simple plural suffix: "almond" matches "almonds"
  // but "egg" won't match "eggplant". Multi-word keywords use substring match.
  function keywordIn(keyword, ingredient) {
    const kw = keyword.toLowerCase();
    if (kw.includes(" ")) return ingredient.includes(kw);
    return new RegExp(`\\b${escapeRe(kw)}(?:s|es)?\\b`).test(ingredient);
  }

  // ---- parser (mirror of lib/parser.ts) ----------------------------------
  const HEADER = /ingredients?\s*[:\-]/i;
  const END =
    /\b(contains|may contain|manufactured|distributed|allergen|nutrition|net wt|best by|directions|storage)\b/i;

  function findSection(text) {
    if (!text) return "";
    const h = HEADER.exec(text);
    let s = h ? text.slice(h.index + h[0].length) : text;
    const e = END.exec(s);
    if (e) s = s.slice(0, e.index);
    return s.trim();
  }

  function cleanText(text) {
    return text
      .replace(/\r/g, "\n")
      .replace(/-\s*\n\s*/g, "")
      .replace(/\s*\n\s*/g, " ")
      .replace(/\s{2,}/g, " ")
      .trim();
  }

  function cleanIngredient(item) {
    return item
      .trim()
      .replace(/^[.;:*•·\-\s]+|[.;:*•·\-\s]+$/g, "")
      .replace(/\s{2,}/g, " ")
      .trim()
      .toLowerCase();
  }

  function parseIngredients(rawText) {
    let section = cleanText(findSection(rawText));
    if (!section) return [];
    section = section.replace(/[()[\]]/g, ", "); // flatten parentheticals
    const parts = section.split(/[,;•·|]| and /);
    const seen = new Set();
    const out = [];
    for (const part of parts) {
      const c = cleanIngredient(part);
      if (!c || c.length < 2 || seen.has(c)) continue;
      seen.add(c);
      out.push(c);
    }
    return out;
  }

  // ---- allergen matching (mirror of lib/allergenEngine.ts) ---------------
  function detectAllergens(ingredients) {
    const found = new Map();
    for (const ingredient of ingredients) {
      const ing = ingredient.toLowerCase();

      for (const [key, keywords] of Object.entries(DATA.allergens)) {
        for (const keyword of keywords) {
          if (keywordIn(keyword, ing)) {
            found.set(`${key}::${ingredient}`, {
              allergen: displayName(key),
              allergenKey: key,
              matchedIngredient: ingredient,
              severity: "high",
              reason: `'${ingredient}' is a known source of ${displayName(key)}.`,
            });
          }
        }
      }

      for (const [alias, possible] of Object.entries(DATA.aliases)) {
        if (keywordIn(alias, ing)) {
          for (const key of possible) {
            const id = `${key}::${ingredient}`;
            const existing = found.get(id);
            if (existing && existing.severity === "high") continue;
            found.set(id, {
              allergen: displayName(key),
              allergenKey: key,
              matchedIngredient: ingredient,
              severity: "medium",
              reason: `'${ingredient}' can be a hidden source of ${displayName(
                key,
              )} — needs review.`,
            });
          }
        }
      }
    }
    return [...found.values()];
  }

  function scan(text) {
    const ingredients = parseIngredients(text || "");
    return {
      rawText: text || "",
      ingredients,
      detectedAllergens: detectAllergens(ingredients),
    };
  }

  // ---- OCR via tesseract.js (loaded from CDN, optional) ------------------
  const TESSERACT_URL = "https://unpkg.com/tesseract.js@5.1.0/dist/tesseract.min.js";

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const el = document.createElement("script");
      el.src = src;
      el.onload = resolve;
      el.onerror = () => reject(new Error(`Failed to load ${src}`));
      document.head.appendChild(el);
    });
  }

  async function ocr(image) {
    if (!window.Tesseract) await loadScript(TESSERACT_URL);
    try {
      const { data } = await window.Tesseract.recognize(image, "eng");
      return (data.text || "").trim();
    } catch {
      return ""; // let the caller treat "no text" as needs-review
    }
  }

  // ---- data loading + public API -----------------------------------------
  const ready = (async () => {
    const [allergens, aliases, concerns] = await Promise.all([
      fetch("./data/allergens.json").then((r) => r.json()),
      fetch("./data/ingredientAliases.json").then((r) => r.json()),
      fetch("./data/dietaryConcerns.json").then((r) => r.json()),
    ]);
    DATA.allergens = allergens;
    DATA.aliases = aliases.aliases || {};
    DATA.concerns = concerns.concerns || {};
  })();

  window.AllergyEngine = {
    ready,
    ENGINE_TO_UI,
    async scanText(text) {
      await ready;
      return scan(text);
    },
    async scanImage(image) {
      await ready;
      const text = await ocr(image);
      return scan(text);
    },
  };
})();
