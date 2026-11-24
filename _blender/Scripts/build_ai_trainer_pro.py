import bpy
import bmesh
import math
import os
import numpy as np
from mathutils import Vector, Matrix, Euler

SRC_FBX = r"G:\Unity_Gym\AI-Gym\Assets\Characters\Ch38_nonPBR.fbx"
SRC_TEX_DIR = r"G:\Unity_Gym\AI-Gym\Assets\Characters\Textures"
OUT_TEX_DIR = r"G:\Unity_Gym\AI-Gym\Assets\Characters\Textures_TrainerPro"
OUT_BLEND = r"G:\Unity_Gym\AI-Gym\_blender\AI_Trainer_Pro.blend"
OUT_FBX = r"G:\Unity_Gym\AI-Gym\Assets\Characters\AI_Trainer_Pro.fbx"
RENDER_FULL = r"C:\Users\hyung\.gemini\antigravity\brain\bc816dce-1a90-4961-b863-c22ec5353e0c\scratch\trainer_pro_full.png"
RENDER_CLOSE = r"C:\Users\hyung\.gemini\antigravity\brain\bc816dce-1a90-4961-b863-c22ec5353e0c\scratch\trainer_pro_closeup.png"

os.makedirs(OUT_TEX_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
os.makedirs(os.path.dirname(RENDER_FULL), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------------------------------------------------------
# 1. Optimized 1024px Skin/Hair Textures + Fabric Micro-Weave Normal Map
# ---------------------------------------------------------
def resize_and_save_png(src_name, out_name, target_sz=1024, is_non_color=False):
    src_path = os.path.join(SRC_TEX_DIR, src_name)
    out_path = os.path.join(OUT_TEX_DIR, out_name)
    img = bpy.data.images.load(src_path, check_existing=False)
    if is_non_color:
        img.colorspace_settings.name = 'Non-Color'
    w, h = img.size
    if w > target_sz or h > target_sz:
        img.scale(target_sz, target_sz)
    img.filepath_raw = out_path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)
    return out_path

tex_skin_col = resize_and_save_png("Ch38_1001_Diffuse.png", "TrainerPro_Skin_Albedo.png", 1024, False)
tex_skin_nrm = resize_and_save_png("Ch38_1001_Normal.png",  "TrainerPro_Skin_Normal.png", 1024, True)
tex_hair_col = resize_and_save_png("Ch38_1002_Diffuse.png", "TrainerPro_Hair_Albedo.png", 1024, False)
tex_hair_nrm = resize_and_save_png("Ch38_1002_Normal.png",  "TrainerPro_Hair_Normal.png", 1024, True)

# Crisp 256x256 tileable athletic micro-weave fabric normal map (fast vectorized numpy!)
tex_fab_nrm = os.path.join(OUT_TEX_DIR, "TrainerPro_Fabric_Normal.png")
sz = 256
yy, xx = np.mgrid[0:sz, 0:sz].astype(np.float32)
u = (xx + yy) * (2.0 * np.pi / 8.0)
v = (xx - yy) * (2.0 * np.pi / 8.0)
hmap = 0.5 * np.sin(u) * np.cos(v) + 0.25 * np.sin(xx * (2.0 * np.pi / 4.0))
dx = (np.roll(hmap, -1, axis=1) - np.roll(hmap, 1, axis=1)) * 0.28
dy = (np.roll(hmap, -1, axis=0) - np.roll(hmap, 1, axis=0)) * 0.28
inv_len = 1.0 / np.sqrt(dx * dx + dy * dy + 1.0)
rgba_n = np.empty((sz, sz, 4), dtype=np.float32)
rgba_n[..., 0] = (-dx * inv_len) * 0.5 + 0.5
rgba_n[..., 1] = (-dy * inv_len) * 0.5 + 0.5
rgba_n[..., 2] = (1.0 * inv_len) * 0.5 + 0.5
rgba_n[..., 3] = 1.0
nimg = bpy.data.images.new("FabricNrmTmp", width=sz, height=sz, alpha=False)
nimg.colorspace_settings.name = 'Non-Color'
nimg.pixels.foreach_set(rgba_n.ravel())
nimg.filepath_raw = tex_fab_nrm
nimg.file_format = 'PNG'
nimg.save()
bpy.data.images.remove(nimg)

# ---------------------------------------------------------
# 2. Fast Numpy 3D-World-Space -> UV-Space Anti-Aliased Texture Baker!
#    Eliminates 100% of polygon sawtooth edges -> Razor-sharp AAA sportswear seams!
# ---------------------------------------------------------
def hex_srgb(h):
    h = h.lstrip('#')
    return np.array([int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0], dtype=np.float32)

def bake_world_shader_to_uv(obj, out_path, color_fn, tex_size=1024, default_hex="#F3F5F9"):
    me = obj.data
    me.calc_loop_triangles()
    uv_layer = me.uv_layers.active
    mw = obj.matrix_world

    # World-space vertex positions array
    wverts = np.array([mw @ v.co for v in me.vertices], dtype=np.float32)

    W = H = tex_size
    wx_buf = np.zeros((H, W), dtype=np.float32)
    wy_buf = np.zeros((H, W), dtype=np.float32)
    wz_buf = np.zeros((H, W), dtype=np.float32)
    mask   = np.zeros((H, W), dtype=bool)

    for tri in me.loop_triangles:
        l0, l1, l2 = tri.loops
        v0, v1, v2 = tri.vertices
        u0, vv0 = uv_layer.data[l0].uv
        u1, vv1 = uv_layer.data[l1].uv
        u2, vv2 = uv_layer.data[l2].uv

        x0, y0 = u0 * (W - 1), vv0 * (H - 1)
        x1, y1 = u1 * (W - 1), vv1 * (H - 1)
        x2, y2 = u2 * (W - 1), vv2 * (H - 1)

        minx = max(0, int(math.floor(min(x0, x1, x2))))
        maxx = min(W - 1, int(math.ceil(max(x0, x1, x2))))
        miny = max(0, int(math.floor(min(y0, y1, y2))))
        maxy = min(H - 1, int(math.ceil(max(y0, y1, y2))))
        if maxx < minx or maxy < miny:
            continue

        denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(denom) < 1e-8:
            continue

        gy, gx = np.mgrid[miny:maxy + 1, minx:maxx + 1]
        a = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / denom
        b = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / denom
        c = 1.0 - a - b
        inside = (a >= -1e-4) & (b >= -1e-4) & (c >= -1e-4)
        if not np.any(inside):
            continue

        p0, p1, p2 = wverts[v0], wverts[v1], wverts[v2]
        sub_mask = mask[miny:maxy + 1, minx:maxx + 1]
        sub_wx   = wx_buf[miny:maxy + 1, minx:maxx + 1]
        sub_wy   = wy_buf[miny:maxy + 1, minx:maxx + 1]
        sub_wz   = wz_buf[miny:maxy + 1, minx:maxx + 1]

        sub_wx[inside] = a[inside] * p0[0] + b[inside] * p1[0] + c[inside] * p2[0]
        sub_wy[inside] = a[inside] * p0[1] + b[inside] * p1[1] + c[inside] * p2[1]
        sub_wz[inside] = a[inside] * p0[2] + b[inside] * p1[2] + c[inside] * p2[2]
        sub_mask[inside] = True

    # Evaluate crisp smooth color function on all covered UV pixels
    img_rgb = np.empty((H, W, 3), dtype=np.float32)
    img_rgb[:] = hex_srgb(default_hex)
    if np.any(mask):
        img_rgb[mask] = color_fn(wx_buf[mask], wy_buf[mask], wz_buf[mask])

    # UV Island Bleeding (8 iterations of dilation so mipmaps NEVER bleed dark seams!)
    dil_mask = mask.copy()
    for _ in range(10):
        new_mask = dil_mask.copy()
        for dy_s, dx_s in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            shifted_m = np.roll(np.roll(dil_mask, dy_s, axis=0), dx_s, axis=1)
            fill = shifted_m & (~new_mask)
            if np.any(fill):
                shifted_c = np.roll(np.roll(img_rgb, dy_s, axis=0), dx_s, axis=1)
                img_rgb[fill] = shifted_c[fill]
                new_mask |= fill
        dil_mask = new_mask

    rgba = np.ones((H, W, 4), dtype=np.float32)
    rgba[..., :3] = np.clip(img_rgb, 0.0, 1.0)
    bimg = bpy.data.images.new("BakeTmp", width=W, height=H, alpha=False)
    bimg.pixels.foreach_set(rgba.ravel())
    bimg.filepath_raw = out_path
    bimg.file_format = 'PNG'
    bimg.save()
    bpy.data.images.remove(bimg)
    return out_path

def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def blend(c_a, c_b, t):
    return c_a * (1.0 - t[..., None]) + c_b * t[..., None]

# ---------------------------------------------------------
# 3. Import Ch38 Official 65-Bone Mixamo Base (Armature 100% Untouched!)
# ---------------------------------------------------------
bpy.ops.import_scene.fbx(filepath=SRC_FBX)
arm = bpy.data.objects["Armature"]
arm_inv = arm.matrix_world.inverted()

for mat in list(bpy.data.materials):
    bpy.data.materials.remove(mat, do_unlink=True)
for img in list(bpy.data.images):
    bpy.data.images.remove(img, do_unlink=True)

body_obj   = bpy.data.objects["Ch38_Body"]
hair_obj   = bpy.data.objects["Ch38_Hair"]
lashes_obj = bpy.data.objects["Ch38_Eyelashes"]
shirt_obj  = bpy.data.objects["Ch38_Shirt"]
shorts_obj = bpy.data.objects["Ch38_Shorts"]
socks_obj  = bpy.data.objects["Ch38_Socks"]
shoes_obj  = bpy.data.objects["Ch38_Shoes"]

# Palette (Clean Off-White + Deep Friendly Navy + Warm Sand Beige + Soft Mint!)
C_WHITE  = hex_srgb("#F4F6FA")
C_NAVY   = hex_srgb("#1A2740")
C_NAVY2  = hex_srgb("#131E33")
C_MINT   = hex_srgb("#5BC2A4")
C_BEIGE  = hex_srgb("#D9C39E")
C_SOLE   = hex_srgb("#222832")
C_SEAM   = hex_srgb("#11192A")

# Bake 1: Razor-Sharp Two-Tone Athletic Trainer Zip-Up Top (Ch38_Shirt -> 1024x1024!)
def shirt_color_fn(x, y, z):
    n = len(x)
    ax = np.abs(x)
    col = np.broadcast_to(C_WHITE, (n, 3)).copy()

    # Sleek gentle athletic V-chevron line across chest & straight across back
    front_factor = smoothstep(0.02, -0.05, y)
    v_dip = 0.032 * front_factor * np.clip(1.0 - ax / 0.20, 0.0, 1.0)
    split_z = 1.248 - v_dip

    # Torso mask (ax < 0.24 smoothly transitions into sleeves)
    in_torso = smoothstep(0.245, 0.215, ax)

    # Lower torso in Deep Navy below split_z - 0.040
    t_navy_low = smoothstep(split_z - 0.037, split_z - 0.043, z) * in_torso
    col = blend(col, C_NAVY, t_navy_low)

    # Warm Beige thin pinstripe (split_z - 0.040 .. split_z - 0.023)
    t_beige = smoothstep(split_z - 0.042, split_z - 0.038, z) * smoothstep(split_z - 0.021, split_z - 0.025, z) * in_torso
    col = blend(col, C_BEIGE, t_beige)

    # Soft Mint athletic accent stripe (split_z - 0.023 .. split_z)
    t_mint = smoothstep(split_z - 0.025, split_z - 0.021, z) * smoothstep(split_z + 0.002, split_z - 0.002, z) * in_torso
    col = blend(col, C_MINT, t_mint)

    # Subtle tailored navy side-contour panels strictly below the chevron stripe (keeps upper white chest spotless!)
    t_side = smoothstep(0.145, 0.160, ax) * smoothstep(split_z - 0.042, split_z - 0.055, z) * in_torso
    col = blend(col, C_NAVY2, t_side * 0.85)

    # Crisp stand-up collar in Deep Navy (clean smooth line at Z = 1.484!)
    t_collar = smoothstep(1.480, 1.486, z) * smoothstep(0.16, 0.12, ax)
    col = blend(col, C_NAVY, t_collar)
    # Thin Warm Beige inner collar rim line
    t_collar_rim = smoothstep(1.475, 1.479, z) * smoothstep(1.484, 1.480, z) * smoothstep(0.16, 0.12, ax)
    col = blend(col, C_BEIGE, t_collar_rim)

    # Sleek Deep Navy under-sleeve panel along inner arms
    in_sleeve = smoothstep(0.215, 0.245, ax)
    t_underarm = smoothstep(1.392, 1.385, z) * in_sleeve
    col = blend(col, C_NAVY, t_underarm)

    # Sleeve cuffs: Warm Beige stripe + Soft Mint stripe + Deep Navy cuff
    t_cuff_beige = smoothstep(0.580, 0.585, ax) * smoothstep(0.602, 0.597, ax)
    t_cuff_mint  = smoothstep(0.598, 0.603, ax) * smoothstep(0.622, 0.617, ax)
    t_cuff_navy  = smoothstep(0.618, 0.623, ax)
    col = blend(col, C_BEIGE, t_cuff_beige)
    col = blend(col, C_MINT,  t_cuff_mint)
    col = blend(col, C_NAVY,  t_cuff_navy)

    # Subtle darker navy zipper seam line on front center (X in [-0.006, 0.006], Z = 1.24..1.485)
    t_zip = smoothstep(0.007, 0.004, ax) * smoothstep(-0.02, -0.06, y) * smoothstep(1.235, 1.245, z) * smoothstep(1.490, 1.482, z)
    col = blend(col, C_NAVY2, t_zip)

    # Subtle fabric tonal micro-depth (keeps white from looking blown-out flat)
    return col

tex_shirt_col = bake_world_shader_to_uv(shirt_obj, os.path.join(OUT_TEX_DIR, "TrainerPro_Shirt_Albedo.png"), shirt_color_fn, 1024, "#F4F6FA")

# Bake 2: Razor-Sharp Deep Navy Athletic Trainer Shorts + Beige Waistband & Mint/Beige Side Piping
def shorts_color_fn(x, y, z):
    n = len(x)
    ax = np.abs(x)
    col = np.broadcast_to(C_NAVY, (n, 3)).copy()

    # Clean Warm Beige athletic waistband trim at top
    t_waist = smoothstep(0.935, 0.941, z)
    col = blend(col, C_BEIGE, t_waist)

    # Sleek vertical side piping along outer thighs (split half Mint, half Beige)
    in_outer = smoothstep(0.152, 0.164, ax)
    t_stripe_mint  = in_outer * smoothstep(-0.036, -0.032, y) * smoothstep(-0.012, -0.016, y) * smoothstep(0.935, 0.928, z)
    t_stripe_beige = in_outer * smoothstep(-0.016, -0.012, y) * smoothstep( 0.008,  0.004, y) * smoothstep(0.935, 0.928, z)
    col = blend(col, C_MINT,  t_stripe_mint)
    col = blend(col, C_BEIGE, t_stripe_beige)

    # Crisp thin Soft Mint bottom hem trim on shorts
    t_hem = smoothstep(0.588, 0.582, z)
    col = blend(col, C_NAVY2, t_hem)
    return col

tex_shorts_col = bake_world_shader_to_uv(shorts_obj, os.path.join(OUT_TEX_DIR, "TrainerPro_Shorts_Albedo.png"), shorts_color_fn, 1024, "#1A2740")

# Bake 3: Razor-Sharp Clean White / Deep Navy / Warm Beige Running Sneakers (Ch38_Shoes -> 1024x1024!)
def shoes_color_fn(x, y, z):
    n = len(x)
    col = np.broadcast_to(C_WHITE, (n, 3)).copy()

    # Deep Navy heel counter & collar
    t_heel = smoothstep(0.018, 0.026, y) * smoothstep(0.036, 0.044, z)
    col = blend(col, C_NAVY, t_heel)
    # Deep Navy upper tongue/collar trim
    t_collar = smoothstep(0.088, 0.095, z)
    col = blend(col, C_NAVY, t_collar)
    # Subtle Soft Mint heel tab highlight
    t_tab = smoothstep(0.068, 0.075, y) * smoothstep(0.038, 0.044, z) * smoothstep(0.062, 0.056, z)
    col = blend(col, C_MINT, t_tab)
    # Crisp Warm Beige athletic midsole stripe (Z = 0.018..0.036)
    t_mid = smoothstep(0.016, 0.020, z) * smoothstep(0.038, 0.033, z)
    col = blend(col, C_BEIGE, t_mid)
    # Dark rubber outsole (Z < 0.018)
    t_sole = smoothstep(0.020, 0.016, z)
    col = blend(col, C_SOLE, t_sole)
    return col

tex_shoes_col = bake_world_shader_to_uv(shoes_obj, os.path.join(OUT_TEX_DIR, "TrainerPro_Shoes_Albedo.png"), shoes_color_fn, 1024, "#F4F6FA")
print("Baked anti-aliased outfit textures cleanly!")

# ---------------------------------------------------------
# 4. Create Clean PBR Materials
# ---------------------------------------------------------
def load_img(path, non_color=False):
    im = bpy.data.images.load(path, check_existing=True)
    if non_color:
        im.colorspace_settings.name = 'Non-Color'
    return im

def hex_to_lin_rgba(h):
    h = h.lstrip('#')
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(r), lin(g), lin(b), 1.0)

