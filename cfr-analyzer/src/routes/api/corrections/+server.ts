import type { RequestHandler } from '@sveltejs/kit';
import Database from 'better-sqlite3';
import { join } from 'path';

const dbPath = join(process.cwd(), 'data', 'ecfr_analysis.db');

export const GET: RequestHandler = async ({ url }) => {
  try {
    const db = new Database(dbPath, { readonly: true });

    // Get query parameters
    const agencyName = url.searchParams.get('agency_name') || '';
    const limit = parseInt(url.searchParams.get('limit') || '50', 10);
    const offset = parseInt(url.searchParams.get('offset') || '0', 10);

    // Build SQL query
    let query = 'SELECT * FROM agency_corrections';
    const params: any[] = [];

    if (agencyName) {
      query += ' WHERE agency_name = ?';
      params.push(agencyName);
    }

    query += ' ORDER BY error_corrected DESC LIMIT ? OFFSET ?';
    params.push(limit, offset);

    // Execute query
    const corrections = db.prepare(query).all(...params);

    // Get total count for pagination
    const totalQuery = agencyName
      ? 'SELECT COUNT(*) as count FROM agency_corrections WHERE agency_name = ?'
      : 'SELECT COUNT(*) as count FROM agency_corrections';
    const totalParams = agencyName ? [agencyName] : [];
    const total = db.prepare(totalQuery).get(...totalParams).count;

    db.close();

    return new Response(
      JSON.stringify({ corrections, total, limit, offset }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  } catch (error) {
    console.error('Error fetching corrections:', error);
    return new Response(JSON.stringify({ error: 'Failed to fetch corrections' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
};