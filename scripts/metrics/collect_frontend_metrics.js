#!/usr/bin/env node
/**
 * Frontend Code Metrics Collector.
 *
 * Collects various code quality metrics for the LLARS frontend:
 * - JSDoc coverage for Vue components and composables
 * - Line counts and file sizes
 * - Component complexity indicators
 *
 * Usage:
 *   node scripts/metrics/collect_frontend_metrics.js [--json]
 *
 * Author: LLARS Team
 * Date: January 2026
 */

const fs = require('fs');
const path = require('path');

const LARGE_FILE_THRESHOLD = 500;
const FRONTEND_PATH = path.join(__dirname, '../../llars-frontend/src');

/**
 * Check if a file has a JSDoc header comment.
 * @param {string} content - File content
 * @returns {boolean}
 */
function hasJSDocHeader(content) {
  // Check for JSDoc-style comment at the start of the file
  const trimmed = content.trim();
  return trimmed.startsWith('/**') ||
         trimmed.startsWith('<!--') ||  // Vue template comment
         trimmed.match(/^<script[^>]*>\s*\/\*\*/);  // Script tag with JSDoc
}

/**
 * Count JSDoc comments in a file.
 * @param {string} content - File content
 * @returns {number}
 */
function countJSDocComments(content) {
  const matches = content.match(/\/\*\*[\s\S]*?\*\//g);
  return matches ? matches.length : 0;
}

/**
 * Count functions/methods in a file.
 * @param {string} content - File content
 * @returns {number}
 */
function countFunctions(content) {
  const patterns = [
    /function\s+\w+\s*\(/g,           // function declarations
    /\w+\s*:\s*function\s*\(/g,        // object method shorthand
    /\w+\s*=\s*(?:async\s+)?function/g, // function expressions
    /(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?\([^)]*\)\s*=>/g, // arrow functions
    /\w+\s*\([^)]*\)\s*{/g,           // method definitions
  ];

  let count = 0;
  for (const pattern of patterns) {
    const matches = content.match(pattern);
    if (matches) count += matches.length;
  }

  return Math.max(1, Math.floor(count / 2)); // Rough estimate, avoid double counting
}

/**
 * Collect metrics for Vue files in a directory.
 * @param {string} dir - Directory path
 * @param {string} basePath - Base path for relative paths
 * @returns {Object}
 */
function collectVueMetrics(dir, basePath) {
  const results = {
    files: [],
    totalFiles: 0,
    totalLines: 0,
    filesWithJSDoc: 0,
    largeFiles: [],
  };

  if (!fs.existsSync(dir)) {
    return results;
  }

  function walkDir(currentDir) {
    const entries = fs.readdirSync(currentDir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(currentDir, entry.name);

      if (entry.isDirectory()) {
        if (!['node_modules', 'dist', '.git', 'coverage'].includes(entry.name)) {
          walkDir(fullPath);
        }
      } else if (entry.name.endsWith('.vue') || entry.name.endsWith('.js')) {
        try {
          const content = fs.readFileSync(fullPath, 'utf8');
          const lines = content.split('\n').length;
          const relativePath = path.relative(basePath, fullPath);
          const hasJSDoc = hasJSDocHeader(content);
          const jsDocCount = countJSDocComments(content);

          results.files.push({
            path: relativePath,
            lines,
            hasJSDoc,
            jsDocCount,
          });

          results.totalFiles++;
          results.totalLines += lines;
          if (hasJSDoc) results.filesWithJSDoc++;
          if (lines > LARGE_FILE_THRESHOLD) {
            results.largeFiles.push(`${relativePath} (${lines} lines)`);
          }
        } catch (err) {
          console.error(`Error reading ${fullPath}: ${err.message}`);
        }
      }
    }
  }

  walkDir(dir);
  return results;
}

/**
 * Main function to collect all frontend metrics.
 */
function collectAllMetrics() {
  const timestamp = new Date().toISOString();

  const directories = {
    components: path.join(FRONTEND_PATH, 'components'),
    composables: path.join(FRONTEND_PATH, 'composables'),
    views: path.join(FRONTEND_PATH, 'views'),
    services: path.join(FRONTEND_PATH, 'services'),
  };

  const results = {
    timestamp,
    directories: {},
    summary: {
      totalFiles: 0,
      totalLines: 0,
      filesWithJSDoc: 0,
      coverage: 0,
    },
    largeFiles: [],
  };

  let totalFiles = 0;
  let filesWithJSDoc = 0;
  let totalLines = 0;

  for (const [name, dirPath] of Object.entries(directories)) {
    const metrics = collectVueMetrics(dirPath, FRONTEND_PATH);

    results.directories[name] = {
      path: path.relative(path.join(__dirname, '../..'), dirPath),
      files: metrics.totalFiles,
      lines: metrics.totalLines,
      filesWithJSDoc: metrics.filesWithJSDoc,
      coverage: metrics.totalFiles > 0
        ? Math.round((metrics.filesWithJSDoc / metrics.totalFiles) * 100)
        : 0,
      largeFiles: metrics.largeFiles,
    };

    totalFiles += metrics.totalFiles;
    filesWithJSDoc += metrics.filesWithJSDoc;
    totalLines += metrics.totalLines;
    results.largeFiles.push(...metrics.largeFiles);
  }

  results.summary = {
    totalFiles,
    totalLines,
    filesWithJSDoc,
    coverage: totalFiles > 0 ? Math.round((filesWithJSDoc / totalFiles) * 100) : 0,
  };

  return results;
}

/**
 * Print metrics in human-readable format.
 * @param {Object} metrics
 */
function printHumanReadable(metrics) {
  console.log('\n' + '='.repeat(60));
  console.log('LLARS Frontend Code Metrics');
  console.log('='.repeat(60));
  console.log(`Generated: ${metrics.timestamp}\n`);

  console.log('📁 Directory Breakdown:');
  console.log('-'.repeat(60));

  for (const [name, data] of Object.entries(metrics.directories)) {
    const icon = data.coverage >= 70 ? '✅' : data.coverage >= 50 ? '⚠️' : '❌';
    console.log(`\n${name.toUpperCase()} (${data.path})`);
    console.log(`  Files: ${data.files}, Lines: ${data.lines.toLocaleString()}`);
    console.log(`  JSDoc Coverage: ${data.filesWithJSDoc}/${data.files} (${data.coverage}%) ${icon}`);

    if (data.largeFiles.length > 0) {
      console.log(`  ⚠️  Large files: ${data.largeFiles.slice(0, 3).join(', ')}`);
    }
  }

  console.log('\n' + '-'.repeat(60));
  console.log('📊 SUMMARY');
  console.log('-'.repeat(60));
  const s = metrics.summary;
  const icon = s.coverage >= 70 ? '✅' : s.coverage >= 50 ? '⚠️' : '❌';
  console.log(`  Total Files: ${s.totalFiles}`);
  console.log(`  Total Lines: ${s.totalLines.toLocaleString()}`);
  console.log(`  JSDoc Coverage: ${s.coverage}% ${icon}`);

  if (metrics.largeFiles.length > 0) {
    console.log(`\n⚠️  Large files (>${LARGE_FILE_THRESHOLD} lines):`);
    metrics.largeFiles.slice(0, 10).forEach(f => console.log(`    - ${f}`));
    if (metrics.largeFiles.length > 10) {
      console.log(`    ... and ${metrics.largeFiles.length - 10} more`);
    }
  }

  console.log('\n' + '='.repeat(60));
}

// Main execution
const outputJson = process.argv.includes('--json');
const metrics = collectAllMetrics();

if (outputJson) {
  console.log(JSON.stringify(metrics, null, 2));
} else {
  printHumanReadable(metrics);
}

// Save to file (only in non-JSON mode to avoid corrupting stdout output)
if (!outputJson) {
  const outputDir = path.join(__dirname, '../../docs/metrics');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const outputFile = path.join(outputDir, 'frontend_metrics.json');
  fs.writeFileSync(outputFile, JSON.stringify(metrics, null, 2));
  console.log(`\n💾 Metrics saved to: ${outputFile}`);
}
