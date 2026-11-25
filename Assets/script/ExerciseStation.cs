using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.UI;

// 기구 가까이에서 E를 누르면 플레이어가 의자에 앉아 직접 운동한다.
// 씬에 배치된 ExerciseCanvas(힘 강도 게이지·우측 하단 버튼·상단 슬림 HUD)를 제어한다.
public class ExerciseStation : MonoBehaviour
{
    [SerializeField] Font font;
    [SerializeField] FPSController player;
    [SerializeField] Animator machine;       // "Scene" 상태가 있는 기구 애니메이션
    [SerializeField] Transform seatPoint;    // 기구 기준 위치
    [SerializeField] Transform facing;       // 이 오브젝트의 앞쪽(+Z)을 보고 앉는다
    [SerializeField] TrainerAppear trainer;
    [SerializeField] string machineName = "랫풀다운";
    [SerializeField] float useRange = 2.6f;
    [SerializeField] float exitDistance = 2.2f;          // [추가] 운동 종료 시 기구 콜라이더 바깥으로 안전하게 내리는 거리
    [SerializeField] float pullSpeed = 1.4f; // 1초에 바가 움직이는 비율
    [SerializeField] PlayerSeatPose pose;                // 앉은 자세와 손 IK (클립 미사용 시에만)
    [SerializeField] string machineAnimState = "Scene";  // 기구 Animator 상태 이름 (기본 Scene)
    [SerializeField] string playerAnimState = "";        // 보미오 Animator 상태 이름
    [SerializeField] Vector3 hipsOffsetLocal;            // 기구 로컬 기준 보미오 골반 미세 오프셋
    [SerializeField] float camDistance = 4.4f;
    [SerializeField] float camYawOffset = 0f;          // [추가] 카메라 수평 회전 보정(풀업바처럼 반대 방향 기구용)
    [SerializeField] float fullPullTime = 0.5f;          // 클립에서 최대 수축 시점(0~1)
    [SerializeField] int targetReps = 10;                // 목표 횟수

    [Header("▼ [씬 캔버스 UI 연결] 05_UI/ExerciseCanvas 안의 오브젝트")]
    [SerializeField] GameObject promptBanner;       // [추가] 기구 앞 "E : 운동하기" 둥근 배너
    [SerializeField] Text promptLabel;              // [추가] 배너 문구 텍스트
    [SerializeField] GameObject exerciseHudRoot;    // [추가] 운동 중 전체 HUD 루트
    [SerializeField] Text hudTitleText;             // [추가] 상단 카드 제목 ("체스트프레스 · 1 / 10회")
    [SerializeField] Text hudSubText;               // [추가] 상단 카드 보조 안내 문구
    [SerializeField] Image strengthFill;            // [추가] 왼쪽 세로 힘 강도 게이지 채움 바
    [SerializeField] Text strengthValueText;        // [추가] 왼쪽 게이지 하단 퍼센트("78%" / "최대!")
    [SerializeField] Button pullButton;             // [추가] 오른쪽 하단 '꾹 누르기' 버튼
    [SerializeField] Text pullButtonLabel;          // [추가] 버튼 안 동작 문구("밀기"/"당기기"/"펴기")
    [SerializeField] Button stopButton;             // [추가] 오른쪽 하단 '운동 그만하기' 버튼

    // 운동 중에는 질문 버튼·T키·시점 고정 버튼을 막아 화면 버튼과 겹치지 않게 한다
    public static bool InUse { get; private set; }
    static ExerciseStation promptOwner;  // [추가] 6대 기구가 하나의 PromptBanner를 공유할 때 충돌 방지
    static ExerciseStation activeStation; // [추가] 6대 기구가 하나의 버튼 세트를 공유할 때 현재 활성 기구 추적

    // [추가] 힘 강도 게이지 색상 단계 (민트 -> 앰버 -> 골드)
    static readonly Color ColorLow  = new Color(0.13f, 0.65f, 0.52f, 1f);
    static readonly Color ColorMid  = new Color(0.98f, 0.78f, 0.18f, 1f);
    static readonly Color ColorHigh = new Color(1.00f, 0.58f, 0.12f, 1f);
    static readonly Color BtnNormal = new Color(0.13f, 0.65f, 0.52f, 1f);
    static readonly Color BtnHeld   = new Color(0.98f, 0.74f, 0.16f, 1f);

    bool holdBtn; // 화면의 누르기 버튼을 누르고 있는지
    CharacterController cc;
    Animator playerAnim;
    Renderer[] demoRenderers; // 기존 시범 캐릭터 렌더러 (E키 운동 중 완벽 숨김, 끝나면 복구)
    Transform demoHips;       // 기존 시범 캐릭터 Hips 본 (보미오 앉는 위치 1:1 기준)
    bool active, wentDown;
    float pull;
    int reps;
    Vector3 exitPos;
    Vector3 origPlayerScale;
    float yaw, pitch;
    Quaternion baseRot;
    Camera cam, fpCam;
    Renderer[] headParts;

