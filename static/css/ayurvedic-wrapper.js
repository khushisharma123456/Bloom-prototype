// Ayurvedic Remedy Wrapper
class AyurvedicRemedyWrapper {
    constructor() {
        this.baseUrl = '/api/get-ayurvedic-recommendations';
    }

    async getAyurvedicRecommendations(symptoms) {
        try {
            // Fetch the recipes data
            const recipesResponse = await fetch('/static/data/recipes.json');
            if (!recipesResponse.ok) {
                throw new Error('Failed to fetch recipes data');
            }
            const recipesData = await recipesResponse.json();

            // Format the prompt for Gemini
            const prompt = `I have the following symptoms: ${symptoms.join(', ')}.

            Here are all the available ayurvedic recipes from recipes.json:
            ${JSON.stringify(recipesData, null, 2)}

            Based on my symptoms, please:
            1. Look through the recipes and recommend the ones that match my symptoms in their 'category' field
            2. For each recommendation, include:
               - title
               - description
               - preparation time
               - ingredients (with quantities)
               - preparation steps
               - benefits
               - best time to consume
               - precautions
               - storage instructions
               - shelf life

            IMPORTANT: Only recommend items that are in these lists. Do not suggest any other remedies.`;

            const response = await fetch(this.baseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symptoms: symptoms,
                    prompt: prompt,
                    recipesData: recipesData
                })
            });

            if (!response.ok) {
                throw new Error(`API call failed: ${response.statusText}`);
            }

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.message || 'Failed to get ayurvedic recommendations');
            }

            // Extract recommended names from Gemini response (support 'name' or 'title')
            const recommendedNames = (data.recommendations.ayurvedicRemedies || []).map(r => (r.name || r.title) && (r.name || r.title).trim()).filter(Boolean);
            // Filter original recipesData.remedies for these names
            const remediesArr = Array.isArray(recipesData.remedies) ? recipesData.remedies : [];
            const filteredRemedies = remediesArr.filter(remedy => recommendedNames.includes(remedy.name));

            return {
                ayurvedicRemedies: filteredRemedies
            };
        } catch (error) {
            console.error('Error getting ayurvedic recommendations:', error);
            throw error;
        }
    }
}

// Export the wrapper
export default AyurvedicRemedyWrapper;