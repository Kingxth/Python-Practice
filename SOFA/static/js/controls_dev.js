
import { moveSimulatedPresence } from './app.js';
document.addEventListener('keydown', (event) => {
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
    return;
  }

  switch (event.key) {
    case 'ArrowUp':
    case 'w':
    case 'W':
      moveSimulatedPresence(1, 0); // Norte
      break;

    case 'ArrowDown':
    case 's':
    case 'S':
      moveSimulatedPresence(-1, 0); // Sur
      break;

    case 'ArrowLeft':
    case 'a':
    case 'A':
      moveSimulatedPresence(0, -1); // Oeste
      break;

    case 'ArrowRight':
    case 'd':
    case 'D':
      moveSimulatedPresence(0, 1); // Este
      break;
  }
});

console.log('🎮 Controles de Teclado (Flechas / WASD) activados.');