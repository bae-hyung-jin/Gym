r"""
Rebuild synced Blender Mixamo IK + machine animations + Unity exports for 5 new gym machines
with mathematically exact Mixamo bone-axis helpers (foot_world_euler, hand_world_euler,
auto-verified pole angles) so ZERO limbs, knees, ankles, or wrists ever twist!
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
    # Capture exact rest-pose world rotation matrices for LeftFoot & RightFoot
    rest_rot = {}
    for bn in ("LeftFoot", "RightFoot"):
        pb = arm.pose.bones[f"mixamorig:{bn}"]
        rest_rot[bn] = (arm.matrix_world @ pb.matrix).to_3x3().normalized()
    return arm, meshes, rest_rot


def ensure_limb_ik_connected(arm):
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


def hand_world_euler(finger_dir_vec, palm_normal_vec):
    """Exact Mixamo LeftHand/RightHand world Euler: bone +Y = finger_dir, bone +Z = palm_normal."""
    y = Vector(finger_dir_vec).normalized()
    z = Vector(palm_normal_vec).normalized()
    x = y.cross(z)
    if x.length < 1e-5:
        x = Vector((1, 0, 0))
    else:
        x.normalize()
    z = x.cross(y).normalized()
    M = Matrix((
        (x.x, y.x, z.x),
        (x.y, y.y, z.y),
        (x.z, y.z, z.z),
    ))
    return M.to_euler('XYZ')


def foot_world_euler(toe_dir_vec, sole_up_vec, rest_foot_rot_3x3):
    """
    Exact Mixamo LeftFoot/RightFoot world Euler:
    Maps Bomio rest standing frame (left=+X, back=+Y, up=+Z; toes=-Y)
    to (toe_dir_vec, sole_up_vec) so shoes sit 100% flat and untwisted!
    """
    fwd = Vector(toe_dir_vec).normalized()
    up = Vector(sole_up_vec).normalized()
    left = up.cross(fwd)
    if left.length < 1e-5:
        left = Vector((1, 0, 0))
    else:
        left.normalize()
    back = -fwd
    up = fwd.cross(left).normalized()
    R_frame = Matrix((
        (left.x, back.x, up.x),
        (left.y, back.y, up.y),
        (left.z, back.z, up.z),
    ))
    return (R_frame @ rest_foot_rot_3x3).to_euler('XYZ')


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


def add_leg_ik_auto(arm, side, target_obj, pole_obj, expected_knee_dir):
    """
    Attach 2-bone IK to mixamorig:{side}Leg and automatically pick the exact pole_angle
    that aligns the thigh's forward (+Z) axis with expected_knee_dir (ZERO twisted knees!).
    """
    pb_leg = arm.pose.bones[f"mixamorig:{side}Leg"]
    pb_thigh = arm.pose.bones[f"mixamorig:{side}UpLeg"]
    # Slight natural knee pre-bend around local +X (breaks straight-leg singularity)
    pb_leg.rotation_mode = 'XYZ'
    pb_leg.rotation_euler = (math.radians(-10.0), 0.0, 0.0)
    pb_leg.lock_ik_y = True
    pb_leg.lock_ik_z = True

    c = pb_leg.constraints.new('IK')
    c.target = target_obj
    c.pole_target = pole_obj
    c.chain_count = 2

    exp = Vector(expected_knee_dir).normalized()
    best_deg = 90.0
    best_score = -999.0
    for cand in (-90.0, 90.0, 0.0, 180.0):
        c.pole_angle = math.radians(cand)
        bpy.context.view_layer.update()
        # Check BOTH thigh +Z alignment AND knee joint displacement toward pole_obj
        M_thigh = (arm.matrix_world @ pb_thigh.matrix).to_3x3().normalized()
        thigh_z = M_thigh.col[2]
        knee_pos = arm.matrix_world @ pb_leg.head
        hip_pos = arm.matrix_world @ pb_thigh.head
        ank_pos = arm.matrix_world @ pb_leg.tail
        mid = (hip_pos + ank_pos) * 0.5
        knee_out = (knee_pos - mid)
        knee_dir = knee_out.normalized() if knee_out.length > 1e-4 else thigh_z
        score = thigh_z.dot(exp) * 2.0 + knee_dir.dot(exp)
        if score > best_score:
            best_score = score
            best_deg = cand
    c.pole_angle = math.radians(best_deg)
    bpy.context.view_layer.update()
    print(f"    [AutoLegIK] {side}Leg pole_angle={best_deg:+.0f}° (score={best_score:.2f})")
    return c


def add_arm_ik_auto(arm, side, target_obj, pole_obj, expected_elbow_dir):
    """
    Attach 2-bone IK to mixamorig:{side}ForeArm and automatically pick the exact pole_angle
    that aligns the elbow bend toward expected_elbow_dir (ZERO twisted arms!).
    """
    pb_fa = arm.pose.bones[f"mixamorig:{side}ForeArm"]
    pb_ua = arm.pose.bones[f"mixamorig:{side}Arm"]
    # Mixamo elbow hinge is around local Z
    prebend = 25.0 if side == "Left" else -25.0
    pb_fa.rotation_mode = 'XYZ'
    pb_fa.rotation_euler = (0.0, 0.0, math.radians(prebend))
    pb_fa.lock_ik_x = True
    pb_fa.lock_ik_y = True
    pb_fa.lock_ik_z = False

    c = pb_fa.constraints.new('IK')
    c.target = target_obj
    c.pole_target = pole_obj
    c.chain_count = 2

    exp = Vector(expected_elbow_dir).normalized()
    best_deg = 0.0
    best_score = -999.0
    for cand in (0.0, 90.0, -90.0, 180.0):
        c.pole_angle = math.radians(cand)
        bpy.context.view_layer.update()
        sh_pos = arm.matrix_world @ pb_ua.head
        el_pos = arm.matrix_world @ pb_fa.head
        wr_pos = arm.matrix_world @ pb_fa.tail
        mid = (sh_pos + wr_pos) * 0.5
        el_out = el_pos - mid
        el_dir = el_out.normalized() if el_out.length > 1e-4 else Vector((0, 0, 0))
        score = el_dir.dot(exp)
        if score > best_score:
            best_score = score
            best_deg = cand
    c.pole_angle = math.radians(best_deg)
    bpy.context.view_layer.update()
    print(f"    [AutoArmIK] {side}ForeArm pole_angle={best_deg:+.0f}° (score={best_score:.2f})")
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
        ("Index",  (75, 85, 62)),
        ("Middle", (80, 90, 65)),
        ("Ring",   (80, 90, 65)),
        ("Pinky",  (80, 88, 62)),
    ]:
        set_pose_rot(arm, f"{side}Hand{f_name}1", a1 * strength, 0, 0)
        set_pose_rot(arm, f"{side}Hand{f_name}2", a2 * strength, 0, 0)
        set_pose_rot(arm, f"{side}Hand{f_name}3", a3 * strength, 0, 0)
    s = 1.0 if side == "Left" else -1.0
    set_pose_rot(arm, f"{side}HandThumb1", 40 * strength, 18 * s * strength, -28 * s * strength)
    set_pose_rot(arm, f"{side}HandThumb2", 48 * strength, 0, 0)
    set_pose_rot(arm, f"{side}HandThumb3", 42 * strength, 0, 0)


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
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.frame_start, sc.frame_end = 1, 61

    piv_l = bpy.data.objects["Pivot_LegArm_L"]
    piv_r = bpy.data.objects["Pivot_LegArm_R"]

    # Include EVERY moving part on the selected stack (plates + 5~30kg label badges + holes + bushings + spacers + top plate caps + pin!)
    static_weight_prefixes = ("Weight_GuideRod_", "Weight_TopRodCollar_", "Weight_TopCable", "Weight_BottomBumper")
    moving_weights = [
        o for o in bpy.data.objects
        if o.type == 'MESH' and o.name.startswith("Weight_")
        and not o.name.startswith(static_weight_prefixes)
        and (
            o.name.startswith(("Weight_TopPlate", "Weight_SelectorPin", "Weight_CableAnchor", "Weight_Red"))
            or o.matrix_world.translation.z > 0.56
        )
    ]
    piv_w = create_pivot("Pivot_WeightStack", (0, 0.68, 0.58), moving_weights)

    # Frame 1 = Open (+28°), Frame 31 = Closed (+4° squeezed inward so knees don't collide), Frame 61 = Open (+28°)
    for fr, ang_deg, wz in ((1, 28.0, 0.0), (31, 4.0, 0.14), (61, 28.0, 0.0)):
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

    arm, meshes, rest_rot = append_bomio()
    ensure_limb_ik_connected(arm)

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    sc.frame_set(1)
    bpy.context.view_layer.update()

    # Facing +Y: world_yaw = 180° (athlete Left is -X, athlete Right is +X!)
    set_hips_world_pose(arm, (0.0, -0.20, 0.555), world_yaw_deg=180.0, pitch_deg=4.0)
    set_pose_rot(arm, "Spine",   -4, 0, 0)
    set_pose_rot(arm, "Spine1",  -4, 0, 0)
    set_pose_rot(arm, "Head",     6, 0, 0)
    set_pose_rot(arm, "LeftShoulder",   0, 0, -14)
    set_pose_rot(arm, "RightShoulder",  0, 0,  14)

    # Feet attached to moving leg arms (inside the leg arm frames, toes pointing +Y!)
    # At frame 1 (open +28°), place feet at world pos corresponding to leg arms
    sc.frame_set(31)
    bpy.context.view_layer.update()
    rot_ft_l = foot_world_euler((0, 1, 0), (0, 0, 1), rest_rot["LeftFoot"])
    rot_ft_r = foot_world_euler((0, 1, 0), (0, 0, 1), rest_rot["RightFoot"])
    # Left foot is on -X (piv_l), Right foot is on +X (piv_r)!
    ik_foot_l = make_empty("IK_Foot_L", (-0.11, 0.25, 0.24), rot_ft_l, parent=piv_l, disp='ARROWS')
    ik_foot_r = make_empty("IK_Foot_R", ( 0.11, 0.25, 0.24), rot_ft_r, parent=piv_r, disp='ARROWS')
    pole_kn_l = make_empty("Pole_Knee_L", (-0.12, 0.35, 0.72), parent=piv_l, disp='SPHERE')
    pole_kn_r = make_empty("Pole_Knee_R", ( 0.12, 0.35, 0.72), parent=piv_r, disp='SPHERE')

    add_leg_ik_auto(arm, "Left",  ik_foot_l, pole_kn_l, expected_knee_dir=(0, 1, 0.3))
    add_leg_ik_auto(arm, "Right", ik_foot_r, pole_kn_r, expected_knee_dir=(0, 1, 0.3))
    add_copy_rot(arm, "LeftFoot",  ik_foot_l)
    add_copy_rot(arm, "RightFoot", ik_foot_r)

    # Hands gripping Seat_HandleGrip_L/R (±0.261, -0.08, 0.50)
    # Facing +Y: Left hand on -X grips bar running along Y -> fingers curl inward (+X), palm faces +X (inward)
    rot_h_l = hand_world_euler((0, 1, -0.2), (1, 0, 0))
    rot_h_r = hand_world_euler((0, 1, -0.2), (-1, 0, 0))
    ik_hand_l = make_empty("IK_Hand_L", (-0.261, -0.115, 0.500), rot_h_l)
    ik_hand_r = make_empty("IK_Hand_R", ( 0.261, -0.115, 0.500), rot_h_r)
    pole_el_l = make_empty("Pole_Elbow_L", (-0.42, -0.35, 0.65), disp='SPHERE')
    pole_el_r = make_empty("Pole_Elbow_R", ( 0.42, -0.35, 0.65), disp='SPHERE')

    add_arm_ik_auto(arm, "Left",  ik_hand_l, pole_el_l, expected_elbow_dir=(-0.5, -1, 0))
    add_arm_ik_auto(arm, "Right", ik_hand_r, pole_el_r, expected_elbow_dir=( 0.5, -1, 0))
    add_copy_rot(arm, "LeftHand",  ik_hand_l)
    add_copy_rot(arm, "RightHand", ik_hand_r)
    curl_hand_fingers(arm, "Left",  1.0)
    curl_hand_fingers(arm, "Right", 1.0)

    bpy.ops.object.mode_set(mode='OBJECT')
    bake_and_export("HipAdduction", arm, meshes, mroot, 1, 31, 61, cam_loc=(-1.75, 1.45, 1.45), cam_tgt=(0.0, 0.0, 0.72))


# ==============================================================================
# 2. LYING LEG CURL (Prone lying facing +X, deep hamstring curl UP to +102 deg!)
# ==============================================================================
def build_lying_leg_curl():
    print("\n=== [2/5] Building LyingLegCurl ===")
    bpy.ops.wm.open_mainfile(filepath=SRC["LyingLegCurl"])
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.frame_start, sc.frame_end = 1, 61

    piv_curl = bpy.data.objects["Pivot_LegCurl_Arm"]
    static_weight_prefixes = ("Weight_GuideRod_", "Weight_TopRodCollar_", "Weight_TopCable", "Weight_BottomBumper")
    moving_weights = [
        o for o in bpy.data.objects
        if o.type == 'MESH' and o.name.startswith("Weight_")
        and not o.name.startswith(static_weight_prefixes)
        and (
            o.name.startswith(("Weight_TopPlate", "Weight_SelectorPin", "Weight_CableAnchor", "Weight_GuideBushing"))
            or o.matrix_world.translation.z > 0.59
        )
    ]
    piv_w = create_pivot("Pivot_WeightStack", (-0.18, 0.62, 0.62), moving_weights)

    # Start: 0 deg (legs extended), Peak: +102 deg (curled high up toward glutes!), End: 0 deg
    for fr, ang_deg, wz in ((1, 0.0, 0.0), (31, 102.0, 0.16), (61, 0.0, 0.0)):
        piv_curl.rotation_mode = 'XYZ'
        piv_curl.rotation_euler = (0.0, math.radians(ang_deg), 0.0)
        piv_curl.keyframe_insert("rotation_euler", frame=fr)
        piv_w.location.z = 0.62 + wz
        piv_w.keyframe_insert("location", frame=fr)
    for ob in (piv_curl, piv_w):
        set_bezier(ob)

    mroot = collect_machine_root("LyingLegCurl_Root")

    arm, meshes, rest_rot = append_bomio()
    ensure_limb_ik_connected(arm)

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    sc.frame_set(1)
    bpy.context.view_layer.update()

    # Prone lying facing +X:
    # Hips local axes: +X = Left (+Y world), +Y = Head (+X world), +Z = Front/Belly (-Z world)
    R_prone = Matrix((
        (0.0,  1.0,  0.0),
        (1.0,  0.0,  0.0),
        (0.0,  0.0, -1.0),
    )).to_euler('XYZ')

    # Pad_Thigh top is Z=0.634, Pad_Chest top is Z=0.630.
    # Place Hips at X=0.04 so hands comfortably grip Handle_Grip_Rear/Front (X=1.065) while knees stay on Pad_Thigh!
    hips_ctrl = make_empty("IK_Hips", (0.04, 0.05, 0.68), R_prone, size=0.10, disp='CUBE')
    add_copy_loc(arm, "Hips", hips_ctrl)
    add_copy_rot(arm, "Hips", hips_ctrl)

    set_pose_rot(arm, "Spine",   -3, 0, 0)
    set_pose_rot(arm, "Spine1",  -3, 0, 0)
    set_pose_rot(arm, "Head",   -18, 0, 0)

    # Ankles hooked right UNDER Ankle_RollerPad (-0.82, 0.009, 0.245) at frame 1
    # When prone facing +X, toes point DOWN (-Z), soles face BACK (-X)
    rot_ft_l = foot_world_euler((0, 0, -1), (-1, 0, 0), rest_rot["LeftFoot"])
    rot_ft_r = foot_world_euler((0, 0, -1), (-1, 0, 0), rest_rot["RightFoot"])
    ik_foot_l = make_empty("IK_Foot_L", (-0.79,  0.14, 0.27), rot_ft_l, parent=piv_curl, disp='ARROWS')
    ik_foot_r = make_empty("IK_Foot_R", (-0.79, -0.04, 0.27), rot_ft_r, parent=piv_curl, disp='ARROWS')

    # Knee poles placed BELOW thigh pad (Z=0.10) -> expected_knee_dir = (0, 0, -1) (DOWN into Pad_Thigh!)
    pole_kn_l = make_empty("Pole_Knee_L", (-0.44,  0.14, 0.05), disp='SPHERE')
    pole_kn_r = make_empty("Pole_Knee_R", (-0.44, -0.04, 0.05), disp='SPHERE')

    add_leg_ik_auto(arm, "Left",  ik_foot_l, pole_kn_l, expected_knee_dir=(0, 0, -1))
    add_leg_ik_auto(arm, "Right", ik_foot_r, pole_kn_r, expected_knee_dir=(0, 0, -1))
    add_copy_rot(arm, "LeftFoot",  ik_foot_l)
    add_copy_rot(arm, "RightFoot", ik_foot_r)

    # Hands gripping Handle_Grip_Rear (1.065, 0.285, 0.347) & Handle_Grip_Front (1.065, -0.185, 0.347)
    rot_h_l = hand_world_euler((1, 0, -0.3), (0, -1, 0))
    rot_h_r = hand_world_euler((1, 0, -0.3), (0,  1, 0))
    ik_hand_l = make_empty("IK_Hand_L", (1.04,  0.285, 0.36), rot_h_l)
    ik_hand_r = make_empty("IK_Hand_R", (1.04, -0.185, 0.36), rot_h_r)
    pole_el_l = make_empty("Pole_Elbow_L", (0.82,  0.34, 0.25), disp='SPHERE')
    pole_el_r = make_empty("Pole_Elbow_R", (0.82, -0.24, 0.25), disp='SPHERE')

    add_arm_ik_auto(arm, "Left",  ik_hand_l, pole_el_l, expected_elbow_dir=(0,  0.4, -1))
    add_arm_ik_auto(arm, "Right", ik_hand_r, pole_el_r, expected_elbow_dir=(0, -0.4, -1))
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
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.frame_start, sc.frame_end = 1, 61

    piv_l = bpy.data.objects["Pivot_Arm_L"]
    piv_r = bpy.data.objects["Pivot_Arm_R"]

    base_rx_l, base_ry_l, base_rz_l = piv_l.rotation_euler
    base_rx_r, base_ry_r, base_rz_r = piv_r.rotation_euler
    # Lift -30 deg so handles rise smoothly from Z=0.59 (chest) to Z=0.86 (full lockout within arm reach!)
    for fr, lift_deg in ((1, 0.0), (31, -30.0), (61, 0.0)):
        piv_l.rotation_euler = (base_rx_l + math.radians(lift_deg), base_ry_l, base_rz_l)
        piv_r.rotation_euler = (base_rx_r + math.radians(lift_deg), base_ry_r, base_rz_r)
        piv_l.keyframe_insert("rotation_euler", frame=fr)
        piv_r.keyframe_insert("rotation_euler", frame=fr)
    for ob in (piv_l, piv_r):
        set_bezier(ob)

    mroot = collect_machine_root("BenchPress_Root")

    arm, meshes, rest_rot = append_bomio()
    ensure_limb_ik_connected(arm)

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    sc.frame_set(1)
    bpy.context.view_layer.update()

    # Supine on bench (proper right-handed rotation, det=+1!):
    # Hips local axes: +X = (+1, 0, 0) [Left is +X!], +Y = (0, +1, 0) [Head is +Y!], +Z = (0, 0, +1) [Chest UP +Z!]
    R_supine = Matrix((
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    )).to_euler('XYZ')

    # Bench_CushionPad top is Z=0.41, Y=-0.73..+0.34.
    # Place Hips at Y=-0.46, Z=0.49 -> chest/shoulders directly under Arm_HandleGrip (Y=-0.241), head on bench (Y=+0.22)!
    hips_ctrl = make_empty("IK_Hips", (0.0, -0.46, 0.49), R_supine, size=0.10, disp='CUBE')
    add_copy_loc(arm, "Hips", hips_ctrl)
    add_copy_rot(arm, "Hips", hips_ctrl)

    # Feet planted flat on gym floor (Z=0.115 ankle height -> soles at Z=0.0!)
    # Facing supine with legs toward -Y: toes point -Y, soles face +Z (up). Left leg is +X, Right leg is -X!
    rot_ft_l = foot_world_euler((0, -1, 0), (0, 0, 1), rest_rot["LeftFoot"])
    rot_ft_r = foot_world_euler((0, -1, 0), (0, 0, 1), rest_rot["RightFoot"])
    ik_foot_l = make_empty("IK_Foot_L", ( 0.24, -0.95, 0.115), rot_ft_l, disp='ARROWS')
    ik_foot_r = make_empty("IK_Foot_R", (-0.24, -0.95, 0.115), rot_ft_r, disp='ARROWS')
    pole_kn_l = make_empty("Pole_Knee_L", ( 0.26, -0.82, 0.72), disp='SPHERE')
    pole_kn_r = make_empty("Pole_Knee_R", (-0.26, -0.82, 0.72), disp='SPHERE')

    add_leg_ik_auto(arm, "Left",  ik_foot_l, pole_kn_l, expected_knee_dir=(0, -0.3, 1))
    add_leg_ik_auto(arm, "Right", ik_foot_r, pole_kn_r, expected_knee_dir=(0, -0.3, 1))
    add_copy_rot(arm, "LeftFoot",  ik_foot_l)
    add_copy_rot(arm, "RightFoot", ik_foot_r)

    # Athlete Left (+X) grips Arm_HandleGrip_R (+0.278, -0.241, 0.590) -> parent=piv_r!
    # Athlete Right (-X) grips Arm_HandleGrip_L (-0.278, -0.241, 0.590) -> parent=piv_l!
    # Pressing UP (+Z): fingers wrap toward head (+Y), palms face UP (+Z)
    rot_h_l = hand_world_euler((0, 0.5, 0.86), (0, -0.86, 0.5))
    rot_h_r = hand_world_euler((0, 0.5, 0.86), (0, -0.86, 0.5))
    ik_hand_l = make_empty("IK_Hand_L", ( 0.278, -0.241, 0.575), rot_h_l, parent=piv_r)
    ik_hand_r = make_empty("IK_Hand_R", (-0.278, -0.241, 0.575), rot_h_r, parent=piv_l)
    pole_el_l = make_empty("Pole_Elbow_L", ( 0.65, -0.26, 0.25), disp='SPHERE')
    pole_el_r = make_empty("Pole_Elbow_R", (-0.65, -0.26, 0.25), disp='SPHERE')

    add_arm_ik_auto(arm, "Left",  ik_hand_l, pole_el_l, expected_elbow_dir=( 1, -0.2, -0.5))
    add_arm_ik_auto(arm, "Right", ik_hand_r, pole_el_r, expected_elbow_dir=(-1, -0.2, -0.5))
    add_copy_rot(arm, "LeftHand",  ik_hand_l)
    add_copy_rot(arm, "RightHand", ik_hand_r)
    curl_hand_fingers(arm, "Left",  1.0)
    curl_hand_fingers(arm, "Right", 1.0)

    bpy.ops.object.mode_set(mode='OBJECT')
    bake_and_export("BenchPress", arm, meshes, mroot, 1, 31, 61, cam_loc=(1.75, -1.75, 1.35), cam_tgt=(0.0, -0.35, 0.55))


# ==============================================================================
# 4. STAIR CLIMBER (Continuous 6-step conveyor + alternating climbing IK)
# ==============================================================================
def build_stair_climber():
    print("\n=== [4/5] Building StairClimber ===")
    bpy.ops.wm.open_mainfile(filepath=SRC["StairClimber"])
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

    arm, meshes, rest_rot = append_bomio()
    ensure_limb_ik_connected(arm)

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    sc.frame_set(1)
    bpy.context.view_layer.update()

    # Standing facing +Y console: world_yaw = 180° (Left = -X, Right = +X)
    hips_ctrl = set_hips_world_pose(arm, (0.0, -0.14, 1.56), world_yaw_deg=180.0, pitch_deg=10.0)
    set_pose_rot(arm, "Spine",   6, 0, 0)
    set_pose_rot(arm, "Spine1",  5, 0, 0)
    set_pose_rot(arm, "Head",    6, 0, 0)

    # Feet stepping flat on stairs (toes +Y, sole normal +Z!)
    rot_ft_l = foot_world_euler((0, 1, 0), (0, 0, 1), rest_rot["LeftFoot"])
    rot_ft_r = foot_world_euler((0, 1, 0), (0, 0, 1), rest_rot["RightFoot"])
    ik_foot_l = make_empty("IK_Foot_L", (-0.13, 0.0, 0.90), rot_ft_l, disp='ARROWS')
    ik_foot_r = make_empty("IK_Foot_R", ( 0.13, -0.20, 0.72), rot_ft_r, disp='ARROWS')
    pole_kn_l = make_empty("Pole_Knee_L", (-0.14, 0.55, 1.25), disp='SPHERE')
    pole_kn_r = make_empty("Pole_Knee_R", ( 0.14, 0.55, 1.25), disp='SPHERE')

    add_leg_ik_auto(arm, "Left",  ik_foot_l, pole_kn_l, expected_knee_dir=(0, 1, 0))
    add_leg_ik_auto(arm, "Right", ik_foot_r, pole_kn_r, expected_knee_dir=(0, 1, 0))
    add_copy_rot(arm, "LeftFoot",  ik_foot_l)
    add_copy_rot(arm, "RightFoot", ik_foot_r)

    # Hands gripping side handrails cleanly
    rot_h_l = hand_world_euler((0, 1, 0.3), (1, 0, -0.4))
    rot_h_r = hand_world_euler((0, 1, 0.3), (-1, 0, -0.4))
    ik_hand_l = make_empty("IK_Hand_L", (-0.355, 0.085, 1.655), rot_h_l)
    ik_hand_r = make_empty("IK_Hand_R", ( 0.355, 0.085, 1.655), rot_h_r)
    pole_el_l = make_empty("Pole_Elbow_L", (-0.48, -0.25, 1.48), disp='SPHERE')
    pole_el_r = make_empty("Pole_Elbow_R", ( 0.48, -0.25, 1.48), disp='SPHERE')

    add_arm_ik_auto(arm, "Left",  ik_hand_l, pole_el_l, expected_elbow_dir=(-0.5, -1, -0.5))
    add_arm_ik_auto(arm, "Right", ik_hand_r, pole_el_r, expected_elbow_dir=( 0.5, -1, -0.5))
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
                lift_z = 0.12 * math.sin(math.pi * s)
            ft_obj.location.y = yb
            ft_obj.location.z = zb + 0.115 + lift_z
            ft_obj.keyframe_insert("location", frame=fr)
        hips_ctrl.location.z = 1.56 + 0.03 * math.cos(2 * math.pi * (cy * 2.0))
        hips_ctrl.keyframe_insert("location", frame=fr)

    bpy.ops.object.mode_set(mode='OBJECT')
    bake_and_export("StairClimber", arm, meshes, mroot, 1, 21, f_end, cam_loc=(1.95, -1.75, 1.85), cam_tgt=(0.0, 0.0, 1.15))


# ==============================================================================
# 5. V-SQUAT (Standing facing -Y, shoulders cleanly UNDER ShoulderPad_Cushion!)
# ==============================================================================
def build_v_squat():
    print("\n=== [5/5] Building VSquat ===")
    bpy.ops.wm.open_mainfile(filepath=SRC["VSquat"])
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

    # Frame 1 = Standing (0°), Frame 31 = Deep Squat (+20° down), Frame 61 = Standing (0°)
    for fr, deg in ((1, 0.0), (31, 20.0), (61, 0.0)):
        piv_car.rotation_mode = 'XYZ'
        piv_car.rotation_euler = (math.radians(deg), 0.0, 0.0)
        piv_car.keyframe_insert("rotation_euler", frame=fr)
    set_bezier(piv_car)

    mroot = collect_machine_root("VSquat_Root")

    arm, meshes, rest_rot = append_bomio()
    ensure_limb_ik_connected(arm)

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    sc.frame_set(1)
    bpy.context.view_layer.update()

    # ShoulderPad_Cushion bottom is Z=1.365! Bomio shoulder-to-hips = 0.498m -> Hips Z=0.835 puts shoulders cleanly UNDER pads!
    # BackPad_Cushion front is Y=-0.176 -> Hips Y=-0.26 so back rests cleanly AGAINST BackPad without clipping!
    hips_ctrl = set_hips_world_pose(arm, (0.0, -0.26, 0.835), world_yaw_deg=0.0, pitch_deg=-10.0, parent=piv_car)
    set_pose_rot(arm, "Spine",   -3, 0, 0)
    set_pose_rot(arm, "Spine1",  -3, 0, 0)
    set_pose_rot(arm, "Head",     6, 0, 0)

    # Footplate_RibbedDeck: ctr=(0,-0.58,0.355), slope ~15.6 deg (higher toward -Y)
    # Match exact deck slope: toe_dir=(0, -0.963, 0.270), sole_up=(0, 0.270, 0.963)!
    rot_ft_l = foot_world_euler((0, -0.963, 0.270), (0, 0.270, 0.963), rest_rot["LeftFoot"])
    rot_ft_r = foot_world_euler((0, -0.963, 0.270), (0, 0.270, 0.963), rest_rot["RightFoot"])
    # Facing -Y: Left is +X, Right is -X!
    ik_foot_l = make_empty("IK_Foot_L", ( 0.18, -0.58, 0.46), rot_ft_l, disp='ARROWS')
    ik_foot_r = make_empty("IK_Foot_R", (-0.18, -0.58, 0.46), rot_ft_r, disp='ARROWS')
    pole_kn_l = make_empty("Pole_Knee_L", ( 0.22, -1.25, 0.78), disp='SPHERE')
    pole_kn_r = make_empty("Pole_Knee_R", (-0.22, -1.25, 0.78), disp='SPHERE')

    add_leg_ik_auto(arm, "Left",  ik_foot_l, pole_kn_l, expected_knee_dir=(0, -1, 0))
    add_leg_ik_auto(arm, "Right", ik_foot_r, pole_kn_r, expected_knee_dir=(0, -1, 0))
    add_copy_rot(arm, "LeftFoot",  ik_foot_l)
    add_copy_rot(arm, "RightFoot", ik_foot_r)

    # Hands gripping Handgrip_VerticalRubber_L/R (±0.355, -0.210, 1.308) parented to Carriage
    # Facing -Y: Left hand (+X) grips vertical handle -> finger_dir = (0, -1, 0), palm_normal = (-1, 0, 0) (inward)
    rot_h_l = hand_world_euler((0, -1, 0), (-1, 0, 0))
    rot_h_r = hand_world_euler((0, -1, 0), ( 1, 0, 0))
    ik_hand_l = make_empty("IK_Hand_L", ( 0.355, -0.210, 1.305), rot_h_l, parent=piv_car)
    ik_hand_r = make_empty("IK_Hand_R", (-0.355, -0.210, 1.305), rot_h_r, parent=piv_car)
    pole_el_l = make_empty("Pole_Elbow_L", ( 0.55, -0.05, 1.05), parent=piv_car, disp='SPHERE')
    pole_el_r = make_empty("Pole_Elbow_R", (-0.55, -0.05, 1.05), parent=piv_car, disp='SPHERE')

    add_arm_ik_auto(arm, "Left",  ik_hand_l, pole_el_l, expected_elbow_dir=( 0.5, 0.5, -1))
    add_arm_ik_auto(arm, "Right", ik_hand_r, pole_el_r, expected_elbow_dir=(-0.5, 0.5, -1))
    add_copy_rot(arm, "LeftHand",  ik_hand_l)
    add_copy_rot(arm, "RightHand", ik_hand_r)
    curl_hand_fingers(arm, "Left",  1.0)
    curl_hand_fingers(arm, "Right", 1.0)

    bpy.ops.object.mode_set(mode='OBJECT')
    bake_and_export("VSquat", arm, meshes, mroot, 1, 31, 61, cam_loc=(1.95, -2.05, 1.45), cam_tgt=(0.0, -0.25, 0.90))


if __name__ == "__main__":
    build_hip_adduction()
    build_lying_leg_curl()
    build_bench_press()
    build_stair_climber()
    build_v_squat()
    print("\nALL 5 REBUILT BOMIO MIXAMO IK ANIMATIONS COMPLETED!")
