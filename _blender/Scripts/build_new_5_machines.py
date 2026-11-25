r"""
Build synced Blender IK + machine animations + Unity exports for 5 new gym machines:
1. HipAdduction       (hip_adduction (1).blend)             -> seated hip adduction (Pivot_LegArm_L/R + weight stack)
2. LyingLegCurl       (lying_leg_curl.blend)                -> prone leg curl (Pivot_LegCurl_Arm + weight stack)
3. BenchPress         (plate_loaded_bench_press (2).blend)  -> supine converging press (Pivot_Arm_L/R + hands IK)
4. StairClimber       (stair_climber.blend)                 -> continuous 6-step belt + alternating climbing IK
5. VSquat             (v_squat.blend)                       -> standing V-squat carriage pivot + shoulder/foot/hand IK
"""
import bpy
import math
import os
from mathutils import Vector, Euler, Matrix

BOMIO_BLEND = r"G:\Unity_Gym\AI-Gym\_blender\Bomio_Exercises\01_Avatar\Player_Bomio.blend"
OUT_BLEND   = r"G:\Unity_Gym\AI-Gym\_blender\Bomio_Exercises\03_Animations_IK"
OUT_ANIM    = r"G:\Unity_Gym\AI-Gym\Assets\Bomio_Exercises\Animations"
OUT_TEX     = r"G:\Unity_Gym\AI-Gym\Assets\Bomio_Exercises\Textures"
SCRATCH     = r"C:\Users\hyung\.gemini\antigravity\brain\bc816dce-1a90-4961-b863-c22ec5353e0c\scratch"

SRC = {
    "HipAdduction": r"e:\내 드라이브\굿노트백업\3-2\창업프로젝트\Unity(서원대학교)\1125\한도윤\hip_adduction (1).blend",
    "LyingLegCurl": r"e:\내 드라이브\굿노트백업\3-2\창업프로젝트\Unity(서원대학교)\1125\한도윤\lying_leg_curl.blend",
    "BenchPress":   r"e:\내 드라이브\굿노트백업\3-2\창업프로젝트\Unity(서원대학교)\1125\한도윤\plate_loaded_bench_press (2).blend",
    "StairClimber": r"e:\내 드라이브\굿노트백업\3-2\창업프로젝트\Unity(서원대학교)\1125\한도윤\stair_climber.blend",
    "VSquat":       r"e:\내 드라이브\굿노트백업\3-2\창업프로젝트\Unity(서원대학교)\1125\한도윤\v_squat.blend",
}

for d in (OUT_BLEND, OUT_ANIM, OUT_TEX, SCRATCH):
    os.makedirs(d, exist_ok=True)


def set_bezier(obj):
    if not obj or not obj.animation_data or not obj.animation_data.action:
        return
    act = obj.animation_data.action
    fcurves = getattr(act, "fcurves", None)
    if fcurves is None or len(fcurves) == 0:
        for lay in getattr(act, "layers", []):
            for st in getattr(lay, "strips", []):
                for cb in getattr(st, "channelbags", []):
                    for fc in cb.fcurves:
                        for kp in fc.keyframe_points:
                            kp.interpolation = 'BEZIER'
        return
    for fc in fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'


def extract_machine_textures(tag):
    sub = os.path.join(OUT_TEX, tag)
    os.makedirs(sub, exist_ok=True)
    for img in bpy.data.images:
        if img.name in ("Render Result", "Viewer Node"):
            continue
        if img.packed_file is not None and img.size[0] > 0:
            if not img.name.startswith(("Ch38_", "Bomio_")):
                safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in img.name)
                if not safe.lower().endswith((".png", ".jpg", ".jpeg")):
                    safe += ".png"
                out_p = os.path.join(sub, safe)
                img.filepath_raw = out_p
                img.file_format = 'PNG'
                img.save()


def create_pivot(name, wloc, children, parent=None):
    piv = bpy.data.objects.new(name, None)
    piv.empty_display_type = 'PLAIN_AXES'
    piv.empty_display_size = 0.15
    bpy.context.scene.collection.objects.link(piv)
    piv.matrix_world = Matrix.Translation(Vector(wloc))
    if parent is not None:
        piv.parent = parent
        piv.matrix_parent_inverse = parent.matrix_world.inverted()
    bpy.context.view_layer.update()
    for ch in children:
        mw = ch.matrix_world.copy()
        ch.parent = piv
        ch.matrix_parent_inverse = piv.matrix_world.inverted()
        ch.matrix_world = mw
    bpy.context.view_layer.update()
    return piv


def append_bomio():
    """Append Player_Bomio keeping its exact Armature rest transform: loc=0, rot=(90°,0,0), scale=0.01."""
    before = set(bpy.data.objects)
    with bpy.data.libraries.load(BOMIO_BLEND, link=False) as (df, dt):
        dt.objects = list(df.objects)
    for ob in dt.objects:
        if ob is not None:
            bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    added = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in added if o.type == 'ARMATURE')
    arm.name = "Bomio_Armature"
    meshes = [o for o in added if o.type == 'MESH']
    return arm, meshes


