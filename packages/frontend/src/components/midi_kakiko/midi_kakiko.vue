<!--
SPDX-FileCopyrightText: syuilo and misskey-project
SPDX-License-Identifier: AGPL-3.0-only
-->

<template>
	<div class="midi_kakiko" :class="$style.root">
		<h2>MIDI カキコ</h2>
		<p>（一部独自の）MML形式で記載することで、音楽を生成してドライブに追加します。対応は正弦波のみです</p>
		<textarea :class="$style.form" :placeholder=placeholder></textarea>
		<button :class="$style.button">生成</button>
	</div>
</template>
	
<script lang="ts" setup>
import { } from 'vue';
</script>
	
<style lang="scss" module>
	.root {
		background-color: var(--panel);
		border-radius: var(--X4);
		padding: 1rem;
		margin: 1rem 0;
		border-radius: 8px;
		font-family: inherit;
	}

	.form {
		background: transparent;
		border: 1px solid var(--X4);
		width: 100%;
		height: 4rem;
		border-radius: 4px;
		font-family: inherit;
	}

	.button {
		background: linear-gradient(90deg, var(--buttonGradateA), var(--buttonGradateB));
		color: var(--fgOnAccent);
		padding: 0.25rem 2rem;
		border-radius: 8px;
		outline: none;
		border: 1px solid var(--X4);
		font-family: inherit;
	}
</style>
	