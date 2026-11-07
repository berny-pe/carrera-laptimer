const form = document.getElementById('setupForm');
const errorBox = document.getElementById('setupError');

function selectedMode() {
    return form.querySelector('input[name="mode"]:checked').value;
}

function updateFields() {
    const mode = selectedMode();
    document.getElementById('lapsField').hidden = mode !== 'laps';
    document.getElementById('timeField').hidden = mode !== 'time';
}

form.querySelectorAll('input[name="mode"]').forEach(function (radio) {
    radio.addEventListener('change', updateFields);
});

form.addEventListener('submit', function (event) {
    event.preventDefault();
    errorBox.textContent = '';

    const mode = selectedMode();
    const payload = { mode: mode };
    if (mode === 'laps') {
        payload.laps = parseInt(document.getElementById('laps').value, 10);
    } else {
        payload.time_seconds = Math.round(parseFloat(document.getElementById('minutes').value) * 60);
    }

    fetch('/api/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
        .then(function (response) {
            return response.json().then(function (data) {
                if (!response.ok) throw new Error(data.error || 'Invalid settings');
                window.location.href = '/race';
            });
        })
        .catch(function (err) {
            errorBox.textContent = err.message;
        });
});

updateFields();
