"""MiriWaBom AI Trainer humanoid avatar (1.74m real-world scale, Unity Humanoid T-pose).
Run: blender -b --python make_ai_trainer_avatar.py
Optional preview: set AVATAR_PREVIEW=<path.png>
Faces -Y in Blender (+Z in Unity), feet grounded cleanly at Z=0.000."""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

OUT_FBX = r"G:\Unity_Gym\AI-Gym\Assets\Characters\AI_Trainer_Avatar.fbx"
OUT_BLEND = r"G:\Unity_Gym\AI-Gym\_blender\AI_Trainer_Avatar.blend"
PREVIEW = os.environ.get("AVATAR_PREVIEW", "")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection

# ---------- materials (MiriWaBom Navy / Yellow / Cream sports palette) ----------
def make_mat(name, rgb, rough=0.72, metal=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    try:
        m.use_nodes = True
        p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        p.inputs["Base Color"].default_value = (*rgb, 1)
        p.inputs["Roughness"].default_value = rough
        if "Metallic" in p.inputs:
            p.inputs["Metallic"].default_value = metal
    except Exception:
        pass
    return m

MATS = {
    "Skin":    make_mat("Trainer_Skin",    (0.76, 0.56, 0.44), 0.58),
    "Top":     make_mat("Trainer_NavyTop", (0.045, 0.075, 0.175), 0.78),  # MiriWaBom Navy #202C4D (linear)
    "Accent":  make_mat("Trainer_Yellow",  (0.95, 0.58, 0.03), 0.55),     # MiriWaBom Yellow #FFC62E (linear)
    "Pants":   make_mat("Trainer_Pants",   (0.06, 0.07, 0.095), 0.80),    # Dark Charcoal
    "Socks":   make_mat("Trainer_Socks",   (0.88, 0.88, 0.90), 0.75),
    "Shoes":   make_mat("Trainer_Shoes",   (0.92, 0.92, 0.94), 0.45),     # Clean White Sneakers
    "Sole":    make_mat("Trainer_Sole",    (0.12, 0.14, 0.18), 0.65),
    "Hair":    make_mat("Trainer_Hair",    (0.03, 0.025, 0.02), 0.62),
    "White":   make_mat("Trainer_White",   (0.95, 0.95, 0.95), 0.50),
    "Lip":     make_mat("Trainer_Lip",     (0.45, 0.21, 0.19), 0.50),
    "Metal":   make_mat("Trainer_Metal",   (0.72, 0.76, 0.82), 0.25, 0.88),
    "Headset": make_mat("Trainer_Headset", (0.04, 0.045, 0.055), 0.35, 0.25),
}
MAT_ORDER = list(MATS)

# ---------- humanoid bones (T-pose, 1.74m tall) ----------
BONES = {
    "Hips":  (None,    (0, 0, .95),  (0, 0, 1.05)),
    "Spine": ("Hips",  (0, 0, 1.05), (0, 0, 1.20)),
    "Chest": ("Spine", (0, 0, 1.20), (0, 0, 1.40)),
    "Neck":  ("Chest", (0, 0, 1.40), (0, 0, 1.52)),
    "Head":  ("Neck",  (0, 0, 1.52), (0, 0, 1.74)),
}
for side, sx in (("Left", 1), ("Right", -1)):
    BONES.update({
        f"{side}Shoulder": ("Chest",           (sx*.04, 0, 1.38), (sx*.16, 0, 1.38)),
        f"{side}UpperArm": (f"{side}Shoulder", (sx*.16, 0, 1.38), (sx*.44, 0, 1.38)),
        f"{side}LowerArm": (f"{side}UpperArm", (sx*.44, 0, 1.38), (sx*.71, 0, 1.38)),
        f"{side}Hand":     (f"{side}LowerArm", (sx*.71, 0, 1.38), (sx*.83, 0, 1.38)),
        f"{side}UpperLeg": ("Hips",            (sx*.09, 0, .95),  (sx*.09, 0, .50)),
        f"{side}LowerLeg": (f"{side}UpperLeg", (sx*.09, 0, .50),  (sx*.09, 0, .09)),
        f"{side}Foot":     (f"{side}LowerLeg", (sx*.09, 0, .09),  (sx*.09, -.12, .03)),
        f"{side}Toes":     (f"{side}Foot",     (sx*.09, -.12, .03), (sx*.09, -.20, .03)),
    })
SEGS = {k: (Vector(h), Vector(t)) for k, (_p, h, t) in BONES.items()}

def weights_for(co):
    ds = []
    for name, (a, b) in SEGS.items():
        ab = b - a
        t = max(0.0, min(1.0, (co - a).dot(ab) / ab.length_squared))
        ds.append(((co - (a + ab * t)).length, name))
    ds.sort()
    top = [(1.0 / (d + .015) ** 3, n) for d, n in ds[:3]]
    tot = sum(w for w, _ in top)
    return {n: w / tot for w, n in top}

# ---------- body: skin-modifier athletic trainer skeleton ----------
NODES = []
def node(name, co, r, parent=None):
    NODES.append((name, Vector(co), r, parent))

node("hips",     (0, 0, .96),   (.148, .098))
node("spine",    (0, 0, 1.11),  (.138, .092), "hips")
node("chest",    (0, 0, 1.29),  (.172, .108), "spine")
node("neckbase", (0, 0, 1.42),  (.074, .065), "chest")
node("neck",     (0, 0, 1.49),  (.052, .052), "neckbase")
node("head",     (0, -.002, 1.605), (.088, .098), "neck")
node("headtop",  (0, .004, 1.695), (.068, .076), "head")

for s, sx in (("L", 1), ("R", -1)):
    node("sh" + s,    (sx*.165, 0, 1.385), (.064, .062), "neckbase")
    node("elbow" + s, (sx*.44,  0, 1.375), (.045, .045), "sh" + s)
    node("wrist" + s, (sx*.70,  0, 1.375), (.034, .030), "elbow" + s)
    node("hand" + s,  (sx*.77,  0, 1.375), (.042, .016), "wrist" + s)
    node("fing" + s,  (sx*.84,  0, 1.375), (.030, .011), "hand" + s)
    node("thumb" + s, (sx*.755, -.048, 1.368), (.012, .012), "wrist" + s)
    node("hip" + s,   (sx*.090, 0, .93),   (.094, .092), "hips")
    node("knee" + s,  (sx*.092, 0, .49),   (.058, .058), "hip" + s)
    node("ankle" + s, (sx*.092, 0, .10),   (.038, .038), "knee" + s)
    node("ball" + s,  (sx*.092, -.11, .045), (.042, .036), "ankle" + s)
    node("toe" + s,   (sx*.092, -.185, .035), (.034, .028), "ball" + s)

sk_bm = bmesh.new()
skin_layer = sk_bm.verts.layers.skin.verify()
vmap = {}
for name, co, r, parent in NODES:
    v = sk_bm.verts.new(co)
    v[skin_layer].radius = r
    vmap[name] = v
    if parent:
        sk_bm.edges.new((vmap[parent], v))
vmap["hips"][skin_layer].use_root = True

sk_me = bpy.data.meshes.new("SkinSkeleton")
sk_bm.to_mesh(sk_me); sk_bm.free()
sk_ob = bpy.data.objects.new("SkinSkeleton", sk_me)
col.objects.link(sk_ob)
sm = sk_ob.modifiers.new("Skin", 'SKIN')
sm.use_smooth_shade = True
sm.branch_smoothing = 1.0
ss = sk_ob.modifiers.new("Sub", 'SUBSURF')
ss.levels = 2; ss.render_levels = 2
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
body_me = bpy.data.meshes.new_from_object(sk_ob.evaluated_get(dg))
bpy.data.objects.remove(sk_ob)

body_bm = bmesh.new(); body_bm.from_mesh(body_me)
body_bm.normal_update()
body_bm.verts.index_update()
body_bvh = BVHTree.FromBMesh(body_bm)

def ray_y(bvh, x, z):
    hit = bvh.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)))
    return hit[0].y if hit[0] is not None else None

