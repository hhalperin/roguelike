/* Spire — interactive demo logic.
   Vanilla, no build. A small state machine drives nine facets that follow the
   format contracts under ../formats/. Content is illustrative (a Defect-class
   sample run); nothing here wires to the real engine. */
(function () {
  "use strict";

  /* ------------------------------ content ------------------------------ */
  var SOFT_CAP = 12;

  function freshNodes() {
    return [
      { id: "n0", kind: "combat", enemy: "bug", label: "bug", shape: "circle", done: true, reachable: false },
      { id: "n1", kind: "unknown", label: "?", shape: "diamond", done: false, reachable: true },
      { id: "n2", kind: "campfire", label: "rest", shape: "camp", done: false, reachable: false },
      { id: "n3", kind: "combat", enemy: "feat", label: "feat", shape: "circle", done: false, reachable: false },
      { id: "n4", kind: "event", label: "?", shape: "diamond", done: false, reachable: false },
      { id: "n5", kind: "shop", label: "shop", shape: "hex", done: false, reachable: false },
      { id: "n6", kind: "boss", enemy: "boss", label: "boss", shape: "boss", done: false, reachable: false }
    ];
  }

  var ENEMIES = {
    bug: {
      name: "Flaky Suite", kind: "Elite · bug room", room: "bug",
      intent: "Will fail CI randomly if ignored.",
      blurb: "Clear by stabilizing the suite — not by quarantining tests.",
      acceptance: "python -m pytest -q  →  exit 0",
      telegraph: "Telegraph: CI roulette", turnEffect: "Flaky Suite reshuffles — a red test blinks green.",
      maxHp: 3
    },
    feat: {
      name: "Scope Creep", kind: "Feature room", room: "feat",
      intent: "Will expand the PR until acceptance is undefined.",
      blurb: "Clear by shipping a vertical slice with a written Done.",
      acceptance: "PR open + checklist green  →  exit 0",
      telegraph: "Telegraph: one more must-have", turnEffect: "Scope Creep whispers 'just one more field'.",
      maxHp: 3
    },
    boss: {
      name: "Unclear Requirements", kind: "Act I boss", room: "boss",
      intent: "Will block ship until someone owns the decision.",
      blurb: "Clear by recording a decision and a spike outcome.",
      acceptance: "decision.md committed  →  exit 0",
      telegraph: "Telegraph: move the goalposts", turnEffect: "The goalposts slide two feet to the left.",
      maxHp: 4
    }
  };

  // Cards carry a room filter, energy cost, and progress (damage) toward clear.
  var ALL_CARDS = [
    { id: "c-ftf", cost: 1, title: "Failing Test First", body: "Pin the flake with a red test.", rooms: ["bug", "boss"], progress: 2, rarity: "common" },
    { id: "c-char", cost: 1, title: "Characterization", body: "Lock current behavior in a test.", rooms: ["bug", "feat", "boss"], progress: 1, rarity: "common" },
    { id: "c-slice", cost: 2, title: "Vertical Slice", body: "Ship one thin end-to-end path.", rooms: ["feat", "boss"], progress: 2, rarity: "uncommon" },
    { id: "c-decide", cost: 1, title: "Record Decision", body: "Write the call + the spike outcome.", rooms: ["boss"], progress: 2, rarity: "uncommon" },
    { id: "c-accept", cost: 0, title: "Run Acceptance", body: "Execute the room's checks.", rooms: ["bug", "feat", "boss"], progress: 0, rarity: "common", isAccept: true }
  ];

  var OFFERS = [
    { id: "o1", title: "Quarantine Test", rarity: "rare", note: "Rare · often a trap" },
    { id: "o2", title: "Retry Gate", rarity: "uncommon", note: "Uncommon" },
    { id: "o3", title: "Flake Journal", rarity: "common", note: "Common" }
  ];

  var WARES = [
    { id: "w1", title: "Characterization", kind: "card", price: 2 },
    { id: "w2", title: "Failing Test First", kind: "card", price: 2 },
    { id: "w3", title: "Coverage Floor", kind: "relic", price: 3 }
  ];

  var EVENT = {
    title: "Just One More Requirement",
    body: "A stakeholder adds a “tiny” must-have before ship. Accepting expands this feature room into an elite.",
    choices: [
      { id: "accept", label: "Accept scope", consequence: "Gain Bloated Scope curse.", greedy: true },
      { id: "cut", label: "Cut scope", consequence: "Requires a Cut Scope card." },
      { id: "park", label: "Park in backlog", consequence: "Log it and leave — no curse." }
    ]
  };

  var ASCENSION = [
    { level: 0, blurb: "Warn only. A0 is always available." },
    { level: 5, blurb: "Lint can block Stop." },
    { level: 10, blurb: "Lint and tests can block Stop. Coverage not yet enforced. Ascension only moves when you apply." },
    { level: 15, blurb: "Coverage regressions can block Stop." },
    { level: 20, blurb: "Every room requires review evidence." }
  ];

  var PRIORS = [
    "Prior bias: bug 36% · feature 22% · refactor 16%",
    "Prior bias: feature 41% · bug 19% · chore 14%",
    "Prior bias: refactor 28% · bug 27% · feature 21%"
  ];

  function freshDeck() {
    return [
      { id: "d1", name: "orient", plays: 0, when: "floor 0" },
      { id: "d2", name: "add-endpoint", plays: 0, when: "floor 0" },
      { id: "d3", name: "run-tests", plays: 4, when: "today" },
      { id: "d4", name: "characterization", plays: 1, when: "floor 2" }
    ];
  }

  /* ------------------------------ state ------------------------------ */
  var DEFAULTS = {
    screen: "title", returnScreen: "map",
    act: "I", floor: 3, streak: 2, deckSize: 6, tokens: 4, taken: 1, skips: 4,
    ascension: 10, ascPick: 10,
    selectedNodeId: null, priorSeed: 0,
    currentEnemy: "bug", enemyHp: 0, energy: 3, energyMax: 3, playedThisTurn: [],
    campMode: "prune", pruneId: null, shopId: null,
    theme: "light"
  };

  var state, NODES, DECK;

  function resetState(hard) {
    state = Object.assign({}, DEFAULTS);
    NODES = freshNodes();
    DECK = freshDeck();
    if (hard) {
      // full "reset run" returns to a mid-run save snapshot
      NODES[0].done = true;
      NODES[0].reachable = false;
      NODES[1].reachable = true;
    }
  }

  /* ------------------------------ elements ------------------------------ */
  var $ = function (id) { return document.getElementById(id); };
  var els = {};

  /* ------------------------------ helpers ------------------------------ */
  var toastTimer = null;
  function toast(msg) {
    els.toast.textContent = msg;
    els.toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { els.toast.classList.remove("show"); }, 1900);
  }

  function orbRow(container, n, max) {
    container.innerHTML = "";
    for (var i = 0; i < max; i++) {
      var o = document.createElement("span");
      o.className = "orb" + (i < n ? "" : " spent");
      container.appendChild(o);
    }
  }

  function bindStats() {
    var map = {
      floor: state.floor, deck: state.deckSize, streak: state.streak,
      tokens: state.tokens, taken: state.taken, skips: state.skips
    };
    document.querySelectorAll("[data-bind]").forEach(function (el) {
      el.textContent = String(map[el.getAttribute("data-bind")]);
    });
    $("chrome-act").textContent = state.act;
    $("chrome-floor").textContent = String(state.floor);
    $("chrome-streak").textContent = String(state.streak);
    $("chrome-asc").textContent = String(state.ascension);
  }

  var LABELS = {
    title: "Title", map: "Map", intent: "Intent", combat: "Combat", event: "Event",
    reward: "Reward", campfire: "Campfire", shop: "Shop", ascension: "Ascension"
  };

  function selectedNode() {
    for (var i = 0; i < NODES.length; i++) if (NODES[i].id === state.selectedNodeId) return NODES[i];
    return null;
  }

  function advanceReachable() {
    var found = false;
    for (var i = 0; i < NODES.length; i++) {
      NODES[i].reachable = false;
      if (!NODES[i].done && !found) { NODES[i].reachable = true; found = true; }
    }
  }

  /* ------------------------------ screen switch ------------------------------ */
  function showScreen(name) {
    state.screen = name;
    document.querySelectorAll(".screen").forEach(function (s) {
      s.classList.toggle("is-active", s.getAttribute("data-screen") === name);
    });
    var active = document.querySelector('.screen[data-screen="' + name + '"]');
    if (active) {
      var facet = getComputedStyle(active).getPropertyValue("--facet-" + active.getAttribute("data-facet")).trim();
      document.documentElement.style.setProperty("--facet", facet || "var(--facet-map)");
    }

    // chrome + banner
    els.chrome.hidden = name === "title";
    var inRoom = name === "intent" || name === "combat";
    els.chromeEnergy.hidden = name !== "combat";
    var roomActive = inRoom;
    els.banner.hidden = !roomActive;
    if (roomActive) renderBanner(name);

    // nav highlight
    document.querySelectorAll(".jump-btn").forEach(function (b) {
      b.classList.toggle("is-current", b.getAttribute("data-go") === name);
    });

    bindStats();
    render();
  }

  function renderBanner(name) {
    var enemy = ENEMIES[state.currentEnemy];
    els.bannerText.textContent = "ROOM ACTIVE: " + enemy.name + " · " + enemy.room;
    els.bannerActions.innerHTML = "";
    if (name === "intent") {
      var ret = document.createElement("a");
      ret.textContent = "Return";
      ret.setAttribute("role", "button");
      ret.tabIndex = 0;
      ret.addEventListener("click", function () { showScreen("combat"); });
      els.bannerActions.appendChild(ret);
    } else {
      var span = document.createElement("span");
      span.className = "hint";
      span.textContent = "Energy locked to this room";
      els.bannerActions.appendChild(span);
    }
    var flee = document.createElement("a");
    flee.className = "flee-link";
    flee.textContent = "Flee…";
    flee.setAttribute("role", "button");
    flee.tabIndex = 0;
    flee.addEventListener("click", doFlee);
    els.bannerActions.appendChild(flee);
  }

  /* ------------------------------ renderers ------------------------------ */
  function render() {
    bindStats();
    switch (state.screen) {
      case "map": renderMap(); break;
      case "intent": renderIntent(); break;
      case "combat": renderCombat(); break;
      case "event": renderEvent(); break;
      case "reward": renderReward(); break;
      case "campfire": renderCamp(); break;
      case "shop": renderShop(); break;
      case "ascension": renderAscension(); break;
    }
  }

  function renderMap() {
    els.mapGraph.innerHTML = "";
    NODES.forEach(function (node, idx) {
      if (idx > 0) {
        var seg = document.createElement("div");
        seg.className = "map-seg";
        var link = document.createElement("div");
        link.className = "map-link" + (NODES[idx - 1].done ? " lit" : "");
        seg.appendChild(link);
        els.mapGraph.appendChild(seg);
      }
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "node " + node.shape;
      if (node.done) btn.classList.add("done");
      if (node.reachable) btn.classList.add("reachable");
      if (node.id === state.selectedNodeId) btn.classList.add("selected");
      btn.disabled = !node.reachable;
      btn.setAttribute("aria-label", node.kind + (node.reachable ? " (reachable)" : ""));
      btn.setAttribute("aria-pressed", node.id === state.selectedNodeId ? "true" : "false");
      if (node.shape === "diamond") {
        var s = document.createElement("span");
        s.textContent = node.label;
        btn.appendChild(s);
      } else {
        btn.textContent = node.label;
      }
      btn.addEventListener("click", function () {
        state.selectedNodeId = node.id;
        renderMap();
        updateMapDetail();
      });
      els.mapGraph.appendChild(btn);
    });
    updateMapDetail();
  }

  function updateMapDetail() {
    var node = selectedNode();
    els.enter.disabled = !node || !node.reachable;
    if (!node) {
      $("map-kind").textContent = "—";
      $("map-title").innerHTML = "<strong>Pick a node</strong>";
      $("map-prior").textContent = "";
      return;
    }
    $("map-kind").textContent = node.kind === "unknown" ? "?" : node.kind;
    var titles = {
      combat: node.enemy === "feat" ? "Feature room" : "Bug room",
      unknown: "Unknown node", campfire: "Campfire", event: "Event node",
      shop: "Shop", boss: "Act boss"
    };
    $("map-title").innerHTML = "<strong>" + (titles[node.kind] || node.kind) + "</strong>";
    $("map-prior").textContent = node.kind === "unknown"
      ? PRIORS[state.priorSeed % PRIORS.length]
      : "Reachable · enter to open the room.";
  }

  function renderIntent() {
    var e = ENEMIES[state.currentEnemy];
    $("intent-kind").textContent = e.kind;
    $("intent-name").textContent = e.name;
    $("intent-text").textContent = e.intent;
    $("intent-blurb").textContent = e.blurb;
    $("intent-acceptance").textContent = e.acceptance;
  }

  function legalCards() {
    var room = ENEMIES[state.currentEnemy].room;
    return ALL_CARDS.filter(function (c) { return !c.isAccept; }).map(function (c) {
      return { card: c, legal: c.rooms.indexOf(room) !== -1 };
    });
  }

  function renderCombat() {
    var e = ENEMIES[state.currentEnemy];
    $("combat-name").textContent = e.name;
    $("combat-telegraph").textContent = e.telegraph;
    var pct = Math.max(0, Math.min(100, Math.round((state.enemyHp / e.maxHp) * 100)));
    $("combat-hp-fill").style.width = pct + "%";
    $("combat-hp-text").textContent = "Stability " + (e.maxHp - state.enemyHp) + " / " + e.maxHp;
    orbRow(els.combatOrbs, state.energy, state.energyMax);
    orbRow(els.chromeOrbs, state.energy, state.energyMax);

    var cards = legalCards();
    var n = cards.length;
    els.combatHand.innerHTML = "";
    cards.forEach(function (entry, i) {
      var c = entry.card;
      var played = state.playedThisTurn.indexOf(c.id) !== -1;
      var costly = state.energy < c.cost;
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "play-card " + c.rarity;
      if (!entry.legal) btn.classList.add("illegal");
      if (costly && entry.legal) btn.classList.add("too-costly");
      btn.disabled = played || !entry.legal || costly;
      // fan geometry
      var mid = (n - 1) / 2;
      var rot = (i - mid) * 6;
      var ty = Math.abs(i - mid) * 8;
      btn.style.setProperty("--rot", rot + "deg");
      btn.style.setProperty("--ty", ty + "px");
      var reason = !entry.legal ? "Illegal here · " + c.rooms.join("/") + " only"
        : costly ? "Needs " + c.cost + " energy" : c.rooms.join(" · ");
      btn.innerHTML =
        '<span class="cost">' + c.cost + "</span>" +
        '<span class="notch" aria-hidden="true"></span>' +
        "<h4>" + c.title + "</h4>" +
        '<div class="body">' + c.body + "</div>" +
        '<div class="rtype">' + reason + "</div>";
      if (!btn.disabled) {
        btn.addEventListener("click", function () { playCard(c, btn); });
      }
      els.combatHand.appendChild(btn);
    });
  }

  function playCard(c, btn) {
    if (state.energy < c.cost) return;
    state.energy -= c.cost;
    state.playedThisTurn.push(c.id);
    state.enemyHp = Math.min(ENEMIES[state.currentEnemy].maxHp, state.enemyHp + c.progress);
    btn.classList.add("committing");
    $("combat-log").textContent = "Log: played " + c.title + " (+" + c.progress + " progress)";
    var remaining = ENEMIES[state.currentEnemy].maxHp - state.enemyHp;
    setTimeout(function () {
      renderCombat();
      if (remaining <= 0) toast("Room stabilized — run acceptance");
    }, 320);
  }

  function renderEvent() {
    $("event-title").textContent = EVENT.title;
    $("event-body").textContent = EVENT.body;
    els.eventChoices.innerHTML = "";
    EVENT.choices.forEach(function (ch) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "choice" + (ch.greedy ? " greedy" : "");
      btn.innerHTML = '<span class="c-label">' + ch.label + "</span>" +
        '<span class="c-consequence">' + ch.consequence + "</span>";
      btn.addEventListener("click", function () { resolveEvent(ch); });
      els.eventChoices.appendChild(btn);
    });
  }

  function resolveEvent(ch) {
    if (ch.id === "accept") toast("Bloated Scope curse · logged");
    else if (ch.id === "cut") toast("Cut scope · slice preserved");
    else toast("Parked in backlog");
    completeNode("map");
  }

  function renderReward() {
    els.rewardOffers.innerHTML = "";
    OFFERS.forEach(function (o) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "offer " + o.rarity;
      btn.innerHTML = '<span class="notch" aria-hidden="true"></span>' +
        "<h4>" + o.title + "</h4><span class='rarity'>" + o.note + "</span>";
      btn.addEventListener("click", function () {
        state.taken += 1;
        state.deckSize += 1;
        if (state.deckSize > SOFT_CAP) toast("Over soft cap — prune at a campfire");
        else toast("Took " + o.title);
        completeNode("map");
      });
      els.rewardOffers.appendChild(btn);
    });
    $("reward-caption").innerHTML = "Run stats · taken <span>" + state.taken +
      "</span> / skipped <span>" + state.skips + "</span> · deck <span>" +
      state.deckSize + "</span>/" + SOFT_CAP;
  }

  function renderCamp() {
    var sorted = DECK.slice().sort(function (a, b) { return a.plays - b.plays; });
    els.campList.innerHTML = "";
    sorted.forEach(function (card) {
      var row = document.createElement("button");
      row.type = "button";
      row.className = "deck-row" + (state.pruneId === card.id ? " selected" : "");
      row.disabled = state.campMode !== "prune";
      var unplayed = card.plays === 0;
      row.innerHTML = "<span>" + card.name + "</span>" +
        '<span class="meta ' + (unplayed ? "unplayed" : "") + '">' +
        (unplayed ? "unplayed · " : "") + card.plays + " plays · " + card.when + "</span>";
      if (state.campMode === "prune") {
        row.addEventListener("click", function () {
          state.pruneId = card.id;
          renderCamp();
        });
      }
      els.campList.appendChild(row);
    });
    els.campConfirm.disabled = !(state.campMode === "prune" && state.pruneId);
    var hints = {
      prune: "Burn dead weight. Unplayed cards sort first.",
      upgrade: "Upgrade is a v0 stub — pick Prune or Rest to act.",
      rest: "Rest clears the room and heals energy flavor."
    };
    $("camp-hint").textContent = hints[state.campMode];
    els.campConfirm.hidden = state.campMode !== "prune";
  }

  function renderShop() {
    els.shopWares.innerHTML = "";
    WARES.forEach(function (w) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ware" + (state.shopId === w.id ? " selected" : "");
      btn.innerHTML = '<span class="price">' + w.price + "</span>" +
        '<span class="kind">' + w.kind + "</span>" +
        "<h4>" + w.title + "</h4>";
      btn.addEventListener("click", function () {
        state.shopId = w.id;
        renderShop();
      });
      els.shopWares.appendChild(btn);
    });
    els.buy.disabled = !state.shopId;
  }

  function renderAscension() {
    els.ascLadder.innerHTML = "";
    ASCENSION.forEach(function (r) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "rung" + (r.level === state.ascPick ? " picked" : "");
      btn.innerHTML = '<span class="tier">A' + r.level + "</span>" +
        "<span>" + shortAsc(r.level) + "</span>" +
        (r.level === state.ascension ? '<span class="applied-tag">applied</span>' : "");
      btn.addEventListener("click", function () {
        state.ascPick = r.level;
        renderAscension();
      });
      els.ascLadder.appendChild(btn);
    });
    var picked = ASCENSION.filter(function (r) { return r.level === state.ascPick; })[0] || ASCENSION[2];
    $("asc-label").textContent = "A" + picked.level;
    $("asc-blurb").textContent = picked.blurb;
    els.applyAsc.textContent = "Apply A" + picked.level;
  }

  function shortAsc(level) {
    return {
      0: "warn only", 5: "lint blocks", 10: "+ tests block",
      15: "+ coverage regression", 20: "every room reviewed"
    }[level];
  }

  /* ------------------------------ transitions ------------------------------ */
  function completeNode(next) {
    var node = selectedNode();
    if (node) { node.done = true; node.reachable = false; }
    state.selectedNodeId = null;
    state.floor += 1;
    state.streak += 1;
    advanceReachable();
    showScreen(next || "map");
  }

  function beginCombat() {
    state.energy = state.energyMax;
    state.playedThisTurn = [];
    // enemyHp starts at 0 progress (set on enter); keep if already progressing
    $("combat-log").textContent = "Log: combat begun · hand filtered to room";
  }

  function enterNode() {
    var node = selectedNode();
    if (!node || !node.reachable) return;
    if (node.kind === "combat" || node.kind === "boss" || node.kind === "unknown") {
      if (node.kind === "unknown") {
        var roll = ["bug", "feat", "bug"][state.priorSeed % 3];
        state.currentEnemy = roll;
        toast("Unknown resolved · " + ENEMIES[roll].name);
      } else {
        state.currentEnemy = node.enemy;
      }
      state.enemyHp = 0;
      state.energy = state.energyMax;
      state.playedThisTurn = [];
      showScreen("intent");
      return;
    }
    if (node.kind === "event") { showScreen("event"); return; }
    if (node.kind === "campfire") {
      state.campMode = "prune"; state.pruneId = null;
      syncCampModeButtons();
      showScreen("campfire"); return;
    }
    if (node.kind === "shop") { state.shopId = null; showScreen("shop"); }
  }

  function doFlee() {
    toast("Fled · streak broken");
    state.streak = Math.max(0, state.streak - 1);
    state.selectedNodeId = null;
    showScreen("map");
  }

  function runAcceptance() {
    var e = ENEMIES[state.currentEnemy];
    if (state.enemyHp < e.maxHp) {
      $("combat-log").textContent = "Log: acceptance failed · room not yet stable (play more cards)";
      toast("Acceptance failed — keep playing");
      return;
    }
    $("combat-log").textContent = "Log: acceptance passed · room clear";
    fanfare(function () { showScreen("reward"); });
  }

  function fanfare(done) {
    els.fanfare.hidden = false;
    setTimeout(function () { els.fanfare.hidden = true; done(); }, 640);
  }

  function endTurn() {
    state.energy = state.energyMax;
    state.playedThisTurn = [];
    $("combat-log").textContent = "Log: end turn · " + ENEMIES[state.currentEnemy].turnEffect;
    renderCombat();
  }

  function syncCampModeButtons() {
    document.querySelectorAll('[data-action="camp-mode"]').forEach(function (b) {
      b.classList.toggle("is-on", b.getAttribute("data-mode") === state.campMode);
    });
  }

  /* ------------------------------ theme ------------------------------ */
  function applyTheme() {
    document.documentElement.setAttribute("data-theme", state.theme);
    $("theme-label").textContent = state.theme === "light" ? "Dark" : "Light";
  }

  /* ------------------------------ wiring ------------------------------ */
  function onStageClick(e) {
    var t = e.target.closest("[data-go],[data-action]");
    if (!t) return;
    var go = t.getAttribute("data-go");
    var action = t.getAttribute("data-action");

    if (go) {
      if (go === "ascension") state.returnScreen = state.screen === "ascension" ? "map" : state.screen;
      if (go === "combat") beginCombat();
      showScreen(go);
      return;
    }

    switch (action) {
      case "new-climb":
        resetState(false);
        state.floor = 1; state.deckSize = 4; state.streak = 0; state.taken = 0; state.skips = 0;
        NODES.forEach(function (n, i) { n.done = false; n.reachable = i === 0; });
        toast("New climb · Floor 1");
        showScreen("map");
        break;
      case "refresh-prior":
        state.priorSeed += 1; toast("Priors refreshed"); renderMap();
        break;
      case "flee": doFlee(); break;
      case "run-acceptance": runAcceptance(); break;
      case "end-turn": endTurn(); break;
      case "skip-reward":
        state.skips += 1; toast("Skipped — lean deck"); completeNode("map");
        break;
      case "camp-mode":
        state.campMode = t.getAttribute("data-mode"); state.pruneId = null;
        syncCampModeButtons(); renderCamp();
        break;
      case "camp-leave":
        if (state.campMode === "rest") { toast("Rested"); completeNode("map"); }
        else completeNode("map");
        break;
      case "shop-leave": completeNode("map"); break;
      case "asc-cancel": showScreen(state.returnScreen || "map"); break;
    }
  }

  function wire() {
    els = {
      chrome: $("chrome"), chromeEnergy: $("chrome-energy"), chromeOrbs: $("chrome-orbs"),
      banner: $("banner"), bannerText: $("banner-text"), bannerActions: $("banner-actions"),
      toast: $("toast"), fanfare: $("fanfare"),
      mapGraph: $("map-graph"), enter: $("btn-enter"),
      combatHand: $("combat-hand"), combatOrbs: $("combat-orbs"),
      eventChoices: $("event-choices"), rewardOffers: $("reward-offers"),
      campList: $("camp-list"), campConfirm: $("btn-camp-confirm"),
      shopWares: $("shop-wares"), buy: $("btn-buy"),
      ascLadder: $("asc-ladder"), applyAsc: $("btn-apply-asc")
    };

    document.querySelector(".app-shell").addEventListener("click", onStageClick);
    document.querySelectorAll(".jump-btn").forEach(function (b) {
      b.addEventListener("click", function () {
        var name = b.getAttribute("data-go");
        if (name === "combat") beginCombat();
        showScreen(name);
      });
    });

    els.enter.addEventListener("click", enterNode);

    els.campConfirm.addEventListener("click", function () {
      if (!state.pruneId) return;
      var idx = -1;
      for (var i = 0; i < DECK.length; i++) if (DECK[i].id === state.pruneId) { idx = i; break; }
      if (idx >= 0) {
        var name = DECK[idx].name;
        DECK.splice(idx, 1);
        state.deckSize = Math.max(0, state.deckSize - 1);
        toast("Pruned " + name);
      }
      state.pruneId = null;
      completeNode("map");
    });

    els.buy.addEventListener("click", function () {
      var ware = WARES.filter(function (w) { return w.id === state.shopId; })[0];
      if (!ware) return;
      if (state.tokens < ware.price) { toast("Not enough focus tokens"); return; }
      if (ware.kind === "card" && state.deckSize + 1 > SOFT_CAP) { toast("Soft cap — prune before buying"); return; }
      state.tokens -= ware.price;
      if (ware.kind === "card") state.deckSize += 1;
      toast("Bought " + ware.title);
      state.shopId = null;
      completeNode("map");
    });

    els.applyAsc.addEventListener("click", function () {
      state.ascension = state.ascPick;
      toast("Applied A" + state.ascension);
      showScreen(state.returnScreen || "map");
    });

    $("btn-theme").addEventListener("click", function () {
      state.theme = state.theme === "light" ? "dark" : "light";
      applyTheme();
      toast(state.theme === "dark" ? "Dark theme" : "Light theme");
    });

    $("btn-reset").addEventListener("click", function () {
      var theme = state.theme;
      resetState(true);
      state.theme = theme;
      applyTheme();
      toast("Run reset");
      showScreen("title");
    });
  }

  /* ------------------------------ boot ------------------------------ */
  resetState(true);
  wire();
  applyTheme();
  syncCampModeButtons();
  showScreen("title");
})();
