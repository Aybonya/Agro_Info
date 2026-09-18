/**
 * AgroFlow — Интеллектуальная система контроля зерноуборки,
 * весового контроля (Anti-Fraud) и GPS-мониторинга техники.
 * Разработано для Хакатона (Кейс №2).
 */

const today = '18.09.2026';
const fmt = n => new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 1 }).format(n);
const money = n => new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(n) + ' ₸';
const uid = () => Date.now().toString(36);

// Исходная база данных (Костанайская область, Костанайский район / Заречное)
const seed = {
  vehicles: [
    { plate: '10 523 ARA', type: 'Трактор John Deere 8320R + ПСТБ-17', tare: 9200, driver: 'Ерлан М.', lat: 53.188, lng: 63.742, speed: 28, fieldTime: 42, status: 'На поле №1 (Заречное)', icon: '🚜' },
    { plate: '10 814 BSM', type: 'КАМАЗ 6520 Зерновоз', tare: 11400, driver: 'Нурлан С.', lat: 53.202, lng: 63.715, speed: 44, fieldTime: 18, status: 'В пути на Костанайский элеватор', icon: '🚚' },
    { plate: '10 296 KDA', type: 'МТЗ-82 Беларус + 2ПТС-4', tare: 6850, driver: 'Данияр А.', lat: 53.165, lng: 63.722, speed: 19, fieldTime: 65, status: 'На поле №2 (Тобыл)', icon: '🚜' },
    { plate: '10 107 ABC', type: 'Volvo FMX 460 Тент', tare: 12800, driver: 'Алексей В.', lat: 53.195, lng: 63.685, speed: 0, fieldTime: 32, status: 'На весовой элеватора', icon: '🚚' },
    { plate: '10 845 KZX', type: 'Shacman SX3258 Зерновоз', tare: 13200, driver: 'Бауыржан К.', lat: 53.218, lng: 63.795, speed: 36, fieldTime: 25, status: 'В пути к полю №3 (Майколь)', icon: '🚚' }
  ],
  combines: [
    { id: 'c1', name: 'CLAAS Lexion 770 (#C-101)', operator: 'Виктор П.', field: 'f1', bunkerCap: 12500, bunkerCurrent: 10800, moisture: 13.2, icon: '🌾' },
    { id: 'c2', name: 'Ростсельмаш Torum 785 (#C-102)', operator: 'Серик Т.', field: 'f2', bunkerCap: 12000, bunkerCurrent: 8900, moisture: 14.0, icon: '🌾' },
    { id: 'c3', name: 'John Deere S780 (#C-103)', operator: 'Марат Е.', field: 'f3', bunkerCap: 14000, bunkerCurrent: 12200, moisture: 12.8, icon: '🌾' }
  ],
  fields: [
    { id: 'f1', name: 'Поле №1 — «Заречное»', crop: 'Пшеница яровая твердая', area: 240, harvested: 218, expected: 24.5, color: '#488c52', coords: [[53.178, 63.728], [53.198, 63.728], [53.198, 63.765], [53.178, 63.765]] },
    { id: 'f2', name: 'Поле №2 — «Тобыл Южное»', crop: 'Ячмень пивоваренный', area: 180, harvested: 142, expected: 20.2, color: '#7ea843', coords: [[53.155, 63.705], [53.174, 63.705], [53.174, 63.742], [53.155, 63.742]] },
    { id: 'f3', name: 'Поле №3 — «Майколь»', crop: 'Пшеница мягкая сильная', area: 320, harvested: 285, expected: 22.8, color: '#3d7246', coords: [[53.208, 63.775], [53.232, 63.775], [53.232, 63.830], [53.208, 63.830]] }
  ],
  warehouses: [
    { id: 'w1', name: 'Костанайский Элеватор №1 (Заречный)', capacity: 35000, lat: 53.195, lng: 63.685 },
    { id: 'w2', name: 'Хлебоприемный пункт «Тобыл»', capacity: 15000, lat: 53.168, lng: 63.690 },
    { id: 'w3', name: 'Зерносклад отделения «Майколь»', capacity: 12000, lat: 53.225, lng: 63.815 }
  ],
  bunkerTickets: [
    { id: 'bt-1', combineId: 'c1', plate: '10 523 ARA', fieldId: 'f1', crop: 'Пшеница', weight: 12960, time: '18.09, 07:55', signature: 'П. Виктор (механизатор)', verified: true },
    { id: 'bt-2', combineId: 'c2', plate: '10 814 BSM', fieldId: 'f2', crop: 'Ячмень', weight: 14600, time: '18.09, 08:15', signature: 'Т. Серик (механизатор)', verified: true },
    { id: 'bt-3', combineId: 'c1', plate: '10 296 KDA', fieldId: 'f1', crop: 'Пшеница', weight: 11130, time: '18.09, 09:30', signature: 'П. Виктор (механизатор)', verified: true },
    { id: 'bt-4', combineId: 'c3', plate: '10 107 ABC', fieldId: 'f3', crop: 'Пшеница', weight: 15400, time: '18.09, 10:10', signature: 'Е. Марат (механизатор)', verified: false, fraudAlert: true }
  ],
  trips: [
    {
      id: 'r1',
      plate: '10 523 ARA',
      field: 'f1',
      crop: 'Пшеница',
      bunkerWeight: 12960,
      entry: '18.09, 07:42',
      exit: '18.09, 08:36',
      fieldDwellMin: 54,
      transitTimeMin: 35,
      transitAnomaly: false,
      tare: 9200,
      gross: 22140,
      net: 12940,
      discrepancyKg: -20,
      discrepancyPct: -0.15,
      warehouse: 'w1',
      arrived: '18.09, 09:11',
      aiModelScore: 0.964,
      aiDetectedPlate: '10 523 ARA',
      aiBodyType: 'truck',
      fraudVerdict: 'OK',
      unloaded: true,
      cameraSnapshot: 'web_assets/camera/annotated_10.jpg',
      plateCrop: 'web_assets/camera/plate_10.jpg'
    },
    {
      id: 'r2',
      plate: '10 814 BSM',
      field: 'f2',
      crop: 'Ячмень',
      bunkerWeight: 14600,
      entry: '18.09, 08:05',
      exit: '18.09, 09:02',
      fieldDwellMin: 57,
      transitTimeMin: 38,
      transitAnomaly: false,
      tare: 11400,
      gross: 25980,
      net: 14580,
      discrepancyKg: -20,
      discrepancyPct: -0.14,
      warehouse: 'w1',
      arrived: '18.09, 09:40',
      aiModelScore: 0.941,
      aiDetectedPlate: '10 814 BSM',
      aiBodyType: 'truck',
      fraudVerdict: 'OK',
      unloaded: true,
      cameraSnapshot: 'web_assets/camera/annotated_5.jpg',
      plateCrop: 'web_assets/camera/plate_5.jpg'
    },
    {
      id: 'r3',
      plate: '10 107 ABC',
      field: 'f3',
      crop: 'Пшеница',
      bunkerWeight: 15400,
      entry: '18.09, 09:40',
      exit: '18.09, 10:25',
      fieldDwellMin: 45,
      transitTimeMin: 58,
      transitAnomaly: true,
      tare: 12800,
      gross: 26950,
      net: 14150,
      discrepancyKg: -1250,
      discrepancyPct: -8.12,
      warehouse: 'w1',
      arrived: '18.09, 11:23',
      aiModelScore: 0.975,
      aiDetectedPlate: '10 107 ABC',
      aiBodyType: 'truck',
      fraudVerdict: 'FRAUD_ALERT',
      unloaded: false,
      cameraSnapshot: 'web_assets/camera/annotated_18.jpg',
      plateCrop: 'web_assets/camera/plate_18.jpg'
    }
  ],
  sales: [
    { date: '16.09.2026', crop: 'Пшеница 3 класс', weight: 84000, price: 95000, buyer: 'ТОО «Астық-Трейд»', warehouse: 'w1' },
    { date: '17.09.2026', crop: 'Ячмень пивоваренный', weight: 45000, price: 82000, buyer: 'АО «Баян Агро»', warehouse: 'w1' }
  ],
  expenses: [
    { date: '16.09.2026', category: 'ГСМ', amount: 480000, note: 'Дизельное топливо Евро-5 (2 400 л)' },
    { date: '17.09.2026', category: 'Оплата труда', amount: 320000, note: 'Смена механизаторов и водителей' },
    { date: '18.09.2026', category: 'Ремонт техники', amount: 145000, note: 'Замена гидравлического шланга комбайна CLAAS' }
  ]
};

const STORAGE_KEY = 'agroflow-kostanay-v3';
let db = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');

// Принудительная миграция: если данных нет или координаты старые (Астана lat ~51)
if (!db || !db.vehicles || !db.vehicles[0] || db.vehicles[0].lat < 52 || db.vehicles[0].lng > 70) {
  console.log('[AgroFlow] Инициализация реальных полей Костанайской области...');
  db = structuredClone(seed);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
}

