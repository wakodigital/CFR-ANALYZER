import type { RequestHandler } from '@sveltejs/kit';
import Database from 'better-sqlite3';
import { join } from 'path';

const dbPath = join(process.cwd(), 'data', 'ecfr_analysis.db');

// Singleton database instance
let db: Database.Database | null = null;

function getDb() {
    if (!db) {
        db = new Database(dbPath, { readonly: true });
    }
    return db;
}

interface QueryParams {
    page?: string;
    limit?: string;
    agency_name?: string;
    error_message?: string;
    sort?: string;
    direction?: 'asc' | 'desc';
}

export const GET: RequestHandler = async ({ url }) => {
    try {
        const db = getDb();
        const params: QueryParams = Object.fromEntries(url.searchParams);

        const page = parseInt(params.page || '1', 10);
        const limit = parseInt(params.limit || '50', 10);
        const offset = (page - 1) * limit;
        const agency_name = params.agency_name || '';
        const error_message = params.error_message || '';
        const sort = params.sort || 'id';
        const direction = params.direction || 'asc';

        // Validate sort and direction
        const validSortColumns = ['id', 'agency_name', 'cfr_reference', 'error_message', 'timestamp'];
        if (!validSortColumns.includes(sort)) {
            throw new Error('Invalid sort column');
        }
        if (!['asc', 'desc'].includes(direction)) {
            throw new Error('Invalid sort direction');
        }

        // Build query
        const whereClauses = [];
        const queryParams = [];
        if (agency_name) {
            whereClauses.push('agency_name LIKE ?');
            queryParams.push(`%${agency_name}%`);
        }
        if (error_message) {
            whereClauses.push('error_message LIKE ?');
            queryParams.push(`%${error_message}%`);
        }
        const whereClause = whereClauses.length ? `WHERE ${whereClauses.join(' AND ')}` : '';

        // Fetch errors
        const errors = db
            .prepare(`
                SELECT id, agency_name, cfr_reference, error_message, timestamp
                FROM cfr_reference_errors
                ${whereClause}
                ORDER BY ${sort} ${direction}
                LIMIT ? OFFSET ?
            `)
            .all(...queryParams, limit, offset) as {
                id: number;
                agency_name: string;
                cfr_reference: string;
                error_message: string;
                timestamp: string;
            }[];

        // Get total count for pagination
        const total = db
            .prepare(`
                SELECT COUNT(*) as count
                FROM cfr_reference_errors
                ${whereClause}
            `)
            .get(...queryParams) as { count: number };

        return new Response(
            JSON.stringify({
                data: errors,
                pagination: {
                    page,
                    limit,
                    total: total.count,
                    totalPages: Math.ceil(total.count / limit)
                }
            }),
            {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    } catch (error) {
        console.error('Error fetching CFR reference errors:', error);
        return new Response(JSON.stringify({ error: 'Failed to fetch errors' }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
};

// Close database on server shutdown
process.on('SIGTERM', () => {
    if (db) {
        db.close();
        db = null;
    }
});