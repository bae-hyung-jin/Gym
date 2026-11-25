import re, math
from collections import Counter

SCENE_PATH = 'Assets/Scenes/AIGym.unity'
with open(SCENE_PATH, 'r', encoding='utf-8') as f:
    text = f.read()

FONT_GUID = "8835d391fc6f18144b277cf3b43fbb85"
TXT_GUID  = "5f7201a12d95ffc409449d95f23cf332"
IMG_GUID  = "fe87c0e1cc204ed48ad3b37840f39efc"

def esc_kor(s):
    return "".join(f"\\u{ord(c):04X}" if ord(c) > 127 else c for c in s)

# 11 TabletStand PrefabInstance IDs (1997001001 + i*10), root Transform IDs (1997001003 + i*10)
stands_info = [
    (0,  "체스트프레스",          "가슴 · 팔 뒤쪽",          "등받이 밀착 · 앞쪽으로 천천히 밀기"),
    (1,  "벤치프레스",            "가슴 전체 · 삼두근",      "등 밀착 · 천장 방향으로 부드럽게 밀기"),
    (2,  "랫풀다운",              "등 근육 · 바른 자세",     "가슴 펴기 · 바를 가슴 위로 당기기"),
    (3,  "풀업바",                "등 상부 · 팔 근력",       "바를 넓게 잡고 천천히 끌어올리기"),
    (4,  "암컬 머신",             "팔 앞쪽 (이두근)",        "팔꿈치 고정 · 반동 없이 접어 올리기"),
    (5,  "파워 레그프레스",       "허벅지 · 엉덩이",         "허리 밀착 · 무릎 잠그지 않고 밀기"),
    (6,  "레그 익스텐션",         "허벅지 앞쪽",             "엉덩이 고정 · 무릎 천천히 펴기"),
    (7,  "라잉 레그컬",           "허벅지 뒤쪽 (햄스트링)",  "무릎 패드 고정 · 뒤꿈치 접어 올리기"),
    (8,  "힙 어덕션",             "허벅지 안쪽 · 골반 안정", "등받이 밀착 · 양 무릎 부드럽게 모으기"),
    (9,  "V-스쿼트",              "허벅지 전반 · 엉덩이",    "어깨 패드 밀착 · 천천히 앉았다 일어서기"),
    (10, "천국의 계단 (스텝밀)",  "심폐 지구력 · 하체 체력", "시선 정면 · 일정 속도로 계단 오르기"),
]

# Exact World Space Canvas transform relative to TabletStand root (scale 1.15):
# Screen front center = (0, 1.2295, -0.0335), Rotation X = +38 deg (front faces -Z & +Y!)
rad = math.radians(38.0)
qx = math.sin(rad / 2.0)
qw = math.cos(rad / 2.0)

next_id = 1998000001
def alloc():
    global next_id
    v = next_id
    next_id += 1
    return v

new_docs = []

def make_txt(name, parent_rt, pos_y, h, fsize, fstyle, r, g, b, txt):
    go, rt, cr, tx = alloc(), alloc(), alloc(), alloc()
    new_docs.append(f"""--- !u!1 &{go}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {rt}}}
  - component: {{fileID: {cr}}}
  - component: {{fileID: {tx}}}
  m_Layer: 5
  m_Name: {name}
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!224 &{rt}
RectTransform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: {parent_rt}}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
  m_AnchorMin: {{x: 0, y: 1}}
  m_AnchorMax: {{x: 1, y: 1}}
  m_AnchoredPosition: {{x: 16, y: {pos_y}}}
  m_SizeDelta: {{x: -32, y: {h}}}
  m_Pivot: {{x: 0, y: 1}}
--- !u!222 &{cr}
CanvasRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_CullTransparentMesh: 1
--- !u!114 &{tx}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {TXT_GUID}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: UnityEngine.UI::UnityEngine.UI.Text
  m_Material: {{fileID: 0}}
  m_Color: {{r: {r}, g: {g}, b: {b}, a: 1}}
  m_RaycastTarget: 0
  m_RaycastPadding: {{x: 0, y: 0, z: 0, w: 0}}
  m_Maskable: 1
  m_OnCullStateChanged:
    m_PersistentCalls:
      m_Calls: []
  m_FontData:
    m_Font: {{fileID: 12800000, guid: {FONT_GUID}, type: 3}}
    m_FontSize: {fsize}
    m_FontStyle: {fstyle}
    m_BestFit: 0
    m_MinSize: 10
    m_MaxSize: 40
    m_Alignment: 4
    m_AlignByGeometry: 0
    m_RichText: 1
    m_HorizontalOverflow: 0
    m_VerticalOverflow: 1
    m_LineSpacing: 1.15
  m_Text: "{esc_kor(txt)}" """)
    return rt

