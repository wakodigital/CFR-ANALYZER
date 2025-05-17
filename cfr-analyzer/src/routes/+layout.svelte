<script lang="ts">
  import '../app.css';
  import Navigation from '$lib/components/Navigation.svelte';

  let { children } = $props();
</script>

<div class="flex min-h-screen">
  <Navigation />
  <main class="flex-1 p-4 pt-16 lg:ml-64 lg:pt-4">
    {@render children()}
  </main>
</div>