const save = () => localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
const q = s => document.querySelector(s);
const pageContent = q('#pageContent');

const pageInfo = {
  dashboard: ['ТОО «КОСТАНАЙ-АГРО» · КОСТАНАЙСКАЯ ОБЛАСТЬ', 'Панель управления и метрики'],
  map: ['МОНИТОРИНГ ПОЛЕЙ И ТЕХНИКИ · КОСТАНАЙ', 'Интерактивная GPS-Карта полей (Live)'],
  weighing: ['ВЕСОВАЯ ЭЛЕВАТОРА · AI ДЕТЕКЦИЯ', 'Весовой контроль & Anti-Fraud'],
  bunker: ['УЧЕТ В ПОЛЕ · БУНКЕР КОМБАЙНА', 'Бункерные ведомости и перегрузка'],
  trips: ['ЛОГИСТИКА И БЕЗОПАСНОСТЬ', 'Журнал рейсов и контроль пути'],
  storage: ['УЧЁТ ХРАНЕНИЯ · ЭЛЕВАТОРЫ', 'Элеваторы и склады Костанайской обл.'],
  fields: ['АНАЛИТИКА УРОЖАЙНОСТИ', 'Поля и урожайность (ц/га)'],
  finance: ['ЭКОНОМИКА ХОЗЯЙСТВА', 'Финансы, маржа и себестоимость'],
  reports: ['ЭКСПОРТ ДАННЫХ', 'Отчёты и выгрузка в Excel']
};

let current = 'dashboard';
let leafletMap = null;
let currentMapMode = 'satellite';
let baseTileLayers = {};
let mapVehicleMarkers = {};
let gpsInterval = null;

function getVehicle(p) { return db.vehicles.find(x => x.plate === p); }
function field(id) { return db.fields.find(x => x.id === id); }
function wh(id) { return db.warehouses.find(x => x.id === id); }

function fieldNet(id) {
  return db.trips.filter(r => r.field === id && r.unloaded).reduce((s, r) => s + r.net, 0);
}

function stock(id) {
  let inW = db.trips.filter(r => r.warehouse === id && r.unloaded).reduce((s, r) => s + r.net, 0);
  let sold = db.sales.reduce((s, x) => s + (x.warehouse === id ? x.weight : 0), 0);
  return Math.max(0, inW - sold);
}

function totalStock() { return db.warehouses.reduce((s, w) => s + stock(w.id), 0); }
function totalHarvest() { return db.trips.filter(r => r.unloaded).reduce((s, r) => s + r.net, 0); }

function toast(t) {
  const x = q('#toast');
  x.innerHTML = `<span>✓</span> ${t}`;
  x.classList.add('show');
  setTimeout(() => x.classList.remove('show'), 3000);
}

function statusBadge(r) {
  if (r.fraudVerdict === 'FRAUD_ALERT') return '<span class="status fraud">⚠ Недостача зерна (-8.1%)</span>';
  if (r.unloaded) return '<span class="status done">✓ Принято на элеватор</span>';
  if (r.arrived) return '<span class="status progress">⚖ На весах</span>';
  if (r.transitAnomaly) return '<span class="status alert">⏱ Аномальная задержка</span>';
  if (r.exit) return '<span class="status progress">🚚 В пути</span>';
  return '<span class="status progress">🚜 Загрузка на поле</span>';
}

function nav(page) {
  current = page;
  document.querySelectorAll('.nav-item').forEach(x => x.classList.toggle('active', x.dataset.page === page));
  q('#pageKicker').textContent = pageInfo[page][0];
  q('#pageTitle').textContent = pageInfo[page][1];
  if (gpsInterval) { clearInterval(gpsInterval); gpsInterval = null; }
  render();
}

/* =========================================================================
   1. ОБЗОР (DASHBOARD)
   ========================================================================= */
function dashboard() {
  const t = totalHarvest();
  const st = totalStock();
  const rev = db.sales.reduce((s, x) => s + (x.weight / 1000) * x.price, 0);
  const exp = db.expenses.reduce((s, x) => s + x.amount, 0);
  const alertsCount = db.trips.filter(r => r.fraudVerdict === 'FRAUD_ALERT' || r.transitAnomaly).length;

  return `
    <div class="dashboard-grid">
      <div class="stat-card">
        <div class="stat-top">Убрано и принято <span class="stat-icon ic-green">🌾</span></div>
        <div class="stat-value">${fmt(t / 1000)} <small>тонн</small></div>
        <div class="trend">↗ +28.5 т за сегодня</div>
      </div>
      <div class="stat-card">
        <div class="stat-top">На складах и элеваторах <span class="stat-icon ic-yellow">▣</span></div>
        <div class="stat-value">${fmt(st / 1000)} <small>тонн</small></div>
        <div class="trend">Вместимость: 45 500 т (${fmt(st / 45500 * 100)}%)</div>
      </div>
      <div class="stat-card">
        <div class="stat-top">Средняя урожайность <span class="stat-icon ic-blue">⌁</span></div>
        <div class="stat-value">${yieldAvg()} <small>ц/га</small></div>
        <div class="trend">План совхоза перевыполнен на 108%</div>
      </div>
      <div class="stat-card">
        <div class="stat-top">Статус Anti-Fraud <span class="stat-icon ${alertsCount ? 'ic-orange' : 'ic-green'}">🛡</span></div>
        <div class="stat-value" style="color:${alertsCount ? 'var(--red)' : 'var(--green)'}">${alertsCount ? alertsCount + ' инцидент' : 'Штатно'}</div>
        <div class="trend ${alertsCount ? 'down' : ''}">${alertsCount ? 'Заблокирован рейс: подозрение на слив' : 'Все веса сходятся в пределах 1.5%'}</div>
      </div>
    </div>

    <div class="two-col">
      <article class="card">
        <div class="card-heading">
          <div>
            <div class="card-title">Накопленный урожай и темпы уборки</div>
            <p class="subtle">Фактический вывоз зерна на элеватор, тонн в сутки</p>
          </div>
          <div class="legend"><span><i></i>Факт</span><span><i class="lime"></i>План</span></div>
        </div>
        ${chart([38, 74, 118, 165, 212, 260, Math.round(t / 1000)], ['12.09', '13.09', '14.09', '15.09', '16.09', '17.09', '18.09'])}
      </article>

      <article class="card">
        <div class="card-heading">
          <div>
            <div class="card-title">Поля уборочной кампании</div>
            <p class="subtle">Прогресс по геозонам совхоза</p>
          </div>
          <button class="link-button" onclick="nav('fields')">Все поля →</button>
        </div>
        ${db.fields.map(f => `
          <div class="field-row">
            <div class="field-mark">⌁</div>
            <div>
              <strong>${f.name}</strong>
              <small>${f.crop} · ${f.area} га</small>
            </div>
            <div class="field-value">
              ${Math.round(f.harvested / f.area * 100)}%
              <span>${f.harvested} из ${f.area} га</span>
            </div>
          </div>
        `).join('')}
      </article>
    </div>

    <div class="two-col" style="margin-top:18px;">
      <article class="card">
        <div class="card-heading">
          <div>
            <div class="card-title">Оперативный мониторинг техники (Live GPS)</div>
            <p class="subtle">Текущая позиция зерновозов и комбайнов в полях</p>
          </div>
          <button class="link-button" onclick="nav('map')">Открыть карту →</button>
        </div>
        <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:12px;">
          ${db.vehicles.slice(0, 3).map(v => `
            <div class="vehicle-track-card" onclick="nav('map')">
              <div class="vehicle-header">
                <span class="vehicle-plate">${v.plate}</span>
                <span class="vehicle-speed">${v.speed} км/ч</span>
              </div>
              <div class="vehicle-meta">
                <span>${v.icon} ${v.type}</span>
                <span class="vehicle-geofence">● ${v.status}</span>
              </div>
            </div>
          `).join('')}
        </div>
      </article>

      <article class="card">
        <div class="card-heading">
          <div>
            <div class="card-title">Камера весовой элеватора (AI-контроль)</div>
            <p class="subtle">Последнее распознавание нейросетью YOLO11</p>
          </div>
          <button class="link-button" onclick="nav('weighing')">Открыть весовую →</button>
        </div>
        <div style="display:flex; gap:14px; align-items:center;">
          <img src="web_assets/camera/annotated_10.jpg" style="width:130px; height:75px; object-fit:cover; border-radius:8px; border:1px solid #c8d6cc;">
          <div>
            <div style="font-weight:800; font-size:13px; font-family:'JetBrains Mono'">KZ 523 ARA</div>
            <div style="font-size:11px; color:var(--green); font-weight:700">✓ Госномер распознан (96.4%)</div>
            <div style="font-size:11px; color:var(--muted)">Кузов: Трактор с прицепом (97.5%)</div>
          </div>
        </div>
      </article>
    </div>
  `;
}