if "ScreenCanvas_00" not in text:
    for i, title, part, tip in stands_info:
        pi_id = 1997001000 + i * 10 + 1
        tr_id = 1997001000 + i * 10 + 3

        c_go, c_rt, c_cv, c_cr, c_im = alloc(), alloc(), alloc(), alloc(), alloc()
        t1_rt = make_txt("Txt_Title", c_rt, -18,  44, 28, 1, 1.0,  1.0,  1.0,  title)
        t2_rt = make_txt("Txt_Part",  c_rt, -68,  32, 18, 1, 0.45, 0.95, 0.80, part)
        t3_rt = make_txt("Txt_Tip",   c_rt, -106, 54, 15, 0, 0.92, 0.96, 1.0,  tip)
        t4_rt = make_txt("Txt_Hint",  c_rt, -168, 28, 14, 1, 1.0,  0.84, 0.35, "클릭 / F키로 상세 보기")

        new_docs.append(f"""--- !u!1 &{c_go}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {c_rt}}}
  - component: {{fileID: {c_cv}}}
  - component: {{fileID: {c_cr}}}
  - component: {{fileID: {c_im}}}
  m_Layer: 5
  m_Name: ScreenCanvas_{i:02d}
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!224 &{c_rt}
RectTransform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {c_go}}}
  m_LocalRotation: {{x: {qx:.7f}, y: 0, z: 0, w: {qw:.7f}}}
  m_LocalPosition: {{x: 0, y: 1.2295, z: -0.0335}}
  m_LocalScale: {{x: 0.001, y: 0.001, z: 0.001}}
  m_ConstrainProportionsScale: 0
  m_Children:
  - {{fileID: {t1_rt}}}
  - {{fileID: {t2_rt}}}
  - {{fileID: {t3_rt}}}
  - {{fileID: {t4_rt}}}
  m_Father: {{fileID: {tr_id}}}
  m_LocalEulerAnglesHint: {{x: 38, y: 0, z: 0}}
  m_AnchorMin: {{x: 0, y: 0}}
  m_AnchorMax: {{x: 0, y: 0}}
  m_AnchoredPosition: {{x: 0, y: 1.2295}}
  m_SizeDelta: {{x: 330, y: 210}}
  m_Pivot: {{x: 0.5, y: 0.5}}
--- !u!223 &{c_cv}
Canvas:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {c_go}}}
  m_Enabled: 1
  serializedVersion: 3
  m_RenderMode: 2
  m_Camera: {{fileID: 0}}
  m_PlaneDistance: 100
  m_PixelPerfect: 0
  m_ReceivesEvents: 1
  m_OverrideSorting: 0
  m_OverridePixelPerfect: 0
  m_SortingBucketNormalizedSize: 0
  m_VertexColorAlwaysGammaSpace: 0
  m_AdditionalShaderChannelsFlag: 0
  m_UpdateRectTransformForStandalone: 0
  m_SortingLayerID: 0
  m_SortingOrder: 0
  m_TargetDisplay: 0
--- !u!222 &{c_cr}
CanvasRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {c_go}}}
  m_CullTransparentMesh: 1
--- !u!114 &{c_im}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {c_go}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {IMG_GUID}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: UnityEngine.UI::UnityEngine.UI.Image
  m_Material: {{fileID: 0}}
  m_Color: {{r: 0.06, g: 0.11, b: 0.19, a: 0.94}}
  m_RaycastTarget: 0
  m_RaycastPadding: {{x: 0, y: 0, z: 0, w: 0}}
  m_Maskable: 1
  m_OnCullStateChanged:
    m_PersistentCalls:
      m_Calls: []
  m_Sprite: {{fileID: 0}}
  m_Type: 0
  m_PreserveAspect: 0
  m_FillCenter: 1
  m_FillMethod: 4
  m_FillAmount: 1
  m_FillClockwise: 1
  m_FillOrigin: 0
  m_UseSpriteMesh: 0
  m_PixelsPerUnitMultiplier: 1""")

        # Register c_go in PrefabInstance m_AddedGameObjects for pi_id!
        pat_pi = rf'(--- !u!1001 &{pi_id}\nPrefabInstance:.*?    m_AddedGameObjects: )\[\]'
        rep_pi = rf'''\g<1>
    - targetCorrespondingSourceObject: {{fileID: -8679921383154817045, guid: 9f4e2a1b8c7d4e6fa0123456789abc10, type: 3}}
      insertIndex: -1
      addedObject: {{fileID: {c_go}}}'''
        text, n = re.subn(pat_pi, rep_pi, text, count=1, flags=re.DOTALL)
        assert n == 1, f"Failed to register addedGameObject on PI {pi_id}"

    marker_roots = "--- !u!1660057539 &9223372036854775807"
    idx = text.find(marker_roots)
    assert idx != -1
    text = text[:idx] + "\n".join(new_docs) + "\n" + text[idx:]

    with open(SCENE_PATH, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Added millimeter-aligned World Space ScreenCanvas to all 11 3D Tablet Stands!")

ids = re.findall(r'^--- !u!\d+ &(-?\d+)', text, re.M)
dups = {k: v for k, v in Counter(ids).items() if v > 1}
print("Duplicate IDs:", dups)
