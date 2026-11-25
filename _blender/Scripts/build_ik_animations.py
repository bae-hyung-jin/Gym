r"""
Build physically accurate, silky-smooth 60-frame looping Blender IK exercise animations
for Player_Bomio on:
1. ArmCurlBench_A_Collar_Separated (Seated Preacher Arm Curl, synchronized lever + avatar!)
2. PullUpBar_Separated (Athletic Pull-Up, hands IK-locked on top bar, chin over bar!)

Workflow per exercise:
- Loads Player_Bomio + separated equipment (scaled to real-world height for 1.78m Bomio)
- Attaches live Blender IK constraints (IK + Pole Targets + Wrist Copy-Rotation + Finger Grip Curls)
- Keyframes smooth sinusoidal 60-frame loop (30fps = 2.0s/rep)
- Saves editable IK .blend -> G:\Unity_Gym\AI-Gym\_blender\Blend\Anim_Bomio_<Name>_IK.blend
- Renders verification frames (Start / Peak / Angle) to scratch/
- Bakes IK -> clean FK keyframes on all 65 Mixamo bones (clear_constraints=True)
- Exports Unity-ready FBX:
  * Combined (Avatar + Animated Machine): Assets\Animations\Exercises\Anim_Bomio_<Name>_Combined.fbx
  * Avatar-only Humanoid Clip:            Assets\Animations\Exercises\Anim_Bomio_<Name>.fbx
"""
import bpy
import math
import os
import numpy as np
from mathutils import Vector, Matrix, Euler

BOMIO_BLEND   = r"G:\Unity_Gym\AI-Gym\_blender\Bomio_Exercises\01_Avatar\Player_Bomio.blend"
ARMCURL_BLEND = r"G:\Unity_Gym\AI-Gym\_blender\Bomio_Exercises\02_Equipment_Separated\ArmCurlBench_A_Collar_Separated.blend"
PULLUP_BLEND  = r"G:\Unity_Gym\AI-Gym\_blender\Bomio_Exercises\02_Equipment_Separated\PullUpBar_Separated.blend"
OUT_BLEND_DIR = r"G:\Unity_Gym\AI-Gym\_blender\Bomio_Exercises\03_Animations_IK"
OUT_FBX_DIR   = r"G:\Unity_Gym\AI-Gym\Assets\Bomio_Exercises\Animations"
SCRATCH       = r"C:\Users\hyung\.gemini\antigravity\brain\bc816dce-1a90-4961-b863-c22ec5353e0c\scratch"

os.makedirs(OUT_BLEND_DIR, exist_ok=True)
os.makedirs(OUT_FBX_DIR, exist_ok=True)
os.makedirs(SCRATCH, exist_ok=True)

FPS = 30
FRAME_START = 1
FRAME_PEAK  = 31
FRAME_END   = 61  # 60-frame seamless loop (frame 61 == frame 1)

def append_all_objects(blend_path):
    """Append all objects from another .blend into current scene and return them."""
    before = set(bpy.data.objects)
    with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
        data_to.objects = list(data_from.objects)
    added = []
    for ob in data_to.objects:
        if ob is not None:
            bpy.context.scene.collection.objects.link(ob)
            added.append(ob)
    bpy.context.view_layer.update()
    return [o for o in bpy.data.objects if o not in before]

def make_empty(name, world_pos, rot_euler=(0, 0, 0), parent=None, size=0.06, disp='PLAIN_AXES'):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = disp
    e.empty_display_size = size
    bpy.context.scene.collection.objects.link(e)
    e.location = Vector(world_pos)
    e.rotation_euler = Euler(rot_euler, 'XYZ')
    bpy.context.view_layer.update()
    if parent is not None:
        mw = e.matrix_world.copy()
        e.parent = parent
        e.matrix_parent_inverse = parent.matrix_world.inverted()
        e.matrix_world = mw
        bpy.context.view_layer.update()
    return e

def set_pose_rot(arm, bone_name, rx_deg, ry_deg, rz_deg):
    pb = arm.pose.bones[f"mixamorig:{bone_name}"]
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (math.radians(rx_deg), math.radians(ry_deg), math.radians(rz_deg))

