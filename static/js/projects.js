(() => {
    "use strict";

    const app = document.getElementById("projects-app");
    if (!app) return;

    const DUMMY_UUID = "00000000-0000-0000-0000-000000000000";
    const SEARCH_DEBOUNCE_DELAY = 300;
    const config = {
        projectsEndpoint: app.dataset.projectsEndpoint,
        starUrlTemplate: app.dataset.starUrlTemplate,
        editUrlTemplate: app.dataset.editUrlTemplate,
        deleteUrlTemplate: app.dataset.deleteUrlTemplate,
        loginUrl: app.dataset.loginUrl,
        csrfToken: app.dataset.csrfToken,
        isAuthenticated: app.dataset.isAuthenticated === "true",
        isSuperuser: app.dataset.isSuperuser === "true",
        canEdit: app.dataset.canEdit === "true",
    };

    const loadingState = document.getElementById("projects-loading");
    const errorState = document.getElementById("projects-error");
    const emptyState = document.getElementById("projects-empty");
    const gridContainer = document.getElementById("projects-grid");
    const searchForm = document.getElementById("project-search-form");
    const searchInput = document.getElementById("search-input");

    let projectsAbortController;
    let searchDebounceTimer;

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    function projectUrl(template, projectId) {
        return template.replace(DUMMY_UUID, encodeURIComponent(projectId));
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

    function closeProjectModal() {
        const modal = document.getElementById("add-project-modal");
        if (modal?.matches(":popover-open")) modal.hidePopover();
    }

    function buildLink(url, label) {
        if (!url) return "";

        return `
            <a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">
                ${escapeHtml(label || "View")}
            </a>
        `;
    }

    function buildStarControl(project, projectId) {
        if (!config.isAuthenticated) {
            return `
                <a href="${escapeHtml(config.loginUrl)}" class="button button-star" title="Log in to star this project">
                    <span aria-hidden="true">★</span>
                    Login to star
                    <span class="star-count">${project.star_count}</span>
                </a>
            `;
        }

        const starUrl = projectUrl(config.starUrlTemplate, projectId);
        const starredClass = project.is_starred ? " is-starred" : "";
        const starText = project.is_starred ? "Unstar" : "Star";
        const starTitle = project.is_starred
            ? "Remove your star"
            : "Star this project";

        return `
            <form method="post" action="${escapeHtml(starUrl)}" class="star-form">
                <input type="hidden" name="csrfmiddlewaretoken" value="${escapeHtml(config.csrfToken)}">
                <button type="submit" class="button button-star${starredClass}" title="${starTitle}">
                    <span aria-hidden="true">★</span>
                    ${starText}
                    <span class="star-count">${project.star_count}</span>
                </button>
            </form>
        `;
    }

    function buildProjectCardElement(item) {
        const project = item.fields;
        const projectId = item.pk;
        const articleElement = document.createElement("article");
        articleElement.className = "project-card";
        articleElement.tabIndex = 0;

        const imageHtml = project.thumbnail
            ? `<img class="project-image" src="${escapeHtml(project.thumbnail)}" alt="Preview of ${escapeHtml(project.title)}">`
            : "";
        const noteHtml = project.note
            ? `<span>${escapeHtml(project.note)}</span>`
            : "";
        const editHtml = config.canEdit
            ? `<a href="${escapeHtml(projectUrl(config.editUrlTemplate, projectId))}">Edit</a>`
            : "";
        const deleteHtml = config.isSuperuser
            ? `
                <form method="post" action="${escapeHtml(projectUrl(config.deleteUrlTemplate, projectId))}" class="project-delete-form">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${escapeHtml(config.csrfToken)}">
                    <button type="submit" class="project-delete-trigger">Delete</button>
                </form>
            `
            : "";

        articleElement.innerHTML = `
            <div class="project-media">
                ${imageHtml}
                <div class="project-overlay">
                    <h2>${escapeHtml(project.title)}</h2>
                    <p class="project-role">${escapeHtml(project.role)}</p>
                    <p class="project-description">${escapeHtml(project.description)}</p>
                    <div class="project-links">
                        ${buildLink(project.primary_link_url, project.primary_link_label)}
                        ${buildLink(project.secondary_link_url, project.secondary_link_label)}
                        ${buildLink(project.third_link_url, project.third_link_label)}
                        ${noteHtml}
                        ${buildStarControl(project, projectId)}
                        ${editHtml}
                        ${deleteHtml}
                    </div>
                </div>
            </div>
            <h2 class="project-mobile-title">${escapeHtml(project.title)}</h2>
        `;

        const deleteForm = articleElement.querySelector(".project-delete-form");
        if (deleteForm) {
            deleteForm.addEventListener("submit", (event) => {
                if (!window.confirm("Delete this project?")) {
                    event.preventDefault();
                }
            });
        }

        return articleElement;
    }

    async function fetchProjects(searchQuery = "") {
        if (projectsAbortController) projectsAbortController.abort();
        projectsAbortController = new AbortController();

        try {
            displayPageSection({ showLoading: true });
            const url = new URL(config.projectsEndpoint, window.location.origin);
            if (searchQuery) url.searchParams.set("title", searchQuery);

            const response = await fetch(url, {
                headers: { Accept: "application/json" },
                signal: projectsAbortController.signal,
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const projectData = await response.json();
            gridContainer.replaceChildren();

            if (projectData.length === 0) {
                displayPageSection({ showEmpty: true });
                return;
            }

            projectData.forEach((item) => {
                gridContainer.appendChild(buildProjectCardElement(item));
            });
            displayPageSection({ showGrid: true });
        } catch (error) {
            if (error.name === "AbortError") return;
            console.error("Error loading projects:", error);
            displayPageSection({ showError: true });
        }
    }

    function searchProjects() {
        const searchQuery = searchInput.value.trim();
        const browserUrl = new URL(window.location.href);

        if (searchQuery) {
            browserUrl.searchParams.set("title", searchQuery);
        } else {
            browserUrl.searchParams.delete("title");
        }
        window.history.replaceState({}, "", browserUrl);
        fetchProjects(searchQuery);
    }

    searchInput.addEventListener("input", () => {
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(searchProjects, SEARCH_DEBOUNCE_DELAY);
    });

    searchForm.addEventListener("submit", (event) => {
        event.preventDefault();
        clearTimeout(searchDebounceTimer);
        searchProjects();
    });

    fetchProjects(searchInput.value.trim());
})();
