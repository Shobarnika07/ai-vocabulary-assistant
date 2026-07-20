function showToast(message, type) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = 'toast ' + type;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function spawnConfetti() {
    const colors = ['#FF6B9D', '#4D96FF', '#FFD93D', '#2ECC71', '#9B59B6', '#FF8C42'];
    for (let i = 0; i < 20; i++) {
        const conf = document.createElement('div');
        conf.style.cssText = 'position:fixed;width:10px;height:10px;border-radius:2px;pointer-events:none;z-index:9999;animation:confetti 1s ease forwards;';
        conf.style.left = Math.random() * 100 + 'vw';
        conf.style.top = Math.random() * 60 + 40 + 'vh';
        conf.style.background = colors[Math.floor(Math.random() * colors.length)];
        conf.style.transform = 'rotate(' + Math.random() * 360 + 'deg)';
        document.body.appendChild(conf);
        setTimeout(() => conf.remove(), 1200);
    }
}

function deleteWord(id) {
    if (!confirm('Delete this word?')) return;
    fetch('/api/delete/' + id, { method: 'DELETE' })
        .then(function(r) { return r.json(); })
        .then(function() {
            var card = document.querySelector('.word-card[data-id="' + id + '"]');
            if (card) {
                card.style.transition = 'all 0.4s ease';
                card.style.transform = 'translateX(60px) scale(0.9)';
                card.style.opacity = '0';
                setTimeout(function() { card.remove(); }, 400);
            }
            showToast('Word removed!', 'info');
        });
}

function addSample(word, meaning, example, category) {
    var form = new FormData();
    form.append('word', word);
    form.append('meaning', meaning);
    form.append('example', example);
    form.append('category', category);
    fetch('/add', {
        method: 'POST',
        body: new URLSearchParams(form),
    }).then(function() {
        var btn = event.target;
        btn.classList.add('added');
        btn.innerHTML = '&#10004; Added!';
        showToast('"' + word + '" added! Great choice!', 'success');
        setTimeout(function() {
            btn.classList.remove('added');
            btn.textContent = word;
        }, 2000);
    });
}

function importWords() {
    var area = document.getElementById('import-area');
    var result = document.getElementById('import-result');
    if (!area.value.trim()) return;
    var form = new FormData();
    form.append('words', area.value);
    fetch('/api/import', {
        method: 'POST',
        body: new URLSearchParams(form),
    })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.success) {
                result.innerHTML = '&#127881; Imported ' + data.imported + ' words! Reloading...';
                result.style.color = 'var(--green)';
                area.value = '';
                spawnConfetti();
                setTimeout(function() { location.reload(); }, 1500);
            } else {
                result.innerHTML = '&#128532; Error: ' + data.error;
                result.style.color = 'var(--red)';
            }
        });
}

document.addEventListener('DOMContentLoaded', function() {
    var optionBtns = document.querySelectorAll('.option-btn');
    optionBtns.forEach(function(btn) {
        btn.addEventListener('mouseenter', function() {
            this.style.animation = 'none';
            this.offsetHeight;
            this.style.animation = '';
        });
    });
});