function yieldAvg() {
  let a = db.fields.reduce((s, f) => s + f.area, 0);
  let w = db.fields.reduce((s, f) => s + fieldNet(f.id), 0);
  return a ? fmt(w / 10 / a) : '24.2';
}

/* =========================================================================
   2. GPS КАРТА И ГЕОЗОНЫ (MAP & GEOFENCING)
   ========================================================================= */
function mapPage() {
  return `
    <div class="section-head">
      <div>
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;">
          <span style="background:#eaf6ee; color:#185338; font-size:11px; font-weight:800; padding:3px 8px; border-radius:6px; border:1px solid #c2e2cc; display:inline-flex; align-items:center; gap:4px;">
            <span>📍</span> КОСТАНАЙСКАЯ ОБЛАСТЬ · ПОЛЯ С. ЗАРЕЧНОЕ / П. ТОБЫЛ
          </span>
          <span style="font-size:11px; color:#5c7667; font-family:'JetBrains Mono'; font-weight:700;">53.195° N, 63.740° E · Спутник Esri World Imagery</span>
        </div>
        <h2>Интерактивная GPS-Карта полей и техники</h2>
        <p class="subtle">Спутниковый мониторинг пшеничных полей Костанайской области, геозон, времени заезда/выезда и зерновозов в реальном времени</p>
      </div>
      <div style="display:flex; gap:10px;">
        <button class="button" onclick="toggleMapLayer()">🛰 Спутник / 🗺 Схема</button>
        <button class="button primary" onclick="simulateGpsStep()">▶ Симуляция движения ТС</button>
      </div>
    </div>

    <div class="map-layout">
      <div class="map-container">
        <div id="leafletMap"></div>
      </div>
      <div class="map-telemetry-panel">
        <div class="card-title">Бортовая телеметрия ТС (10 регион)</div>
        <p class="subtle">Кликните на машину на карте или в списке</p>
        <div id="vehicleTelemetryList" style="display:flex; flex-direction:column; gap:10px;">
          ${db.vehicles.map((v, i) => `
            <div class="vehicle-track-card ${i === 0 ? 'active' : ''}" onclick="focusVehicle('${v.plate}')">
              <div class="vehicle-header">
                <span class="vehicle-plate">${v.plate}</span>
                <span class="vehicle-speed">${v.speed} км/ч</span>
              </div>
              <div class="vehicle-meta">
                <span>${v.icon} ${v.type}</span>
                <small>Водитель: ${v.driver}</small>
                <span class="vehicle-geofence">● ${v.status}</span>
                <small style="color:#6e8578; margin-top:3px;">Время на поле: ${v.fieldTime} мин</small>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;
}

function initLeafletMap() {
  const mapEl = q('#leafletMap');
  if (!mapEl) return;

  if (leafletMap) {
    leafletMap.remove();
    leafletMap = null;
  }

  // Центральная точка уборочных полей Костанайского района (с. Заречное / п. Тобыл)
  leafletMap = L.map('leafletMap').setView([53.195, 63.740], 12);

  // Спутниковый снимок высокого разрешения Esri (реальные поля, лесополосы, дороги)
  baseTileLayers.satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 18,
    attribution: 'Tiles &copy; Esri &mdash; Спутник · Костанайская область, Казахстан'
  });

  // Схематический слой OpenStreetMap
  baseTileLayers.osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap contributors · Костанай'
  });

  // По умолчанию включаем детальный спутниковый снимок полей
  if (currentMapMode === 'satellite') {
    baseTileLayers.satellite.addTo(leafletMap);
  } else {
    baseTileLayers.osm.addTo(leafletMap);
  }

  // Отрисовка геозон полей с полигонами
  db.fields.forEach(f => {
    const polygon = L.polygon(f.coords, {
      color: f.color,
      fillColor: f.color,
      fillOpacity: 0.38,
      weight: 2.5,
      dashArray: '6, 6'
    }).addTo(leafletMap);

    polygon.bindPopup(`
      <div style="font-family:Manrope,sans-serif; min-width:190px;">
        <div style="font-size:10px; color:#888; text-transform:uppercase; font-weight:700;">Геозона Костанайского района</div>
        <strong style="font-size:14px; color:#123e2a;">${f.name}</strong><br>
        <div style="margin:6px 0; padding:6px; background:#f4f7f5; border-radius:6px; font-size:11px; line-height:1.5;">
          <div>Культура: <b>${f.crop}</b></div>
          <div>Площадь: <b>${f.area} га</b></div>
          <div>Прогноз урожайности: <b>${f.expected} ц/га</b></div>
        </div>
        <div style="font-size:11px; color:#28704b; font-weight:800;">
          Убрано: ${f.harvested} га (${Math.round(f.harvested/f.area*100)}%)
        </div>
      </div>
    `);
  });

  // Отрисовка элеваторов и зерноскладов совхоза
  db.warehouses.forEach(w => {
    const isMain = w.id === 'w1';
    const elevatorIcon = L.divIcon({
      html: `
        <div style="background:${isMain ? '#123925' : '#1d4835'}; color:#9fe838; font-size:11px; border-radius:7px; padding:4px 8px; border:2px solid ${isMain ? '#9fe838' : '#69b422'}; font-weight:800; box-shadow:0 4px 14px rgba(0,0,0,0.4); white-space:nowrap; display:flex; align-items:center; gap:5px;">
          <span>${isMain ? '🏢' : '▣'}</span>
          <span>${w.name}</span>
        </div>
      `,
      className: 'custom-map-icon',
      iconSize: [210, 30]
    });
    L.marker([w.lat, w.lng], { icon: elevatorIcon })
      .addTo(leafletMap)
      .bindPopup(`
        <div style="font-family:Manrope,sans-serif; min-width:200px;">
          <strong style="font-size:13px; color:#123e2a;">${w.name}</strong><br>
          <span style="font-size:11px; color:#555;">Координаты: <b>${w.lat.toFixed(3)}°N, ${w.lng.toFixed(3)}°E</b></span><br>
          <span style="font-size:11px; color:#555;">Вместимость: <b>${fmt(w.capacity)} тонн</b></span><br>
          <span style="font-size:11px; color:#28704b; font-weight:700;">Остаток: ${fmt(stock(w.id)/1000)} т</span>
          ${isMain ? '<hr style="margin:6px 0; border:0; border-top:1px solid #eee;"><span style="font-size:10px; color:#d97706; font-weight:800;">● Весовая платформа & AI Камера (YOLO11)</span>' : ''}
        </div>
      `);
  });

  // Отрисовка комбайнов в полях
  db.combines.forEach(c => {
    const f = field(c.field);
    let pos = [53.188, 63.746];
    if (f && f.coords && f.coords.length) {
      const avgLat = f.coords.reduce((s, p) => s + p[0], 0) / f.coords.length;
      const avgLng = f.coords.reduce((s, p) => s + p[1], 0) / f.coords.length;
      pos = [avgLat + 0.002, avgLng + 0.003];
    }
    const cIcon = L.divIcon({
      html: `<div style="background:#f1c40f; color:#000; border-radius:50%; width:34px; height:34px; display:grid; place-items:center; font-size:18px; border:2px solid #fff; box-shadow:0 3px 10px rgba(0,0,0,0.3); cursor:pointer;" title="${c.name}">${c.icon}</div>`,
      className: '',
      iconSize: [34, 34]
    });
    L.marker(pos, { icon: cIcon }).addTo(leafletMap).bindPopup(`
      <div style="font-family:Manrope,sans-serif; min-width:190px;">
        <strong style="font-size:13px;">${c.name}</strong><br>
        <span style="font-size:11px; color:#555;">Механизатор: <b>${c.operator}</b></span><br>
        <span style="font-size:11px; color:#555;">Поле: <b>${f ? f.name : 'Поле'}</b></span><br>
        <div style="margin-top:6px; font-size:12px; color:#28704b; font-weight:700;">
          Бункер: ${fmt(c.bunkerCurrent)} из ${fmt(c.bunkerCap)} кг (${Math.round(c.bunkerCurrent/c.bunkerCap*100)}%)
        </div>
        <span style="font-size:11px; color:#666;">Влажность зерна: <b>${c.moisture}%</b></span>
      </div>
    `);
  });

  // Отрисовка машин с госномерами 10 региона
  mapVehicleMarkers = {};
  db.vehicles.forEach(v => {
    const vIcon = L.divIcon({
      html: `
        <div class="map-vehicle-pin" style="background:#1b4d36; color:#fff; padding:3px 8px; border-radius:6px; font-weight:800; font-size:11px; border:1.5px solid #9fe838; display:flex; align-items:center; gap:5px; box-shadow:0 3px 10px rgba(0,0,0,0.3); cursor:pointer;">
          <span>${v.icon}</span> <span>${v.plate}</span>
        </div>
      `,
      className: '',
      iconSize: [125, 30]
    });
    const marker = L.marker([v.lat, v.lng], { icon: vIcon }).addTo(leafletMap);
    marker.bindPopup(`
      <div style="font-family:Manrope,sans-serif; min-width:210px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-family:'JetBrains Mono'; font-weight:800; font-size:14px; color:#123e2a;">${v.plate}</span>
          <span style="font-size:10px; background:#e4f3e8; color:#1b5e20; font-weight:800; padding:1px 6px; border-radius:4px;">10 KZ</span>
        </div>
        <div style="font-size:11px; color:#555; margin-top:2px;">${v.type}</div>
        <div style="font-size:11px; color:#555;">Водитель: <b>${v.driver}</b></div>
        <hr style="border:0; border-top:1px solid #eee; margin:8px 0;">
        <div style="font-size:12px; color:#1a5b3e; font-weight:700;">Скорость: ${v.speed} км/ч</div>
        <div style="font-size:11px; color:#444;">Геозона / Статус: <b>${v.status}</b></div>
        <div style="font-size:11px; color:#666;">Координаты: <b>${v.lat.toFixed(4)}°N, ${v.lng.toFixed(4)}°E</b></div>
      </div>
    `);
    mapVehicleMarkers[v.plate] = marker;
  });

  // Запуск симуляции движения каждые 2.5 секунды
  gpsInterval = setInterval(() => {
    simulateGpsStep(false);
  }, 2500);
}

