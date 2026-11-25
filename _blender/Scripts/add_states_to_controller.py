path = 'Assets/Starter Assets/Runtime/ThirdPersonController/Character/Animations/StarterAssetsThirdPerson.controller'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add to m_ChildStates
target_child = """  - serializedVersion: 1
    m_State: {fileID: 910000105}
    m_Position: {x: 580, y: 600, z: 0}"""

new_children = """  - serializedVersion: 1
    m_State: {fileID: 910000105}
    m_Position: {x: 580, y: 600, z: 0}
  - serializedVersion: 1
    m_State: {fileID: 910000106}
    m_Position: {x: 580, y: 660, z: 0}
  - serializedVersion: 1
    m_State: {fileID: 910000107}
    m_Position: {x: 580, y: 720, z: 0}
  - serializedVersion: 1
    m_State: {fileID: 910000108}
    m_Position: {x: 580, y: 780, z: 0}
  - serializedVersion: 1
    m_State: {fileID: 910000109}
    m_Position: {x: 580, y: 840, z: 0}
  - serializedVersion: 1
    m_State: {fileID: 910000110}
    m_Position: {x: 580, y: 900, z: 0}"""

if target_child in content:
    content = content.replace(target_child, new_children, 1)
    print("Added child states to controller.")
else:
    print("WARNING: target_child not found!")

# 2. Add AnimatorState definitions
new_states = """--- !u!1102 &910000106
AnimatorState:
  serializedVersion: 6
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_Name: HipAdduction
  m_Speed: 1
  m_CycleOffset: 0
  m_Transitions: []
  m_StateMachineBehaviours: []
  m_Position: {x: 50, y: 50, z: 0}
  m_IKOnFeet: 0
  m_WriteDefaultValues: 1
  m_Mirror: 0
  m_SpeedParameterActive: 0
  m_MirrorParameterActive: 0
  m_CycleOffsetParameterActive: 0
  m_TimeParameterActive: 0
  m_Motion: {fileID: -623603649343465320, guid: 77459d3cf7b4e7248b37afe88fc3d88c, type: 3}
  m_Tag: 
  m_SpeedParameter: 
  m_MirrorParameter: 
  m_CycleOffsetParameter: 
  m_TimeParameter: 
--- !u!1102 &910000107
AnimatorState:
  serializedVersion: 6
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_Name: LyingLegCurl
  m_Speed: 1
  m_CycleOffset: 0
  m_Transitions: []
  m_StateMachineBehaviours: []
  m_Position: {x: 50, y: 50, z: 0}
  m_IKOnFeet: 0
  m_WriteDefaultValues: 1
  m_Mirror: 0
  m_SpeedParameterActive: 0
  m_MirrorParameterActive: 0
  m_CycleOffsetParameterActive: 0
  m_TimeParameterActive: 0
  m_Motion: {fileID: -623603649343465320, guid: 520bd94e0378d494abecbaa294f0b7ae, type: 3}
  m_Tag: 
  m_SpeedParameter: 
  m_MirrorParameter: 
  m_CycleOffsetParameter: 
  m_TimeParameter: 
--- !u!1102 &910000108
AnimatorState:
  serializedVersion: 6
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_Name: BenchPress
  m_Speed: 1
  m_CycleOffset: 0
  m_Transitions: []
  m_StateMachineBehaviours: []
  m_Position: {x: 50, y: 50, z: 0}
  m_IKOnFeet: 0
  m_WriteDefaultValues: 1
  m_Mirror: 0
  m_SpeedParameterActive: 0
  m_MirrorParameterActive: 0
  m_CycleOffsetParameterActive: 0
  m_TimeParameterActive: 0
  m_Motion: {fileID: -623603649343465320, guid: 0fde24130c268b44f90a3d701255afa3, type: 3}
  m_Tag: 
  m_SpeedParameter: 
  m_MirrorParameter: 
  m_CycleOffsetParameter: 
  m_TimeParameter: 
--- !u!1102 &910000109
AnimatorState:
  serializedVersion: 6
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_Name: StairClimber
  m_Speed: 1
  m_CycleOffset: 0
  m_Transitions: []
  m_StateMachineBehaviours: []
  m_Position: {x: 50, y: 50, z: 0}
  m_IKOnFeet: 0
  m_WriteDefaultValues: 1
  m_Mirror: 0
  m_SpeedParameterActive: 0
  m_MirrorParameterActive: 0
  m_CycleOffsetParameterActive: 0
  m_TimeParameterActive: 0
  m_Motion: {fileID: -623603649343465320, guid: 9246ece969d94f242a66e16209226941, type: 3}
  m_Tag: 
  m_SpeedParameter: 
  m_MirrorParameter: 
  m_CycleOffsetParameter: 
  m_TimeParameter: 
--- !u!1102 &910000110
AnimatorState:
  serializedVersion: 6
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_Name: VSquat
  m_Speed: 1
  m_CycleOffset: 0
  m_Transitions: []
  m_StateMachineBehaviours: []
  m_Position: {x: 50, y: 50, z: 0}
  m_IKOnFeet: 0
  m_WriteDefaultValues: 1
  m_Mirror: 0
  m_SpeedParameterActive: 0
  m_MirrorParameterActive: 0
  m_CycleOffsetParameterActive: 0
  m_TimeParameterActive: 0
  m_Motion: {fileID: -623603649343465320, guid: 7d93aab32e90eea4bb94ec9c0b579e15, type: 3}
  m_Tag: 
  m_SpeedParameter: 
  m_MirrorParameter: 
  m_CycleOffsetParameter: 
  m_TimeParameter: 
"""

content = content.rstrip() + "\n" + new_states

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated StarterAssetsThirdPerson.controller successfully.")
