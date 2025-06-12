// Ayurvedic Gemini Wrapper for getting Ayurvedic recommendations
class AyurvedicGeminiWrapper {
    constructor() {
        this.baseUrl = '/api';
    }

    // Get Ayurvedic recommendations from Gemini based on symptoms
    async getAyurvedicRecommendations(symptoms) {
        try {
            console.log('Starting ayurvedic recommendations for symptoms:', symptoms);
            
            const prompt = this.buildAyurvedicPrompt(symptoms);
            console.log('Making API call to:', `${this.baseUrl}/get-recommendations`);
            
            const response = await fetch(`${this.baseUrl}/get-recommendations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: prompt,
                    symptoms: symptoms
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

    // Build the prompt for Ayurvedic recommendations
    buildAyurvedicPrompt(symptoms) {
        const symptomsText = symptoms.join(', ');
        return `You are an expert Ayurvedic practitioner specializing in women's health and menstrual wellness.

Based on the following symptoms: ${symptomsText}

Please provide 4-6 traditional Ayurvedic remedies (nuskhe) that can help relieve these symptoms. Focus on natural ingredients, traditional preparations, and holistic healing approaches. Format your response as a JSON object with this exact structure:

{
  "ayurvedicRemedies": [
    {
      "title": "English Remedy Name",
      "description": "Brief description of the remedy and its ayurvedic principle",
      "ingredients": [
        "Ingredient 1 with quantity",
        "Ingredient 2 with quantity",
        "Ingredient 3 with quantity",
        "Ingredient 4 with quantity"
      ],
      "steps": [
        "Step 1: Detailed preparation instruction",
        "Step 2: Detailed preparation instruction",
        "Step 3: Detailed preparation instruction",
        "Step 4: Detailed preparation instruction",
        "Step 5: Usage instruction"
      ],
      "benefits": "Comprehensive list of benefits including doshas it balances",
      "bestTimeToConsume": "Best time of day and frequency",
      "precautions": [
        "Important precaution 1",
        "Important precaution 2",
        "Important precaution 3"
      ],
      "storageInstructions": "How to store the prepared remedy",
      "shelfLife": "How long the remedy remains effective",
      "time": "Preparation time and treatment duration",
      "image": "/static/Images/default-remedy.jpg"
    }
  ]
}

Focus on remedies that are:
- Traditional Ayurvedic formulations (churnas, kashayams, lehyams, etc.)
- Safe and natural with easily available ingredients
- Specifically effective for the mentioned symptoms
- Include proper doshas (Vata, Pitta, Kapha) balancing information
- Provide practical preparation methods suitable for home preparation

Make sure each remedy includes comprehensive ingredient lists, clear step-by-step preparation instructions, proper usage guidelines, and important safety precautions.`;
    }
}

// Export the wrapper
export default AyurvedicGeminiWrapper;
