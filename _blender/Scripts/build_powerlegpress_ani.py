import bpy
import math
import os
from mathutils import Vector, Matrix, Euler

RIG_BLEND = r"D:\Unity\Gym\_blender\Blend\ChestPress_ani_done.blend"
MACHINE_BLEND = r"D:\Unity\Gym\_blender\Cleaned\PowerLegPress\PowerLegPress_Clean.blend"
OUT_BLEND = r"D:\Unity\Gym\_blender\Cleaned\PowerLegPress\PowerLegPress_ani.blend"
OUT_FBX = r"D:\Unity\Gym\_blender\Cleaned\PowerLegPress\PowerLegPress_ani.fbx"
PREVIEW_DIR = r"C:\Users\User\.gemini\antigravity\brain\5341817e-21d8-4bf0-a858-9b4e0faed54e\scratch"

# -------------------------------------------------------------------------
# 1. Start from ChestPress_ani_done.blend (keeps full Mixamo Control Rig + character + materials)
#    Remove ChestPress machine objects & old animation, then append PowerLegPress_Clean!
# -------------------------------------------------------------------------
bpy.ops.wm.open_mainfile(filepath=RIG_BLEND)

# Delete ChestPress hierarchy
cp_root = bpy.data.objects.get("ChestPress")
if cp_root:
    to_del = []
    def collect(o):
        to_del.append(o)
        for c in o.children:
            collect(c)
    collect(cp_root)
    for o in to_del:
        bpy.data.objects.remove(o, do_unlink=True)

# Also remove any orphan cameras/lights from source
for o in list(bpy.data.objects):
    if o.type in {'CAMERA', 'LIGHT'}:
        bpy.data.objects.remove(o, do_unlink=True)

# Clear ALL existing animation data and actions
for o in bpy.data.objects:
    o.animation_data_clear()
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)

# Append all objects from PowerLegPress_Clean.blend
with bpy.data.libraries.load(MACHINE_BLEND, link=False) as (data_from, data_to):
    data_to.objects = list(data_from.objects)

machine_col = bpy.data.collections.new("PowerLegPress_Clean")
bpy.context.scene.collection.children.link(machine_col)
for o in data_to.objects:
    if o is not None:
        machine_col.objects.link(o)

arm = bpy.data.objects["Armature"]
arm.location = (0.0, 0.0, 0.0)
arm.rotation_euler = (0.0, 0.0, 0.0)
arm.scale = (1.0, 1.0, 1.0)

# Reset all pose bones to rest pose
for pb in arm.pose.bones:
    pb.location = (0.0, 0.0, 0.0)
    pb.rotation_euler = (0.0, 0.0, 0.0)
    pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    pb.scale = (1.0, 1.0, 1.0)

# Ensure IK mode (ik_fk_switch = 0.0) on hands & feet
for cname in ("Ctrl_Hand_IK_Left", "Ctrl_Hand_IK_Right", "Ctrl_Foot_IK_Left", "Ctrl_Foot_IK_Right"):
    if cname in arm.pose.bones and "ik_fk_switch" in arm.pose.bones[cname].keys():
        arm.pose.bones[cname]["ik_fk_switch"] = 0.0

# Enable IK Stretch on BOTH arms so hands never detach from Ctrl_Hand_IK!
for side in ("Left", "Right"):
    fa = arm.pose.bones[f"ForeArm_IK_{side}"]
    ua = arm.pose.bones[f"Arm_IK_{side}"]
    ua.ik_stretch = 0.35
    fa.ik_stretch = 0.35
    for c in fa.constraints:
        if c.type == 'IK':
            c.use_stretch = True
    # Ensure Hand deform bone stays attached cleanly to ForeArm tail even during stretch
    # (already parented to mixamorig5:*ForeArm which has COPY_TRANSFORMS from ForeArm_IK_*)

bpy.context.view_layer.update()

# Helper: build 3x3 rotation matrix whose columns are (x_axis, y_axis, z_axis)
def basis_mat3(y_dir, z_hint):
    y = Vector(y_dir).normalized()
    z = Vector(z_hint)
    z = (z - y * z.dot(y)).normalized()
    x = y.cross(z).normalized()
    z = x.cross(y).normalized()
    m = Matrix((
        (x.x, y.x, z.x),
        (x.y, y.y, z.y),
        (x.z, y.z, z.z),
    ))
    return m