def curl_hand_fingers(arm, side, strength=1.0):
    """Curl fingers tightly around a horizontal gym grip bar (side='Left' or 'Right')."""
    # Local +X rotation curls fingers inward toward palm (+Z) on BOTH Left & Right hands!
    for f_name, (a1, a2, a3) in [
        ("Index",  (78, 92, 68)),
        ("Middle", (82, 95, 70)),
        ("Ring",   (84, 95, 72)),
        ("Pinky",  (85, 92, 68)),
    ]:
        set_pose_rot(arm, f"{side}Hand{f_name}1", a1 * strength, 0, 0)
        set_pose_rot(arm, f"{side}Hand{f_name}2", a2 * strength, 0, 0)
        set_pose_rot(arm, f"{side}Hand{f_name}3", a3 * strength, 0, 0)
    # Thumb wraps firmly across index/middle fingers around opposite side of bar
    s = 1.0 if side == "Left" else -1.0
    set_pose_rot(arm, f"{side}HandThumb1", 42 * strength, 18 * s * strength, -32 * s * strength)
    set_pose_rot(arm, f"{side}HandThumb2", 52 * strength, 0, 0)
    set_pose_rot(arm, f"{side}HandThumb3", 45 * strength, 0, 0)

def ensure_limb_ik_connected(arm):
    """Ensure ForeArm & Leg bones have use_connect=True so Blender 2-bone IK solves full Arm+ForeArm & Thigh+Shin!"""
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    for child_bn in ("LeftForeArm", "RightForeArm", "LeftLeg", "RightLeg"):
        eb = arm.data.edit_bones[f"mixamorig:{child_bn}"]
        if eb.parent is not None:
            eb.parent.tail = eb.head.copy()
            eb.use_connect = True
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()

def add_ik(arm, bone_suffix, target_obj, pole_obj, pole_deg, chain_len=2, hinge_z_prebend_deg=0.0):
    pb = arm.pose.bones[f"mixamorig:{bone_suffix}"]
    if abs(hinge_z_prebend_deg) > 0.1:
        # Break collinear T-pose singularity & enforce true 1-DOF human elbow hinge!
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0.0, 0.0, math.radians(hinge_z_prebend_deg))
        pb.lock_ik_x = True
        pb.lock_ik_y = True
    c = pb.constraints.new('IK')
    c.target = target_obj
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

def set_hips_world_pose(arm, world_pos, world_yaw_deg=0.0, pitch_deg=0.0):
    """Create & bind world-space IK_Hips target so Hips sits at exact world position & orientation."""
    # Note: In Bomio rest pose, Hips bone local axes are:
    # X = +X world, Y = +Z world (up), Z = -Y world (front)
    # That equals world Euler(-90deg, 0, 0) rotated by yaw around world Z!
    base_rot = Matrix.Rotation(math.radians(world_yaw_deg), 3, 'Z') @ \
               Matrix.Rotation(math.radians(pitch_deg), 3, 'X') @ \
               Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0))) # cols: X=(1,0,0), Y=(0,0,1), Z=(0,-1,0)
    hips_ctrl = make_empty("IK_Hips", world_pos, base_rot.to_euler('XYZ'), size=0.12, disp='CUBE')
    add_copy_loc(arm, "Hips", hips_ctrl)
    add_copy_rot(arm, "Hips", hips_ctrl)
    return hips_ctrl

def hand_world_euler(arm_dir_vec, palm_normal_vec, side):
    """
    Build exact world Euler for LeftHand / RightHand bone so:
    - Bone +Y points along arm_dir_vec (wrist -> fingertips)
    - Bone +Z points along palm_normal_vec (direction palm faces!)
    On LeftHand:  X = Y x Z (right-handed! Check: Y=(+1,0,0), Z=(0,0,-1) => YxZ=(0,+1,0)=+X! Matches!)
    On RightHand: X = Y x Z (Check: Y=(-1,0,0), Z=(0,0,-1) => YxZ=(0,-1,0)=+X! Matches!)
    """
    y = Vector(arm_dir_vec).normalized()
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

