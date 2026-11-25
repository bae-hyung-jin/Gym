import os, re, hashlib

TEX_GUIDS = {
    "Ref_HipAdduction_Texture":     "3254a5ccf442b81419145bc86363faac",
    "WeightStack_Numbers_Tex":      "22ba068a03c3dc946a3309979d0c6971",
    "Ref_LyingLegCurl_Texture":     "a139db10bc59cf747bfdc1d94d53a79e",
    "WeightStack_Curl_Numbers_Tex": "48fdbb9dd27325f47a396c825d2b585b",
    "Ref_BenchPress_Texture":       "50c21ce51f47d6a4a8b1bff61a2e539d",
    "Ref_StairClimber_Texture":     "a3f98b8bf682b884c97a80092169905d",
    "StairClimber_Decals_Atlas":    "72d1e0f5b96cbd548963c781164fa0df",
    "Ref_VSquat_Texture":           "9772cb69fc274a344ac87899b34df649",
    "VSquat_Decals_Atlas":          "4220366d3263c9242be5c53d971babc4",
}

BOMIO_MATS = {
    "M_Bomio_Hair":        "92b20004a1c24d3e8f0123456789cd04",
    "M_Bomio_Skin":        "92b20003a1c24d3e8f0123456789cd03",
    "M_Bomio_Sneaker":     "92b20008a1c24d3e8f0123456789cd08",
    "M_Bomio_TrackBlack":  "92b20007a1c24d3e8f0123456789cd07",
    "M_Bomio_TrackJacket": "92b20005a1c24d3e8f0123456789cd05",
    "M_Bomio_TrackPants":  "92b20006a1c24d3e8f0123456789cd06",
    "M_Bomio_ZipperMetal": "92b20009a1c24d3e8f0123456789cd09",
}