def set_pose_bone_world(arm_obj, bone_name, pos=None, mat3=None):
    pb = arm_obj.pose.bones[bone_name]
    cur = pb.matrix.copy()
    m = mat3.to_4x4() if mat3 is not None else cur.to_3x3().to_4x4()
    m.translation = Vector(pos) if pos is not None else cur.translation.copy()
    pb.matrix = m
    bpy.context.view_layer.update()

# -------------------------------------------------------------------------
# 2. Pose the character cleanly seated on PowerLegPress_Clean
# -------------------------------------------------------------------------
# Seat cushion top surface is around (0, 0.06, 0.46), backrest front around (0, 0.41, 0.78) tilted -48 deg X.
# Place Ctrl_Hips firmly on the seat, reclined onto backrest:
hips_pos = Vector((0.0, 0.10, 0.54))
# Ctrl_Hips rest matrix has local +X=(1,0,0), +Y=(0,0,1), +Z=(0,-1,0) -> rotating world by Rx(-34 deg) tilts +Z toward +Y
hips_rot = Matrix.Rotation(math.radians(-34.0), 3, 'X') @ arm.data.bones["Ctrl_Hips"].matrix_local.to_3x3()
set_pose_bone_world(arm, "Ctrl_Hips", pos=hips_pos, mat3=hips_rot)

# Spine gentle recline to align upper back flush against the 48-deg backrest, and neck/head looking forward
# Check local X pitch direction on Spine/Neck/Head:
# In rest pose, Ctrl_Spine local +X = (1,0,0), local +Y ≈ (0,0,1), local +Z ≈ (0,-1,0)
# So negative local X rotation leans BACKWARD (+Y), positive local X rotation nods FORWARD (-Y)!
arm.pose.bones["Ctrl_Spine"].rotation_euler  = Euler((math.radians(-6.0), 0.0, 0.0), 'XYZ')
arm.pose.bones["Ctrl_Spine1"].rotation_euler = Euler((math.radians(-5.0), 0.0, 0.0), 'XYZ')
arm.pose.bones["Ctrl_Spine2"].rotation_euler = Euler((math.radians(-3.0), 0.0, 0.0), 'XYZ')
arm.pose.bones["Ctrl_Neck"].rotation_euler   = Euler((math.radians(16.0), 0.0, 0.0), 'XYZ')
arm.pose.bones["Ctrl_Head"].rotation_euler   = Euler((math.radians(18.0), 0.0, 0.0), 'XYZ')
bpy.context.view_layer.update()

# Lower & slightly protract shoulders toward the side handles so arm reach is natural & comfortable
for side, sgn in (("Left", 1.0), ("Right", -1.0)):
    pb = arm.pose.bones[f"Ctrl_Shoulder_{side}"]
    # Rotate shoulder down (-Z) and forward (-Y) in world space
    cur_m = pb.matrix.to_3x3()
    # Roll around Y to drop shoulder downward, yaw slightly forward
    drop = Matrix.Rotation(math.radians(-14.0 * sgn), 3, 'Y')
    fwd  = Matrix.Rotation(math.radians( 10.0 * sgn), 3, 'Z')
    set_pose_bone_world(arm, f"Ctrl_Shoulder_{side}", mat3=(fwd @ drop @ cur_m))

bpy.context.view_layer.update()

# Print where shoulders, head, backrest ended up so we can verify!
for b in ("mixamorig5:Hips", "mixamorig5:Spine2", "mixamorig5:Head", "mixamorig5:LeftArm", "mixamorig5:RightArm"):
    print(f"POSE {b:22s}: head={tuple(round(v,3) for v in arm.pose.bones[b].head)}")

