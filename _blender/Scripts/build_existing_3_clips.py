r"""
Retarget & refine Player_Bomio exercise animations directly synced frame-for-frame
to the 3 existing animated gym machines in Assets/Gym/1124/:
1. ChestPress_ani_done.fbx  (frames 2..73) -> Anim_Bomio_ChestPress
2. LatPulldown_ani.fbx      (frames 2..61) -> Anim_Bomio_LatPulldown
3. LegExtension_ani.fbx     (frames 2..60) -> Anim_Bomio_LegExtension

Per machine:
- Imports existing animated machine FBX
- Appends Player_Bomio (packed black tracksuit + 30-bone articulated fingers)
- Retargets all 65 Mixamo bones from old demo character -> Player_Bomio
- Refines posture/grips where Ch06 differed from Ch38 (e.g. LatPulldown clean bar clearance + 0mm IK grip lock!)
- Removes old pink/hoodie demo character from the scene
- Saves .blend preview, pure Player_Bomio Humanoid clip FBX, and clean Machine-Only animated FBX!
"""
import bpy
import math
import os
import numpy as np
from mathutils import Vector, Matrix, Euler

BOMIO_BLEND = r"G:\Unity_Gym\AI-Gym\_blender\Bomio_Exercises\01_Avatar\Player_Bomio.blend"
OUT_BLEND   = r"G:\Unity_Gym\AI-Gym\_blender\Bomio_Exercises\03_Animations_IK"
OUT_ANIM    = r"G:\Unity_Gym\AI-Gym\Assets\Bomio_Exercises\Animations"
OUT_EQUIP   = r"G:\Unity_Gym\AI-Gym\Assets\Bomio_Exercises\Equipment"
SCRATCH     = r"C:\Users\hyung\.gemini\antigravity\brain\bc816dce-1a90-4961-b863-c22ec5353e0c\scratch"

os.makedirs(OUT_BLEND, exist_ok=True)
os.makedirs(OUT_ANIM, exist_ok=True)
os.makedirs(OUT_EQUIP, exist_ok=True)

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
    return arm, meshes

def strip_prefix(name):
    return name.split(':', 1)[1] if ':' in name else name

def retarget_mixamo(src_arm, dst_arm, f_start, f_end, hips_world_offset=(0.0, 0.0, 0.0)):
    """Retarget all matching Mixamo bones from src_arm -> dst_arm using world-space rotation & Hips location."""
    src_map = {}
    for b in src_arm.data.bones:
        if b.name.startswith("mixamorig"):
            src_map[strip_prefix(b.name)] = b.name

    # Optional Hips offset Empty so we can cleanly adjust seating depth (e.g. LatPulldown bar clearance!)
    hips_off_e = None
    if any(abs(v) > 1e-4 for v in hips_world_offset):
        hips_off_e = bpy.data.objects.new("_TmpHipsTarget", None)
        bpy.context.scene.collection.objects.link(hips_off_e)

    for pb in dst_arm.pose.bones:
        suf = strip_prefix(pb.name)
        if suf not in src_map:
            continue
        src_bn = src_map[suf]
        cr = pb.constraints.new('COPY_ROTATION')
        cr.target = src_arm
        cr.subtarget = src_bn
        cr.target_space = 'WORLD'
        cr.owner_space = 'WORLD'
        if suf == "Hips":
            if hips_off_e is None:
                cl = pb.constraints.new('COPY_LOCATION')
                cl.target = src_arm
                cl.subtarget = src_bn
                cl.target_space = 'WORLD'
                cl.owner_space = 'WORLD'
            else:
                # Keyframe offset world location each frame
                off_v = Vector(hips_world_offset)
                for f in range(f_start, f_end + 1):
                    bpy.context.scene.frame_set(f)
                    bpy.context.view_layer.update()
                    sh = src_arm.matrix_world @ src_arm.pose.bones[src_bn].head
                    hips_off_e.location = sh + off_v
                    hips_off_e.keyframe_insert(data_path="location", frame=f)
                cl = pb.constraints.new('COPY_LOCATION')
                cl.target = hips_off_e
                cl.target_space = 'WORLD'
                cl.owner_space = 'WORLD'

    # Bake retargeted motion cleanly into pure FK keyframes on dst_arm
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    dst_arm.select_set(True)
    bpy.context.view_layer.objects.active = dst_arm
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
    if hips_off_e is not None:
        bpy.data.objects.remove(hips_off_e, do_unlink=True)

