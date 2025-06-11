// Mood Data Initializer for testing the mood cycle chart
function initializeSampleMoodData() {
    // Check if mood data already exists
    const existingData = localStorage.getItem('moodEntries');
    if (existingData && JSON.parse(existingData).length > 5) {
        console.log('Mood data already exists, skipping initialization');
        return; // Don't override existing data if there's substantial data
    }
    
    console.log('Initializing sample mood data...');
    
    // Create sample mood data for the past 28 days
    const today = new Date();
    const sampleMoods = ['happy', 'content', 'neutral', 'sad', 'angry'];
    const sampleEntries = [];
    
    for (let i = 0; i < 28; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        
        // Create realistic mood pattern based on cycle phase
        let mood;
        const cycleDay = (28 - i) % 28 + 1;
        
        if (cycleDay <= 5) {
            // Menstrual phase - lower moods
            mood = Math.random() < 0.6 ? (Math.random() < 0.5 ? 'sad' : 'neutral') : 'content';
        } else if (cycleDay <= 14) {
            // Follicular phase - improving moods
            mood = Math.random() < 0.7 ? (Math.random() < 0.6 ? 'content' : 'happy') : 'neutral';
        } else if (cycleDay <= 16) {
            // Ovulation - peak moods
            mood = Math.random() < 0.8 ? 'happy' : 'content';
        } else {
            // Luteal phase - declining moods
            mood = Math.random() < 0.5 ? (Math.random() < 0.4 ? 'sad' : 'neutral') : (Math.random() < 0.7 ? 'content' : 'angry');
        }
        
        sampleEntries.push({
            date: dateStr,
            mood: mood,
            note: `Sample entry for cycle day ${cycleDay}`
        });
    }
    
    localStorage.setItem('moodEntries', JSON.stringify(sampleEntries));
    console.log('Sample mood data initialized with', sampleEntries.length, 'entries');
}

// Call the function when the script loads
if (typeof window !== 'undefined') {
    initializeSampleMoodData();
}
