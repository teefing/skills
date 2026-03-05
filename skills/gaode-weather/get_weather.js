const https = require('https');

const API_BASE = 'https://restapi.amap.com/v3/weather/weatherInfo';
const DEFAULT_KEY = 'fb0b8bd4f451541239cd995aeea6b4ea';

function parseArgs() {
  const args = process.argv.slice(2);
  const params = {
    city: null,
    key: process.env.GAODE_WEATHER_KEY || DEFAULT_KEY,
    extensions: 'base',
    json: false
  };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--city' && args[i + 1]) {
      params.city = args[i + 1];
      i++;
    } else if (args[i] === '--key' && args[i + 1]) {
      params.key = args[i + 1];
      i++;
    } else if (args[i] === '--extensions' && args[i + 1]) {
      params.extensions = args[i + 1];
      i++;
    } else if (args[i] === '--json') {
      params.json = true;
    }
  }

  return params;
}

function fetchWeather(params) {
  return new Promise((resolve, reject) => {
    if (!params.key) {
      reject(new Error('API key is required. Set GAODE_WEATHER_KEY env or use --key parameter.'));
      return;
    }
    if (!params.city) {
      reject(new Error('City adcode is required. Use --city parameter.'));
      return;
    }

    const url = `${API_BASE}?key=${params.key}&city=${params.city}&extensions=${params.extensions}`;

    https.get(url, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          resolve(json);
        } catch (e) {
          reject(new Error(`Failed to parse response: ${e.message}`));
        }
      });
    }).on('error', (e) => {
      reject(new Error(`Request failed: ${e.message}`));
    });
  });
}

function formatWeather(info) {
  const lines = [];
  lines.push(`\x1b[1;36m${info.city}\x1b[0m`);
  lines.push(`  Weather: \x1b[33m${info.weather}\x1b[0m`);
  lines.push(`  Temperature: \x1b[32m${info.temperature}°C\x1b[0m`);
  lines.push(`  Humidity: ${info.humidity}%`);
  lines.push(`  Wind: ${info.winddirection} ${info.windpower}`);
  lines.push(`  Report Time: ${info.reporttime}`);
  return lines.join('\n');
}

function formatForecast(casts) {
  const lines = [];
  casts.forEach((cast, index) => {
    lines.push(`\x1b[1;36m${cast.date} (${cast.week})\x1b[0m`);
    lines.push(`  Day: \x1b[33m${cast.dayweather}\x1b[0m ${cast.daytemp}°C | Night: ${cast.nightweather} ${cast.nighttemp}°C`);
    lines.push(`  Wind: ${cast.daywind} ${cast.daypower}`);
    if (index < casts.length - 1) lines.push('');
  });
  return lines.join('\n');
}

async function main() {
  const params = parseArgs();

  try {
    const response = await fetchWeather(params);

    if (response.status !== '1') {
      console.error(`Error: ${response.info || 'Unknown error'}`);
      process.exit(1);
    }

    if (params.json) {
      console.log(JSON.stringify(response, null, 2));
      return;
    }

    console.log(`\x1b[1;35mGaode Weather\x1b[0m`);
    console.log('─'.repeat(50));

    if (params.extensions === 'all' && response.forecasts && response.forecasts[0]) {
      const forecast = response.forecasts[0];
      console.log(`\x1b[1;37mCity: ${forecast.city}\x1b[0m\n`);
      console.log(formatForecast(forecast.casts));
    } else if (response.lives && response.lives[0]) {
      console.log(formatWeather(response.lives[0]));
    } else {
      console.log('No weather data found.');
    }

  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

main();