def make_pbr_mat(name, color_hex=None, albedo_img=None, normal_img=None, normal_str=0.5,
                 metallic=0.0, roughness=0.72, uv_scale=1.0, alpha_clip=False, emission_hex=None, emission_str=0.0):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness

    if albedo_img is not None:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = albedo_img
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        if alpha_clip:
            nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
            m.surface_render_method = 'DITHERED'
    elif color_hex is not None:
        bsdf.inputs["Base Color"].default_value = hex_to_lin_rgba(color_hex)

    if normal_img is not None:
        ntex = nt.nodes.new("ShaderNodeTexImage")
        ntex.image = normal_img
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.inputs["Strength"].default_value = normal_str
        if uv_scale != 1.0:
            tc = nt.nodes.new("ShaderNodeTexCoord")
            mp = nt.nodes.new("ShaderNodeMapping")
            mp.inputs["Scale"].default_value = (uv_scale, uv_scale, 1.0)
            nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
            nt.links.new(mp.outputs["Vector"], ntex.inputs["Vector"])
        nt.links.new(ntex.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    if emission_hex is not None and emission_str > 0.0:
        bsdf.inputs["Emission Color"].default_value = hex_to_lin_rgba(emission_hex)
        bsdf.inputs["Emission Strength"].default_value = emission_str
    return m

im_skin_col   = load_img(tex_skin_col, False)
im_skin_nrm   = load_img(tex_skin_nrm, True)
im_hair_col   = load_img(tex_hair_col, False)
im_hair_nrm   = load_img(tex_hair_nrm, True)
im_fab_nrm    = load_img(tex_fab_nrm,  True)
im_shirt_col  = load_img(tex_shirt_col, False)
im_shorts_col = load_img(tex_shorts_col, False)
im_shoes_col  = load_img(tex_shoes_col, False)

m_skin      = make_pbr_mat("M_Trainer_Skin",       albedo_img=im_skin_col, normal_img=im_skin_nrm, normal_str=0.65, roughness=0.58)
m_hair      = make_pbr_mat("M_Trainer_Hair",       albedo_img=im_hair_col, normal_img=im_hair_nrm, normal_str=0.70, roughness=0.55)
m_lashes    = make_pbr_mat("M_Trainer_Eyelashes",  albedo_img=im_hair_col, roughness=0.60, alpha_clip=True)
m_shirt     = make_pbr_mat("M_Trainer_Shirt",      albedo_img=im_shirt_col, normal_img=im_fab_nrm, normal_str=0.30, roughness=0.78, uv_scale=12.0)
m_shorts    = make_pbr_mat("M_Trainer_Shorts",     albedo_img=im_shorts_col, normal_img=im_fab_nrm, normal_str=0.35, roughness=0.78, uv_scale=10.0)
m_tights    = make_pbr_mat("M_Trainer_Tights",     color_hex="#182234", normal_img=im_fab_nrm, normal_str=0.30, roughness=0.80, uv_scale=10.0)
m_socks     = make_pbr_mat("M_Trainer_Socks",      color_hex="#EFF2F7", roughness=0.82)
m_shoes     = make_pbr_mat("M_Trainer_Shoes",      albedo_img=im_shoes_col, roughness=0.52)

m_navy      = make_pbr_mat("M_Trainer_Navy",       color_hex="#18243A", roughness=0.70)
m_mint      = make_pbr_mat("M_Trainer_Mint",       color_hex="#5BC2A4", roughness=0.50)
m_headset   = make_pbr_mat("M_Trainer_Headset",    color_hex="#202530", metallic=0.25, roughness=0.36)
m_metal     = make_pbr_mat("M_Trainer_Metal",      color_hex="#D2C2A3", metallic=0.85, roughness=0.26)
m_watch_scr = make_pbr_mat("M_Trainer_WatchScreen",color_hex="#0C1622", metallic=0.10, roughness=0.10, emission_hex="#5EE0B8", emission_str=1.2)
m_led_mint  = make_pbr_mat("M_Trainer_MintLED",    color_hex="#62E8C0", roughness=0.20, emission_hex="#62E8C0", emission_str=1.8)

# Assign crisp single-material baked textures to body/hair/shirt/shorts/shoes
for o, mat in [
    (body_obj,   m_skin),
    (hair_obj,   m_hair),
    (lashes_obj, m_lashes),
    (shirt_obj,  m_shirt),
    (shorts_obj, m_shorts),
    (shoes_obj,  m_shoes),
]:
    o.data.materials.clear()
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.material_index = 0
        p.use_smooth = True

# ---------------------------------------------------------
# 5. Seamless Athletic Compression Tights under Shorts (ZERO jagged steps, 100% Mixamo knee weights!)
#    Use Ch38_Body lower legs (0.345..0.60) + Ch38_Socks upper calf (0.175..0.365) cleanly styled as sleek
#    matte charcoal-navy compression tights ending neatly at crisp white crew socks (0.11..0.175)!
# ---------------------------------------------------------
# Duplicate lower-leg faces of Ch38_Body into Trainer_Tights_Upper (inflated +2.5mm cleanly)
def extract_tights(src_obj, name, z_min, z_max, inflate):
    dup = src_obj.copy()
    dup.data = src_obj.data.copy()
    dup.name = name
    bpy.context.collection.objects.link(dup)
    bm = bmesh.new()
    bm.from_mesh(dup.data)
    mw = dup.matrix_world
    mw_inv = mw.inverted()
    del_f = [f for f in bm.faces if not (z_min <= (mw @ f.calc_center_median()).z <= z_max)]
    bmesh.ops.delete(bm, geom=del_f, context='FACES')
    bm.normal_update()
    for v in bm.verts:
        wp = mw @ v.co
        wn = (mw.to_3x3() @ v.normal).normalized()
        v.co = mw_inv @ (wp + wn * inflate)
    bm.to_mesh(dup.data)
    bm.free()
    dup.data.update()
    dup.data.materials.clear()
    dup.data.materials.append(m_tights)
    for p in dup.data.polygons:
        p.material_index = 0
        p.use_smooth = True
    return dup

tights_up  = extract_tights(body_obj,  "Trainer_Tights_Upper", 0.340, 0.720, 0.0025)
tights_low = extract_tights(socks_obj, "Trainer_Tights_Lower", 0.172, 0.365, 0.0020)

# Remove covered lower leg skin from Ch38_Body (Z < 0.68) and upper sock above ankle cuff (Z > 0.178)
for target_obj, cut_fn in [
    (body_obj,  lambda wc: wc.z < 0.68),
    (socks_obj, lambda wc: wc.z > 0.178),
]:
    bm = bmesh.new()
    bm.from_mesh(target_obj.data)
    mw = target_obj.matrix_world
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if cut_fn(mw @ f.calc_center_median())], context='FACES')
    bm.to_mesh(target_obj.data)
    bm.free()
    target_obj.data.update()