function simulateGpsStep(withToast = true) {
  db.vehicles.forEach(v => {
    // Небольшое смещение координат для имитации движения по дорогам и полям Костанайского района
    const dLat = (Math.random() - 0.48) * 0.0016;
    const dLng = (Math.random() - 0.46) * 0.0020;
    v.lat = Math.max(53.150, Math.min(53.240, v.lat + dLat));
    v.lng = Math.max(63.680, Math.min(63.830, v.lng + dLng));
    v.speed = Math.max(12, Math.min(55, v.speed + Math.floor((Math.random() - 0.5) * 6)));
    v.fieldTime += 1;

    if (mapVehicleMarkers[v.plate]) {
      mapVehicleMarkers[v.plate].setLatLng([v.lat, v.lng]);
    }
  });

  if (current === 'map') {
    const list = q('#vehicleTelemetryList');
    if (list) {
      list.innerHTML = db.vehicles.map(v => `
        <div class="vehicle-track-card" onclick="focusVehicle('${v.plate}')">
          <div class="vehicle-header">
            <span class="vehicle-plate">${v.plate}</span>
            <span class="vehicle-speed">${v.speed} км/ч</span>
          </div>
          <div class="vehicle-meta">
            <span>${v.icon} ${v.type}</span>
            <small>Водитель: ${v.driver}</small>
            <span class="vehicle-geofence">● ${v.status}</span>
            <small style="color:#6e8578; margin-top:3px;">Время на поле: ${v.fieldTime} мин</small>
          </div>
        </div>
      `).join('');
    }
  }

  if (withToast) toast('GPS-трекинг: координаты и телеметрия обновлены');
}

function focusVehicle(plate) {
  const v = getVehicle(plate);
  if (v && leafletMap && mapVehicleMarkers[plate]) {
    leafletMap.flyTo([v.lat, v.lng], 15, { duration: 1.2 });
    mapVehicleMarkers[plate].openPopup();
  }
}

function toggleMapLayer() {
  if (!leafletMap || !baseTileLayers.satellite || !baseTileLayers.osm) return;
  if (currentMapMode === 'satellite') {
    leafletMap.removeLayer(baseTileLayers.satellite);
    baseTileLayers.osm.addTo(leafletMap);
    currentMapMode = 'osm';
    toast('Переключено на схематическую карту (OpenStreetMap)');
  } else {
    leafletMap.removeLayer(baseTileLayers.osm);
    baseTileLayers.satellite.addTo(leafletMap);
    currentMapMode = 'satellite';
    toast('Переключено на спутниковый снимок полей (Esri World Imagery)');
  }
}

/* =========================================================================
   3. ВЕСОВАЯ И AI-КАМЕРА (WEIGHBRIDGE & ANTI-FRAUD)
   ========================================================================= */
function weighingPage() {
  const alertTrip = db.trips.find(r => r.fraudVerdict === 'FRAUD_ALERT') || db.trips[0];

  return `
    <div class="section-head">
      <div>
        <h2>Весовая платформа & Распознавание через AI (YOLO11)</h2>
        <p class="subtle">Сквозной контроль: распознавание номера и кузова + сверка с бункерным талоном комбайна</p>
      </div>
      <button class="button primary" onclick="runWeighbridgeAiScan()">📸 Тестовый заезд машины (AI Скан)</button>
    </div>

    <div class="ai-weigh-grid">
      <!-- Видеокамера распознавания -->
      <div class="camera-feed-card">
        <div class="camera-header">
          <span class="camera-live-badge"><span class="pulse-dot" style="background:#ff4757"></span> LIVE · КАМЕРА №1 (ВЪЕЗД НА ВЕСЫ)</span>
          <span style="font-size:11px; color:#8ea79a; font-family:'JetBrains Mono'">FPS: 25.0 · 1280x720 · YOLO11n</span>
        </div>
        <div class="camera-body">
          <img src="${alertTrip.cameraSnapshot || 'web_assets/camera/annotated_10.jpg'}" class="camera-img-view" id="cameraLiveView">
          
          <div class="ai-overlay-box">
            <strong>AI ОБЪЕКТ ДЕТЕКТИРОВАН</strong>
            <div>Класс: <b style="color:#00d7ff">${alertTrip.aiBodyType === 'truck' ? 'Тягач / Грузовик' : 'Прицеп'} (${fmt(alertTrip.aiModelScore*100)}%)</b></div>
            <div>Госномер: <b style="color:#ffd700; font-family:'JetBrains Mono'">${alertTrip.plate}</b></div>
            <div>Снимок: Автоматическая фиксация заезда</div>
          </div>

          <div class="camera-plate-crop-inset">
            <img src="${alertTrip.plateCrop || 'web_assets/camera/plate_10.jpg'}" alt="Кроп номера">
            <span>ГОСНОМЕР: ${alertTrip.plate}</span>
          </div>
        </div>
        <div class="camera-controls">
          <select id="cameraSwitch" onchange="switchCamera(this.value)">
            <option value="1">Камера 1: Въезд на весы (Элеватор №1)</option>
            <option value="2">Камера 2: Выезд с весов (Контроль тары)</option>
            <option value="3">Камера 3: КПП выезда с Поля №1</option>
          </select>
          <button class="button" onclick="runWeighbridgeAiScan()">Сделать скан</button>
          <span style="margin-left:auto; font-size:11px; color:#a1b8ac;">Модель: <b>truck_plate_yolo11n.pt</b> (mAP 94.1%)</span>
        </div>
      </div>

      <!-- Весовой терминал и Anti-Fraud вердикт -->
      <div class="antifraud-scale-card">
        <div class="scale-hero">
          <div class="label">ВЕСОВОЙ ДАТЧИК ПЛАТФОРМЫ · БРУТТО</div>
          <div class="big-kg" id="scaleLiveGross">${fmt(alertTrip.gross)} <small>кг</small></div>
          <div class="scale-breakdown">
            <div>
              <small>Паспортная тара машины</small>
              <strong>${fmt(alertTrip.tare)} кг</strong>
            </div>
            <div>
              <small>Фактический вес зерна (НЕТТО)</small>
              <strong style="color:var(--lime)">${fmt(alertTrip.net)} кг</strong>
            </div>
          </div>
        </div>

        <!-- Вердикт Anti-Fraud системы -->
        <div class="antifraud-verdict ${alertTrip.fraudVerdict === 'FRAUD_ALERT' ? 'alert' : 'ok'}">
          <div class="verdict-header">
            <span class="verdict-icon">${alertTrip.fraudVerdict === 'FRAUD_ALERT' ? '🚨' : '✅'}</span>
            <span>${alertTrip.fraudVerdict === 'FRAUD_ALERT' ? 'ТРЕВОГА: НЕСООТВЕТСТВИЕ ВЕСА (ANTI-FRAUD)' : 'ВЕС ПОДТВЕРЖДЕН: ДОПУСК НА ВЫГРУЗКУ'}</span>
          </div>
          <div class="verdict-details">
            <div>Бункерный талон комбайна: <b>${fmt(alertTrip.bunkerWeight)} кг</b></div>
            <div>Фактически на весах элеватора: <b>${fmt(alertTrip.net)} кг</b></div>
            <div>Расхождение: <b style="color:${alertTrip.fraudVerdict === 'FRAUD_ALERT' ? 'var(--red)' : 'var(--green)'}">${alertTrip.discrepancyKg > 0 ? '+' : ''}${fmt(alertTrip.discrepancyKg)} кг (${alertTrip.discrepancyPct}%)</b></div>
            <div style="margin-top:8px; font-weight:700; color:${alertTrip.fraudVerdict === 'FRAUD_ALERT' ? 'var(--red)' : 'var(--green)'}">
              ${alertTrip.fraudVerdict === 'FRAUD_ALERT' ? '⚠ Внимание! Недостача превышает 1.5% (отсыпка зерна в пути). Шлагбаум заблокирован!' : '✓ Расхождение в пределах нормы (до 1.5%). Шлагбаум открыт!'}
            </div>
          </div>
        </div>

        <div class="card" style="padding:16px;">
          <div class="card-title" style="font-size:13px;">Действия оператора весовой</div>
          <div style="display:flex; gap:10px; margin-top:12px;">
            <button class="button primary" style="flex:1" onclick="acceptTripWeight('${alertTrip.id}')">Принять рейс</button>
            <button class="button" style="color:var(--red); border-color:#f1b2ae;" onclick="flagFraud('${alertTrip.id}')">Акт хищения</button>
          </div>
        </div>
      </div>
    </div>
  `;
}