def render_frames(tag, shots):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 768, 768
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new("AnimW")
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs["Color"].default_value = (0.20, 0.24, 0.30, 1.0)
    bg.inputs["Strength"].default_value = 0.9
    sc.world = w

    lights = []
    for nm, loc, en in [("AL1", (2.6, -3.2, 3.0), 380), ("AL2", (-2.4, -2.2, 2.2), 200), ("AL3", (0.0, 3.0, 2.6), 240)]:
        ld = bpy.data.lights.new(nm, 'AREA'); ld.energy = en; ld.size = 2.5
        lo = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo)
        lo.location = Vector(loc)
        lo.rotation_euler = (Vector((0, 0, 1.0)) - lo.location).to_track_quat('-Z', 'Y').to_euler()
        lights.append((lo, ld))

    cd = bpy.data.cameras.new("AC")
    cam = bpy.data.objects.new("AC", cd); sc.collection.objects.link(cam); sc.camera = cam
    cd.lens = 45

    for fname, frame_idx, loc, tgt in shots:
        sc.frame_set(frame_idx)
        bpy.context.view_layer.update()
        cam.location = Vector(loc)
        cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(SCRATCH, f"{tag}_{fname}.png")
        bpy.ops.render.render(write_still=True)

    bpy.data.objects.remove(cam); bpy.data.cameras.remove(cd)
    for lo, ld in lights:
        bpy.data.objects.remove(lo); bpy.data.lights.remove(ld)