# -------------------------------------------------------------------------
# 3. Position BOTH Hands squarely on Handle_R (+X = Left hand) and Handle_L (-X = Right hand)
# -------------------------------------------------------------------------
# Handle_R is at (+0.33, y=[-0.12..+0.12], z=0.40), radius 0.024m (outer surface x=±0.354, top z=0.424)
# Natural horizontal-bar grip:
#   - Palm faces INWARD toward the bar (-X for Left, +X for Right) and slightly down
#   - 4 fingers point DOWNWARD (-Z) across the outer side of the bar and curl INWARD underneath it
#   - Thumb rests cleanly ON TOP of the bar pointing forward (-Y)
for side, sgn in (("Left", 1.0), ("Right", -1.0)):
    wrist_pos = Vector((0.365 * sgn, 0.045, 0.455))
    finger_dir = Vector((-0.18 * sgn, -0.38, -0.91)).normalized()
    palm_norm  = Vector((-0.92 * sgn, -0.10, -0.38)).normalized()
    hand_m3 = basis_mat3(finger_dir, palm_norm)
    set_pose_bone_world(arm, f"Ctrl_Hand_IK_{side}", pos=wrist_pos, mat3=hand_m3)

    # Arm Pole target cleanly behind and slightly outside the elbow
    pole_pos = Vector((0.48 * sgn, 0.38, 0.58))
    set_pose_bone_world(arm, f"Ctrl_ArmPole_IK_{side}", pos=pole_pos)

# Tight wrap-around cylinder grip (4 fingers curl under bar, thumb wraps gently over top of bar)
finger_pose = {
    "Ctrl_Thumb1_Left":   (-14.0,  16.0,  10.0),
    "Ctrl_Thumb2_Left":   ( 24.0,   0.0,   6.0),
    "Ctrl_Thumb3_Left":   ( 28.0,   0.0,   4.0),
    "Ctrl_Index1_Left":   ( 52.0,   0.0,  -3.0),
    "Ctrl_Index2_Left":   ( 74.0,   0.0,   0.0),
    "Ctrl_Index3_Left":   ( 52.0,   0.0,   0.0),
    "Ctrl_Middle1_Left":  ( 56.0,   0.0,  -1.0),
    "Ctrl_Middle2_Left":  ( 76.0,   0.0,   0.0),
    "Ctrl_Middle3_Left":  ( 54.0,   0.0,   0.0),
    "Ctrl_Ring1_Left":    ( 58.0,   0.0,   2.0),
    "Ctrl_Ring2_Left":    ( 76.0,   0.0,   0.0),
    "Ctrl_Ring3_Left":    ( 54.0,   0.0,   0.0),
    "Ctrl_Pinky1_Left":   ( 60.0,   0.0,   4.0),
    "Ctrl_Pinky2_Left":   ( 74.0,   0.0,   0.0),
    "Ctrl_Pinky3_Left":   ( 52.0,   0.0,   0.0),

    "Ctrl_Thumb1_Right":  ( 14.0, -16.0, -10.0),
    "Ctrl_Thumb2_Right":  (-24.0,   0.0,  -6.0),
    "Ctrl_Thumb3_Right":  (-28.0,   0.0,  -4.0),
    "Ctrl_Index1_Right":  ( 52.0,   0.0,   3.0),
    "Ctrl_Index2_Right":  ( 74.0,   0.0,   0.0),
    "Ctrl_Index3_Right":  ( 52.0,   0.0,   0.0),
    "Ctrl_Middle1_Right": ( 56.0,   0.0,   1.0),
    "Ctrl_Middle2_Right": ( 76.0,   0.0,   0.0),
    "Ctrl_Middle3_Right": ( 54.0,   0.0,   0.0),
    "Ctrl_Ring1_Right":   ( 58.0,   0.0,  -2.0),
    "Ctrl_Ring2_Right":   ( 76.0,   0.0,   0.0),
    "Ctrl_Ring3_Right":   ( 54.0,   0.0,   0.0),
    "Ctrl_Pinky1_Right":  ( 60.0,   0.0,  -4.0),
    "Ctrl_Pinky2_Right":  ( 74.0,   0.0,   0.0),
    "Ctrl_Pinky3_Right":  ( 52.0,   0.0,   0.0),
}
for bname, degs in finger_pose.items():
    if bname in arm.pose.bones:
        arm.pose.bones[bname].rotation_euler = Euler(tuple(math.radians(d) for d in degs), 'XYZ')

bpy.context.view_layer.update()

