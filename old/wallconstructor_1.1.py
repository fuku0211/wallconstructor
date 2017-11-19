# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import time



#//////////////////////////////////////////////////////////////
if 'count_loop' not in sc.sticky:
    sc.sticky['count_loop'] = 0
if 'dict_distance' not in sc.sticky:
    sc.sticky['dict_distance'] = {}
if 'dict_combi' not in sc.sticky:
    sc.sticky['dict_combi'] = {}
if 'count_invalid' not in sc.sticky:
    sc.sticky['count_invalid'] = 0
if 'list_usedindex' not in sc.sticky:
    sc.sticky['list_usedindex'] = []
if 'list_history' not in sc.sticky:
    sc.sticky['list_history'] = []
#//////////////////////////////////////////////////////////////

#/////////////////////////////////////////////////////////////初回だけ点の座標の計算をする
#辞書(キーがそれぞれの曲線のインデックス、値が距離の近いものを順番に並べたリスト)を生成する関数
def Findclosestpt(crvs):
    dict_dist = {}
    list_midpt = [rs.CurveMidPoint(crv) for crv in crvs]
    count = 0
    while count != len(crvs):
        list_distance = [int(rs.Distance(list_midpt[count], i)) for i in list_midpt]
        list_sorted = zip(list_distance, range(len(crvs)))
        list_sorted.sort()
        list_distance, list_sortindex = zip(*list_sorted)
        dict_dist[count] = list_sortindex
        count += 1
    return dict_dist

if sc.sticky['count_loop'] == 0:
    print("start calcilate")
    time_pt_start = time.time()
    sc.sticky['dict_distance'] = Findclosestpt(curve)
    time_pt_end = time.time() - time_pt_start
    print("end calcilate")
    print("点座標計算にかかった時間 = " + str(time_pt_end) + "s")

else:
    print("skip calculate")

#////////////////////////////////////////////////////////////２つのインデックスを求める
for remain in range(len(curve)):
    if remain in sc.sticky['list_usedindex']:
        pass
    else:
		#２つのうちの片方のインデックス
        index_o = remain
        break
list_loft_x = sc.sticky['dict_distance'].values()[index_o]
#もう片方のインデックス
index_x = list_loft_x[1 + sc.sticky['count_invalid']]

sc.sticky['dict_combi'][sc.sticky['count_loop']] = [index_o, index_x, height, thickness]

#////////////////////////////////////////////////////////////////カーブの向きをそろえる
def Flip_crv(crvs, index_a, index_b):
	if rs.CurveDirectionsMatch(crvs[index_a], crvs[index_b]):
		A = crvs[index_a]
		B = crvs[index_b]
	else:
		A = crvs[index_a]
		B = rs.ReverseCurve(crvs[index_b])
	return (A, B)

#///////////////////////////////////////////////////////////////カーブの長さをそろえる
def Extend_trim_crv(A, B, thickness):
	if mode == "extend":
		if rs.CurveLength(A) > rs.CurveLength(B):
			B = rs.OffsetCurve(A, rs.CurveMidPoint(B), thickness)
		else:
			A = rs.OffsetCurve(B, rs.CurveMidPoint(A), thickness)
	elif mode == "trim":
		if rs.CurveLength(A) > rs.CurveLength(B):
			A = rs.OffsetCurve(B, rs.CurveMidPoint(A), thickness)
		else:
			B = rs.OffsetCurve(A, rs.CurveMidPoint(B), thickness)
	return (A, B)

#/////////////////////////////////////////////////////////////////////////壁を立てる
def Makewall(list):
    obj_srf = rs.AddLoftSrf([list[0], list[1]])
    obj_height = rs.AddLine((0,0,0), (0,0,list[2]))
    obj_wall = rs.ExtrudeSurface(obj_srf, obj_height)
    return obj_wall

O = Flip_crv(curve, index_o, index_x)[0]
X = Flip_crv(curve, index_o, index_x)[1]
O = Extend_trim_crv(O, X, thickness)[0]
X = Extend_trim_crv(O, X, thickness)[1]
list_OXheight = [O, X, height]
obj_wall = Makewall(list_OXheight)

#////////////////////////////////////////////////////////////////////////ズームする
if zoom:
    obj_zoom = rs.BoundingBox([obj_wall, curve[index_o], curve[index_x]])
    rs.ZoomBoundingBox(obj_zoom)

#//////////////////////////////////////dict_combiをもとにすべての壁のプレビューを作る
def Makeallpreview(dict_combi):
	preview = [Makewall([Extend_trim_crv(Flip_crv(curve, i[0], i[1])[0], Flip_crv(curve, i[0], i[1])[1], i[3])[0], Extend_trim_crv(Flip_crv(curve, i[0], i[1])[0], Flip_crv(curve, i[0], i[1])[1], i[3])[1], i[2]]) for i in dict_combi.values()]
	return preview

