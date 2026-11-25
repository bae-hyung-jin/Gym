import re

SCENE_PATH = 'Assets/Scenes/AIGym.unity'

with open(SCENE_PATH, 'r', encoding='utf-8') as f:
    scene_text = f.read()

# Machines to add
# (Name, KoreanName, AnimState, FBX_Guid, Ctrl_Guid, PI_ID, GO_ID, TR_ID, AN_ID, ES_ID, BC_ID, PosX, PosY, PosZ, RotY, CamDist, CamYaw, BoxSize, BoxCenter)
machines = [
    (
        "HipAdduction_Ani",
        "\\uD799 \\uC5B4\\uB355\\uC158",
        "HipAdduction",
        "5e747f8d40d4d384b9e3f056ba75b0f9",
        "81a2c3d4e5f64789a0b1c2d3e4f50011",
        1994004001, 1994004002, 1994004003, 1994004004, 1994004005, 1995000010,
        -2.5, 0.0, 1.5, -90.0,
        3.8, 0.0,
        "{x: 1.3, y: 1.5, z: 1.4}", "{x: 0, y: 0.75, z: 0}"
    ),
    (
        "LyingLegCurl_Ani",
        "\\uB77C\\uC789 \\uB808\\uADF8\\uCEEC",
        "LyingLegCurl",
        "f150b197a5d7f494783ab502464ca9de",
        "81a2c3d4e5f64789a0b1c2d3e4f50012",
        1994005001, 1994005002, 1994005003, 1994005004, 1994005005, 1995000011,
        -2.5, 0.0, 9.5, -90.0,
        3.8, 0.0,
        "{x: 1.2, y: 1.3, z: 2.0}", "{x: 0, y: 0.65, z: 0}"
    ),
    (
        "BenchPress_Ani",
        "\\uD50C\\uB808\\uC774\\uD2B8 \\uB85C\\uB514\\uB4DC \\uBD84\\uCE58\\uD504\\uB808\\uC2A4",
        "BenchPress",
        "251fed0e6365bc642be534b7bc743a07",
        "81a2c3d4e5f64789a0b1c2d3e4f50013",
        1994006001, 1994006002, 1994006003, 1994006004, 1994006005, 1995000012,
        2.5, 0.0, 13.5, 90.0,
        4.0, 0.0,
        "{x: 1.5, y: 1.4, z: 1.8}", "{x: 0, y: 0.7, z: 0}"
    ),
    (
        "StairClimber_Ani",
        "\\uCC9C\\uAD6D\\uC758 \\uACC4\\uB2E8 (\\uC2A4\\uD158\\uBC00)",
        "StairClimber",
        "d0f40caba3e273540a60e6bd9164e244",
        "81a2c3d4e5f64789a0b1c2d3e4f50014",
        1994007001, 1994007002, 1994007003, 1994007004, 1994007005, 1995000013,
        2.5, 0.0, 5.5, 90.0,
        4.2, 0.0,
        "{x: 1.2, y: 2.2, z: 1.8}", "{x: 0, y: 1.1, z: 0}"
    ),
    (
        "VSquat_Ani",
        "V-\\uC2A4\\uCFFC\\uD2B8",
        "VSquat",
        "7b75d5901151da942990e2b700013d98",
        "81a2c3d4e5f64789a0b1c2d3e4f50015",
        1994008001, 1994008002, 1994008003, 1994008004, 1994008005, 1995000014,
        2.5, 0.0, 9.5, 90.0,
        4.2, 0.0,
        "{x: 1.4, y: 1.8, z: 2.2}", "{x: 0, y: 0.9, z: 0}"
    ),
]

# Generate YAML blocks
new_blocks = []
new_children_refs = []

