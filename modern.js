/**
 * Agro Info — GPS Fleet Monitor
 * ТОО «Олжа Агро» · Костанайская область
 *
 * РЕАЛЬНЫЕ ОБЪЕКТЫ И МАРШРУТЫ:
 *  - Элеватор «Олжа Астык» (Костанай, ул. Дощанова 157, 172 000 т)
 *  - Зерноток / ХПП «Олжа Садчиковское» (с. Садчиковка, весовая, сушилка)
 *  - ХПП «Олжа Майколь» (с. Майколь, северный кластер)
 *  - ХПП «Олжа Заречное» (п. Заречное / Тобыл, восточный кластер)
 *  - Реальные контуры полей в сельскохозяйственных районах
 *
 * ВОЗМОЖНОСТИ РЕДАКТИРОВАНИЯ:
 *  - Перетаскивание маркеров элеваторов (drag-and-drop)
 *  - Редактирование вершин полей (перетаскивание углов полигона)
 *  - Рисование новых полей (клик по точкам, двойной клик — завершить)
 *  - Установка новых элеваторов в 1 клик
 *  - Сброс к реальным базам Олжа Агро в 1 клик
 *  - Сохранение в localStorage
 */

// ═══════════════════════════════════════════════════════════
// РЕАЛЬНЫЕ ОБЪЕКТЫ ПО УМОЛЧАНИЮ (ОЛЖА АГРО)
// ═══════════════════════════════════════════════════════════
const DEFAULT_WAREHOUSES = [
  {
    id: 'w-astik',
    name: 'Элеватор «Олжа Астық»',
    sub: 'г. Костанай, ул. Дощанова 157 · 172 000 т (авто/жд приёмка)',
    lat: 53.2223,
    lng: 63.6030
  },
  {
    id: 'w-sadchikov',
    name: 'Зерноток «Олжа Садчиковское»',
    sub: 'с. Садчиковка · База, весовая, зерносушилка и МТФ',
    lat: 53.0335,
    lng: 63.4810
  },
  {
    id: 'w-maykol',
    name: 'ХПП «Олжа Майколь»',
    sub: 'с. Майколь · Северный зерноприёмный пункт',
    lat: 53.2820,
    lng: 63.4750
  },
  {
    id: 'w-zarech',
    name: 'ХПП «Олжа Заречное»',
    sub: 'п. Заречное / Тобыл · Восточный кластер',
    lat: 53.2210,
    lng: 63.7150
  }
];

const DEFAULT_FIELDS = [
  {
    id: 'f-sadch1',
    name: 'Садчиковское — Поле №1',
    crop: 'Озимая пшеница',
    color: '#22c55e',
    area: 480,
    harvested: 310,
    expected: 24.5,
    coords: [
      [53.0450, 63.4420],
      [53.0680, 63.4480],
      [53.0640, 63.4980],
      [53.0410, 63.4920]
    ]
  },
  {
    id: 'f-sadch2',
    name: 'Садчиковское — Поле №2',
    crop: 'Яровой ячмень',
    color: '#f59e0b',
    area: 360,
    harvested: 180,
    expected: 21.0,
    coords: [
      [53.0220, 63.4150],
      [53.0420, 63.4210],
      [53.0380, 63.4680],
      [53.0180, 63.4620]
    ]
  },
  {
    id: 'f-sadch3',
    name: 'Садчиковское — Поле №3',
    crop: 'Подсолнечник',
    color: '#eab308',
    area: 520,
    harvested: 80,
    expected: 18.0,
    coords: [
      [52.9980, 63.4550],
      [53.0180, 63.4600],
      [53.0140, 63.5180],
      [52.9940, 63.5120]
    ]
  },
  {
    id: 'f-zarech',
    name: 'Олжа Заречное — Участок №4',
    crop: 'Твёрдая пшеница',
    color: '#3b82f6',
    area: 410,
    harvested: 240,
    expected: 23.0,
    coords: [
      [53.2200, 63.7400],
      [53.2460, 63.7480],
      [53.2420, 63.8100],
      [53.2160, 63.8020]
    ]
  },
  {
    id: 'f-maykol',
    name: 'Олжа Майколь — Участок №5',
    crop: 'Рапс яровой',
    color: '#a78bfa',
    area: 390,
    harvested: 150,
    expected: 19.5,
    coords: [
      [53.2820, 63.4750],
      [53.3100, 63.4850],
      [53.3050, 63.5450],
      [53.2770, 63.5350]
    ]
  }
];

// ═══════════════════════════════════════════════════════════
// МАРШРУТЫ ТЕХНИКИ (Поля и реальные дороги Костанайского района)
// ═══════════════════════════════════════════════════════════
const WAYPOINTS = {
  // КАМАЗ 6520 Зерновоз: автотрасса Садчиковка → Костанайский Элеватор Олжа Астык
  kamaz: [
    [53.0335, 63.4810], // Зерноток Садчиковка
    [53.0450, 63.5010],
    [53.0680, 63.5280], // Трасса вдоль р. Тобол
    [53.0980, 63.5510], // Октябрьское
    [53.1350, 63.5720], // Мичурино
    [53.1720, 63.5850], // Южный въезд в Костанай
    [53.2010, 63.5950], // ул. Абая
    [53.2223, 63.6030], // Элеватор «Олжа Астык»
    [53.2010, 63.5950], // Обратно
    [53.1720, 63.5850],
    [53.1350, 63.5720],
    [53.0980, 63.5510],
    [53.0680, 63.5280],
    [53.0450, 63.5010]
  ],
  // John Deere 8320R: челночный сбор зерна в Садчиковском Поле №1
  deere: [
    [53.0470, 63.4480],
    [53.0660, 63.4520],
    [53.0660, 63.4580],
    [53.0470, 63.4540],
    [53.0470, 63.4600],
    [53.0660, 63.4640],
    [53.0660, 63.4700],
    [53.0470, 63.4660],
    [53.0470, 63.4720],
    [53.0660, 63.4760]
  ],
  // МТЗ-82 Беларус: подвоз зерна от комбайна на Поле №1 к Зернотоку Садчиковка
  belarus: [
    [53.0470, 63.4580], // Разгрузка комбайна на краю поля
    [53.0420, 63.4710], // Полевая грунтовая дорога
    [53.0335, 63.4810], // Зерноток Садчиковка (разгрузка в бункер)
    [53.0420, 63.4710]  // Возврат на поле
  ],
  // Volvo FMX 460: рейс Участок Заречное → Большой мост через Тобол → Элеватор Олжа Астык
  volvo: [
    [53.2240, 63.7650], // Поле Заречное
    [53.2210, 63.7150], // ХПП Заречное
    [53.2180, 63.6700], // Мост через р. Тобол (пр. Тауелсиздик)
    [53.2200, 63.6300], // ул. Дощанова
    [53.2223, 63.6030], // Элеватор «Олжа Астык»
    [53.2200, 63.6300],
    [53.2180, 63.6700],
    [53.2210, 63.7150]
  ],
  // Shacman SX3258: рейс Поле Майколь → трасса → Элеватор Олжа Астык
  shacman: [
    [53.2920, 63.5050], // Поле Майколь
    [53.2820, 63.4750], // ХПП Майколь
    [53.2620, 63.5250], // Трасса на Костанай
    [53.2380, 63.5700], // С-З въезд в город
    [53.2223, 63.6030], // Элеватор «Олжа Астык»
    [53.2380, 63.5700],
    [53.2620, 63.5250],
    [53.2820, 63.4750]
  ]
};

