// Yoga Asana Wrapper
class YogaWrapper {
    constructor() {
        this.baseUrl = '/api/get-yoga-recommendations';
    }

    async getYogaRecommendations(symptoms) {
        try {
            // Fetch the yoga data
            const yogaResponse = await fetch('/static/data/yoga.json');
            
            if (!yogaResponse.ok) {
                throw new Error('Failed to fetch yoga data');
            }

            const yogaData = await yogaResponse.json();

            // Format the prompt for Gemini
            const prompt = `I have the following symptoms: ${symptoms.join(', ')}.

            Here are all the available yoga asanas from yoga.json:
            ${JSON.stringify(yogaData, null, 2)}

            Based on my symptoms, please:
            1. Look through the yoga asanas and recommend the ones that have matching symptoms in their 'relievesSymptoms' array
            2. For each recommendation, include:
               - name
               - steps
               - duration
               - precautions
               - benefits
               - contraindications
               - difficulty level
               - best time to practice

            IMPORTANT: Only recommend items that are in these lists. Do not suggest any other asanas.`;

            const response = await fetch(this.baseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symptoms: symptoms,
                    prompt: prompt,
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