parts = []
def add_bm_part(name, bm, mat_key, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    parts.append((ob, mat_key))
    return ob

def extract(src, pred, offset):
    src.normal_update(); src.verts.index_update()
    new = bmesh.new(); vm = {}
    for f in src.faces:
        if not pred(f.calc_center_median()):
            continue
        vs = []
        for v in f.verts:
            if v.index not in vm:
                vm[v.index] = new.verts.new(v.co + v.normal * offset)
            vs.append(vm[v.index])
        new.faces.new(vs)
    new.normal_update()
    return new

def solid(bm, thickness):
    me = bpy.data.meshes.new("tmp"); bm.to_mesh(me)
    ob = bpy.data.objects.new("tmp", me); col.objects.link(ob)
    m = ob.modifiers.new("S", 'SOLIDIFY'); m.thickness = thickness; m.offset = -1
    bpy.context.view_layer.update()
    ev = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(ob); bpy.data.meshes.remove(me)
    out = bmesh.new(); out.from_mesh(ev); bpy.data.meshes.remove(ev)
    return out

def ellipsoid(center, scale, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=12, radius=1.0)
    M = Matrix.Translation(center) @ (rot or Matrix.Identity(4)) @ Matrix.Diagonal((*scale, 1))
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return bm

def cylinder_seg(p0, p1, r, segs=12):
    v0, v1 = Vector(p0), Vector(p1)
    d = v1 - v0
    length = d.length
    if length < 1e-5:
        return bmesh.new()
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r, radius2=r, depth=length)
    mid = (v0 + v1) * 0.5
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation(mid) @ rot, verts=bm.verts)
    return bm