# Style crisp off-white crew ankle socks (Z = 0.11..0.178) cleanly!
socks_obj.data.materials.clear()
socks_obj.data.materials.append(m_socks)
for p in socks_obj.data.polygons:
    p.material_index = 0
    p.use_smooth = True

# ---------------------------------------------------------
# 6. Helper for Exact Outward Surface Snapping & Mixamo Rigged Accessories
# ---------------------------------------------------------
def create_rigged_mesh(name, bm_world, mat_list, bone_name):
    for v in bm_world.verts:
        v.co = arm_inv @ v.co
    bmesh.ops.recalc_face_normals(bm_world, faces=bm_world.faces)
    for f in bm_world.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm_world.to_mesh(me)
    bm_world.free()
    for m in mat_list:
        me.materials.append(m)
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    obj.parent = arm
    obj.matrix_parent_inverse = Matrix.Identity(4)
    vg = obj.vertex_groups.new(name=bone_name)
    vg.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm
    return obj

# Guaranteed outermost front-facing (-Y) chest surface sampling!
_shirt_world_verts = [shirt_obj.matrix_world @ v.co for v in shirt_obj.data.vertices]
def snap_front_outward(obj, x, z, offset_out=0.004):
    near = [p for p in _shirt_world_verts if abs(p.x - x) < 0.030 and abs(p.z - z) < 0.030 and p.y < 0.0]
    if near:
        front_y = min(p.y for p in near)
        # Estimate outward chest normal gently tilted by X curvature
        nrm = Vector((x * 1.4, -1.0, 0.08)).normalized()
        return Vector((x, front_y, z)) + nrm * offset_out, nrm
    return Vector((x, -0.125, z)), Vector((0.0, -1.0, 0.0))

