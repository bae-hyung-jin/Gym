import re
from collections import Counter

SCENE_PATH = 'Assets/Scenes/AIGym.unity'
with open(SCENE_PATH, 'r', encoding='utf-8') as f:
    text = f.read()

FONT_GUID = "8835d391fc6f18144b277cf3b43fbb85"

# IDs:
# MachineInfoCard: GO=1992000100, RT=1992000101, CR=1992000102, Img=1992000103
# AccentBar:       GO=1992000104, RT=1992000105, CR=1992000106, Img=1992000107
# Title:           GO=1992000108, RT=1992000109, CR=1992000110, Txt=1992000111
# Part:            GO=1992000112, RT=1992000113, CR=1992000114, Txt=1992000115
# HowTo:           GO=1992000116, RT=1992000117, CR=1992000118, Txt=1992000119
# Caution:         GO=1992000120, RT=1992000121, CR=1992000122, Txt=1992000123

def make_text_obj(go_id, rt_id, cr_id, tx_id, name, pos_x, pos_y, sz_x, sz_y, fsize, fstyle, r, g, b, default_txt):
    return f"""--- !u!1 &{go_id}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {rt_id}}}
  - component: {{fileID: {cr_id}}}
  - component: {{fileID: {tx_id}}}
  m_Layer: 5
  m_Name: {name}
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!224 &{rt_id}
RectTransform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go_id}}}
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 1992000101}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
  m_AnchorMin: {{x: 0, y: 1}}
  m_AnchorMax: {{x: 1, y: 1}}
  m_AnchoredPosition: {{x: {pos_x}, y: {pos_y}}}
  m_SizeDelta: {{x: {sz_x}, y: {sz_y}}}
  m_Pivot: {{x: 0, y: 1}}
--- !u!222 &{cr_id}
CanvasRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go_id}}}
  m_CullTransparentMesh: 1
--- !u!114 &{tx_id}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go_id}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: 5f7201a12d95ffc409449d95f23cf332, type: 3}}
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
    m_Alignment: 0
    m_AlignByGeometry: 0
    m_RichText: 1
    m_HorizontalOverflow: 0
    m_VerticalOverflow: 1
    m_LineSpacing: 1.15
  m_Text: "{default_txt}"
"""

card_yaml = f"""--- !u!1 &1992000100
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 1992000101}}
  - component: {{fileID: 1992000102}}
  - component: {{fileID: 1992000103}}
  m_Layer: 5
  m_Name: MachineInfoCard
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 0
--- !u!224 &1992000101
RectTransform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1992000100}}
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children:
  - {{fileID: 1992000105}}
  - {{fileID: 1992000109}}
  - {{fileID: 1992000113}}
  - {{fileID: 1992000117}}
  - {{fileID: 1992000121}}
  m_Father: {{fileID: 1992000002}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
  m_AnchorMin: {{x: 1, y: 1}}
  m_AnchorMax: {{x: 1, y: 1}}
  m_AnchoredPosition: {{x: -28, y: -105}}
  m_SizeDelta: {{x: 540, y: 220}}
  m_Pivot: {{x: 1, y: 1}}
--- !u!222 &1992000102
CanvasRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1992000100}}
  m_CullTransparentMesh: 1
--- !u!114 &1992000103
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1992000100}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: fe87c0e1cc204ed48ad3b37840f39efc, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: UnityEngine.UI::UnityEngine.UI.Image
  m_Material: {{fileID: 0}}
  m_Color: {{r: 0.08, g: 0.12, b: 0.2, a: 0.92}}
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
  m_PixelsPerUnitMultiplier: 1
--- !u!1 &1992000104
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 1992000105}}
  - component: {{fileID: 1992000106}}
  - component: {{fileID: 1992000107}}
  m_Layer: 5
  m_Name: AccentBar
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!224 &1992000105
RectTransform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1992000104}}
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 1992000101}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
  m_AnchorMin: {{x: 0, y: 1}}
  m_AnchorMax: {{x: 1, y: 1}}
  m_AnchoredPosition: {{x: 0, y: 0}}
  m_SizeDelta: {{x: 0, y: 6}}
  m_Pivot: {{x: 0.5, y: 1}}
--- !u!222 &1992000106
CanvasRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1992000104}}
  m_CullTransparentMesh: 1
--- !u!114 &1992000107
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1992000104}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: fe87c0e1cc204ed48ad3b37840f39efc, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: UnityEngine.UI::UnityEngine.UI.Image
  m_Material: {{fileID: 0}}
  m_Color: {{r: 0.13, g: 0.65, b: 0.52, a: 1}}
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
  m_PixelsPerUnitMultiplier: 1
""" + \
make_text_obj(1992000108, 1992000109, 1992000110, 1992000111, "Title",   24, -18,  -48, 34, 24, 1, 1.0,  1.0,  1.0,  "\\uAE30\\uAD6C \\uC548\\uB0B4") + \
make_text_obj(1992000112, 1992000113, 1992000114, 1992000115, "Part",    24, -52,  -48, 26, 18, 1, 0.45, 0.92, 0.78, "\\uC6B4\\uB3D9 \\uBD80\\uC704") + \
make_text_obj(1992000116, 1992000117, 1992000118, 1992000119, "HowTo",   24, -84,  -48, 66, 17, 0, 0.94, 0.96, 0.99, "\\uC0AC\\uC6A9\\uBC95") + \
make_text_obj(1992000120, 1992000121, 1992000122, 1992000123, "Caution", 24, -154, -48, 52, 16, 0, 1.0,  0.85, 0.45, "\\uC548\\uC804 \\uD301")

# 1. Add 1992000101 to ExerciseCanvas (1992000002) m_Children
if "{fileID: 1992000101}" not in text:
    pat_ec = r'(--- !u!224 &1992000002\nRectTransform:.*?m_Children:\n)(.*?)(  m_Father:)'
    m_ec = re.search(pat_ec, text, re.DOTALL)
    assert m_ec, "ExerciseCanvas RectTransform not found!"
    text = text[:m_ec.end(2)] + "  - {fileID: 1992000101}\n" + text[m_ec.end(2):]
    print("Added MachineInfoCard to ExerciseCanvas children.")

# 2. Insert card_yaml BEFORE SceneRoots
if "--- !u!1 &1992000100" not in text:
    marker_roots = "--- !u!1660057539 &9223372036854775807"
    idx = text.find(marker_roots)
    assert idx != -1, "SceneRoots not found!"
    text = text[:idx] + card_yaml + text[idx:]
    print("Inserted MachineInfoCard UI hierarchy before SceneRoots.")

# 3. Wire infoCardRoot..infoCautionText to every ExerciseStation component
wire_fields = """  stopButton: {fileID: 1992000075}
  infoCardRoot: {fileID: 1992000100}
  infoTitleText: {fileID: 1992000111}
  infoPartText: {fileID: 1992000115}
  infoHowToText: {fileID: 1992000119}
  infoCautionText: {fileID: 1992000123}
  customTargetPart: 
  customHowToUse: 
  customSafetyTip: 
  customHudTip: """

text, count = re.subn(r'  stopButton: \{fileID: 1992000075\}(?!\n  infoCardRoot:)', wire_fields, text)
print(f"Wired MachineInfoCard to {count} ExerciseStation components.")

with open(SCENE_PATH, 'w', encoding='utf-8') as f:
    f.write(text)

ids = re.findall(r'^--- !u!\d+ &(-?\d+)', text, re.M)
dups = {k: v for k, v in Counter(ids).items() if v > 1}
print("Duplicate IDs:", dups)
