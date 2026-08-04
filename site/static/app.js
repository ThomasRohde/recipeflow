const state = {
  manifest: null,
  recipe: null,
  notation: localStorage.getItem("potato-index-notation") || "ledger",
  query: "",
  zoom: 0.8,
};

// Fetched sheet markup by `${slug}.${notation}`: a string once loaded, a Promise
// while in flight, false when this build does not carry the sheet.
const sheets = new Map();

const elements = {
  caret: document.querySelector(".carbon-caret"),
  image: document.querySelector("#recipe-image"),
  list: document.querySelector("#recipe-list"),
  search: document.querySelector("#recipe-search"),
  sheetScroll: document.querySelector("#diagram-scroll"),
  stage: document.querySelector("#sheet-stage"),
  steps: document.querySelector("#recipe-steps"),
  switch: document.querySelector("#notation-switch"),
  tagRow: document.querySelector("#tag-row"),
};

function text(id, value) {
  document.querySelector(`#${id}`).textContent = value || "";
}

function recipeFromHash() {
  const slug = window.location.hash.slice(1);
  return state.manifest.recipes.find((recipe) => recipe.slug === slug) || state.manifest.recipes[0];
}

function bandClass(recipe) {
  return recipe.band ? `pip-${recipe.band.code.toLowerCase()}` : "";
}

function renderRecipeList() {
  const query = state.query.trim().toLocaleLowerCase();
  const recipes = state.manifest.recipes.filter((recipe) => {
    const searchable = [recipe.title, recipe.description, recipe.yield, recipe.variety, recipe.origin, ...recipe.tags]
      .filter(Boolean)
      .join(" ")
      .toLocaleLowerCase();
    return searchable.includes(query);
  });

  text("recipe-results", query
    ? `${recipes.length} turned up · ${state.manifest.recipe_count} on the shelf`
    : `${state.manifest.recipe_count} crates open`);

  if (!recipes.length) {
    const item = document.createElement("li");
    item.className = "cellar-empty";
    item.textContent = "Nothing down here matches that.";
    elements.list.replaceChildren(item);
    return;
  }

  elements.list.replaceChildren(...recipes.map((recipe) => {
    const index = state.manifest.recipes.indexOf(recipe);
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = `#${recipe.slug}`;
    link.dataset.slug = recipe.slug;

    const number = document.createElement("span");
    number.className = "lot-number";
    number.textContent = String(index + 1).padStart(2, "0");

    const title = document.createElement("strong");
    title.textContent = recipe.title;

    const gauge = document.createElement("span");
    gauge.className = "lot-gauge";
    // Only lots with a texture reading get a gauge; an empty track would imply
    // a measurement that was never taken.
    if (recipe.band) {
      const track = document.createElement("span");
      track.className = "pip-track";
      const pip = document.createElement("span");
      pip.className = `pip ${bandClass(recipe)}`;
      pip.style.left = `${Math.round(recipe.band.position * 0.46)}px`;
      track.append(pip);
      gauge.append(track);
    }
    const tag = document.createElement("small");
    tag.textContent = recipe.tags[0] || "";
    gauge.append(tag);

    link.append(number, title, gauge);
    item.append(link);
    return item;
  }));
}

function renderNotationSwitch() {
  elements.switch.replaceChildren(...state.manifest.notations.map((notation, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.notation = notation.id;
    const number = document.createElement("span");
    number.textContent = `0${index + 1}`;
    button.append(number, document.createTextNode(notation.label));
    button.addEventListener("click", () => selectNotation(notation.id));
    return button;
  }));
}

function renderTags(tags) {
  elements.tagRow.replaceChildren(...tags.map((tag) => {
    const span = document.createElement("span");
    span.textContent = tag;
    return span;
  }));
}

function renderGrade(recipe) {
  const grade = document.querySelector("#texture-grade");
  if (!recipe.band) {
    grade.hidden = true;
    return;
  }
  grade.hidden = false;
  text("grade-headline", `Band ${recipe.band.code} — ${recipe.band.label}`);
  text("grade-bag", `Bag words to look for: ${recipe.band.bag}`);
  text("grade-note", recipe.band.note);
  document.querySelector("#grade-needle").style.left = `${recipe.band.position}%`;
}

function renderSteps(recipe) {
  elements.steps.replaceChildren(...recipe.steps.map((step, index) => {
    const item = document.createElement("li");
    if (step.kind === "setup") item.classList.add("is-setup");
    const number = document.createElement("span");
    number.className = "step-number";
    number.textContent = String(index + 1).padStart(2, "0");
    const body = document.createElement("span");
    body.className = "step-text";
    body.textContent = step.text;
    item.append(number, body);
    return item;
  }));
}

