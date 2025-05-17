import type { RequestHandler } from '@sveltejs/kit';
import { createClient } from '@supabase/supabase-js';
import { SUPABASE_URL, SUPABASE_ANON_KEY } from '$env/static/private';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

export const GET: RequestHandler = async ({ url }) => {
  try {
    // Get query parameters
    const agencyName = url.searchParams.get('agency_name') || '';
    const limit = parseInt(url.searchParams.get('limit') || '50', 10);
    const offset = parseInt(url.searchParams.get('offset') || '0', 10);

    // Build Supabase query
    let query = supabase
      .from('agency_corrections')
      .select('*', { count: 'exact' })
      .order('error_corrected', { ascending: false })
      .range(offset, offset + limit - 1);

    if (agencyName) {
      query = query.eq('agency_name', agencyName);
    }

    // Execute query
    const { data: corrections, error, count } = await query;

    if (error) {
      console.error('Error fetching corrections:', error);
      return new Response(JSON.stringify({ error: 'Failed to fetch corrections' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    return new Response(
      JSON.stringify({ corrections, total: count, limit, offset }),
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