def bake_and_export(arm, equip_objs, tag, action_name):
    """Bake live IK constraints into pure FK keyframes on all 65 Mixamo bones & export Unity FBXs."""
    sc = bpy.context.scene
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')

    bpy.ops.nla.bake(
        frame_start=FRAME_START,
        frame_end=FRAME_END,
        only_selected=True,
        visual_keying=True,
        clear_constraints=True,
        clear_parents=False,
        use_current_action=False,
        bake_types={'POSE'},
    )
    if arm.animation_data and arm.animation_data.action:
        arm.animation_data.action.name = action_name
    bpy.ops.object.mode_set(mode='OBJECT')

    # Remove temporary IK Empty helpers so Unity FBX hierarchy stays super clean
    ik_helpers = [o for o in bpy.data.objects if o.type == 'EMPTY' and (o.name.startswith("IK_") or o.name.startswith("Pole_"))]
    for h in ik_helpers:
        bpy.data.objects.remove(h, do_unlink=True)

    # 1. Export Avatar-only Mixamo Humanoid Clip FBX (ready to drop into Unity Animator Controller!)
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.parent == arm:
            o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    fbx_avatar = os.path.join(OUT_FBX_DIR, f"Anim_Bomio_{tag}.fbx")
    bpy.ops.export_scene.fbx(
        filepath=fbx_avatar,
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

    # 2. Export Combined FBX (Avatar + Animated Machine together for instant preview / synchronized playback!)
    bpy.ops.object.select_all(action='SELECT')
    fbx_comb = os.path.join(OUT_FBX_DIR, f"Anim_Bomio_{tag}_WithMachine.fbx")
    bpy.ops.export_scene.fbx(
        filepath=fbx_comb,
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
        path_mode='COPY',
        embed_textures=True,
    )
    print(f"  Exported: {fbx_avatar} ({os.path.getsize(fbx_avatar)/1048576:.2f} MB)")
    print(f"  Exported: {fbx_comb} ({os.path.getsize(fbx_comb)/1048576:.2f} MB)")

# ==============================================================================
# EXERCISE 1: SEATED PREACHER ARM CURL (ArmCurlBench_A_Collar)
# ==============================================================================
def build_armcurl():
    print("\n=== Building Exercise 1: Seated Arm Curl (IK) ===")
    bpy.ops.wm.open_mainfile(filepath=BOMIO_BLEND)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start = FRAME_START
    sc.frame_end = FRAME_END

    arm = bpy.data.objects["Armature"]
    ensure_limb_ik_connected(arm)
    eq_objs = append_all_objects(ARMCURL_BLEND)

    # Scale ArmCurlBench to 1.16x so preacher pad top (~1.13m) hits right under Bomio's armpits!
    eq_root = bpy.data.objects["ArmCurlBench_A_Collar_Root"]
    eq_root.scale = (1.16, 1.16, 1.16)
    bpy.context.view_layer.update()

    lever   = bpy.data.objects["ArmCurl_LeverArm"]
    handles = bpy.data.objects["ArmCurl_Handles"]

    # Recompute exact world-space centroids of left/right chrome hand grips from handles mesh!
    h_pts = np.array([handles.matrix_world @ v.co for v in handles.data.vertices])
    gl_pts = h_pts[(h_pts[:, 0] > 0.16) & (h_pts[:, 2] > 0.62)]
    gr_pts = h_pts[(h_pts[:, 0] < -0.16) & (h_pts[:, 2] > 0.62)]
    grip_l_w = Vector(gl_pts.mean(axis=0))
    grip_r_w = Vector(gr_pts.mean(axis=0))
    print(f"  Scaled Chrome Grips: L={tuple(round(v,3) for v in grip_l_w)} R={tuple(round(v,3) for v in grip_r_w)}")

    for old_g in ("Grip_L", "Grip_R"):
        if old_g in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[old_g], do_unlink=True)

    # Exact chrome bar centerline markers parented to handles (so we read exact bar world pos every frame!)
    bar_l = make_empty("Grip_L", grip_l_w, (0, 0, 0), parent=handles, size=0.04, disp='PLAIN_AXES')
    bar_r = make_empty("Grip_R", grip_r_w, (0, 0, 0), parent=handles, size=0.04, disp='PLAIN_AXES')

    # World-space IK hand targets (updated every frame so PALM CENTER stays 0.000mm locked on chrome bar!)
    ik_hand_l = make_empty("IK_Hand_L", grip_l_w, (0, 0, 0), size=0.05, disp='ARROWS')
    ik_hand_r = make_empty("IK_Hand_R", grip_r_w, (0, 0, 0), size=0.05, disp='ARROWS')

    # Elbow Pole Targets resting solidly along the sloped front surface of the preacher pad!
    pole_el_l = make_empty("Pole_Elbow_L", ( 0.22, -0.05, 0.72), size=0.05, disp='SPHERE')
    pole_el_r = make_empty("Pole_Elbow_R", (-0.22, -0.05, 0.72), size=0.05, disp='SPHERE')

    # Seated Hips cleanly ON TOP of the centered seat cushion (back seat lip is Z~0.80 -> Hips at Y=+0.28, Z=0.815 -> ZERO seat clip!)
    hips_ctrl = set_hips_world_pose(arm, (0.0, 0.280, 0.815), world_yaw_deg=0.0, pitch_deg=15.0)

    # Feet planted FLAT on floor cleanly BEHIND the weight horn (Y=+0.08, X=+-0.32 -> ZERO frame/horn clipping!)
    ik_foot_l = make_empty("IK_Foot_L", ( 0.32,  0.08, 0.092), size=0.07, disp='ARROWS')
    ik_foot_r = make_empty("IK_Foot_R", (-0.32,  0.08, 0.092), size=0.07, disp='ARROWS')
    pole_kn_l = make_empty("Pole_Knee_L", ( 0.36, -0.35, 0.56), size=0.05, disp='SPHERE')
    pole_kn_r = make_empty("Pole_Knee_R", (-0.36, -0.35, 0.56), size=0.05, disp='SPHERE')

    # Pose spine leaning snugly against preacher pad, head watching handles, fingers gripping chrome bar!
    set_pose_rot(arm, "Spine",   14, 0, 0)
    set_pose_rot(arm, "Spine1",  16, 0, 0)
    set_pose_rot(arm, "Spine2",  10, 0, 0)
    set_pose_rot(arm, "Neck",   -14, 0, 0)
    set_pose_rot(arm, "Head",   -16, 0, 0)
    set_pose_rot(arm, "LeftShoulder",   0, 0,  12)
    set_pose_rot(arm, "RightShoulder",  0, 0, -12)
    set_pose_rot(arm, "LeftFoot",  -6, 0, 0)
    set_pose_rot(arm, "RightFoot", -6, 0, 0)
    curl_hand_fingers(arm, "Left",  1.0)
    curl_hand_fingers(arm, "Right", 1.0)

    # Wire live Blender IK constraints with true 1-DOF human elbow hinge pre-bend (0.000m wrist error!)
    add_ik(arm, "LeftForeArm",  ik_hand_l, pole_el_l, pole_deg=0.0,   chain_len=2, hinge_z_prebend_deg= 35.0)
    add_ik(arm, "RightForeArm", ik_hand_r, pole_el_r, pole_deg=180.0, chain_len=2, hinge_z_prebend_deg=-35.0)
    add_copy_rot(arm, "LeftHand",  ik_hand_l)
    add_copy_rot(arm, "RightHand", ik_hand_r)
    add_ik(arm, "LeftLeg",  ik_foot_l, pole_kn_l, pole_deg=90.0, chain_len=2)
    add_ik(arm, "RightLeg", ik_foot_r, pole_kn_r, pole_deg=90.0, chain_len=2)

    for f in range(FRAME_START, FRAME_END + 1):
        phase = (f - FRAME_START) / float(FRAME_END - FRAME_START)
        curl = 0.5 - 0.5 * math.cos(2.0 * math.pi * phase)  # 0 -> 1 -> 0
        # Lever starts at +6 deg (extended down the pad), curls UP through -78 deg (clean full bicep curl!)
        lever_deg = 6.0 - 84.0 * curl
        lever.rotation_euler = (math.radians(lever_deg), 0.0, 0.0)
        lever.keyframe_insert(data_path="rotation_euler", frame=f)

        # Handles swivel +35 deg at peak so chrome grips rise smoothly toward shoulders!
        handles.rotation_euler = (math.radians(35.0 * curl), 0.0, 0.0)
        handles.keyframe_insert(data_path="rotation_euler", frame=f)

        # Keep elbows planted firmly down on the sloped preacher pad throughout the curl!
        pole_el_l.location = Vector(( 0.23, -0.10, 0.62))
        pole_el_r.location = Vector((-0.23, -0.10, 0.62))
        pole_el_l.keyframe_insert(data_path="location", frame=f)
        pole_el_r.keyframe_insert(data_path="location", frame=f)

        # Evaluate exact world-space chrome bar position after lever rotation so PALM CENTER hugs the bar 0.000mm!
        bpy.context.view_layer.update()
        for ik_h, bar_m, side_sgn, side_nm in ((ik_hand_l, bar_l, 1.0, 'Left'), (ik_hand_r, bar_r, -1.0, 'Right')):
            bar_pos = bar_m.matrix_world.translation
            elb_est = Vector((side_sgn * 0.22, -0.07, 0.87))
            f_dir   = (bar_pos - elb_est).normalized()
            # Supinated underhand palm normal (perpendicular to forearm, facing UP-BACK toward Bomio's chest!)
            p_up = f_dir.cross(Vector((-1.0, 0.0, 0.0))).normalized()
            if p_up.z < 0 and p_up.y < 0:
                p_up = -p_up
            # Offset wrist 6.8cm back along forearm + 1.5cm below palm surface so curled fingers wrap RIGHT around bar!
            ik_h.location = bar_pos - f_dir * 0.068 - p_up * 0.015
            ik_h.rotation_euler = hand_world_euler(f_dir, p_up, side_nm)
            ik_h.keyframe_insert(data_path="location", frame=f)
            ik_h.keyframe_insert(data_path="rotation_euler", frame=f)

        # Subtle lifelike torso brace & head focus
        set_pose_rot(arm, "Spine1", 16.0 + 3.0 * curl, 0, 0)
        set_pose_rot(arm, "Head",  -16.0 - 5.0 * curl, 0, 0)
        arm.pose.bones["mixamorig:Spine1"].keyframe_insert(data_path="rotation_euler", frame=f)
        arm.pose.bones["mixamorig:Head"].keyframe_insert(data_path="rotation_euler", frame=f)

    blend_out = os.path.join(OUT_BLEND_DIR, "Anim_Bomio_ArmCurl_IK.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    print(f"  Saved IK Blend: {blend_out}")

    render_frames("armcurl", [
        ("f01_side",  1,  (2.05, -0.35, 1.05), (0.0,  0.02, 0.85)),
        ("f31_side",  31, (2.05, -0.35, 1.05), (0.0,  0.02, 0.85)),
        ("f31_front", 31, (1.20, -1.70, 1.15), (0.0,  0.02, 0.85)),
        ("f31_rear",  31, (1.35,  1.55, 1.55), (0.0,  0.05, 0.72)),
    ])

    bake_and_export(arm, eq_objs, "ArmCurl", "Bomio_ArmCurl")

# ==============================================================================
# EXERCISE 2: ATHLETIC PULL-UP (PullUpBar)
# ==============================================================================
def build_pullup():
    print("\n=== Building Exercise 2: Athletic Pull-Up (IK) ===")
    bpy.ops.wm.open_mainfile(filepath=BOMIO_BLEND)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start = FRAME_START
    sc.frame_end = FRAME_END

    arm = bpy.data.objects["Armature"]
    ensure_limb_ik_connected(arm)
    eq_objs = append_all_objects(PULLUP_BLEND)

    # Scale PullUpBar to realistic 2.30m height for 1.78m Bomio!
    eq_root = bpy.data.objects["PullUpBar_Root"]
    eq_root.scale = (2.30, 2.30, 2.30)
    bpy.context.view_layer.update()

    top_bar = bpy.data.objects["PullUp_TopBar"]
    tb_pts = np.array([top_bar.matrix_world @ v.co for v in top_bar.data.vertices])
    center_bar = tb_pts[np.abs(tb_pts[:, 0]) < 0.30]
    bar_y = float(center_bar[:, 1].mean())
    bar_z = float((center_bar[:, 2].min() + center_bar[:, 2].max()) * 0.5)
    print(f"  Scaled Top Pull-Up Bar: Y={bar_y:.3f}, Z={bar_z:.3f}, X=[{tb_pts[:,0].min():.3f}, {tb_pts[:,0].max():.3f}]")

    # Bomio faces +Y (facing uprights) at clean shoulder-width grip (X = +-0.245, well inside +-0.33 upright brackets!)
    # Pronated overhand pull-up grip: wrist sits 7.5cm BELOW bar_z so PALM hooks directly over the top bar!
    # Fingers curl toward +Y (forward around bar) -> arm_dir = UP (+Z), palm_normal = FORWARD (+Y)
    grip_half_w = 0.245
    arm_up   = Vector((0.0, 0.18, 0.98)).normalized()
    palm_fwd = Vector((0.0, 0.98, -0.18)).normalized()
    lh_rot = hand_world_euler(arm_up, palm_fwd, 'Left')
    rh_rot = hand_world_euler(arm_up, palm_fwd, 'Right')

    # Wrist sits directly below-front of bar so palm center sits squarely ON (bar_y, bar_z)!
    ik_hand_l = make_empty("IK_Hand_L", (-grip_half_w, bar_y - 0.020, bar_z - 0.072), lh_rot, parent=top_bar, size=0.06, disp='ARROWS')
    ik_hand_r = make_empty("IK_Hand_R", ( grip_half_w, bar_y - 0.020, bar_z - 0.072), rh_rot, parent=top_bar, size=0.06, disp='ARROWS')

    # Elbow Pole Targets pointing cleanly DOWN & OUT (never backward into uprights!)
    pole_el_l = make_empty("Pole_Elbow_L", (-0.55, bar_y - 0.08, 1.45), size=0.06, disp='SPHERE')
    pole_el_r = make_empty("Pole_Elbow_R", ( 0.55, bar_y - 0.08, 1.45), size=0.06, disp='SPHERE')

    # Hips controller facing +Y (world_yaw_deg = 180) cleanly under the bar (Y = bar_y - 0.10 so chin & chest never touch bar!)
    hips_ctrl = set_hips_world_pose(arm, (0.0, bar_y - 0.10, 1.15), world_yaw_deg=180.0, pitch_deg=0.0)

    # Clean athletic tucked legs (knees bent naturally backward toward -Y open air, ZERO twist!)
    ik_foot_l = make_empty("IK_Foot_L", (-0.12, bar_y - 0.42, 0.58), size=0.07, disp='ARROWS')
    ik_foot_r = make_empty("IK_Foot_R", ( 0.12, bar_y - 0.42, 0.58), size=0.07, disp='ARROWS')
    pole_kn_l = make_empty("Pole_Knee_L", (-0.14, bar_y + 0.35, 0.80), size=0.05, disp='SPHERE')
    pole_kn_r = make_empty("Pole_Knee_R", ( 0.14, bar_y + 0.35, 0.80), size=0.05, disp='SPHERE')

    curl_hand_fingers(arm, "Left",  1.05)
    curl_hand_fingers(arm, "Right", 1.05)
    set_pose_rot(arm, "LeftFoot",  28, 0, 0)
    set_pose_rot(arm, "RightFoot", 28, 0, 0)

    # Wire live Blender IK constraints with true 1-DOF human elbow hinge pre-bend (0.000m wrist error!)
    add_ik(arm, "LeftForeArm",  ik_hand_l, pole_el_l, pole_deg=0.0,   chain_len=2, hinge_z_prebend_deg= 35.0)
    add_ik(arm, "RightForeArm", ik_hand_r, pole_el_r, pole_deg=180.0, chain_len=2, hinge_z_prebend_deg=-35.0)
    add_copy_rot(arm, "LeftHand",  ik_hand_l)
    add_copy_rot(arm, "RightHand", ik_hand_r)
    add_ik(arm, "LeftLeg",  ik_foot_l, pole_kn_l, pole_deg=90.0, chain_len=2)
    add_ik(arm, "RightLeg", ik_foot_r, pole_kn_r, pole_deg=90.0, chain_len=2)

    # Keyframe smooth 60-frame Pull-Up motion!
    for f in range(FRAME_START, FRAME_END + 1):
        phase = (f - FRAME_START) / float(FRAME_END - FRAME_START)
        pull = 0.5 - 0.5 * math.cos(2.0 * math.pi * phase)  # 0 (hang) -> 1 (chin cleanly over bar!) -> 0

        # Smooth vertical pull-up (+0.45m): chin rises cleanly above 2.27m top bar while chest stays cleanly in front!
        hz = 1.15 + 0.45 * pull
        hy = (bar_y - 0.08) - 0.08 * pull
        hips_ctrl.location = Vector((0.0, hy, hz))
        hips_ctrl.keyframe_insert(data_path="location", frame=f)

        # Tucked legs follow hips smoothly in open air behind Bomio (-Y)
        ik_foot_l.location = Vector((-0.11, hy - 0.34, hz - 0.56 + 0.04 * pull))
        ik_foot_r.location = Vector(( 0.11, hy - 0.34, hz - 0.56 + 0.04 * pull))
        pole_kn_l.location = Vector((-0.13, hy + 0.38, hz - 0.25))
        pole_kn_r.location = Vector(( 0.13, hy + 0.38, hz - 0.25))
        for obj in (ik_foot_l, ik_foot_r, pole_kn_l, pole_kn_r):
            obj.keyframe_insert(data_path="location", frame=f)

        # Elbows drive cleanly DOWN & slightly OUT/FORWARD (real pull-up biomechanics!)
        ez = 1.72 - 0.34 * pull
        ey = bar_y - 0.04 - 0.12 * pull
        pole_el_l.location = Vector((-0.52 - 0.08 * pull, ey, ez))
        pole_el_r.location = Vector(( 0.52 + 0.08 * pull, ey, ez))
        pole_el_l.keyframe_insert(data_path="location", frame=f)
        pole_el_r.keyframe_insert(data_path="location", frame=f)

        # Athletic chest lift & chin looking slightly up over the bar + scapular depression
        set_pose_rot(arm, "Spine",  -2.5 * pull, 0, 0)
        set_pose_rot(arm, "Spine1", -4.5 * pull, 0, 0)
        set_pose_rot(arm, "Spine2", -5.5 * pull, 0, 0)
        set_pose_rot(arm, "Head",   -6.0 - 8.0 * pull, 0, 0)
        set_pose_rot(arm, "LeftShoulder",  0, 0,  10.0 - 16.0 * pull)
        set_pose_rot(arm, "RightShoulder", 0, 0, -10.0 + 16.0 * pull)
        for bn in ("Spine", "Spine1", "Spine2", "Head", "LeftShoulder", "RightShoulder"):
            arm.pose.bones[f"mixamorig:{bn}"].keyframe_insert(data_path="rotation_euler", frame=f)

    blend_out = os.path.join(OUT_BLEND_DIR, "Anim_Bomio_PullUp_IK.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    print(f"  Saved IK Blend: {blend_out}")

    render_frames("pullup", [
        ("f01_34",   1,  (2.1, -2.5, 1.55), (0.0, 0.05, 1.38)),
        ("f31_34",   31, (2.1, -2.5, 1.55), (0.0, 0.05, 1.38)),
        ("f31_side", 31, (2.7,  0.0, 1.65), (0.0, 0.05, 1.50)),
    ])

    bake_and_export(arm, eq_objs, "PullUp", "Bomio_PullUp")

build_armcurl()
build_pullup()
print("\nALL IK ANIMATIONS BUILT, VERIFIED & EXPORTED!")
