import type { RequestHandler } from '@sveltejs/kit';
import Database from 'better-sqlite3';
import { join } from 'path';
import { DB_PATH } from '$env/static/private';

const dbPath = join(process.cwd(), DB_PATH);

export const GET: RequestHandler = async ({ url }) => {
  try {
    const db = new Database(dbPath, { readonly: true });

    // Get query parameters
    const search = url.searchParams.get('search') || '';
    const sort = url.searchParams.get('sort') || 'name';
    const limit = parseInt(url.searchParams.get('limit') || '50', 10);
    const offset = parseInt(url.searchParams.get('offset') || '0', 10);

    // Build SQL query
    let query = 'SELECT * FROM agencies';
    const params: any[] = [];

    if (search) {
      query += ' WHERE name LIKE ?';
      params.push(`%${search}%`);
    }

    if (sort === 'word_count') {
      query += ' ORDER BY word_count DESC';
    } else {
      query += ' ORDER BY name ASC';
    }

    query += ' LIMIT ? OFFSET ?';
    params.push(limit, offset);

    // Execute query
    const agencies = db.prepare(query).all(...params);

    // Get total count for pagination
    const total = db.prepare('SELECT COUNT(*) as count FROM agencies').get().count;

    db.close();

    return new Response(
      JSON.stringify({ agencies, total, limit, offset }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  } catch (error) {
    console.error('Error fetching agencies:', error);
    return new Response(JSON.stringify({ error: 'Failed to fetch agencies' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
};