# ---------- body & tailored trainer sportswear ----------
add_bm_part("Body", body_bm.copy(), "Skin")

# Navy athletic short-sleeve polo / training top (smooth leveled hem!)
top_pred = lambda c: .96 <= c.z <= 1.445 and abs(c.x) <= .32 and not (c.z > 1.415 and abs(c.x) < .085)
top_raw = extract(body_bm, top_pred, .011)
# Level the bottom hem vertices cleanly so there's zero sawtooth edge
for v in top_raw.verts:
    if v.co.z < .985 and abs(v.co.x) < .24:
        v.co.z = .965
top_raw.normal_update()
top_bvh = BVHTree.FromBMesh(top_raw)
add_bm_part("TrainerTop", solid(top_raw.copy(), .005), "Top")

# Clean yellow brand collar + thin neat sleeve cuff bands
collar = extract(body_bm, lambda c: 1.40 <= c.z <= 1.445 and abs(c.x) < .105 and not (c.z > 1.42 and abs(c.x) < .082), .015)
add_bm_part("CollarAccent", solid(collar, .004), "Accent")
cuffs = extract(body_bm, lambda c: 1.32 <= c.z <= 1.44 and .295 <= abs(c.x) <= .325, .013)
add_bm_part("SleeveCuffs", solid(cuffs, .0035), "Accent")

# Dark charcoal athletic training pants + socks + clean sneakers
add_bm_part("Pants", solid(extract(body_bm, lambda c: .16 <= c.z <= 1.02 and abs(c.x) < .22, .007), .005), "Pants")
add_bm_part("Socks", solid(extract(body_bm, lambda c: .095 <= c.z < .165 and abs(c.x) < .22, .006), .004), "Socks")
add_bm_part("Shoes", solid(extract(body_bm, lambda c: .028 <= c.z < .098 and abs(c.x) < .22, .011), .006), "Shoes")
add_bm_part("ShoeSoles", solid(extract(body_bm, lambda c: c.z < .032 and abs(c.x) < .22, .012), .005), "Sole")

# Neat fitted sporty hairstyle (smoothly hugging the skull, no floating beret!)
hair_shell = extract(body_bm, lambda c: (c.z >= 1.640) or (1.575 <= c.z < 1.640 and c.y > -.012), .009)
add_bm_part("HairBase", solid(hair_shell, .006), "Hair")

# ---------- friendly face ----------
def face_y(x, z):
    return ray_y(body_bvh, x, z) or -.095

for sx in (1, -1):
    ex, ez = sx * .033, 1.622
    fy = face_y(ex, ez)
    add_bm_part(f"Sclera{sx}", ellipsoid((ex, fy + .001, ez), (.013, .008, .0095)), "White")
    add_bm_part(f"Iris{sx}",   ellipsoid((ex, fy - .0045, ez), (.0072, .005, .0072)), "Hair")
    bz = 1.647
    add_bm_part(f"Brow{sx}", ellipsoid((sx * .035, face_y(sx * .035, bz) - .001, bz),
                (.019, .005, .0035), Matrix.Rotation(math.radians(6 * sx), 4, 'Y')), "Hair")
    hit = body_bvh.ray_cast(Vector((sx * 1.0, 0, 1.612)), Vector((-sx, 0, 0)))[0]
    if hit is not None:
        add_bm_part(f"Ear{sx}", ellipsoid((hit.x + sx * .002, hit.y + .005, 1.612), (.010, .015, .026)), "Skin")

ny = face_y(0, 1.598)
add_bm_part("Nose", ellipsoid((0, ny - .011, 1.596), (.011, .018, .020)), "Skin")
my = face_y(0, 1.568)
add_bm_part("Smile", ellipsoid((0, my - .001, 1.568), (.025, .005, .0048)), "Lip")

