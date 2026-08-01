const notationCopy = {
  flow: "Flow follows ingredients across time.",
  "compact-table": "Compact Table compresses the route into a nested ingredient grid.",
  ledger: "Kitchen Ledger audits every entry: what came in, what happened, and what came out.",
};

const state = {
  manifest: null,
  recipe: null,
  notation: localStorage.getItem("potato-index-notation") || "flow",
  zoom: 1,
};

const elements = {
  diagram: document.querySelector("#recipe-diagram"),
  diagramScroll: document.querySelector("#diagram-scroll"),
  list: document.querySelector("#recipe-list"),
  switch: document.querySelector("#notation-switch"),
};

function text(id, value) {
  document.querySelector(`#${id}`).textContent = value || "";
}

function recipeFromHash() {
  const slug = window.location.hash.slice(1);
  return state.manifest.recipes.find((recipe) => recipe.slug === slug) || state.manifest.recipes[0];
}

function ingredientText(ingredient) {
  const quantity = ingredient.quantity ? `${ingredient.quantity} ` : "";
  const optional = ingredient.optional ? " (optional)" : "";
  return `${quantity}${ingredient.label}${optional}`;
}

function operationText(operation) {
  const inputs = operation.inputs.map((input) => {
    const quantity = input.quantity ? `${input.quantity} ` : "";
    return `${quantity}${input.label}`;
  });
  const conditions = [operation.duration, operation.temperature, operation.until].filter(Boolean);
  const source = inputs.length ? `${inputs.join(", ")} → ` : "";
  const detail = conditions.length ? ` · ${conditions.join(" · ")}` : "";
  return `${source}${operation.action} → ${operation.outputs.join(", ")}${detail}`;
}

function renderRecipeList() {
  elements.list.replaceChildren(...state.manifest.recipes.map((recipe, index) => {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = `#${recipe.slug}`;
    link.dataset.slug = recipe.slug;
    link.innerHTML = `<span>${String(index + 1).padStart(2, "0")}</span><strong>${recipe.title}</strong><small>${recipe.tags[1] || recipe.tags[0]}</small>`;
    item.append(link);
    return item;
  }));
}

function renderNotationSwitch() {
  elements.switch.replaceChildren(...state.manifest.notations.map((notation, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.notation = notation.id;
    button.innerHTML = `<span>0${index + 1}</span>${notation.label}`;
    button.addEventListener("click", () => selectNotation(notation.id));
    return button;
  }));
}

function renderTags(tags) {
  const row = document.querySelector("#tag-row");
  row.replaceChildren(...tags.map((tag) => {
    const span = document.createElement("span");
    span.textContent = tag;
    return span;
  }));
}

function setLinks(recipe, index) {
  const source = document.querySelector("#recipe-source");
  source.href = recipe.source.url;
  source.textContent = `${recipe.source.author || recipe.source.title || "Original source"} ↗`;
  document.querySelector("#recipe-yaml").href = recipe.yaml;
  const previous = state.manifest.recipes[(index - 1 + state.manifest.recipes.length) % state.manifest.recipes.length];
  const next = state.manifest.recipes[(index + 1) % state.manifest.recipes.length];
  document.querySelector("#previous-recipe").href = `#${previous.slug}`;
  document.querySelector("#previous-recipe").textContent = `← ${previous.title}`;
  document.querySelector("#next-recipe").href = `#${next.slug}`;
  document.querySelector("#next-recipe").textContent = `${next.title} →`;
}

function renderTextRecipe(recipe) {
  const ingredients = recipe.ingredients.map((ingredient) => {
    const item = document.createElement("li");
    item.textContent = ingredientText(ingredient);
    return item;
  });
  document.querySelector("#ingredient-list").replaceChildren(...ingredients);

  const setup = recipe.setup.map((operation) => ({
    action: `Setup: ${operation.action}${operation.target ? ` ${operation.target}` : ""}`,
    inputs: [],
    outputs: ["ready"],
    duration: operation.duration,
    temperature: operation.temperature,
    until: null,
  }));
  const operations = [...setup, ...recipe.operations].map((operation) => {
    const item = document.createElement("li");
    item.textContent = operationText(operation);
    return item;
  });
  document.querySelector("#operation-list").replaceChildren(...operations);
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
  text("view-description", notationCopy[state.notation]);
}

