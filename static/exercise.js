// static/exercise.js

// Helper to get query params
function getQueryParam(name) {
    const url = new URL(window.location.href);
    return url.searchParams.get(name);
}

let allExercises = [];
let allRoutines = [];
let exercises = [];

// Load JSON files
function loadJSON(url) {
    // Add cache busting
    const separator = url.includes('?') ? '&' : '?';
    const urlWithCacheBuster = `${url}${separator}t=${new Date().getTime()}`;
    return fetch(urlWithCacheBuster).then(res => {
        if (!res.ok) {
            throw new Error(`Failed to fetch ${url}`);
        }
        return res.json();
    });
}

async function loadDataAndInit() {
    try {
        console.log('Loading data...');
        allExercises = await loadJSON('/api/exercises');
        console.log('Loaded exercises:', allExercises);

        allRoutines = await loadJSON('/api/routines');
        console.log('Loaded routines:', allRoutines);

        const routineName = getQueryParam('routine');
        console.log('Looking for routine:', routineName);

        let routine = null;
        if (routineName) {
            routine = allRoutines.find(r => r.name === routineName);
        } if (routine) {
            console.log('Found routine:', routine);
            console.log('Routine poses:', routine.poses);
            console.log('Available exercises:', allExercises.map(e => e.name));

            exercises = routine.poses.map(poseName => {
                // First try exact match
                let exercise = allExercises.find(e => e.name === poseName);

                // If no exact match, try matching just the Sanskrit name part
                if (!exercise) {
                    const sanskritName = poseName.split(' (')[0];
                    exercise = allExercises.find(e => e.name === sanskritName || e.name.startsWith(sanskritName));
                }

                if (!exercise) {
                    console.warn(`Could not find exercise for pose: ${poseName}`);
                }

                return exercise;
            }).filter(Boolean);
            console.log('Matched exercises:', exercises);
        } else {
            console.log('No routine found, using all exercises');
            exercises = allExercises;
        }

        console.log('Final exercises to render:', exercises);
        window.renderRoutine(exercises); // Call the render function defined in exercise.html
    } catch (error) {
        console.error('Error loading data:', error);
        // Fallback to default exercises if API fails
        exercises = [];
        window.renderRoutine(exercises);
    }
}

window.addEventListener('DOMContentLoaded', loadDataAndInit);

// Optionally, export exercises for debugging
window.getCurrentExercises = () => exercises;

// Carousel logic removed to prevent duplicate video display
