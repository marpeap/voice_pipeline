/**
 * DASHBOARD CONFIGURATION — Marpeap Voice Agent
 * Niveau 2 : Intermédiaire (Basic Auth, Validation, Backup)
 * 
 * Auth: Marpeap / Error404
 * Port: 4000
 */

const express = require('express');
const basicAuth = require('basic-auth');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
require('dotenv').config();

const app = express();
const PORT = process.env.DASHBOARD_PORT || 4000;

// Chemins
const ENV_PATH = '/var/www/marpeap.com/retell-agent/.env';
const BACKUP_DIR = path.join(__dirname, 'backups');

// Middleware
app.use(express.json());
app.use(express.static('public'));

// ========== AUTHENTIFICATION ==========
const authenticate = (req, res, next) => {
  const credentials = basicAuth(req);
  
  if (!credentials || 
      credentials.name !== 'Marpeap' || 
      credentials.pass !== 'Error404') {
    res.set('WWW-Authenticate', 'Basic realm="Marpeap Dashboard"');
    return res.status(401).json({ error: 'Authentication required' });
  }
  
  next();
};

// Appliquer auth sur toutes les routes API
app.use('/api/', authenticate);

// ========== FONCTIONS UTILITAIRES ==========

const readEnvFile = () => {
  try {
    if (!fs.existsSync(ENV_PATH)) {
      return {};
    }
    const content = fs.readFileSync(ENV_PATH, 'utf8');
    const env = {};
    content.split('\n').forEach(line => {
      const match = line.match(/^([^=]+)=(.*)$/);
      if (match) {
        env[match[1]] = match[2];
      }
    });
    return env;
  } catch (e) {
    console.error('Erreur lecture .env:', e);
    return {};
  }
};

const writeEnvFile = (config) => {
  // 1. Backup
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const backupPath = path.join(BACKUP_DIR, `.env.backup.${timestamp}`);
  
  if (fs.existsSync(ENV_PATH)) {
    fs.copyFileSync(ENV_PATH, backupPath);
  }
  
  // 2. Générer contenu
  const content = Object.entries(config)
    .map(([key, value]) => `${key}=${value}`)
    .join('\n');
  
  // 3. Écriture atomique
  fs.writeFileSync(`${ENV_PATH}.tmp`, content);
  fs.renameSync(`${ENV_PATH}.tmp`, ENV_PATH);
  
  return backupPath;
};

const maskKey = (key) => {
  if (!key || key.length < 8) return '***';
  return key.substring(0, 4) + '***' + key.substring(key.length - 4);
};

// ========== ENDPOINTS API ==========