def ensure_elbow_ik_connected(arm):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    for child_bn in ("LeftForeArm", "RightForeArm"):
        eb = arm.data.edit_bones[f"mixamorig:{child_bn}"]
        if eb.parent is not None:
            eb.parent.tail = eb.head.copy()
            eb.use_connect = True
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()

def lock_hands_to_bars(arm, bar_l_obj, bar_r_obj, f_start, f_end, grip_offset_z=-0.068, pole_l_pos=(-0.55, -0.30, 1.05), pole_r_pos=(0.55, -0.30, 1.05)):
    """Post-pass 2-bone Arm IK lock so Bomio's hands stay 0.000mm locked onto moving LatPulldown bars!"""
    ensure_elbow_ik_connected(arm)

    def make_e(nm, loc):
        e = bpy.data.objects.new(nm, None)
        bpy.context.scene.collection.objects.link(e)
        e.location = Vector(loc)
        return e

    # Determine which bar is on Bomio's Left vs Right at f_start!
    bpy.context.scene.frame_set(f_start)
    bpy.context.view_layer.update()
    lh_w = arm.matrix_world @ arm.pose.bones["mixamorig:LeftHand"].head
    bl_c = sum((bar_l_obj.matrix_world @ Vector(c) for c in bar_l_obj.bound_box), Vector()) / 8.0
    br_c = sum((bar_r_obj.matrix_world @ Vector(c) for c in bar_r_obj.bound_box), Vector()) / 8.0
    if (br_c - lh_w).length < (bl_c - lh_w).length:
        bar_l_obj, bar_r_obj = bar_r_obj, bar_l_obj

    ik_l = make_e("_IK_L", (0, 0, 0))
    ik_r = make_e("_IK_R", (0, 0, 0))
    # Pole targets placed on Left/Right side matching bar_l / bar_r X signs
    sgn_l = 1.0 if (sum((bar_l_obj.matrix_world @ Vector(c) for c in bar_l_obj.bound_box), Vector()) / 8.0).x >= 0 else -1.0
    pl = make_e("_Pole_L", (sgn_l * 0.58, -0.35, 1.05))
    pr = make_e("_Pole_R", (-sgn_l * 0.58, -0.35, 1.05))

    for f in range(f_start, f_end + 1):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        cl = sum((bar_l_obj.matrix_world @ Vector(c) for c in bar_l_obj.bound_box), Vector()) / 8.0
        cr = sum((bar_r_obj.matrix_world @ Vector(c) for c in bar_r_obj.bound_box), Vector()) / 8.0
        ik_l.location = cl + Vector((0.0, 0.0, grip_offset_z))
        ik_r.location = cr + Vector((0.0, 0.0, grip_offset_z))
        ik_l.keyframe_insert(data_path="location", frame=f)
        ik_r.keyframe_insert(data_path="location", frame=f)

    # Add 2-bone IK on LeftForeArm & RightForeArm with 1-DOF elbow hinge!
    for bn, ik_t, pl_t, pdeg, preb in [
        ("LeftForeArm",  ik_l, pl, 0.0,    35.0),
        ("RightForeArm", ik_r, pr, 180.0, -35.0),
    ]:
        pb = arm.pose.bones[f"mixamorig:{bn}"]
        pb.lock_ik_x = True
        pb.lock_ik_y = True
        c = pb.constraints.new('IK')
        c.target = ik_t
        c.pole_target = pl_t
        c.pole_angle = math.radians(pdeg)
        c.chain_count = 2

    # Curl fingers tightly around bar across all frames!
    for side in ("Left", "Right"):
        for f_name, (a1, a2, a3) in [("Index",(78,90,65)),("Middle",(82,92,68)),("Ring",(84,92,68)),("Pinky",(84,90,65))]:
            for k, ang in ((1, a1), (2, a2), (3, a3)):
                pb = arm.pose.bones[f"mixamorig:{side}Hand{f_name}{k}"]
                pb.rotation_mode = 'XYZ'
                pb.rotation_euler = (math.radians(ang), 0.0, 0.0)
                pb.keyframe_insert(data_path="rotation_euler", frame=f_start)
                pb.keyframe_insert(data_path="rotation_euler", frame=f_end)

    # Bake arm IK cleanly back into the existing action
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
        use_current_action=True,
        bake_types={'POSE'},
    )
    bpy.ops.object.mode_set(mode='OBJECT')
    for h in (ik_l, ik_r, pl, pr):
        bpy.data.objects.remove(h, do_unlink=True)

