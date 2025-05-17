import type { RequestHandler } from '@sveltejs/kit';
import Database from 'better-sqlite3';
import { join } from 'path';

const dbPath = join(process.cwd(), 'data', 'ecfr_analysis.db');

export const GET: RequestHandler = async () => {
  try {
    const db = new Database(dbPath, { readonly: true });

    // 1. Top and Bottom 10% by Word Count
    const agencies = db.prepare('SELECT name, word_count FROM agencies WHERE word_count > 0 ORDER BY word_count DESC').all();
    const totalAgencies = agencies.length;
    const top10PercentCount = Math.ceil(totalAgencies * 0.1);
    const topWordCount = agencies.slice(0, top10PercentCount).slice(0, 5);
    const bottomWordCount = agencies.slice(-top10PercentCount).slice(-5);

    // 2. Word Count Statistics
    const wordCountStats = db.prepare(`
      SELECT 
        SUM(word_count) as total_words,
        AVG(word_count) as mean_words,
        (SELECT word_count FROM agencies WHERE word_count IS NOT NULL ORDER BY word_count LIMIT 1 OFFSET CAST(? / 2 AS INTEGER)) as median_words,
        SQRT(
          AVG(
            CASE 
              WHEN word_count IS NOT NULL 
              THEN (word_count - (SELECT AVG(word_count) FROM agencies WHERE word_count IS NOT NULL)) * 
                  (word_count - (SELECT AVG(word_count) FROM agencies WHERE word_count IS NOT NULL))
              ELSE 0
            END
          )
        ) as std_dev
      FROM agencies
      WHERE word_count IS NOT NULL
    `).get(totalAgencies);

    // 3. Top 10% by Correction Frequency
    const correctionCounts = db.prepare(`
      SELECT a.name, COUNT(c.id) as correction_count
      FROM agencies a
      LEFT JOIN agency_corrections c ON a.name = c.agency_name
      GROUP BY a.name
      ORDER BY correction_count DESC
    `).all();
    const topCorrections = correctionCounts.slice(0, top10PercentCount).slice(0, 5);

    // 4. Correction Rate per Word Count
    const correctionRates = db.prepare(`
      SELECT 
        a.name, 
        a.word_count,
        COUNT(c.id) as correction_count,
        (COUNT(c.id) * 1000.0 / a.word_count) as corrections_per_1000_words
      FROM agencies a
      LEFT JOIN agency_corrections c ON a.name = c.agency_name
      GROUP BY a.name
      HAVING a.word_count > 0
      ORDER BY corrections_per_1000_words DESC
    `).all();
    const topCorrectionRates = correctionRates.slice(0, top10PercentCount).slice(0, 5);

    // 5. Recent Corrections
    const recentCorrections = db.prepare(`
      SELECT c.agency_name, c.title, c.corrective_action, c.error_corrected, c.fr_citation
      FROM agency_corrections c
      ORDER BY c.error_corrected DESC
      LIMIT 5
    `).all();

    // 6. Sub-Agency Ratio
    const subAgencyRatios = db.prepare(`
      SELECT 
        name, 
        sub_agencies, 
        word_count,
        (sub_agencies * 1000.0 / word_count) as sub_agencies_per_1000_words
      FROM agencies
      WHERE word_count > 0
      ORDER BY sub_agencies_per_1000_words DESC
    `).all();
    const topSubAgencyRatios = subAgencyRatios.slice(0, top10PercentCount).slice(0, 5);

    db.close();

    return new Response(
      JSON.stringify({
        topWordCount,
        bottomWordCount,
        wordCountStats,
        topCorrections,
        topCorrectionRates,
        recentCorrections,
        topSubAgencyRatios
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  } catch (error) {
    console.error('Error fetching metrics:', error);
    return new Response(JSON.stringify({ error: 'Failed to fetch metrics' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
};