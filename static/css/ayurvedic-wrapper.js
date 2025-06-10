// Ayurvedic Remedy Wrapper
class AyurvedicRemedyWrapper {
    constructor() {
        this.baseUrl = '/api/get-ayurvedic-recommendations';
    }    async getAyurvedicRecommendations(symptoms) {
        try {
            console.log('Starting ayurvedic recommendations for symptoms:', symptoms);
            
            // Fetch the recipes data using the new route
            const recipesResponse = await fetch('/data/recipes.json');
            if (!recipesResponse.ok) {
                console.error('Failed to fetch recipes data:', recipesResponse.status, recipesResponse.statusText);
                throw new Error(`Failed to fetch recipes data: ${recipesResponse.status} ${recipesResponse.statusText}`);
            }
            const recipesData = await recipesResponse.json();
            console.log('Successfully fetched recipes data');            console.log('Making API call to:', this.baseUrl);
            const response = await fetch(this.baseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symptoms: symptoms,
                    recipesData: recipesData
                })
            });

            console.log('API response status:', response.status, response.statusText);
            if (!response.ok) {
                const errorText = await response.text();
                console.error('API error response:', errorText);
                throw new Error(`API call failed: ${response.status} ${response.statusText} - ${errorText}`);
            }

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.message || 'Failed to get ayurvedic recommendations');
            }

            // Return the recommendations directly from the API
            return {
                ayurvedicRemedies: data.recommendations.ayurvedicRemedies || []
            };
        } catch (error) {
            console.error('Error getting ayurvedic recommendations:', error);
            throw error;
        }
    }
}

// Export the wrapper
export default AyurvedicRemedyWrapper;