# (mat_name, tex_name_or_None, base_color_rgba, metallic, roughness)
MACHINE_MATS = {
    "HipAdduction": [
        ("Mat_Bolt_PhotoTex",        "Ref_HipAdduction_Texture", (1.0, 1.0, 1.0, 1.0), 0.88, 0.20),
        ("Mat_CamMetal_PhotoTex",    "Ref_HipAdduction_Texture", (1.0, 1.0, 1.0, 1.0), 0.72, 0.32),
        ("Mat_Chrome_PhotoTex",      "Ref_HipAdduction_Texture", (1.0, 1.0, 1.0, 1.0), 0.92, 0.18),
        ("Mat_Frame_PhotoTex",       "Ref_HipAdduction_Texture", (1.0, 1.0, 1.0, 1.0), 0.35, 0.44),
        ("Mat_Leather_PhotoTex",     "Ref_HipAdduction_Texture", (1.0, 1.0, 1.0, 1.0), 0.00, 0.45),
        ("Mat_PinHole_Dark",         None,                       (0.02, 0.02, 0.025, 1.0), 0.10, 0.90),
        ("Mat_Placard_PhotoTex",     "Ref_HipAdduction_Texture", (1.0, 1.0, 1.0, 1.0), 0.08, 0.28),
        ("Mat_RedAnodized_Accent",   None,                       (0.68, 0.045, 0.055, 1.0), 0.32, 0.26),
        ("Mat_Rubber_PhotoTex",      "Ref_HipAdduction_Texture", (1.0, 1.0, 1.0, 1.0), 0.00, 0.70),
        ("Mat_TowerShroud_PhotoTex", "Ref_HipAdduction_Texture", (1.0, 1.0, 1.0, 1.0), 0.14, 0.30),
        ("Mat_WeightNumbers_Decal",  "WeightStack_Numbers_Tex",  (1.0, 1.0, 1.0, 1.0), 0.06, 0.32),
        ("Mat_WeightPlate_PhotoTex", "Ref_HipAdduction_Texture", (1.0, 1.0, 1.0, 1.0), 0.48, 0.50),
        ("Mat_WhiteTrim_PhotoTex",   "Ref_HipAdduction_Texture", (1.0, 1.0, 1.0, 1.0), 0.15, 0.30),
    ],
    "LyingLegCurl": [
        ("Mat_Bolt_PhotoTex",        "Ref_LyingLegCurl_Texture",     (1.0, 1.0, 1.0, 1.0), 0.90, 0.20),
        ("Mat_CamMetal_PhotoTex",    "Ref_LyingLegCurl_Texture",     (1.0, 1.0, 1.0, 1.0), 0.86, 0.26),
        ("Mat_Chrome_PhotoTex",      "Ref_LyingLegCurl_Texture",     (1.0, 1.0, 1.0, 1.0), 0.94, 0.16),
        ("Mat_Frame_PhotoTex",       "Ref_LyingLegCurl_Texture",     (1.0, 1.0, 1.0, 1.0), 0.38, 0.42),
        ("Mat_Leather_PhotoTex",     "Ref_LyingLegCurl_Texture",     (1.0, 1.0, 1.0, 1.0), 0.00, 0.44),
        ("Mat_PinHole_Dark",         None,                           (0.02, 0.02, 0.025, 1.0), 0.10, 0.90),
        ("Mat_Placard_PhotoTex",     "Ref_LyingLegCurl_Texture",     (1.0, 1.0, 1.0, 1.0), 0.05, 0.26),
        ("Mat_Rubber_PhotoTex",      "Ref_LyingLegCurl_Texture",     (1.0, 1.0, 1.0, 1.0), 0.00, 0.72),
        ("Mat_TowerHood_PhotoTex",   "Ref_LyingLegCurl_Texture",     (1.0, 1.0, 1.0, 1.0), 0.18, 0.36),
        ("Mat_WeightNumbers_Decal",  "WeightStack_Curl_Numbers_Tex", (1.0, 1.0, 1.0, 1.0), 0.06, 0.30),
        ("Mat_WeightPlate_PhotoTex", "Ref_LyingLegCurl_Texture",     (1.0, 1.0, 1.0, 1.0), 0.48, 0.48),
        ("Mat_YellowKnob_PhotoTex",  "Ref_LyingLegCurl_Texture",     (1.0, 1.0, 1.0, 1.0), 0.10, 0.24),
    ],
    "BenchPress": [
        ("Mat_AluminumCap_PhotoTex",  "Ref_BenchPress_Texture", (1.0, 1.0, 1.0, 1.0), 0.72, 0.22),
        ("Mat_Bolt_PhotoTex",         "Ref_BenchPress_Texture", (1.0, 1.0, 1.0, 1.0), 0.95, 0.20),
        ("Mat_ChromeHorn_PhotoTex",   "Ref_BenchPress_Texture", (1.0, 1.0, 1.0, 1.0), 0.96, 0.16),
        ("Mat_Collar_PhotoTex",       "Ref_BenchPress_Texture", (1.0, 1.0, 1.0, 1.0), 0.50, 0.38),
        ("Mat_Frame_PhotoTex",        "Ref_BenchPress_Texture", (1.0, 1.0, 1.0, 1.0), 0.35, 0.45),
        ("Mat_LeatherBench_PhotoTex", "Ref_BenchPress_Texture", (1.0, 1.0, 1.0, 1.0), 0.00, 0.46),
        ("Mat_Rubber_PhotoTex",       "Ref_BenchPress_Texture", (1.0, 1.0, 1.0, 1.0), 0.00, 0.68),
        ("Mat_SteelArm_PhotoTex",     "Ref_BenchPress_Texture", (1.0, 1.0, 1.0, 1.0), 0.92, 0.25),
    ],
    "StairClimber": [
        ("Mat_Body_Black_PhotoTex",      "Ref_StairClimber_Texture",  (1.0, 1.0, 1.0, 1.0), 0.28, 0.48),
        ("Mat_Chrome_HRSensor_PhotoTex", "Ref_StairClimber_Texture",  (1.0, 1.0, 1.0, 1.0), 0.94, 0.16),
        ("Mat_Console_ScreenUI",         "StairClimber_Decals_Atlas", (1.0, 1.0, 1.0, 1.0), 0.05, 0.22),
        ("Mat_Handrail_Rubber_PhotoTex", "Ref_StairClimber_Texture",  (1.0, 1.0, 1.0, 1.0), 0.00, 0.66),
        ("Mat_Hub_SDotLogo",             "StairClimber_Decals_Atlas", (1.0, 1.0, 1.0, 1.0), 0.15, 0.42),
        ("Mat_Red_SafetyLine",           None,                        (0.76, 0.08, 0.08, 1.0), 0.05, 0.42),
        ("Mat_Shroud_Charcoal_PhotoTex", "Ref_StairClimber_Texture",  (1.0, 1.0, 1.0, 1.0), 0.22, 0.42),
        ("Mat_Side_Wordmark",            "StairClimber_Decals_Atlas", (1.0, 1.0, 1.0, 1.0), 0.22, 0.44),
        ("Mat_Step_DiamondTread",        "StairClimber_Decals_Atlas", (1.0, 1.0, 1.0, 1.0), 0.05, 0.62),
        ("Mat_Step_Riser_PhotoTex",      "Ref_StairClimber_Texture",  (1.0, 1.0, 1.0, 1.0), 0.10, 0.52),
        ("Mat_Trim_LightGrey_PhotoTex",  "Ref_StairClimber_Texture",  (1.0, 1.0, 1.0, 1.0), 0.22, 0.38),
    ],
    "VSquat": [
        ("Mat_Bracket_DarkSteel_PhotoTex",  "Ref_VSquat_Texture",  (1.0, 1.0, 1.0, 1.0), 0.42, 0.40),
        ("Mat_Chrome_OlympicHorn_PhotoTex", "Ref_VSquat_Texture",  (1.0, 1.0, 1.0, 1.0), 0.95, 0.14),
        ("Mat_Footplate_RibbedTread",       "VSquat_Decals_Atlas", (1.0, 1.0, 1.0, 1.0), 0.38, 0.42),
        ("Mat_Frame_MatteBlack_PhotoTex",   "Ref_VSquat_Texture",  (1.0, 1.0, 1.0, 1.0), 0.35, 0.44),
        ("Mat_Leather_BlackPad",            "VSquat_Decals_Atlas", (1.0, 1.0, 1.0, 1.0), 0.00, 0.54),
        ("Mat_Nylon_WhiteBumper",           None,                  (0.82, 0.83, 0.84, 1.0), 0.00, 0.38),
        ("Mat_Rubber_GripAndFeet_PhotoTex", "Ref_VSquat_Texture",  (1.0, 1.0, 1.0, 1.0), 0.00, 0.72),
    ],
}