def render_check(tag, f_start, f_peak, cam_loc, cam_tgt):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = sc.render.resolution_y = 640
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new("CW")
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs["Color"].default_value = (0.20, 0.24, 0.30, 1.0)
    bg.inputs["Strength"].default_value = 0.9
    sc.world = w

    lights = []
    for nm, loc, en in [("L1", (2.6, -3.2, 3.0), 360), ("L2", (-2.4, -2.2, 2.2), 180), ("L3", (0.0, 3.0, 2.6), 220)]:
        ld = bpy.data.lights.new(nm, 'AREA'); ld.energy = en; ld.size = 2.5
        lo = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo)
        lo.location = Vector(loc)
        lo.rotation_euler = (Vector((0, 0, 1.0)) - lo.location).to_track_quat('-Z', 'Y').to_euler()
        lights.append((lo, ld))

    cd = bpy.data.cameras.new("CC")
    cam = bpy.data.objects.new("CC", cd); sc.collection.objects.link(cam); sc.camera = cam
    cd.lens = 45
    cam.location = Vector(cam_loc)
    cam.rotation_euler = (Vector(cam_tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()

    for suf, fr in [("start", f_start), ("peak", f_peak)]:
        sc.frame_set(fr)
        bpy.context.view_layer.update()
        sc.render.filepath = os.path.join(SCRATCH, f"bomio_{tag}_{suf}.png")
        bpy.ops.render.render(write_still=True)

    bpy.data.objects.remove(cam); bpy.data.cameras.remove(cd)
    for lo, ld in lights:
        bpy.data.objects.remove(lo); bpy.data.lights.remove(ld)

def process_existing_machine(tag, src_fbx, f_start, f_peak, f_end, demo_prefixes, cam_loc, cam_tgt, hips_offset=(0,0,0), lat_bars=None):
    print(f"\n=== Processing {tag} ({f_start}..{f_end}, peak={f_peak}) ===")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=src_fbx, automatic_bone_orientation=False)
    bpy.context.view_layer.update()

    sc = bpy.context.scene
    sc.render.fps = 30
    sc.frame_start = f_start
    sc.frame_end = f_end

    src_arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    # Collect old demo character meshes to remove AFTER retargeting
    old_demo = [src_arm] + [o for o in bpy.data.objects if o.type == 'MESH' and (o.parent == src_arm or any(o.name.startswith(p) for p in demo_prefixes))]

    bomio_arm, bomio_meshes = append_bomio()
    retarget_mixamo(src_arm, bomio_arm, f_start, f_end, hips_world_offset=hips_offset)

    # Remove old demo character cleanly
    for o in old_demo:
        if o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.update()

    # Optional hand-bar IK lock (for LatPulldown so hands stay 0mm locked on Bar_Grip_L/R!)
    if lat_bars is not None:
        bl = bpy.data.objects.get(lat_bars[0])
        br = bpy.data.objects.get(lat_bars[1])
        if bl and br:
            lock_hands_to_bars(bomio_arm, bl, br, f_start, f_end, grip_offset_z=-0.068)

    # Rename action cleanly for Unity Animator
    if bomio_arm.animation_data and bomio_arm.animation_data.action:
        bomio_arm.animation_data.action.name = f"Bomio_{tag}"

    # Render visual verification (Start & Peak frames!)
    render_check(tag.lower(), f_start, f_peak, cam_loc, cam_tgt)

    # Save .blend (with Bomio + Machine synced)
    blend_out = os.path.join(OUT_BLEND, f"Anim_Bomio_{tag}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    print(f"  Saved Blend: {blend_out}")

    # Export 1: Pure Player_Bomio Humanoid Animation Clip FBX (ready for Unity Animator Controller!)
    bpy.ops.object.select_all(action='DESELECT')
    bomio_arm.name = "Armature" # Match Player_Bomio.fbx standard root name!
    bomio_arm.select_set(True)
    for m in bomio_meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = bomio_arm
    fbx_anim = os.path.join(OUT_ANIM, f"Anim_Bomio_{tag}.fbx")
    bpy.ops.export_scene.fbx(
        filepath=fbx_anim,
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

    # Export 2: Clean Machine-Only Animated FBX (without old pink/hoodie demo person!)
    bomio_set = {bomio_arm} | set(bomio_meshes)
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.data.objects:
        if o not in bomio_set and o.type in {'MESH', 'EMPTY'}:
            o.select_set(True)
    fbx_eq = os.path.join(OUT_EQUIP, f"{tag}_MachineOnly_Ani.fbx")
    bpy.ops.export_scene.fbx(
        filepath=fbx_eq,
        use_selection=True,
        object_types={'MESH', 'EMPTY'},
        use_mesh_modifiers=True,
        bake_anim=True,
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
    print(f"  Exported Avatar Clip:  {fbx_anim} ({os.path.getsize(fbx_anim)/1048576:.2f} MB)")
    print(f"  Exported Machine Only: {fbx_eq} ({os.path.getsize(fbx_eq)/1048576:.2f} MB)")

# 1. ChestPress (Ch38 -> Bomio exact match!)
process_existing_machine(
    tag="ChestPress",
    src_fbx=r"G:\Unity_Gym\AI-Gym\Assets\Gym\1124\ChestPress_ani_done.fbx",
    f_start=2, f_peak=37, f_end=73,
    demo_prefixes=("Ch38_", "Trainer_Smartwatch", "Cap", "Headset", "Mic"),
    cam_loc=(1.75, -1.85, 1.35), cam_tgt=(0.10, 0.05, 0.85),
    hips_offset=(0.0, 0.0, 0.0),
)

# 2. LatPulldown (Ch06 -> Bomio: seated squarely on Seat so hands reach 0.000m on Bar_Grip at Frame 2~61 AND bar clears chin!)
process_existing_machine(
    tag="LatPulldown",
    src_fbx=r"G:\Unity_Gym\AI-Gym\Assets\Gym\1124\LatPulldown_ani.fbx",
    f_start=2, f_peak=32, f_end=61,
    demo_prefixes=("Ch06",),
    cam_loc=(1.85, -2.10, 1.55), cam_tgt=(0.0, -0.15, 1.05),
    hips_offset=(0.0, 0.04, 0.05),
    lat_bars=("Bar_Grip_L", "Bar_Grip_R"),
)

# 3. LegExtension (Ch06 -> Bomio seated cleanly on Seat, pressing Ankle_Pad!)
process_existing_machine(
    tag="LegExtension",
    src_fbx=r"G:\Unity_Gym\AI-Gym\Assets\Gym\1124\LegExtension_ani.fbx",
    f_start=2, f_peak=32, f_end=60,
    demo_prefixes=("Ch06",),
    cam_loc=(1.80, -1.90, 1.30), cam_tgt=(0.10, 0.0, 0.72),
    hips_offset=(0.0, 0.01, -0.01),
)

# 4. PowerLegPress (Ch38 -> Bomio exact match!)
process_existing_machine(
    tag="PowerLegPress",
    src_fbx=r"G:\Unity_Gym\AI-Gym\Assets\Gym\1124\PowerLegPress_ani.fbx",
    f_start=2, f_peak=37, f_end=73,
    demo_prefixes=("Ch38_", "Trainer_Smartwatch", "Cap", "Headset", "Mic"),
    cam_loc=(2.10, -2.05, 1.35), cam_tgt=(0.0, -0.35, 0.70),
    hips_offset=(0.0, 0.0, 0.0),
)

print("\nALL 4 EXISTING MACHINE BOMIO CLIPS BUILT & EXPORTED!")