# Verify hand-to-Ctrl_Hand_IK distance (should be 0.000m!)
for side in ("Left", "Right"):
    h = arm.pose.bones[f"mixamorig5:{side}Hand"].head
    c = arm.pose.bones[f"Ctrl_Hand_IK_{side}"].head
    print(f"HAND CHECK {side:5s}: hand={tuple(round(v,3) for v in h)} ctrl={tuple(round(v,3) for v in c)} gap={(h-c).length:.4f}m")

# -------------------------------------------------------------------------
# 4. Animate Lever_Pivot & Foot IK cleanly in sync (72-frame smooth loop!)
# -------------------------------------------------------------------------
pivot = bpy.data.objects["Lever_Pivot"]
fp_grip = bpy.data.objects["FootPlate_Grip"]

# Base footplate surface frame at Lever_Pivot = 0 deg:
# FootPlate_Grip center = (0, -0.5812, 0.6668), front surface is +0.006 along n0
tilt0 = math.radians(20.0)
u0 = Vector((0.0, -math.sin(tilt0), math.cos(tilt0)))  # up along plate
n0 = Vector((0.0,  math.cos(tilt0), math.sin(tilt0)))  # normal facing user (+Y, +Z)
p_grip0 = fp_grip.matrix_world.translation.copy() + n0 * 0.006
pivot_origin = pivot.matrix_world.translation.copy()

# Set Leg Pole targets straight in front of/above the knees
set_pose_bone_world(arm, "Ctrl_LegPole_IK_Left",  pos=Vector(( 0.16, -0.35, 1.25)))
set_pose_bone_world(arm, "Ctrl_LegPole_IK_Right", pos=Vector((-0.16, -0.35, 1.25)))

# Keyframe all static/upper-body/hand/finger/pole bones at frame 1 and 72
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 72
scene.render.fps = 24

static_ctrl_bones = [
    "Ctrl_Hips", "Ctrl_Spine", "Ctrl_Spine1", "Ctrl_Spine2", "Ctrl_Neck", "Ctrl_Head",
    "Ctrl_Shoulder_Left", "Ctrl_Shoulder_Right",
    "Ctrl_Hand_IK_Left", "Ctrl_Hand_IK_Right",
    "Ctrl_ArmPole_IK_Left", "Ctrl_ArmPole_IK_Right",
    "Ctrl_LegPole_IK_Left", "Ctrl_LegPole_IK_Right",
] + list(finger_pose.keys())

for f in (1, 72):
    scene.frame_set(f)
    for bname in static_ctrl_bones:
        if bname in arm.pose.bones:
            pb = arm.pose.bones[bname]
            pb.keyframe_insert(data_path="location", frame=f)
            pb.keyframe_insert(data_path="rotation_euler", frame=f)

# Animate Lever_Pivot + Ctrl_Foot_IK_Left/Right across 1..72 using smooth cosine curve
# Angle: -5 deg (deep bend, rest) -> +17 deg (smooth leg press extension) -> -5 deg
ANG_MIN = math.radians(-5.0)
ANG_MAX = math.radians(17.0)

# Sample every 6 frames so circular arc of footplate has zero linear-chord drift!
sample_frames = list(range(1, 73, 6))
if 72 not in sample_frames:
    sample_frames.append(72)

for f in sample_frames:
    phase = (f - 1) / 71.0  # 0..1
    # Smooth cosine ease-in-out: 0 at f=1, 1 at f=36.5, 0 at f=72
    t = 0.5 * (1.0 - math.cos(2.0 * math.pi * phase))
    ang = ANG_MIN + (ANG_MAX - ANG_MIN) * t

    scene.frame_set(f)
    pivot.rotation_euler = Euler((ang, 0.0, 0.0), 'XYZ')
    pivot.keyframe_insert(data_path="rotation_euler", frame=f)

    # Rotate footplate contact point & frame by `ang` around pivot_origin X axis
    R = Matrix.Rotation(ang, 3, 'X')
    u = R @ u0
    n = R @ n0
    plate_center = pivot_origin + R @ (p_grip0 - pivot_origin)

    for side, sgn in (("Left", 1.0), ("Right", -1.0)):
        # Contact center on FootPlate_Grip: x = ±0.135, slightly below center along u so toes stay nicely on pad
        # Ankle bone head sits ~0.105m out from the sole along n, shifted -0.04m along u (toward heel)
        foot_pos = plate_center + Vector((0.135 * sgn, 0.0, 0.0)) + n * 0.102 - u * 0.06
        # Slight natural outward toe angle (5 deg around n)
        R_toe = Matrix.Rotation(math.radians(-5.0 * sgn), 3, n)
        foot_y = R_toe @ u
        foot_m3 = basis_mat3(foot_y, n)
        set_pose_bone_world(arm, f"Ctrl_Foot_IK_{side}", pos=foot_pos, mat3=foot_m3)

        pb = arm.pose.bones[f"Ctrl_Foot_IK_{side}"]
        pb.keyframe_insert(data_path="location", frame=f)
        pb.keyframe_insert(data_path="rotation_euler", frame=f)