function switchCamera(camId) {
  const img = q('#cameraLiveView');
  if (!img) return;
  if (camId === '1') img.src = 'web_assets/camera/annotated_10.jpg';
  else if (camId === '2') img.src = 'web_assets/camera/annotated_5.jpg';
  else img.src = 'web_assets/camera/annotated_18.jpg';
  toast(`Переключено на Камеру №${camId}`);
}

function runWeighbridgeAiScan() {
  toast('YOLO11: Анализ кадра... Номер KZ 814 BSM (97.8%) распознан. Вес зафиксирован.');
  setTimeout(() => {
    nav('weighing');
  }, 400);
}

function acceptTripWeight(tripId) {
  const r = db.trips.find(x => x.id === tripId);
  if (r) {
    r.unloaded = true;
    r.fraudVerdict = 'OK';
    save();
    toast(`Рейс ${r.plate} принят: ${fmt(r.net / 1000)} т поступило на ${wh(r.warehouse).name}`);
    render();
  }
}

function flagFraud(tripId) {
  const r = db.trips.find(x => x.id === tripId);
  if (r) {
    r.fraudVerdict = 'FRAUD_ALERT';
    save();
    toast('Составлен акт расхождения веса. Уведомление отправлено в Службу Безопасности');
    render();
  }
}

/* =========================================================================
   4. БУНКЕРНЫЕ ВЕДОМОСТИ КОМБАЙНОВ (COMBINE GRAIN UNLOAD)
   ========================================================================= */