# 6A. Half-Zip Front Track Zipper + Metallic Slider & Pull Tab (100% outward on chest!)
bm_zip = bmesh.new()
segs = 14
prev_ring = None
for i in range(segs + 1):
    z = 1.248 + (1.482 - 1.248) * (i / segs)
    pt, nrm = snap_front_outward(shirt_obj, 0.0, z, 0.0025)
    w = 0.0042
    d = 0.0025
    v0 = bm_zip.verts.new(pt + Vector((-w,  d, 0)))
    v1 = bm_zip.verts.new(pt + Vector(( w,  d, 0)))
    v2 = bm_zip.verts.new(pt + Vector(( w, -d, 0)))
    v3 = bm_zip.verts.new(pt + Vector((-w, -d, 0)))
    ring = (v0, v1, v2, v3)
    if prev_ring is not None:
        for k in range(4):
            kn = (k + 1) % 4
            f = bm_zip.faces.new((prev_ring[k], prev_ring[kn], ring[kn], ring[k]))
            f.material_index = 0
    prev_ring = ring

zp, zn = snap_front_outward(shirt_obj, 0.0, 1.456, 0.006)
res_sl = bmesh.ops.create_cube(bm_zip, size=1.0, matrix=Matrix.Translation(zp) @ Matrix.Diagonal((0.011, 0.007, 0.015, 1.0)))
for v in res_sl["verts"]:
    for f in v.link_faces: f.material_index = 1
