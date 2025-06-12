
// Dynamic Recipe Loader
// Loads recipe data from the backend and populates cards

class RecipeManager {
    constructor() {
        this.recipes = [];
        this.currentCategory = 'All';
        this.searchTerm = '';
    }

    async loadRecipes() {
        try {
            const response = await fetch('/api/recipes');
            if (response.ok) {
                const data = await response.json();
                this.recipes = data.remedies || [];
                this.renderAyurvedaRemedies();
            } else {
                console.error('Failed to load recipes');
                this.showErrorMessage();
            }
        } catch (error) {
            console.error('Error loading recipes:', error);
            this.showErrorMessage();
        }
    }

    renderAyurvedaRemedies() {
        const container = document.getElementById('ayurvedaRemedyGrid');
        if (!container) return;

        const filteredRecipes = this.filterRecipes();
        
        if (filteredRecipes.length === 0) {
            container.innerHTML = `
                <div class="no-results">
                    <p>No remedies found matching your criteria.</p>
                </div>
            `;
            return;
        }

        let html = '';
        filteredRecipes.forEach(recipe => {
            const imageUrl = recipe.image ? `/static/${recipe.image}` : '/static/Images/default-recipe.png';
            
            html += `
                <div class="recipe-card" data-category="${recipe.badge}">
                    <div class="recipe-image" style="background-image: url('${imageUrl}');">
                        <span class="recipe-badge">${recipe.badge}</span>
                    </div>
                    <div class="recipe-info">
                        <h3>${recipe.name}</h3>
                        <div class="recipe-meta">
                            <span>⏱️ ${recipe.time}</span>
                            ${recipe.calories ? `<span>🔥 ${recipe.calories}</span>` : ''}
                        </div>
                        <p>${recipe.description}</p>
                        <button class="view-recipe" onclick="viewRecipe('${encodeURIComponent(recipe.name)}')">View Remedy →</button>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    filterRecipes() {
        return this.recipes.filter(recipe => {
            const matchesCategory = this.currentCategory === 'All' || 
                                  recipe.badge.toLowerCase().includes(this.currentCategory.toLowerCase());
            
            const matchesSearch = this.searchTerm === '' || 
                                recipe.name.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
                                recipe.description.toLowerCase().includes(this.searchTerm.toLowerCase());
            
            return matchesCategory && matchesSearch;
        });
    }

    showErrorMessage() {
        const container = document.getElementById('ayurvedaRemedyGrid');
        if (container) {
            container.innerHTML = `
                <div class="error-message">
                    <p>Unable to load recipes. Please refresh the page or try again later.</p>
                </div>
            `;
        }
    }
}

// Global functions for template compatibility
function filterAyurvedaRemedies(category) {
    if (window.recipeManager) {
        window.recipeManager.currentCategory = category;
        window.recipeManager.renderAyurvedaRemedies();
        
        // Update active button
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        event.target.classList.add('active');
    }
}

function searchAyurvedaRemedies() {
    if (window.recipeManager) {
        const searchInput = document.getElementById('ayurvedaSearchInput');
        window.recipeManager.searchTerm = searchInput.value.toLowerCase().trim();
        window.recipeManager.renderAyurvedaRemedies();
    }
}

function viewRecipe(recipeName) {
    window.location.href = `/remedy/${encodeURIComponent(recipeName)}`;
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.recipeManager = new RecipeManager();
    window.recipeManager.loadRecipes();
    
    // Add search input event listener
    const searchInput = document.getElementById('ayurvedaSearchInput');
    if (searchInput) {
        searchInput.addEventListener('input', searchAyurvedaRemedies);
    }
});
