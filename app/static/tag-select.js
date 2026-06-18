/**
 * Tag Select Component - Modern multi-select with tag display
 * Converts standard HTML select[multiple] into a modern tag-based UI.
 * Updates incrementally (no full DOM rebuild on selection change).
 */

class TagSelect {
    constructor(selectElement) {
        this.selectElement = selectElement;
        this.selectedIds = new Set();
        this.wrapper = null;
        this.container = null;
        this.docClickHandler = null;
        this.init();
    }

    init() {
        Array.from(this.selectElement.options).forEach(option => {
            if (option.selected) {
                this.selectedIds.add(option.value);
            }
        });

        this.selectElement.style.display = 'none';

        this.wrapper = document.createElement('div');
        this.wrapper.style.position = 'relative';
        this.selectElement.parentNode.insertBefore(this.wrapper, this.selectElement);

        this.container = document.createElement('div');
        this.container.className = 'tag-select-wrapper';
        this.wrapper.appendChild(this.container);

        this.buildUI();
        this.bindEvents();
    }

    // ── UI Construction (called once) ──

    buildUI() {
        // Tags section
        const tagsSection = document.createElement('div');
        tagsSection.className = 'tag-select-tags';
        this.container.appendChild(tagsSection);

        // Input / trigger
        const inputWrapper = document.createElement('div');
        inputWrapper.className = 'tag-select-input';
        inputWrapper.style.position = 'relative';

        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.className = 'tag-select-search';
        searchInput.placeholder = `Ajouter ${this.getPlaceholder()}...`;
        searchInput.autocomplete = 'off';

        const icon = document.createElement('span');
        icon.className = 'tag-select-icon';
        icon.innerHTML = '<i class="fas fa-chevron-down"></i>';

        inputWrapper.appendChild(searchInput);
        inputWrapper.appendChild(icon);
        this.container.appendChild(inputWrapper);

        // Dropdown
        const dropdown = document.createElement('div');
        dropdown.className = 'tag-select-dropdown';

        const optionsList = document.createElement('div');
        optionsList.className = 'tag-select-options';

        Array.from(this.selectElement.options).forEach(option => {
            if (option.value) {
                optionsList.appendChild(this.createOptionEl(option));
            }
        });

        dropdown.appendChild(optionsList);
        inputWrapper.appendChild(dropdown);

        // Populate initial tags
        this.selectedIds.forEach(id => {
            const option = this.selectElement.querySelector(`option[value="${id}"]`);
            if (option) this.appendTag(id, option.textContent);
        });

        // Store refs
        this.tagsSection = tagsSection;
        this.searchInput = searchInput;
        this.dropdown = dropdown;
        this.inputWrapper = inputWrapper;
        this.optionsList = optionsList;
    }

    // ── Tag element factory ──

