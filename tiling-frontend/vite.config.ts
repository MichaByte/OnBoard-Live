import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { viteSingleFile } from 'vite-plugin-singlefile';

export default defineConfig(({ command }) => ({
	plugins: [
		svelte({
			/* plugin options */
		}),
		command === 'build' &&
			viteSingleFile({
				removeViteModuleLoader: true
			})
	],
	build: {
		minify: true
	}
}));