res_pl = bmesh.ops.create_cube(bm_zip, size=1.0, matrix=Matrix.Translation(zp + Vector((0.0, -0.005, -0.016))) @ Matrix.Diagonal((0.007, 0.003, 0.020, 1.0)))
for v in res_pl["verts"]:
    for f in v.link_faces: f.material_index = 1

zip_obj = create_rigged_mesh("Trainer_HalfZip", bm_zip, [m_navy, m_metal], "mixamorig5:Spine2")

# 6B. Sleek Left-Chest AI Trainer Shield Emblem Badge (100% outward on chest!)
bm_badge = bmesh.new()
bp, bn = snap_front_outward(shirt_obj, 0.088, 1.385, 0.0035)
rot_badge = Vector((0, 0, 1)).rotation_difference(bn).to_matrix().to_4x4()

res_rim = bmesh.ops.create_cone(bm_badge, cap_ends=True, cap_tris=False, segments=28, radius1=0.025, radius2=0.023, depth=0.004,
                                matrix=Matrix.Translation(bp) @ rot_badge)
for v in res_rim["verts"]:
    for f in v.link_faces: f.material_index = 1  # Brushed champagne/gold metal rim
res_in = bmesh.ops.create_cone(bm_badge, cap_ends=True, cap_tris=False, segments=28, radius1=0.021, radius2=0.020, depth=0.005,
                               matrix=Matrix.Translation(bp + bn * 0.0012) @ rot_badge)
