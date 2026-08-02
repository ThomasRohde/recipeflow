# Europe batch 3 research ledger

Retrieved and authored on 2026-08-02. This ledger follows the site policy: RecipeFlow text is paraphrased from the linked sources, while source quantities, temperatures, times, completion criteria, omissions, and ambiguities are preserved rather than normalized away.

## Bryndzové halušky — Slovakia

- Recipe: `site/recipes/bryndzove-halusky.recipe.yaml`
- Primary source: [Slovakia.travel — Bryndzové halušky](https://slovakia.travel/bryndzove-halusky)
- Source standing: Slovakia's official tourism portal; the page credits SACR.
- Evidence used: 700 g potatoes, 500 g semi-coarse flour, 50 g smoked bacon, 120 g sheep bryndza, salt; finely grate peeled potatoes; conditionally add water; press the firm dough into salted boiling water; cook 2–3 minutes after floating; fry finely diced bacon; mix hot unrinsed dumplings with bryndza and bacon drippings; loosen with 2–3 tablespoons cooking water only if too thick; finish with bacon and drippings.
- Omitted or ambiguous at source: no yield; no salt amount or allocation; no amount for conditional dough water; no boiling-water amount; no allocation of bacon drippings between the bryndza mixture and final pour-over.
- Fidelity notes: Buttermilk or sour milk is kept as an unquantified serving note, not invented as a graph input. Bacon drippings and cooking water are split explicitly so their reuse is visible.

## Cepelinai — Lithuania

- Recipe: `site/recipes/cepelinai.recipe.yaml`
- Primary source: [LRT — World Cepelinai Day: How make the “potato royalty” dish at home](https://www.lrt.lt/en/news-in-english/19/1337712/world-cepelinai-day-how-make-the-potato-royalty-dish-at-home)
- Source standing: English-language recipe published by Lithuania's national public broadcaster; credited to Justinas Šuliokas, LRT.lt.
- Evidence used: 20 raw potatoes, 10 boiled potatoes, one egg, 1 teaspoon each salt and black pepper, 500 g minced meat; grate and strain raw potatoes; mash boiled potatoes and combine; mix filling; use 15–20 g filling per oblong dumpling; form 25–30; boil 30–40 minutes without sticking; serve with sour cream and bacon bits.
- Omitted or ambiguous at source: no potato varieties or sizes; the 10 cooked potatoes enter already boiled; no meat type; no water quantity or cooking heat; no sour-cream or bacon-bit quantities; no instruction to recover settled potato starch from the strained liquid.
- Fidelity notes: The strained liquid is treated as waste because the source says to strain it off and gives it no later use. Sour cream and bacon bits remain unquantified rather than receiving guessed amounts.

## Rhodope Patatnik — Bulgaria

- Recipe: `site/recipes/patatnik.recipe.yaml`
- Primary source: [Bon Apeti — Родопски пататник](https://www.bonapeti.bg/recepti/rodopski-patatnik/)
- Source standing: Bulgarian culinary publisher Bon Apeti; recipe attributed to guest Nevena Raycheva of Pri Vodenitsata tavern and dated 2005-10-05.
- Evidence used: 1 kg potatoes, 100 g butter, 100 g Bulgarian white cheese, one onion, 5–6 fresh spearmint sprigs; dough of 200–220 g flour, 100 ml water, 1–2 tablespoons oil, and 1/2 tablespoon salt; roll wider than pan; grease and line with overhang; add grated-potato filling; fold edges over; pan-cook about 30 minutes, turn, then cook 15 minutes on the other side.
- Omitted or ambiguous at source: no yield, pan size/material, or heat level. Oil and salt are listed under the dough heading but are also called for in the pan/filling without allocation.
- Fidelity notes: This is explicitly labeled as the source's pastry-enclosed pan-cooked variant. The graph splits the listed oil and salt qualitatively across their documented uses without inventing sub-quantities. Other egg, cheese, bare-potato, and oven-baked regional variants are not merged into it.
- Access note: An official Visit Bulgaria PDF containing a Patatnik recipe was discoverable, but its live URL presented bot verification and its searchable extract was incomplete. The accessible, complete Bulgarian Bon Apeti source was therefore used for executable authoring.

## Rakott krumpli — Hungary

- Recipe: `site/recipes/rakott-krumpli.recipe.yaml`
- Primary source: [Lidl Konyha — Rakott krumpli](https://konyha.lidl.hu/recept/rakott-krumpli)
- Source standing: Native Hungarian recipe by chef Széll Tamás for Lidl Konyha.
- Evidence used: 15 eggs, 300 g paired dry sausage, 1.2 L 30% cream, 13 g salt, 10–12 large potatoes, three garlic cloves, 3–4 thyme sprigs; eggs exactly 3 minutes in boiling heavily salted water and 7 minutes off heat; cold-cool and peel; season cream; peel potatoes without wetting, slice 2 mm, dry; layer; bake at 110–140 °C for at least 2–3 hours until browned; cream should bubble by 40–50 minutes; rest 30 minutes.
- Omitted or ambiguous at source: no serving yield; the 13 g salt is not allocated between egg water and cream; egg-water and cooling-water quantities are absent; cream is poured “enough to cover,” so possible remainder is unresolved; the initial temperature within the range is not fixed.
- Fidelity notes: The unusual egg timing, dry potato handling, temperature range, bubbling checkpoint, and resting time are kept. No oven preheat was added because the source does not state one.

## Stoemp with carrots and leeks — Belgium

- Recipe: `site/recipes/stoemp.recipe.yaml`
- Primary source: [APAQ-W — Stoemp aux carottes et poireaux](https://www.apaqw.be/fr/stoemp-aux-carottes-et-poireaux)
- Source standing: Wallonia's public agency for promotion of quality agriculture.
- Evidence used: three medium carrots, two medium leeks, 1 kg tender-fleshed potatoes, 120 ml milk, two tablespoons butter, one tablespoon olive oil, nutmeg, salt, pepper; boil vegetables 15–20 minutes until tender; drain; coarsely mash while leaving pieces; mix in milk and butter; season; nutmeg optional; serve hot. Yield four.
- Omitted or ambiguous at source: no quantities for water, salt, pepper, or nutmeg; salt allocation between water and finish is absent; the listed tablespoon of olive oil never appears in the method.
- Fidelity notes: The olive oil is intentionally left unconsumed and marked optional because the complete method succeeds without it; this preserves the source inconsistency without silently assigning it a use. Suggested meat, Belgian sausage, fish, and fried egg accompaniments remain notes because the source gives no quantities and they are not part of the core method.

## Potato Skordalia — Greece

- Recipe: `site/recipes/skordalia.recipe.yaml`
- Primary source: [Akis Petretzikis — Σκορδαλιά](https://akispetretzikis.com/recipe/886/skordalia)
- Same-author cross-check: [Akis Petretzikis — Bakaliaros skordalia](https://akispetretzikis.com/en/recipe/898/mpakaliaros-skordalia)
- Source standing: Native Greek recipe from Greek chef Akis Petretzikis; the cross-check is another recipe on the same author's site.
- Evidence used from the standalone page: 750 g potatoes, 1 teaspoon coarse salt, 175 ml olive oil, three garlic cloves, 50 ml white-wine vinegar, salt, pepper; spring onion, 3–4 parsley sprigs, and olive oil to serve; drain potatoes, steam-dry 5 minutes, lightly mash, blend and add garlic dressing, adjust, garnish. Yield 1 kg.
- Cross-check evidence used: the standalone directions omit the sentence that puts and cooks the cut potatoes in the boiling water. The same author's related recipe explicitly boils the potatoes for 15–30 minutes until tender; that transition is used and disclosed in the YAML.
- Omitted or ambiguous at source: no water quantity; no fine-salt or pepper quantities or allocation; no amount for finishing olive oil. The standalone page's central boiling transition is missing.
- Fidelity notes: Ingredient quantities remain those of the standalone potato Skordalia, not the doubled quantities in the related cod-and-Skordalia page. Only the missing cooking transition and endpoint are borrowed, and that provenance is attached to the operation and source notes.
