using UnityEditor;
using UnityEditor.Build;
using UnityEditor.WebGL;
using UnityEngine;

public static class WebOptimizer
{
    [MenuItem("Tools/Optimize WebGL Settings")]
    public static void ApplyWebGLOptimization()
    {
        var webTarget = NamedBuildTarget.WebGL;

        // 1. Build Compression (Brotli + Decompression Fallback for universal static hosting)
        PlayerSettings.WebGL.compressionFormat = WebGLCompressionFormat.Brotli;
        PlayerSettings.WebGL.decompressionFallback = true;
        PlayerSettings.WebGL.dataCaching = true;

        // 2. WASM & IL2CPP Code Size Optimization
        UserBuildSettings.codeOptimization = WasmCodeOptimization.DiskSizeLTO;
        PlayerSettings.SetIl2CppCodeGeneration(webTarget, Il2CppCodeGeneration.OptimizeSize);
        PlayerSettings.stripEngineCode = true;
        PlayerSettings.stripUnusedMeshComponents = true;
        PlayerSettings.SetManagedStrippingLevel(webTarget, ManagedStrippingLevel.Medium);

        // 3. Exceptions & Symbols (Release-ready, keeps explicit try/catch working)
        PlayerSettings.WebGL.exceptionSupport = WebGLExceptionSupport.ExplicitlyThrownExceptionsOnly;
        PlayerSettings.WebGL.debugSymbolMode = WebGLDebugSymbolMode.Off;

        // 4. WebGL Frame Pacing (use browser requestAnimationFrame)
        QualitySettings.vSyncCount = 0;

        AssetDatabase.SaveAssets();
        Debug.Log("[WebOptimizer] WebGL release optimization settings applied (Brotli + Fallback, DiskSizeLTO, OptimizeSize, Stripping=Medium, StripUnusedMeshComponents=true).");
    }
}