# ---------- AI Trainer signature accessories: wireless headset mic + chest badge + whistle ----------
add_bm_part("Headset_EarPad", ellipsoid((-.094, .004, 1.612), (.012, .018, .022)), "Headset")
add_bm_part("Headset_Band",   cylinder_seg((-.092, .006, 1.612), (-.055, .078, 1.600), .0045), "Headset")
add_bm_part("Headset_Boom",   cylinder_seg((-.092, -.005, 1.604), (-.038, -.105, 1.570), .0035), "Headset")
add_bm_part("Headset_Mic",    ellipsoid((-.034, -.108, 1.569), (.008, .008, .006)), "Accent")

# Whistle lanyard on chest
ty_chest = ray_y(top_bvh, 0, 1.24) or -.115
add_bm_part("Lanyard_L", cylinder_seg((.052, -.035, 1.42), (.004, ty_chest - .008, 1.245), .003), "Accent")
add_bm_part("Lanyard_R", cylinder_seg((-.052, -.035, 1.42), (-.004, ty_chest - .008, 1.245), .003), "Accent")
add_bm_part("Whistle",   ellipsoid((0, ty_chest - .012, 1.225), (.012, .010, .018)), "Metal")

# Chest yellow brand emblem bar on left chest
ty_badge = ray_y(top_bvh, .078, 1.325) or -.108
add_bm_part("BrandEmblem", ellipsoid((.078, ty_badge - .004, 1.325), (.022, .005, .022)), "Accent")

# ---------- armature ----------
arm_data = bpy.data.armatures.new("AITrainerArmature")
arm = bpy.data.objects.new("AITrainerArmature", arm_data)
col.objects.link(arm)
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = {}
for name, (parent, head, tail) in BONES.items():
    b = arm_data.edit_bones.new(name)
    b.head, b.tail = Vector(head), Vector(tail)
    eb[name] = b
for name, (parent, *_r) in BONES.items():
    if parent:
        eb[name].parent = eb[parent]
bpy.ops.object.mode_set(mode='OBJECT')

# ---------- weights, materials, join ----------
for ob, mat_key in parts:
    me = ob.data
    for k in MAT_ORDER:
        me.materials.append(MATS[k])
    idx = MAT_ORDER.index(mat_key)
    for p in me.polygons:
        p.material_index = idx
    groups = {}
    for v in me.vertices:
        for g, val in weights_for(v.co).items():
            vg = groups.get(g)
            if vg is None:
                vg = groups[g] = ob.vertex_groups.new(name=g)
            vg.add([v.index], val, 'REPLACE')

for ob in bpy.context.view_layer.objects:
    ob.select_set(False)
objs = [p[0] for p in parts]
for ob in objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = "AI_Trainer_Mesh"; body.data.name = "AI_Trainer_Mesh"

# Ground feet accurately at Z = 0.000
min_z = min(v.co.z for v in body.data.vertices)
if abs(min_z) > 1e-4:
    for v in body.data.vertices:
        v.co.z -= min_z
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    for b in arm_data.edit_bones:
        b.head.z -= min_z
        b.tail.z -= min_z
    bpy.ops.object.mode_set(mode='OBJECT')

max_z = max(v.co.z for v in body.data.vertices)
body.parent = arm
mod = body.modifiers.new("Armature", 'ARMATURE'); mod.object = arm
print(f"BUILT AI_Trainer_Avatar | height={max_z:.3f}m | tris={sum(len(p.vertices)-2 for p in body.data.polygons)} | mats={len(body.data.materials)}")

# ---------- optional preview render ----------
if PREVIEW:
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.light = 'STUDIO'
    scene.render.resolution_x, scene.render.resolution_y = 640, 860
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    col.objects.link(cam); scene.camera = cam
    cam.location, cam.rotation_euler = (0.45, -3.6, 0.92), (math.radians(88), 0, math.radians(7))
    scene.render.filepath = PREVIEW
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)

# ---------- save .blend and export .fbx ----------
os.makedirs(os.path.dirname(OUT_FBX), exist_ok=True)
os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)

for ob in bpy.context.view_layer.objects:
    ob.select_set(False)
arm.select_set(True); body.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(
    filepath=OUT_FBX, use_selection=True, object_types={'ARMATURE', 'MESH'},
    add_leaf_bones=False, bake_anim=False, apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z', axis_up='Y', path_mode='COPY', embed_textures=False)
print("EXPORTED:", OUT_FBX)