if preview:
    print("start preview")
    time_preview_start = time.time()
    preview = Makeallpreview(sc.sticky['dict_combi'])
    time_preview_end = time.time() - time_preview_start
    print("end preview")
    print("プレビュー作成にかかった時間 = " + str(time_preview_end) + "s")
else:
    print("skip preview")
    preview = obj_wall

#/////////////////////////////////////////////////////////////////////目印をつくる
pt_o = rs.DivideCurve(curve[index_o], 10)
pt_x = rs.DivideCurve(curve[index_x], 10)
mark_o = [rs.AddCircle(center_o, mark) for center_o in pt_o]
mark_x1 = [rs.AddLine((center_x[0] - mark,center_x[1],center_x[2]), (center_x[0] + mark,center_x[1],center_x[2])) for center_x in pt_x]
mark_x2 = [rs.AddLine((center_x[0],center_x[1] - mark,center_x[2]), (center_x[0],center_x[1] + mark,center_x[2])) for center_x in pt_x]
a = mark_o
b = mark_x1 + mark_x2

#///////////////////////////////////////////////////////////////デバック情報を表示
print(str(sc.sticky['count_loop']) + "個目の壁")
print("ロフト元のインデックス = " + str(index_o))
print("ロフト先のインデックス = " + str(index_x))
print("今の辞書情報 = " + str(sc.sticky['dict_combi'][sc.sticky['count_loop']]))
print("len(sc.sticky['list usedindex']) = " + str(len(sc.sticky['list_usedindex'])))
print("len(sc.sticky['list histroy']) = " + str(len(sc.sticky['list_history'])))

#////////////////////////////////////////////////////////////次の組み合わせを探す
if next:
    print("input key = next")
    if len(curve) - len(sc.sticky['list_usedindex']) <= 2:
        bake = True
        print("start bake")
    else:
        sc.sticky['count_loop'] += 1
        sc.sticky['count_invalid'] = 0
        sc.sticky['list_usedindex'].append(index_o)
        sc.sticky['list_usedindex'].append(index_x)
        sc.sticky['list_history'].append(2)

#//////////////////////////////////////////////////////////////ロフト元が違う場合
if loft_o:
    print("input key = loft_o")
    if len(curve) - len(sc.sticky['list_usedindex']) <= 2:
        bake = True
        print("Start bake")
    else:
        sc.sticky['list_usedindex'].append(index_o)
        del sc.sticky['dict_combi'][sc.sticky['count_loop']]
        sc.sticky['count_loop'] += 1
        sc.sticky['count_invalid'] = 0
        sc.sticky['list_history'].append(1)

#//////////////////////////////////////////////////////////////ロフト先が違う場合
if loft_x:
    print("input key = loft_x")
    del sc.sticky['dict_combi'][sc.sticky['count_loop']]
    if sc.sticky['count_invalid'] == len(list_loft_x) - 2:
        sc.sticky['count_invalid'] = 0
    elif sc.sticky['count_invalid'] == 14:
        sc.sticky['count_invalid'] = 0
    else:
        sc.sticky['count_invalid'] += 1

#///////////////////////////////////////////////////////////////////////アンドゥ
if undo:
	print("input key = undo")
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

#////////////////////////////////////////////////////////リセットするときの挙動
def Reset():
    sc.sticky['count_loop'] = 0
    sc.sticky['count_invalid'] = 0
    sc.sticky['dict_distance'] = {}
    sc.sticky['dict_combi'] = {}
    sc.sticky['preview'] = []
    sc.sticky['list_usedindex'] = []
    sc.sticky['list_history'] = []

#///////////////////////////////////////////////////////////////////ベイクする
if bake:
    print("input key = bake")
    preview = Makeallpreview(sc.sticky['dict_combi'])
    zoom = rs.BoundingBox(preview)
    rs.ZoomBoundingBox(zoom)
    for wall in preview:
        doc_obj = rs.coercerhinoobject(wall)
        doc_attributes = doc_obj.Attributes
        doc_geometry = doc_obj.Geometry
        sc.doc = Rhino.RhinoDoc.ActiveDoc
        rhino_obj = sc.doc.Objects.Add(doc_geometry, doc_attributes)
        sc.doc = ghdoc
    Reset()

count_invalid = "✕は" + str(sc.sticky['count_invalid'] + 1) + "番目の候補です"
len_index = len(sc.sticky['list_usedindex'])