def ensure_limb_ik_connected(arm):
    """Ensure ForeArm & Leg bones have use_connect=True and matched tail/head so 2-bone IK solves reliably."""
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    for child_bn in ("LeftForeArm", "RightForeArm", "LeftLeg", "RightLeg"):
        eb = arm.data.edit_bones.get(f"mixamorig:{child_bn}")
        if eb and eb.parent is not None:
            eb.parent.tail = eb.head.copy()
            eb.use_connect = True
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()


def make_empty(name, wloc, wrot_euler=(0,0,0), parent=None, size=0.05, disp='PLAIN_AXES'):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = disp
    e.empty_display_size = size
    bpy.context.scene.collection.objects.link(e)
    R = Euler(wrot_euler, 'XYZ').to_matrix().to_4x4()
    e.matrix_world = Matrix.Translation(Vector(wloc)) @ R
    if parent is not None:
        e.parent = parent
        e.matrix_parent_inverse = parent.matrix_world.inverted()
    bpy.context.view_layer.update()
    return e


def set_pose_rot(arm, bone_name, rx_deg, ry_deg, rz_deg):
    pb = arm.pose.bones.get(f"mixamorig:{bone_name}")
    if pb:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (math.radians(rx_deg), math.radians(ry_deg), math.radians(rz_deg))


def add_ik(arm, bone_suffix, target_obj, pole_obj=None, pole_deg=90.0, chain_len=2, hinge_z_prebend_deg=0.0):
    pb = arm.pose.bones[f"mixamorig:{bone_suffix}"]
    if abs(hinge_z_prebend_deg) > 0.1:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0.0, 0.0, math.radians(hinge_z_prebend_deg))
        pb.lock_ik_x = True
        pb.lock_ik_y = True
        pb.lock_ik_z = False
    c = pb.constraints.new('IK')
    c.target = target_obj
    if pole_obj is not None:
        c.pole_target = pole_obj
        c.pole_angle = math.radians(pole_deg)
    c.chain_count = chain_len
    return c


def add_copy_rot(arm, bone_suffix, target_obj):
    pb = arm.pose.bones[f"mixamorig:{bone_suffix}"]
    c = pb.constraints.new('COPY_ROTATION')
    c.target = target_obj
    c.target_space = 'WORLD'
    c.owner_space = 'WORLD'
    return c


def add_copy_loc(arm, bone_suffix, target_obj):
    pb = arm.pose.bones[f"mixamorig:{bone_suffix}"]
    c = pb.constraints.new('COPY_LOCATION')
    c.target = target_obj
    c.target_space = 'WORLD'
    c.owner_space = 'WORLD'
    return c


def set_hips_world_pose(arm, world_pos, world_yaw_deg=0.0, pitch_deg=0.0, roll_deg=0.0, parent=None):
    base_rot = Matrix.Rotation(math.radians(world_yaw_deg), 3, 'Z') @ \
               Matrix.Rotation(math.radians(pitch_deg), 3, 'X') @ \
               Matrix.Rotation(math.radians(roll_deg), 3, 'Y') @ \
               Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
    hips_ctrl = make_empty("IK_Hips", world_pos, base_rot.to_euler('XYZ'), parent=parent, size=0.10, disp='CUBE')
    add_copy_loc(arm, "Hips", hips_ctrl)
    add_copy_rot(arm, "Hips", hips_ctrl)
    return hips_ctrl


def curl_hand_fingers(arm, side, strength=1.0):
    for f_name, (a1, a2, a3) in [
        ("Index",  (70, 75, 55)),
        ("Middle", (75, 80, 60)),
        ("Ring",   (75, 80, 60)),
        ("Pinky",  (75, 80, 60)),
    ]:
        set_pose_rot(arm, f"{side}Hand{f_name}1", a1 * strength, 0, 0)
        set_pose_rot(arm, f"{side}Hand{f_name}2", a2 * strength, 0, 0)
        set_pose_rot(arm, f"{side}Hand{f_name}3", a3 * strength, 0, 0)
    s = 1.0 if side == "Left" else -1.0
    set_pose_rot(arm, f"{side}HandThumb1", 35 * strength, 15 * s * strength, -25 * s * strength)
    set_pose_rot(arm, f"{side}HandThumb2", 45 * strength, 0, 0)
    set_pose_rot(arm, f"{side}HandThumb3", 40 * strength, 0, 0)


def collect_machine_root(name):
    top = [o for o in bpy.data.objects if o.parent is None and o.type in {'MESH', 'EMPTY'}]
    return create_pivot(name, (0, 0, 0), top)