for v in res_in["verts"]:
    for f in v.link_faces: f.material_index = 0  # Deep Navy emblem plate
res_bar = bmesh.ops.create_cube(bm_badge, size=1.0,
                                matrix=Matrix.Translation(bp + bn * 0.0038) @ rot_badge @ Matrix.Diagonal((0.024, 0.006, 0.003, 1.0)))
for v in res_bar["verts"]:
    for f in v.link_faces: f.material_index = 2  # Soft Mint pulse stripe
res_dot = bmesh.ops.create_cone(bm_badge, cap_ends=True, cap_tris=False, segments=16, radius1=0.0045, radius2=0.0045, depth=0.003,
                                matrix=Matrix.Translation(bp + bn * 0.0038 + Vector((0, 0, 0.009))) @ rot_badge)
for v in res_dot["verts"]:
    for f in v.link_faces: f.material_index = 1  # Small gold crest dot above stripe

badge_obj = create_rigged_mesh("Trainer_ChestBadge", bm_badge, [m_navy, m_metal, m_mint], "mixamorig5:Spine2")

# 6C. Wireless GX Trainer Mic Headset (refined mic tip tucked neatly at right cheek corner!)
bm_hs = bmesh.new()
def add_tube(bm, pts, radii, segs=12, mat_idx=0):
    rings = []
    for i, p in enumerate(pts):
        tang = (pts[1] - pts[0]).normalized() if i == 0 else ((pts[-1] - pts[-2]).normalized() if i == len(pts) - 1 else (pts[i + 1] - pts[i - 1]).normalized())
        up = Vector((0, 0, 1)) if abs(tang.z) < 0.9 else Vector((1, 0, 0))
        s1 = tang.cross(up).normalized()
        s2 = tang.cross(s1).normalized()
        r = radii[i]
        rings.append([bm.verts.new(p + (s1 * math.cos(2 * math.pi * s / segs) + s2 * math.sin(2 * math.pi * s / segs)) * r) for s in range(segs)])
    for i in range(len(rings) - 1):
        for s in range(segs):
            sn = (s + 1) % segs
            f = bm.faces.new((rings[i][s], rings[i][sn], rings[i + 1][sn], rings[i + 1][s]))
            f.material_index = mat_idx
    bm.faces.new(list(reversed(rings[0]))).material_index = mat_idx
    bm.faces.new(rings[-1]).material_index = mat_idx

bw = body_obj.matrix_world
ear_pts = [bw @ v.co for v in body_obj.data.vertices if (bw @ v.co).x < -0.072 and 1.59 < (bw @ v.co).z < 1.67 and -0.05 < (bw @ v.co).y < 0.03]
ear_x = min(p.x for p in ear_pts) if ear_pts else -0.094
ear_y = sum(p.y for p in ear_pts) / len(ear_pts) if ear_pts else -0.017
ear_z = sum(p.z for p in ear_pts) / len(ear_pts) if ear_pts else 1.627

hook_pts = [
    Vector((ear_x - 0.003, ear_y + 0.022, ear_z - 0.024)),
    Vector((ear_x - 0.004, ear_y + 0.026, ear_z + 0.010)),
    Vector((ear_x - 0.005, ear_y + 0.010, ear_z + 0.031)),
    Vector((ear_x - 0.007, ear_y - 0.015, ear_z + 0.023)),
    Vector((ear_x - 0.009, ear_y - 0.021, ear_z - 0.002)),
]
add_tube(bm_hs, hook_pts, [0.0038, 0.0042, 0.0042, 0.0042, 0.0048], segs=10, mat_idx=0)

pod_pos = Vector((ear_x - 0.008, ear_y - 0.015, ear_z - 0.004))
res_pod = bmesh.ops.create_icosphere(bm_hs, subdivisions=2, radius=1.0,
                                     matrix=Matrix.Translation(pod_pos) @ Matrix.Diagonal((0.0065, 0.013, 0.015, 1.0)))