// 1. GET /api/config — Lire configuration
app.get('/api/config', (req, res) => {
  try {
    const env = readEnvFile();
    
    res.json({
      retell: {
        configured: !!env.RETELL_API_KEY,
        key_preview: maskKey(env.RETELL_API_KEY),
        agent_id: env.AGENT_ID || ''
      },
      elevenlabs: {
        configured: !!env.ELEVENLABS_API_KEY,
        key_preview: maskKey(env.ELEVENLABS_API_KEY),
        voice_id: env.CARTESIA_VOICE_ID || env.ELEVENLABS_VOICE_ID || ''
      },
      agent: {
        name: env.AGENT_NAME || 'Sarah',
        company: env.AGENT_COMPANY || 'Marpeap Digitals',
        prompt: env.AGENT_PROMPT || ''
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 2. POST /api/config — Sauvegarder configuration
app.post('/api/config', (req, res) => {
  try {
    const {
      retell_api_key,
      elevenlabs_api_key,
      agent_id,
      agent_name,
      agent_company,
      agent_prompt,
      voice_id
    } = req.body;
    
    // Lire config actuelle
    const currentEnv = readEnvFile();
    
    // Fusionner
    const newEnv = {
      ...currentEnv,
      RETELL_API_KEY: retell_api_key || currentEnv.RETELL_API_KEY,
      ELEVENLABS_API_KEY: elevenlabs_api_key || currentEnv.ELEVENLABS_API_KEY,
      AGENT_ID: agent_id || currentEnv.AGENT_ID,
      AGENT_NAME: agent_name || currentEnv.AGENT_NAME,
      AGENT_COMPANY: agent_company || currentEnv.AGENT_COMPANY,
      AGENT_PROMPT: agent_prompt || currentEnv.AGENT_PROMPT,
      ELEVENLABS_VOICE_ID: voice_id || currentEnv.ELEVENLABS_VOICE_ID,
      PORT: '3000'
    };
    
    // Sauvegarder
    const backupPath = writeEnvFile(newEnv);
    
    res.json({
      success: true,
      message: 'Configuration sauvegardée',
      backup_created: path.basename(backupPath)
    });
    
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 3. POST /api/test/retell — Tester connexion Retell
app.post('/api/test/retell', async (req, res) => {
  try {
    const { api_key } = req.body;
    const key = api_key || readEnvFile().RETELL_API_KEY;
    
    if (!key) {
      return res.status(400).json({ error: 'Clé API manquante' });
    }
    
    const start = Date.now();
    
    // Test simple : récupérer les agents
    const response = await fetch('https://api.retellai.com/v2/list-agents', {
      headers: {
        'Authorization': `Bearer ${key}`,
        'Content-Type': 'application/json'
      }
    });
    
    const latency = Date.now() - start;
    
    if (response.ok) {
      const data = await response.json();
      res.json({
        success: true,
        latency_ms: latency,
        agents_count: data.length || 0,
        message: 'Connexion OK'
      });
    } else {
      res.status(400).json({
        success: false,
        error: `Erreur Retell: ${response.status}`,
        message: 'Clé invalide ou service indisponible'
      });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 4. POST /api/test/elevenlabs — Tester connexion ElevenLabs
app.post('/api/test/elevenlabs', async (req, res) => {
  try {
    const { api_key } = req.body;
    const key = api_key || readEnvFile().ELEVENLABS_API_KEY;
    
    if (!key) {
      return res.status(400).json({ error: 'Clé API manquante' });
    }
    
    const start = Date.now();
    
    // Test : récupérer les voix
    const response = await fetch('https://api.elevenlabs.io/v1/voices', {
      headers: {
        'xi-api-key': key
      }
    });
    
    const latency = Date.now() - start;
    
    if (response.ok) {
      const data = await response.json();
      const frenchVoices = data.voices.filter(v => 
        v.labels?.language === 'fr' || 
        v.name.toLowerCase().includes('french')
      );
      
      res.json({
        success: true,
        latency_ms: latency,
        total_voices: data.voices.length,
        french_voices: frenchVoices.length,
        voices: frenchVoices.slice(0, 5).map(v => ({
          id: v.voice_id,
          name: v.name
        }))
      });
    } else {
      res.status(400).json({
        success: false,
        error: `Erreur ElevenLabs: ${response.status}`
      });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 5. POST /api/restart — Redémarrer le serveur voice
app.post('/api/restart', (req, res) => {
  exec('pm2 reload voice-agent || pm2 restart voice-agent || echo "PM2 not found"', 
    (error, stdout, stderr) => {
      if (error) {
        console.error('Erreur restart:', error);
        return res.status(500).json({ 
          error: 'Erreur redémarrage',
          details: error.message 
        });
      }
      
      res.json({
        success: true,
        message: 'Serveur redémarré',
        output: stdout
      });
    }
  );
});

// 6. GET /api/backups — Lister les backups
app.get('/api/backups', (req, res) => {
  try {
    const files = fs.readdirSync(BACKUP_DIR)
      .filter(f => f.startsWith('.env.backup'))
      .sort()
      .reverse();
    
    res.json({ backups: files });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 7. GET /api/status — Status serveur
app.get('/api/status', (req, res) => {
  res.json({
    status: 'OK',
    dashboard: 'running',
    timestamp: new Date().toISOString(),
    env_file_exists: fs.existsSync(ENV_PATH)
  });
});

// ========== PAGE PRINCIPALE ==========

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Démarrage
app.listen(PORT, () => {
  console.log(`\n🎛️  Dashboard Marpeap démarré`);
  console.log(`================================`);
  console.log(`🌐 URL: http://localhost:${PORT}`);
  console.log(`🔐 Auth: Marpeap / Error404`);
  console.log(`📁 Env: ${ENV_PATH}`);
  console.log(`================================\n`);
});