// ═══════════════════════════════════════════════════════════
// ТЕКУЩИЙ ФЛОТ
// ═══════════════════════════════════════════════════════════
const fleetData = [
  { id:'v1', plate:'10 523 ARA', type:'John Deere 8320R', driver:'Ерлан Мухамедиев',
    routeKey:'deere', baseSpeed:18, speed:18, rpm:1850, fuelRate:24.2,
    status:'Уборка (Садчиковское Поле №1)', kind:'tractor', color:'#f59e0b',
    segIdx:0, progress:0, lat:53.0470, lng:63.4480, heading:15 },
  { id:'v2', plate:'10 814 BSM', type:'КАМАЗ 6520 Зерновоз', driver:'Нурлан Сейткали',
    routeKey:'kamaz', baseSpeed:44, speed:44, rpm:2100, fuelRate:32.5,
    status:'Рейс: Садчиковка → Олжа Астык', kind:'truck', color:'#3b82f6',
    segIdx:2, progress:0.4, lat:53.0800, lng:63.5370, heading:35 },
  { id:'v3', plate:'10 296 KDA', type:'МТЗ-82 Беларус', driver:'Данияр Абенов',
    routeKey:'belarus', baseSpeed:22, speed:22, rpm:1650, fuelRate:14.8,
    status:'Подвоз зерна на Зерноток Садчиковка', kind:'tractor', color:'#22c55e',
    segIdx:0, progress:0.5, lat:53.0380, lng:63.4760, heading:145 },
  { id:'v4', plate:'10 107 ABC', type:'Volvo FMX 460', driver:'Алексей Ветров',
    routeKey:'volvo', baseSpeed:48, speed:48, rpm:1950, fuelRate:29.1,
    status:'Рейс: Заречное → Олжа Астык', kind:'truck', color:'#ef4444',
    segIdx:1, progress:0.7, lat:53.2190, lng:63.6850, heading:270 },
  { id:'v5', plate:'10 845 KZX', type:'Shacman SX3258', driver:'Бауыржан Касымов',
    routeKey:'shacman', baseSpeed:42, speed:42, rpm:2050, fuelRate:34.0,
    status:'Рейс: Майколь → Олжа Астык', kind:'truck', color:'#a78bfa',
    segIdx:1, progress:0.3, lat:53.2700, lng:63.5050, heading:135 }
];

// ═══════════════════════════════════════════════════════════
// ГЛОБАЛЬНОЕ СОСТОЯНИЕ
// ═══════════════════════════════════════════════════════════
let leafletMap        = null;
let currentLayerType  = 'satellite';
let baseLayers        = {};
let vehicleMarkers    = {};
let vehicleTrails     = {};
let selectedPlate     = fleetData[0].plate;
let followVehicleLocked = false;
let simRunning        = true;
let simMultiplier     = 1;
let animTimer         = null;
let chartGauge        = null;

// Данные пользователя (поля и элеваторы)
let userFields       = [];   // {id, name, crop, color, coords, area, ...}
let userWarehouses   = [];   // {id, name, sub, lat, lng}
let fieldLayers      = {};   // id → L.polygon
let warehouseLayers  = {};   // id → L.marker
let vertexHandles    = [];   // массив маркеров вершин для интерактивного перетаскивания

// Режим редактирования
let editMode         = false;
let editTool         = null;  // 'field' | 'warehouse' | 'edit_vertices' | null
let drawPoints       = [];
let drawMarkers      = [];
let drawPreview      = null;

const FIELD_COLORS = ['#22c55e', '#f59e0b', '#3b82f6', '#eab308', '#a78bfa', '#ec4899', '#06b6d4'];
const fmt = n => n != null ? new Intl.NumberFormat('ru-RU').format(n) : '—';

// ═══════════════════════════════════════════════════════════
// TOAST
// ═══════════════════════════════════════════════════════════
function toast(msg, dur = 2800) {
  const el = document.getElementById('toastNotify');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('show'), dur);
}

// ═══════════════════════════════════════════════════════════
// LOCALSTORAGE & ПРЕДУСТАНОВКИ
// ═══════════════════════════════════════════════════════════
function loadUserData() {
  try {
    const f = localStorage.getItem('agroflow_fields');
    const w = localStorage.getItem('agroflow_warehouses');
    
    if (f) {
      const parsed = JSON.parse(f);
      userFields = (Array.isArray(parsed) && parsed.length > 0) ? parsed : JSON.parse(JSON.stringify(DEFAULT_FIELDS));
    } else {
      userFields = JSON.parse(JSON.stringify(DEFAULT_FIELDS));
    }

    if (w) {
      const parsed = JSON.parse(w);
      userWarehouses = (Array.isArray(parsed) && parsed.length > 0) ? parsed : JSON.parse(JSON.stringify(DEFAULT_WAREHOUSES));
    } else {
      userWarehouses = JSON.parse(JSON.stringify(DEFAULT_WAREHOUSES));
    }
  } catch(e) {
    userFields     = JSON.parse(JSON.stringify(DEFAULT_FIELDS));
    userWarehouses = JSON.parse(JSON.stringify(DEFAULT_WAREHOUSES));
  }
}

function saveUserData(showToast = true) {
  localStorage.setItem('agroflow_fields',     JSON.stringify(userFields));
  localStorage.setItem('agroflow_warehouses', JSON.stringify(userWarehouses));
  if (showToast) toast('💾 Изменения сохранены');
}

function resetToRealOlzhaAgro() {
  if (!confirm('Восстановить реальные поля и элеваторы Олжа Агро по умолчанию?')) return;
  
  clearVertexHandles();
  Object.keys(fieldLayers).forEach(k => { if (fieldLayers[k]) leafletMap.removeLayer(fieldLayers[k]); });
  Object.keys(warehouseLayers).forEach(k => { if (warehouseLayers[k]) leafletMap.removeLayer(warehouseLayers[k]); });
  fieldLayers = {};
  warehouseLayers = {};

  userFields     = JSON.parse(JSON.stringify(DEFAULT_FIELDS));
  userWarehouses = JSON.parse(JSON.stringify(DEFAULT_WAREHOUSES));
  saveUserData(false);

  userFields.forEach(f => renderField(f));
  userWarehouses.forEach(w => renderWarehouse(w));
  fitAllObjects();
  toast('🌾 Реальные поля и элеваторы Олжа Агро загружены');
}