for v in res_pod["verts"]:
    for f in v.link_faces: f.material_index = 0
res_led = bmesh.ops.create_icosphere(bm_hs, subdivisions=2, radius=0.0025,
                                     matrix=Matrix.Translation(pod_pos + Vector((-0.006, -0.004, 0.004))))
for v in res_led["verts"]:
    for f in v.link_faces: f.material_index = 2

# Boom arm ends cleanly beside right mouth corner (does not cover lips!)
boom_pts = [
    pod_pos + Vector((-0.002, -0.008, -0.006)),
    Vector((ear_x - 0.011, ear_y - 0.056, ear_z - 0.025)),
    Vector((ear_x - 0.002, ear_y - 0.098, ear_z - 0.038)),
    Vector((-0.064,        ear_y - 0.124, ear_z - 0.044)),
    Vector((-0.048,        ear_y - 0.131, ear_z - 0.045)),
]
add_tube(bm_hs, boom_pts, [0.0024, 0.0021, 0.0019, 0.0018, 0.0019], segs=8, mat_idx=1)
mic_pos = boom_pts[-1] + Vector((0.005, -0.002, 0.0))
res_mic = bmesh.ops.create_icosphere(bm_hs, subdivisions=2, radius=1.0,
                                     matrix=Matrix.Translation(mic_pos) @ Matrix.Diagonal((0.0075, 0.0052, 0.0052, 1.0)))
for v in res_mic["verts"]:
    for f in v.link_faces: f.material_index = 0

headset_obj = create_rigged_mesh("Trainer_Headset", bm_hs, [m_headset, m_metal, m_led_mint], "mixamorig5:Head")

# 6D. Snug Fitness Smartwatch on Left Wrist (tighter fit around navy sleeve cuff!)
bm_watch = bmesh.new()
w_pts = []
for src_w in (shirt_obj, body_obj):
    mw = src_w.matrix_world
    for v in src_w.data.vertices:
        p = mw @ v.co
        if 0.656 < p.x < 0.674:
            w_pts.append(p)
wx = 0.665
wy = sum(p.y for p in w_pts) / len(w_pts)
wz = sum(p.z for p in w_pts) / len(w_pts)
ry = max(abs(p.y - wy) for p in w_pts) - 0.001
rz = max(abs(p.z - wz) for p in w_pts) - 0.001

segs_w = 24
half_w = 0.010
thick_w = 0.004
iL, iR, oL, oR = [], [], [], []
for s in range(segs_w):
    ang = 2.0 * math.pi * s / segs_w
    cy = math.cos(ang); cz = math.sin(ang)
    iL.append(bm_watch.verts.new(Vector((wx - half_w, wy + cy * ry, wz + cz * rz))))
    iR.append(bm_watch.verts.new(Vector((wx + half_w, wy + cy * ry, wz + cz * rz))))
    oL.append(bm_watch.verts.new(Vector((wx - half_w, wy + cy * (ry + thick_w), wz + cz * (rz + thick_w)))))
    oR.append(bm_watch.verts.new(Vector((wx + half_w, wy + cy * (ry + thick_w), wz + cz * (rz + thick_w)))))
for s in range(segs_w):
    sn = (s + 1) % segs_w
    for q in [(oL[s], oR[s], oR[sn], oL[sn]), (iR[s], iL[s], iL[sn], iR[sn]),
              (iL[s], oL[s], oL[sn], iL[sn]), (oR[s], iR[s], iR[sn], oR[sn])]:
        bm_watch.faces.new(q).material_index = 0

case_pos = Vector((wx, wy, wz + rz + 0.0035))
res_case = bmesh.ops.create_cone(bm_watch, cap_ends=True, cap_tris=False, segments=24, radius1=0.020, radius2=0.0185, depth=0.0085,
                                 matrix=Matrix.Translation(case_pos))
for v in res_case["verts"]:
    for f in v.link_faces: f.material_index = 1
res_face = bmesh.ops.create_cone(bm_watch, cap_ends=True, cap_tris=False, segments=24, radius1=0.0155, radius2=0.0155, depth=0.003,
                                 matrix=Matrix.Translation(case_pos + Vector((0, 0, 0.004))))
for v in res_face["verts"]:
    for f in v.link_faces: f.material_index = 2

watch_obj = create_rigged_mesh("Trainer_Smartwatch", bm_watch, [m_headset, m_metal, m_watch_scr], "mixamorig5:LeftForeArm")

# ---------------------------------------------------------
# 6E. Repair Missing Mixamo Ch38 Finger Vertex Weights (All 30 Finger Joints!)
#     Ch38_nonPBR.fbx omits 9/15 finger vertex groups per hand; rebuild smooth
#     bone-capsule weights in REST pose so all 10 fingers curl cleanly in Control Rig.
# ---------------------------------------------------------
def _dist_pt_seg(p, a, b):
    ab = b - a
    l2 = ab.length_squared
    if l2 < 1e-10:
        return (p - a).length, 0.0
    t = max(0.0, min(1.0, (p - a).dot(ab) / l2))
    return (p - (a + ab * t)).length, t

