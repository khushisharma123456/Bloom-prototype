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
    return fetch(url).then(res => {
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
        }        if (routine) {
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

// --- YOUTUBE SHORTS CAROUSEL ---
document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/exercise_videos')
        .then(res => res.json())
        .then(data => {
            if (data.exercises && Array.isArray(data.exercises)) {
                renderExerciseCarousel(data.exercises);
                if (window.renderRoutine) window.renderRoutine(data.exercises);
            }
        });
});

function renderExerciseCarousel(exercises) {
    const rightPanel = document.querySelector('.right-panel');
    if (!rightPanel) return;

    // Remove old carousel if exists
    let oldCarousel = document.getElementById('exercise-carousel');
    if (oldCarousel) oldCarousel.remove();

    // Carousel container
    const carousel = document.createElement('div');
    carousel.id = 'exercise-carousel';
    carousel.style.display = 'flex';
    carousel.style.flexDirection = 'column';
    carousel.style.alignItems = 'center';
    carousel.style.margin = '30px 0';

    // Slides wrapper
    const slidesWrapper = document.createElement('div');
    slidesWrapper.style.display = 'flex';
    slidesWrapper.style.alignItems = 'center';
    slidesWrapper.style.justifyContent = 'center';
    slidesWrapper.style.width = '100%';
    slidesWrapper.style.maxWidth = '480px';
    slidesWrapper.style.position = 'relative';

    // Carousel state
    let current = 0;

    function renderSlide(idx) {
        slidesWrapper.innerHTML = '';
        const ex = exercises[idx];
        // Video or fallback
        let videoDiv = document.createElement('div');
        videoDiv.style.width = '320px';
        videoDiv.style.height = '570px';
        videoDiv.style.background = '#eee';
        videoDiv.style.display = 'flex';
        videoDiv.style.alignItems = 'center';
        videoDiv.style.justifyContent = 'center';
        videoDiv.style.borderRadius = '16px';
        videoDiv.style.overflow = 'hidden';
        if (ex.youtube_video_id) {
            videoDiv.innerHTML = `<iframe width="320" height="570" src="https://www.youtube.com/embed/${ex.youtube_video_id}?autoplay=0&mute=1&modestbranding=1&rel=0&playsinline=1&controls=1&enablejsapi=1" frameborder="0" allowfullscreen allow="autoplay; encrypted-media"></iframe>`;
        } else {
            videoDiv.innerHTML = `<div style='color:#888;text-align:center;'>No video found</div>`;
        }
        slidesWrapper.appendChild(videoDiv);
    }

    // Navigation buttons
    const prevBtn = document.createElement('button');
    prevBtn.textContent = '<';
    prevBtn.style.margin = '0 10px';
    prevBtn.style.fontSize = '2rem';
    prevBtn.style.background = '#fff';
    prevBtn.style.border = '1px solid #ccc';
    prevBtn.style.borderRadius = '50%';
    prevBtn.style.width = '48px';
    prevBtn.style.height = '48px';
    prevBtn.style.cursor = 'pointer';
    prevBtn.onclick = function() {
        current = (current - 1 + exercises.length) % exercises.length;
        renderSlide(current);
        updateCaption();
    };

    const nextBtn = document.createElement('button');
    nextBtn.textContent = '>';
    nextBtn.style.margin = '0 10px';
    nextBtn.style.fontSize = '2rem';
    nextBtn.style.background = '#fff';
    nextBtn.style.border = '1px solid #ccc';
    nextBtn.style.borderRadius = '50%';
    nextBtn.style.width = '48px';
    nextBtn.style.height = '48px';
    nextBtn.style.cursor = 'pointer';
    nextBtn.onclick = function() {
        current = (current + 1) % exercises.length;
        renderSlide(current);
        updateCaption();
    };

    slidesWrapper.appendChild(prevBtn);
    renderSlide(current);
    slidesWrapper.appendChild(nextBtn);

    // Caption
    const caption = document.createElement('div');
    caption.style.marginTop = '12px';
    caption.style.fontWeight = 'bold';
    caption.style.fontSize = '1.1rem';
    caption.style.color = '#5a4a6a';
    function updateCaption() {
        caption.textContent = `${exercises[current].name} - ${exercises[current].instructions || ''}`;
    }
    updateCaption();

    carousel.appendChild(slidesWrapper);
    carousel.appendChild(caption);

    // Insert carousel at the top of right panel
    rightPanel.insertBefore(carousel, rightPanel.firstChild);
}
