# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import time
# この中の変数は処理終了後に消えない/////////////////////////////////////////////////
if 'count_loop' not in sc.sticky:
    sc.sticky['count_loop'] = 0# 何個目の壁なのか示す数字
if 'dict_distance' not in sc.sticky:
    sc.sticky['dict_distance'] = {}# 下記
if 'dict_combi' not in sc.sticky:
    sc.sticky['dict_combi'] = {}# 壁に関する情報を格納する辞書
if 'count_error' not in sc.sticky:
    sc.sticky['count_error'] = 0# 
if 'list_usedindex' not in sc.sticky:
    sc.sticky['list_usedindex'] = []# 使用済みのインデックス
if 'list_history' not in sc.sticky:
    sc.sticky['list_history'] = []# 操作の記録

# 初回だけ距離計算をする/////////////////////////////////////////////////
# 辞書(キー:曲線のインデックス 値:距離の近いものを順番に並べたリスト)を生成する
def Findclosestpt(crvs):
    dict_dist = {}
    list_midpt = [rs.CurveMidPoint(crv) for crv in crvs]
    count = 0
    while count != len(crvs):
        list_distance = [int(rs.Distance(list_midpt[count], i)) for i in list_midpt]
        list_sorted = zip(list_distance, range(len(crvs)))
        list_sorted.sort()
        list_distance, list_sortindex = zip(*list_sorted)#並べ替えたインデックスを取り出す
        dict_dist[count] = list_sortindex
        count += 1
    return dict_dist

start = time.time()
if sc.sticky['count_loop'] == 0:# ここで初回かどうか判断
    print("Start Calculate")
    sc.sticky['dict_distance'] = Findclosestpt(curve)
    print("End Calculate")

else:
    print("Skip Calculate")
end = time.time() - start
print("calculatetime = " + str(end))

# ２つのインデックスを求める/////////////////////////////////////////////////
for remain in range(len(curve)):
    if remain in sc.sticky['list_usedindex']:
        pass
    else:
        index_o = remain#２つのうちの片方のインデックス
        break
list_loft_x = sc.sticky['dict_distance'].values()[index_o]
index_x = list_loft_x[1 + sc.sticky['count_error']]#もう片方のインデックス

# 辞書に登録する情報を作成/////////////////////////////////////////////////
class Info():
	def __init__(self, crvs, ind_o, ind_x, num_loop, mode, thick, height):#コンストラクタ
		self.crvs = crvs
		self.ind_o = ind_o
		self.ind_x = ind_x
		self.num_loop = num_loop
		self.mode = mode
		self.thick = thick
		self.height = height

	def get_wall(self):# 壁のインデックスを返却
		return self.num_loop
	def get_o(self):# 曲線のインデックス１を返却
		return self.ind_o
	def get_x(self):# 曲線のインデックス2を返却
		return self.ind_x
	def get_thick(self):# 壁の厚みを返却
		return self.thick
	def get_height(self):# 壁の高さを返却
		return self.height
	def get_adjust(self):# 曲線の長さ調整の仕方を返却
		if self.mode == "extend":# 長い方に揃える
			if rs.CurveLength(self.crvs[self.ind_o]) >= rs.CurveLength(self.crvs[self.ind_x]):
				pattern = 1
			else:
				pattern = 2
		else:# 短い方に揃える
			if rs.CurveLength(self.crvs[self.ind_o]) >= rs.CurveLength(self.crvs[self.ind_x]):
				pattern = 3
			else:
				pattern = 4
		return pattern
data = Info(curve, index_o, index_x, sc.sticky["count_loop"], mode, thickness, height)
sc.sticky["dict_combi"][data.get_wall()] = (data.get_o(), data.get_x(), data.get_adjust(), data.get_thick(), data.get_height(),)

# プレビューを作成/////////////////////////////////////////////////
def Previewwall(dict, index, crvs, zoommode):# 壁を作る
	# get_adjustの中身で処理を決める
	if dict[index][2] == 1:
		A = crvs[dict[index][0]]
		B = rs.OffsetCurve(crvs[dict[index][0]], rs.CurveMidPoint(crvs[dict[index][1]]), dict[index][3])
	elif dict[index][2] == 2:
		A = rs.OffsetCurve(crvs[dict[index][1]], rs.CurveMidPoint(crvs[dict[index][0]]), dict[index][3])
		B = crvs[dict[index][1]]
	elif dict[index][2] == 3:
		A = rs.OffsetCurve(crvs[dict[index][1]], rs.CurveMidPoint(crvs[dict[index][0]]), dict[index][3])
		B = crvs[dict[index][1]]
	elif dict[index][2] == 4:
		A = crvs[dict[index][0]]
		B = rs.OffsetCurve(crvs[dict[index][0]], rs.CurveMidPoint(crvs[dict[index][1]]), dict[index][3])

	obj_srf = rs.AddLoftSrf([A, B])
	obj_height = rs.AddLine((0,0,0), (0,0,dict[index][4]))
	obj_wall = rs.ExtrudeSurface(obj_srf, obj_height)

	if zoommode:# 壁と曲線で箱を作り、箱をズーム
		obj_zoom = rs.BoundingBox([obj_wall, crvs[dict[index][0]], crvs[dict[index][1]]])
		rs.ZoomBoundingBox(obj_zoom)

	return obj_wall

