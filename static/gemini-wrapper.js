// Gemini Wrapper for Frontend
class GeminiWrapper {
    constructor() {
        this.apiKey = null;
        this.baseUrl = '/api';
    }

    // Get API key from Flask backend
    async getApiKey() {
        if (this.apiKey) return this.apiKey;
        
        try {
            const response = await fetch(`${this.baseUrl}/get-api-key`);
            if (!response.ok) {
                throw new Error(`Failed to get API key: ${response.status}`);
            }
            const data = await response.json();
            this.apiKey = data.apiKey;
            return this.apiKey;
        } catch (error) {
            console.error('Error getting API key:', error);
            throw error;
        }
    }

    // Get yoga recommendations from symptoms
    async getRecommendations(symptoms) {
        try {
            await this.getApiKey(); // Ensure we have the API key
            
            const prompt = this.buildYogaPrompt(symptoms);
            console.log('Sending prompt to Flask API:', prompt);
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

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`API call failed: ${response.status} - ${errorText}`);
            }

            const result = await response.json();
            console.log('Received response from Flask API:', result);
              if (!result.success) {
                throw new Error(result.message || 'API call failed');
            }

            // Parse the Gemini response
            if (result.recommendations) {
                return result.recommendations;
            } else if (result.response) {
                // Handle the case where the response is in 'response' field
                const geminiData = JSON.parse(result.response);
                return geminiData;
            } else {
                throw new Error('No recommendations found in response');
            }
            
        } catch (error) {
            console.error('Error getting recommendations:', error);
            throw error;
        }
    }

    // Build the prompt for yoga recommendations
    buildYogaPrompt(symptoms) {
        const symptomsText = symptoms.join(', ');
        return `You are an expert yoga instructor specializing in women's wellness and menstrual health.
        
Based on the following symptoms: ${symptomsText}

Please provide 6-8 yoga asanas that can help relieve these symptoms. Format your response as a JSON object with this exact structure:

{
  "yogaAsanas": [
    {
      "name": "Asana Name",
      "duration": "5-10 minutes",
      "steps": [
        "Step 1 description",
        "Step 2 description",
        "Step 3 description",
        "Step 4 description",
        "Step 5 description",
        "Step 6 description",
        "Step 7 description"
      ],
      "benefits": [
        "Benefit 1",
        "Benefit 2",
        "Benefit 3",
        "Benefit 4"
      ],
      "relievesSymptoms": [
        "Symptom 1",
        "Symptom 2",
        "Symptom 3"
        
      ],
      "precautions": [
        "Precaution 1",
        "Precaution 2",
        "Precaution 3",
        "Precaution 4",
        "Precaution 5"
      ],
       "Difficulty-Level": [
        "Difficulty-Level 1",
      ],
      "image": ""
    }
  ]
}

Focus on asanas that are:
- Safe during menstruation
- Gentle and restorative
- Specifically helpful for the mentioned symptoms
- Suitable for beginners to intermediate practitioners

Make sure to provide clear, step-by-step instructions and relevant precautions for each pose.`;
    }
}

export default GeminiWrapper;
