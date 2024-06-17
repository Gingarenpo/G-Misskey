
import { Endpoint } from '@/server/api/endpoint-base.js';
import { ApiError } from '../../error.js';
import { Injectable } from '@nestjs/common';

import { KakikoService } from './KakikoService.js';
import { DriveFileEntityService } from '@/core/entities/DriveFileEntityService.js';
import { DriveService } from '@/core/DriveService.js';

// 多分APIの情報系
export const meta = {
	tags: ['midi_kakiko'],

	requireCredential: false,

	res: {
		type: 'object',
		optional: false, nullable: false,
		ref: 'Note',
	},

	errors: {
		syntaxError: {
			message: 'MML Syntax Error.',
			code: 'MIDI_KAKIKO_ERROR',
			id: 'MIDI_KAKIKO_ERROR',
		},
	},

	kind: 'write:drive',

} as const;

// 渡すパラメータ
export const paramDef = {
	type: 'object',
	properties: {
		mml: { type: 'string' },
	},
	required: ['mml'],
} as const;

@Injectable()
export default class extends Endpoint<typeof meta, typeof paramDef> { // eslint-disable-line import/no-default-export
	constructor(
		private kakiko: KakikoService, 
		private df: DriveFileEntityService,
		private ds: DriveService
	) {
		super(meta, paramDef, async (ps, me) => {
			let file = this.kakiko.exec(ps.mml);
			// nullの場合落ちている
			if (file == null) {
				throw new ApiError(meta.errors.syntaxError);
			}

			let date = new Date();


			// このファイルをアップロードする
			// kakikoディレクトリにアップロードする。作ってくれないので
			// このディレクトリはUIで作ってちょ
			const driveFile = await this.ds.addFile({
				user: me,
				path: file,
				name: `${date.getFullYear()}-${("00"+(date.getMonth()+1)).slice(-2)}-${("00"+(date.getDate())).slice(-2)}_${("00"+(date.getHours())).slice(-2)}_${("00"+(date.getMinutes())).slice(-2)}_${("00"+(date.getSeconds())).slice(-2)}`,
				comment: "KAKIKO | MML:" + ps.mml,
				folderId: null,
				force: false,
			});
			return await this.df.pack(driveFile, { self: true });
		});
	}
}

export function a() {
	return 5;
}