import re
from collections import Counter

SCENE_PATH = 'Assets/Scenes/AIGym.unity'
with open(SCENE_PATH, 'r', encoding='utf-8') as f:
    text = f.read()

FONT_GUID   = "8835d391fc6f18144b277cf3b43fbb85"
TABLET_GUID = "9f4e2a1b8c7d4e6fa0123456789abc01"
IMG_GUID    = "fe87c0e1cc204ed48ad3b37840f39efc"
TXT_GUID    = "5f7201a12d95ffc409449d95f23cf332"
BTN_GUID    = "4e29b1a8efbd4b44bb3f3716e73f07ff"

def esc_kor(s):
    return "".join(f"\\u{ord(c):04X}" if ord(c) > 127 else c for c in s)

# 1. Fix PromptBanner (1992000007) overlap with AI Coach bubble: move y: 120 -> y: 315
pat_pb = r'(--- !u!224 &1992000007\nRectTransform:.*?  m_AnchoredPosition: \{x: 0, y: )[-\d\.]+(\})'
text, n_pb = re.subn(pat_pb, r'\g<1>315\g<2>', text, count=1, flags=re.DOTALL)
print(f"Moved PromptBanner up to y=315 (matches={n_pb})")

# ID allocator starting at 1992000200 (zero conflict with existing <= 1992000123)
next_id = 1992000200
def alloc():
    global next_id
    v = next_id
    next_id += 1
    return v

docs = []

