<script lang="ts">
  import { page } from '$app/stores';
  import { writable } from 'svelte/store';

  // Track mobile menu state
  let mobileMenuOpen = writable(false);

  // Navigation items
  const navItems = [
    { name: 'Dashboard', href: '/' },
    { name: 'Agencies', href: '/agencies' }
  ];

  // Toggle mobile menu
  function toggleMobileMenu() {
    mobileMenuOpen.update(val => !val);
  }

  // Close mobile menu when a link is clicked
  function closeMobileMenu() {
    mobileMenuOpen.set(false);
  }
</script>

<!-- Desktop Aside (hidden on mobile) -->
<aside class="hidden lg:block fixed top-0 left-0 w-64 h-screen bg-gray-800 text-white">
  <div class="p-4">
    <h2 class="text-xl font-bold">eCFR Dashboard</h2>
  </div>
  <nav>
    <ul class="space-y-2">
      {#each navItems as item}
        <li>
          <a
            href={item.href}
            class="block px-4 py-2 text-sm hover:bg-gray-700 {$page.url.pathname === item.href ? 'bg-gray-700' : ''}"
          >
            {item.name}
          </a>
        </li>
      {/each}
    </ul>
  </nav>
</aside>

<!-- Mobile Navbar (hidden on desktop) -->
<div class="lg:hidden">
  <nav class="fixed top-0 left-0 right-0 bg-gray-800 text-white z-50">
    <div class="flex items-center justify-between p-4">
      <h2 class="text-xl font-bold">eCFR Dashboard</h2>
      <button
        on:click={toggleMobileMenu}
        class="text-white focus:outline-none"
        aria-label="Toggle menu"
      >
        <svg
          class="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d={$mobileMenuOpen ? 'M6 18L18 6M6 6l12 12' : 'M4 6h16M4 12h16M4 18h16'}
          ></path>
        </svg>
      </button>
    </div>
    {#if $mobileMenuOpen}
      <ul class="bg-gray-800 space-y-2 p-4">
        {#each navItems as item}
          <li>
            <a
              href={item.href}
              on:click={closeMobileMenu}
              class="block px-4 py-2 text-sm hover:bg-gray-700 {$page.url.pathname === item.href ? 'bg-gray-700' : ''}"
            >
              {item.name}
            </a>
          </li>
        {/each}
      </ul>
    {/if}
  </nav>
</div>