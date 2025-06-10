// Yoga Asana Wrapper
class YogaWrapper {
    constructor() {
        this.baseUrl = '/api/get-yoga-recommendations';
    }    async getYogaRecommendations(symptoms) {
        try {
            // Fetch the yoga data using the new route
            const yogaResponse = await fetch('/data/yoga.json');
            
            if (!yogaResponse.ok) {
                throw new Error(`Failed to fetch yoga data: ${yogaResponse.status} ${yogaResponse.statusText}`);
            }

            const yogaData = await yogaResponse.json();

            const response = await fetch(this.baseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symptoms: symptoms,
                    yogaData: yogaData
                })
            });

            if (!response.ok) {
                throw new Error(`API call failed: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || 'Failed to get yoga recommendations');
            }

            // Return the recommendations directly from the API
            return {
                yogaAsanas: data.recommendations.yogaAsanas || []
            };
        } catch (error) {
            console.error('Error getting yoga recommendations:', error);
            throw error;
        }
    }
}

// Export the wrapper
export default YogaWrapper;