    createTagEl(id, text) {
        const tag = document.createElement('span');
        tag.className = 'tag-badge';
        tag.dataset.id = id;

        const textNode = document.createElement('span');
        textNode.textContent = text;

        const closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'tag-close';
        closeBtn.setAttribute('aria-label', 'Remove');
        closeBtn.innerHTML = '<i class="fas fa-times"></i>';

        closeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.removeSelection(id);
        });

        tag.appendChild(textNode);
        tag.appendChild(closeBtn);
        return tag;
    }

    appendTag(id, text) {
        this.tagsSection.appendChild(this.createTagEl(id, text));
    }

    removeTagEl(id) {
        const tag = this.tagsSection.querySelector(`.tag-badge[data-id="${id}"]`);
        if (tag) {
            tag.style.transition = 'transform 0.15s ease, opacity 0.15s ease';
            tag.style.transform = 'scale(0.8)';
            tag.style.opacity = '0';
            setTimeout(() => tag.remove(), 150);
        }
    }

    // ── Option element factory ──

    createOptionEl(option) {
        const el = document.createElement('div');
        el.className = 'tag-select-option';
        el.dataset.value = option.value;
        if (this.selectedIds.has(option.value)) el.classList.add('selected');

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = option.value;
        checkbox.checked = this.selectedIds.has(option.value);

        const label = document.createElement('label');
        label.className = 'tag-select-option-label';
        label.appendChild(checkbox);

        const textSpan = document.createElement('span');
        textSpan.textContent = option.textContent;
        label.appendChild(textSpan);

        el.appendChild(label);

        // Click on the row toggles selection
        el.addEventListener('click', (e) => {
            if (e.target.tagName === 'INPUT') return;
            e.preventDefault();
            this.toggleSelection(option.value, !checkbox.checked);
        });

        // Prevent label from forwarding click to checkbox (double-toggle)
        label.addEventListener('click', (e) => {
            e.preventDefault();
        });

        checkbox.addEventListener('change', (e) => {
            this.toggleSelection(option.value, e.target.checked);
        });

        return el;
    }

    // ── Events ──

    bindEvents() {
        // Toggle dropdown
        this.inputWrapper.addEventListener('click', (e) => {
            if (e.target.closest('.tag-close')) return;
            e.stopPropagation();
            this.toggleDropdown();
        });

        // Close on outside click (single shared handler)
        this.docClickHandler = (e) => {
            if (!this.wrapper.contains(e.target)) {
                this.closeDropdown();
            }
        };
        document.addEventListener('click', this.docClickHandler);

        // Search filter
        this.searchInput.addEventListener('input', (e) => {
            this.filterOptions(e.target.value);
        });

        // Keyboard
        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeDropdown();
                this.inputWrapper.focus();
            } else if (e.key === 'Backspace' && this.searchInput.value === '' && this.selectedIds.size > 0) {
                const lastId = Array.from(this.selectedIds).pop();
                this.removeSelection(lastId);
            } else if (e.key === 'Enter' || e.key === 'ArrowDown') {
                e.preventDefault();
                // Focus first visible option
                const visible = this.optionsList.querySelector('.tag-select-option:not([style*="display: none"])');
                if (visible) {
                    visible.focus();
                    visible.scrollIntoView({ block: 'nearest' });
                }
            }
        });

        // Keyboard navigation within options
        this.optionsList.addEventListener('keydown', (e) => {
            const current = e.target.closest('.tag-select-option');
            if (!current) return;
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                const dir = e.key === 'ArrowDown' ? 'nextSibling' : 'previousSibling';
                let sibling = current[dir];
                while (sibling && (sibling.style.display === 'none' || !sibling.classList.contains('tag-select-option'))) {
                    sibling = sibling[dir];
                }
                if (sibling) {
                    sibling.focus();
                    sibling.scrollIntoView({ block: 'nearest' });
                }
            } else if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const value = current.dataset.value;
                const cb = current.querySelector('input[type="checkbox"]');
                if (cb) {
                    this.toggleSelection(value, !cb.checked);
                }
            }
        });
    }

    // ── Dropdown ──

    toggleDropdown() {
        this.dropdown.classList.toggle('show');
        if (this.dropdown.classList.contains('show')) {
            this.searchInput.focus();
        } else {
            this.searchInput.value = '';
            this.filterOptions('');
        }
    }

    closeDropdown() {
        this.dropdown.classList.remove('show');
        this.searchInput.value = '';
        this.filterOptions('');
    }

    // ── Search ──

    filterOptions(searchText) {
        const lowerSearch = searchText.toLowerCase();
        Array.from(this.optionsList.querySelectorAll('.tag-select-option')).forEach(opt => {
            const matches = opt.textContent.toLowerCase().includes(lowerSearch);
            opt.style.display = matches ? '' : 'none';
            opt.tabIndex = matches ? 0 : -1;
        });
    }

    // ── Selection (incremental — no full rebuild) ──

    toggleSelection(value, selected) {
        if (selected) {
            this.addSelection(value);
        } else {
            this.removeSelection(value);
        }
    }

    addSelection(value) {
        if (this.selectedIds.has(value)) return;
        this.selectedIds.add(value);
        this.updateHiddenSelect();

        // Add tag with pop animation
        const option = this.selectElement.querySelector(`option[value="${value}"]`);
        if (option) this.appendTag(value, option.textContent);

        // Mark option as selected
        this.setOptionState(value, true);
    }

    removeSelection(value) {
        if (!this.selectedIds.has(value)) return;
        this.selectedIds.delete(value);
        this.updateHiddenSelect();

        // Animate and remove tag
        this.removeTagEl(value);

        // Unmark option
        this.setOptionState(value, false);
    }

    setOptionState(value, selected) {
        const el = this.optionsList?.querySelector(`.tag-select-option[data-value="${value}"]`);
        if (!el) return;
        el.classList.toggle('selected', selected);
        const cb = el.querySelector('input[type="checkbox"]');
        if (cb) cb.checked = selected;
    }

    updateHiddenSelect() {
        Array.from(this.selectElement.options).forEach(option => {
            option.selected = this.selectedIds.has(option.value);
        });
    }

    getPlaceholder() {
        return this.selectElement.dataset.plural || 'sélections';
    }
}

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('select[multiple].tag-select').forEach(select => {
        new TagSelect(select);
    });
});
