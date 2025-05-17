<script lang="ts">
  import { onMount } from 'svelte';
  import type { Agency, Correction } from '$lib/types';

  let agencies: Agency[] = [];
  let corrections: Correction[] = [];
  let totalAgencies = 0;
  let totalCorrections = 0;
  let limit = 15;
  let offset = 0;
  let search = '';
  let sort = 'name';
  let selectedAgency: string | null = null;
  let error: string | null = null;
  let showModal = false;

  async function fetchAgencies() {
    try {
      const params = new URLSearchParams({
        search,
        sort,
        limit: limit.toString(),
        offset: offset.toString()
      });
      const response = await fetch(`/api/agencies?${params}`);
      if (!response.ok) throw new Error('Failed to fetch agencies');
      const data = await response.json();
      agencies = data.agencies;
      totalAgencies = data.total;
      error = null;
    } catch (err) {
      error = err.message;
    }
  }

  async function fetchCorrections(agencyName: string | null) {
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: '0' // Reset offset for corrections
      });
      if (agencyName) params.set('agency_name', agencyName);
      const response = await fetch(`/api/corrections?${params}`);
      if (!response.ok) throw new Error('Failed to fetch corrections');
      const data = await response.json();
      corrections = data.corrections;
      totalCorrections = data.total;
      error = null;
    } catch (err) {
      error = err.message;
    }
  }

  onMount(fetchAgencies);

  function handleSearch(event: Event) {
    search = (event.target as HTMLInputElement).value;
    offset = 0;
    fetchAgencies();
  }

  function handleSort(event: Event) {
    sort = (event.target as HTMLSelectElement).value;
    fetchAgencies();
  }

  function nextPage() {
    if (offset + limit < totalAgencies) {
      offset += limit;
      fetchAgencies();
    }
  }

  function prevPage() {
    if (offset > 0) {
      offset -= limit;
      fetchAgencies();
    }
  }

  function selectAgency(agencyName: string) {
    selectedAgency = agencyName;
    fetchCorrections(agencyName);
    showModal = true;
  }
  function closeModal() {
    showModal = false;
  }
</script>

<div class="container mx-auto p-4">
  <h1 class="text-4xl font-extrabold mb-8 text-gray-800 tracking-tight flex items-center gap-2">
    eCFR Agencies
  </h1>

  <div class="mb-6 flex flex-col sm:flex-row gap-4 items-center">
    <div class="relative w-full sm:w-1/2">
      <input
        type="text"
        placeholder="Search agencies..."
        value={search}
        on:input={handleSearch}
        class="border border-gray-300 rounded-lg p-3 pl-10 w-full focus:ring-2 focus:ring-blue-400 focus:outline-none shadow-sm transition"
      />
      <svg class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 105 11a6 6 0 0012 0z" /></svg>
    </div>
    <select on:change={handleSort} class="border border-gray-300 rounded-lg p-3 w-full sm:w-auto focus:ring-2 focus:ring-blue-400 focus:outline-none shadow-sm transition">
      <option value="name" selected={sort === 'name'}>Sort by Name</option>
      <option value="word_count" selected={sort === 'word_count'}>Sort by Word Count</option>
    </select>
  </div>

  {#if error}
    <p class="text-red-500 text-lg font-semibold">{error}</p>
  {:else if agencies.length === 0}
    <div class="flex justify-center items-center h-32">
      <svg class="animate-spin h-8 w-8 text-blue-500 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
      <span class="text-gray-500">Loading...</span>
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each agencies as agency}
        <div class="bg-white border border-gray-200 rounded-2xl p-6 shadow-lg hover:shadow-2xl transition group cursor-pointer relative overflow-hidden flex flex-col justify-between min-h-64 w-full">
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-xl font-bold text-gray-800 group-hover:text-blue-600 transition">{agency.name}</h2>
            <span class="bg-blue-100 text-blue-700 text-xs font-semibold px-2 py-1 rounded-full">{agency.short_name || 'N/A'}</span>
          </div>
          <p class="text-gray-500 text-sm mb-1">Slug: <span class="font-mono">{agency.slug || 'N/A'}</span></p>
          <div class="flex flex-wrap gap-2 my-2">
            <span class="bg-green-100 text-green-700 text-xs font-medium px-2 py-1 rounded">Sub-agencies: {agency.sub_agencies}</span>
            <span class="bg-purple-100 text-purple-700 text-xs font-medium px-2 py-1 rounded">Word Count: {agency.word_count.toLocaleString()}</span>
          </div>
          <div class="text-gray-400 text-xs truncate mb-2">CFR References: {JSON.stringify(agency.cfr_references)}</div>
          <button
            on:click={() => selectAgency(agency.name)}
            class="mt-2 w-full py-2 bg-blue-500 text-white rounded-lg font-semibold shadow hover:bg-blue-600 transition"
          >
            View Corrections
          </button>
        </div>
      {/each}
    </div>

    <div class="mt-6 flex flex-col sm:flex-row justify-between items-center gap-4">
      <button
        on:click={prevPage}
        disabled={offset === 0}
        class="px-5 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg font-semibold text-gray-700 disabled:opacity-50 transition"
      >
        Previous
      </button>
      <span class="text-gray-600">Page {Math.floor(offset / limit) + 1} of {Math.ceil(totalAgencies / limit)}</span>
      <button
        on:click={nextPage}
        disabled={offset + limit >= totalAgencies}
        class="px-5 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg font-semibold text-gray-700 disabled:opacity-50 transition"
      >
        Next
      </button>
    </div>

    {#if showModal && selectedAgency}
      <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40 px-2">
        <div class="bg-white border border-blue-100 rounded-2xl p-4 sm:p-6 shadow-2xl w-full max-w-2xl relative animate-fade-in max-h-[90vh] overflow-y-auto">
          <button class="absolute top-2 right-2 sm:top-3 sm:right-3 text-gray-400 hover:text-blue-500 text-2xl font-bold" on:click={closeModal} aria-label="Close">&times;</button>
          <div class="flex flex-col sm:flex-row items-start sm:items-center gap-2 mb-4">
            <h2 class="text-xl sm:text-2xl font-bold text-blue-700 break-words">Corrections for {selectedAgency}</h2>
          </div>
          {#if corrections.length === 0}
            <p class="text-gray-500">No corrections available.</p>
          {:else}
            <ul class="list-disc pl-5 space-y-2">
              {#each corrections as correction}
                <li class="text-gray-700 bg-gray-50 rounded-lg p-3 shadow-sm">
                  <span class="font-semibold text-blue-700">Title {correction.title}</span>: {correction.corrective_action}
                  <span class="block text-xs text-gray-500 mt-1">Corrected: {correction.error_corrected || 'N/A'} | Occurred: {correction.error_occurred || 'N/A'} | FR Citation: {correction.fr_citation || 'N/A'}</span>
                </li>
              {/each}
            </ul>
          {/if}
        </div>
      </div>
    {/if}
  {/if}
</div>