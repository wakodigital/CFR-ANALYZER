import type { RequestHandler } from '@sveltejs/kit';
import { createClient } from '@supabase/supabase-js';
import { SUPABASE_URL, SUPABASE_ANON_KEY } from '$env/static/private';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

export const GET: RequestHandler = async ({ url }) => {
  try {
    // Get query parameters
    const search = url.searchParams.get('search')?.trim() || '';
    const sort = url.searchParams.get('sort') === 'word_count' ? 'word_count' : 'name';
    const limit = Math.max(1, Math.min(100, parseInt(url.searchParams.get('limit') || '50', 10)));
    const offset = Math.max(0, parseInt(url.searchParams.get('offset') || '0', 10));

    // Build Supabase query
    let query = supabase
      .from('agencies')
      .select('name, word_count, sub_agencies, cfr_references, agency_corrections(count)', { count: 'exact' })
      .neq('word_count', 0);

    if (search) {
      query = query.ilike('name', `%${search}%`);
    }

    query = query.order(sort, { ascending: sort === 'name' });
    query = query.range(offset, offset + limit - 1);

    // Execute query
    const { data: agencies, error, count } = await query;

    if (error) {
      console.error('Supabase query error:', error);
      throw new Error(error.message);
    }

    // Transform correction_count
    const formattedAgencies = agencies.map(agency => ({
      ...agency,
      correction_count: agency.agency_corrections?.correction_count || 0
    }));

    return new Response(
      JSON.stringify({ agencies: formattedAgencies, total: count || 0, limit, offset }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  } catch (error) {
    console.error('Error fetching agencies:', error);
    return new Response(
      JSON.stringify({ error: 'Failed to fetch agencies', details: error.message }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};