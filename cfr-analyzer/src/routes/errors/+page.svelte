<script lang="ts">
    import { onMount } from 'svelte';
    import { writable } from 'svelte/store';
    import Toastify from 'toastify-js';
    import 'toastify-js/src/toastify.css';

    interface ErrorRow {
        id: number;
        agency_name: string;
        cfr_reference: string; // JSON string
        error_message: string;
        timestamp: string;
    }

    interface Pagination {
        page: number;
        limit: number;
        total: number;
        totalPages: number;
    }

    // Stores
    let errors = writable<ErrorRow[]>([]);
    let pagination = writable<Pagination>({ page: 1, limit: 50, total: 0, totalPages: 0 });
    let agencyFilter = writable<string>('');
    let messageFilter = writable<string>('');
    let sortKey = writable<keyof ErrorRow | string>('id');
    let sortDirection = writable<'asc' | 'desc'>('asc');
    let loading = writable<boolean>(false);

    // Parse cfr_reference JSON
    function parseCfrReference(ref: string): string {
        try {
            const parsed = JSON.parse(ref);
            const parts = [];
            if (parsed.title) parts.push(`Title ${parsed.title}`);
            if (parsed.subtitle) parts.push(`Subtitle ${parsed.subtitle}`);
            if (parsed.chapter) parts.push(`Chapter ${parsed.chapter}`);
            if (parsed.subchapter) parts.push(`Subchapter ${parsed.subchapter}`);
            if (parsed.part) parts.push(`Part ${parsed.part}`);
            if (parsed.subpart) parts.push(`Subpart ${parsed.subpart}`);
            if (parsed.section) parts.push(`Section ${parsed.section}`);
            return parts.join(', ');
        } catch {
            return ref; // Return raw string if parsing fails
        }
    }

    // Fetch errors
    async function fetchErrors(page: number = 1) {
        loading.set(true);
        try {
            const params = new URLSearchParams({
                page: page.toString(),
                limit: $pagination.limit.toString(),
                agency_name: $agencyFilter,
                error_message: $messageFilter,
                sort: $sortKey,
                direction: $sortDirection
            });
            const response = await fetch(`/api/errors?${params}`);
            if (!response.ok) throw new Error('Failed to fetch errors');
            const { data, pagination: newPagination } = await response.json();
            errors.set(data);
            pagination.set(newPagination);
        } catch (error) {
            Toastify({
                text: 'Failed to load errors. Please try again.',
                duration: 3000,
                gravity: 'top',
                position: 'right',
                backgroundColor: '#dc2626'
            }).showToast();
        } finally {
            loading.set(false);
        }
    }

    onMount(() => {
        fetchErrors();
    });

    // Toggle sort
    function toggleSort(key: keyof ErrorRow | string) {
        if ($sortKey === key) {
            sortDirection.set($sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            sortKey.set(key);
            sortDirection.set('asc');
        }
        fetchErrors($pagination.page);
    }

    // Change page
    function changePage(newPage: number) {
        if (newPage >= 1 && newPage <= $pagination.totalPages) {
            fetchErrors(newPage);
        }
    }

    // Debounce filters
    let filterTimeout: NodeJS.Timeout;
    $: {
        clearTimeout(filterTimeout);
        filterTimeout = setTimeout(() => {
            fetchErrors(1);
        }, 300);
    }
</script>

<div class="container mx-auto p-4">
    <h1 class="text-4xl font-extrabold mb-8 text-gray-800 tracking-tight flex items-center gap-2">
        CFR Reference Errors
    </h1>

    <!-- Loading state -->
    {#if $loading}
        <div class="space-y-4">
            {#each Array(5) as _}
                <div class="animate-pulse bg-gray-200 h-12 rounded-lg"></div>
            {/each}
        </div>
    {:else}
        <!-- Errors table -->
        <div class="overflow-x-auto rounded-2xl shadow-lg bg-white">
            <table class="w-full border-collapse">
                <thead>
                    <tr class="bg-gray-200">
                        <th
                            class="p-4 text-left cursor-pointer text-lg font-semibold text-gray-700"
                            on:click={() => toggleSort('id')}
                            role="columnheader"
                            aria-sort={$sortKey === 'id' ? $sortDirection : 'none'}
                        >
                            ID
                            {#if $sortKey === 'id'}
                                <span class="ml-1">{$sortDirection === 'asc' ? '↑' : '↓'}</span>
                            {/if}
                        </th>
                        <th
                            class="p-4 text-left cursor-pointer text-lg font-semibold text-gray-700"
                            on:click={() => toggleSort('agency_name')}
                            role="columnheader"
                            aria-sort={$sortKey === 'agency_name' ? $sortDirection : 'none'}
                        >
                            Agency Name
                            {#if $sortKey === 'agency_name'}
                                <span class="ml-1">{$sortDirection === 'asc' ? '↑' : '↓'}</span>
                            {/if}
                        </th>
                        <th
                            class="p-4 text-left cursor-pointer text-lg font-semibold text-gray-700"
                            on:click={() => toggleSort('cfr_reference')}
                            role="columnheader"
                            aria-sort={$sortKey === 'cfr_reference' ? $sortDirection : 'none'}
                        >
                            CFR Reference
                            {#if $sortKey === 'cfr_reference'}
                                <span class="ml-1">{$sortDirection === 'asc' ? '↑' : '↓'}</span>
                            {/if}
                        </th>
                        <th
                            class="p-4 text-left cursor-pointer text-lg font-semibold text-gray-700"
                            on:click={() => toggleSort('error_message')}
                            role="columnheader"
                            aria-sort={$sortKey === 'error_message' ? $sortDirection : 'none'}
                        >
                            Error Message
                            {#if $sortKey === 'error_message'}
                                <span class="ml-1">{$sortDirection === 'asc' ? '↑' : '↓'}</span>
                            {/if}
                        </th>
                        <th
                            class="p-4 text-left cursor-pointer text-lg font-semibold text-gray-700"
                            on:click={() => toggleSort('timestamp')}
                            role="columnheader"
                            aria-sort={$sortKey === 'timestamp' ? $sortDirection : 'none'}
                        >
                            Timestamp
                            {#if $sortKey === 'timestamp'}
                                <span class="ml-1">{$sortDirection === 'asc' ? '↑' : '↓'}</span>
                            {/if}
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {#each $errors as error}
                        <tr class="border-b border-gray-200 hover:bg-gray-50 transition">
                            <td class="p-4">{error.id}</td>
                            <td class="p-4 font-semibold text-blue-700">{error.agency_name}</td>
                            <td class="p-4">{parseCfrReference(error.cfr_reference)}</td>
                            <td class="p-4">{error.error_message}</td>
                            <td class="p-4">{error.timestamp}</td>
                        </tr>
                    {:else}
                        <tr>
                            <td colspan="5" class="p-4 text-center text-gray-500">No errors found</td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>

        <!-- Pagination -->
        {#if $pagination.totalPages > 1}
            <div class="mt-6 flex justify-center gap-2">
                <button
                    class="px-4 py-2 bg-gray-200 rounded-lg disabled:opacity-50"
                    disabled={$pagination.page === 1}
                    on:click={() => changePage($pagination.page - 1)}
                    aria-label="Previous page"
                >
                    Previous
                </button>
                {#each Array($pagination.totalPages) as _, i}
                    <button
                        class="px-4 py-2 rounded-lg {i + 1 === $pagination.page ? 'bg-blue-500 text-white' : 'bg-gray-200'}"
                        on:click={() => changePage(i + 1)}
                        aria-label={`Page ${i + 1}`}
                    >
                        {i + 1}
                    </button>
                {/each}
                <button
                    class="px-4 py-2 bg-gray-200 rounded-lg disabled:opacity-50"
                    disabled={$pagination.page === $pagination.totalPages}
                    on:click={() => changePage($pagination.page + 1)}
                    aria-label="Next page"
                >
                    Next
                </button>
            </div>
        {/if}
    {/if}
</div>

<style>
    /* Ensure table is responsive on small screens */
    @media (max-width: 640px) {
        table {
            display: block;
            overflow-x: auto;
            white-space: nowrap;
        }
    }
</style>