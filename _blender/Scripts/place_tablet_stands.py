import os, re, math, hashlib
from collections import Counter

FBX_GUID      = "9f4e2a1b8c7d4e6fa0123456789abc10"
INTERACT_GUID = "9f4e2a1b8c7d4e6fa0123456789abc02"

def det_guid(key):
    return hashlib.md5(f"tablet_stand_{key}".encode("utf-8")).hexdigest()

# 1. Create 4 URP/Lit materials for Gym_TabletStand
mat_dir = "Assets/Bomio_Exercises/Materials/TabletStand"
os.makedirs(mat_dir, exist_ok=True)
if not os.path.exists(f"{mat_dir}.meta"):
    with open(f"{mat_dir}.meta", "w", encoding="utf-8") as f:
        f.write(f"fileFormatVersion: 2\nguid: {det_guid('folder')}\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n")

mats_spec = [
    ("Mat_Tablet_Stand",  (0.11, 0.12, 0.15, 1.0), 0.45, 0.62, (0, 0, 0)),
    ("Mat_Tablet_Chrome", (0.82, 0.85, 0.88, 1.0), 0.92, 0.82, (0, 0, 0)),
    ("Mat_Tablet_Bezel",  (0.06, 0.07, 0.09, 1.0), 0.25, 0.72, (0, 0, 0)),
    ("Mat_Tablet_Screen", (0.12, 0.65, 0.54, 1.0), 0.05, 0.88, (0.08, 0.45, 0.38)),
]

ext_entries = []
for mname, (r,g,b,a), met, smooth, (er,eg,eb) in mats_spec:
    mguid = det_guid(mname)
    em_kw = "\n  - _EMISSION" if (er+eg+eb) > 0 else ""
    valid_kw = f"m_ValidKeywords:{em_kw}" if em_kw else "m_ValidKeywords: []"
    mat_yaml = f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!114 &-8363384787373660979
MonoBehaviour:
  m_ObjectHideFlags: 11
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 0}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: d0353a89b1f911e48b9e16bdc9f2e058, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: Unity.RenderPipelines.Universal.Editor::UnityEditor.Rendering.Universal.AssetVersion
  version: 10
--- !u!21 &2100000
Material:
  serializedVersion: 8
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {mname}
  m_Shader: {{fileID: 4800000, guid: 933532a4fcc9baf4fa0491de14d08ed7, type: 3}}
  m_Parent: {{fileID: 0}}
  m_ModifiedSerializedProperties: 0
  {valid_kw}
  m_InvalidKeywords: []
  m_LightmapFlags: 4
  m_EnableInstancingVariants: 0
  m_DoubleSidedGI: 0
  m_CustomRenderQueue: -1
  stringTagMap:
    RenderType: Opaque
  disabledShaderPasses:
  - MOTIONVECTORS
  m_LockedProperties: 
  m_SavedProperties:
    serializedVersion: 3
    m_TexEnvs: []
    m_Ints: []
    m_Floats:
    - _Metallic: {met:.3f}
    - _Smoothness: {smooth:.3f}
    - _ReceiveShadows: 1
    - _EnvironmentReflections: 1
    - _SpecularHighlights: 1
    - _Surface: 0
    - _WorkflowMode: 1
    - _ZWrite: 1
    m_Colors:
    - _BaseColor: {{r: {r:.4f}, g: {g:.4f}, b: {b:.4f}, a: {a:.4f}}}
    - _Color: {{r: {r:.4f}, g: {g:.4f}, b: {b:.4f}, a: {a:.4f}}}
    - _EmissionColor: {{r: {er:.4f}, g: {eg:.4f}, b: {eb:.4f}, a: 1}}
  m_BuildTextureStacks: []
  m_AllowLocking: 1