def det_guid(key):
    return hashlib.md5(f"bomio_new5_mat_{key}".encode("utf-8")).hexdigest()

def make_urp_mat(mat_name, tex_guid, rgba, metallic, smoothness):
    tex_ref = f"{{fileID: 2800000, guid: {tex_guid}, type: 3}}" if tex_guid else "{fileID: 0}"
    r, g, b, a = rgba
    return f"""%YAML 1.1
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
  m_Name: {mat_name}
  m_Shader: {{fileID: 4800000, guid: 933532a4fcc9baf4fa0491de14d08ed7, type: 3}}
  m_Parent: {{fileID: 0}}
  m_ModifiedSerializedProperties: 0
  m_ValidKeywords: []
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
    m_TexEnvs:
    - _BaseMap:
        m_Texture: {tex_ref}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _BumpMap:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _DetailAlbedoMap:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _DetailMask:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _DetailNormalMap:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _EmissionMap:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _MainTex:
        m_Texture: {tex_ref}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _MetallicGlossMap:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _OcclusionMap:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _ParallaxMap:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _SpecGlossMap:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - unity_Lightmaps:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - unity_LightmapsInd:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - unity_ShadowMasks:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    m_Ints: []
    m_Floats:
    - _AddPrecomputedVelocity: 0
    - _AlphaClip: 0
    - _AlphaToMask: 0
    - _Blend: 0
    - _BlendModePreserveSpecular: 1
    - _BumpScale: 1
    - _ClearCoatMask: 0
    - _ClearCoatSmoothness: 0
    - _Cull: 2
    - _Cutoff: 0.5
    - _DetailAlbedoMapScale: 1
    - _DetailNormalMapScale: 1
    - _DstBlend: 0
    - _DstBlendAlpha: 0
    - _EnvironmentReflections: 1
    - _GlossMapScale: 0
    - _Glossiness: 0
    - _GlossyReflections: 0
    - _Metallic: {metallic:.3f}
    - _OcclusionStrength: 1
    - _Parallax: 0.005
    - _QueueOffset: 0
    - _ReceiveShadows: 1
    - _ScreenSpaceReflections: 1
    - _ScreenSpaceReflectionsContributeTransparent: 1
    - _Smoothness: {smoothness:.3f}
    - _SmoothnessTextureChannel: 0
    - _SpecularHighlights: 1
    - _SrcBlend: 1
    - _SrcBlendAlpha: 1
    - _Surface: 0
    - _WorkflowMode: 1
    - _XRMotionVectorsPass: 1
    - _ZWrite: 1
    m_Colors:
    - _BaseColor: {{r: {r:.4f}, g: {g:.4f}, b: {b:.4f}, a: {a:.4f}}}
    - _Color: {{r: {r:.4f}, g: {g:.4f}, b: {b:.4f}, a: {a:.4f}}}
    - _EmissionColor: {{r: 0, g: 0, b: 0, a: 1}}
    - _SpecColor: {{r: 0.19999996, g: 0.19999996, b: 0.19999996, a: 1}}
  m_BuildTextureStacks: []
  m_AllowLocking: 1
"""

