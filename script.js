document.addEventListener('DOMContentLoaded', () => {
  const btnContrast = document.getElementById('btn-contrast');
  const btnIncrease = document.getElementById('btn-font-increase');
  const btnDecrease = document.getElementById('btn-font-decrease');
  const form = document.getElementById('booking-form');
  const bookingsList = document.getElementById('bookings-list');

  let currentFontSize = 16;
  let bookings = [];

  // Recurso de Acessibilidade 1: Alto Contraste
  btnContrast.addEventListener('click', () => {
    document.body.classList.toggle('high-contrast');
  });

  // Recurso de Acessibilidade 2: Redimensionamento de Fonte
  btnIncrease.addEventListener('click', () => {
    if (currentFontSize < 24) {
      currentFontSize += 2;
      document.documentElement.style.setProperty('--font-size', `${currentFontSize}px`);
    }
  });

  btnDecrease.addEventListener('click', () => {
    if (currentFontSize > 12) {
      currentFontSize -= 2;
      document.documentElement.style.setProperty('--font-size', `${currentFontSize}px`);
    }
  });

  // Fluxo de Uso Geral: Registar Agendamento na Lista
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = document.getElementById('student-name').value;
    const belt = document.getElementById('belt').value;
    const time = document.getElementById('class-time').value;

    // Adiciona o novo agendamento ao array
    bookings.push({ name, belt, time });

    // Atualiza a interface da lista
    renderBookings();
    form.reset();
  });

  function renderBookings() {
    if (bookings.length === 0) {
      bookingsList.innerHTML = '<li style="color: #666;">Nenhum agendamento realizado ainda.</li>';
      return;
    }

    bookingsList.innerHTML = '';
    bookings.forEach((b, index) => {
      const li = document.createElement('li');
      li.style.marginBottom = '8px';
      li.innerHTML = `<strong>${index + 1}. Atleta:</strong> ${b.name} (${b.belt}) — <em>${b.time}</em>`;
      bookingsList.appendChild(li);
    });
  }
});