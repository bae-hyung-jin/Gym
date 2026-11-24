import bpy, os, hashlib, tempfile

SRC = r"G:\Unity_Gym\AI-Gym\_blender\backup_LatPulldown_ani_original.fbx"
OUT_FBX = r"G:\Unity_Gym\AI-Gym\Assets\Gym\1124\LatPulldown_ani.fbx"
OUT_BLEND = r"G:\Unity_Gym\AI-Gym\_blender\LatPulldown_ani_clean.blend"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
scene = bpy.context.scene
print("Imported objects:", len(bpy.data.objects), "actions:", len(bpy.data.actions))

# 1. Delete faceless cs_* meshes
to_del = [o for o in bpy.data.objects
          if o.name.startswith("cs_") or o.name.startswith("WGT")
          or (o.type == 'MESH' and len(o.data.polygons) == 0)]
for o in to_del:
    bpy.data.objects.remove(o, do_unlink=True)
print("Deleted faceless/cs objects:", len(to_del))

# 2. Animation: find the proper action per object
def find_action(obj):
    cands = []
    exact = f"{obj.name}|{obj.name}|{obj.name}Action"
    if exact in bpy.data.actions:
        cands.append(bpy.data.actions[exact])
    pref = f"{obj.name}|{obj.name}|"
    for a in bpy.data.actions:
        if a.name.startswith(pref) and a not in cands:
            cands.append(a)
    if obj.type == 'ARMATURE':
        a = bpy.data.actions.get("Armature|Armature|Action")
        if a:
            cands.insert(0, a)
    return cands

def sample(obj):
    out = []
    for f in (1, 30, 60):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        m = obj.matrix_world
        out.append(tuple(round(v, 4) for row in m for v in row))
    return out

def sample_arm(obj):
    out = []
    for f in (1, 30, 60):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        vals = []
        for pb in obj.pose.bones[:40]:
            vals.extend(round(v, 4) for v in pb.matrix.to_translation())
        out.append(tuple(vals))
    return out

moving = []
static = []
for obj in list(bpy.data.objects):
    ad = obj.animation_data
    if ad is None:
        continue
    cands = find_action(obj)
    chosen = None
    for a in cands:
        ad.action = a
        try:
            if obj.type == 'ARMATURE':
                s = sample_arm(obj)
            else:
                s = sample(obj)
        except Exception as e:
            print("sample error", obj.name, e)
            continue
        if s[0] != s[1] or s[1] != s[2]:
            chosen = a
            break
    if chosen is not None:
        ad.action = chosen
        moving.append((obj.name, chosen.name))
    else:
        obj.animation_data_clear()
        static.append(obj.name)

print("MOVING objects:", len(moving))
for m in moving:
    print("   ", m)
print("STATIC (anim cleared):", len(static))

# remove unused actions
keep = set(o.animation_data.action for o in bpy.data.objects if o.animation_data and o.animation_data.action)
for a in list(bpy.data.actions):
    if a not in keep:
        bpy.data.actions.remove(a)
print("Remaining actions:", len(bpy.data.actions))
scene.frame_start = 1
scene.frame_end = 60

# 3. Textures: dedupe & downscale
def img_hash(img):
    if img.packed_file:
        return hashlib.sha256(img.packed_file.data).hexdigest()
    return None

hash_map = {}
for img in list(bpy.data.images):
    h = img_hash(img)
    if h is None:
        continue
    if h in hash_map:
        keep_img = hash_map[h]
        img.user_remap(keep_img)
        bpy.data.images.remove(img)
    else:
        hash_map[h] = img

# remove unreferenced images
for img in list(bpy.data.images):
    if img.users == 0:
        bpy.data.images.remove(img)

tmpdir = tempfile.mkdtemp()
for img in list(bpy.data.images):
    if img.size[0] == 0:
        continue
    w, h = img.size
    if max(w, h) > 1024:
        nw = 1024 if w >= h else max(1, int(w * 1024 / h))
        nh = 1024 if h >= w else max(1, int(h * 1024 / w))
        img.scale(nw, nh)
    # save to temp png and repack from it
    safe = "".join(c if c.isalnum() else "_" for c in img.name)
    tmp = os.path.join(tmpdir, safe + ".png")
    has_alpha = img.alpha_mode != 'NONE' and img.depth in (32, 128)
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA' if has_alpha else 'RGB'
    scene.render.image_settings.compression = 90
    img.save_render(tmp, scene=scene)
    img.unpack(method='REMOVE') if img.packed_file else None
    img.filepath = tmp
    img.source = 'FILE'
    img.reload()
    img.pack()
    print("IMG", img.name, list(img.size), "packed_bytes=", len(img.packed_file.data) if img.packed_file else 0)

# 4. Save blend + export
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)

bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.type in {'MESH', 'ARMATURE', 'EMPTY'}:
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
print("EXPORT SIZE MB:", os.path.getsize(OUT_FBX) / 1048576.0)
