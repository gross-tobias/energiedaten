const API_BASE = 'http://localhost:5000/api';

let energyChart = null;
let chartData = {
    labels: [],
    datasets: []
};
let currentChartType = 'line';
let isLoadingData = false;
let hasShownNoDataMessage = false;

// Monatsnamen auf Deutsch
const monthNames = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];

// Initialisierung beim Laden der Seite
document.addEventListener('DOMContentLoaded', () => {
    initializeChart();
    loadData();
    setupEventListeners();
});

function setupEventListeners() {
    // Daten aktualisieren Button
    document.getElementById('fetchAllBtn').addEventListener('click', async () => {
        // Verhindere mehrfache Klicks
        const btn = document.getElementById('fetchAllBtn');
        if (btn.disabled) {
            return;
        }
        btn.disabled = true;
        btn.textContent = 'Lädt...';
        
        showLoading();
        try {
            const response = await fetch(`${API_BASE}/fetch-all`);
            const result = await response.json();
            if (result.success) {
                let message = 'Daten erfolgreich aktualisiert!\n\n';
                if (result.results) {
                    message += 'Ergebnisse:\n';
                    Object.keys(result.results).forEach(key => {
                        message += `- ${key}: ${result.results[key]}\n`;
                    });
                }
                alert(message);
                
                // Zurücksetzen des Flags, damit Nachricht wieder angezeigt werden kann
                hasShownNoDataMessage = false;
                
                // Warte kurz, damit Daten gespeichert werden können, dann lade Daten
                setTimeout(() => {
                    loadData();
                }, 2000);
            } else {
                alert('Fehler beim Aktualisieren der Daten: ' + (result.error || 'Unbekannter Fehler'));
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Fehler beim Aktualisieren der Daten: ' + error.message);
        } finally {
            hideLoading();
            btn.disabled = false;
            btn.textContent = 'Daten aktualisieren';
        }
    });

    // Diagrammtyp ändern
    document.getElementById('chartTypeSelect').addEventListener('change', (e) => {
        currentChartType = e.target.value;
        if (energyChart) {
            energyChart.destroy();
        }
        initializeChart();
        loadData();
    });

    // Datums-Picker Event Listener
    const startDateInput = document.getElementById('startDateInput');
    const endDateInput = document.getElementById('endDateInput');
    
    // Setze Standardwerte (letzte 30 Tage)
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(today.getDate() - 30);
    
    endDateInput.value = today.toISOString().split('T')[0];
    startDateInput.value = thirtyDaysAgo.toISOString().split('T')[0];
    
    startDateInput.addEventListener('change', () => {
        if (startDateInput.value && endDateInput.value) {
            if (new Date(startDateInput.value) > new Date(endDateInput.value)) {
                alert('Startdatum muss vor dem Enddatum liegen!');
                startDateInput.value = thirtyDaysAgo.toISOString().split('T')[0];
                return;
            }
            loadData();
        }
    });
    
    endDateInput.addEventListener('change', () => {
        if (startDateInput.value && endDateInput.value) {
            if (new Date(startDateInput.value) > new Date(endDateInput.value)) {
                alert('Startdatum muss vor dem Enddatum liegen!');
                endDateInput.value = today.toISOString().split('T')[0];
                return;
            }
            loadData();
        }
    });

    // Legend Toggles
    document.getElementById('toggleSolar').addEventListener('change', (e) => {
        toggleDataset('Solar', e.target.checked);
    });

    document.getElementById('toggleWindOnshore').addEventListener('change', (e) => {
        toggleDataset('Wind Onshore', e.target.checked);
    });

    document.getElementById('toggleWindOffshore').addEventListener('change', (e) => {
        toggleDataset('Wind Offshore', e.target.checked);
    });
}

function initializeChart() {
    const ctx = document.getElementById('energyChart').getContext('2d');
    
    const isPieChart = currentChartType === 'pie' || currentChartType === 'doughnut';
    
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            title: {
                display: true,
                text: 'Energieproduktion über Zeit',
                font: {
                    size: 20,
                    weight: 'bold'
                }
            },
            legend: {
                display: !isPieChart,
                position: 'top'
            },
            tooltip: {
                mode: isPieChart ? 'point' : 'index',
                intersect: false,
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        label += context.parsed.y ? context.parsed.y.toFixed(2) + ' kWh' : context.parsed;
                        return label;
                    }
                }
            }
        }
    };
    
    if (!isPieChart) {
        chartOptions.scales = {
            x: {
                display: true,
                title: {
                    display: true,
                    text: 'Zeitraum'
                },
                grid: {
                    display: true,
                    drawBorder: false,
                    borderDash: [5, 5],
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                ticks: {
                    maxRotation: 45,
                    minRotation: 45,
                    callback: function(value, index) {
                        const label = this.getLabelForValue(value);
                        return label;
                    }
                }
            },
            y: {
                display: true,
                title: {
                    display: true,
                    text: 'Energie (kWh)'
                },
                beginAtZero: true,
                ticks: {
                    callback: function(value) {
                        return value.toFixed(0) + ' kWh';
                    }
                }
            }
        };
        chartOptions.interaction = {
            mode: 'nearest',
            axis: 'x',
            intersect: false
        };
    }
    
    energyChart = new Chart(ctx, {
        type: currentChartType,
        data: chartData,
        options: chartOptions
    });
}

