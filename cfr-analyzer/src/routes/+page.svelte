<script lang="ts">
  import { onMount } from 'svelte';
  import type { Agency, WordCountStats, CorrectionMetric, CorrectionRate, Correction, SubAgencyRatio } from '$lib/types';

  interface Metrics {
    topWordCount: Agency[];
    bottomWordCount: Agency[];
    wordCountStats: WordCountStats;
    topCorrections: CorrectionMetric[];
    topCorrectionRates: CorrectionRate[];
    recentCorrections: Correction[];
    topSubAgencyRatios: SubAgencyRatio[];
  }

  let metrics: Metrics | null = null;
  let error: string | null = null;

  onMount(async () => {
    try {
      const response = await fetch('/api/metrics');
      if (!response.ok) throw new Error('Failed to fetch metrics');
      metrics = await response.json();
    } catch (err) {
      error = err;
    }
  });
</script>

<div class="container mx-auto p-4">
  <h1 class="text-4xl font-extrabold mb-8 text-gray-800 tracking-tight flex items-center gap-2">
    eCFR Dashboard
  </h1>

  {#if error}
    <p class="text-red-500 text-lg font-semibold">{error}</p>
  {:else if !metrics}
    <div class="flex justify-center items-center h-32">
      <svg class="animate-spin h-8 w-8 text-blue-500 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
      <span class="text-gray-500">Loading metrics...</span>
    </div>
  {:else}
    <!-- Word Count Statistics -->
    {#if metrics}
    <div class="mb-8">
      <h2 class="text-2xl font-semibold mb-4 text-blue-700">Word Count Statistics</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="border border-gray-200 rounded-2xl p-6 shadow-lg bg-white">
          <p class="text-gray-600">Total Words</p>
          <p class="text-2xl font-bold text-blue-700">{metrics.wordCountStats.total_words.toLocaleString()}</p>
        </div>
        <div class="border border-gray-200 rounded-2xl p-6 shadow-lg bg-white">
          <p class="text-gray-600">Median Words</p>
          <p class="text-2xl font-bold text-blue-700">{metrics.wordCountStats.median_words.toLocaleString()}</p>
        </div>
        <div class="border border-gray-200 rounded-2xl p-6 shadow-lg bg-white">
          <p class="text-gray-600">Mean Words</p>
          <p class="text-2xl font-bold text-blue-700">{Math.round(metrics.wordCountStats.mean_words).toLocaleString()}</p>
        </div>
        <div class="border border-gray-200 rounded-2xl p-6 shadow-lg bg-white">
          <p class="text-gray-600">Standard Deviation</p>
          <p class="text-2xl font-bold text-blue-700">{Math.round(metrics.wordCountStats.std_dev).toLocaleString()}</p>
        </div>
      </div>
    </div>

    <!-- Top and Bottom Word Count -->
    <div class="mb-8">
      <h2 class="text-2xl font-semibold mb-4 text-blue-700">Word Count Extremes</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="border border-gray-200 rounded-2xl p-6 shadow-lg bg-white">
          <h3 class="text-lg font-semibold mb-2 text-blue-600">Top 10% by Word Count</h3>
          <ul class="list-disc pl-5 space-y-1">
            {#each metrics.topWordCount as agency}
              <li class="text-gray-700"><span class="font-semibold text-blue-700">{agency.name}</span>: {agency.word_count.toLocaleString()} words</li>
            {/each}
          </ul>
        </div>
        <div class="border border-gray-200 rounded-2xl p-6 shadow-lg bg-white">
          <h3 class="text-lg font-semibold mb-2 text-blue-600">Bottom 10% by Word Count</h3>
          <ul class="list-disc pl-5 space-y-1">
            {#each metrics.bottomWordCount as agency}
              <li class="text-gray-700"><span class="font-semibold text-blue-700">{agency.name}</span>: {agency.word_count.toLocaleString()} words</li>
            {/each}
          </ul>
        </div>
      </div>
    </div>

    <!-- Top Correction Frequency -->
    <div class="mb-8">
      <h2 class="text-2xl font-semibold mb-4 text-blue-700">Top 10% by Correction Frequency</h2>
      <div class="border border-gray-200 rounded-2xl p-6 shadow-lg bg-white">
        <ul class="list-disc pl-5 space-y-1">
          {#each metrics.topCorrections as agency}
            <li class="text-gray-700"><span class="font-semibold text-blue-700">{agency.name}</span>: {agency.correction_count.toLocaleString()} corrections</li>
          {/each}
        </ul>
      </div>
    </div>

    <!-- Top Correction Rate -->
    <div class="mb-8">
      <h2 class="text-2xl font-semibold mb-4 text-blue-700">Top 10% by Correction Rate</h2>
      <div class="border border-gray-200 rounded-2xl p-6 shadow-lg bg-white">
        <ul class="list-disc pl-5 space-y-1">
          {#each metrics.topCorrectionRates as agency}
            <li class="text-gray-700"><span class="font-semibold text-blue-700">{agency.name}</span>: {agency.corrections_per_1000_words.toFixed(2)} corrections/1,000 words</li>
          {/each}
        </ul>
      </div>
    </div>

    <!-- Recent Corrections -->
    <div class="mb-8">
      <h2 class="text-2xl font-semibold mb-4 text-blue-700">Recent Corrections</h2>
      <div class="border border-gray-200 rounded-2xl p-6 shadow-lg bg-white">
        <ul class="list-disc pl-5 space-y-1">
          {#each metrics.recentCorrections as correction}
            <li class="text-gray-700">
              <span class="font-semibold text-blue-700">{correction.agency_name}</span> (Title {correction.title}): {correction.corrective_action} (Corrected: {correction.error_corrected})
            </li>
          {/each}
        </ul>
      </div>
    </div>

    <!-- Sub-Agency Ratio -->
    <div class="mb-8">
      <h2 class="text-2xl font-semibold mb-4 text-blue-700">Top 10% by Sub-Agency Ratio</h2>
      <div class="border border-gray-200 rounded-2xl p-6 shadow-lg bg-white">
        <ul class="list-disc pl-5 space-y-1">
          {#each metrics.topSubAgencyRatios as agency}
            <li class="text-gray-700"><span class="font-semibold text-blue-700">{agency.name}</span>: {agency.sub_agencies_per_1000_words.toFixed(2)} sub-agencies/1,000 words</li>
          {/each}
        </ul>
      </div>
    </div>
    {/if}
  {/if}
</div>