// ═══════════════════════════════════════════════════════════
// SVG ИКОНКИ ТЕХНИКИ (маленькие, вид сверху, точный масштаб)
// ═══════════════════════════════════════════════════════════
function vehicleSvg(v) {
  const c = v.color;
  if (v.kind === 'tractor') {
    // Маленький трактор ~28px
    return `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28">
      <ellipse cx="14" cy="15" rx="7" ry="8" fill="${c}"/>
      <ellipse cx="14" cy="8"  rx="5.5" ry="5" fill="${c}"/>
      <rect x="11" y="6" width="6" height="4" rx="1.5" fill="rgba(255,255,255,0.85)"/>
      <ellipse cx="7"  cy="19" rx="3"   ry="4"   fill="#1e293b" stroke="${c}" stroke-width="1.2"/>
      <ellipse cx="21" cy="19" rx="3"   ry="4"   fill="#1e293b" stroke="${c}" stroke-width="1.2"/>
      <ellipse cx="7.5"  cy="9"  rx="1.8" ry="2.2" fill="#1e293b" stroke="${c}" stroke-width="1"/>
      <ellipse cx="20.5" cy="9"  rx="1.8" ry="2.2" fill="#1e293b" stroke="${c}" stroke-width="1"/>
      <polygon points="14,1 17,7 11,7" fill="white" opacity="0.9"/>
    </svg>`;
  }
  // Грузовик ~20x34px
  return `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="34" viewBox="0 0 20 34">
    <rect x="2" y="5"  width="16" height="24" rx="2.5" fill="${c}" opacity="0.9"/>
    <rect x="3" y="3"  width="14" height="10" rx="3"   fill="${c}"/>
    <rect x="5" y="4"  width="10" height="7"  rx="2"   fill="rgba(255,255,255,0.82)"/>
    <rect x="0" y="4"  width="3" height="5" rx="1.5" fill="#1e293b" stroke="${c}" stroke-width="0.8"/>
    <rect x="17" y="4" width="3" height="5" rx="1.5" fill="#1e293b" stroke="${c}" stroke-width="0.8"/>
    <rect x="0" y="14" width="3" height="6" rx="1.5" fill="#1e293b" stroke="${c}" stroke-width="0.8"/>
    <rect x="17" y="14" width="3" height="6" rx="1.5" fill="#1e293b" stroke="${c}" stroke-width="0.8"/>
    <rect x="0" y="24" width="3" height="5" rx="1.5" fill="#1e293b" stroke="${c}" stroke-width="0.8"/>
    <rect x="17" y="24" width="3" height="5" rx="1.5" fill="#1e293b" stroke="${c}" stroke-width="0.8"/>
    <polygon points="10,0 13,5 7,5" fill="white" opacity="0.9"/>
  </svg>`;
}

// ═══════════════════════════════════════════════════════════
// MOTION ENGINE (реальная скорость 1:1 с учетом широты)
// ═══════════════════════════════════════════════════════════
const TICK_MS = 50;
const LAT_M   = 111000;

function initMotionEngine() {
  if (animTimer) clearInterval(animTimer);
  animTimer = setInterval(() => {
    if (!simRunning) return;
    fleetData.forEach(v => {
      const wps = WAYPOINTS[v.routeKey];
      if (!wps || wps.length < 2) return;

      const p1  = wps[v.segIdx];
      const ni  = (v.segIdx + 1) % wps.length;
      const p2  = wps[ni];

      // Геодезическое расстояние в метрах с учетом косинуса широты
      const dLat = (p2[0] - p1[0]) * LAT_M;
      const dLng = (p2[1] - p1[1]) * LAT_M * Math.cos(p1[0] * Math.PI / 180);
      const segDistM = Math.sqrt(dLat * dLat + dLng * dLng) || 1;

      // Приращение в метрах за 1 тик таймера
      const mpt = (v.speed / 3.6) * (TICK_MS / 1000) * simMultiplier;
      v.progress += mpt / segDistM;

      if (v.progress >= 1) {
        v.progress = 0;
        v.segIdx = ni;
      }

      const cp1 = wps[v.segIdx];
      const cp2 = wps[(v.segIdx + 1) % wps.length];
      v.lat = cp1[0] + (cp2[0] - cp1[0]) * v.progress;
      v.lng = cp1[1] + (cp2[1] - cp1[1]) * v.progress;

      // Курс направления (азимут)
      const br = Math.atan2((cp2[1] - cp1[1]) * Math.cos(v.lat * Math.PI / 180), cp2[0] - cp1[0]);
      v.heading = Math.round(((br * 180 / Math.PI) + 360) % 360);

      // Легкие реалистичные микроколебания скорости
      v.speed = Math.max(10, Math.min(65, v.baseSpeed + Math.sin(Date.now() / 3000 + v.progress * 4) * 2.2));
      v.rpm   = Math.round(1400 + (v.speed / 65) * 1100 + Math.random() * 30);

      if (vehicleMarkers[v.plate]) {
        vehicleMarkers[v.plate].setLatLng([v.lat, v.lng]);
        const el = vehicleMarkers[v.plate].getElement();
        if (el) {
          const w = el.querySelector('.veh-wrap');
          if (w) w.style.transform = `rotate(${v.heading}deg)`;
        }
      }
      if (vehicleTrails[v.plate]) {
        const path = vehicleTrails[v.plate].getLatLngs();
        path.push([v.lat, v.lng]);
        if (path.length > 35) path.shift();
        vehicleTrails[v.plate].setLatLngs(path);
      }
    });

    if (followVehicleLocked && leafletMap) {
      const av = fleetData.find(x => x.plate === selectedPlate);
      if (av) leafletMap.panTo([av.lat, av.lng], { animate: false });
    }
    updateGaugeChart();
    updateSidebarSpeeds();
  }, TICK_MS);
}