    static bool uiEventsWired; // [추가] 공유 Canvas 버튼 이벤트 중복 등록 방지

    void Start()
    {
        InUse = false;
        promptOwner = null;
        activeStation = null;
        uiEventsWired = false;
        cc = player.GetComponent<CharacterController>();
        fpCam = player.cameraTransform.GetComponent<Camera>();
        var cg = new GameObject("ExerciseCamera");
        cam = cg.AddComponent<Camera>();
        cam.depth = 100f;
        cam.fieldOfView = 50f;
        cg.SetActive(false);

        // [수정] 씬에 배치된 ExerciseCanvas UI 초기화 및 공용 버튼 이벤트 1회 연결
        if (promptBanner != null) promptBanner.SetActive(false);
        if (exerciseHudRoot != null) exerciseHudRoot.SetActive(false);
        WireSharedCanvasEvents();

        // 평소에는 기존 시범 캐릭터와 기구가 계속 시범 동작을 재생하도록 두고, 시범자 렌더러·Hips만 캐시
        if (machine != null)
        {
            var demos = new System.Collections.Generic.List<Renderer>();
            Transform armRoot = null;
            foreach (var t in machine.GetComponentsInChildren<Transform>(true))
            {
                if (armRoot == null && t.name == "Armature") armRoot = t;
                if (demoHips == null && t.name.Contains("Hips")) demoHips = t;
            }
            foreach (var r in machine.GetComponentsInChildren<Renderer>(true))
            {
                // [수정] SkinnedMeshRenderer + Armature 하위 + 시범자 이름 접두어까지 빠짐없이 수집
                string rn = r.name;
                bool isDemoName = rn.StartsWith("Ch06") || rn.StartsWith("Ch38") || rn.StartsWith("Trainer_");
                if (r is SkinnedMeshRenderer || (armRoot != null && r.transform.IsChildOf(armRoot)) || isDemoName)
                    demos.Add(r);
            }
            demoRenderers = demos.ToArray();
        }
    }

    // [추가] 씬 캔버스의 공용 '꾹 누르기' / '그만하기' 버튼 이벤트를 한 번만 연결
    void WireSharedCanvasEvents()
    {
        if (uiEventsWired) return;
        if (pullButton == null || stopButton == null) return;
        uiEventsWired = true;

        var trig = pullButton.GetComponent<EventTrigger>() ?? pullButton.gameObject.AddComponent<EventTrigger>();
        trig.triggers.Clear();
        void AddTrig(EventTriggerType type, bool value)
        {
            var e = new EventTrigger.Entry { eventID = type };
            e.callback.AddListener(_ => { if (activeStation != null) activeStation.holdBtn = value; });
            trig.triggers.Add(e);
        }
        AddTrig(EventTriggerType.PointerDown, true);
        AddTrig(EventTriggerType.PointerUp, false);
        AddTrig(EventTriggerType.PointerExit, false);

        stopButton.onClick.RemoveAllListeners();
        stopButton.onClick.AddListener(() => { if (activeStation != null && activeStation.active) activeStation.End(); });
    }

    // [추가] 시범 캐릭터 숨김/표시 헬퍼 (Animator의 가시성 키에도 절대 겹치지 않도록 3중 차단)
    void SetDemoVisible(bool visible)
    {
        if (demoRenderers == null) return;
        foreach (var r in demoRenderers)
        {
            if (r == null) continue;
            r.forceRenderingOff = !visible;
            r.enabled = visible;
            if (machine != null && r.gameObject != machine.gameObject)
                r.gameObject.SetActive(visible);
        }
    }

    // [추가] 기구별 직관적인 동작 동사 반환
    string GetActionVerb()
    {
        if (machineName.Contains("체스트") || machineName.Contains("프레스")) return "밀기";
        if (machineName.Contains("익스텐션")) return "펴기";
        if (machineName.Contains("암컬")) return "올리기";
        if (machineName.Contains("풀업") || machineName.Contains("턱걸이")) return "올라가기";
        return "당기기";
    }

