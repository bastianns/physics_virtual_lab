let muatanCount = 0;
const maxMuatan = 10;
const penggaris = document.getElementById('penggaris');
const kainWol = document.getElementById('kain_wol');
const serpihanKertas = document.getElementById('serpihan_kertas');
const muatanNegatifContainer = document.getElementById('muatanNegatifContainer');

let chargeDecreasing = false; // Track if charge is already decreasing
let chargeInterval = null;

// Set initial positions
penggaris.style.position = 'absolute';
penggaris.style.left = '100px';
penggaris.style.top = '100px';

// Make the ruler draggable
makeDraggable(penggaris);

// Function to make an element draggable
function makeDraggable(element) {
    let isDragging = false;
    let initialX, initialY, currentX, currentY, xOffset = 0, yOffset = 0;

    element.addEventListener('mousedown', (e) => dragStart(e, element));

    function dragStart(e, element) {
        initialX = e.clientX - xOffset;
        initialY = e.clientY - yOffset;
        if (e.target === element) {
            isDragging = true;
            document.addEventListener('mousemove', drag);
            document.addEventListener('mouseup', dragEnd);
        }
    }

    function drag(e) {
        if (isDragging) {
            e.preventDefault();
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;

            xOffset = currentX;
            yOffset = currentY;
            setTranslate(currentX, currentY, element);

            // Attraction logic for paper if charge is present
            if (element === penggaris && muatanCount > 0) {
                if (isCloseEnough(penggaris, serpihanKertas)) {
                    moveSerpihanToPenggaris();
                    if (!chargeDecreasing) startDecreasingCharge();
                } else {
                    stopDecreasingCharge();
                }
            }
        }
    }

    function dragEnd() {
        isDragging = false;
        document.removeEventListener('mousemove', drag);
        document.removeEventListener('mouseup', dragEnd);

        // Charge addition check when near the wool
        if (element === penggaris && isCloseEnough(penggaris, kainWol)) {
            addNegativeCharge();
        }
    }

    function setTranslate(xPos, yPos, el) {
        el.style.left = `${xPos}px`;
        el.style.top = `${yPos}px`;
    }
}

// Add negative charge
function addNegativeCharge() {
    if (muatanCount < maxMuatan) {
        const newCharge = document.createElement('img');
        newCharge.src = 'muatanNegatifSrc'; // Replace with actual source path
        newCharge.classList.add("muatan");
        muatanNegatifContainer.appendChild(newCharge);
        muatanCount++;
        console.log(`Muatan ditambahkan. Muatan saat ini: ${muatanCount}`);
    }
}

// Start decreasing charge near paper
function startDecreasingCharge() {
    chargeDecreasing = true;
    chargeInterval = setInterval(() => {
        if (muatanCount > 0) {
            muatanNegatifContainer.removeChild(muatanNegatifContainer.lastChild);
            muatanCount--;
            console.log(`Muatan saat ini: ${muatanCount}`);

            if (muatanCount === 0) {
                stopDecreasingCharge();
                resetSerpihanKertasPosition();
            }
        }
    }, 1000);
}

// Stop charge decrease
function stopDecreasingCharge() {
    chargeDecreasing = false;
    clearInterval(chargeInterval);
}

// Reset the paper's position
function resetSerpihanKertasPosition() {
    serpihanKertas.style.left = '50%';
    serpihanKertas.style.top = '50%';
}

// Move paper towards ruler
function moveSerpihanToPenggaris() {
    const rulerRect = penggaris.getBoundingClientRect();
    serpihanKertas.style.left = `${rulerRect.left + 10}px`;
    serpihanKertas.style.top = `${rulerRect.top + 10}px`;
}

// Check proximity between elements
function isCloseEnough(elem1, elem2, range = 100) {
    const rect1 = elem1.getBoundingClientRect();
    const rect2 = elem2.getBoundingClientRect();
    const horizontalDistance = Math.abs(rect1.left - rect2.left);
    const verticalDistance = Math.abs(rect1.top - rect2.top);
    return (horizontalDistance <= range && verticalDistance <= range);
}

// Function to get the current material from the URL
function getCurrentMaterialFromURL() {
    const path = window.location.pathname;
    const material = path.split('/')[2]; // Extracts the material from the URL path
    if (!material) {
        console.error('No material specified in URL');
    }
    return material;
}

// Submit conclusion and save simulation result using /submit_material_progress
document.getElementById('submitConclusion').addEventListener('click', function() {
    const conclusionText = document.getElementById('conclusionText').value;
    const material = getCurrentMaterialFromURL(); // Get the material dynamically from URL path

    if (!material) {
        alert("Please enter a valid material name.");
        return;
    }

    // Submit only the conclusion for praktikum (no score)
    fetch('/submit_material_progress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            material: material,  // Use the material dynamically from the URL
            is_praktikum: true, // Indicating this is a praktikum
            conclusion: conclusionText // User's conclusion
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert('Praktikum submitted successfully');
        } else {
            console.error('Error in praktikum submission:', data.error);
        }
    })
    .catch(error => console.error("Error submitting praktikum:", error));
});