// ═══════════════════════════════════════════════════════════
// LEAFLET MAP INIT
// ═══════════════════════════════════════════════════════════
function initLeafletMap() {
  const container = document.getElementById('modernLeafletMap');
  if (!container) return;
  if (leafletMap) { leafletMap.remove(); leafletMap = null; }

  // Центрируем на сельскохозяйственном поясе Костанайского района
  leafletMap = L.map('modernLeafletMap', { zoomControl: false, doubleClickZoom: false })
    .setView([53.1500, 63.5800], 11);

  L.control.zoom({ position: 'topright' }).addTo(leafletMap);

  baseLayers.satellite = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { maxZoom: 18, attribution: '© Esri Satellite' }
  );
  baseLayers.osm = L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    { maxZoom: 18, attribution: '© OpenStreetMap' }
  );
  (currentLayerType === 'satellite' ? baseLayers.satellite : baseLayers.osm).addTo(leafletMap);

  // Клики карты для рисования
  leafletMap.on('click', onMapClick);
  leafletMap.on('dblclick', onMapDblClick);

  // Маркеры техники
  vehicleMarkers = {};
  vehicleTrails  = {};
  fleetData.forEach(v => {
    const trail = L.polyline([[v.lat, v.lng]], {
      color: v.color, weight: 2.5, opacity: 0.45, dashArray: '5 8'
    }).addTo(leafletMap);
    vehicleTrails[v.plate] = trail;

    const svgStr = vehicleSvg(v);
    const iw = v.kind === 'tractor' ? 36 : 28;
    const ih = v.kind === 'tractor' ? 36 : 48;

    const vIcon = L.divIcon({
      html: `<div style="display:flex;flex-direction:column;align-items:center;cursor:pointer;">
        <div class="veh-wrap" style="transform:rotate(${v.heading}deg);transition:transform .18s linear;filter:drop-shadow(0 2px 5px rgba(0,0,0,0.6));">
          ${svgStr}
        </div>
        <div style="margin-top:1px;background:rgba(13,21,32,0.92);color:#fff;font-size:9.5px;font-weight:800;padding:1px 6px;border-radius:20px;border:1.5px solid ${v.color};font-family:'JetBrains Mono',monospace;white-space:nowrap;backdrop-filter:blur(4px);box-shadow:0 2px 6px rgba(0,0,0,0.4);">${v.plate}</div>
      </div>`,
      className: '',
      iconSize: [iw + 30, ih + 16],
      iconAnchor: [(iw + 30) / 2, ih / 2]
    });

    const marker = L.marker([v.lat, v.lng], { icon: vIcon }).addTo(leafletMap);
    marker.on('click', () => focusVehicle(v.plate));
    marker.bindPopup(`
      <div style="font-family:Manrope,sans-serif;min-width:210px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span style="font-family:'JetBrains Mono';font-weight:800;font-size:13px;">${v.plate}</span>
          <span style="font-size:10px;background:#eff6ff;color:#1d4ed8;font-weight:800;padding:1px 6px;border-radius:4px;">KZ 10</span>
        </div>
        <div style="font-size:11px;color:#64748b;margin-top:2px;">${v.type}</div>
        <div style="font-size:11px;color:#64748b;">Водитель: <b>${v.driver}</b></div>
        <hr style="border:0;border-top:1px solid #e2e8f0;margin:6px 0;">
        <div style="font-size:12px;color:${v.color};font-weight:800;">▶ ${Math.round(v.speed)} км/ч</div>
        <div style="font-size:11px;color:#475569;margin-top:2px;">${v.status}</div>
      </div>`);
    vehicleMarkers[v.plate] = marker;
  });

  // Отрисовка полей и элеваторов
  userFields.forEach(f => renderField(f));
  userWarehouses.forEach(w => renderWarehouse(w));

  // Подгоняем вид карты под все объекты, чтобы охватить все поля и элеватор
  fitAllObjects();

  renderSidebar();
  renderQuickVehicles();
}

// ═══════════════════════════════════════════════════════════
// ФОКУСИРОВКА И НАВИГАЦИЯ ПО КЛАСТЕРАМ
// ═══════════════════════════════════════════════════════════
function fitAllObjects() {
  if (!leafletMap) return;
  const allCoords = [];
  userFields.forEach(f => f.coords.forEach(c => allCoords.push(c)));
  userWarehouses.forEach(w => allCoords.push([w.lat, w.lng]));
  if (allCoords.length > 0) {
    const bounds = L.latLngBounds(allCoords);
    leafletMap.fitBounds(bounds.pad(0.12));
  }
}

function focusCluster(clusterName) {
  if (!leafletMap) return;
  if (clusterName === 'all') {
    fitAllObjects();
    toast('🗺 Все поля и элеваторы Олжа Агро');
  } else if (clusterName === 'sadchikovka') {
    leafletMap.flyTo([53.0360, 63.4680], 13, { duration: 0.8 });
    toast('🌾 Кластер «Олжа Садчиковское» (Поля №1, №2, №3 и Зерноток)');
  } else if (clusterName === 'kostanay') {
    leafletMap.flyTo([53.2223, 63.6030], 14, { duration: 0.8 });
    toast('🏢 Главный Элеватор «Олжа Астык» (Костанай)');
  } else if (clusterName === 'zarechnoye') {
    leafletMap.flyTo([53.2280, 63.7650], 13, { duration: 0.8 });
    toast('🌾 Восточный кластер «Олжа Заречное» (Участок №4 и ХПП)');
  } else if (clusterName === 'maykol') {
    leafletMap.flyTo([53.2920, 63.5050], 13, { duration: 0.8 });
    toast('🌾 Северный кластер «Олжа Майколь» (Участок №5 и ХПП)');
  }
}

// ═══════════════════════════════════════════════════════════
// ОТРИСОВКА ПОЛЕЙ
// ═══════════════════════════════════════════════════════════
function renderField(f) {
  if (fieldLayers[f.id]) {
    leafletMap.removeLayer(fieldLayers[f.id]);
    if (fieldLayers[f.id + '_label']) leafletMap.removeLayer(fieldLayers[f.id + '_label']);
  }

  const poly = L.polygon(f.coords, {
    color: f.color,
    fillColor: f.color,
    fillOpacity: 0.24,
    weight: 2.5
  }).addTo(leafletMap);

  poly.bindPopup(`
    <div style="font-family:Manrope,sans-serif;min-width:190px;">
      <div style="font-size:11px;color:${f.color};font-weight:800;text-transform:uppercase;letter-spacing:.5px;">Поле · Олжа Агро</div>
      <div style="font-size:14px;font-weight:800;color:#1e293b;margin:3px 0;">${f.name}</div>
      <div style="font-size:11.5px;color:#475569;">Культура: <b>${f.crop || '—'}</b></div>
      <div style="font-size:11.5px;color:#475569;">Площадь: ~<b>${f.area || '?'} га</b></div>
      <div style="font-size:11px;color:#64748b;margin-top:3px;">Убрано: <b>${f.harvested || 0} га</b> · Урож-ть: <b>${f.expected || 22} ц/га</b></div>
      <hr style="border:0;border-top:1px solid #e2e8f0;margin:8px 0 6px;">
      <div style="display:flex;gap:5px;flex-wrap:wrap;">
        <button onclick="startEditingFieldVertices('${f.id}')" style="padding:4px 9px;background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;border-radius:6px;font-size:11px;font-weight:700;cursor:pointer;">📐 Изменить контур</button>
        <button onclick="editFieldName('${f.id}')" style="padding:4px 9px;background:#f8fafc;color:#334155;border:1px solid #cbd5e1;border-radius:6px;font-size:11px;font-weight:700;cursor:pointer;">✏ Свойства</button>
        <button onclick="deleteField('${f.id}')" style="padding:4px 9px;background:#fef2f2;color:#dc2626;border:1px solid #fecaca;border-radius:6px;font-size:11px;font-weight:700;cursor:pointer;">🗑 Удалить</button>
      </div>
    </div>`);

  poly.on('click', () => {
    if (editTool === 'edit_vertices') {
      startEditingFieldVertices(f.id);
    }
  });

  fieldLayers[f.id] = poly;

  // Центральная плашка-подпись
  const center = poly.getBounds().getCenter();
  const label = L.marker(center, {
    icon: L.divIcon({
      html: `<div style="background:rgba(13,21,32,0.85);color:${f.color};font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:16px;border:1px solid ${f.color};white-space:nowrap;backdrop-filter:blur(4px);font-family:Manrope,sans-serif;box-shadow:0 2px 6px rgba(0,0,0,0.5);">${f.name}</div>`,
      className: '', iconSize: null
    })
  }).addTo(leafletMap);
  fieldLayers[f.id + '_label'] = label;
}

