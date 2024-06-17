import soundfile
import numpy as np
import re
import time
import argparse
import random
import sys
import os

"""
	指定した周波数、指定した秒数、指定した音量で指定したサンプリングレートの
	正弦波を作成し、そのデータを返す。
	エラーチェックはしていない。
"""
def _createWave(freq, sec, volume, rate):
	t = np.linspace(0, sec, int(rate * sec) + 1) # サンプルレート * 秒数分の配列を作成
	w = np.sin(2 * np.pi * freq * t) # その分だけ正弦波を生成
	
	# lengthの1%をフェードインアウトさせることでプチプチノイズを消す
	fi = np.linspace(0, 1, int(sec / 100 * rate)) # かけ合わせるフェードアウト用配列
	fo = np.linspace(1, 0, int(sec / 100 * rate)) # かけ合わせるフェードアウト用配列
	w[-int(sec / 100 * rate)-1:-1] = w[-int(sec / 100 * rate)-1:-1] * fo
	w[0:int(sec / 100 * rate)] = w[0:int(sec / 100 * rate)] * fi
	return (w * volume).astype(np.float32) # 16ビット型のデータとして返す

"""
	簡易MMLパーサー
	MMLを読み込み、解析してそれを正弦波で鳴らした際のndarrayを返す
	MMLとして不適切な場合はその設定はスキップされる。その結果空のndarrayになる可能性もある
	
	同時に再生することも可能だが（チャンネル指定）、その場合はボリュームを調整しないと
	クリッピングするので注意。自動でクリッピングをどうにかしてくれる機能は取り入れていない。
	
	<Initial Parameter>
	ノートの途中に記すとそこから再設定される
	O3 = 開始オクターブを3にする。国際表記
	L4 = 省略した際の音符をこの長さにする。1,2,4,8,16,32…と2の累乗から選べる
	[] = この中身を繰り返す。]の後に数字を書くとその回数だけ繰り返す。省略すると1回だけになるので意味がない
	T120 = テンポ（BPM）を指定する。自然数対応。
	V0 = ボリューム。0～100の間で指定する。100がMAX。0は無音。
	
	<Note Parameter>
	※12音階平均律とし、A3 = 440Hzとしている。
	
	CDEFGAB = ドレミファソラシ
	+ = ♯
	- = ♭
	< = 次の音階を1オクターブ上げる
	> = 次の音階を1オクターブ下げる（これらは重ねることで、一気に数オクターブ上げることができる）
	R = 休符
	CDEFGABRの後に数字を書くと、その長さで発音する。Ｌ参照。
	
	<例：蛙の歌＞
	T120L4O3CDEFEDCREFGAGFERCRCRCRCRC8C8D8D8E8E8F8F8EDCR
	
	なおスペースを使って見やすいようにしてもかまわない（スペースは全て切り詰められる）
	
	<複数チャンネルを使用したい場合>
	|で区切ると、区切られた中身を1つのチャンネルとみなして、同時発音を可能とする。
	|で区切った中身は個別の設定が再度適用されるので、別の設定を行うことも可能。
	
	例：T120L4O3CDEFEDCREFGAGFERCRCRCRCRC8C8D8D8E8E8F8F8EDCRR1|T120L4O3R1R1CDEFEDCREFGAGFERCRCRCRCRC8C8D8D8E8E8F8F8EDCR
	これで蛙の歌の輪唱が行える

	現在、複数チャンネルが別々の長さを持っている場合は強制的に一番長い演奏に揃えられるが、
	その場合に短いほうは再度先頭から再生してしまうので注意。
	できるだけチャンネル長さは揃えること。

"""
def parseMML(mml, rate=44100):
	FREQS_3 = {
		"C": 261.626,
		"C+": 277.183,
		"D-": 277.183,
		"D": 293.665,
		"D+": 311.127,
		"E-": 311.127,
		"E": 329.628,
		"F": 349.228,
		"F+": 369.994,
		"G-": 369.994,
		"G": 391.995,
		"G+": 415.305,
		"A-": 415.305,
		"A": 440.000,
		"A+": 466.164,
		"B-": 466.164,
		"B": 493.883,
		"R": 0.000,
	} # 周波数（O3） オクターブが1上がるごとに2倍する
	
	
	# スペースを取り除く
	mml = mml.replace(" ", "")
	
	# チャンネルを分解してチャンネルごとに繰り返す
	datas = []
	for channel in mml.split("|"):
		#print(f"------------- channel {len(datas)+1} begin -------------")
		# 繰り返しを展開する（入れ子対応）
		while True:
			t = re.sub(r"\[(.+?)\](\d*)", lambda m: m.group(1) * int(m.group(2) if m.group(2) != "" else 1), channel)
			if t == channel:
				channel = t
				break;
			channel = t
		
		#print(f"channel{len(datas)+1} | repeat open: {channel}")
		# 解析を開始するため、該当する項目を全て取る
		data = np.empty(0)
		BPM = 120 # デフォルトテンポ
		OCTAVE = 3 # デフォルトオクターブ
		LENGTH = 4 # デフォルトの長さ
		VOLUME = 50 # デフォルトのボリューム（うるさいのでデフォはゲイン0.5）
		for note in re.finditer(r"(?:((?:C|D|E|F|G|A|B|R|\<|\>)[+-]?)(\d*)|(?:([OLTV])(\d+)))", channel):
			# 音階、長さ、設定、数値
			if note.group(1) is None:
				dec = int(note.group(4)) # 数値として解釈してもらうため
				# 設定項目を変更する
				if note.group(3) == "T" and dec > 0:
					# BPMを変更
					BPM = dec
				elif note.group(3) == "O":
					# オクターブ変更
					OCTAVE = dec
				elif note.group(3) == "V" and (0 <= dec <= 100):
					# ボリューム変更
					VOLUME = dec
				elif note.group(3) == "L" and (dec & (dec - 1)) == 0:
					# 長さ変更
					LENGTH = dec
					#print("change to " + str(dec))
				continue # 次の要素を読み取る
			
			# オクターブ変更ショートカットの場合
			if note.group(1) == "<":
				OCTAVE += 1
				continue
			elif note.group(1) == ">":
				OCTAVE -= 1
				continue
			
			
			# 音階の場合
			# 長さを確定
			l = LENGTH
			if note.group(2) != "" and (int(note.group(2)) & (int(note.group(2)) - 1) == 0):
				# 有効な長さが指定されている場合
				l = int(note.group(2))
			
			# 周波数を確定
			f = FREQS_3[note.group(1)] * (2 ** (OCTAVE - 3)) # 周波数（O3基準で累乗倍）
			
			# テンポと長さから発音秒数を確定
			b4 = 1 / (BPM / 60) # 四分音符1回あたりの発音秒数を指定
			b = b4 * (4 / l) # 今回発音する長さは現在の長さで4を割れば出てくる
			
			# 音量を正規化
			v = VOLUME / 100
			
			# 波形を作成
			#print(f"Create WAVE[{note.group(1)}]: f={f}, b={b}, v={v}, r={rate}")
			d = _createWave(f, b, v, rate)
			data = np.r_[data, d[0:-2]] # なぜかノイズ入るので1個消す
			
		# データ完成したので返す
		datas.append(data)
		
	# チャンネルごとの波形データを足し合わせる
	# 一致しないと足し合わせないので一番長いものに合わせる
	res = np.empty(max([d.shape[0] for d in datas]))
	for data in datas:
		res = res + np.resize(data, (max([d.shape[0] for d in datas]),))
	return res
	

# そのまんま呼ばれたら
if __name__ == "__main__":
	# args解析
	parser = argparse.ArgumentParser(description="Create WAV File from Original MML.")
	parser.add_argument("mml", help="The MML what you want to convert")
	parser.add_argument("-s", "--rate", help="Sampling Rate(Default = 44100)", default=44100, type=int)
	args = parser.parse_args()

	# カレントディレクトリ移動
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	
	# データを作成
	data = parseMML(args.mml, args.rate)

	# 空の場合は作成に失敗している
	if len(data) == 0:
		print("Data is empty.", file=sys.stderr)
		sys.exit(1)
	
	# 保存
	id = random.randbytes(8).hex()
	soundfile.write(file=f"tmp_{id}.wav", data=data, samplerate=args.rate, subtype="PCM_32")
	
	print(f"{os.getcwd()}/tmp_{id}.wav")