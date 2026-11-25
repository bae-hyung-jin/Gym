import re

# Read template from Anim_Bomio_ArmCurl.fbx.meta
with open('Assets/Bomio_Exercises/Animations/Anim_Bomio_ArmCurl.fbx.meta', 'r', encoding='utf-8') as f:
    armcurl_meta = f.read()

# Extract humanDescription section
m_hd = re.search(r'(  humanDescription:.*?\n  lastHumanDescriptionAvatarSource: \{fileID: 9000000, guid: 69b1e1903886de948b8ec6db7917ac00, type: 3\}\n  autoGenerateAvatarMappingIfUnspecified: 1\n  animationType: 3\n  humanoidOversampling: 1\n  avatarSetup: 2\n  addHumanoidExtraRootOnlyWhenUsingAvatar: 1\n  importBlendShapeDeformPercent: 1\n  remapMaterialsIfMaterialImportModeIsNone: 0\n  additionalBone: 0)', armcurl_meta, re.DOTALL)
human_section = m_hd.group(1)

humanoid_clips = [
    ("HipAdduction", 61, "77459d3cf7b4e7248b37afe88fc3d88c"),
    ("LyingLegCurl", 61, "520bd94e0378d494abecbaa294f0b7ae"),
    ("BenchPress", 61, "0fde24130c268b44f90a3d701255afa3"),
    ("StairClimber", 121, "9246ece969d94f242a66e16209226941"),
    ("VSquat", 61, "7d93aab32e90eea4bb94ec9c0b579e15"),
]

for name, last_frame, guid in humanoid_clips:
    path = f'Assets/Bomio_Exercises/Animations/Anim_Bomio_{name}.fbx.meta'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace clipAnimations
    clip_block = f"""    clipAnimations:
    - serializedVersion: 16
      name: {name}
      takeName: Scene
      internalID: -623603649343465320
      firstFrame: 1
      lastFrame: {last_frame}
      wrapMode: 0
      orientationOffsetY: 0
      level: 0
      cycleOffset: 0
      loop: 0
      hasAdditiveReferencePose: 0
      loopTime: 1
      loopBlend: 0
      loopBlendOrientation: 1
      loopBlendPositionY: 1
      loopBlendPositionXZ: 1
      keepOriginalOrientation: 1
      keepOriginalPositionY: 1
      keepOriginalPositionXZ: 1
      heightFromFeet: 0
      mirror: 0
      bodyMask: 01000000010000000100000001000000010000000100000001000000010000000100000001000000010000000100000001000000u
      curves: []
      events: []
      transformMask: []
      maskType: 3
      maskSource: {{instanceID: 0}}
      additiveReferencePoseFrame: 0"""
    
    # Replace clipAnimations: []
    content = re.sub(r'    clipAnimations:\s*\[\]', clip_block, content)
    
    # Replace humanDescription / animationType section
    pattern = r'  humanDescription:.*?\n  additionalBone: \d+'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, human_section, content, flags=re.DOTALL)
    else:
        # If not present, replace up to additionalBone
        pattern2 = r'  lastHumanDescriptionAvatarSource:.*?\n  additionalBone: \d+'
        content = re.sub(pattern2, human_section, content, flags=re.DOTALL)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {path}")

# Now machine clips
machine_clips = [
    ("HipAdduction", 61, "5e747f8d40d4d384b9e3f056ba75b0f9"),
    ("LyingLegCurl", 61, "f150b197a5d7f494783ab502464ca9de"),
    ("BenchPress", 61, "251fed0e6365bc642be534b7bc743a07"),
    ("StairClimber", 121, "d0f40caba3e273540a60e6bd9164e244"),
    ("VSquat", 61, "7b75d5901151da942990e2b700013d98"),
]

for name, last_frame, guid in machine_clips:
    path = f'Assets/Bomio_Exercises/Animations/Anim_Bomio_{name}_WithMachine.fbx.meta'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    clip_block = f"""    clipAnimations:
    - serializedVersion: 16
      name: Scene
      takeName: Scene
      internalID: -623603649343465320
      firstFrame: 1
      lastFrame: {last_frame}
      wrapMode: 0
      orientationOffsetY: 0
      level: 0
      cycleOffset: 0
      loop: 0
      hasAdditiveReferencePose: 0
      loopTime: 1
      loopBlend: 0
      loopBlendOrientation: 0
      loopBlendPositionY: 0
      loopBlendPositionXZ: 0
      keepOriginalOrientation: 0
      keepOriginalPositionY: 1
      keepOriginalPositionXZ: 0
      heightFromFeet: 0
      mirror: 0
      bodyMask: 01000000010000000100000001000000010000000100000001000000010000000100000001000000010000000100000001000000u
      curves: []
      events: []
      transformMask: []
      maskType: 3
      maskSource: {{instanceID: 0}}
      additiveReferencePoseFrame: 0"""
    
    content = re.sub(r'    clipAnimations:\s*\[\]', clip_block, content)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {path}")