// ═══════════════════════════════════════════════════════════
// ОТРИСОВКА ЭЛЕВАТОРОВ И ПЕРЕМЕЩЕНИЕ (DRAG-AND-DROP)
// ═══════════════════════════════════════════════════════════
function renderWarehouse(w) {
  if (warehouseLayers[w.id]) leafletMap.removeLayer(warehouseLayers[w.id]);

  const ic = L.divIcon({
    html: `<div style="background:#0d1520;color:#f59e0b;font-size:11px;border-radius:8px;padding:5px 10px;border:2px solid #f59e0b;font-weight:800;box-shadow:0 0 14px rgba(245,158,11,0.35);white-space:nowrap;display:flex;align-items:center;gap:6px;font-family:Manrope,sans-serif;cursor:${editMode?'move':'pointer'};">
      <span style="font-size:14px;">🏢</span> ${w.name}
    </div>`,
    className: '', iconSize: null
  });

  const marker = L.marker([w.lat, w.lng], {
    icon: ic,
    draggable: editMode // В режиме редактирования маркер можно свободно таскать
  }).addTo(leafletMap);

  marker.bindPopup(`
    <div style="font-family:Manrope,sans-serif;min-width:210px;">
      <div style="font-size:13.5px;font-weight:800;color:#1e293b;">${w.name}</div>
      <div style="font-size:11px;color:#64748b;margin-top:2px;">${w.sub || 'Элеватор / ХПП · Олжа Агро'}</div>
      <div style="font-size:10px;color:#94a3b8;font-family:'JetBrains Mono';margin-top:4px;">${w.lat.toFixed(4)}° N, ${w.lng.toFixed(4)}° E</div>
      <hr style="border:0;border-top:1px solid #e2e8f0;margin:8px 0 6px;">
      <div style="display:flex;gap:5px;">
        <button onclick="enableWarehouseDrag('${w.id}')" style="padding:4px 9px;background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;border-radius:6px;font-size:11px;font-weight:700;cursor:pointer;">📍 Переместить</button>
        <button onclick="editWarehouseName('${w.id}')" style="padding:4px 9px;background:#f8fafc;color:#334155;border:1px solid #cbd5e1;border-radius:6px;font-size:11px;font-weight:700;cursor:pointer;">✏ Название</button>
        <button onclick="deleteWarehouse('${w.id}')" style="padding:4px 9px;background:#fef2f2;color:#dc2626;border:1px solid #fecaca;border-radius:6px;font-size:11px;font-weight:700;cursor:pointer;">🗑</button>
      </div>
    </div>`);

  marker.on('dragend', e => {
    const pos = e.target.getLatLng();
    w.lat = Number(pos.lat.toFixed(5));
    w.lng = Number(pos.lng.toFixed(5));
    saveUserData(false);
    toast(`📍 Новые координаты «${w.name}»: ${w.lat}, ${w.lng}`);
  });

  warehouseLayers[w.id] = marker;
}

function enableWarehouseDrag(id) {
  const m = warehouseLayers[id];
  if (m) {
    m.dragging.enable();
    m.closePopup();
    toast('📍 Перетащите маркер элеватора в нужное место на карте', 4000);
  }
}

// ═══════════════════════════════════════════════════════════
// ИНТЕРАКТИВНОЕ РЕДАКТИРОВАНИЕ ВЕРШИН ПОЛЕЙ (CONTOUR EDIT)
// ═══════════════════════════════════════════════════════════
function clearVertexHandles() {
  vertexHandles.forEach(h => { if (leafletMap) leafletMap.removeLayer(h); });
  vertexHandles = [];
}

function startEditingFieldVertices(fieldId) {
  const f = userFields.find(x => x.id === fieldId);
  if (!f) return;

  clearVertexHandles();
  leafletMap.closePopup();

  // Создаем круглые перетаскиваемые ручки на каждой вершине
  f.coords.forEach((coord, idx) => {
    const handleIcon = L.divIcon({
      className: 'poly-vertex-handle',
      iconSize: [14, 14],
      iconAnchor: [7, 7]
    });

    const handle = L.marker(coord, {
      icon: handleIcon,
      draggable: true,
      zIndexOffset: 2000
    }).addTo(leafletMap);

    handle.bindTooltip(`Угол ${idx + 1} · Тяните для изменения границы`, { direction: 'top', offset: [0, -8] });

    // Живое обновление полигона при перетаскивании
    handle.on('drag', e => {
      const pos = e.target.getLatLng();
      f.coords[idx] = [Number(pos.lat.toFixed(5)), Number(pos.lng.toFixed(5))];
      if (fieldLayers[f.id]) {
        fieldLayers[f.id].setLatLngs(f.coords);
      }
      if (fieldLayers[f.id + '_label']) {
        fieldLayers[f.id + '_label'].setLatLng(fieldLayers[f.id].getBounds().getCenter());
      }
    });

    // Сохранение и пересчет площади при завершении перетаскивания
    handle.on('dragend', () => {
      f.area = Math.round(calcAreaHa(f.coords));
      saveUserData(false);
      toast(`📐 Граница поля «${f.name}» обновлена: ~${f.area} га`);
    });

    vertexHandles.push(handle);
  });

  toast(`📐 Редактирование «${f.name}»: тяните маркеры на углах поля`, 5000);
}

function showAllFieldVertexHandles() {
  clearVertexHandles();
  userFields.forEach(f => {
    f.coords.forEach((coord, idx) => {
      const handleIcon = L.divIcon({
        className: 'poly-vertex-handle',
        iconSize: [14, 14],
        iconAnchor: [7, 7]
      });

      const handle = L.marker(coord, {
        icon: handleIcon,
        draggable: true,
        zIndexOffset: 2000
      }).addTo(leafletMap);

      handle.on('drag', e => {
        const pos = e.target.getLatLng();
        f.coords[idx] = [Number(pos.lat.toFixed(5)), Number(pos.lng.toFixed(5))];
        if (fieldLayers[f.id]) fieldLayers[f.id].setLatLngs(f.coords);
        if (fieldLayers[f.id + '_label']) fieldLayers[f.id + '_label'].setLatLng(fieldLayers[f.id].getBounds().getCenter());
      });

      handle.on('dragend', () => {
        f.area = Math.round(calcAreaHa(f.coords));
        saveUserData(false);
        toast(`📐 Контур «${f.name}»: ~${f.area} га`);
      });

      vertexHandles.push(handle);
    });
  });
  toast('📐 Перетаскивайте маркеры на углах полей для изменения границ', 5000);
}