def bake_and_export(tag, arm, bomio_meshes, machine_root, f_start, f_peak, f_end, cam_loc, cam_tgt):
    bpy.context.view_layer.update()
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm

    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.nla.bake(
        frame_start=f_start,
        frame_end=f_end,
        only_selected=True,
        visual_keying=True,
        clear_constraints=True,
        clear_parents=False,
        use_current_action=False,
        bake_types={'POSE'},
    )
    bpy.ops.object.mode_set(mode='OBJECT')
    if arm.animation_data and arm.animation_data.action:
        arm.animation_data.action.name = f"Bomio_{tag}"

    for ob in list(bpy.data.objects):
        if ob.name.startswith(("IK_", "Pole_")):
            bpy.data.objects.remove(ob, do_unlink=True)
    bpy.context.view_layer.update()

    # Visual verification render at Start & Peak
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
    sc.render.resolution_x = 768
    sc.render.resolution_y = 768
    if not sc.world:
        sc.world = bpy.data.worlds.new("W")
    if sc.world.node_tree and sc.world.node_tree.nodes.get("Background"):
        sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.38, 0.44, 1.0)
    if not any(o.type == 'LIGHT' for o in bpy.data.objects):
        ld = bpy.data.lights.new("Sun", 'SUN')
        ld.energy = 3.5
        lo = bpy.data.objects.new("Sun", ld)
        lo.rotation_euler = (0.75, 0.25, 0.65)
        sc.collection.objects.link(lo)
    cd = bpy.data.cameras.new("CheckCam")
    co = bpy.data.objects.new("CheckCam", cd)
    sc.collection.objects.link(co)
    co.location = Vector(cam_loc)
    co.rotation_euler = (Vector(cam_tgt) - co.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = co

    for label, fr in (("start", f_start), ("peak", f_peak)):
        sc.frame_set(fr)
        bpy.context.view_layer.update()
        sc.render.filepath = os.path.join(SCRATCH, f"new5_{tag.lower()}_{label}.png")
        bpy.ops.render.render(write_still=True)

    bpy.data.objects.remove(co, do_unlink=True)

    bpy.ops.file.pack_all()
    blend_out = os.path.join(OUT_BLEND, f"Anim_Bomio_{tag}_IK.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    print(f"  Saved Blend: {blend_out}")

    bomio_orig_name = arm.name
    arm.name = "Armature"
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    for m in bomio_meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = arm
    fbx_clip = os.path.join(OUT_ANIM, f"Anim_Bomio_{tag}.fbx")
    bpy.ops.export_scene.fbx(
        filepath=fbx_clip,
        use_selection=True,
        object_types={'ARMATURE', 'MESH'},
        use_mesh_modifiers=True,
        add_leaf_bones=True,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        armature_nodetype='NULL',
        bake_anim=True,
        bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=True,
        bake_anim_step=1.0,
        apply_scale_options='FBX_SCALE_NONE',
        axis_forward='-Z',
        axis_up='Y',
        path_mode='AUTO',
        embed_textures=False,
    )

    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.data.objects:
        if o.type in {'ARMATURE', 'MESH', 'EMPTY'}:
            o.select_set(True)
    fbx_wm = os.path.join(OUT_ANIM, f"Anim_Bomio_{tag}_WithMachine.fbx")
    bpy.ops.export_scene.fbx(
        filepath=fbx_wm,
        use_selection=True,
        object_types={'ARMATURE', 'MESH', 'EMPTY'},
        use_mesh_modifiers=True,
        add_leaf_bones=True,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        armature_nodetype='NULL',
        bake_anim=True,
        bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=True,
        bake_anim_step=1.0,
        apply_scale_options='FBX_SCALE_NONE',
        axis_forward='-Z',
        axis_up='Y',
        path_mode='AUTO',
        embed_textures=False,
    )
    arm.name = bomio_orig_name
    print(f"  Exported Clip:        {fbx_clip} ({os.path.getsize(fbx_clip)/1048576:.2f} MB)")
    print(f"  Exported WithMachine: {fbx_wm} ({os.path.getsize(fbx_wm)/1048576:.2f} MB)")


# ==============================================================================
# 1. HIP ADDUCTION (Seated facing +Y, adduction squeeze inward)
# ==============================================================================
def build_hip_adduction():
    print("\n=== [1/5] Building HipAdduction ===")
    bpy.ops.wm.open_mainfile(filepath=SRC["HipAdduction"])
    extract_machine_textures("HipAdduction")
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.frame_start, sc.frame_end = 1, 61

    piv_l = bpy.data.objects["Pivot_LegArm_L"]
    piv_r = bpy.data.objects["Pivot_LegArm_R"]

    moving_weights = [
        o for o in bpy.data.objects
        if o.type == 'MESH' and (
            o.name.startswith(("Weight_TopPlate", "Weight_SelectorPin"))
            or (o.name.startswith(("Weight_Plate_", "Weight_PinHole_", "Weight_PinBushing_"))
                and o.matrix_world.translation.z > 0.56)
        )
    ]
    piv_w = create_pivot("Pivot_WeightStack", (0, 0.68, 0.58), moving_weights)

    # Frame 1 = Open (+26°), Frame 31 = Closed (0° squeezed inward), Frame 61 = Open (+26°)
    for fr, ang_deg, wz in ((1, 26.0, 0.0), (31, 0.0, 0.14), (61, 26.0, 0.0)):
        piv_l.rotation_mode = 'XYZ'
        piv_r.rotation_mode = 'XYZ'
        piv_l.rotation_euler = (0.0, 0.0, math.radians(ang_deg))
        piv_r.rotation_euler = (0.0, 0.0, math.radians(-ang_deg))
        piv_l.keyframe_insert("rotation_euler", frame=fr)
        piv_r.keyframe_insert("rotation_euler", frame=fr)
        piv_w.location.z = 0.58 + wz
        piv_w.keyframe_insert("location", frame=fr)
    for ob in (piv_l, piv_r, piv_w):
        set_bezier(ob)

    mroot = collect_machine_root("HipAdduction_Root")

    arm, meshes = append_bomio()
    ensure_limb_ik_connected(arm)

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    # Athlete seated facing +Y: world_yaw = 180°, sitting comfortably on cushion
    set_hips_world_pose(arm, (0.0, -0.16, 0.520), world_yaw_deg=180.0, pitch_deg=2.0)
    set_pose_rot(arm, "Spine",   -2, 0, 0)
    set_pose_rot(arm, "Spine1",  -2, 0, 0)
    set_pose_rot(arm, "Head",     6, 0, 0)
    # Relax shoulders downwards toward seat handles
    set_pose_rot(arm, "LeftShoulder",   0, 0, -18)
    set_pose_rot(arm, "RightShoulder",  0, 0,  18)

    # Feet on Base_FootrestPlate (Y=0.28, Z=0.17)
    ik_foot_l = make_empty("IK_Foot_L", (-0.16, 0.28, 0.175), (0, 0, 0), disp='ARROWS')
    ik_foot_r = make_empty("IK_Foot_R", ( 0.16, 0.28, 0.175), (0, 0, 0), disp='ARROWS')

    # Knee poles attached to moving leg arms so knees track the thigh pads!
    pole_kn_l = make_empty("Pole_Knee_L", (-0.21, 0.18, 0.65), parent=piv_l, disp='SPHERE')
    pole_kn_r = make_empty("Pole_Knee_R", ( 0.21, 0.18, 0.65), parent=piv_r, disp='SPHERE')

    add_ik(arm, "LeftLeg",  ik_foot_l, pole_kn_l, pole_deg=-90.0, chain_len=2)
    add_ik(arm, "RightLeg", ik_foot_r, pole_kn_r, pole_deg=-90.0, chain_len=2)
    add_copy_rot(arm, "LeftFoot",  ik_foot_l)
    add_copy_rot(arm, "RightFoot", ik_foot_r)

    # Hands grip Seat_HandleGrip_L/R (X=±0.261, Y=-0.12, Z=0.50)
    ik_hand_l = make_empty("IK_Hand_L", (-0.261, -0.120, 0.505), Euler((0, math.radians(90), 0), 'XYZ'))
    ik_hand_r = make_empty("IK_Hand_R", ( 0.261, -0.120, 0.505), Euler((0, math.radians(-90), 0), 'XYZ'))
    pole_el_l = make_empty("Pole_Elbow_L", (-0.36, -0.22, 0.60), disp='SPHERE')
    pole_el_r = make_empty("Pole_Elbow_R", ( 0.36, -0.22, 0.60), disp='SPHERE')

    add_ik(arm, "LeftForeArm",  ik_hand_l, pole_el_l, pole_deg=0.0,   chain_len=2, hinge_z_prebend_deg= 30.0)
    add_ik(arm, "RightForeArm", ik_hand_r, pole_el_r, pole_deg=180.0, chain_len=2, hinge_z_prebend_deg=-30.0)
    add_copy_rot(arm, "LeftHand",  ik_hand_l)
    add_copy_rot(arm, "RightHand", ik_hand_r)
    curl_hand_fingers(arm, "Left",  1.0)
    curl_hand_fingers(arm, "Right", 1.0)

    bpy.ops.object.mode_set(mode='OBJECT')
    bake_and_export("HipAdduction", arm, meshes, mroot, 1, 31, 61, cam_loc=(-1.75, 1.45, 1.45), cam_tgt=(0.0, 0.0, 0.72))


# ==============================================================================
# 2. LYING LEG CURL (Prone lying facing +X, concentric knee on Pivot X=-0.44)
# ==============================================================================
def build_lying_leg_curl():
    print("\n=== [2/5] Building LyingLegCurl ===")
    bpy.ops.wm.open_mainfile(filepath=SRC["LyingLegCurl"])
    extract_machine_textures("LyingLegCurl")
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.frame_start, sc.frame_end = 1, 61

    piv_curl = bpy.data.objects["Pivot_LegCurl_Arm"]
    moving_weights = [
        o for o in bpy.data.objects
        if o.type == 'MESH' and (
            o.name.startswith(("Weight_TopPlate", "Weight_SelectorPin"))
            or (o.name.startswith(("Weight_Plate_", "Weight_PinHole_", "Weight_PinBushing_"))
                and o.matrix_world.translation.z > 0.60)
        )
    ]
    piv_w = create_pivot("Pivot_WeightStack", (-0.18, 0.62, 0.62), moving_weights)

    # Start: lever resting at 0 deg, Peak: curls UP to +78 deg
    for fr, ang_deg, wz in ((1, 0.0, 0.0), (31, 78.0, 0.14), (61, 0.0, 0.0)):
        piv_curl.rotation_mode = 'XYZ'
        piv_curl.rotation_euler = (0.0, math.radians(ang_deg), 0.0)
        piv_curl.keyframe_insert("rotation_euler", frame=fr)
        piv_w.location.z = 0.62 + wz
        piv_w.keyframe_insert("location", frame=fr)
    for ob in (piv_curl, piv_w):
        set_bezier(ob)

    mroot = collect_machine_root("LyingLegCurl_Root")

    arm, meshes = append_bomio()
    ensure_limb_ik_connected(arm)

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    # Prone lying facing +X:
    # Col 0 (Left/Right) = (0, 1, 0)
    # Col 1 (Head/Up)    = (1, 0, 0.08)
    # Col 2 (Front/Down) = (0.08, 0, -1)
    R_prone = Matrix((
        (0.0,  1.0,  0.0),
        (0.99, 0.0,  0.08),
        (0.08, 0.0, -0.99),
    )).to_euler('XYZ')

    # Concentric knee alignment: machine pivot is at X=-0.44. Bomio thigh is 0.43m -> Hips at X=-0.01!
    hips_ctrl = make_empty("IK_Hips", (-0.01, 0.05, 0.56), R_prone, size=0.10, disp='CUBE')
    add_copy_loc(arm, "Hips", hips_ctrl)
    add_copy_rot(arm, "Hips", hips_ctrl)

    set_pose_rot(arm, "Spine",   -4, 0, 0)
    set_pose_rot(arm, "Spine1",  -4, 0, 0)
    set_pose_rot(arm, "Head",   -16, 0, 0)

    # Ankles hooked UNDER Ankle_RollerPad (-0.820, 0.009, 0.245)
    ik_foot_l = make_empty("IK_Foot_L", (-0.82,  0.11, 0.20), (0, 0, 0), parent=piv_curl, disp='ARROWS')
    ik_foot_r = make_empty("IK_Foot_R", (-0.82, -0.01, 0.20), (0, 0, 0), parent=piv_curl, disp='ARROWS')

    # Knee poles placed DOWN below pad (Z=0.20) with pole_deg=180 so knees stay firmly on Pad_Thigh!
    pole_kn_l = make_empty("Pole_Knee_L", (-0.44,  0.11, 0.20), disp='SPHERE')
    pole_kn_r = make_empty("Pole_Knee_R", (-0.44, -0.01, 0.20), disp='SPHERE')

    add_ik(arm, "LeftLeg",  ik_foot_l, pole_kn_l, pole_deg=180.0, chain_len=2)
    add_ik(arm, "RightLeg", ik_foot_r, pole_kn_r, pole_deg=180.0, chain_len=2)
    add_copy_rot(arm, "LeftFoot",  ik_foot_l)
    add_copy_rot(arm, "RightFoot", ik_foot_r)

    # Hands gripping Handle_Grip_Front & Handle_Grip_Rear (or resting on front elbow pad / grips)
    ik_hand_l = make_empty("IK_Hand_L", (1.02,  0.285, 0.348), Euler((math.radians(90), 0, 0), 'XYZ'))
    ik_hand_r = make_empty("IK_Hand_R", (1.02, -0.185, 0.348), Euler((math.radians(-90), 0, 0), 'XYZ'))
    pole_el_l = make_empty("Pole_Elbow_L", (0.85,  0.285, 0.257), disp='SPHERE')
    pole_el_r = make_empty("Pole_Elbow_R", (0.85, -0.185, 0.257), disp='SPHERE')

    add_ik(arm, "LeftForeArm",  ik_hand_l, pole_el_l, pole_deg=0.0,   chain_len=2, hinge_z_prebend_deg= 30.0)
    add_ik(arm, "RightForeArm", ik_hand_r, pole_el_r, pole_deg=180.0, chain_len=2, hinge_z_prebend_deg=-30.0)
    add_copy_rot(arm, "LeftHand",  ik_hand_l)
    add_copy_rot(arm, "RightHand", ik_hand_r)
    curl_hand_fingers(arm, "Left",  1.0)
    curl_hand_fingers(arm, "Right", 1.0)

    bpy.ops.object.mode_set(mode='OBJECT')
    bake_and_export("LyingLegCurl", arm, meshes, mroot, 1, 31, 61, cam_loc=(-1.55, -1.85, 1.35), cam_tgt=(0.05, 0.08, 0.58))


# ==============================================================================
# 3. PLATE-LOADED BENCH PRESS (Supine lying facing +Z, Head at +Y, pressing UP)
# ==============================================================================
def build_bench_press():
    print("\n=== [3/5] Building BenchPress ===")
    bpy.ops.wm.open_mainfile(filepath=SRC["BenchPress"])
    extract_machine_textures("BenchPress")
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.frame_start, sc.frame_end = 1, 61

    piv_l = bpy.data.objects["Pivot_Arm_L"]
    piv_r = bpy.data.objects["Pivot_Arm_R"]

    base_rx_l, base_ry_l, base_rz_l = piv_l.rotation_euler
    base_rx_r, base_ry_r, base_rz_r = piv_r.rotation_euler
    for fr, lift_deg in ((1, 0.0), (31, -38.0), (61, 0.0)):
        piv_l.rotation_euler = (base_rx_l + math.radians(lift_deg), base_ry_l, base_rz_l)
        piv_r.rotation_euler = (base_rx_r + math.radians(lift_deg), base_ry_r, base_rz_r)
        piv_l.keyframe_insert("rotation_euler", frame=fr)
        piv_r.keyframe_insert("rotation_euler", frame=fr)
    for ob in (piv_l, piv_r):
        set_bezier(ob)

    mroot = collect_machine_root("BenchPress_Root")

    arm, meshes = append_bomio()
    ensure_limb_ik_connected(arm)

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    # Supine on bench:
    # Exact verified Empty Euler: rx = 0, ry = 180, rz = 0! (Spine -> +Y, Chest -> +Z UP)
    R_supine = Euler((0.0, math.pi, 0.0), 'XYZ')

    # Bench cushion surface is at Z=0.373. Hips sits at Y=-0.28, Z=0.45. Head reaches Y=+0.25!
    hips_ctrl = make_empty("IK_Hips", (0.0, -0.28, 0.45), R_supine, size=0.10, disp='CUBE')
    add_copy_loc(arm, "Hips", hips_ctrl)
    add_copy_rot(arm, "Hips", hips_ctrl)

    # Feet planted firmly flat on gym floor (Z=0.0, soles at Z=0.082)
    ik_foot_l = make_empty("IK_Foot_L", (-0.26, -0.76, 0.082), (0, 0, 0), disp='ARROWS')
    ik_foot_r = make_empty("IK_Foot_R", ( 0.26, -0.76, 0.082), (0, 0, 0), disp='ARROWS')
    pole_kn_l = make_empty("Pole_Knee_L", (-0.28, -0.62, 0.48), disp='SPHERE')
    pole_kn_r = make_empty("Pole_Knee_R", ( 0.28, -0.62, 0.48), disp='SPHERE')

    add_ik(arm, "LeftLeg",  ik_foot_l, pole_kn_l, pole_deg=90.0, chain_len=2)
    add_ik(arm, "RightLeg", ik_foot_r, pole_kn_r, pole_deg=90.0, chain_len=2)
    add_copy_rot(arm, "LeftFoot",  ik_foot_l)
    add_copy_rot(arm, "RightFoot", ik_foot_r)

    # Hands gripping Arm_HandleGrip_L (-0.2784, -0.2405, 0.5899) and Arm_HandleGrip_R (0.2784, -0.2405, 0.5899)
    ik_hand_l = make_empty("IK_Hand_L", (-0.2784, -0.2405, 0.590), Euler((0, math.radians(-90), 0), 'XYZ'), parent=piv_l)
    ik_hand_r = make_empty("IK_Hand_R", ( 0.2784, -0.2405, 0.590), Euler((0, math.radians( 90), 0), 'XYZ'), parent=piv_r)
    # Elbows flare outwards in bench press plane
    pole_el_l = make_empty("Pole_Elbow_L", (-0.52, -0.22, 0.28), disp='SPHERE')
    pole_el_r = make_empty("Pole_Elbow_R", ( 0.52, -0.22, 0.28), disp='SPHERE')

    add_ik(arm, "LeftForeArm",  ik_hand_l, pole_el_l, pole_deg=0.0,   chain_len=2, hinge_z_prebend_deg= 30.0)
    add_ik(arm, "RightForeArm", ik_hand_r, pole_el_r, pole_deg=180.0, chain_len=2, hinge_z_prebend_deg=-30.0)
    add_copy_rot(arm, "LeftHand",  ik_hand_l)
    add_copy_rot(arm, "RightHand", ik_hand_r)
    curl_hand_fingers(arm, "Left",  1.0)
    curl_hand_fingers(arm, "Right", 1.0)

    bpy.ops.object.mode_set(mode='OBJECT')
    bake_and_export("BenchPress", arm, meshes, mroot, 1, 31, 61, cam_loc=(1.75, -1.75, 1.35), cam_tgt=(0.0, -0.25, 0.55))


# ==============================================================================
# 4. STAIR CLIMBER (Continuous 6-step conveyor + alternating steps)
# ==============================================================================
def build_stair_climber():
    print("\n=== [4/5] Building StairClimber ===")
    bpy.ops.wm.open_mainfile(filepath=SRC["StairClimber"])
    extract_machine_textures("StairClimber")
    sc = bpy.context.scene
    sc.render.fps = 30
    f_end = 121
    sc.frame_start, sc.frame_end = 1, f_end

    steps_pivs = []
    base_y0, base_z0 = -0.420, 0.495
    dy, dz = 0.235, 0.205
    for i in range(4):
        riser = bpy.data.objects[f"Step_RiserBody_0{i}"]
        tread = bpy.data.objects[f"Step_TreadPad_0{i}"]
        piv = create_pivot(f"Pivot_Step_0{i}", (0.0, base_y0 + i*dy, base_z0 + i*dz), [riser, tread])
        steps_pivs.append((piv, riser, tread))

    for i in (4, 5):
        src_p, src_r, src_t = steps_pivs[3]
        nr = src_r.copy(); nr.data = src_r.data.copy(); nr.name = f"Step_RiserBody_0{i}"; sc.collection.objects.link(nr)
        nt = src_t.copy(); nt.data = src_t.data.copy(); nt.name = f"Step_TreadPad_0{i}"; sc.collection.objects.link(nt)
        nr.parent = None; nt.parent = None
        piv = create_pivot(f"Pivot_Step_0{i}", src_p.matrix_world.translation, [nr, nt])
        steps_pivs.append((piv, nr, nt))

    belt_pts = [
        (0.0, base_y0 + 3*dy, base_z0 + 3*dz),
        (1.0, base_y0 + 2*dy, base_z0 + 2*dz),
        (2.0, base_y0 + 1*dy, base_z0 + 1*dz),
        (3.0, base_y0 + 0*dy, base_z0 + 0*dz),
        (3.5, base_y0 + 0.06, base_z0 - 0.16),
        (4.5, 0.0,            0.35),
        (5.5, base_y0 + 3*dy + 0.08, 0.86),
        (6.0, base_y0 + 3*dy, base_z0 + 3*dz),
    ]
    def eval_belt(u):
        u = u % 6.0
        for j in range(len(belt_pts) - 1):
            u0, y0, z0 = belt_pts[j]
            u1, y1, z1 = belt_pts[j+1]
            if u0 <= u <= u1:
                t = (u - u0) / (u1 - u0)
                scl = 0.72 if (3.35 <= u <= 5.65) else 1.0
                return (y0 + (y1-y0)*t, z0 + (z1-z0)*t, scl)
        return (belt_pts[0][1], belt_pts[0][2], 1.0)

    for idx, (piv, _, _) in enumerate(steps_pivs):
        u0 = (3 - idx) % 6
        for fr in range(1, f_end + 1, 2):
            phase = (fr - 1) / (f_end - 1)
            yb, zb, sb = eval_belt(u0 + phase * 6.0)
            piv.location = (0.0, yb, zb)
            piv.scale = (sb, sb, sb)
            piv.keyframe_insert("location", frame=fr)
            piv.keyframe_insert("scale", frame=fr)

    mroot = collect_machine_root("StairClimber_Root")

    arm, meshes = append_bomio()
    ensure_limb_ik_connected(arm)

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    # Standing facing +Y console: world_yaw = 180°, slight forward athletic lean
    hips_ctrl = set_hips_world_pose(arm, (0.0, -0.14, 1.56), world_yaw_deg=180.0, pitch_deg=10.0)
    set_pose_rot(arm, "Spine",   6, 0, 0)
    set_pose_rot(arm, "Spine1",  5, 0, 0)
    set_pose_rot(arm, "Head",    6, 0, 0)

    # Feet stepping on stairs
    ik_foot_l = make_empty("IK_Foot_L", (-0.13, 0.0, 0.85), (0, 0, 0), disp='ARROWS')
    ik_foot_r = make_empty("IK_Foot_R", ( 0.13, 0.0, 0.85), (0, 0, 0), disp='ARROWS')
    pole_kn_l = make_empty("Pole_Knee_L", (-0.15, 0.45, 1.25), disp='SPHERE')
    pole_kn_r = make_empty("Pole_Knee_R", ( 0.15, 0.45, 1.25), disp='SPHERE')

    add_ik(arm, "LeftLeg",  ik_foot_l, pole_kn_l, pole_deg=-90.0, chain_len=2)
    add_ik(arm, "RightLeg", ik_foot_r, pole_kn_r, pole_deg=-90.0, chain_len=2)
    add_copy_rot(arm, "LeftFoot",  ik_foot_l)
    add_copy_rot(arm, "RightFoot", ik_foot_r)

    # Hands resting on sensor handrails
    ik_hand_l = make_empty("IK_Hand_L", (-0.355, 0.085, 1.655), Euler((0, math.radians(45), 0), 'XYZ'))
    ik_hand_r = make_empty("IK_Hand_R", ( 0.355, 0.085, 1.655), Euler((0, math.radians(-45), 0), 'XYZ'))
    pole_el_l = make_empty("Pole_Elbow_L", (-0.48, -0.22, 1.48), disp='SPHERE')
    pole_el_r = make_empty("Pole_Elbow_R", ( 0.48, -0.22, 1.48), disp='SPHERE')

    add_ik(arm, "LeftForeArm",  ik_hand_l, pole_el_l, pole_deg=0.0,   chain_len=2, hinge_z_prebend_deg= 30.0)
    add_ik(arm, "RightForeArm", ik_hand_r, pole_el_r, pole_deg=180.0, chain_len=2, hinge_z_prebend_deg=-30.0)
    add_copy_rot(arm, "LeftHand",  ik_hand_l)
    add_copy_rot(arm, "RightHand", ik_hand_r)
    curl_hand_fingers(arm, "Left",  0.9)
    curl_hand_fingers(arm, "Right", 0.9)

    for fr in range(1, f_end + 1, 2):
        cy = ((fr - 1) / 40.0) % 1.0
        for ft_obj, offset in ((ik_foot_l, 0.0), (ik_foot_r, 0.5)):
            t = (cy + offset) % 1.0
            if t <= 0.5:
                s = t / 0.5
                u = 1.15 + s * 1.0
                yb, zb, _ = eval_belt(u)
                lift_z = 0.0
            else:
                s = (t - 0.5) / 0.5
                u = 2.15 - s * 1.0
                yb, zb, _ = eval_belt(u)
                lift_z = 0.14 * math.sin(math.pi * s)
            ft_obj.location.y = yb
            ft_obj.location.z = zb + 0.082 + lift_z
            ft_obj.keyframe_insert("location", frame=fr)
        hips_ctrl.location.z = 1.55 + 0.032 * math.cos(2 * math.pi * (cy * 2.0))
        hips_ctrl.keyframe_insert("location", frame=fr)

    bpy.ops.object.mode_set(mode='OBJECT')
    bake_and_export("StairClimber", arm, meshes, mroot, 1, 21, f_end, cam_loc=(1.95, -1.75, 1.85), cam_tgt=(0.0, 0.0, 1.15))


# ==============================================================================
# 5. V-SQUAT (Standing upright facing -Y, squatting into deep parallel)
# ==============================================================================
def build_v_squat():
    print("\n=== [5/5] Building VSquat ===")
    bpy.ops.wm.open_mainfile(filepath=SRC["VSquat"])
    extract_machine_textures("VSquat")
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.frame_start, sc.frame_end = 1, 61

    moving = [
        o for o in bpy.data.objects
        if o.type == 'MESH' and (
            o.name.startswith(("BackPad_", "ShoulderPad_", "Handgrip_", "WeightHorn_"))
            or (o.name.startswith("Carriage_") and "PillowBlockBase" not in o.name)
        )
    ]
    piv_car = create_pivot("Pivot_Carriage", (0.0, 0.54, 0.95), moving)

    # Frame 1 = Standing (0°), Frame 31 = Deep Squat (+18° down), Frame 61 = Standing (0°)
    for fr, deg in ((1, 0.0), (31, 18.0), (61, 0.0)):
        piv_car.rotation_mode = 'XYZ'
        piv_car.rotation_euler = (math.radians(deg), 0.0, 0.0)
        piv_car.keyframe_insert("rotation_euler", frame=fr)
    set_bezier(piv_car)

    mroot = collect_machine_root("VSquat_Root")

    arm, meshes = append_bomio()
    ensure_limb_ik_connected(arm)

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    # Standing upright facing -Y: world_yaw = 0.0°
    # Back resting against BackPad_Cushion (Y=-0.118), parented to Carriage with correct parent inverse!
    hips_ctrl = set_hips_world_pose(arm, (0.0, -0.19, 0.98), world_yaw_deg=0.0, pitch_deg=-14.0, parent=piv_car)
    set_pose_rot(arm, "Spine",   -4, 0, 0)
    set_pose_rot(arm, "Spine1",  -4, 0, 0)
    set_pose_rot(arm, "Head",    10, 0, 0)

    # Feet planted on sloped Footplate_RibbedDeck
    # Mixamo Foot local axes facing -Y: toes point along -Y
    ik_foot_l = make_empty("IK_Foot_L", ( 0.18, -0.62, 0.44), (0, 0, 0), disp='ARROWS')
    ik_foot_r = make_empty("IK_Foot_R", (-0.18, -0.62, 0.44), (0, 0, 0), disp='ARROWS')
    # Knees bend forward along -Y!
    pole_kn_l = make_empty("Pole_Knee_L", ( 0.20, -1.10, 0.82), disp='SPHERE')
    pole_kn_r = make_empty("Pole_Knee_R", (-0.20, -1.10, 0.82), disp='SPHERE')

    add_ik(arm, "LeftLeg",  ik_foot_l, pole_kn_l, pole_deg=90.0, chain_len=2)
    add_ik(arm, "RightLeg", ik_foot_r, pole_kn_r, pole_deg=90.0, chain_len=2)
    add_copy_rot(arm, "LeftFoot",  ik_foot_l)
    add_copy_rot(arm, "RightFoot", ik_foot_r)

    # Hands gripping Handgrip_VerticalRubber_L/R (±0.355, -0.210, 1.3075) parented to Carriage
    ik_hand_l = make_empty("IK_Hand_L", ( 0.355, -0.210, 1.308), Euler((math.radians(-90), 0, 0), 'XYZ'), parent=piv_car)
    ik_hand_r = make_empty("IK_Hand_R", (-0.355, -0.210, 1.308), Euler((math.radians( 90), 0, 0), 'XYZ'), parent=piv_car)
    pole_el_l = make_empty("Pole_Elbow_L", ( 0.48, -0.15, 1.15), parent=piv_car, disp='SPHERE')
    pole_el_r = make_empty("Pole_Elbow_R", (-0.48, -0.15, 1.15), parent=piv_car, disp='SPHERE')

    add_ik(arm, "LeftForeArm",  ik_hand_l, pole_el_l, pole_deg=0.0,   chain_len=2, hinge_z_prebend_deg= 30.0)
    add_ik(arm, "RightForeArm", ik_hand_r, pole_el_r, pole_deg=180.0, chain_len=2, hinge_z_prebend_deg=-30.0)
    add_copy_rot(arm, "LeftHand",  ik_hand_l)
    add_copy_rot(arm, "RightHand", ik_hand_r)
    curl_hand_fingers(arm, "Left",  1.0)
    curl_hand_fingers(arm, "Right", 1.0)

    bpy.ops.object.mode_set(mode='OBJECT')
    bake_and_export("VSquat", arm, meshes, mroot, 1, 31, 61, cam_loc=(1.95, -2.05, 1.45), cam_tgt=(0.0, -0.20, 0.95))


if __name__ == "__main__":
    build_hip_adduction()
    build_lying_leg_curl()
    build_bench_press()
    build_stair_climber()
    build_v_squat()
    print("\nALL 5 NEW BOMIO IK ANIMATIONS & EXPORTS COMPLETED!")
