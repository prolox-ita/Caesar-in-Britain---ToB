const dateData = {
    'cesare': {
        title: "Giulio Cesare",
        desc: "La prima volta che le aquile romane hanno toccato il suolo britannico (55-54 BCE). Una sfida contro le maree e le tribù di Cassivellauno.",
        leader: "Leader: C. Iulius Caesar",
        img: "[Placeholder Immagine Cesare]"
    },
    'claudio': {
        title: "L'Imperatore Claudio",
        desc: "Nel 43 AD, Roma torna per restare. Quattro legioni attraversano la Manica per sottomettere definitivamente i Britanni.",
        leader: "Leader: Aulus Plautius / Claudius",
        img: "[Placeholder Immagine Claudio]"
    }
};

function showDate(key) {
    // Aggiorna classi attive
    document.querySelectorAll('.timeline-item').forEach(el => {
        el.classList.remove('active');
    });
    event.currentTarget.classList.add('active');

    // Aggiorna i testi con una piccola animazione di fade
    const container = document.getElementById('date-details');
    container.style.opacity = 0;

    setTimeout(() => {
        document.getElementById('detail-title').innerText = dateData[key].title;
        document.getElementById('detail-desc').innerText = dateData[key].desc;
        document.querySelector('.leader-tag').innerText = dateData[key].leader;
        container.style.opacity = 1;
    }, 300);
}


const CAMPAIGNS = [
    {
        year: '56-55 BCE',
        title: "Caesar's First Expedition",
        desc: "Julius Caesar crosses the channel with two legions — the first Roman commander to set foot on the shores of Britannia. The landing is contested, the terrain unfamiliar, and the tribes resistant. A beachhead is established and then abandoned. Caesar returns to Gaul, but the island's call remains.",
        status: 'In Development', playable: false, link: 'In development'

    },
    {
        year: '43 AD',
        title: 'The Claudian Invasion',
        desc: "Emperor Claudius dispatches four legions under Aulus Plautius to complete what Caesar began. A new era of Roman conquest is underway — and Britannia will never be the same.",
        status: 'Planned', playable: false, link: 'In development'
    }
];

document.querySelectorAll('.tl-dot:not(.future)').forEach(dot => {
    dot.addEventListener('click', () => {
        const idx = parseInt(dot.dataset.idx);
        document.querySelectorAll('.tl-dot').forEach((d, i) => d.classList.toggle('active', i === idx));
        const c = CAMPAIGNS[idx];
        document.getElementById('tlCard').innerHTML = `
                <p class="tl-card-year">${c.year}</p>
                <h3 class="tl-card-title">${c.title}</h3>
                <p class="tl-card-desc">${c.desc}</p>
                <span class="tl-card-status ${c.playable ? 'playable' : 'dev'}">${c.status}</span>
                <span class="tl-link">${c.link}</span>
            `;
    });
});