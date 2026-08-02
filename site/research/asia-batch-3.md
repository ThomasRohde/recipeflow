# Asia batch 3 research handoff

Retrieved 2026-08-02. Each linked page was read in full as source evidence only. The YAML paraphrases or closely translates the selected recipe while keeping exact quantities, timing, temperature, sensory endpoints, optionality, and source gaps visible. No facts were imported from comparison recipes.

## Nikujaga

- Source: [Ministry of Agriculture, Forestry and Fisheries of Japan — Japanese style beef and potato stew](https://www.maff.go.jp/e/policies/market/japan-cuisine/japan/12/index.html)
- Source standing and access: first-party English recipe from Japan's Ministry of Agriculture, Forestry and Fisheries; the complete live page was readable.
- Yield and timing evidence: ingredients are for two servings. The stew cooks 10 minutes covered and 10 minutes uncovered. The introduction permits immediate eating or an approximately one-hour rest followed by reheating.
- Ingredient evidence: 200 g thinly sliced beef loin; 1 teaspoon soy sauce for the beef; 1/2 onion; 2 potatoes; 1/2 carrot; 2 snow peas; 300 ml water; 5 x 10 cm dried kelp; a separate 4 teaspoons soy sauce; 1 tablespoon sugar; and 2 tablespoons "Japanese sweet sauce."
- Operation evidence: rub the first soy sauce onto the beef; wedge the onion; peel and roughly cut the potatoes; string the snow peas, boil them, cool them in cold water, and cut them into 2 mm strips; wipe the kelp; boil the water, kelp, second soy sauce, sugar, and sweet sauce over medium; add beef and vegetables and cook 10 minutes under a small inner lid; uncover and cook 10 minutes to remove moisture; plate and top with snow peas.
- Omissions and ambiguities: the live English page says to boil two snow peas for **30 minutes**. That unusually long value is retained verbatim and flagged, not corrected. Carrot preparation is absent even though carrot is added to the pot. Snow-pea boiling and cooling water quantities are absent. "Japanese sweet sauce" is not identified more precisely. No sensory doneness endpoint is given for the beef, potatoes, or reduction.
- Fidelity decisions: the official MAFF recipe replaced an initially considered secondary-source recipe. The two soy-sauce amounts remain separate. The missing carrot preparation stays visible. Optional rest/reheat wording is carried in the final serving action rather than made mandatory.
- YAML: `site/recipes/nikujaga.recipe.yaml`

## Aloo Posto

- Source: [Bong Eats — Alu Posto](https://www.bongeats.com/recipe/alu-posto)
- Source standing and access: culturally focused Bengali recipe publisher; the complete page, ingredient list, method, and serving suggestions were readable.
- Yield and timing evidence: five servings and 30 minutes cooking, although the first method step separately requires a two-hour poppy-seed soak.
- Ingredient evidence: 60 g mustard oil; 1/4 teaspoon nigella seeds; 2 dried red chillies; 25 g onion; 500 g potatoes; 50 g poppy seeds; 4 green chillies; 12 g salt; and 8 g sugar. The method additionally specifies 75 g grinding water, unquantified soaking water, and conditional splashes of hot water.
- Operation evidence: soak poppy seeds two hours; strain and grind with 2 green chillies and 75 g water to a coarse paste; peel and cut potatoes into 1 cm cubes; optionally slice and fry onion for about 1 minute; temper oil with dried chilli and nigella; fry potatoes about 5 minutes without browning; cook poppy paste, salt, and sugar on low about 4 minutes until its raw smell leaves; cover and cook until potatoes are soft, adding hot-water splashes only if dry; finish with 2 slit green chillies and 1 teaspoon mustard oil; optionally return the fried onion.
- Omissions and ambiguities: onion is displayed in the ingredient list but explicitly presented as a family variation. The 60 g oil supplies an exact 1-teaspoon finish plus cooking oil without a cross-unit allocation. Soaking water and conditional hot water are unquantified. The displayed 30-minute cooking time does not include the two-hour soak. Rice with dal or roti are serving suggestions without quantities or included recipes.
- Fidelity decisions: onion and its two uses remain optional. Green chillies split exactly 2 plus 2. One teaspoon oil is reserved without converting it to grams; the remainder stays unquantified. Conditional water remains optional.
- YAML: `site/recipes/aloo-posto.recipe.yaml`

## Jeera Aloo

- Source: [Sanjeev Kapoor — Jeera Aloo](https://www.sanjeevkapoor.com/Recipe/Jeera-Aloo.html)
- Source standing and access: named recipe by Sanjeev Kapoor; the complete live recipe card was readable.
- Yield and timing evidence: serves four; 11 to 15 minutes preparation; 16 to 20 minutes cooking.
- Ingredient evidence: 1 tablespoon plus 1 teaspoon cumin seeds; 4 medium boiled, peeled, cubed potatoes; 1 tablespoon coriander seeds; 1 tablespoon ghee (the source line says "1 tablespoons"); 1/2 teaspoon red chilli powder; 1 teaspoon dried mango powder; 1 teaspoon chaat masala; salt to taste; and 1 tablespoon chopped coriander leaves.
- Operation evidence: dry-roast 1 tablespoon cumin until golden and crush it; dry-roast coriander until fragrant and crush it; heat ghee, add the remaining 1 teaspoon cumin, and sauté 30 seconds; toss potatoes 2 to 3 minutes; add crushed spices and dry seasonings and cook another 2 to 3 minutes; turn off heat, drizzle some water, add chopped coriander, and toss; turn heat back on, cover, and cook 2 minutes; garnish with a coriander sprig and serve hot.
- Omissions and ambiguities: "some water" and the coriander garnish sprig appear only in the method. The water has no quantity. The listed chopped coriander is added before covering, so the differently prepared garnish sprig is treated as an additional unquantified method-only material. No heat level is stated.
- Fidelity decisions: the combined cumin line is split into the exact 1-tablespoon and 1-teaspoon uses. Roasting/crushing branches remain independent until seasoning. The ghee grammar typo survives in `source_text` but is normalized to 1 tablespoon in the human label.
- YAML: `site/recipes/jeera-aloo.recipe.yaml`

## Gamja Jorim

- Source: [Korean Bapsang — Gamja Jorim (Korean Braised Potatoes)](https://www.koreanbapsang.com/gamja-jorim-braised-potatoes/)
- Source standing and access: Korean home-cooking recipe by Hyosun Ro, updated 2025-04-02; the full article, recipe card, variation notes, and instructions were readable.
- Yield and timing evidence: four servings; 10 minutes preparation; 15 minutes cooking; 30 minutes total.
- Ingredient evidence: 1.5 lb potatoes (about 3 medium); 1 carrot (about 3 oz); 2 to 3 green chilli peppers or 1/2 green bell pepper; 1/4 medium onion; 1 tablespoon cooking oil. Braising liquid: 3 tablespoons soy sauce, or 2 tablespoons soy plus 1 tablespoon gochujang; 1 tablespoon sugar; 1 tablespoon optional rice wine or mirin; 1 tablespoon corn syrup or oligodang, or 1 extra tablespoon sugar; 1 teaspoon minced garlic; a pinch black pepper; 3/4 cup water. Finish: 1 teaspoon sesame oil and 1/2 teaspoon roasted sesame seeds.
- Operation evidence: leave potato skins on or peel, cube to about 1 inch, and briefly rinse and soak only if using starchy potatoes; cut chosen vegetables into large chunks; combine the braising liquid except sesame oil and seeds, adding 1–3 teaspoons gochugaru only if desired; sauté potatoes in oil over medium 4 to 5 minutes; add sauce and boil over high; add carrot, cover, reduce to medium, and cook about 5 to 6 minutes until potatoes are almost cooked yet firm; add pepper and onion and boil uncovered about 3 minutes until sauce is reduced and slightly thickened; stir in sesame oil and sprinkle sesame seeds.
- Omissions and ambiguities: the article says carrot, onion, and peppers are guidelines and the dish can be potatoes only. Multiple sauce substitutions are mutually exclusive. Rice wine may be omitted. Optional gochugaru is 1 to 3 teaspoons to taste. Starchy potatoes may be rinsed and briefly soaked, but that is not universal. Cook time varies by potato.
- Fidelity decisions: the graph uses the first-listed soy-sauce, rice-wine, corn-syrup, and green-chilli route. Rice wine, gochugaru, all guideline vegetables, skin-on preparation, and the starchy-potato rinse/soak remain visibly optional. Other substitutions stay explicit in recipe ambiguity instead of becoming simultaneous inputs.
- YAML: `site/recipes/gamja-jorim.recipe.yaml`

## Aloo Chop

- Source: [The Kitchn — Aloo Chop](https://www.thekitchn.com/aloo-chop-recipe-23221541)
- Source standing and access: Bangladeshi family recipe by Saida Chowdhury, published by The Kitchn; the complete article, card, notes, and make-ahead guidance were readable.
- Yield and timing evidence: about 10 pieces; 4 to 5 servings; 30 minutes preparation; 27 to 38 minutes cooking.
- Ingredient evidence: 1 1/4 lb russet potatoes (about 3 medium); 1/2 medium yellow onion; 3 to 4 small Indian green chillies; 1/2 cup cilantro leaves and tender stems; 2 teaspoons divided kosher salt; 1 teaspoon ground coriander; 1 large egg white; 1 teaspoon water; 1/3 cup plain fine breadcrumbs; 1/8 teaspoon black pepper; 3/4 cup canola oil.
- Operation evidence: peel and chop potatoes into 2-inch pieces; cover with cold water by about 2 inches, boil, and simmer 5 to 8 minutes until fork-tender; drain, cool, and rice or mash smooth; prepare onion, chillies, and cilantro; mix with potatoes, 1 3/4 teaspoons salt, and coriander while slightly mashing aromatics; whisk egg white and water until almost foamy; season breadcrumbs with the remaining 1/4 teaspoon salt and pepper; form 10 oblong 1/4-cup portions; egg-and-crumb coat, optionally double-coat with leftovers, and refrigerate at least 30 minutes or overnight; heat oil over medium until shimmering and crumbs gently bubble; fry uncrowded batches 5 to 7 minutes until golden all around, reducing heat if needed; transfer to paper towels.
- Omissions and ambiguities: potato-water volume is qualitative. Chilli count is a heat-dependent range. The optional second coating depends on unknown leftovers. The holding choice is refrigeration for at least 30 minutes or freezing for up to one month; refrigerated pieces fry over medium for 5–7 minutes, while frozen pieces fry directly from frozen over medium-low for 8–10 minutes.
- Fidelity decisions: salt is split exactly 1 3/4 plus 1/4 teaspoons. Both refrigerated and frozen holding/frying conditions remain visible in the graph. Parchment and paper-towel preparations remain setup prerequisites rather than food materials.
- YAML: `site/recipes/aloo-chop.recipe.yaml`

## Sambal Goreng Kentang

- Source: [Bango — Resep Sambal Goreng Kentang Enak Untuk Masakan Sehari-hari](https://www.bango.co.id/r/resep-sambal-goreng-kentang-enak-untuk-masakan-sehari-hari.html/257277)
- Source standing and access: Indonesian first-party recipe from Bango / Masak Apa Hari Ini; the full Indonesian article, card, and duplicated localized card were readable.
- Yield and timing evidence: four servings; 45 minutes.
- Ingredient evidence: 500 g cubed potatoes; 750 ml water; 1/2 teaspoon salt; 2 lemongrass stalks; 2 lime leaves; 2 cm galangal; 1 Indonesian bay leaf; 4 tablespoons thick coconut milk; 2 tablespoons Bango sweet soy sauce; a separate 1.5 teaspoons salt; 2 tablespoons fried shallots. Ground paste: 5 shallots, 3 garlic cloves, 3 large red chillies, 5 small red chillies, 1 cm galangal, and 1 cm ginger.
- Operation evidence: soak potatoes with water and first salt about 15 minutes; heat oil and fry until cooked and browned, with the article additionally specifying crispness; drain; blend the ground-paste ingredients smooth; sauté paste, lemongrass, galangal, lime leaf, and bay until fragrant, with the article additionally saying cooked/no longer raw and oil separated; add coconut milk, sweet soy, and second salt; add potatoes and mix evenly; sprinkle fried shallots and serve.
- Omissions and ambiguities: no oil appears in the displayed ingredient list even though potatoes are fried and the paste is sautéed. The source does not state oil amount, frying temperature, sauté temperature, or whether frying oil is reused. The two galangal amounts are separate. The card gives no duration after coconut milk or potatoes are added. A no-coconut-milk storage variation appears only in introductory advice.
- Fidelity decisions: separate unquantified method-only frying and sautéing oils avoid inventing reuse. Both galangal entries and both salts remain distinct. Sensory endpoints from the card and its adjacent preparation guidance are combined without importing external technique.
- YAML: `site/recipes/sambal-goreng-kentang.recipe.yaml`
