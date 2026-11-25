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

    [Header("▼ [기구 설명 카드 UI 연결] 05_UI/ExerciseCanvas/MachineInfoCard")]
    [SerializeField] GameObject infoCardRoot;       // [추가] 기구 접근 시 표시할 씬 UI 설명 카드 루트 (에디터에서 자유 편집)
    [SerializeField] Text infoTitleText;            // [추가] 카드 제목 텍스트
    [SerializeField] Text infoPartText;             // [추가] 운동 부위 텍스트
    [SerializeField] Text infoHowToText;            // [추가] 사용법 텍스트
    [SerializeField] Text infoCautionText;          // [추가] 안전 팁 텍스트

    [Header("▼ [기구 설명 (인스펙터에서 자유 수정 — 비우면 기본 설명 자동 사용)]")]
    [SerializeField] string customTargetPart;       // [추가] 인스펙터에서 직접 적을 운동 부위
    [TextArea(2, 3), SerializeField] string customHowToUse;  // [추가] 인스펙터에서 직접 적을 사용법
    [TextArea(2, 3), SerializeField] string customSafetyTip; // [추가] 인스펙터에서 직접 적을 안전 팁
    [SerializeField] string customHudTip;           // [추가] 운동 중 상단 HUD 한 줄 가이드
    [SerializeField] string customActionVerb;       // [추가] 인스펙터에서 직접 정할 버튼 문구 (예: 밀기, 모으기, 오르기)
    [SerializeField] bool isContinuousCardio;       // [추가] 천국의 계단처럼 앞으로만 계속 오르는 유산소 기구 체크박스

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
    float cardioTime;      // [추가] 천국의 계단(스텝밀) 전용: 역재생 없이 앞으로만 계속 오르는 연속 재생 시간(0~1 루프)
    float cardioStepAccum; // [추가] 한 걸음(1/6 사이클) 누적 카운터
    int reps;
    Vector3 exitPos;
    Vector3 origPlayerScale;
    float yaw, pitch;
    Quaternion baseRot;
    Camera cam, fpCam;
    Renderer[] headParts;

    static bool uiEventsWired; // [추가] 공유 Canvas 버튼 이벤트 중복 등록 방지

    struct MachineGuide
    {
        public string part;      // 운동 부위
        public string howTo;     // 쉬운 사용 방법
        public string caution;   // 호흡 · 관절 안전 포인트
        public string hudTip;    // 운동 중 상단 HUD 보조 가이드
    }

    void Start()
    {
        InUse = false;
        promptOwner = null;
        activeStation = null;
        uiEventsWired = false;
        if (infoCardRoot != null) infoCardRoot.SetActive(false);
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

    // [추가] 외부(DoorSurvey 자동 이동)에서 기구 표시 이름을 읽을 수 있도록 프로퍼티 공개
    public string MachineDisplayName => machineName ?? "";

    // [수정] 인스펙터에 직접 적은 버튼 문구가 있으면 우선 사용, 비어 있으면 기구 이름으로 자동 선택
    string GetActionVerb()
    {
        if (!string.IsNullOrWhiteSpace(customActionVerb)) return customActionVerb.Trim();
        if (machineName.Contains("체스트") || machineName.Contains("프레스")) return "밀기";
        if (machineName.Contains("익스텐션")) return "펴기";
        if (machineName.Contains("어덕션")) return "모으기";
        if (machineName.Contains("레그컬")) return "굽히기";
        if (machineName.Contains("계단") || machineName.Contains("스텝밀")) return "오르기";
        if (machineName.Contains("스쿼트")) return "앉았다 일어서기";
        if (machineName.Contains("암컬")) return "올리기";
        if (machineName.Contains("풀업") || machineName.Contains("턱걸이")) return "올라가기";
        return "당기기";
    }

    // [추가] 신규 5종 포함 헬스장 전체 11종 기구의 운동 부위·사용법·안전 주의사항 데이터베이스
    MachineGuide GetMachineGuide()
    {
        string n = machineName ?? "";
        if (n.Contains("어덕션"))
            return new MachineGuide
            {
                part = "허벅지 안쪽 · 골반 안정화",
                howTo = "의자에 등을 편히 붙이고 손잡이를 잡은 뒤, 양 무릎을 안쪽으로 천천히 모았다가 풀어 주세요.",
                caution = "허리가 등받이에서 뜨지 않게 유지하고, 모을 때 숨을 내쉬세요.",
                hudTip = "등받이 밀착 · 양 무릎을 부드럽게 모으기 · 아프면 즉시 멈춤"
            };
        if (n.Contains("레그컬"))
            return new MachineGuide
            {
                part = "허벅지 뒤쪽 (햄스트링 · 무릎 보호)",
                howTo = "배와 허벅지를 패드에 대고 엎드린 뒤, 발목 패드를 엉덩이 쪽으로 천천히 접어 올리세요.",
                caution = "허리가 과하게 꺾이지 않도록 상체를 패드에 붙이고 천천히 내리세요.",
                hudTip = "무릎은 패드 고정 · 뒤꿈치를 엉덩이 쪽으로 천천히 접기"
            };
        if (n.Contains("벤치프레스"))
            return new MachineGuide
            {
                part = "가슴 전체 · 어깨 앞쪽 · 팔 뒤쪽",
                howTo = "벤치에 등을 대고 발을 바닥에 단단히 디딘 뒤, 양 손잡이를 천장 방향으로 부드럽게 밀어 올리세요.",
                caution = "어깨가 귀 쪽으로 올라가지 않게 가슴을 펴고, 팔꿈치를 완전히 잠그지 마세요.",
                hudTip = "양발 바닥 고정 · 가슴을 펴고 천장 방향으로 부드럽게 밀기"
            };
        if (n.Contains("계단") || n.Contains("스텝밀"))
            return new MachineGuide
            {
                part = "심폐 지구력 · 하체 전체 체력",
                howTo = "양쪽 손잡이를 가볍게 잡고 발바닥 전체로 계단을 밟으며 일정한 리듬으로 올라가세요.",
                caution = "상체가 너무 숙여지지 않게 시선은 정면을 보고, 숨이 차면 바로 멈추세요.",
                hudTip = "시선 정면 · 손잡이 가볍게 잡기 · 숨이 차면 쉬었다 하세요"
            };
        if (n.Contains("스쿼트"))
            return new MachineGuide
            {
                part = "허벅지 전반 · 엉덩이 (등받이 허리 지지)",
                howTo = "어깨 패드 아래로 들어가 등을 기대고, 무릎을 굽혀 천천히 앉았다가 발판으로 밀어 일어나세요.",
                caution = "무릎이 안쪽으로 모이지 않게 발끝 방향을 유지하고, 호흡을 참지 마세요.",
                hudTip = "등받이 밀착 · 무릎과 발끝 같은 방향 · 천천히 앉았다 일어서기"
            };
        if (n.Contains("체스트"))
            return new MachineGuide
            {
                part = "가슴 · 팔 뒤쪽 · 상체 밀기 근력",
                howTo = "등받이에 등을 편하게 붙이고 손잡이를 잡은 뒤, 앞쪽으로 팔을 천천히 뻗어 밀어 주세요.",
                caution = "밀 때 숨을 내쉬고, 어깨 앞쪽에 통증이 있으면 무리하게 뒤로 젖히지 마세요.",
                hudTip = "등받이 밀착 · 숨을 내쉬며 앞쪽으로 천천히 밀기"
            };
        if (n.Contains("랫풀"))
            return new MachineGuide
            {
                part = "등 근육 · 바른 상체 자세",
                howTo = "의자에 앉아 위쪽 바를 넓게 잡고, 가슴 위쪽을 향해 팔꿈치를 아래로 천천히 당겨 내리세요.",
                caution = "허리를 뒤로 과하게 젖히지 말고, 등을 조이는 느낌으로 부드럽게 당기세요.",
                hudTip = "가슴 펴기 · 팔꿈치를 아래로 부드럽게 당기기"
            };
        if (n.Contains("익스텐션"))
            return new MachineGuide
            {
                part = "허벅지 앞쪽 (대퇴사두근 · 무릎 지지)",
                howTo = "의자에 깊게 앉아 손잡이를 잡고, 발목 패드를 들어 올리듯 무릎을 천천히 펴 주세요.",
                caution = "무릎을 탁 튕기지 말고 끝에서 잠깐 멈춘 뒤 천천히 내려 주세요.",
                hudTip = "엉덩이 고정 · 반동 없이 무릎을 천천히 펴기"
            };
        if (n.Contains("레그프레스"))
            return new MachineGuide
            {
                part = "허벅지 전반 · 엉덩이 하체 근력",
                howTo = "등받이에 허리를 꼭 붙이고 발판 중앙에 발을 올린 뒤, 다리 힘으로 발판을 천천히 밀어 주세요.",
                caution = "무릎을 끝까지 쫙 펴서 잠그지 말고, 약간 여유를 둔 상태로 반복하세요.",
                hudTip = "허리 등받이 밀착 · 무릎 완전히 잠그지 않기"
            };
        if (n.Contains("암컬"))
            return new MachineGuide
            {
                part = "팔 앞쪽 (이두근 · 물건 들기 근력)",
                howTo = "앞쪽 패드에 팔꿈치를 안정적으로 고정하고, 손잡이를 어깨 쪽으로 천천히 접어 올리세요.",
                caution = "어깨나 허리 반동을 쓰지 말고 팔 앞쪽 힘으로 부드럽게 올렸다 내려 주세요.",
                hudTip = "팔꿈치 패드 고정 · 반동 없이 천천히 접어 올리기"
            };
        if (n.Contains("풀업") || n.Contains("턱걸이"))
            return new MachineGuide
            {
                part = "등 상부 · 팔 전체 근력",
                howTo = "위쪽 바를 어깨너비보다 살짝 넓게 잡고, 가슴이 바에 가까워지도록 천천히 끌어올리세요.",
                caution = "어깨가 아프면 무리하게 매달리지 말고 편한 범위까지만 천천히 연습하세요.",
                hudTip = "어깨 힘 빼고 가슴을 바 쪽으로 천천히 끌어올리기"
            };
        return new MachineGuide
        {
            part = "전신 근력 · 균형 운동",
            howTo = "바른 자세로 기구에 자리 잡고 천천히 움직여 보세요.",
            caution = "아프거나 불편하면 바로 멈추고 쉬었다 하세요.",
            hudTip = "아프면 바로 멈추세요 · 쉬었다 하셔도 돼요"
        };
    }

    // [추가] 인스펙터에 직접 입력한 설명이 있으면 우선 사용하고, 비어 있으면 기구별 기본 설명 사용
    MachineGuide GetEffectiveGuide()
    {
        var g = GetMachineGuide();
        if (!string.IsNullOrWhiteSpace(customTargetPart)) g.part    = customTargetPart.Trim();
        if (!string.IsNullOrWhiteSpace(customHowToUse))   g.howTo   = customHowToUse.Trim();
        if (!string.IsNullOrWhiteSpace(customSafetyTip))  g.caution = customSafetyTip.Trim();
        if (!string.IsNullOrWhiteSpace(customHudTip))     g.hudTip  = customHudTip.Trim();
        return g;
    }

    // [수정] 씬에 배치된 05_UI/ExerciseCanvas/MachineInfoCard에 설명을 채워 표시 (맞춤 코칭 중에는 숨김)
    void ShowInfoCard()
    {
        if (infoCardRoot == null) return;
        if (DoorSurvey.IsCoachingActive)
        {
            if (infoCardRoot.activeSelf) infoCardRoot.SetActive(false);
            return;
        }
        var g = GetEffectiveGuide();
        if (infoTitleText != null)   infoTitleText.text   = $"{machineName}  안내";
        if (infoPartText != null)    infoPartText.text    = $"운동 부위  ·  {g.part}";
        if (infoHowToText != null)   infoHowToText.text   = $"사용법: {g.howTo}";
        if (infoCautionText != null) infoCautionText.text = $"안전 팁: {g.caution}";
        if (!infoCardRoot.activeSelf) infoCardRoot.SetActive(true);
    }

    // [수정] 인스펙터 체크박스(isContinuousCardio) 우선, 미체크 시 기구 이름으로 자동 판별
    bool IsContinuousCardio() => isContinuousCardio || (machineName != null && (machineName.Contains("계단") || machineName.Contains("스텝밀")));

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
                // [수정] 가까이 온 기구만 공용 PromptBanner + 기구 설명 카드를 함께 표시
                promptOwner = this;
                if (promptLabel != null) promptLabel.text = $"{machineName} 운동하기 (E)";
                if (promptBanner != null) promptBanner.SetActive(true);
                ShowInfoCard();
                if (kb.eKey.wasPressedThisFrame) Begin();
            }
            else if (promptOwner == this)
            {
                promptOwner = null;
                if (promptBanner != null) promptBanner.SetActive(false);
                if (infoCardRoot != null) infoCardRoot.SetActive(false);
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
        bool isCardio = IsContinuousCardio();

        if (isCardio)
        {
            // [추가] 천국의 계단(스텝밀): 누르는 동안 앞으로만 계속 오르고, 손을 떼면 그 자리에서 부드럽게 정지 (절대 역재생 안 함!)
            pull = Mathf.MoveTowards(pull, pressing ? 1f : 0f, 2.4f * Time.deltaTime);
            float delta = pull * 0.28f * Time.deltaTime; // 120프레임(6계단) 기준 자연스러운 오르기 속도
            cardioTime = (cardioTime + delta) % 1f;
            cardioStepAccum += delta;

            machine.Play(machineAnimState, 0, cardioTime);
            machine.Update(0f);
            SetDemoVisible(false);

            if (playerAnim != null && !string.IsNullOrEmpty(playerAnimState))
            {
                playerAnim.Play(playerAnimState, 0, cardioTime);
                playerAnim.Update(0f);
            }

            UpdateExerciseUi(pressing);

            // 6계단 루프 중 1계단(1/6 = 0.1667) 오를 때마다 1회(1걸음) 카운트
            const float oneStep = 1f / 6f;
            if (cardioStepAccum >= oneStep)
            {
                cardioStepAccum -= oneStep;
                reps++;
                OnRepCompleted(reps);
                if (reps >= targetReps) { End(); return; }
            }
            return;
        }

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
            hudSubText.text = GetEffectiveGuide().hudTip;

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
        pull = 0; cardioTime = 0; cardioStepAccum = 0; reps = 0; wentDown = false; holdBtn = false;
        promptOwner = null;
        if (promptBanner != null) promptBanner.SetActive(false);
        if (infoCardRoot != null) infoCardRoot.SetActive(false);
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
            var g = GetEffectiveGuide();
            trainer.StartCoaching(seatPoint, faceT, an);
            trainer.SayCoaching($"{machineName} 운동을 시작합니다! {g.part}에 좋은 기구예요. {g.howTo}");
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