// ═══════════════════════════════════════════════════════════
// РИСОВАНИЕ НОВОГО ПОЛЯ И УСТАНОВКА ЭЛЕВАТОРА
// ═══════════════════════════════════════════════════════════
function onMapClick(e) {
  if (!editMode || !editTool) return;

  const { lat, lng } = e.latlng;

  if (editTool === 'warehouse') {
    const name = prompt('Название элеватора / ХПП Олжа Агро:', 'Элеватор Олжа');
    if (!name) return;
    const sub = prompt('Описание / филиал:', 'Костанайская область · Приёмный пункт');
    const w = {
      id: 'w-' + Date.now(),
      name: name.trim(),
      sub: (sub || '').trim(),
      lat: Number(lat.toFixed(5)),
      lng: Number(lng.toFixed(5))
    };
    userWarehouses.push(w);
    renderWarehouse(w);
    saveUserData();
    toast(`🏢 Элеватор «${w.name}» успешно добавлен`);
    return;
  }

  if (editTool === 'field') {
    drawPoints.push([Number(lat.toFixed(5)), Number(lng.toFixed(5))]);

    const vm = L.circleMarker([lat, lng], {
      radius: 5, color: '#f59e0b', fillColor: '#f59e0b',
      fillOpacity: 1, weight: 2
    }).addTo(leafletMap);
    drawMarkers.push(vm);

    if (drawPreview) leafletMap.removeLayer(drawPreview);
    if (drawPoints.length >= 2) {
      drawPreview = L.polygon(drawPoints, {
        color: '#f59e0b', fillColor: '#f59e0b',
        fillOpacity: 0.18, weight: 2, dashArray: '6 5'
      }).addTo(leafletMap);
    }

    toast(`Точка ${drawPoints.length} добавлена · Двойной клик для завершения`);
  }
}

function onMapDblClick(e) {
  L.DomEvent.stop(e);
  if (!editMode || editTool !== 'field' || drawPoints.length < 3) {
    if (editTool === 'field' && drawPoints.length < 3) {
      toast('⚠ Для поля требуется минимум 3 вершины');
    }
    return;
  }
  finishDrawField();
}

function finishDrawField() {
  if (drawPoints.length < 3) { toast('⚠ Требуется минимум 3 точки'); return; }

  const name = prompt('Название поля:', 'Поле Олжа Агро №' + (userFields.length + 1));
  if (!name) { cancelDraw(); return; }
  const crop = prompt('Сельхозкультура (пшеница, ячмень, рапс):', 'Пшеница');

  const color = FIELD_COLORS[userFields.length % FIELD_COLORS.length];
  const area = Math.round(calcAreaHa(drawPoints));

  const f = {
    id: 'f-' + Date.now(),
    name: name.trim(),
    crop: (crop || '').trim(),
    color, area,
    coords: drawPoints.slice(),
    harvested: 0, expected: 22.0
  };

  userFields.push(f);
  renderField(f);
  saveUserData();
  cancelDraw();
  toast(`✅ Поле «${f.name}» (~${f.area} га) добавлено`);
}

function cancelDraw() {
  drawPoints = [];
  drawMarkers.forEach(m => leafletMap.removeLayer(m));
  drawMarkers = [];
  if (drawPreview) { leafletMap.removeLayer(drawPreview); drawPreview = null; }
  if (leafletMap) leafletMap.getContainer().style.cursor = '';
}

// ═══════════════════════════════════════════════════════════
// РЕЖИМ РЕДАКТИРОВАНИЯ
// ═══════════════════════════════════════════════════════════
function toggleEditMode() {
  editMode = !editMode;
  editTool = null;
  cancelDraw();
  clearVertexHandles();

  const panel = document.getElementById('editPanel');
  const btn   = document.getElementById('btnEditMode');
  if (panel) panel.style.display = editMode ? 'flex' : 'none';
  if (btn)   btn.classList.toggle('active', editMode);

  // Обновляем драггабл для элеваторов
  userWarehouses.forEach(w => renderWarehouse(w));
  userFields.forEach(f => renderField(f));

  if (editMode) {
    toast('✏ Режим редактирования включён: перемещайте объекты или рисуйте новые', 4000);
  } else {
    toast('Режим редактирования выключён');
  }
}

function setEditTool(tool) {
  editTool = tool;
  cancelDraw();
  clearVertexHandles();

  document.querySelectorAll('.edit-tool-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.tool === tool));

  if (tool === 'field') {
    leafletMap.getContainer().style.cursor = 'crosshair';
    toast('🌾 Кликайте вершины контура по спутниковой карте. Двойной клик — завершить.', 5000);
  } else if (tool === 'warehouse') {
    leafletMap.getContainer().style.cursor = 'cell';
    toast('🏢 Кликните на карте, чтобы установить элеватор / ХПП', 4000);
  } else if (tool === 'edit_vertices') {
    leafletMap.getContainer().style.cursor = 'default';
    showAllFieldVertexHandles();
  }
}

function deleteField(id) {
  if (!confirm('Удалить это поле?')) return;
  if (fieldLayers[id]) { leafletMap.removeLayer(fieldLayers[id]); delete fieldLayers[id]; }
  if (fieldLayers[id + '_label']) { leafletMap.removeLayer(fieldLayers[id + '_label']); delete fieldLayers[id + '_label']; }
  userFields = userFields.filter(f => f.id !== id);
  clearVertexHandles();
  saveUserData();
  leafletMap.closePopup();
  toast('🗑 Поле удалено');
}

function deleteWarehouse(id) {
  if (!confirm('Удалить этот элеватор?')) return;
  if (warehouseLayers[id]) { leafletMap.removeLayer(warehouseLayers[id]); delete warehouseLayers[id]; }
  userWarehouses = userWarehouses.filter(w => w.id !== id);
  saveUserData();
  leafletMap.closePopup();
  toast('🗑 Элеватор удалён');
}

function editFieldName(id) {
  const f = userFields.find(x => x.id === id);
  if (!f) return;
  const newName = prompt('Название поля:', f.name);
  if (!newName) return;
  const newCrop = prompt('Культура:', f.crop);
  f.name = newName.trim();
  f.crop = (newCrop || '').trim();
  renderField(f);
  saveUserData();
  leafletMap.closePopup();
  toast(`✏ Данные поля «${f.name}» обновлены`);
}

function editWarehouseName(id) {
  const w = userWarehouses.find(x => x.id === id);
  if (!w) return;
  const newName = prompt('Название элеватора:', w.name);
  if (!newName) return;
  const newSub = prompt('Описание / адрес:', w.sub || '');
  w.name = newName.trim();
  w.sub  = (newSub || '').trim();
  renderWarehouse(w);
  saveUserData();
  leafletMap.closePopup();
  toast(`✏ Элеватор обновлен`);
}

function clearAllData() {
  if (!confirm('Удалить ВСЕ поля и элеваторы?')) return;
  clearVertexHandles();
  userFields.forEach(f => {
    if (fieldLayers[f.id])          leafletMap.removeLayer(fieldLayers[f.id]);
    if (fieldLayers[f.id + '_label']) leafletMap.removeLayer(fieldLayers[f.id + '_label']);
  });
  userWarehouses.forEach(w => { if (warehouseLayers[w.id]) leafletMap.removeLayer(warehouseLayers[w.id]); });
  userFields = []; userWarehouses = [];
  fieldLayers = {}; warehouseLayers = {};
  localStorage.removeItem('agroflow_fields');
  localStorage.removeItem('agroflow_warehouses');
  toast('🗑 Все объекты очищены');
}

// Примерная площадь в гектарах (формула Гаусса с учетом широты)
function calcAreaHa(pts) {
  let area = 0;
  const n = pts.length;
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    area += pts[i][1] * pts[j][0];
    area -= pts[j][1] * pts[i][0];
  }
  // Перевод в гектары: 1° lat ≈ 111 000 м, 1° lng ≈ 67 000 м на 53° с.ш.
  return Math.abs(area) / 2 * 111000 * 67000 / 10000;
}