async function loadData() {
    // Verhindere mehrfache gleichzeitige Aufrufe
    if (isLoadingData) {
        console.log('loadData() läuft bereits, überspringe...');
        return;
    }
    
    isLoadingData = true;
    showLoading();
    
    try {
        // Datum aus Inputs lesen
        const startDateInput = document.getElementById('startDateInput');
        const endDateInput = document.getElementById('endDateInput');
        
        let startDate = startDateInput.value || null;
        let endDate = endDateInput.value || null;
        
        // End-Datum auf Ende des Tages setzen (23:59:59)
        if (endDate) {
            endDate = endDate + ' 23:59:59';
        }

        // Daten laden
        let url = `${API_BASE}/energy-data`;
        const params = [];
        if (startDate) {
            params.push(`start=${startDate}`);
        }
        if (endDate) {
            params.push(`end=${endDate}`);
        }
        if (params.length > 0) {
            url += '?' + params.join('&');
        }

        const response = await fetch(url);
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // Prüfe ob Daten vorhanden sind
        const hasData = Object.keys(data).length > 0 && 
                       Object.values(data).some(source => source.values && source.values.length > 0);
        
        if (!hasData) {
            console.warn('Keine Daten gefunden. Bitte zuerst Daten aktualisieren.');
            console.log('API Response:', data);
            
            // Zeige Nachricht nur einmal
            if (!hasShownNoDataMessage) {
                hasShownNoDataMessage = true;
                const message = 'Keine Daten in der Datenbank gefunden.\n\n' +
                              'Bitte klicken Sie auf "Daten aktualisieren" um Daten von der Energy Charts API zu laden.\n\n' +
                              'Dies kann einige Sekunden dauern.';
                alert(message);
            }
            return;
        }

        // Daten gefunden - zurücksetzen des Flags
        hasShownNoDataMessage = false;

        // Chart-Daten aktualisieren
        updateChart(data);

        // Durchschnittswerte für Stat-Cards berechnen
        calculateAverages(data);

    } catch (error) {
        console.error('Error loading data:', error);
        alert('Fehler beim Laden der Daten: ' + error.message);
    } finally {
        hideLoading();
        isLoadingData = false;
    }
}

function groupDataByMonth(labels, values) {
    const monthlyData = {};
    
    labels.forEach((label, index) => {
        const date = new Date(label);
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        const monthLabel = `${monthNames[date.getMonth()]} ${date.getFullYear()}`;
        
        if (!monthlyData[monthKey]) {
            monthlyData[monthKey] = {
                label: monthLabel,
                values: [],
                sum: 0,
                count: 0
            };
        }
        
        if (values[index] !== null && values[index] !== undefined) {
            monthlyData[monthKey].values.push(values[index]);
            monthlyData[monthKey].sum += values[index];
            monthlyData[monthKey].count++;
        }
    });
    
    // Durchschnitt pro Monat berechnen
    const result = {
        labels: [],
        values: []
    };
    
    Object.keys(monthlyData).sort().forEach(key => {
        const month = monthlyData[key];
        result.labels.push(month.label);
        result.values.push(month.sum / month.count); // Durchschnitt
    });
    
    return result;
}

function calculateTimeRange() {
    const startDateInput = document.getElementById('startDateInput');
    const endDateInput = document.getElementById('endDateInput');
    
    if (!startDateInput.value || !endDateInput.value) {
        return { days: 30, type: 'month' };
    }
    
    const start = new Date(startDateInput.value);
    const end = new Date(endDateInput.value);
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays <= 7) {
        return { days: diffDays, type: 'day' };
    } else if (diffDays <= 90) {
        return { days: diffDays, type: 'month' };
    } else if (diffDays <= 365) {
        return { days: diffDays, type: 'year' };
    } else {
        return { days: diffDays, type: 'year' };
    }
}

