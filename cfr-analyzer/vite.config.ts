import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	optimizeDeps: {
		exclude: ['clsx', 'devalue', 'highcharts', 'svelte-highcharts']
	},
	ssr: {
		noExternal: ['highcharts', 'svelte-highcharts']
	}
});
