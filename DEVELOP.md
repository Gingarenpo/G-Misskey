# 開発備忘録
Misskeyの改造を行うにあたり、どの辺のファイルをどういじればいいのかをまとめています（2025年4月10日時点での情報なので古いかも）

## バックエンド関連
APIの追加、機能面の追加を実現したい場合はこっち。`package/backend/src`の中身を基本的にいじっていく。以降、パスが表示された場合はここからの相対ルート。

ちなみにバックエンドはNest.jsのDIを使っている模様。まあなんのこっちゃだけど調べて理解できる人は調べよう。

### エンドポイントを追加したい
エンドポイントの管理は、`server/api/endpoint-list.ts`で行う。昔は`server/api/endpoints.ts`で管理していたらしいがモジュール化に伴い多分変更になったんだと思う。

ここにexportという形で書いていくと自動で反映されるよう。
```Typescript
export * as 'エンドポイント' from 'エンドポイントの定義が行われているJSファイル';
```
なぜかjs。コンパイル後だから？

なおもちろんのことながら、実際にエンドポイントを定義しているTSファイルを作らないと意味がない。多分どこにおいてもいいんだろうが、見た感じでは`server/api/endpoints`ディレクトリにいろいろまとまっている印象。ここにディレクトリを掘るなどして作っておけばよろし。

### エンドポイントの処理を定義したい
TSファイルを作成したら、`IEndpointMeta`インターフェースを実装したクラスを作成する。なんだがベースの抽象クラスがいるっぽいので、`server/api/endpoint-base.js`をインポートしてEndpointクラスを継承する。

```Typescript
import { Endpoint } from '@/server/api/endpoint-base.js';
import { Injectable } from '@nestjs/common';

@Injectable()
export default class extends Endpoint<typeof meta, typeof paramDef> {
    constructor(
        // 必要なServiceをインスタンス列挙
        // 例
        private kakiko: KakikoService,
    ) {
        super(meta, paramDef, async (params, user, token, file, cleanup, ip, headers) => {
            // エンドポイント内で実行する処理
            // 最終的に返すのはたいていの場合Serviceのメソッド実行結果
        })
    }
}
```

#### Serviceってなあに？
ググれ。要は、処理ロジックの根本となる部分。こんな感じで作る

```Typescript
import { Injectable } from '@nestjs/common';

@Injectable()
export class SampleService {
    // 好きなメソッドを定義する
    exec(param1, param2, ...): string|null {
        // なんやかんや
        return "ああああ";
    }
}
```

これを適当なところに置いておく。Nest.jsのディレクトリ構成に合っていないから自力で探そう。

#### それぞれの引数わかんないんだけど

Endpoint抽象クラスはコンストラクタとしてmeta, paramDef, callbackを受け取る。metaとparamDefはよくわかっていないのでこの辺のコピペ。

```Typescript
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
```

コールバック関数が実際にAPI叩かれると実行される。asyncで実行されるので戻り値はPromise。つまりを言えばawait中で使えるよ、って感じ。

- **params** : 知らん。`SchemaType<Ps>`という型定義されている
- **user** : APIを叩いた人のデータが入る。ユーザー名とか入っている。apiだと`i`で取れるやつ。
- **token** : アクセストークンが取れるらしい
- **file** : アップロードされたファイル？
- **cleanup** : ファイルのクリーンアップを行う関数？