def make_mat_meta(guid):
    return f"""fileFormatVersion: 2
guid: {guid}
NativeFormatImporter:
  externalObjects: {{}}
  mainObjectFileID: 2100000
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""

def make_folder_meta(guid):
    return f"""fileFormatVersion: 2
guid: {guid}
folderAsset: yes
DefaultImporter:
  externalObjects: {{}}
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""

for machine, mats in MACHINE_MATS.items():
    out_dir = f"Assets/Bomio_Exercises/Materials/{machine}"
    os.makedirs(out_dir, exist_ok=True)
    folder_meta = f"{out_dir}.meta"
    if not os.path.exists(folder_meta):
        with open(folder_meta, "w", encoding="utf-8") as f:
            f.write(make_folder_meta(det_guid(f"folder_{machine}")))

    ext_entries = []
    # 1. Bind Bomio avatar materials
    for bname, bguid in BOMIO_MATS.items():
        ext_entries.append(f"""  - first:
      type: UnityEngine:Material
      assembly: UnityEngine.CoreModule
      name: {bname}
    second: {{fileID: 2100000, guid: {bguid}, type: 2}}""")

    # 2. Create and bind each machine material
    for mname, tname, rgba, met, rough in mats:
        mguid = det_guid(f"{machine}/{mname}")
        tguid = TEX_GUIDS[tname] if tname else None
        smooth = max(0.05, min(0.95, 1.0 - rough))
        mat_path = f"{out_dir}/{mname}.mat"
        with open(mat_path, "w", encoding="utf-8") as f:
            f.write(make_urp_mat(mname, tguid, rgba, met, smooth))
        with open(f"{mat_path}.meta", "w", encoding="utf-8") as f:
            f.write(make_mat_meta(mguid))
        ext_entries.append(f"""  - first:
      type: UnityEngine:Material
      assembly: UnityEngine.CoreModule
      name: {mname}
    second: {{fileID: 2100000, guid: {mguid}, type: 2}}""")

    # 3. Inject externalObjects into Anim_Bomio_<Machine>_WithMachine.fbx.meta
    fbx_meta = f"Assets/Bomio_Exercises/Animations/Anim_Bomio_{machine}_WithMachine.fbx.meta"
    with open(fbx_meta, "r", encoding="utf-8") as f:
        mc = f.read()
    ext_block = "  externalObjects:\n" + "\n".join(ext_entries) + "\n  materials:"
    mc_new, n = re.subn(r'  externalObjects:.*?\n  materials:', ext_block, mc, flags=re.DOTALL)
    assert n == 1, f"Failed to patch externalObjects in {fbx_meta}"
    with open(fbx_meta, "w", encoding="utf-8") as f:
        f.write(mc_new)
    print(f"[{machine}] Created {len(mats)} URP materials + bound {len(ext_entries)} total materials to {fbx_meta}")
