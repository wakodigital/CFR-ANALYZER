import type { RequestHandler } from '@sveltejs/kit';
import { createClient } from '@supabase/supabase-js';
import { SUPABASE_URL, SUPABASE_ANON_KEY } from '$env/static/private';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

export const GET: RequestHandler = async () => {
  try {
    // 1. Top and Bottom 10% by Word Count
    const { data: agencies, error: agenciesError } = await supabase
      .from('agencies')
      .select('name, short_name, word_count')
      .gt('word_count', 0)
      .order('word_count', { ascending: false });

    if (agenciesError) throw new Error(`Agencies query error: ${agenciesError.message}`);

    const totalAgencies = agencies.length;
    const top10PercentCount = Math.ceil(totalAgencies * 0.1);
    const topWordCount = agencies.slice(0, top10PercentCount).slice(0, 5);
    const bottomWordCount = agencies.slice(-top10PercentCount).slice(-5);

    // 2. Word Count Statistics
    const { data: wordCountStats, error: statsError } = await supabase.rpc('word_count_stats', {
      total_agencies: totalAgencies
    });

    console.log('wordCountStats:', wordCountStats);
    if (statsError) throw new Error(`Stats RPC error: ${statsError.message}`);
    if (!wordCountStats) throw new Error('No stats returned from word_count_stats');

    // 3. Top 10% by Correction Frequency
    const { data: correctionCounts, error: correctionsError } = await supabase.rpc('correction_counts');

    console.log('correctionCounts:', correctionCounts.slice(0, 5));
    if (correctionsError) throw new Error(`Corrections RPC error: ${correctionsError.message}`);
    if (!correctionCounts) throw new Error('No correction counts returned');

    const topCorrections = correctionCounts.slice(0, top10PercentCount).slice(0, 5);

    // 4. Correction Rate per Word Count
    const { data: correctionRates, error: ratesError } = await supabase.rpc('correction_rates');

    console.log('correctionRates:', correctionRates.slice(0, 5));
    if (ratesError) throw new Error(`Correction rates RPC error: ${ratesError.message}`);
    if (!correctionRates) throw new Error('No correction rates returned');

    const topCorrectionRates = correctionRates.slice(0, top10PercentCount).slice(0, 5);

    // 5. Recent Corrections
    const { data: recentCorrections, error: recentError } = await supabase
      .from('agency_corrections')
      .select('agency_name, title, correction_id, corrective_action, error_corrected, error_occurred, fr_citation, last_modified')
      .order('error_corrected', { ascending: false })
      .limit(5);

    console.log('recentCorrections:', recentCorrections);
    if (recentError) throw new Error(`Recent corrections query error: ${recentError.message}`);

    // 6. Sub-Agency Ratio
    const { data: subAgencyRatios, error: subAgencyError } = await supabase.rpc('sub_agency_ratios');

    console.log('subAgencyRatios:', subAgencyRatios.slice(0, 5));
    if (subAgencyError) throw new Error(`Sub-agency ratios RPC error: ${subAgencyError.message}`);
    if (!subAgencyRatios) throw new Error('No sub-agency ratios returned');

    const topSubAgencyRatios = subAgencyRatios.slice(0, top10PercentCount).slice(0, 5);

    return new Response(
      JSON.stringify({
        topWordCount,
        bottomWordCount,
        wordCountStats: wordCountStats || {},
        topCorrections,
        topCorrectionRates,
        recentCorrections: recentCorrections || [],
        topSubAgencyRatios
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  } catch (error) {
    console.error('Error fetching metrics:', error);
    return new Response(
      JSON.stringify({ error: 'Failed to fetch metrics', details: error.message }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};