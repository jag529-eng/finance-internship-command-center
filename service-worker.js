const CACHE='frt-v1';
const CORE=['./','./index.html','./assets/styles.css','./src/app.js','./data/jobs.json','./data/employers.json','./data/monitor_health.json'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE.filter(Boolean))).catch(()=>{})));
self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;e.respondWith(fetch(e.request).then(r=>{const clone=r.clone();caches.open(CACHE).then(c=>c.put(e.request,clone));return r}).catch(()=>caches.match(e.request)))})