function formatLabel(dateString, timeRangeType) {
    const date = new Date(dateString);
    
    if (timeRangeType === 'day') {
        return `${String(date.getDate()).padStart(2, '0')}.${String(date.getMonth() + 1).padStart(2, '0')}`;
    } else if (timeRangeType === 'month') {
        return `${monthNames[date.getMonth()]} ${date.getFullYear()}`;
    } else {
        return `${monthNames[date.getMonth()]} ${date.getFullYear()}`;
    }
}

function updateChart(data) {
    const colors = {
        'Solar': '#FFD700',
        'Wind Onshore': '#4CAF50',
        'Wind Offshore': '#2196F3'
    };

    const isPieChart = currentChartType === 'pie' || currentChartType === 'doughnut';
    const timeRange = calculateTimeRange();
    
    if (isPieChart) {
        // Für Kreisdiagramme: Summe aller Werte pro Energiequelle
        const datasets = [];
        const labels = [];
        const values = [];
        const backgroundColors = [];
        
        Object.keys(data).forEach(sourceName => {
            const sourceData = data[sourceName];
            const sum = sourceData.values.reduce((acc, val) => acc + (val || 0), 0);
            if (sum > 0) {
                labels.push(sourceName);
                values.push(sum);
                backgroundColors.push(colors[sourceName] || '#000000');
            }
        });
        
        chartData.labels = labels;
        chartData.datasets = [{
            label: 'Energieproduktion',
            data: values,
            backgroundColor: backgroundColors,
            borderWidth: 2,
            borderColor: '#fff'
        }];
    } else {
        // Sammle alle eindeutigen Labels
        const allLabels = new Set();
        Object.values(data).forEach(source => {
            source.labels.forEach(label => allLabels.add(label));
        });
        const sortedLabels = Array.from(allLabels).sort();

        let processedLabels = [];
        let processedData = {};

        if (timeRange.type === 'day') {
            // Bei Tagen: Zeige einzelne Tage
            processedLabels = sortedLabels;
            Object.keys(data).forEach(sourceName => {
                processedData[sourceName] = {
                    labels: data[sourceName].labels,
                    values: data[sourceName].values
                };
            });
        } else if (timeRange.type === 'month') {
            // Bei Monaten: Gruppiere nach Monaten
            const monthlyData = {};
            Object.keys(data).forEach(sourceName => {
                monthlyData[sourceName] = groupDataByMonth(data[sourceName].labels, data[sourceName].values);
            });

            const allMonths = new Set();
            Object.values(monthlyData).forEach(source => {
                source.labels.forEach(month => allMonths.add(month));
            });
            
            processedLabels = Array.from(allMonths).sort((a, b) => {
                const partsA = a.split(' ');
                const partsB = b.split(' ');
                if (partsA.length !== 2 || partsB.length !== 2) return a.localeCompare(b);
                
                const [monthA, yearA] = partsA;
                const [monthB, yearB] = partsB;
                const yearNumA = parseInt(yearA);
                const yearNumB = parseInt(yearB);
                
                if (yearNumA !== yearNumB) return yearNumA - yearNumB;
                
                const monthIndexA = monthNames.indexOf(monthA);
                const monthIndexB = monthNames.indexOf(monthB);
                return monthIndexA - monthIndexB;
            });
            
            Object.keys(monthlyData).forEach(sourceName => {
                processedData[sourceName] = monthlyData[sourceName];
            });
        } else {
            // Bei Jahren: Zeige alle 12 Monate
            const monthlyData = {};
            Object.keys(data).forEach(sourceName => {
                monthlyData[sourceName] = groupDataByMonth(data[sourceName].labels, data[sourceName].values);
            });

            const allMonths = new Set();
            Object.values(monthlyData).forEach(source => {
                source.labels.forEach(month => allMonths.add(month));
            });
            
            processedLabels = Array.from(allMonths).sort((a, b) => {
                const partsA = a.split(' ');
                const partsB = b.split(' ');
                if (partsA.length !== 2 || partsB.length !== 2) return a.localeCompare(b);
                
                const [monthA, yearA] = partsA;
                const [monthB, yearB] = partsB;
                const yearNumA = parseInt(yearA);
                const yearNumB = parseInt(yearB);
                
                if (yearNumA !== yearNumB) return yearNumA - yearNumB;
                
                const monthIndexA = monthNames.indexOf(monthA);
                const monthIndexB = monthNames.indexOf(monthB);
                return monthIndexA - monthIndexB;
            });
            
            Object.keys(monthlyData).forEach(sourceName => {
                processedData[sourceName] = monthlyData[sourceName];
            });
        }

        // Datasets erstellen
        const datasets = [];
        
        Object.keys(processedData).forEach(sourceName => {
            const sourceData = processedData[sourceName];
            const values = new Array(processedLabels.length).fill(0);
            
            sourceData.labels.forEach((label, index) => {
                const labelIndex = processedLabels.indexOf(label);
                if (labelIndex !== -1) {
                    values[labelIndex] = sourceData.values[index];
                }
            });

            const datasetConfig = {
                label: sourceName,
                data: values,
                borderColor: colors[sourceName] || '#000000',
                backgroundColor: colors[sourceName] ? `${colors[sourceName]}80` : '#00000080',
                borderWidth: 3
            };

            if (currentChartType === 'line') {
                datasetConfig.fill = false;
                datasetConfig.tension = 0.4;
                datasetConfig.pointRadius = 3;
                datasetConfig.pointHoverRadius = 6;
            } else if (currentChartType === 'bar') {
                datasetConfig.borderRadius = 5;
            } else if (currentChartType === 'radar') {
                datasetConfig.fill = true;
                datasetConfig.tension = 0.4;
            }

            datasets.push(datasetConfig);
        });

        chartData.labels = processedLabels;
        chartData.datasets = datasets;
    }
    
    // X-Achse aktualisieren mit gestrichelten Linien und Titel
    if (!isPieChart && energyChart) {
        const timeRange = calculateTimeRange();
        let xAxisTitle = 'Zeitraum';
        
        if (timeRange.type === 'day') {
            xAxisTitle = 'Tag';
        } else if (timeRange.type === 'month') {
            xAxisTitle = 'Monat';
        } else {
            xAxisTitle = 'Monat';
        }
        
        energyChart.options.scales.x.title.text = xAxisTitle;
        energyChart.options.scales.x.grid = {
            display: true,
            drawBorder: false,
            borderDash: [5, 5],
            color: 'rgba(0, 0, 0, 0.1)'
        };
    }
    
    energyChart.data = chartData;
    energyChart.update();
}

