// src/swarm/static/rest_mode/js/modules/blueprintManager.js

import { fetchBlueprintMetadata as fetchMetadataAPI } from './apiService.js';
import { showToast } from '../toast.js';
import { appendRawMessage } from '../messages.js';
import { debugLog } from './debugLogger.js';
import { createChatHistoryEntry } from './chatHistory.js';

/**
 * Populates the blueprint selection dialog and dropdown.
 * @param {Array} blueprints - The list of blueprints fetched from the API.
 */
function populateBlueprintDialog(blueprints) {
    const blueprintDialogElement = document.getElementById('blueprintDialog');
    const blueprintDropdown = document.getElementById('blueprintDropdown');
    const currentPath = window.location.pathname; // Get the current URL path

    if (!blueprintDialogElement || !blueprintDropdown) {
        debugLog('Blueprint dialog or dropdown element not found.');
        return;
    }

    // Populate dialog
    blueprintDialogElement.innerHTML = blueprints
        .map(
            (bp) => `
        <div class="blueprint-option" data-id="${bp.id}">
            <p class="blueprint-title">${bp.title}</p>
            <p class="blueprint-description">${bp.description}</p>
        </div>`
        )
        .join('');

    // Populate dropdown
    blueprintDropdown.innerHTML = blueprints
        .map(
            (bp) => `
        <option value="${bp.id}">${bp.title}</option>`
        )
        .join('');

    // Find the blueprint matching the current path
    const matchedBlueprint = blueprints.find((bp) =>
        currentPath.includes(bp.route) // Assuming each blueprint has a `route` property
    );

    // Set the default dropdown value
    if (matchedBlueprint) {
        blueprintDropdown.value = matchedBlueprint.id; // Set the dropdown value
        selectBlueprint(matchedBlueprint); // Select the blueprint by default
    }

    // Add click event for each dialog option
    blueprintDialogElement.querySelectorAll('.blueprint-option').forEach((option) => {
        option.addEventListener('click', () => {
            const selectedId = option.getAttribute('data-id');
            const selectedBlueprint = blueprints.find((bp) => bp.id === selectedId);
            if (selectedBlueprint) {
                selectBlueprint(selectedBlueprint);
            }
        });
    });

    // Add change event for dropdown
    blueprintDropdown.addEventListener('change', (event) => {
        const selectedId = event.target.value;
        const selectedBlueprint = blueprints.find((bp) => bp.id === selectedId);
        if (selectedBlueprint) {
            selectBlueprint(selectedBlueprint);
        }
    });
}

/**
 * Updates the UI and metadata when a blueprint is selected.
 * @param {Object} blueprint - The selected blueprint.
 */
export function selectBlueprint(blueprint) {
    const blueprintMetadataElement = document.getElementById('blueprintMetadata');
    const blueprintDialogElement = document.getElementById('blueprintDialog');
    const persistentMessageElement = document.getElementById('firstUserMessage');

    if (!blueprintMetadataElement || !persistentMessageElement) {
        debugLog('Required elements for blueprint selection not found.');
        return;
    }

    const blueprintName = blueprint.title;
    const blueprintDescription = blueprint.description;

    // Update UI
    blueprintMetadataElement.innerHTML = `<h2>${blueprintName}</h2>`;
    persistentMessageElement.innerHTML = `<h2>${blueprintName}</h2><p>${blueprintDescription}</p>`;

    // Hide the blueprint dialog
    if (blueprintDialogElement) {
        blueprintDialogElement.classList.add('hidden');
    }

    // Notify user about blueprint change
    appendRawMessage(
        'assistant',
        {
            content: `Blueprint loaded: ${blueprintName}`,
        },
        'Assistant'
    );

    debugLog('Blueprint selected and UI updated.', blueprint);
}

/**
 * Initializes blueprint management by fetching metadata and populating the UI.
 */
export async function initializeBlueprints() {
    debugLog('Initializing blueprint management.');
    try {
        const blueprints = await fetchMetadataAPI();
        if (blueprints.length === 0) throw new Error('No blueprints available.');

        // Set default blueprint
        const defaultBlueprint = blueprints[0];
        selectBlueprint(defaultBlueprint);

        // Populate blueprint dialog and dropdown
        populateBlueprintDialog(blueprints);
    } catch (error) {
        debugLog('Error fetching blueprint metadata:', error);

        appendRawMessage(
            'assistant',
            {
                content:
                    'Could not retrieve blueprint metadata. Check out the troubleshooting guide at <a href="https://github.com/matthewhand/open-swarm/TROUBLESHOOTING.md">Troubleshooting Guide</a>.',
            },
            'Assistant'
        );
    }
}