    void Update()
    {
        if (seatPoint == null || player == null || machine == null) return;
        var kb = Keyboard.current; var mouse = Mouse.current;
        if (kb == null || mouse == null) return;

        if (!active)
        {
            var near = !PlayerFreeze.Frozen && !InUse && Flat(player.transform.position - seatPoint.position).magnitude < useRange;
            if (near)
            {
                // [수정] 가까이 온 기구만 공용 PromptBanner를 켜고 이름을 갱신
                promptOwner = this;
                if (promptLabel != null) promptLabel.text = $"{machineName} 운동하기";
                if (promptBanner != null) promptBanner.SetActive(true);
                if (kb.eKey.wasPressedThisFrame) Begin();
            }
            else if (promptOwner == this)
            {
                promptOwner = null;
                if (promptBanner != null) promptBanner.SetActive(false);
            }
            return;
        }

        if (kb.eKey.wasPressedThisFrame || kb.escapeKey.wasPressedThisFrame) { End(); return; }

        // 마우스 오른쪽 버튼을 누른 채 움직이면 카메라를 돌려 앉은 모습을 여러 각도에서 본다
        if (mouse.rightButton.isPressed)
        {
            var look = mouse.delta.ReadValue() * 0.15f;
            yaw = Mathf.Clamp(yaw + look.x, -110f, 110f);
            pitch = Mathf.Clamp(pitch - look.y, 0f, 45f);
        }

        bool pressing = kb.spaceKey.isPressed || holdBtn;
        var target = pressing ? 1f : 0f;
        pull = Mathf.MoveTowards(pull, target, pullSpeed * Time.deltaTime);

        machine.Play(machineAnimState, 0, pull * fullPullTime);
        machine.Update(0f);
        SetDemoVisible(false); // [추가] 매 프레임 Animator 갱신 직후 시범자 재활성화 완벽 차단

        if (playerAnim != null && !string.IsNullOrEmpty(playerAnimState))
        {
            playerAnim.Play(playerAnimState, 0, pull * fullPullTime);
            playerAnim.Update(0f);
        }

        // [추가] 왼쪽 세로 힘 강도 게이지 & 버튼 눌림 피드백 실시간 갱신
        UpdateExerciseUi(pressing);

        if (pull > 0.95f) wentDown = true;
        else if (pull < 0.1f && wentDown)
        {
            wentDown = false;
            reps++;
            OnRepCompleted(reps);
            if (reps >= targetReps) { End(); return; }
        }
    }

    // [추가] 씬 캔버스의 상단 HUD + 왼쪽 힘 강도 게이지 + 버튼 피드백 갱신
    void UpdateExerciseUi(bool pressing)
    {
        if (hudTitleText != null)
            hudTitleText.text = $"{machineName}  ·  {reps} / {targetReps}회";
        if (hudSubText != null)
            hudSubText.text = "아프면 바로 멈추세요 · 쉬었다 하셔도 돼요";

        if (strengthFill != null)
        {
            strengthFill.fillAmount = Mathf.Clamp01(pull);
            strengthFill.color = pull < 0.5f
                ? Color.Lerp(ColorLow, ColorMid, pull * 2f)
                : Color.Lerp(ColorMid, ColorHigh, (pull - 0.5f) * 2f);
        }
        if (strengthValueText != null)
        {
            strengthValueText.text = pull >= 0.95f ? "최대!" : $"{Mathf.RoundToInt(pull * 100f)}%";
            strengthValueText.color = pull >= 0.95f ? ColorMid : Color.white;
        }
        if (pullButton != null && pullButton.image != null)
        {
            pullButton.image.color = pressing ? BtnHeld : BtnNormal;
        }
    }

    void OnRepCompleted(int count)
    {
        string coachMent = "";
        switch (count)
        {
            case 1:
                coachMent = "좋아요! 정확한 자세로 잘 하고 계세요! 아프면 바로 멈추세요.";
                break;
            case 3:
                coachMent = "숨을 내쉬면서 힘을 주고, 천천히 돌아오세요. 힘들면 쉬었다 하셔도 돼요.";
                break;
            case 5:
                coachMent = "벌써 반이에요! 무리하지 마세요. 쉬었다 하셔도 돼요.";
                break;
            case 7:
                coachMent = "잘하고 계세요. 불편하면 바로 멈추셔도 괜찮아요.";
                break;
        }

        if (!string.IsNullOrEmpty(coachMent) && trainer != null)
            trainer.SayCoaching(coachMent);
    }

    void LateUpdate()
    {
        if (!active) return;
        var pivot = seatPoint.position + Vector3.up * 1.12f; // [수정] 헬스장 통합 스케일(1.28x) 기구에 맞춘 3인칭 시선 높이
        var rot = baseRot * Quaternion.Euler(-pitch, yaw + camYawOffset, 0f); // 기구 방향에 맞춘 3인칭 카메라 보정
        cam.transform.position = pivot + rot * new Vector3(0f, 0f, camDistance);
        cam.transform.LookAt(pivot);
    }

    static Vector3 Flat(Vector3 v) { v.y = 0; return v; }