def add_panel(name, parent_rt, amin, amax, pivot, pos, size, rgba, active=1, child_rts=None):
    go, rt, cr, im = alloc(), alloc(), alloc(), alloc()
    ch_yaml = "\n".join(f"  - {{fileID: {c}}}" for c in (child_rts or []))
    ch_block = f"m_Children:\n{ch_yaml}" if child_rts else "m_Children: []"
    r, g, b, a = rgba
    docs.append(f"""--- !u!1 &{go}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {rt}}}
  - component: {{fileID: {cr}}}
  - component: {{fileID: {im}}}
  m_Layer: 5
  m_Name: {name}
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: {active}
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
  {ch_block}
  m_Father: {{fileID: {parent_rt}}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
  m_AnchorMin: {{x: {amin[0]}, y: {amin[1]}}}
  m_AnchorMax: {{x: {amax[0]}, y: {amax[1]}}}
  m_AnchoredPosition: {{x: {pos[0]}, y: {pos[1]}}}
  m_SizeDelta: {{x: {size[0]}, y: {size[1]}}}
  m_Pivot: {{x: {pivot[0]}, y: {pivot[1]}}}
--- !u!222 &{cr}
CanvasRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_CullTransparentMesh: 1
--- !u!114 &{im}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {IMG_GUID}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: UnityEngine.UI::UnityEngine.UI.Image
  m_Material: {{fileID: 0}}
  m_Color: {{r: {r}, g: {g}, b: {b}, a: {a}}}
  m_RaycastTarget: 1
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
    return go, rt, im

def add_text(name, parent_rt, amin, amax, pivot, pos, size, fsize, fstyle, align, rgba, txt):
    go, rt, cr, tx = alloc(), alloc(), alloc(), alloc()
    r, g, b, a = rgba
    docs.append(f"""--- !u!1 &{go}
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
  m_AnchorMin: {{x: {amin[0]}, y: {amin[1]}}}
  m_AnchorMax: {{x: {amax[0]}, y: {amax[1]}}}
  m_AnchoredPosition: {{x: {pos[0]}, y: {pos[1]}}}
  m_SizeDelta: {{x: {size[0]}, y: {size[1]}}}
  m_Pivot: {{x: {pivot[0]}, y: {pivot[1]}}}
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
  m_Color: {{r: {r}, g: {g}, b: {b}, a: {a}}}
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
    m_Alignment: {align}
    m_AlignByGeometry: 0
    m_RichText: 1
    m_HorizontalOverflow: 0
    m_VerticalOverflow: 1
    m_LineSpacing: 1.2
  m_Text: "{esc_kor(txt)}" """)
    return go, rt, tx

def add_button(name, parent_rt, amin, amax, pivot, pos, size, bg_rgba, label_txt, fsize, target_comp_id, method_name, int_arg=None):
    go, rt, cr, im, bt = alloc(), alloc(), alloc(), alloc(), alloc()
    lbl_go, lbl_rt, lbl_tx = add_text("Label", rt, (0,0), (1,1), (0.5,0.5), (0,0), (0,0), fsize, 1, 4, (1,1,1,1), label_txt)
    r, g, b, a = bg_rgba
    mode = 3 if int_arg is not None else 1
    int_val = int_arg if int_arg is not None else 0
    docs.append(f"""--- !u!1 &{go}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {rt}}}
  - component: {{fileID: {cr}}}
  - component: {{fileID: {im}}}
  - component: {{fileID: {bt}}}
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
  m_Children:
  - {{fileID: {lbl_rt}}}
  m_Father: {{fileID: {parent_rt}}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
  m_AnchorMin: {{x: {amin[0]}, y: {amin[1]}}}
  m_AnchorMax: {{x: {amax[0]}, y: {amax[1]}}}
  m_AnchoredPosition: {{x: {pos[0]}, y: {pos[1]}}}
  m_SizeDelta: {{x: {size[0]}, y: {size[1]}}}
  m_Pivot: {{x: {pivot[0]}, y: {pivot[1]}}}
--- !u!222 &{cr}
CanvasRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_CullTransparentMesh: 1
--- !u!114 &{im}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {IMG_GUID}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: UnityEngine.UI::UnityEngine.UI.Image
  m_Material: {{fileID: 0}}
  m_Color: {{r: {r}, g: {g}, b: {b}, a: {a}}}
  m_RaycastTarget: 1
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
--- !u!114 &{bt}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {BTN_GUID}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: UnityEngine.UI::UnityEngine.UI.Button
  m_Navigation:
    m_Mode: 3
    m_WrapAround: 0
    m_SelectOnUp: {{fileID: 0}}
    m_SelectOnDown: {{fileID: 0}}
    m_SelectOnLeft: {{fileID: 0}}
    m_SelectOnRight: {{fileID: 0}}
  m_Transition: 1
  m_Colors:
    m_NormalColor: {{r: 1, g: 1, b: 1, a: 1}}
    m_HighlightedColor: {{r: 0.92, g: 0.96, b: 1, a: 1}}
    m_PressedColor: {{r: 0.78, g: 0.82, b: 0.88, a: 1}}
    m_SelectedColor: {{r: 1, g: 1, b: 1, a: 1}}
    m_DisabledColor: {{r: 0.5, g: 0.5, b: 0.5, a: 0.5}}
    m_ColorMultiplier: 1
    m_FadeDuration: 0.1
  m_SpriteState:
    m_HighlightedSprite: {{fileID: 0}}
    m_PressedSprite: {{fileID: 0}}
    m_SelectedSprite: {{fileID: 0}}
    m_DisabledSprite: {{fileID: 0}}
  m_AnimationTriggers:
    m_NormalTrigger: Normal
    m_HighlightedTrigger: Highlighted
    m_PressedTrigger: Pressed
    m_SelectedTrigger: Selected
    m_DisabledTrigger: Disabled
  m_Interactable: 1
  m_TargetGraphic: {{fileID: {im}}}
  m_OnClick:
    m_PersistentCalls:
      m_Calls:
      - m_Target: {{fileID: {target_comp_id}}}
        m_TargetAssemblyTypeName: GymTabletGuide, Assembly-CSharp
        m_MethodName: {method_name}
        m_Mode: {mode}
        m_Arguments:
          m_ObjectArgument: {{fileID: 0}}
          m_ObjectArgumentAssemblyTypeName: UnityEngine.Object, UnityEngine
          m_IntArgument: {int_val}
          m_FloatArgument: 0
          m_StringArgument: 
          m_BoolArgument: 0
        m_CallState: 2""")
    return go, rt, bt

if "GymTabletPanel" not in text:
    tablet_comp_id = alloc()

    # Open button at top-right (left of '체험 끝내기 · 요약')
    open_go, open_rt, open_bt = add_button(
        "Btn_GymTablet", 1992000002,
        (1, 1), (1, 1), (1, 1), (-285, -28), (210, 56),
        (0.13, 0.65, 0.52, 0.96), "기구 도감 (G)", 22,
        tablet_comp_id, "OpenTablet"
    )

    # Pre-allocate TabletPanel RT ID so children can reference it
    panel_rt = alloc()
    panel_go = alloc()
    panel_cr = alloc()
    panel_im = alloc()

    # Header Title & Close Button
    _, hdr_rt, _ = add_text("HeaderTitle", panel_rt, (0,1), (1,1), (0,1), (36, -24), (-220, 46), 30, 1, 3, (1,1,1,1), "헬스장 기구 안내 태블릿 (11종)")
    _, close_rt, _ = add_button("Btn_CloseTablet", panel_rt, (1,1), (1,1), (1,1), (-28, -22), (120, 48), (0.65, 0.22, 0.24, 1), "닫기", 22, tablet_comp_id, "CloseTablet")

    # 11 Machine Buttons on left column
    machine_labels = [
        "체스트프레스", "벤치프레스", "랫풀다운", "풀업바", "암컬 머신",
        "파워 레그프레스", "레그 익스텐션", "라잉 레그컬", "힙 어덕션", "V-스쿼트", "천국의 계단"
    ]
    btn_rts = []
    btn_ids = []
    for i, lbl in enumerate(machine_labels):
        _, brt, bid = add_button(
            f"Btn_Machine_{i:02d}", panel_rt,
            (0,1), (0,1), (0,1), (32, -96 - i * 58), (340, 50),
            (0.16, 0.22, 0.34, 1), lbl, 20,
            tablet_comp_id, "SelectMachine", int_arg=i
        )
        btn_rts.append(brt)
        btn_ids.append(bid)

    # Right Detail Screen
    _, det_title_rt, det_title_tx = add_text("DetailTitle", panel_rt, (0,1), (1,1), (0,1), (410, -104), (-445, 52), 34, 1, 0, (1,1,1,1), "체스트프레스")
    _, det_part_rt,  det_part_tx  = add_text("DetailPart",  panel_rt, (0,1), (1,1), (0,1), (410, -162), (-445, 36), 22, 1, 0, (0.45, 0.92, 0.78, 1), "운동 부위")
    _, det_how_rt,   det_how_tx   = add_text("DetailHowTo", panel_rt, (0,1), (1,1), (0,1), (410, -220), (-445, 160), 23, 0, 0, (0.94, 0.96, 0.99, 1), "[사용 방법]")
    _, det_caut_rt,  det_caut_tx  = add_text("DetailCaution", panel_rt, (0,1), (1,1), (0,1), (410, -395), (-445, 140), 21, 0, 0, (1.0, 0.85, 0.45, 1), "[안전 포인트]")
    _, det_rec_rt,   det_rec_tx   = add_text("DetailRecommend", panel_rt, (0,1), (1,1), (0,1), (410, -545), (-445, 64), 20, 1, 0, (0.68, 0.86, 1.0, 1), "추천 대상")
    _, move_rt, _ = add_button("Btn_MoveToMachine", panel_rt, (1,0), (1,0), (1,0), (-36, 32), (300, 62), (0.98, 0.74, 0.16, 1), "이 기구로 이동 →", 24, tablet_comp_id, "MoveToSelectedMachine")

    all_panel_children = [hdr_rt, close_rt] + btn_rts + [det_title_rt, det_part_rt, det_how_rt, det_caut_rt, det_rec_rt, move_rt]
    ch_yaml = "\n".join(f"  - {{fileID: {c}}}" for c in all_panel_children)

    docs.append(f"""--- !u!1 &{panel_go}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {panel_rt}}}
  - component: {{fileID: {panel_cr}}}
  - component: {{fileID: {panel_im}}}
  m_Layer: 5
  m_Name: GymTabletPanel
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 0
--- !u!224 &{panel_rt}
RectTransform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {panel_go}}}
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children:
{ch_yaml}
  m_Father: {{fileID: 1992000002}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
  m_AnchorMin: {{x: 0.5, y: 0.5}}
  m_AnchorMax: {{x: 0.5, y: 0.5}}
  m_AnchoredPosition: {{x: 0, y: 0}}
  m_SizeDelta: {{x: 1320, y: 760}}
  m_Pivot: {{x: 0.5, y: 0.5}}
--- !u!222 &{panel_cr}
CanvasRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {panel_go}}}
  m_CullTransparentMesh: 1
