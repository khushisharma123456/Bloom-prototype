// Yoga Asana Wrapper
class YogaWrapper {
    constructor() {
        this.baseUrl = '/api/get-recommendations'; // Use Gemini API endpoint for personalized recommendations
        this.fallbackUrl = '/api/get-yoga-recommendations'; // Fallback to static database if Gemini fails
    }

    // Build a comprehensive prompt for Gemini API
    buildYogaPrompt(symptoms) {
        const symptomsText = symptoms.join(', ');
        return `You are an expert yoga instructor specializing in women's wellness and menstrual health.
        
Based on the following symptoms: ${symptomsText}

Please provide 6-8 yoga asanas that are specifically targeted to relieve these exact symptoms. Focus on poses that directly address the mentioned issues. Format your response as a JSON object with this exact structure:

{
  "yogaAsanas": [
    {
      "name": "Asana Name",
      "duration": "5-10 minutes",
      "steps": [
        "Step 1: Detailed instruction",
        "Step 2: Detailed instruction",
        "Step 3: Detailed instruction",
        "Step 4: Detailed instruction",
        "Step 5: Detailed instruction"
      ],
      "benefits": [
        "Specific benefit 1 for mentioned symptoms",
        "Specific benefit 2 for mentioned symptoms",
        "Specific benefit 3 for mentioned symptoms"
      ],
      "relievesSymptoms": [
        "Exact symptom 1 from the input",
        "Exact symptom 2 from the input"
      ],
      "precautions": [
        "Important safety precaution 1",
        "Important safety precaution 2",
        "Important safety precaution 3"
      ],
      "difficultyLevel": "Beginner/Intermediate/Advanced",
      "image": ""
    }
  ]
}

IMPORTANT GUIDELINES:
- Each pose MUST specifically target the mentioned symptoms: ${symptomsText}
- The "relievesSymptoms" array should contain the exact symptoms mentioned in the input
- Prioritize poses that are safe during menstruation
- Include gentle, restorative poses suitable for beginners
- Provide clear, step-by-step instructions
- Focus on poses that have proven effectiveness for the specific symptoms mentioned
- Ensure each pose directly addresses at least one of the input symptoms

Make sure every recommended pose is specifically chosen because it helps with: ${symptomsText}`;
    }

    async getYogaRecommendations(symptoms) {
        try {
            console.log('Getting personalized yoga recommendations for symptoms:', symptoms);
            
            // First, try to get personalized recommendations from Gemini API
            const prompt = this.buildYogaPrompt(symptoms);
            console.log('Using Gemini API for personalized recommendations...');
            
            const response = await fetch(this.baseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: prompt,
                    symptoms: symptoms
                })
            });

            if (response.ok) {
                const data = await response.json();
                
                if (data.success && data.recommendations) {
                    console.log('Successfully received personalized recommendations from Gemini API');
                    return {
                        yogaAsanas: data.recommendations.yogaAsanas || []
                    };
                }
            }
            
            console.log('Gemini API failed or unavailable, falling back to static database...');
            // Fallback to the static database approach
            return await this.getFallbackRecommendations(symptoms);
            
        } catch (error) {
            console.error('Error getting personalized yoga recommendations:', error);
            console.log('Attempting fallback to static database...');
            
            // Fallback to the static database approach
            try {
                return await this.getFallbackRecommendations(symptoms);
            } catch (fallbackError) {
                console.error('Fallback also failed:', fallbackError);
                throw new Error('Unable to get yoga recommendations from both personalized and static sources');
            }
        }
    }

    async getFallbackRecommendations(symptoms) {
        try {
            // Fetch the yoga data using the new route
            const yogaResponse = await fetch('/data/yoga.json');
            
            if (!yogaResponse.ok) {
                throw new Error(`Failed to fetch yoga data: ${yogaResponse.status} ${yogaResponse.statusText}`);
            }

            const yogaData = await yogaResponse.json();

            const response = await fetch(this.fallbackUrl, {
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
                throw new Error(`Fallback API call failed: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || 'Failed to get fallback yoga recommendations');
            }

            // Return the recommendations directly from the API
            return {
                yogaAsanas: data.recommendations.yogaAsanas || []
            };
        } catch (error) {
            console.error('Error getting fallback yoga recommendations:', error);
            throw error;
        }
    }
}

// Export the wrapper
export default YogaWrapper;