function bunkerPage() {
  return `
    <div class="section-head">
      <div>
        <h2>Бункерные ведомости комбайнеров (Учёт в поле)</h2>
        <p class="subtle">Фиксация перегрузки зерна из комбайна в грузовик с цифровой подписью механизатора</p>
      </div>
      <button class="button primary" onclick="openNewBunkerTicketModal()">+ Новая выгрузка комбайна</button>
    </div>

    <div class="bunker-grid">
      ${db.combines.map(c => `
        <div class="bunker-card">
          <div class="bunker-header">
            <span class="combine-tag">${c.name}</span>
            <span style="font-size:11px; color:var(--muted)">Поле: <b>${field(c.field)?.name.replace('Поле №','№') || '№1'}</b></span>
          </div>
          <div>
            <small style="color:var(--muted); font-size:11px;">Текущий бункер комбайна</small>
            <div class="bunker-weight">${fmt(c.bunkerCurrent)} <small style="font-size:14px; color:var(--muted)">кг</small></div>
            <div class="progressbar" style="margin-top:8px;"><i style="width:${Math.round(c.bunkerCurrent/c.bunkerCap*100)}%"></i></div>
            <div style="font-size:11px; color:var(--muted); display:flex; justify-content:space-between; margin-top:4px;">
              <span>Заполнено: ${Math.round(c.bunkerCurrent/c.bunkerCap*100)}%</span>
              <span>Влажность: <b>${c.moisture}%</b></span>
            </div>
          </div>
          <div style="font-size:11px; border-top:1px solid var(--line); padding-top:10px;">
            Оператор: <b>${c.operator}</b>
          </div>
        </div>
      `).join('')}
    </div>

    <div class="card table-card">
      <div style="padding:16px 20px; border-bottom:1px solid var(--line); font-weight:800; font-size:13px;">
        Электронный реестр бункерных талонов
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>ТАЛОН ID</th>
            <th>КОМБАЙН</th>
            <th>МАШИНА (ПРИЕМЩИК)</th>
            <th>ПОЛЕ</th>
            <th>ВЫГРУЖЕННЫЙ ВЕС</th>
            <th>ВРЕМЯ</th>
            <th>ПОДПИСЬ МЕХАНИЗАТОРА</th>
            <th>СТАТУС НА ВЕСОВОЙ</th>
          </tr>
        </thead>
        <tbody>
          ${db.bunkerTickets.map(b => `
            <tr>
              <td><code>${b.id}</code></td>
              <td><b>${db.combines.find(c => c.id === b.combineId)?.name || b.combineId}</b></td>
              <td><span class="plate-badge">${b.plate}</span></td>
              <td>${field(b.fieldId)?.name || b.fieldId}</td>
              <td style="font-family:'JetBrains Mono'; font-weight:800">${fmt(b.weight)} кг</td>
              <td>${b.time}</td>
              <td><span class="signature-stamp">${b.signature}</span></td>
              <td>${b.fraudAlert ? '<span class="status alert">Расхождение на весах!</span>' : '<span class="status done">Сверено на элеваторе</span>'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

function openNewBunkerTicketModal() {
  modal(`
    <h2>Оформить перегрузку из комбайна</h2>
    <form class="modal-form" id="bunkerForm">
      <label>Комбайн
        <select name="combineId">
          ${db.combines.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
        </select>
      </label>
      <label>Зерновоз / Трактор
        <select name="plate">
          ${db.vehicles.map(v => `<option value="${v.plate}">${v.plate} (${v.type})</option>`).join('')}
        </select>
      </label>
      <label>Поле
        <select name="fieldId">
          ${db.fields.map(f => `<option value="${f.id}">${f.name}</option>`).join('')}
        </select>
      </label>
      <label>Вес зерна из бункера, кг
        <input name="weight" type="number" value="12500" required>
      </label>
      <label class="wide">Факсимиле / Электронная подпись комбайнера
        <input name="signature" value="П. Виктор (механизатор)" required>
      </label>
      <div class="modal-actions wide">
        <button type="button" class="button" onclick="closeModal()">Отмена</button>
        <button class="button primary">Подписать и передать в систему</button>
      </div>
    </form>
  `);

  q('#bunkerForm').onsubmit = e => {
    e.preventDefault();
    const o = Object.fromEntries(new FormData(e.target));
    db.bunkerTickets.unshift({
      id: 'bt-' + (db.bunkerTickets.length + 1),
      combineId: o.combineId,
      plate: o.plate,
      fieldId: o.fieldId,
      crop: 'Пшеница',
      weight: +o.weight,
      time: '18.09, 11:45',
      signature: o.signature,
      verified: true
    });
    save();
    closeModal();
    toast('Бункерный талон создан и передан на весовую элеватора');
    render();
  };
}

/* =========================================================================
   5. РЕЙСЫ И ЛОГИСТИКА (TRIPS & TRANSIT MONITORING)
   ========================================================================= */
function tripsPage() {
  return `
    <div class="section-head">
      <div>
        <h2>Журнал рейсов и мониторинг пути</h2>
        <p class="subtle">Сквозная цепочка: Заезд на поле → Бункер комбайна → Время в пути → Весовая → Склад</p>
      </div>
      <button class="button primary" onclick="nav('weighing')">+ Зафиксировать въезд</button>
    </div>

    <div class="filters">
      <input id="tripSearch" placeholder="Поиск по номеру, культуре или полю" oninput="filterTrips()">
      <select id="tripFilter" onchange="filterTrips()">
        <option value="">Все статусы</option>
        <option value="fraud">⚠ Инциденты (Anti-Fraud)</option>
        <option value="done">Приняты на складе</option>
      </select>
    </div>

    <div id="tripResults">
      <div class="card table-card">
        <table class="data-table">
          <thead>
            <tr>
              <th>МАШИНА</th>
              <th>ПОЛЕ / КУЛЬТУРА</th>
              <th>БУНКЕР В ПОЛЕ</th>
              <th>ВЕС НЕТТО</th>
              <th>РАСХОЖДЕНИЕ</th>
              <th>ВРЕМЯ В ПУТИ</th>
              <th>AI-КАМЕРА</th>
              <th>СТАТУС</th>
              <th>ДЕЙСТВИЯ</th>
            </tr>
          </thead>
          <tbody>
            ${db.trips.map(r => `
              <tr>
                <td>
                  <span class="plate-badge">${r.plate}</span><br>
                  <small style="color:var(--muted)">${getVehicle(r.plate)?.type || 'Грузовик'}</small>
                </td>
                <td>
                  ${field(r.field)?.name || 'Поле'}<br>
                  <span class="type-tag">${r.crop}</span>
                </td>
                <td style="font-family:'JetBrains Mono'">${fmt(r.bunkerWeight)} кг</td>
                <td style="font-family:'JetBrains Mono'; font-weight:800">${fmt(r.net)} кг</td>
                <td style="color:${r.discrepancyPct < -1.5 ? 'var(--red)' : 'var(--green)'}; font-weight:800">
                  ${r.discrepancyKg > 0 ? '+' : ''}${fmt(r.discrepancyKg)} кг (${r.discrepancyPct}%)
                </td>
                <td>
                  ${r.transitTimeMin} мин
                  ${r.transitAnomaly ? '<br><small style="color:var(--red); font-weight:800">⚠ Задержка (+25м)</small>' : ''}
                </td>
                <td>
                  <button class="action-btn" onclick="showAiCard('${r.id}')">📷 AI Карточка</button>
                </td>
                <td>${statusBadge(r)}</td>
                <td>
                  <button class="action-btn" onclick="tripAction('${r.id}')">
                    ${r.unloaded ? 'Архив' : r.fraudVerdict === 'FRAUD_ALERT' ? 'Проверить' : 'Разгрузить'}
                  </button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function showAiCard(tripId) {
  const r = db.trips.find(x => x.id === tripId) || db.trips[0];
  modal(`
    <h2>Карточка фиксации ТС нейросетью YOLO11</h2>
    <div style="margin-bottom:14px;">
      <img src="${r.cameraSnapshot || 'web_assets/camera/annotated_10.jpg'}" style="width:100%; border-radius:10px; border:1px solid #d2ddd6;">
    </div>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:12px;">
      <div>
        <small style="color:var(--muted)">Распознанный номер:</small>
        <div style="font-family:'JetBrains Mono'; font-weight:800; font-size:15px;">${r.plate}</div>
        <div style="color:var(--green); font-weight:700;">Уверенность OCR: ${fmt(r.aiModelScore * 100)}%</div>
      </div>
      <div>
        <small style="color:var(--muted)">Тип кузова:</small>
        <div style="font-weight:800; font-size:14px;">${r.aiBodyType === 'truck' ? 'Тягач / Зерновоз' : 'Прицеп'}</div>
        <div style="color:var(--muted);">Время фиксации: ${r.arrived || r.exit}</div>
      </div>
    </div>
    <div class="modal-actions">
      <button class="button primary" onclick="closeModal()">Закрыть</button>
    </div>
  `);
}

function tripAction(id) {
  const r = db.trips.find(x => x.id === id);
  if (r.unloaded) {
    toast(`Рейс ${r.plate} уже выгружен на ${wh(r.warehouse).name}`);
    return;
  }
  if (r.fraudVerdict === 'FRAUD_ALERT') {
    modal(`
      <h2 style="color:var(--red)">🚨 Инцидент безопасности: Недостача ${fmt(Math.abs(r.discrepancyKg))} кг</h2>
      <p style="font-size:13px; line-height:1.6;">
        Бункерный талон комбайна зафиксировал <b>${fmt(r.bunkerWeight)} кг</b>, однако на весах элеватора взвешено лишь <b>${fmt(r.net)} кг</b>.
        Время в пути составило <b>58 минут</b> (на 25 минут дольше нормы).
      </p>
      <div class="modal-actions">
        <button class="button" onclick="closeModal()">Закрыть</button>
        <button class="button primary" style="background:var(--red)" onclick="closeModal(); toast('Служебное расследование инициировано');">Сформировать протокол СБ</button>
      </div>
    `);
    return;
  }
  r.unloaded = true;
  save();
  toast(`Успешно выгружено: ${fmt(r.net / 1000)} т принято на ${wh(r.warehouse).name}`);
  render();
}

function filterTrips() {
  const s = q('#tripSearch').value.toLowerCase();
  const f = q('#tripFilter').value;
  const rows = db.trips.filter(r => {
    const match = (r.plate + r.crop + (field(r.field)?.name || '')).toLowerCase().includes(s);
    if (f === 'fraud') return match && r.fraudVerdict === 'FRAUD_ALERT';
    if (f === 'done') return match && r.unloaded;
    return match;
  });
  // Simple re-render of table
  nav('trips');
}

/* =========================================================================
   6. СКЛАДЫ И ЭЛЕВАТОР (STORAGE)
   ========================================================================= */
function storagePage() {
  return `
    <div class="section-head">
      <div>
        <h2>Остатки на хранении (Элеваторы совхоза)</h2>
        <p class="subtle">Баланс пополняется только после официальной фиксации на весовой элеватора</p>
      </div>
      <button class="button primary" onclick="openSaleModal()">+ Отгрузка / Продажа зерна</button>
    </div>

    <div class="inventory">
      ${db.warehouses.map(w => {
        const s = stock(w.id);
        const p = Math.min(100, (s / w.capacity) * 100);
        return `
          <article class="card warehouse-card">
            <div class="warehouse-banner">
              <h3>${w.name}</h3>
              <span>Активное зернохранилище</span>
            </div>
            <div class="warehouse-info">
              <div class="warehouse-n">${fmt(s / 1000)} <small>т</small></div>
              <p>из максимальной вместимости ${fmt(w.capacity / 1000)} т</p>
              <div class="progressbar"><i style="width:${p}%"></i></div>
              <p>Заполнено на ${fmt(p)}%</p>
            </div>
          </article>
        `;
      }).join('')}
    </div>

    <div class="two-col" style="margin-top:20px;">
      <article class="card">
        <div class="card-title">Состав запасов по культурам</div>
        <p class="subtle">Подтвержденные складские приходы урожая 2026</p>
        ${['Пшеница твердая', 'Ячмень пивоваренный', 'Пшеница озимая'].map(c => {
          const n = db.trips.filter(r => r.unloaded && r.crop.includes(c.split(' ')[0])).reduce((s, r) => s + r.net, 0);
          return `
            <div class="field-row">
              <div class="field-mark">🌾</div>
              <strong>${c}</strong>
              <div class="field-value">${fmt(n / 1000)} т</div>
            </div>
          `;
        }).join('')}
      </article>

      <article class="card">
        <div class="card-title">Регламент приемки зерна</div>
        <p class="subtle">Правило перекрестного контроля (Anti-Fraud)</p>
        <div class="mini-kpi">
          <span>Сверка весовой платформы</span>
          <strong>Допуск: до ±1.5%</strong>
          <span>Бункер комбайна − Весы элеватора</span>
        </div>
        <p class="form-note">
          При расхождении выше 1.5% система автоматически блокирует открытие шлагбаума и уведомляет диспетчерский пункт.
        </p>
      </article>
    </div>
  `;
}

function openSaleModal() {
  modal(`
    <h2>Оформить продажу зерна</h2>
    <form class="modal-form" id="saleForm">
      <label>Элеватор / Склад
        <select name="warehouse">
          ${db.warehouses.map(w => `<option value="${w.id}">${w.name} (${fmt(stock(w.id) / 1000)} т доступно)</option>`).join('')}
        </select>
      </label>
      <label>Культура
        <select name="crop">
          <option>Пшеница 3 класс</option>
          <option>Ячмень пивоваренный</option>
        </select>
      </label>
      <label>Количество, тонн
        <input name="weightTons" type="number" value="25" min="1" required>
      </label>
      <label>Цена за тонну, ₸
        <input name="price" type="number" value="95000" min="1000" required>
      </label>
      <label class="wide">Покупатель / Контрагент
        <input name="buyer" value="ТОО «Астық-Экспорт»" required>
      </label>
      <div class="modal-actions wide">
        <button type="button" class="button" onclick="closeModal()">Отмена</button>
        <button class="button primary">Подтвердить отгрузку</button>
      </div>
    </form>
  `);

  q('#saleForm').onsubmit = e => {
    e.preventDefault();
    const o = Object.fromEntries(new FormData(e.target));
    const kg = +o.weightTons * 1000;
    if (kg > stock(o.warehouse)) {
      toast('Недостаточно зерна на складе!');
      return;
    }
    db.sales.unshift({
      date: today,
      crop: o.crop,
      weight: kg,
      price: +o.price,
      buyer: o.buyer,
      warehouse: o.warehouse
    });
    save();
    closeModal();
    toast(`Отгрузка ${o.weightTons} т оформлена. Выручка: ${money(+o.weightTons * +o.price)}`);
    render();
  };
}

/* =========================================================================
   7. ПОЛЯ И УРОЖАЙНОСТЬ (FIELDS)
   ========================================================================= */
function fieldsPage() {
  return `
    <div class="section-head">
      <div>
        <h2>Поля, культуры и фактическая урожайность</h2>
        <p class="subtle">Урожайность = Подтвержденный вес нетто ÷ Площадь поля × 10</p>
      </div>
      <button class="button" onclick="exportData('fields')">↓ Экспорт в Excel</button>
    </div>

    <div class="field-cards">
      ${db.fields.map(f => {
        const net = fieldNet(f.id);
        const y = f.area ? (net / 10 / f.area) : 0;
        return `
          <article class="card field-card">
            <div class="field-visual" style="background:${f.color}"></div>
            <h3>${f.name}</h3>
            <p>${f.crop} · Площадь ${f.area} га</p>
            <div class="progressbar"><i style="width:${Math.round(f.harvested / f.area * 100)}%"></i></div>
            <p>Убрано ${f.harvested} из ${f.area} га (${Math.round(f.harvested / f.area * 100)}%)</p>
            <div class="field-stats">
              <div>СОБРАНО<strong>${fmt(net / 1000)} т</strong></div>
              <div>УРОЖАЙНОСТЬ<strong>${fmt(y)} ц/га</strong></div>
            </div>
          </article>
        `;
      }).join('')}
    </div>

    <div class="card" style="margin-top:20px;">
      <div class="card-heading">
        <div>
          <div class="card-title">Сравнение урожайности по полям (ц/га)</div>
          <p class="subtle">Фактические данные после взвешивания зерновозов</p>
        </div>
      </div>
      ${chart([24.5, 19.8, 22.0], ['Поле №1', 'Поле №2', 'Поле №3'], '#1a5b3e')}
    </div>
  `;
}

/* =========================================================================
   8. ЭКОНОМИКА И МАРЖА (FINANCE)
   ========================================================================= */
function financePage() {
  const rev = db.sales.reduce((s, x) => s + (x.weight / 1000) * x.price, 0);
  const exp = db.expenses.reduce((s, x) => s + x.amount, 0);
  const margin = rev - exp;

  return `
    <div class="section-head">
      <div>
        <h2>Экономика уборочной кампании и маржа</h2>
        <p class="subtle">Доходы от реализации зерна минус прямые затраты на ГСМ, ремонт и оплату труда</p>
      </div>
      <div style="display:flex; gap:10px;">
        <button class="button" onclick="openExpenseModal()">+ Добавить расход</button>
        <button class="button primary" onclick="openSaleModal()">+ Продажа зерна</button>
      </div>
    </div>

    <div class="dashboard-grid">
      <div class="stat-card">
        <div class="stat-top">Выручка от продаж <span class="stat-icon ic-green">₸</span></div>
        <div class="stat-value" style="color:var(--green)">${money(rev)}</div>
        <div class="trend">${db.sales.length} сделки</div>
      </div>
      <div class="stat-card">
        <div class="stat-top">Прямые расходы <span class="stat-icon ic-orange">⛽</span></div>
        <div class="stat-value">${money(exp)}</div>
        <div class="trend">ГСМ, зарплата, ремонт</div>
      </div>
      <div class="stat-card">
        <div class="stat-top">Чистая маржа <span class="stat-icon ic-yellow">📈</span></div>
        <div class="stat-value" style="color:${margin >= 0 ? 'var(--green)' : 'var(--red)'}">${money(margin)}</div>
        <div class="trend">${margin >= 0 ? 'Прибыль сезона' : 'Убыток'}</div>
      </div>
      <div class="stat-card">
        <div class="stat-top">Себестоимость тонны <span class="stat-icon ic-blue">⚖</span></div>
        <div class="stat-value">34 200 <small>₸/т</small></div>
        <div class="trend">При цене реализации 95 000 ₸/т</div>
      </div>
    </div>

    <div class="two-col" style="margin-top:20px;">
      <article class="card">
        <div class="card-heading">
          <div>
            <div class="card-title">Финансовый баланс уборочной</div>
            <p class="subtle">Динамика накопленной выручки, ₸</p>
          </div>
        </div>
        ${chart([0, 2400000, 4800000, 7200000, 9500000, 11670000, rev], ['12.09', '13.09', '14.09', '15.09', '16.09', '17.09', '18.09'], '#216747')}
      </article>

      <article class="card">
        <div class="card-title">Структура прямых затрат</div>
        <p class="subtle">Статьи расходов за текущий период</p>
        ${db.expenses.map(x => `
          <div class="field-row">
            <div class="field-mark">₸</div>
            <div>
              <strong>${x.category}</strong>
              <small>${x.note} · ${x.date}</small>
            </div>
            <div class="field-value" style="color:var(--red)">-${money(x.amount)}</div>
          </div>
        `).join('')}
      </article>
    </div>
  `;
}

function openExpenseModal() {
  modal(`
    <h2>Внести операционный расход</h2>
    <form class="modal-form" id="expForm">
      <label>Категория
        <select name="category">
          <option>ГСМ (Дизельное топливо)</option>
          <option>Оплата труда механизаторов</option>
          <option>Ремонт и запчасти комбайнов</option>
          <option>Ирригация и обработка</option>
        </select>
      </label>
      <label>Сумма, ₸
        <input name="amount" type="number" value="150000" min="1000" required>
      </label>
      <label class="wide">Примечание / Назначение платежа
        <input name="note" value="Закупка фильтров и масла для трактора" required>
      </label>
      <div class="modal-actions wide">
        <button type="button" class="button" onclick="closeModal()">Отмена</button>
        <button class="button primary">Записать расход</button>
      </div>
    </form>
  `);

  q('#expForm').onsubmit = e => {
    e.preventDefault();
    const o = Object.fromEntries(new FormData(e.target));
    db.expenses.unshift({
      date: today,
      category: o.category,
      amount: +o.amount,
      note: o.note
    });
    save();
    closeModal();
    toast('Расход зафиксирован в экономическом балансе');
    render();
  };
}

/* =========================================================================
   9. ОТЧЁТЫ И ЭКСПОРТ В EXCEL (REPORTS)
   ========================================================================= */
function reportsPage() {
  return `
    <div class="section-head">
      <div>
        <h2>Отчёты и экспорт в Excel (CSV с поддержкой кириллицы)</h2>
        <p class="subtle">Выгрузка всех первичных документов для бухгалтерии, 1С и руководства</p>
      </div>
    </div>

    <div class="reports-grid">
      <article class="card report-card">
        <div class="report-icon">⚖</div>
        <div>
          <h3>Реестр весового контроля и детекций камер</h3>
          <p>Все взвешивания, распознанные номера, веса нетто/брутто и вердикты Anti-Fraud</p>
          <button class="action-btn" onclick="exportData('trips')">Скачать Excel ↓</button>
        </div>
      </article>

      <article class="card report-card">
        <div class="report-icon">🌾</div>
        <div>
          <h3>Бункерные ведомости комбайнеров</h3>
          <p>Первичные электронные расписки выгрузки зерна в поле с подписями</p>
          <button class="action-btn" onclick="exportData('bunker')">Скачать Excel ↓</button>
        </div>
      </article>

      <article class="card report-card">
        <div class="report-icon">⌁</div>
        <div>
          <h3>Сводная урожайность по полям</h3>
          <p>Площади полей, валовый сбор, средняя урожайность в центнерах с гектара</p>
          <button class="action-btn" onclick="exportData('fields')">Скачать Excel ↓</button>
        </div>
      </article>

      <article class="card report-card">
        <div class="report-icon">₸</div>
        <div>
          <h3>Экономика и финансовый баланс</h3>
          <p>Выручка от продаж, прямые затраты на ГСМ и фонд оплаты труда</p>
          <button class="action-btn" onclick="exportData('finance')">Скачать Excel ↓</button>
        </div>
      </article>
    </div>

    <div class="card" style="margin-top:20px;">
      <div class="card-title">Справка по архитектуре решения для жюри Хакатона</div>
      <div class="tour-step" style="margin-top:12px;">
        <strong>Сквозная цепочка AgroFlow (Anti-Fraud AgTech):</strong>
        <ol>
          <li><b>В поле:</b> Комбайн насыпает зерно в прицеп трактора и формирует электронный бункерный талон с точным весом.</li>
          <li><b>В пути:</b> GPS-трекинг фиксирует пересечение границы геозоны поля и контролирует время движения к элеватору (исключая скрытые остановки).</li>
          <li><b>На весовой:</b> Нейросеть YOLO11 автоматически распознает госномер и тип кузова автомобиля, извлекая вес пустой тары из базы.</li>
          <li><b>Защита от хищений:</b> Система сверяет бункерный вес с фактическим весом нетто. При расхождении > 1.5% шлагбаум блокируется, а инцидент отправляется в службу безопасности.</li>
        </ol>
      </div>
    </div>
  `;
}

function exportData(kind) {
  let rows = [];
  let filename = 'agroflow-report';

  if (kind === 'trips') {
    filename = 'agroflow-reestr-vzveshivaniya';
    rows = [
      ['Госномер', 'Тип кузова', 'Поле', 'Культура', 'Бункерный вес (кг)', 'Тара (кг)', 'Брутто (кг)', 'Нетто (кг)', 'Расхождение (кг)', 'Расхождение (%)', 'Время в пути (мин)', 'Вердикт Anti-Fraud'],
      ...db.trips.map(r => [
        r.plate,
        r.aiBodyType,
        field(r.field)?.name || r.field,
        r.crop,
        r.bunkerWeight,
        r.tare,
        r.gross,
        r.net,
        r.discrepancyKg,
        r.discrepancyPct + '%',
        r.transitTimeMin,
        r.fraudVerdict
      ])
    ];
  } else if (kind === 'bunker') {
    filename = 'agroflow-bunkernye-talony';
    rows = [
      ['Талон ID', 'Комбайн', 'Машина-приемщик', 'Поле', 'Культура', 'Вес выгрузки (кг)', 'Время', 'Подпись'],
      ...db.bunkerTickets.map(b => [
        b.id,
        db.combines.find(c => c.id === b.combineId)?.name || b.combineId,
        b.plate,
        field(b.fieldId)?.name || b.fieldId,
        b.crop,
        b.weight,
        b.time,
        b.signature
      ])
    ];
  } else if (kind === 'fields') {
    filename = 'agroflow-urozhaynost-poley';
    rows = [
      ['Поле', 'Культура', 'Площадь (га)', 'Убрано (га)', 'Собрано (кг)', 'Урожайность (ц/га)'],
      ...db.fields.map(f => [
        f.name,
        f.crop,
        f.area,
        f.harvested,
        fieldNet(f.id),
        (fieldNet(f.id) / 10 / f.area).toFixed(1)
      ])
    ];
  } else {
    filename = 'agroflow-finansovy-otchet';
    rows = [
      ['Тип', 'Дата', 'Контрагент / Категория', 'Сумма (₸)', 'Примечание'],
      ...db.sales.map(s => ['Доход', s.date, s.buyer, (s.weight / 1000) * s.price, s.crop]),
      ...db.expenses.map(e => ['Расход', e.date, e.category, -e.amount, e.note])
    ];
  }

  const csvContent = '\uFEFF' + rows.map(r => r.map(v => '"' + String(v).replaceAll('"', '""') + '"').join(';')).join('\r\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csvContent], { type: 'text/csv;charset=utf-8;' }));
  a.download = filename + '.csv';
  a.click();
  URL.revokeObjectURL(a.href);
  toast('Отчет успешно экспортирован в Excel (CSV)');
}

/* =========================================================================
   РОУТИНГ И РЕНДЕРИНГ
   ========================================================================= */
function render() {
  const pages = {
    dashboard: dashboard,
    map: mapPage,
    weighing: weighingPage,
    bunker: bunkerPage,
    trips: tripsPage,
    storage: storagePage,
    fields: fieldsPage,
    finance: financePage,
    reports: reportsPage
  };

  pageContent.innerHTML = pages[current]();
  q('#tripBadge').textContent = db.trips.filter(r => !r.unloaded).length;

  if (current === 'map') {
    setTimeout(initLeafletMap, 50);
  } else {
    setTimeout(drawCharts, 50);
  }
}

function chart(values, labels, accent = '#1a5b3e') {
  return `
    <div class="chart-wrap">
      <canvas data-values="${values.join(',')}" data-labels="${labels.join(',')}" data-color="${accent}"></canvas>
    </div>
  `;
}

function drawCharts() {
  document.querySelectorAll('canvas[data-values]').forEach(c => {
    const r = c.getBoundingClientRect();
    const d = window.devicePixelRatio || 1;
    c.width = r.width * d;
    c.height = r.height * d;
    const x = c.getContext('2d');
    x.scale(d, d);

    const w = r.width;
    const h = r.height;
    const vs = c.dataset.values.split(',').map(Number);
    const ls = c.dataset.labels.split(',');
    const max = Math.max(...vs) * 1.25;
    const pad = { l: 40, r: 15, t: 15, b: 30 };

    x.font = '11px Manrope';
    x.strokeStyle = '#e3e8de';
    x.fillStyle = '#84958c';

    // Horizontal grid
    for (let i = 0; i < 4; i++) {
      const y = pad.t + (h - pad.t - pad.b) * (i / 3);
      x.beginPath();
      x.moveTo(pad.l, y);
      x.lineTo(w - pad.r, y);
      x.stroke();
      x.fillText(Math.round(max * (1 - i / 3)), 4, y + 4);
    }

    const pts = vs.map((v, i) => [
      pad.l + (w - pad.l - pad.r) * (i / (vs.length - 1)),
      pad.t + (h - pad.t - pad.b) * (1 - v / max)
    ]);

    // Gradient fill
    x.beginPath();
    pts.forEach((p, i) => (i ? x.lineTo(...p) : x.moveTo(...p)));
    x.lineTo(pts.at(-1)[0], h - pad.b);
    x.lineTo(pts[0][0], h - pad.b);
    x.closePath();

    const g = x.createLinearGradient(0, pad.t, 0, h - pad.b);
    g.addColorStop(0, c.dataset.color + '44');
    g.addColorStop(1, c.dataset.color + '02');
    x.fillStyle = g;
    x.fill();

    // Line
    x.beginPath();
    pts.forEach((p, i) => (i ? x.lineTo(...p) : x.moveTo(...p)));
    x.strokeStyle = c.dataset.color;
    x.lineWidth = 3;
    x.stroke();

    // Points
    pts.forEach(p => {
      x.beginPath();
      x.arc(...p, 4, 0, 7);
      x.fillStyle = '#fff';
      x.fill();
      x.strokeStyle = c.dataset.color;
      x.lineWidth = 2.5;
      x.stroke();
    });

    // Labels
    x.fillStyle = '#64756c';
    ls.forEach((s, i) => x.fillText(s, pts[i][0] - 12, h - 8));
  });
}

function modal(html) {
  q('#modalRoot').innerHTML = `
    <div class="modal-backdrop" onclick="if(event.target===this)closeModal()">
      <div class="modal">${html}</div>
    </div>
  `;
}

function closeModal() {
  q('#modalRoot').innerHTML = '';
}

// Демо-сценарий для презентации перед жюри
q('#demoTour').onclick = () => {
  modal(`
    <div class="tour">
      <h2>Сценарий защиты проекта перед жюри (Кейс №2)</h2>
      <div class="tour-step">
        <strong>Суть решения:</strong> Мы расширили базовое распознавание номеров и машин до <b>комплексной AgTech-платформы предотвращения потерь урожая (Anti-Fraud)</b>.
      </div>
      <ol style="font-size:13px; line-height:1.8;">
        <li><b>Вкладка «Весовая & AI-Камера»:</b> Покажите работу обученной модели YOLO11 (mAP 94.1%). При въезде машина фиксируется, определяется госномер и тип кузова.</li>
        <li><b>Вкладка «GPS-Карта & Геозоны»:</b> Покажите движение техники в реальном времени, автоматический замер времени нахождения на поле и контроль времени в пути.</li>
        <li><b>Вкладка «Бункеры комбайнов»:</b> Продемонстрируйте первичный талон с поля с росписью комбайнера.</li>
        <li><b>Anti-Fraud весовой:</b> Покажите обнаружение расхождения веса (-1 250 кг) и блокировку шлагбаума при попытке хищения зерна.</li>
        <li><b>Экспорт в Excel:</b> Скачайте итоговый отчет в 1 клик.</li>
      </ol>
      <div class="modal-actions">
        <button class="button" onclick="closeModal()">Закрыть</button>
        <button class="button primary" onclick="closeModal(); nav('weighing');">Начать с Весовой & AI →</button>
      </div>
    </div>
  `);
};

q('#nav').onclick = e => {
  const b = e.target.closest('[data-page]');
  if (b) nav(b.dataset.page);
};

q('#resetData').onclick = () => {
  if (confirm('Сбросить все демо-данные до начальных?')) {
    db = structuredClone(seed);
    save();
    render();
    toast('Данные возвращены к начальному состоянию');
  }
};

// Экспорт глобальных функций
window.nav = nav;
window.tripAction = tripAction;
window.showAiCard = showAiCard;
window.openSaleModal = openSaleModal;
window.openExpenseModal = openExpenseModal;
window.openNewBunkerTicketModal = openNewBunkerTicketModal;
window.closeModal = closeModal;
window.exportData = exportData;
window.acceptTripWeight = acceptTripWeight;
window.flagFraud = flagFraud;
window.runWeighbridgeAiScan = runWeighbridgeAiScan;
window.switchCamera = switchCamera;
window.focusVehicle = focusVehicle;
window.simulateGpsStep = simulateGpsStep;
window.toggleMapLayer = toggleMapLayer;

render();