// ═══════════════════════════════════════════════════════════
// ТЕЛЕМЕТРИЯ САЙДБАР
// ═══════════════════════════════════════════════════════════
function renderSidebar() {
  const c = document.getElementById('telemetryListContainer');
  if (!c) return;
  c.innerHTML = fleetData.map(v => `
    <div class="live-vehicle-item ${v.plate === selectedPlate ? 'selected' : ''}" onclick="focusVehicle('${v.plate}')">
      <div class="veh-color-bar" style="background:${v.color}"></div>
      <div class="live-vehicle-inner">
        <div class="live-vehicle-top">
          <span class="live-plate-badge">${v.plate}</span>
          <span class="live-speed-badge" id="spd-${v.id}">${Math.round(v.speed)} км/ч</span>
        </div>
        <div class="live-vehicle-sub">
          <span style="color:#e2e8f0;">${v.type}</span>
          <small style="color:#94a3b8;">${v.driver}</small>
          <span class="live-geozone-tag" style="border-color:${v.color}33;color:${v.color};background:${v.color}15;">● ${v.status}</span>
        </div>
      </div>
    </div>`).join('');
}

function updateSidebarSpeeds() {
  fleetData.forEach(v => {
    const el = document.getElementById(`spd-${v.id}`);
    if (el) el.textContent = Math.round(v.speed) + ' км/ч';
  });
  renderQuickVehicles();
}

function renderQuickVehicles() {
  const c = document.getElementById('mapQuickVehicles');
  if (!c) return;
  c.innerHTML = fleetData.map(v => `
    <div class="map-quick-vehicle ${v.plate === selectedPlate ? 'active' : ''}" onclick="focusVehicle('${v.plate}')"
      style="${v.plate === selectedPlate ? `border-color:${v.color};` : ''}">
      <div class="qv-dot" style="background:${v.color}"></div>
      <span class="v-plate">${v.plate}</span>
      <span style="font-size:11px;color:${v.color};font-family:'JetBrains Mono'">${Math.round(v.speed)} км/ч</span>
    </div>`).join('');
}

function focusVehicle(plate) {
  selectedPlate = plate;
  const v = fleetData.find(x => x.plate === plate);
  if (v && leafletMap && vehicleMarkers[plate]) {
    leafletMap.flyTo([v.lat, v.lng], 14, { duration: 0.8 });
    vehicleMarkers[plate].openPopup();
    toast(`${v.plate} · ${v.driver}`);
    renderSidebar();
    renderQuickVehicles();
    updateGaugeChart();
  }
}

function toggleSimulationPlay() {
  simRunning = !simRunning;
  const btn = document.getElementById('btnSimPlay');
  if (btn) btn.innerHTML = simRunning ? '⏸ Пауза' : '▶ Пуск';
  toast(simRunning ? 'Движение запущено' : 'Движение на паузе');
}

function setSimSpeed(mult) {
  simMultiplier = mult;
  document.querySelectorAll('.sim-speed-btn').forEach(b =>
    b.classList.toggle('active', parseFloat(b.dataset.speed) === mult));
  toast(`Скорость симуляции: ${mult}×`);
}

function toggleFollowVehicle() {
  followVehicleLocked = !followVehicleLocked;
  const btn = document.getElementById('btnFollowLock');
  if (btn) {
    btn.classList.toggle('active', followVehicleLocked);
    btn.innerHTML = followVehicleLocked ? '🎯 Следование ВКЛ' : '🎯 Следовать';
  }
  toast(followVehicleLocked ? 'Камера следует за машиной' : 'Свободный обзор');
}

function toggleMapSatelliteLayer() {
  if (!leafletMap) return;
  if (currentLayerType === 'satellite') {
    leafletMap.removeLayer(baseLayers.satellite);
    baseLayers.osm.addTo(leafletMap);
    currentLayerType = 'osm';
    toast('Слой: Схема');
  } else {
    leafletMap.removeLayer(baseLayers.osm);
    baseLayers.satellite.addTo(leafletMap);
    currentLayerType = 'satellite';
    toast('Слой: Спутник');
  }
}

// ═══════════════════════════════════════════════════════════
// ECHARTS СПИДОМЕТР
// ═══════════════════════════════════════════════════════════
function initEChartsGauge() {
  const dom = document.getElementById('echartGaugeContainer');
  if (!dom || chartGauge) return;
  chartGauge = echarts.init(dom, 'dark');
  updateGaugeChart();
}

function updateGaugeChart() {
  if (!chartGauge) return;
  const v = fleetData.find(x => x.plate === selectedPlate) || fleetData[0];
  chartGauge.setOption({
    backgroundColor: 'transparent',
    series: [{
      type: 'gauge', center: ['50%', '60%'], radius: '90%',
      min: 0, max: 80, splitNumber: 8,
      axisLine: { lineStyle: { width: 8, color: [[.3,'#22c55e'],[.7,'#f59e0b'],[1,'#ef4444']] } },
      pointer: { itemStyle: { color: v.color }, width: 4 },
      axisTick:  { distance: -12, length: 4, lineStyle: { color:'#fff', width:1 } },
      splitLine: { distance: -16, length: 8, lineStyle: { color:'#fff', width:2 } },
      axisLabel: { color:'#94a3b8', distance:-24, fontSize:10, fontFamily:'JetBrains Mono' },
      detail: { valueAnimation:true, formatter:'{value} км/ч', color:'#e2e8f0', fontSize:14, fontFamily:'Unbounded', offsetCenter:[0,'70%'] },
      data: [{ value: Math.round(v.speed), name: v.plate }]
    }]
  });
}

