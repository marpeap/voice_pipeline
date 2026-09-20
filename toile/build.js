// Écrit `config.js` et remplit le nom du salon, à partir de l'environnement du
// déploiement. Deux variables, et rien d'autre :
//
//   AGENT_WS    l'adresse du canal, par exemple wss://agent.marpeap.com/parler
//   SALON       le nom prononcé et affiché, par exemple « Salon Marpeap »
//
// Sans build, la page reste utilisable : le standard la sert lui-même en local
// et le canal part vers le même hôte.
const fs = require('fs');

const agent = process.env.AGENT_WS || '';
const salon = process.env.SALON || 'Salon Marpeap';

fs.writeFileSync('config.js',
  `// Généré au déploiement — ne pas modifier à la main.\n` +
  `window.CONFIGURATION = ${JSON.stringify({ agent })};\n`);

const page = fs.readFileSync('index.html', 'utf8').split('{{SALON}}').join(salon);
fs.writeFileSync('index.html', page);

console.log(`front-end prêt : salon « ${salon} », agent « ${agent || 'même hôte'} »`);
