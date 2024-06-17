/*
 * SPDX-FileCopyrightText: syuilo and misskey-project
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { Module } from '@nestjs/common';

import { CoreModule } from '@/core/CoreModule.js';
import * as endpointsObject from './endpoint-list.js';

import * as ep___midi_kakiko from './endpoints/midi_kakiko/midi_kakiko.js';


import { GetterService } from './GetterService.js';
import { ApiLoggerService } from './ApiLoggerService.js';
import type { Provider } from '@nestjs/common';
import { KakikoService } from './endpoints/midi_kakiko/KakikoService.js';

const endpoints = Object.entries(endpointsObject);
const endpointProviders = endpoints.map(([path, endpoint]): Provider => ({ provide: `ep:${path}`, useClass: endpoint.default }));

const $midi_kakiko: Provider = { provide: 'ep:midi_kakiko', useClass: ep___midi_kakiko.default };

@Module({
	imports: [
		CoreModule,
	],
	providers: [
		GetterService,
		ApiLoggerService,
		...endpointProviders,

		$midi_kakiko,
		KakikoService,
	],
	exports: [
		...endpointProviders,

		$midi_kakiko,
	],
})
export class EndpointsModule {}