function setLinks(recipe, index) {
  const source = document.querySelector("#recipe-source");
  source.href = recipe.source.url;
  source.textContent = `${recipe.source.author || recipe.source.title || "Original source"} ↗`;
  text("recipe-source-title", recipe.source.title || "the source YAML");
  document.querySelector("#recipe-yaml").href = recipe.yaml;

  const recipes = state.manifest.recipes;
  const previous = recipes[(index - 1 + recipes.length) % recipes.length];
  const next = recipes[(index + 1) % recipes.length];
  const previousLink = document.querySelector("#previous-recipe");
  const nextLink = document.querySelector("#next-recipe");
  previousLink.href = `#${previous.slug}`;
  previousLink.querySelector(".crate-title").textContent = previous.title;
  nextLink.href = `#${next.slug}`;
  nextLink.querySelector(".crate-title").textContent = next.title;
}

function updateRecipeImage(recipe) {
  elements.image.classList.add("is-loading");
  elements.image.onload = () => elements.image.classList.remove("is-loading");
  elements.image.src = recipe.image.url;
  elements.image.alt = recipe.image.alt;
  text("recipe-image-caption", recipe.image.caption);
}

function updateActiveControls() {
  document.querySelectorAll("[data-slug]").forEach((link) => {
    const active = link.dataset.slug === state.recipe.slug;
    link.classList.toggle("is-active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  document.querySelectorAll("[data-notation]").forEach((button) => {
    const active = button.dataset.notation === state.notation;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  const notation = state.manifest.notations.find((item) => item.id === state.notation);
  text("view-description", notation ? notation.blurb : "");
}

/* The sheets are inlined rather than used as <img> so the catalogue's own inks
   reach the shapes inside them. The generated SVG carries a fixed width and
   height; both are dropped so the viewBox alone drives scaling. */
function prepareSheet(markup) {
  return markup
    .replace(/<metadata[\s\S]*?<\/metadata>/g, "")
    .replace(/^<svg([^>]*?)\swidth="[\d.]+"\sheight="[\d.]+"/, "<svg$1");
}

function loadSheet(recipe, notation) {
  const key = `${recipe.slug}.${notation}`;
  if (sheets.has(key)) {
    const cached = sheets.get(key);
    return cached instanceof Promise ? cached : Promise.resolve(cached);
  }
  const request = fetch(recipe.variants[notation].url)
    .then((response) => (response.ok ? response.text() : Promise.reject(response.status)))
    .then((markup) => {
      const prepared = prepareSheet(markup);
      sheets.set(key, prepared);
      return prepared;
    })
    .catch(() => {
      sheets.set(key, false);
      return false;
    });
  sheets.set(key, request);
  return request;
}

function captureSheetView() {
  const scroll = elements.sheetScroll;
  const maxX = Math.max(0, scroll.scrollWidth - scroll.clientWidth);
  const maxY = Math.max(0, scroll.scrollHeight - scroll.clientHeight);
  return {
    zoom: state.zoom,
    x: maxX ? scroll.scrollLeft / maxX : 0,
    y: maxY ? scroll.scrollTop / maxY : 0,
  };
}

function paintSheet({ viewState = null } = {}) {
  const recipe = state.recipe;
  const variant = recipe.variants[state.notation];
  const notation = state.manifest.notations.find((item) => item.id === state.notation);
  const markup = sheets.get(`${recipe.slug}.${state.notation}`);

  const scroll = elements.sheetScroll;
  if (typeof markup === "string") {
    elements.stage.innerHTML = markup;
    elements.stage.setAttribute("role", "img");
    elements.stage.setAttribute("aria-label", `${recipe.title} drawn in ${notation.label} notation`);
    if (viewState) {
      state.zoom = viewState.zoom;
      applyZoom();
      const maxX = Math.max(0, scroll.scrollWidth - scroll.clientWidth);
      const maxY = Math.max(0, scroll.scrollHeight - scroll.clientHeight);
      scroll.scrollLeft = viewState.x * maxX;
      scroll.scrollTop = viewState.y * maxY;
    } else {
      fitDiagram();
    }
  } else {
    const message = document.createElement("p");
    message.className = "sheet-pending";
    message.textContent = markup === false ? "Sheet not in this build" : "Unrolling the sheet…";
    elements.stage.replaceChildren(message);
    elements.stage.removeAttribute("role");
    elements.stage.removeAttribute("aria-label");
    elements.stage.style.width = "";
  }

  text("diagram-caption", `${recipe.title} · ${notation.label} · ${variant.width} × ${variant.height}`);
  const open = document.querySelector("#open-diagram");
  open.href = variant.url;
  open.textContent = `Open the full sheet ↗`;
}

function sheetIsPainted() {
  return elements.stage.querySelector("svg") !== null;
}

function applyZoom() {
  if (!sheetIsPainted()) return;
  const variant = state.recipe.variants[state.notation];
  elements.stage.style.width = `${Math.round(variant.width * state.zoom)}px`;
  text("zoom-level", `${Math.round(state.zoom * 100)}%`);
}

function fitDiagram({ allowBelowMinimum = false } = {}) {
  if (!sheetIsPainted()) return;
  const variant = state.recipe.variants[state.notation];
  const available = elements.sheetScroll.clientWidth - 40;
  const fitted = Math.min(1, available / variant.width);
  state.zoom = allowBelowMinimum ? fitted : Math.max(0.4, fitted);
  applyZoom();
  elements.sheetScroll.scrollTo({ left: 0, top: 0, behavior: "smooth" });
}

function selectNotation(notation) {
  if (!state.recipe.variants[notation] || notation === state.notation) return;
  const recipe = state.recipe;
  const viewState = captureSheetView();
  state.notation = notation;
  localStorage.setItem("potato-index-notation", notation);
  updateActiveControls();
  paintSheet();
  loadSheet(recipe, notation).then(() => {
    if (state.recipe.slug === recipe.slug && state.notation === notation) {
      paintSheet({ viewState });
    }
  });
}

function renderRecipe() {
  state.recipe = recipeFromHash();
  const recipe = state.recipe;
  const index = state.manifest.recipes.indexOf(recipe);

  text("lot-index", `Lot ${String(index + 1).padStart(2, "0")} / ${state.manifest.recipe_count}`);
  text("lot-origin", recipe.origin || "Origin not stated");
  text("recipe-yield", recipe.yield && recipe.yield !== "not stated"
    ? `Yield · ${recipe.yield}`
    : "Yield · not stated");
  text("recipe-title", recipe.title);
  text("recipe-description", recipe.description);
  text("recipe-variety", recipe.variety || "Not stated — the source names no variety");
  text("recipe-text", recipe.text);

  renderTags(recipe.tags);
  renderGrade(recipe);
  renderSteps(recipe);
  setLinks(recipe, index);
  updateRecipeImage(recipe);
  updateActiveControls();
  const notation = state.notation;
  loadSheet(recipe, notation).then(() => {
    if (state.recipe.slug === recipe.slug && state.notation === notation) paintSheet();
  });
  paintSheet();

  document.title = `${recipe.title} · Potato Index`;
}

async function start() {
  const response = await fetch("recipes.json");
  if (!response.ok) throw new Error(`Could not load recipes (${response.status})`);
  state.manifest = await response.json();

  const count = state.manifest.recipe_count;
  text("masthead-note", `One ingredient. ${count} arguments about what to do with it — each one drawn, audited, and traced back to whoever said it first.`);
  text("docket-count", `Net wt. ${count} recipes`);
  text("cellar-footnote", `${count} lots are unpacked in this build. Each one is drawn three ways from the same published YAML.`);

  if (!state.manifest.notations.some((item) => item.id === state.notation)) {
    state.notation = "flow";
  }

  renderRecipeList();
  renderNotationSwitch();
  renderRecipe();
}

elements.search.addEventListener("input", (event) => {
  state.query = event.target.value;
  renderRecipeList();
  updateActiveControls();
});

document.querySelector("#zoom-in").addEventListener("click", () => {
  state.zoom = Math.min(1.8, state.zoom + 0.1);
  applyZoom();
});
document.querySelector("#zoom-out").addEventListener("click", () => {
  state.zoom = Math.max(0.1, state.zoom - 0.1);
  applyZoom();
});
document.querySelector("#zoom-fit").addEventListener("click", () => {
  fitDiagram({ allowBelowMinimum: true });
});

window.addEventListener("hashchange", renderRecipe);
window.addEventListener("resize", () => {
  if (state.zoom < 1) fitDiagram();
});

start().catch((error) => {
  text("recipe-title", "The cellar door is stuck");
  text("recipe-description", error.message);
  console.error(error);
});
