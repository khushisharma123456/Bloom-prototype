// Gemini API Wrapper
class GeminiWrapper {
    constructor() {
        this.baseUrl = '/api/get-recommendations';
    }

    async getRecommendations(symptoms) {
        try {
            // Fetch the JSON files
            const yogaResponse = await fetch('/data/yoga.json');
            const recipesResponse = await fetch('/data/recipes.json');
            
            if (!yogaResponse.ok || !recipesResponse.ok) {
                throw new Error('Failed to fetch yoga or recipes data');
            }

            const yogaData = await yogaResponse.json();
            const recipesData = await recipesResponse.json();

            // Format the prompt for Gemini
            const prompt = `I have the following symptoms: ${symptoms.join(', ')}.

            Here are all the available yoga asanas from yoga.json:
            ${JSON.stringify(yogaData, null, 2)}

            Here are all the available ayurvedic recipes from recipes.json:
            ${JSON.stringify(recipesData, null, 2)}

            Based on my symptoms, please:
            1. Look through the yoga asanas and recommend the ones that have matching symptoms in their 'relievesSymptoms' array
            2. Look through the recipes and recommend the ones that match my symptoms in their 'category' field

            For each recommendation, include:
            - For yoga asanas: name, steps, duration, and precautions
            - For ayurvedic remedies: title, description, and preparation time

            IMPORTANT: Only recommend items that are in these lists. Do not suggest any other asanas or remedies.`;

            const response = await fetch(this.baseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symptoms: symptoms,
                    prompt: prompt,
                    yogaData: yogaData,
                    recipesData: recipesData
                })
            });

            if (!response.ok) {
                throw new Error(`API call failed: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || 'Failed to get recommendations');
            }

            return {
                yogaAsanas: data.recommendations.yogaAsanas || [],
                ayurvedicRemedies: data.recommendations.ayurvedicRemedies || []
            };
        } catch (error) {
            console.error('Error getting recommendations:', error);
            throw error;
        }
    }
}

// Export the wrapper
export default GeminiWrapper; 