# Set smooth Bezier interpolation on all fcurves
for obj in (arm, pivot):
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.handle_left_type = 'AUTO_CLAMPED'
                kp.handle_right_type = 'AUTO_CLAMPED'

scene.frame_set(1)
bpy.context.view_layer.update()

# -------------------------------------------------------------------------
# 5. Save PowerLegPress_ani.blend & export clean PowerLegPress_ani.fbx (excluding cs_* widgets)
# -------------------------------------------------------------------------
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print(f"Saved {OUT_BLEND} ({os.path.getsize(OUT_BLEND)/1024:.1f} KB)")

if bpy.context.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.data.objects:
    o.select_set(False)
for o in bpy.data.objects:
    if o.name.startswith("cs_") or o.name.startswith("WGT"):
        continue
    if o.type in {'ARMATURE', 'MESH', 'EMPTY'}:
        o.select_set(True)

bpy.ops.export_scene.fbx(
    filepath=OUT_FBX,
    use_selection=True,
    object_types={'ARMATURE', 'MESH', 'EMPTY'},
    use_armature_deform_only=True,
    add_leaf_bones=False,
    bake_anim=True,
    bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=False,
    bake_anim_use_all_actions=False,
    bake_anim_force_startend_keying=True,
    bake_anim_simplify_factor=1.0,
    path_mode='COPY',
    embed_textures=True,
)
print(f"Saved {OUT_FBX} ({os.path.getsize(OUT_FBX)/1024:.1f} KB)")

# -------------------------------------------------------------------------
# 6. Render multi-angle & close-up verification views (temp camera/lights NOT saved!)
# -------------------------------------------------------------------------
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 1024
scene.render.resolution_y = 768

world = bpy.data.worlds.new("W_Preview")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.18, 0.20, 0.24, 1.0)

center = Vector((0.0, -0.15, 0.65))
def add_light(loc, energy):
    ld = bpy.data.lights.new("L", type='AREA'); ld.energy = energy; ld.size = 3.0
    lo = bpy.data.objects.new("L", ld); lo.location = loc
    lo.rotation_euler = (center - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.collection.objects.link(lo)

add_light(( 2.5, -2.5, 2.8), 450)
add_light((-2.5, -1.8, 2.2), 280)
add_light(( 0.0,  2.5, 2.5), 250)

cd = bpy.data.cameras.new("C"); cd.lens = 45
co = bpy.data.objects.new("C", cd); bpy.context.collection.objects.link(co); scene.camera = co

def render_shot(fname, frame, cam_loc, target, lens=45):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    cd.lens = lens
    co.location = Vector(cam_loc)
    co.rotation_euler = (Vector(target) - Vector(cam_loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(PREVIEW_DIR, fname)
    bpy.ops.render.render(write_still=True)

render_shot("ani_f01_iso.png",       1, (-2.1, -1.9, 1.75), (0.0, -0.10, 0.65))
render_shot("ani_f01_side.png",      1, (-2.6, -0.15, 0.80), (0.0, -0.15, 0.65))
render_shot("ani_f36_side.png",     37, (-2.6, -0.15, 0.80), (0.0, -0.15, 0.65))
render_shot("ani_f01_hand_r_cu.png", 1, (-0.90, -0.30, 0.70), (-0.33, 0.02, 0.42), lens=55)
render_shot("ani_f01_hand_l_cu.png", 1, ( 0.90, -0.30, 0.70), ( 0.33, 0.02, 0.42), lens=55)
print("Rendered all animation verification shots.")