function applyZoom() {
  if (!elements.diagram.naturalWidth) return;
  elements.diagram.style.width = `${Math.round(elements.diagram.naturalWidth * state.zoom)}px`;
  text("zoom-level", `${Math.round(state.zoom * 100)}%`);
}

function fitDiagram() {
  if (!elements.diagram.naturalWidth) return;
  const available = elements.diagramScroll.clientWidth - 32;
  state.zoom = Math.max(0.62, Math.min(1, available / elements.diagram.naturalWidth));
  applyZoom();
  elements.diagramScroll.scrollTo({ left: 0, top: 0, behavior: "smooth" });
}

function updateDiagram({ preservePosition = false } = {}) {
  const variant = state.recipe.variants[state.notation];
  const oldX = elements.diagramScroll.scrollWidth > 0
    ? elements.diagramScroll.scrollLeft / elements.diagramScroll.scrollWidth : 0;
  const oldY = elements.diagramScroll.scrollHeight > 0
    ? elements.diagramScroll.scrollTop / elements.diagramScroll.scrollHeight : 0;
  elements.diagram.classList.add("is-loading");
  elements.diagram.onload = () => {
    elements.diagram.classList.remove("is-loading");
    if (preservePosition) {
      applyZoom();
      elements.diagramScroll.scrollLeft = oldX * elements.diagramScroll.scrollWidth;
      elements.diagramScroll.scrollTop = oldY * elements.diagramScroll.scrollHeight;
    } else {
      fitDiagram();
    }
  };
  elements.diagram.src = variant.url;
  elements.diagram.alt = `${state.recipe.title} in ${variant.label} notation`;
  text("diagram-caption", `${state.recipe.title} · ${variant.label} · ${variant.width} × ${variant.height}`);
  const open = document.querySelector("#open-diagram");
  open.href = variant.url;
  open.textContent = `Open ${variant.label} SVG ↗`;
}

function selectNotation(notation) {
  if (!state.recipe.variants[notation] || notation === state.notation) return;
  state.notation = notation;
  localStorage.setItem("potato-index-notation", notation);
  updateActiveControls();
  updateDiagram({ preservePosition: true });
}

function renderRecipe() {
  state.recipe = recipeFromHash();
  const index = state.manifest.recipes.indexOf(state.recipe);
  text("recipe-index", `${String(index + 1).padStart(2, "0")} / ${String(state.manifest.recipe_count).padStart(2, "0")}`);
  text("recipe-title", state.recipe.title);
  text("recipe-description", state.recipe.description);
  text("recipe-yield", state.recipe.yield ? `Yield · ${state.recipe.yield}` : "");
  renderTags(state.recipe.tags);
  setLinks(state.recipe, index);
  renderTextRecipe(state.recipe);
  updateActiveControls();
  updateDiagram();
  document.title = `${state.recipe.title} · Potato Index`;
}

async function start() {
  const response = await fetch("recipes.json");
  if (!response.ok) throw new Error(`Could not load recipes (${response.status})`);
  state.manifest = await response.json();
  if (!state.manifest.notations.some((item) => item.id === state.notation)) {
    state.notation = "flow";
  }
  renderRecipeList();
  renderNotationSwitch();
  renderRecipe();
}

document.querySelector("#zoom-in").addEventListener("click", () => {
  state.zoom = Math.min(1.8, state.zoom + 0.1);
  applyZoom();
});
document.querySelector("#zoom-out").addEventListener("click", () => {
  state.zoom = Math.max(0.4, state.zoom - 0.1);
  applyZoom();
});
document.querySelector("#zoom-fit").addEventListener("click", fitDiagram);
window.addEventListener("hashchange", renderRecipe);
window.addEventListener("resize", () => {
  if (state.zoom < 1) fitDiagram();
});

start().catch((error) => {
  text("recipe-title", "The cellar door is stuck");
  text("recipe-description", error.message);
  console.error(error);
});
