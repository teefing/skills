const https = require('https');
const http = require('http');

const API_BASE = 'http://github-trending-api.liuxianyu.cn/repository/list';

function parseArgs() {
  const args = process.argv.slice(2);
  const params = {
    language: null,
    since: 'daily',
    limit: 10,
    json: false
  };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--language' && args[i + 1]) {
      params.language = args[i + 1];
      i++;
    } else if (args[i] === '--since' && args[i + 1]) {
      params.since = args[i + 1];
      i++;
    } else if (args[i] === '--limit' && args[i + 1]) {
      params.limit = parseInt(args[i + 1], 10);
      i++;
    } else if (args[i] === '--json') {
      params.json = true;
    }
  }

  return params;
}

function fetchTrending(params) {
  return new Promise((resolve, reject) => {
    let url = `${API_BASE}?dateRange=${params.since}&pageSize=${params.limit}`;
    if (params.language) {
      url += `&language=${encodeURIComponent(params.language)}`;
    }

    const protocol = url.startsWith('https') ? https : http;

    protocol.get(url, (res) => {
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

function formatRepo(repo) {
  const lines = [];
  lines.push(`\x1b[1;36m${repo.username}/${repo.repositoryName}\x1b[0m`);
  lines.push(`  ${repo.description || 'No description'}`);
  lines.push(`  Language: \x1b[33m${repo.language || 'Unknown'}\x1b[0m | ` +
             `Stars: \x1b[32m${repo.starCountStr}\x1b[0m | ` +
             `Forks: \x1b[34m${repo.forkCountStr}\x1b[0m | ` +
             `Today: \x1b[31m+${repo.todayStarStr}\x1b[0m`);
  lines.push(`  URL: \x1b[4;37m${repo.url}\x1b[0m`);
  return lines.join('\n');
}

async function main() {
  const params = parseArgs();

  try {
    const response = await fetchTrending(params);

    if (response.code !== 200) {
      console.error(`Error: ${response.message || 'Unknown error'}`);
      process.exit(1);
    }

    const repos = response.data.list;

    if (params.json) {
      console.log(JSON.stringify(repos, null, 2));
      return;
    }

    console.log(`\x1b[1;35mFetching GitHub Trending\x1b[0m`);
    console.log(`Language: ${params.language || 'all'} | Since: ${params.since} | Limit: ${params.limit}`);
    console.log('─'.repeat(60));

    if (repos.length === 0) {
      console.log('No trending repositories found.');
      return;
    }

    repos.forEach((repo, index) => {
      console.log(`\n[\x1b[1;37m${index + 1}\x1b[0m] ${formatRepo(repo)}`);
    });

    console.log('\n' + '─'.repeat(60));
    console.log(`Total: ${response.data.total} repositories | Showing: ${repos.length}`);
    console.log(`Cache: ${response.data.isCache} | Updated: ${repos[0]?.time || 'N/A'}`);

  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

main();
