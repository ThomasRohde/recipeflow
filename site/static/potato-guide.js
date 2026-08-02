document.documentElement.classList.add("has-js");

const countrySelect = document.querySelector("#country-select");
const countryStatus = document.querySelector("#country-status");
const countryCards = [...document.querySelectorAll("[data-country]")];
const countryNames = new Map(
  [...countrySelect.options].map((option) => [option.value, option.textContent.trim()]),
);

const languageCountries = [
  [/^da\b/i, "dk"],
  [/^sv\b/i, "se"],
  [/^nb\b|^nn\b|^no\b/i, "no"],
  [/^fi\b/i, "fi"],
  [/^de\b/i, "de"],
  [/^nl\b/i, "nl"],
  [/^fr\b/i, "fr"],
  [/^en-GB\b/i, "uk"],
  [/^en-IE\b/i, "ie"],
  [/^es\b|^pt\b/i, "es"],
  [/^it\b/i, "it"],
  [/^pl\b|^cs\b|^sk\b/i, "pl"],
  [/^en-AU\b|^en-NZ\b/i, "anz"],
  [/^en-US\b|^en-CA\b/i, "na"],
];

function countryFromLanguage() {
  for (const language of navigator.languages || [navigator.language]) {
    const match = languageCountries.find(([pattern]) => pattern.test(language));
    if (match) return match[1];
  }
  return "dk";
}

function setCountry(country, { updateUrl = true } = {}) {
  const validCountry = countryNames.has(country) ? country : "dk";
  countrySelect.value = validCountry;
  const showAll = validCountry === "all";
  countryCards.forEach((card) => {
    card.hidden = !showAll && card.dataset.country !== validCountry;
  });
  countryStatus.textContent = showAll
    ? `Showing all ${countryCards.length} regional buying guides.`
    : `Showing the ${countryNames.get(validCountry)} buying guide.`;
  localStorage.setItem("potato-guide-country", validCountry);
  if (updateUrl) {
    const url = new URL(window.location.href);
    url.searchParams.set("country", validCountry);
    window.history.replaceState({}, "", url);
  }
}

countrySelect.addEventListener("change", () => setCountry(countrySelect.value));

const requestedCountry = new URL(window.location.href).searchParams.get("country");
const savedCountry = localStorage.getItem("potato-guide-country");
setCountry(requestedCountry || savedCountry || countryFromLanguage(), { updateUrl: false });

const decoderTabs = [...document.querySelectorAll("[data-potato]")];
const decoderPanels = [...document.querySelectorAll("[data-potato-panel]")];

function selectPotato(potato) {
  decoderTabs.forEach((tab) => {
    const active = tab.dataset.potato === potato;
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
  });
  decoderPanels.forEach((panel) => {
    panel.hidden = panel.dataset.potatoPanel !== potato;
  });
}

decoderTabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectPotato(tab.dataset.potato));
  tab.addEventListener("keydown", (event) => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    const direction = event.key === 'ArrowRight' ? 1 : -1;
    const nextTab = decoderTabs[(index + direction + decoderTabs.length) % decoderTabs.length];
    selectPotato(nextTab.dataset.potato);
    nextTab.focus();
  });
});