"""
    with open(f"{mat_dir}/{mname}.mat", "w", encoding="utf-8") as f:
        f.write(mat_yaml)
    with open(f"{mat_dir}/{mname}.mat.meta", "w", encoding="utf-8") as f:
        f.write(f"fileFormatVersion: 2\nguid: {mguid}\nNativeFormatImporter:\n  externalObjects: {{}}\n  mainObjectFileID: 2100000\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n")
    ext_entries.append(f"""  - first:
      type: UnityEngine:Material
      assembly: UnityEngine.CoreModule
      name: {mname}
    second: {{fileID: 2100000, guid: {mguid}, type: 2}}""")

# 2. Write Gym_TabletStand.fbx.meta
fbx_meta = "Assets/Bomio_Exercises/Equipment/Gym_TabletStand.fbx.meta"
ext_block = "\n".join(ext_entries)
with open(fbx_meta, "w", encoding="utf-8") as f:
    f.write(f"""fileFormatVersion: 2
guid: {FBX_GUID}
ModelImporter:
  serializedVersion: 24600
  internalIDToNameTable: []
  externalObjects:
{ext_block}
  materials:
    materialImportMode: 2
    materialName: 0
    materialSearch: 1
    materialLocation: 1
    searchTexturesGlobally: 0
  animations:
    legacyGenerateAnimations: 4
    clipAnimations: []
    isReadable: 0
  meshes:
    globalScale: 1
    useFileUnits: 1
    useFileScale: 1
  importAnimation: 0
  animationType: 0
  userData: 
  assetBundleName: 
  assetBundleVariant: 
""")
print("Created Gym_TabletStand.fbx.meta + 4 URP materials.")

# 3. Place 11 3D Tablet Stands under 04_Equipment / Gym_TabletStands in AIGym.unity
SCENE_PATH = "Assets/Scenes/AIGym.unity"
with open(SCENE_PATH, "r", encoding="utf-8") as f:
    text = f.read()

if "Gym_TabletStands" not in text:
    # (Name, machineIndex, X, Z, RotY)
    # Placed right beside each machine facing the walkway!
    stands = [
        ("TabletStand_ChestPress",    0,  -8.4, 12.6,  90.0),
        ("TabletStand_BenchPress",    1,   1.2, 14.7, -90.0),
        ("TabletStand_LatPulldown",   2,  -5.8, -1.5,   0.0),
        ("TabletStand_PullUpBar",     3,  -8.4, 18.2,  90.0),
        ("TabletStand_ArmCurl",       4,  -1.1,  6.7,  90.0),
        ("TabletStand_PowerLegPress", 5,  -0.8, 14.8,  90.0),
        ("TabletStand_LegExtension",  6,  -8.4,  8.1,  90.0),
        ("TabletStand_LyingLegCurl",  7,  -1.1, 10.8,  90.0),
        ("TabletStand_HipAdduction",  8,  -1.1,  2.7,  90.0),
        ("TabletStand_VSquat",        9,   1.1, 10.8, -90.0),
        ("TabletStand_StairClimber", 10,   1.1,  6.7, -90.0),
    ]

    root_go, root_tr = 1997000001, 1997000002
    child_trs = []
    blocks = []

    for i, (sname, midx, px, pz, ry) in enumerate(stands):
        base = 1997001000 + i * 10
        pi_id, go_id, tr_id, bc_id, sc_id = base+1, base+2, base+3, base+4, base+5
        child_trs.append(f"  - {{fileID: {tr_id}}}")
        rad = math.radians(ry)
        qw, qy = math.cos(rad/2.0), math.sin(rad/2.0)
        blocks.append(f"""--- !u!1001 &{pi_id}
