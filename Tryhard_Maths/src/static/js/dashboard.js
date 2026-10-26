document.addEventListener('DOMContentLoaded', () => {
    // Verificacion de que la variable existe 

    if (typeof rawDesglose === 'undefined') {
        console.warn('No se encontraron datos para el dashboard.');
        return;
    }

    const labelsBonitos = rawDesglose.map(item => {
        return item.tipo_operacion.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    });

    const scores = rawDesglose.map(item => {
        let aciertos = Number(item.aciertos) || 0;
        let intentos = Number(item.total) || 1;
        let calcScore = intentos > 0 ? Math.round((aciertos / intentos) * 100) : 0;
        let val = item.porcentaje_acierto !== undefined && item.porcentaje_acierto !== null 
                  ? Number(item.porcentaje_acierto) 
                  : calcScore;
        return Math.max(0, Math.min(100, val));
    });

    const velocidades = rawDesglose.map(item => {
        let tiempo = Number(item.tiempo_promedio_seg) || 5;
        let vel = Math.max(0, Math.round(100 - (tiempo * 5))); 
        return Math.max(0, Math.min(100, vel));
    });

    const canvasElement = document.getElementById('radarChart');
    if (canvasElement) {
        const ctx = canvasElement.getContext('2d');
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labelsBonitos,
                datasets: [
                    {
                        label: 'Score / Acierto (%)',
                        data: scores,
                        backgroundColor: 'rgba(255, 255, 255, 0.15)',
                        borderColor: '#ffffff',
                        pointBackgroundColor: '#ffffff',
                        pointBorderColor: '#000000',
                        pointRadius: 4,
                        borderWidth: 2
                    },
                    {
                        label: 'Velocidad (Índice 0-100)',
                        data: velocidades,
                        backgroundColor: 'rgba(100, 100, 100, 0.05)',
                        borderColor: '#777777',
                        pointBackgroundColor: '#333333',
                        pointBorderColor: '#777777',
                        pointRadius: 3,
                        borderWidth: 1.5
                    }
                ]
            },
            options: {
                scales: {
                    r: {
                        angleLines: { color: '#333333' },
                        grid: { color: '#333333' },
                        pointLabels: { color: '#cccccc', font: { size: 11, weight: '500' } },
                        ticks: {
                            backdropColor: 'transparent',
                            color: '#666666',
                            min: 0,
                            max: 100,
                            stepSize: 20
                        }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#cccccc', font: { size: 11 } } }
                }
            }
        });
    }
});