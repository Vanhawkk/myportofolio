(() => {
    "use strict";

    const app = document.getElementById("experiences-app");
    if (!app) return;

    const DUMMY_UUID = "00000000-0000-0000-0000-000000000000";
    const SEARCH_DEBOUNCE_DELAY = 300;
    const config = {
        experiencesEndpoint: app.dataset.experiencesEndpoint,
        createExperienceEndpoint: app.dataset.createExperienceEndpoint,
        starUrlTemplate: app.dataset.starUrlTemplate,
        editUrlTemplate: app.dataset.editUrlTemplate,
        deleteUrlTemplate: app.dataset.deleteUrlTemplate,
        loginUrl: app.dataset.loginUrl,
        csrfToken: app.dataset.csrfToken,
        isAuthenticated: app.dataset.isAuthenticated === "true",
        isSuperuser: app.dataset.isSuperuser === "true",
        canEdit: app.dataset.canEdit === "true",
    };

    const loadingState = document.getElementById("experiences-loading");
    const errorState = document.getElementById("experiences-error");
    const emptyState = document.getElementById("experiences-empty");
    const gridContainer = document.getElementById("experiences-grid");
    const searchForm = document.getElementById("experience-search-form");
    const searchInput = document.getElementById("experience-search-input");
    const experienceForm = document.getElementById("experience-form");

    let experiencesAbortController;
    let searchDebounceTimer;

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    function experienceUrl(template, experienceId) {
        return template.replace(DUMMY_UUID, encodeURIComponent(experienceId));
    }

    function getCookie(name) {
        const cookies = document.cookie ? document.cookie.split(";") : [];

        for (const item of cookies) {
            const cookie = item.trim();
            if (cookie.startsWith(`${name}=`)) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
        return null;
    }

    function displayPageSection({
        showLoading = false,
        showError = false,
        showEmpty = false,
        showGrid = false,
    }) {
        loadingState.classList.toggle("hide", !showLoading);
        errorState.classList.toggle("hide", !showError);
        emptyState.classList.toggle("hide", !showEmpty);
        gridContainer.classList.toggle("hide", !showGrid);
    }

    function closeExperienceModal() {
        const modal = document.getElementById("add-experience-modal");
        if (modal?.matches(":popover-open")) modal.hidePopover();
    }

    function buildStarControl(experience, experienceId) {
        if (!config.isAuthenticated) {
            return `
                <a href="${escapeHtml(config.loginUrl)}" class="button button-star" title="Log in to star this experience">
                    <span aria-hidden="true">★</span>
                    Login to star
                    <span class="star-count">${experience.star_count}</span>
                </a>
            `;
        }

        const starUrl = experienceUrl(config.starUrlTemplate, experienceId);
        const starredClass = experience.is_starred ? " is-starred" : "";
        const starText = experience.is_starred ? "Unstar" : "Star";
        const starTitle = experience.is_starred
            ? "Remove your star"
            : "Star this experience";

        return `
            <form method="post" action="${escapeHtml(starUrl)}" class="star-form">
                <input type="hidden" name="csrfmiddlewaretoken" value="${escapeHtml(config.csrfToken)}">
                <button type="submit" class="button button-star${starredClass}" title="${starTitle}">
                    <span aria-hidden="true">★</span>
                    ${starText}
                    <span class="star-count">${experience.star_count}</span>
                </button>
            </form>
        `;
    }

    function buildExperienceCardElement(item) {
        const experience = item.fields;
        const experienceId = item.pk;
        const articleElement = document.createElement("article");
        articleElement.className = "experience-card";

        const imageHtml = experience.thumbnail
            ? `<img class="experience-image" src="${escapeHtml(experience.thumbnail)}" alt="Thumbnail for ${escapeHtml(experience.title)}">`
            : "";
        const status = experience.is_ongoing ? "Ongoing" : "Done";
        const editHtml = config.canEdit
            ? `
                <a href="${escapeHtml(experienceUrl(config.editUrlTemplate, experienceId))}" class="button button-secondary">
                    Edit
                </a>
            `
            : "";
        const deleteHtml = config.isSuperuser
            ? `
                <form method="post" action="${escapeHtml(experienceUrl(config.deleteUrlTemplate, experienceId))}" class="experience-delete-form">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${escapeHtml(config.csrfToken)}">
                    <button type="submit" class="button button-danger">Delete</button>
                </form>
            `
            : "";
        const actionsHtml = editHtml || deleteHtml
            ? `<div class="experience-actions">${editHtml}${deleteHtml}</div>`
            : "";

        articleElement.innerHTML = `
            ${imageHtml}
            <span class="experience-category">${escapeHtml(experience.category_label)}</span>
            <h2>${escapeHtml(experience.title)}</h2>
            <p class="experience-description">${escapeHtml(experience.description)}</p>
            <p class="experience-status">${status}</p>
            ${buildStarControl(experience, experienceId)}
            ${actionsHtml}
        `;

        const deleteForm = articleElement.querySelector(".experience-delete-form");
        if (deleteForm) {
            deleteForm.addEventListener("submit", (event) => {
                if (!window.confirm("Delete this experience?")) {
                    event.preventDefault();
                }
            });
        }

        return articleElement;
    }

    async function fetchExperiences(searchQuery = "") {
        if (experiencesAbortController) experiencesAbortController.abort();
        experiencesAbortController = new AbortController();

        try {
            displayPageSection({ showLoading: true });
            const url = new URL(
                config.experiencesEndpoint,
                window.location.origin,
            );
            if (searchQuery) url.searchParams.set("q", searchQuery);

            const response = await fetch(url, {
                headers: { Accept: "application/json" },
                signal: experiencesAbortController.signal,
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const experienceData = await response.json();
            gridContainer.replaceChildren();

            if (experienceData.length === 0) {
                displayPageSection({ showEmpty: true });
                return;
            }

            experienceData.forEach((item) => {
                gridContainer.appendChild(buildExperienceCardElement(item));
            });
            displayPageSection({ showGrid: true });
        } catch (error) {
            if (error.name === "AbortError") return;
            console.error("Error loading experiences:", error);
            displayPageSection({ showError: true });
        }
    }

    async function addExperience(event) {
        event.preventDefault();
        const submitButton = experienceForm.querySelector(
            'button[type="submit"]',
        );
        submitButton.disabled = true;

        try {
            const response = await fetch(config.createExperienceEndpoint, {
                method: "POST",
                headers: {
                    "X-CSRFToken": (
                        getCookie("csrftoken") || config.csrfToken
                    ),
                    Accept: "application/json",
                },
                body: new FormData(experienceForm),
            });
            const result = await response.json().catch(() => ({}));

            if (!response.ok) {
                const errorMessages = result.errors
                    ? Object.values(result.errors)
                        .flat()
                        .map((error) => error.message)
                    : [
                        result.message
                        || `Request failed (HTTP ${response.status}).`,
                    ];
                showToast(
                    "Failed to add experience",
                    errorMessages.join(" "),
                    "error",
                );
                return;
            }

            experienceForm.reset();
            closeExperienceModal();
            showToast("Success", result.message, "success");
            await fetchExperiences(searchInput.value.trim());
        } catch (error) {
            console.error("Error adding experience:", error);
            showToast(
                "Failed to add experience",
                "Could not connect to the server. Please try again.",
                "error",
            );
        } finally {
            submitButton.disabled = false;
        }
    }

    function searchExperiences() {
        const searchQuery = searchInput.value.trim();
        const browserUrl = new URL(window.location.href);

        if (searchQuery) {
            browserUrl.searchParams.set("q", searchQuery);
        } else {
            browserUrl.searchParams.delete("q");
        }
        window.history.replaceState({}, "", browserUrl);
        fetchExperiences(searchQuery);
    }

    searchInput.addEventListener("input", () => {
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(
            searchExperiences,
            SEARCH_DEBOUNCE_DELAY,
        );
    });

    searchForm.addEventListener("submit", (event) => {
        event.preventDefault();
        clearTimeout(searchDebounceTimer);
        searchExperiences();
    });

    if (experienceForm) {
        experienceForm.addEventListener("submit", addExperience);
    }

    fetchExperiences(searchInput.value.trim());
})();
