---
name: "gaode-weather"
description: "Get weather information from Gaode Amap API. Invoke when user needs to check weather, temperature, or forecast for a city."
---

# gaode-weather

Get weather information from Gaode Amap (高德地图) API. Supports real-time weather and forecast data.

## Usage

### Get Weather Info
Retrieve weather information for a city.

```bash
node skills/gaode-weather/get_weather.js --city 330110
```

### Get Forecast
Get forecast data for the next few days:

```bash
node skills/gaode-weather/get_weather.js --city 330110 --extensions all
```

### JSON Output
Get results in JSON format:

```bash
node skills/gaode-weather/get_weather.js --city 330110 --json
```

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--city` | 是 | - | City adcode (e.g., 330110 for Hangzhou) |
| `--extensions` | 否 | base | `base` for real-time weather, `all` for forecast |
| `--json` | 否 | false | Output as JSON format |

## Output

### Real-time Weather
- `city`: City name
- `weather`: Weather condition (e.g., 晴)
- `temperature`: Temperature (°C)
- `humidity`: Humidity (%)
- `windDirection`: Wind direction
- `windPower`: Wind power
- `reportTime`: Report time

### Forecast (when extensions=all)
Includes forecast data for the next 3-4 days.

## Common City Adcodes

| City | Adcode |
|------|--------|
| 杭州 | 330110 |
| 北京 | 110000 |
| 上海 | 310000 |
| 广州 | 440100 |
| 深圳 | 440300 |