def Previewmark(crvs, dict, index):# 線の目印を作る
	pt_o = rs.DivideCurve(crvs[dict[index][0]], 10)
	pt_x = rs.DivideCurve(crvs[dict[index][1]], 10)
	mark_o = [rs.AddCircle(cen, mark) for cen in pt_o]
	mark_x1 = [rs.AddLine((cen[0] - mark,cen[1],cen[2]), (cen[0] + mark,cen[1],cen[2])) for cen in pt_x]
	mark_x2 = [rs.AddLine((cen[0],cen[1] - mark,cen[2]), (cen[0],cen[1] + mark,cen[2])) for cen in pt_x]
	a = mark_o
	b = mark_x1 + mark_x2
	return (a, b)

start = time.time()
if next or loft_o or loft_x or undo or bake == True:# ボタンを押した瞬間はプレビュー省略
	print("preview pass")
	pass
else:
	if past == False:# 最後の壁だけ表示
		print("preview only one")
		preview_wall = Previewwall(sc.sticky["dict_combi"], data.get_wall(), curve, zoom)
	else:# 全部の壁を表示
		print("preview all")
		preview_wall = [Previewwall(sc.sticky["dict_combi"], i, curve, zoom) for i in sc.sticky["dict_combi"]]
preview_o = Previewmark(curve, sc.sticky["dict_combi"], data.get_wall())[0]
preview_x = Previewmark(curve, sc.sticky["dict_combi"], data.get_wall())[1]
end = time.time() - start
print("previewtime = " + str(end))

# ボタンが押されたときは以下の操作を行う/////////////////////////////////////////////////
if next:# 次の組み合わせを探す
    print("Input Key = next")
    if len(curve) - len(sc.sticky['list_usedindex']) <= 2:
        bake = True
        print("Start Bake")
    else:
        sc.sticky['count_loop'] += 1
        sc.sticky['count_error'] = 0
        sc.sticky['list_usedindex'].append(index_o)
        sc.sticky['list_usedindex'].append(index_x)
        sc.sticky['list_history'].append(2)

if loft_o:# ロフト元が違う場合
    print("Input Key = loft_o")
    if len(curve) - len(sc.sticky['list_usedindex']) <= 2:
        bake = True
        print("Start Bake")
    else:
        sc.sticky['list_usedindex'].append(index_o)
        del sc.sticky['dict_combi'][sc.sticky['count_loop']]
        sc.sticky['count_loop'] += 1
        sc.sticky['count_error'] = 0
        sc.sticky['list_history'].append(1)

if loft_x:# ロフト先が違う場合
    print("Input Key = loft_x")
    del sc.sticky['dict_combi'][sc.sticky['count_loop']]
    if sc.sticky['count_error'] == len(list_loft_x) - 2:
        sc.sticky['count_error'] = 0
    elif sc.sticky['count_error'] == 14:
        sc.sticky['count_error'] = 0
    else:
        sc.sticky['count_error'] += 1

def Undo():# アンドゥ
	print("Input Key = Undo")
	if sc.sticky['count_loop'] == 0:
		sc.sticky['list_usedindex'] = []
		sc.sticky['list_history'] = []
		
	else:
		if sc.sticky['list_history'][-1] == 2:
			del sc.sticky['dict_combi'][sc.sticky['count_loop']]
			del sc.sticky['dict_combi'][sc.sticky['count_loop'] - 1]
			del sc.sticky['list_usedindex'][-1]
			del sc.sticky['list_usedindex'][-1]
		else:
			del sc.sticky['list_usedindex'][-1]
		del sc.sticky['list_history'][-1]
		sc.sticky['count_loop'] = sc.sticky['count_loop'] - 1

if undo:
	Undo()

def Reset():# リセットするときの挙動
	print("Input Key = Undo")
	sc.sticky['count_loop'] = 0
	sc.sticky['count_error'] = 0
	sc.sticky['dict_distance'] = {}
	sc.sticky['dict_combi'] = {}
	sc.sticky['preview'] = []
	sc.sticky['list_usedindex'] = []
	sc.sticky['list_history'] = []

if bake:# ベイクする
	print("Input Key = bake")
	obj_bake = [Previewwall(sc.sticky["dict_combi"], i, curve, zoom) for i in sc.sticky["dict_combi"]]
	for wall in obj_bake:
		doc_obj = rs.coercerhinoobject(wall)
		doc_attributes = doc_obj.Attributes
		doc_geometry = doc_obj.Geometry
		sc.doc = Rhino.RhinoDoc.ActiveDoc
		rhino_obj = sc.doc.Objects.Add(doc_geometry, doc_attributes)
		sc.doc = ghdoc
	Reset()

O = data.ind_o
X = data.ind_x
count_error = "✕は" + str(sc.sticky['count_error'] + 1) + "番目の候補です"
len_index = len(sc.sticky['list_usedindex'])