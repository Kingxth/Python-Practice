// Módulo de Brújula para Dispositivos Móviles

import { setPlayerOrientation } from './app.js';

let compassActive = false;

export function initCompass() {
  // Verificar si el dispositivo soporta lectura de orientación
  if (!window.DeviceOrientationEvent) {
    console.warn('⚠️ Tu navegador o dispositivo no soporta la brújula (DeviceOrientation).');
    return;
  }

  // Soporte para iOS (iPhone requiere solicitud explícita de permiso)
  if (typeof DeviceOrientationEvent.requestPermission === 'function') {
    DeviceOrientationEvent.requestPermission()
      .then(permissionState => {
        if (permissionState === 'granted') {
          startCompassListener();
        } else {
          console.warn('❌ Permiso de brújula denegado por el usuario.');
        }
      })
      .catch(console.error);
  } else {
    // Android y navegadores estándar
    startCompassListener();
  }
}

function startCompassListener() {
  if (compassActive) return;

  window.addEventListener('deviceorientation', handleOrientation, true);
  compassActive = true;
  console.log('🧭 Brújula activada correctamente.');
}

function handleOrientation(event) {
  let heading = null;

  // iOS provee el Norte directo en webkitCompassHeading
  if (event.webkitCompassHeading !== undefined && event.webkitCompassHeading !== null) {
    heading = event.webkitCompassHeading;
  } 
  // Android / Chrome (alpha representa el giro respecto al Norte magnético)
  else if (event.alpha !== null) {
    heading = 360 - event.alpha;
  }

  if (heading !== null) {
    // Normalizar entre 0° y 360°
    heading = (heading + 360) % 360;
    
    // Actualizar la rotación del cono de visión en app.js
    setPlayerOrientation(Math.round(heading));
  }
}