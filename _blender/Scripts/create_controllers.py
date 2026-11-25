import uuid

controllers = [
    ("HipAdduction_WithMachine", "5e747f8d40d4d384b9e3f056ba75b0f9", "81a2c3d4e5f64789a0b1c2d3e4f50011"),
    ("LyingLegCurl_WithMachine", "f150b197a5d7f494783ab502464ca9de", "81a2c3d4e5f64789a0b1c2d3e4f50012"),
    ("BenchPress_WithMachine", "251fed0e6365bc642be534b7bc743a07", "81a2c3d4e5f64789a0b1c2d3e4f50013"),
    ("StairClimber_WithMachine", "d0f40caba3e273540a60e6bd9164e244", "81a2c3d4e5f64789a0b1c2d3e4f50014"),
    ("VSquat_WithMachine", "7b75d5901151da942990e2b700013d98", "81a2c3d4e5f64789a0b1c2d3e4f50015"),
]

controller_tmpl = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!1102 &-1844476341180057633
AnimatorState:
  serializedVersion: 6
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: Scene
  m_Speed: 1
  m_CycleOffset: 0
  m_Transitions: []
  m_StateMachineBehaviours: []
  m_Position: {{x: 50, y: 50, z: 0}}
  m_IKOnFeet: 0
  m_WriteDefaultValues: 1
  m_Mirror: 0
  m_SpeedParameterActive: 0
  m_MirrorParameterActive: 0
  m_CycleOffsetParameterActive: 0
  m_TimeParameterActive: 0
  m_Motion: {{fileID: -623603649343465320, guid: {motion_guid}, type: 3}}
  m_Tag: 
  m_SpeedParameter: 
  m_MirrorParameter: 
  m_CycleOffsetParameter: 
  m_TimeParameter: 
--- !u!91 &9100000
AnimatorController:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {name}
  serializedVersion: 6
  m_AnimatorParameters: []
  m_AnimatorLayers:
  - serializedVersion: 5
    m_Name: Base Layer
    m_StateMachine: {{fileID: 843377053316915813}}
    m_Mask: {{fileID: 0}}
    m_Motions: []
    m_Behaviours: []
    m_BlendingMode: 0
    m_SyncedLayerIndex: -1
    m_DefaultWeight: 0
    m_IKPass: 0
    m_SyncedLayerAffectsTiming: 0
    m_Controller: {{fileID: 9100000}}
  m_EvaluateTransitionsOnStart: 1
--- !u!1107 &843377053316915813
AnimatorStateMachine:
  serializedVersion: 7
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: Base Layer
  m_ChildStates:
  - serializedVersion: 1
    m_State: {{fileID: -1844476341180057633}}
    m_Position: {{x: 200, y: 0, z: 0}}
  m_ChildStateMachines: []
  m_AnyStateTransitions: []
  m_EntryTransitions: []
  m_StateMachineTransitions: {{}}
  m_StateMachineBehaviours: []
  m_AnyStatePosition: {{x: 50, y: 20, z: 0}}
  m_EntryPosition: {{x: 50, y: 120, z: 0}}
  m_ExitPosition: {{x: 800, y: 120, z: 0}}
  m_ParentStateMachinePosition: {{x: 800, y: 20, z: 0}}
  m_DefaultState: {{fileID: -1844476341180057633}}
"""

meta_tmpl = """fileFormatVersion: 2
guid: {guid}
NativeFormatImporter:
  externalObjects: {{}}
  mainObjectFileID: 9100000
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""

for name, motion_guid, ctrl_guid in controllers:
    ctrl_path = f"Assets/Bomio_Exercises/Equipment/{name}.controller"
    meta_path = f"{ctrl_path}.meta"
    
    with open(ctrl_path, "w", encoding="utf-8") as f:
        f.write(controller_tmpl.format(name=name, motion_guid=motion_guid))
    
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(meta_tmpl.format(guid=ctrl_guid))
    
    print(f"Created {ctrl_path} and meta (guid: {ctrl_guid})")