for m in machines:
    name, kor_name, anim_state, fbx_guid, ctrl_guid, pi_id, go_id, tr_id, an_id, es_id, bc_id, px, py, pz, ry, cam_dist, cam_yaw, box_size, box_center = m
    
    # Calculate quaternion for Y rotation
    import math
    rad = math.radians(ry)
    qw = math.cos(rad / 2.0)
    qy = math.sin(rad / 2.0)
    
    new_children_refs.append(f"  - {{fileID: {tr_id}}}")
    
    block = f"""--- !u!1001 &{pi_id}
PrefabInstance:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_Modification:
    serializedVersion: 3
    m_TransformParent: {{fileID: 1990010008}}
    m_Modifications:
    - target: {{fileID: -8679921383154817045, guid: {fbx_guid}, type: 3}}
      propertyPath: m_LocalScale.x
      value: 1.28
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {fbx_guid}, type: 3}}
      propertyPath: m_LocalScale.y
      value: 1.28
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {fbx_guid}, type: 3}}
      propertyPath: m_LocalScale.z
      value: 1.28
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {fbx_guid}, type: 3}}
      propertyPath: m_LocalPosition.x
      value: {px}
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {fbx_guid}, type: 3}}
      propertyPath: m_LocalPosition.y
      value: {py}
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {fbx_guid}, type: 3}}
      propertyPath: m_LocalPosition.z
      value: {pz}
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {fbx_guid}, type: 3}}
      propertyPath: m_LocalRotation.w
      value: {qw:.7f}
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {fbx_guid}, type: 3}}
      propertyPath: m_LocalRotation.x
      value: 0
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {fbx_guid}, type: 3}}
      propertyPath: m_LocalRotation.y
      value: {qy:.7f}
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {fbx_guid}, type: 3}}
      propertyPath: m_LocalRotation.z
      value: 0
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {fbx_guid}, type: 3}}
      propertyPath: m_LocalEulerAnglesHint.x
      value: 0
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {fbx_guid}, type: 3}}
      propertyPath: m_LocalEulerAnglesHint.y
      value: {ry}
      objectReference: {{fileID: 0}}
    - target: {{fileID: -8679921383154817045, guid: {fbx_guid}, type: 3}}
      propertyPath: m_LocalEulerAnglesHint.z
      value: 0
      objectReference: {{fileID: 0}}
    - target: {{fileID: 919132149155446097, guid: {fbx_guid}, type: 3}}
      propertyPath: m_Name
      value: {name}
      objectReference: {{fileID: 0}}
    m_RemovedComponents: []
    m_RemovedGameObjects: []
    m_AddedGameObjects: []
    m_AddedComponents:
    - targetCorrespondingSourceObject: {{fileID: 919132149155446097, guid: {fbx_guid}, type: 3}}
      insertIndex: -1
      addedObject: {{fileID: {an_id}}}
    - targetCorrespondingSourceObject: {{fileID: 919132149155446097, guid: {fbx_guid}, type: 3}}
      insertIndex: -1
      addedObject: {{fileID: {es_id}}}
    - targetCorrespondingSourceObject: {{fileID: 919132149155446097, guid: {fbx_guid}, type: 3}}
      insertIndex: -1
      addedObject: {{fileID: {bc_id}}}
  m_SourcePrefab: {{fileID: 100100000, guid: {fbx_guid}, type: 3}}
--- !u!1 &{go_id} stripped
GameObject:
  m_CorrespondingSourceObject: {{fileID: 919132149155446097, guid: {fbx_guid}, type: 3}}
  m_PrefabInstance: {{fileID: {pi_id}}}
  m_PrefabAsset: {{fileID: 0}}
--- !u!4 &{tr_id} stripped
Transform:
  m_CorrespondingSourceObject: {{fileID: -8679921383154817045, guid: {fbx_guid}, type: 3}}
  m_PrefabInstance: {{fileID: {pi_id}}}
  m_PrefabAsset: {{fileID: 0}}
--- !u!95 &{an_id}
Animator:
  serializedVersion: 7
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go_id}}}
  m_Enabled: 1
  m_Avatar: {{fileID: 0}}
  m_Controller: {{fileID: 9100000, guid: {ctrl_guid}, type: 2}}
  m_CullingMode: 0
  m_UpdateMode: 0
  m_ApplyRootMotion: 0
  m_LinearVelocityBlending: 0
  m_StabilizeFeet: 0
  m_AnimatePhysics: 0
  m_WarningMessage: 
  m_HasTransformHierarchy: 1
  m_AllowConstantClipSamplingOptimization: 1
  m_KeepAnimatorStateOnDisable: 0
  m_WriteDefaultValuesOnDisable: 0
--- !u!114 &{es_id}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go_id}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: e7fb8faf6e560574fb24166fc533a13f, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: Assembly-CSharp::ExerciseStation
  font: {{fileID: 12800000, guid: 2f82c5addb6e6e64bb1fc2c87cf7f09e, type: 3}}
  player: {{fileID: 920393823}}
  machine: {{fileID: {an_id}}}
  seatPoint: {{fileID: {tr_id}}}
  facing: {{fileID: {tr_id}}}
  trainer: {{fileID: 2051067938}}
  machineName: "{kor_name}"
  useRange: 2.8
  exitDistance: 2
  pullSpeed: 1.4
  pose: {{fileID: 920393829}}
  machineAnimState: Scene
  playerAnimState: {anim_state}
  hipsOffsetLocal: {{x: 0, y: 0, z: 0}}
  camDistance: {cam_dist}
  camYawOffset: {cam_yaw}
  fullPullTime: 0.5
  targetReps: 10
  promptBanner: {{fileID: 1992000006}}
  promptLabel: {{fileID: 1992000021}}
  exerciseHudRoot: {{fileID: 1992000022}}
  hudTitleText: {{fileID: 1992000031}}
  hudSubText: {{fileID: 1992000035}}
  strengthFill: {{fileID: 1992000051}}
  strengthValueText: {{fileID: 1992000055}}
  pullButton: {{fileID: 1992000062}}
  pullButtonLabel: {{fileID: 1992000066}}
  stopButton: {{fileID: 1992000075}}
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
  m_Size: {box_size}
  m_Center: {box_center}"""
    
    new_blocks.append(block)

# 1. Update m_Children in Transform 1990010008
pattern_tr = r'(--- !u!4 &1990010008\nTransform:.*?m_Children:\n)(.*?)(  m_Father:)'
m_tr = re.search(pattern_tr, scene_text, re.DOTALL)
if m_tr:
    current_children = m_tr.group(2)
    updated_children = current_children + "\n".join(new_children_refs) + "\n"
    scene_text = scene_text[:m_tr.start(2)] + updated_children + scene_text[m_tr.end(2):]
    print("Appended child transforms to 04_Equipment.")
else:
    print("ERROR: Transform 1990010008 not found!")

# 2. Append all new blocks to scene_text
scene_text = scene_text.rstrip() + "\n" + "\n".join(new_blocks) + "\n"

with open(SCENE_PATH, 'w', encoding='utf-8') as f:
    f.write(scene_text)

print(f"Successfully added {len(machines)} machines to {SCENE_PATH}!")