--- !u!114 &{panel_im}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {panel_go}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {IMG_GUID}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: UnityEngine.UI::UnityEngine.UI.Image
  m_Material: {{fileID: 0}}
  m_Color: {{r: 0.08, g: 0.12, b: 0.2, a: 0.96}}
  m_RaycastTarget: 1
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

    # GymTabletGuide MonoBehaviour attached to ExerciseCanvas (1992000001)
    btns_yaml = "\n".join(f"  - {{fileID: {b}}}" for b in btn_ids)
    docs.append(f"""--- !u!114 &{tablet_comp_id}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1992000001}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {TABLET_GUID}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: Assembly-CSharp::GymTabletGuide
  tabletPanel: {{fileID: {panel_go}}}
  openButton: {{fileID: {open_go}}}
  detailTitleText: {{fileID: {det_title_tx}}}
  detailPartText: {{fileID: {det_part_tx}}}
  detailHowToText: {{fileID: {det_how_tx}}}
  detailCautionText: {{fileID: {det_caut_tx}}}
  detailRecommendText: {{fileID: {det_rec_tx}}}
  machineButtons:
{btns_yaml}""")

    # Add tablet_comp_id to ExerciseCanvas GameObject (1992000001) m_Component
    pat_ec_go = r'(--- !u!1 &1992000001\nGameObject:.*?m_Component:\n)(.*?)(  m_Layer:)'
    m_go = re.search(pat_ec_go, text, re.DOTALL)
    assert m_go, "ExerciseCanvas GO not found"
    text = text[:m_go.end(2)] + f"  - component: {{fileID: {tablet_comp_id}}}\n" + text[m_go.end(2):]

    # Add open_rt and panel_rt to ExerciseCanvas RectTransform (1992000002) m_Children
    pat_ec_rt = r'(--- !u!224 &1992000002\nRectTransform:.*?m_Children:\n)(.*?)(  m_Father:)'
    m_rt = re.search(pat_ec_rt, text, re.DOTALL)
    assert m_rt, "ExerciseCanvas RT not found"
    text = text[:m_rt.end(2)] + f"  - {{fileID: {open_rt}}}\n  - {{fileID: {panel_rt}}}\n" + text[m_rt.end(2):]

    # Insert all docs before SceneRoots
    marker_roots = "--- !u!1660057539 &9223372036854775807"
    idx = text.find(marker_roots)
    assert idx != -1, "SceneRoots not found"
    text = text[:idx] + "\n".join(docs) + "\n" + text[idx:]
    print(f"Added GymTabletPanel + Btn_GymTablet + 11 buttons + GymTabletGuide component!")

with open(SCENE_PATH, 'w', encoding='utf-8') as f:
    f.write(text)

ids = re.findall(r'^--- !u!\d+ &(-?\d+)', text, re.M)
dups = {k: v for k, v in Counter(ids).items() if v > 1}
print("Duplicate IDs:", dups)