PrefabInstance:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_Modification:
    serializedVersion: 3
    m_TransformParent: {{fileID: {root_tr}}}
    m_Modifications:
    - target: {{fileID: -8679921383154817045, guid: {FBX_GUID}, type: 3}}
      propertyPath: m_LocalScale.x
      value: 1.15
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {FBX_GUID}, type: 3}}
      propertyPath: m_LocalScale.y
      value: 1.15
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {FBX_GUID}, type: 3}}
      propertyPath: m_LocalScale.z
      value: 1.15
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {FBX_GUID}, type: 3}}
      propertyPath: m_LocalPosition.x
      value: {px}
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {FBX_GUID}, type: 3}}
      propertyPath: m_LocalPosition.y
      value: 0
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {FBX_GUID}, type: 3}}
      propertyPath: m_LocalPosition.z
      value: {pz}
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {FBX_GUID}, type: 3}}
      propertyPath: m_LocalRotation.w
      value: {qw:.7f}
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {FBX_GUID}, type: 3}}
      propertyPath: m_LocalRotation.x
      value: 0
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {FBX_GUID}, type: 3}}
      propertyPath: m_LocalRotation.y
      value: {qy:.7f}
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {FBX_GUID}, type: 3}}
      propertyPath: m_LocalRotation.z
      value: 0
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {FBX_GUID}, type: 3}}
      propertyPath: m_LocalEulerAnglesHint.x
      value: 0
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {FBX_GUID}, type: 3}}
      propertyPath: m_LocalEulerAnglesHint.y
      value: {ry}
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {FBX_GUID}, type: 3}}
      propertyPath: m_LocalEulerAnglesHint.z
      value: 0
      objectReference: {{fileID: 0}}
    - target: {{fileID: 919132149155446097, guid: {FBX_GUID}, type: 3}}
      propertyPath: m_Name
      value: {sname}
      objectReference: {{fileID: 0}}
    m_RemovedComponents: []
    m_RemovedGameObjects: []
    m_AddedGameObjects: []
    m_AddedComponents:
    - targetCorrespondingSourceObject: {{fileID: 919132149155446097, guid: {FBX_GUID}, type: 3}}
      insertIndex: -1
      addedObject: {{fileID: {bc_id}}}
    - targetCorrespondingSourceObject: {{fileID: 919132149155446097, guid: {FBX_GUID}, type: 3}}
      insertIndex: -1
      addedObject: {{fileID: {sc_id}}}
  m_SourcePrefab: {{fileID: 100100000, guid: {FBX_GUID}, type: 3}}
--- !u!1 &{go_id} stripped
GameObject:
  m_CorrespondingSourceObject: {{fileID: 919132149155446097, guid: {FBX_GUID}, type: 3}}
  m_PrefabInstance: {{fileID: {pi_id}}}
  m_PrefabAsset: {{fileID: 0}}
--- !u!4 &{tr_id} stripped
Transform:
  m_CorrespondingSourceObject: {{fileID: -8679921383154817045, guid: {FBX_GUID}, type: 3}}
  m_PrefabInstance: {{fileID: {pi_id}}}
  m_PrefabAsset: {{fileID: 0}}
--- !u!65 &{bc_id}
BoxCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go_id}}}
  m_Material: {{fileID: 0}}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_LayerOverridePriority: 0
  m_IsTrigger: 0
  m_ProvidesContacts: 0
  m_Enabled: 1
  serializedVersion: 3
  m_Size: {{x: 0.45, y: 1.45, z: 0.45}}
  m_Center: {{x: 0, y: 0.72, z: 0}}
--- !u!114 &{sc_id}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go_id}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {INTERACT_GUID}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: Assembly-CSharp::TabletStandInteract
  machineIndex: {midx}
  interactRange: 2.8""")

    ch_yaml = "\n".join(child_trs)
    root_yaml = f"""--- !u!1 &{root_go}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {root_tr}}}
  m_Layer: 0
  m_Name: Gym_TabletStands
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &{root_tr}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {root_go}}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children:
{ch_yaml}
  m_Father: {{fileID: 1990010008}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}"""

    # Parent Gym_TabletStands under 04_Equipment (1990010008)
    pat_eq = r'(--- !u!4 &1990010008\nTransform:.*?m_Children:\n)(.*?)(  m_Father:)'
    m_eq = re.search(pat_eq, text, re.DOTALL)
    assert m_eq, "04_Equipment not found"
    text = text[:m_eq.end(2)] + f"  - {{fileID: {root_tr}}}\n" + text[m_eq.end(2):]

    marker_roots = "--- !u!1660057539 &9223372036854775807"
    idx = text.find(marker_roots)
    assert idx != -1
    text = text[:idx] + root_yaml + "\n" + "\n".join(blocks) + "\n" + text[idx:]

    with open(SCENE_PATH, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Placed {len(stands)} 3D Tablet Stands under 04_Equipment/Gym_TabletStands!")

ids = re.findall(r'^--- !u!\d+ &(-?\d+)', text, re.M)
dups = {k: v for k, v in Counter(ids).items() if v > 1}
print("Duplicate IDs:", dups)