// ═══════════════════════════════════════════════════════════
// ИМПОРТ И ЭКСПОРТ (GEOJSON / KML)
// ═══════════════════════════════════════════════════════════
function exportGeoJSON() {
  const features = [];
  userFields.forEach(f => {
    const ring = f.coords.map(pt => [pt[1], pt[0]]);
    if (ring.length > 0 && (ring[0][0] !== ring[ring.length-1][0] || ring[0][1] !== ring[ring.length-1][1])) {
      ring.push(ring[0]);
    }
    features.push({
      type: 'Feature',
      properties: { id: f.id, name: f.name, crop: f.crop, color: f.color, area: f.area, type: 'field' },
      geometry: { type: 'Polygon', coordinates: [ring] }
    });
  });

  userWarehouses.forEach(w => {
    features.push({
      type: 'Feature',
      properties: { id: w.id, name: w.name, sub: w.sub, type: 'warehouse' },
      geometry: { type: 'Point', coordinates: [w.lng, w.lat] }
    });
  });

  const blob = new Blob([JSON.stringify({ type: 'FeatureCollection', features }, null, 2)], { type: 'application/geo+json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'olzha_agro_fields.geojson';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  toast('💾 GeoJSON файл с полями выгружен');
}

function handleFileImport(input) {
  if (!input.files || input.files.length === 0) return;
  const file = input.files[0];
  const reader = new FileReader();

  reader.onload = e => {
    try {
      const content = e.target.result;
      if (file.name.toLowerCase().endsWith('.kml')) {
        parseAndLoadKML(content);
      } else {
        parseAndLoadGeoJSON(JSON.parse(content));
      }
      input.value = '';
    } catch(err) {
      alert('Ошибка чтения файла: ' + err.message);
    }
  };
  reader.readAsText(file);
}

function parseAndLoadGeoJSON(gj) {
  const features = gj.features || (gj.type === 'Feature' ? [gj] : []);
  if (!features || features.length === 0) { toast('⚠ В файле нет объектов'); return; }

  let fieldsCount = 0, whCount = 0;
  features.forEach(feat => {
    const geom = feat.geometry;
    const props = feat.properties || {};
    if (!geom) return;

    if (geom.type === 'Polygon' || geom.type === 'MultiPolygon') {
      const rings = geom.type === 'Polygon' ? geom.coordinates : geom.coordinates[0];
      if (rings && rings.length > 0) {
        const pts = rings[0].map(p => [Number(p[1].toFixed(5)), Number(p[0].toFixed(5))]);
        if (pts.length > 3 && pts[0][0] === pts[pts.length-1][0] && pts[0][1] === pts[pts.length-1][1]) pts.pop();
        if (pts.length >= 3) {
          const name = props.name || props.NAME || props.field_name || ('Поле Олжа ' + (userFields.length + 1));
          const crop = props.crop || props.CROP || props.culture || 'Пшеница';
          const color = props.color || FIELD_COLORS[userFields.length % FIELD_COLORS.length];
          const area = props.area || Math.round(calcAreaHa(pts));

          const f = {
            id: 'f-' + Date.now() + '-' + Math.random().toString(36).substr(2, 5),
            name: String(name), crop: String(crop), color, area, coords: pts,
            harvested: 0, expected: 22.0
          };
          userFields.push(f);
          renderField(f);
          fieldsCount++;
        }
      }
    } else if (geom.type === 'Point') {
      const name = props.name || props.NAME || props.title || 'Элеватор';
      const w = {
        id: 'w-' + Date.now() + '-' + Math.random().toString(36).substr(2, 5),
        name: String(name), sub: props.sub || 'Импортированный объект',
        lat: Number(geom.coordinates[1].toFixed(5)), lng: Number(geom.coordinates[0].toFixed(5))
      };
      userWarehouses.push(w);
      renderWarehouse(w);
      whCount++;
    }
  });

  saveUserData();
  fitAllObjects();
  toast(`✅ Импортировано: ${fieldsCount} полей, ${whCount} элеваторов`);
}

function parseAndLoadKML(kmlText) {
  const parser = new DOMParser();
  const xml = parser.parseFromString(kmlText, 'text/xml');
  const placemarks = xml.querySelectorAll('Placemark');
  let fieldsCount = 0;

  placemarks.forEach(pm => {
    const nameEl = pm.querySelector('name');
    const name = nameEl ? nameEl.textContent.trim() : ('Поле Олжа ' + (userFields.length + 1));
    const coordEl = pm.querySelector('Polygon coordinates, coordinates');
    if (coordEl) {
      const raw = coordEl.textContent.trim().split(/\s+/);
      const pts = [];
      raw.forEach(row => {
        const parts = row.split(',');
        if (parts.length >= 2) {
          const lng = parseFloat(parts[0]), lat = parseFloat(parts[1]);
          if (!isNaN(lat) && !isNaN(lng)) pts.push([Number(lat.toFixed(5)), Number(lng.toFixed(5))]);
        }
      });
      if (pts.length >= 3) {
        if (pts[0][0] === pts[pts.length-1][0] && pts[0][1] === pts[pts.length-1][1]) pts.pop();
        const color = FIELD_COLORS[userFields.length % FIELD_COLORS.length];
        const area = Math.round(calcAreaHa(pts));
        const f = {
          id: 'f-' + Date.now() + '-' + Math.random().toString(36).substr(2, 5),
          name, crop: 'Пшеница', color, area, coords: pts, harvested: 0, expected: 22.0
        };
        userFields.push(f);
        renderField(f);
        fieldsCount++;
      }
    }
  });

  saveUserData();
  fitAllObjects();
  toast(`✅ Импортировано из KML: ${fieldsCount} полей`);
}

// ═══════════════════════════════════════════════════════════
// ЭКСПОРТ В WINDOW ДЛЯ КНОПОК
// ═══════════════════════════════════════════════════════════
window.toggleMapSatelliteLayer    = toggleMapSatelliteLayer;
window.toggleSimulationPlay       = toggleSimulationPlay;
window.setSimSpeed                = setSimSpeed;
window.toggleFollowVehicle        = toggleFollowVehicle;
window.focusVehicle               = focusVehicle;
window.focusCluster               = focusCluster;
window.fitAllObjects              = fitAllObjects;
window.toggleEditMode             = toggleEditMode;
window.setEditTool                = setEditTool;
window.finishDrawField            = finishDrawField;
window.cancelDraw                 = cancelDraw;
window.deleteField                = deleteField;
window.deleteWarehouse            = deleteWarehouse;
window.editFieldName              = editFieldName;
window.editWarehouseName          = editWarehouseName;
window.enableWarehouseDrag        = enableWarehouseDrag;
window.startEditingFieldVertices  = startEditingFieldVertices;
window.showAllFieldVertexHandles  = showAllFieldVertexHandles;
window.resetToRealOlzhaAgro       = resetToRealOlzhaAgro;
window.clearAllData               = clearAllData;
window.saveUserData               = saveUserData;
window.exportGeoJSON              = exportGeoJSON;
window.handleFileImport           = handleFileImport;

window.addEventListener('resize', () => { if (chartGauge) chartGauge.resize(); });

document.addEventListener('DOMContentLoaded', () => {
  loadUserData();
  initLeafletMap();
  initMotionEngine();
  setTimeout(initEChartsGauge, 200);
});
