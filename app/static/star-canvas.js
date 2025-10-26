/////////////////////////////////////////////////////
// This is used for outer space / moving star effect 
// on login, register, and reset password pages
/////////////////////////////////////////////////////

const canvas = document.getElementById('starCanvas');
const ctx = canvas.getContext('2d');

// Keep track of the canvas size
let width = (canvas.width = window.innerWidth);
let height = (canvas.height = window.innerHeight);

// Hold star objects
let stars = [];

// Utility for reading CSS variables
function readCSSVariable(varName) {
    return getComputedStyle(document.documentElement)
        .getPropertyValue(varName)
        .trim();
}

// Create star object
function createStar(size, speed, color) {
    return {
        x: Math.random() * width,
        y: Math.random() * height,
        radius: size,
        speed: speed,
        color: color
    };
}

// Reinitialize star array whenever viewport changes
function initStars() {
    // Clear existing stars
    stars = [];

    // Calculate num of pixels for browser window
    const pixels = width * height;

    // How many multiples of 1.2 million pixels?
    const units = Math.ceil(pixels / 1_200_000);

    // Determine number of stars and set star color
    const numSmallStars = units * 90;
    const numLargeStars = units * 10;
    const smallColor = readCSSVariable('--color-small-star') || '#bbbbbb';
    const largeColor = readCSSVariable('--color-large-star') || '#dddddd';

    // Populate stars, set radius and speed
    for (let i = 0; i < numSmallStars; i++) {
        stars.push(createStar(
            0.5,
            0.05 + Math.random() * 0.1,
            smallColor
        ));
    }
    for (let i = 0; i < numLargeStars; i++) {
        stars.push(createStar(
            1,
            0.2 + Math.random() * 0.2,
            largeColor
        ));
    }
}

// On resize, update canvas dimensions, re-calc star count, start fresh
window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    initStars();
});

// Main animation loop
function animate() {
    const bg = readCSSVariable('--color-block1-bg') || '#252525';
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, width, height);

    for (let star of stars) {
        // Move diagonally up and to the left
        star.x -= star.speed;
        star.y -= star.speed;

        // Wrap horizontally
        if (star.x < 0) {
            star.x = width;
        }
        // Wrap vertically
        if (star.y < 0) {
            star.y = height;
        }

        // Draw the circle for this star
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
        ctx.fillStyle = star.color;
        ctx.fill();
    }

    requestAnimationFrame(animate);
}

// Start animation
function startStars() {
  initStars();
  animate();
}
window.addEventListener('load', startStars);

// Restart animation when data-theme flips
const themeObserver = new MutationObserver((muts) => {
  for (const m of muts) {
    if (m.attributeName === 'data-theme') {
      initStars(); // pick up new CSS var colors
      return;
    }
  }
});
themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });