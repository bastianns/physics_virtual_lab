// Selecting necessary elements
const body = document.querySelector("body"),
  sidebar = body.querySelector(".sidebar"),
  toggle = body.querySelector(".toggle"),
  container = document.querySelector(".container"),
  scoreDisplay = document.getElementById("userScore");

let userScore = 0;
const maxScore = 100;
const correctAnswerPoints = maxScore / 5;
let currentMaterial = '';
let isCompleted = false;
let isQuestionCompleted = {};

toggle.addEventListener("click", () => {
  sidebar.classList.toggle("close");

  if (sidebar.classList.contains('close')) {
    container.style.paddingLeft = '70px';
  } else {
    container.style.paddingLeft = '250px';
  }
});

function toggleAnswer(questionNumber) {
  const button = document.getElementById(`toggleButton${questionNumber}`);
  const jawabanInput = document.getElementById(`jawabanInput${questionNumber}`);
  const submitButton = document.getElementById(`submitButton${questionNumber}`);

  if (isQuestionCompleted[questionNumber]) {
    alert('Anda sudah menyelesaikan latihan ini sebelumnya.');
    return;
  }

  if (!jawabanInput.value || jawabanInput.value.trim() === '') {
    button.textContent = 'Sembunyikan Jawaban';
    jawabanInput.value = getCorrectAnswer(questionNumber);
    submitButton.style.display = 'none';
  } else {
    button.textContent = 'Tampilkan Jawaban';
    jawabanInput.value = '';
    submitButton.style.display = 'block';
  }

  if (jawabanInput.value.trim() !== '') {
    button.disabled = true;
    submitButton.style.display = 'none';
  }
}

function getCorrectAnswer(questionNumber) {
  switch (questionNumber) {
    case 1:
      return '5';
    case 2:
      return '1';
    case 3:
      return 'Jakarta';
    case 4:
      return '3';
    case 5:
      return 'Biru';
    default:
      return '';
  }
}

function submitJawaban(questionNumber) {
  if (isQuestionCompleted[questionNumber]) {
    alert('Anda sudah menyelesaikan latihan ini sebelumnya.');
    return;
  }

  const jawabanInput = document.getElementById(`jawabanInput${questionNumber}`);
  const userAnswer = jawabanInput.value.trim();
  const correctAnswer = getCorrectAnswer(questionNumber);

  if (userAnswer === correctAnswer) {
    userScore += correctAnswerPoints;
    alert('Jawaban Anda Benar!');
  } else {
    alert('Jawaban Anda Salah!');
  }

  isQuestionCompleted[questionNumber] = true;
  document.getElementById(`submitButton${questionNumber}`).style.display = 'none';

  updateScoreDisplay();
  toggleMateri(questionNumber);
}

function updateScoreDisplay() {
  scoreDisplay.textContent = `Skor Anda: ${userScore}`;

  // Send score to the server
  sendProgressToServer();
}

function sendProgressToServer() {
  fetch('/submit_material_progress', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      score: userScore,
      material: currentMaterial,
      is_praktikum: false
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.message) {
      console.log("Progress updated:", data.message);
    } else {
      console.error("Failed to update progress:", data.error);
    }
  })
  .catch(error => console.error("Error:", error));
}

function toggleMateri(questionNumber) {
  const materiDiv = document.getElementById(`materi${questionNumber}`);
  const materiBtn = document.getElementById(`materiBtn${questionNumber}`);

  if (isCompleted) {
    if (!materiDiv.classList.contains('hidden')) {
      alert('Materi sudah ditampilkan, tidak bisa ditampilkan lagi.');
    }
    materiBtn.disabled = true;
    materiBtn.style.backgroundColor = '#f0f0f0';
  }

  materiDiv.classList.toggle('hidden');
}

function getCurrentMaterialFromURL() {
  const path = window.location.pathname;
  const material = path.split('/')[2];
  if (!material) {
    console.error('No material specified in URL');
  }
  return material;
}

document.addEventListener('DOMContentLoaded', function () {
  const material = getCurrentMaterialFromURL();
  if (material) {
    currentMaterial = material;
    console.log('Current material set to:', material);
    updatePageTitle(material);
  } else {
    console.error('No material specified in URL');
  }
});

function updatePageTitle(material) {
  const pageTitle = document.querySelector('h1');
  if (pageTitle) {
    pageTitle.textContent = `Latihan - ${material.replace(/_/g, ' ')}`;
  }
}