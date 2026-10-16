(function () {
  "use strict";

  const form = document.querySelector("[data-intake-form]");
  const textarea = document.querySelector("#intake-message");
  const conversation = document.querySelector("[data-conversation]");
  const quickPrompts = document.querySelector("[data-quick-prompts]");
  const statusMessage = document.querySelector("[data-intake-status]");
  const sendButton = form.querySelector(".send-button");
  const progress = document.querySelector("[data-progress]");
  const stepNumber = document.querySelector("[data-step-number]");
  const startOver = document.querySelector("[data-start-over]");
  const resultsPanel = document.querySelector("[data-results-panel]");
  const resultsList = document.querySelector("[data-results-list]");
  const resultsSummary = document.querySelector("[data-results-summary]");
  const editReferral = document.querySelector("[data-edit-referral]");
  const helpDialog = document.querySelector("[data-help-dialog]");
  const helpButton = document.querySelector("[data-help-button]");
  const closeHelp = document.querySelector("[data-close-help]");
  const memberFilter = document.querySelector("[data-member-filter]");
  const memberCards = [...document.querySelectorAll("[data-member-card]")];
  const memberCount = document.querySelector("[data-member-count]");
  const memberEmpty = document.querySelector("[data-member-empty]");

  let sessionId = null;
  let isReady = false;

  const labels = {
    food: "food & nutrition",
    food_delivery: "meal delivery",
    healthcare: "healthcare",
    mental_health: "emotional well-being",
    physical_activity: "physical activity",
    housing: "housing",
    transportation: "transportation",
  };

  function csrfToken() {
    const input = document.querySelector("[name=csrfmiddlewaretoken]");
    return input ? input.value : "";
  }

  function setStatus(message, isError) {
    statusMessage.textContent = message || "";
    statusMessage.hidden = !message;
    statusMessage.style.color = isError ? "#a75b44" : "#71807a";
  }

  function appendMessage(kind, text) {
    const isUser = kind === "user";
    const wrapper = document.createElement("div");
    wrapper.className = `message ${isUser ? "user-message" : "relay-message"}`;
    wrapper.innerHTML = `
      <span class="avatar ${isUser ? "user-avatar" : "relay-avatar"}" aria-hidden="true">${isUser ? "you" : "r"}</span>
      <div class="message-body">
        <span class="sender-label">${isUser ? "You" : "Relay"} <span>• now</span></span>
        <p></p>
      </div>`;
    wrapper.querySelector("p").textContent = text;
    conversation.appendChild(wrapper);
    wrapper.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function updateProgress(missingFields, status) {
    const remaining = missingFields.length;
    const currentStep = status === "ready" ? 3 : remaining >= 2 ? 1 : 2;
    stepNumber.textContent = currentStep;
    progress.style.width = status === "ready" ? "100%" : `${currentStep === 2 ? 66 : 33}%`;
  }

  function setLoading(loading) {
    sendButton.disabled = loading;
    sendButton.querySelector("span").textContent = loading ? "Thinking…" : (isReady ? "Quick search" : "Send");
  }

  function formatNeed(need) {
    return labels[need] || need.replaceAll("_", " ");
  }

  function summarizeDraft(draft) {
    const needs = (draft.needs || []).map(formatNeed).join(", ");
    const place = [draft.city, draft.county && `${draft.county} County`].filter(Boolean).join(", ");
    return [needs, place].filter(Boolean).join(" · ");
  }

  async function sendIntake(message) {
    const payload = { message };
    if (sessionId) payload.session_id = sessionId;

    const response = await fetch("/api/intake/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "We couldn’t process that message.");
    return data;
  }

  async function searchSession() {
    const response = await fetch(`/api/intake/sessions/${sessionId}/search/`, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken() },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "We couldn’t search for matches yet.");
    return data;
  }

  function showReadyState(data) {
    isReady = true;
    appendMessage("relay", "Before I search, is there anything else you’d like me to consider—such as your child’s age, insurance, preferred language, or accessibility needs?");
    updateProgress([], "ready");
    sendButton.querySelector("span").textContent = "Quick search";
    form.querySelector("textarea").placeholder = "Answer Relay, or start a quick search…";
    startOver.hidden = false;
    resultsSummary.textContent = summarizeDraft(data.draft) || "Based on what you shared.";
  }

  function acknowledgeReadyFollowup(data) {
    isReady = true;
    updateProgress([], "ready");
    resultsSummary.textContent = summarizeDraft(data.draft) || "Based on what you shared.";
    appendMessage("relay", "Thanks—I’ll include that. Would you like to add anything else, or run a quick search?");
  }

  function renderResults(data) {
    const recommendations = data.recommendations || [];
    resultsList.innerHTML = "";
    if (!recommendations.length) {
      resultsList.innerHTML = '<div class="empty-results">We didn’t find an active resource that matches those details yet. Try editing your referral with a little more context, or check back with a local 211 service for additional options.</div>';
    } else {
      recommendations.forEach((recommendation) => {
        const card = document.createElement("article");
        card.className = "result-card";
        const reasons = (recommendation.reasons || []).slice(0, 3);
        const warnings = (recommendation.warnings || []).slice(0, 2);
        const reasonMarkup = reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("");
        const warningMarkup = warnings.map((warning) => `<li class="warning">${escapeHtml(warning)}</li>`).join("");
        const verified = recommendation.last_verified_at ? `Verified ${formatDate(recommendation.last_verified_at)}` : "Verification date not listed";
        const logoMarkup = recommendation.logo_url
          ? `<img class="result-logo" src="${escapeAttribute(recommendation.logo_url)}" alt="${escapeAttribute(recommendation.resource_name)} logo">`
          : `<span class="result-logo-fallback" aria-hidden="true">${escapeHtml(recommendation.resource_name.slice(0, 1))}</span>`;
        card.innerHTML = `
          <div class="result-top">
            <div>
              <div class="result-heading"><div class="result-logo-wrap">${logoMarkup}</div><div><h3 class="result-name">${escapeHtml(recommendation.resource_name)}</h3>
              <div class="result-location"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" stroke="currentColor" stroke-width="1.7"/><circle cx="12" cy="10" r="2.5" stroke="currentColor" stroke-width="1.7"/></svg>${escapeHtml([recommendation.city, recommendation.state].filter(Boolean).join(", "))}</div>
              </div></div>
            </div>
            <span class="match-badge ${recommendation.eligible ? "" : "not-eligible"}">${recommendation.eligible ? `${recommendation.score}% fit` : "Review fit"}</span>
          </div>
          <p class="result-description">${escapeHtml(recommendation.description || "A local community resource that may be able to help.")}</p>
          <ul class="reason-list">${reasonMarkup}${warningMarkup}</ul>
          <div class="result-footer"><span class="verified">${verified}</span>${recommendation.source_url ? `<a class="source-link" href="${escapeAttribute(recommendation.source_url)}" target="_blank" rel="noopener">Visit resource ↗</a>` : ""}</div>`;
        resultsList.appendChild(card);
      });
    }
    resultsPanel.hidden = false;
    form.hidden = true;
    document.querySelector("[data-intake-card]").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function escapeHtml(value) {
    const element = document.createElement("div");
    element.textContent = value == null ? "" : String(value);
    return element.innerHTML;
  }

  function escapeAttribute(value) {
    return escapeHtml(value).replaceAll('"', "&quot;");
  }

  function formatDate(value) {
    return new Intl.DateTimeFormat(undefined, { month: "short", year: "numeric" }).format(new Date(value));
  }

  function updateMemberDirectory() {
    if (!memberFilter || !memberCount) return;

    const query = memberFilter.value.trim().toLowerCase();
    let visibleCount = 0;

    memberCards.forEach((card) => {
      const matches = !query || card.dataset.memberSearch.includes(query);
      card.hidden = !matches;
      if (matches) visibleCount += 1;
    });

    memberCount.textContent = `${visibleCount} member${visibleCount === 1 ? "" : "s"}`;
    if (memberEmpty) memberEmpty.hidden = visibleCount !== 0;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = textarea.value.trim();
    if (!message && !isReady) return;
    if (isReady && !message) {
      setLoading(true);
      setStatus("Looking for local matches…");
      try {
        const data = await searchSession();
        renderResults(data);
        setStatus("");
      } catch (error) {
        setStatus(error.message, true);
      } finally {
        setLoading(false);
      }
      return;
    }

    if (message) appendMessage("user", message);
    textarea.value = "";
    if (quickPrompts) quickPrompts.hidden = true;
    setLoading(true);
    setStatus("");
    try {
      if (isReady) {
        const data = await sendIntake(message);
        sessionId = data.session_id;
        updateProgress(data.missing_fields || [], data.status);
        if (data.status === "ready") {
          acknowledgeReadyFollowup(data);
        } else {
          isReady = false;
          appendMessage("relay", data.question || "What else would help us narrow this down?");
          setStatus(data.draft && summarizeDraft(data.draft) ? `So far: ${summarizeDraft(data.draft)}` : "");
        }
      } else {
        const data = await sendIntake(message);
        sessionId = data.session_id;
        updateProgress(data.missing_fields || [], data.status);
        if (data.status === "ready") {
          showReadyState(data);
        } else {
          appendMessage("relay", data.question || "What else would help us narrow this down?");
          startOver.hidden = false;
          setStatus(data.draft && summarizeDraft(data.draft) ? `So far: ${summarizeDraft(data.draft)}` : "");
        }
      }
    } catch (error) {
      setStatus(error.message, true);
    } finally {
      setLoading(false);
      textarea.focus();
    }
  });

  document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => {
      textarea.value = button.dataset.prompt;
      textarea.focus();
    });
  });

  if (memberFilter) memberFilter.addEventListener("input", updateMemberDirectory);

  startOver.addEventListener("click", () => window.location.reload());
  editReferral.addEventListener("click", () => {
    resultsPanel.hidden = true;
    form.hidden = false;
    textarea.focus();
  });
  helpButton.addEventListener("click", () => helpDialog.showModal());
  closeHelp.addEventListener("click", () => helpDialog.close());
  helpDialog.addEventListener("click", (event) => {
    if (event.target === helpDialog) helpDialog.close();
  });
})();
