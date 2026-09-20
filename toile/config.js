// Où joindre l'agent, pour ce déploiement-ci.
//
// Ce fichier est réécrit à chaque publication à partir de la variable
// d'environnement `AGENT_WS` (voir `vercel.json`). La valeur ci-dessous est
// celle du développement : le standard sert la page lui-même, et le canal part
// vers le même hôte.
window.CONFIGURATION = { agent: "" };