    void Begin()
    {
        active = true; InUse = true; activeStation = this;
        pull = 0; reps = 0; wentDown = false; holdBtn = false;
        promptOwner = null;
        if (promptBanner != null) promptBanner.SetActive(false);
        if (exerciseHudRoot != null) exerciseHudRoot.SetActive(true);
        if (pullButtonLabel != null) pullButtonLabel.text = $"{GetActionVerb()} (꾹 누르기)";
        UpdateExerciseUi(false);

        Cursor.lockState = CursorLockMode.None; Cursor.visible = true;
        player.SetExerciseUiHidden(true); // [추가] 우측 하단 '시점 고정' 버튼 즉시 숨김

        // 기구를 0프레임으로 맞춘 뒤 기존 시범 캐릭터의 정확한 Hips 위치를 읽고 시범자만 완벽 숨김
        machine.enabled = true; machine.speed = 0f;
        machine.Play(machineAnimState, 0, 0f);
        machine.Update(0f);
        Vector3? targetHipsWorld = demoHips != null
            ? (Vector3?)(demoHips.position + machine.transform.TransformVector(hipsOffsetLocal))
            : null;
        SetDemoVisible(false);

        var faceT = facing != null ? facing : seatPoint;
        var f = Flat(faceT.forward).normalized;
        exitPos = seatPoint.position + f * exitDistance; exitPos.y = player.transform.position.y; // [수정] 기구 콜라이더 밖 안전 거리로 하차
        player.enabled = false; cc.enabled = false;
        origPlayerScale = player.transform.localScale;
        baseRot = Quaternion.LookRotation(f, Vector3.up); yaw = -42f; pitch = 12f;
        playerAnim = player.GetComponentInChildren<Animator>();
        if (!string.IsNullOrEmpty(playerAnimState))
        {
            player.transform.localScale = machine.transform.lossyScale;
            player.transform.SetPositionAndRotation(seatPoint.position, baseRot);
        }
        else
        {
            player.transform.SetPositionAndRotation(new Vector3(seatPoint.position.x, player.transform.position.y, seatPoint.position.z), baseRot);
        }
        var an = playerAnim; an.SetFloat("Speed", 0f); an.SetBool("Jump", false);
        var parts = new System.Collections.Generic.List<Renderer>();
        foreach (var r in player.GetComponentsInChildren<Renderer>(true)) foreach (var n in player.hiddenInFirstPerson) if (r.name.Contains(n)) { r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On; parts.Add(r); break; }
        headParts = parts.ToArray();
        if (!string.IsNullOrEmpty(playerAnimState))
        {
            playerAnim.speed = 0f;
            playerAnim.Play(playerAnimState, 0, 0f);
            playerAnim.Update(0f);
            var bomioHips = playerAnim.GetBoneTransform(HumanBodyBones.Hips);
            if (targetHipsWorld.HasValue && bomioHips != null)
            {
                player.transform.position += (targetHipsWorld.Value - bomioHips.position);
            }
        }
        else if (pose != null) pose.enabled = true;
        fpCam.enabled = false; cam.gameObject.SetActive(true);

        if (trainer != null)
        {
            trainer.StartCoaching(seatPoint, faceT, an);
            trainer.SayCoaching($"좋습니다! {machineName} 운동 시작합니다. 천천히 동작을 따라해 보세요.");
        }
    }

    void End()
    {
        active = false; InUse = false;
        if (activeStation == this) activeStation = null;
        holdBtn = false;
        if (exerciseHudRoot != null) exerciseHudRoot.SetActive(false);

        if (pose != null) pose.enabled = false;
        if (playerAnim != null && !string.IsNullOrEmpty(playerAnimState))
        {
            playerAnim.speed = 1f;
            playerAnim.Play("Idle Walk Run Blend", 0, 0f);
        }
        cam.gameObject.SetActive(false); fpCam.enabled = true;
        foreach (var r in headParts) r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.ShadowsOnly;
        player.transform.localScale = origPlayerScale;
        player.transform.position = exitPos;
        player.cameraTransform.localRotation = Quaternion.identity;
        cc.enabled = true; player.enabled = true;
        player.SetExerciseUiHidden(false); // [추가] 시점 고정 버튼 복구

        // 운동이 끝나면 기존 시범 캐릭터를 다시 보이게 하고 시범 애니메이션 재개
        SetDemoVisible(true);
        machine.speed = 1f; machine.enabled = true;
        machine.Play(machineAnimState, 0, 0f);

        if (trainer != null)
        {
            trainer.StopCoaching();
            if (reps > 0)
                trainer.SayCoaching(reps >= targetReps
                    ? $"{reps}회 모두 하셨어요! 정말 잘하셨습니다. 이제 편하게 쉬세요. 불편한 곳이 있으면 현장 선생님과 먼저 이야기하세요."
                    : $"{reps}회 하셨어요. 수고하셨습니다! 불편한 곳이 있으면 현장 선생님과 먼저 이야기하세요.");
        }

        if (reps > 0) SessionLog.Add(machineName, reps);
    }
}