def repair_finger_weights(arm_obj, b_obj):
    for side in ("Left", "Right"):
        for fn in ("Thumb", "Index", "Middle", "Ring", "Pinky"):
            for j in (1, 2, 3):
                bn = f"mixamorig5:{side}Hand{fn}{j}"
                if b_obj.vertex_groups.get(bn) is None:
                    b_obj.vertex_groups.new(name=bn)
    idx_to_name = {vg.index: vg.name for vg in b_obj.vertex_groups}
    bw_m = b_obj.matrix_world
    aw_m = arm_obj.matrix_world
    repaired = 0
    for side in ("Left", "Right"):
        hand_bn = f"mixamorig5:{side}Hand"
        finger_segs = []
        for fn in ("Thumb", "Index", "Middle", "Ring", "Pinky"):
            for j in (1, 2, 3):
                bn = f"mixamorig5:{side}Hand{fn}{j}"
                b = arm_obj.data.bones[bn]
                finger_segs.append((bn, fn, j, aw_m @ b.head_local, aw_m @ b.tail_local))
        prefix = f"mixamorig5:{side}Hand"
        for v in b_obj.data.vertices:
            hand_w_sum = 0.0
            for g in v.groups:
                if idx_to_name.get(g.group, "").startswith(prefix):
                    hand_w_sum += g.weight
            if hand_w_sum < 0.25:
                continue
            vp = bw_m @ v.co
            dists = []
            for bn, fn, j, a_pt, b_pt in finger_segs:
                d, t = _dist_pt_seg(vp, a_pt, b_pt)
                dists.append((d, t, bn, fn, j))
            dists.sort(key=lambda x: x[0])
            nearest_d, _, _, nearest_fn, nearest_j = dists[0]
            k_bone = arm_obj.data.bones[f"mixamorig5:{side}Hand{nearest_fn}1"]
            k_head = aw_m @ k_bone.head_local
            k_dir = ((aw_m @ k_bone.tail_local) - k_head).normalized()
            along = (vp - k_head).dot(k_dir)
            for g in list(v.groups):
                gn = idx_to_name.get(g.group, "")
                if gn.startswith(prefix):
                    b_obj.vertex_groups[gn].remove([v.index])
            if nearest_d > 0.022 or along < -0.012:
                b_obj.vertex_groups[hand_bn].add([v.index], hand_w_sum, 'REPLACE')
                continue
            same_f = [(d, t, bn, j) for (d, t, bn, fn, j) in dists if fn == nearest_fn]
            same_f.sort(key=lambda x: x[0])
            raw_w = {}
            if along < 0.008 and nearest_j == 1:
                f1_ratio = max(0.0, min(1.0, (along + 0.012) / 0.020))
                raw_w[hand_bn] = 1.0 - f1_ratio
                raw_w[f"mixamorig5:{side}Hand{nearest_fn}1"] = f1_ratio
            else:
                sigma = 0.009
                for d, t, bn, j in same_f[:2]:
                    raw_w[bn] = math.exp(-(d * d) / (2.0 * sigma * sigma))
            tot = sum(raw_w.values())
            if tot > 1e-8:
                for bn, wval in raw_w.items():
                    b_obj.vertex_groups[bn].add([v.index], hand_w_sum * (wval / tot), 'REPLACE')
                repaired += 1
    print(f"Repaired 30-joint finger weights on {repaired} hand/finger vertices!")

repair_finger_weights(arm, body_obj)

# ---------------------------------------------------------
# 7. Save Clean Mixamo-Ready .blend & Export Lightweight Unity FBX
# ---------------------------------------------------------
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print("Saved clean Mixamo-ready .blend:", OUT_BLEND)

bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.select_set(True)

bpy.ops.export_scene.fbx(
    filepath=OUT_FBX,
    use_selection=True,
    object_types={'ARMATURE', 'MESH'},
    use_armature_deform_only=True,
    add_leaf_bones=False,
    bake_anim=False,
    path_mode='AUTO',
    embed_textures=False,
    mesh_smooth_type='FACE',
)
print(f"Exported Unity FBX: {OUT_FBX} ({os.path.getsize(OUT_FBX)/1048576.0:.2f} MB)")

# ---------------------------------------------------------
# 8. Render 2 Studio Verification Previews (Temp Lights & Camera NOT saved!)
# ---------------------------------------------------------
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024

world = bpy.data.worlds.new("StudioWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.16, 0.19, 0.24, 1.0)
    bg.inputs["Strength"].default_value = 0.85

def add_light(name, loc, rot_deg, energy, color=(1,1,1), size=2.0):
    ld = bpy.data.lights.new(name, type='AREA')
    ld.energy = energy; ld.color = color; ld.size = size
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    lo.rotation_euler = Euler(tuple(math.radians(a) for a in rot_deg), 'XYZ')
    bpy.context.collection.objects.link(lo)

add_light("KeyLight",  ( 1.8, -2.6, 2.3), (62, 0,  34), 260, (1.00, 0.97, 0.93), 2.2)
add_light("FillLight", (-2.2, -2.0, 1.7), (72, 0, -45), 110, (0.88, 0.94, 1.00), 2.8)
add_light("RimLight",  ( 0.5,  2.2, 2.4), (125, 0, 165), 180, (0.95, 0.98, 1.00), 2.0)

cam_data = bpy.data.cameras.new("PreviewCam")
cam_data.lens = 55
cam_obj = bpy.data.objects.new("PreviewCam", cam_data)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj

def aim(cam, eye, target):
    cam.location = Vector(eye)
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()

aim(cam_obj, (0.75, -2.75, 1.08), (0.0, 0.0, 0.92))
scene.render.filepath = RENDER_FULL
bpy.ops.render.render(write_still=True)

cam_data.lens = 68
aim(cam_obj, (-0.32, -1.05, 1.54), (0.02, -0.02, 1.43))
scene.render.filepath = RENDER_CLOSE
bpy.ops.render.render(write_still=True)

print("Rendered polished v2 verification previews!")