function calculateAverages(data) {
    // Berechne Durchschnittswerte für jede Energiequelle
    const averages = {};
    
    Object.keys(data).forEach(sourceName => {
        const sourceData = data[sourceName];
        if (sourceData.values && sourceData.values.length > 0) {
            // Filtere null/undefined Werte heraus
            const validValues = sourceData.values.filter(val => val !== null && val !== undefined && !isNaN(val));
            
            if (validValues.length > 0) {
                const sum = validValues.reduce((acc, val) => acc + val, 0);
                const average = sum / validValues.length;
                averages[sourceName] = average;
            }
        }
    });
    
    // Formatiere und zeige Durchschnittswerte in Stat-Cards
    function formatValue(value) {
        if (value >= 1000000) {
            return (value / 1000000).toFixed(2) + 'M';
        } else if (value >= 1000) {
            return (value / 1000).toFixed(2) + 'k';
        } else {
            return value.toFixed(2);
        }
    }
    
    // Solar Average
    if (averages['Solar'] !== undefined) {
        document.getElementById('solarValue').textContent = formatValue(averages['Solar']);
    } else {
        document.getElementById('solarValue').textContent = '-';
    }
    
    // Wind Onshore Average
    if (averages['Wind Onshore'] !== undefined) {
        document.getElementById('windOnshoreValue').textContent = formatValue(averages['Wind Onshore']);
    } else {
        document.getElementById('windOnshoreValue').textContent = '-';
    }
    
    // Wind Offshore Average
    if (averages['Wind Offshore'] !== undefined) {
        document.getElementById('windOffshoreValue').textContent = formatValue(averages['Wind Offshore']);
    } else {
        document.getElementById('windOffshoreValue').textContent = '-';
    }
}

function toggleDataset(sourceName, visible) {
    const dataset = energyChart.data.datasets.find(ds => ds.label === sourceName);
    if (dataset) {
        dataset.hidden = !visible;
        energyChart.update();
    }
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}
