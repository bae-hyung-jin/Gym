using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement; // [추가] 추천 코스 GX룸 단계 이동용
using UnityEngine.UI;
#if UNITY_WEBGL && !UNITY_EDITOR
using System.Runtime.InteropServices; // [추가] WebGL 브라우저 팝업(YouTubeModal.jslib) 호출용
#endif

// 문 앞 트리거 또는 에디터 UI 팝업에서 불편한 자세를 선택받아 AI 트레이너(DoorSurvey.Summary)에 전달한다.
public class DoorSurvey : MonoBehaviour
{
    [SerializeField] Font font;
    [SerializeField] DoorTrigger door;
    [SerializeField] string playerTag = "Player";
    [SerializeField] string[] options = { "허리를 숙이기 불편해요", "무릎을 굽히기 불편해요", "팔을 들어올리기 불편해요", "오래 서 있기 힘들어요" };

    [Header("결과 카드 & 패널 연결")]
    [SerializeField] GameObject onboardCanvas;  // [추가] 전체 온보딩 캔버스 (탐험 시작 시 닫기)
    [SerializeField] GameObject surveyPopup;    // [추가] 2/2 몸 상태 선택 팝업
    [SerializeField] GameObject resultPopup;    // [추가] 분석 결과 추천 코스 팝업
    [SerializeField] Text resultTitleText;      // [추가] 결과 제목 텍스트
    [SerializeField] Text resultRouteText;      // [추가] 추천 기구 코스 텍스트
    [SerializeField] Text resultTipText;        // [추가] 안전 안내 한 줄 텍스트

    [Header("추천 코스 안내 HUD & 이동 포인트 (Unity에서 위치·디자인 수정 가능)")]
    [SerializeField] GameObject routeHud;       // [추가] 왼쪽 위 추천 코스 미니 카드 (RouteCard)
    [SerializeField] Text routeStepText;        // [추가] 예: "추천 코스 · 1 / 3"
    [SerializeField] Text routeMachineText;     // [추가] 예: "체스트프레스"
    [SerializeField] Text routeMoveBtnText;     // [추가] "기구 앞으로 이동 →" / "GX룸으로 이동 →"
    [SerializeField] Transform playerTransform; // [추가] PlayerArmature (비우면 Player 태그로 자동 탐색)
    [SerializeField] Transform pointChestPress; // [추가] 체스트프레스 앞 이동 포인트
    [SerializeField] Transform pointLegExtension; // [추가] 레그 익스텐션 앞 이동 포인트
    [SerializeField] Transform pointLatPulldown;  // [추가] 랫풀다운 앞 이동 포인트
    [SerializeField] Transform pointLegPress;     // [추가] 파워 레그프레스 배치 후 연결할 이동 포인트

    [Header("2D AI 아바타 코칭 & TTS 연결 (Unity 캔버스에서 디자인 수정 가능)")]
    [SerializeField] GameObject coachBar;         // [추가] 하단 2D 아바타 + 말풍선 묶음 (CoachBar)
    [SerializeField] Text coachText;              // [추가] 아바타 말풍선 코칭 텍스트 (Txt_CoachSpeech)
    [SerializeField] TrainerVoice trainerVoice;   // [추가] Gemini TTS 음성 재생기 (GymUI의 TrainerVoice)

    [Header("상단 진행도 바 연결 (Unity Slider)")]
    [SerializeField] GameObject progressPanel;    // [추가] 상단 가운데 진행도 바 패널 (ProgressPanel)
    [SerializeField] Slider progressSlider;       // [추가] 게이지 + 미니 트레이너 아이콘 슬라이더
    [SerializeField] Text progressText;           // [추가] 예: "1 / 3 단계 (33%) · 2개 남았어요"

    [Header("루틴 시범 영상 링크 (방식 2: 검수된 안전 영상 풀 + 부위별 기본 링크)")]
    [SerializeField] GeminiClient geminiClient; // [추가] 비워두면 씬에서 자동으로 찾음
    [SerializeField] bool useLiveGoogleSearch = false; // [수정] 무료 API 키에서는 Google Search 도구가 429 제한이라 기본 false (유료 키일 때만 켜기)
    [SerializeField] VideoItem[] curatedVideos; // [추가] 인스펙터에 직접 영상 추가 가능 (비어 있으면 아래 기본 검수 영상 5종 사용)
    [SerializeField] string defaultVideoUrl = "https://www.youtube.com/watch?v=Vm8-ix8r09U"; // [수정] 시니어 의자 스트레칭
    [SerializeField] string backVideoUrl = "https://www.youtube.com/watch?v=H-QUykaDdXI"; // [수정] 의자 5분 무릎·허리 시니어 루틴
    [SerializeField] string shoulderVideoUrl = "https://www.youtube.com/watch?v=bxZBz63MYI8"; // [수정] 레그프레스·레그익스텐션 안전 가이드
    [SerializeField] string kneeVideoUrl = "https://www.youtube.com/watch?v=6Qn-prZpl-Q"; // [수정] 무릎 지키면서 허벅지 키우는 레그 익스텐션
    [SerializeField] string legsVideoUrl = "https://youtube.com/shorts/eb1ggJDALjs?si=PV_0c0ufs_XHnePh"; // [수정] 하체 근력 안전 가이드

    // [추가] 인스펙터가 비어 있어도 바로 동작하는 검증 완료 한국어 시니어 운동 영상 풀 (oEmbed 퍼가기 확인 완료)
    static readonly VideoItem[] DefaultCuratedVideos =
    {
        new VideoItem { title = "의자에서 끝내는 5분 허리·무릎 시니어 관절 루틴", tags = "허리, 무릎, 의자, 좌식, 관절보호", url = "https://www.youtube.com/watch?v=H-QUykaDdXI" },
        new VideoItem { title = "레그프레스·레그익스텐션 무릎 통증 없이 근력 운동하는 법", tags = "하체, 체력, 어깨, 팔, 레그프레스, 레그익스텐션", url = "https://www.youtube.com/watch?v=bxZBz63MYI8" },
        new VideoItem { title = "무릎을 지키면서 허벅지 키우는 레그 익스텐션 기초", tags = "무릎, 하체, 허벅지, 레그익스텐션", url = "https://www.youtube.com/watch?v=6Qn-prZpl-Q" },
        new VideoItem { title = "랫풀다운 머신 제대로 쓰는 법 (헬스기구 기초편)", tags = "등, 상체, 무릎보호, 랫풀다운", url = "https://www.youtube.com/watch?v=VCbhdTq3ha8" },
        new VideoItem { title = "시니어 의자 스트레칭 (허리·전신 마무리)", tags = "허리, 전신, 스트레칭, GX룸, 시니어", url = "https://www.youtube.com/watch?v=Vm8-ix8r09U" }
    };

    // [추가] 인스펙터에서 검수된 유튜브 영상 여러 개를 관리하기 위한 구조체
    [System.Serializable]
    public class VideoItem
    {
        public string title; // 영상 제목 (예: 허리 부담 없는 체스트프레스 시니어 가이드)
        public string tags;  // 관련 부위 키워드 (예: 허리, 체스트프레스)
        public string url;   // 유튜브 주소 (watch?v=... 또는 youtu.be/...)
    }

    bool searchingVideo; // [추가] 영상 검색 중 중복 클릭 방지
    string lastRouteText = ""; // [추가] 추천 코스 문자열 기억 (영상 검색 참고용)
    readonly List<string> routeSteps = new(); // [추가] 확정된 추천 코스 단계 목록
    int routeStepIndex; // [추가] 현재 진행 중인 추천 코스 단계 번호 (0부터)
    int coachTicket;    // [추가] 빠르게 단계를 넘길 때 이전 기구 AI 답변 무시용 티켓
    string lastCoachSpeech = ""; // [추가] '다시 듣기' 버튼용 마지막 코칭 대사

#if UNITY_WEBGL && !UNITY_EDITOR
    // [추가] Assets/Plugins/WebGL/YouTubeModal.jslib 안의 인앱 유튜브 팝업 함수 연결
    [DllImport("__Internal")] static extern void OpenYouTubeModal(string url, string title);
#endif

    // 트레이너에게 질문할 때 같이 보낸다.
    public static string Summary { get; private set; } = "없음";
    public static bool IsFreeMode { get; private set; } = true; // [추가] 자유 탐색 여부

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void ResetSummary()
    {
        Summary = "없음";
        IsFreeMode = true;
    }

    readonly List<string> picked = new();
    readonly List<Button> activeButtons = new();
    bool done;
    bool frozeOnEnable; // [추가] OnEnable에서 플레이어를 잠갔는지 기억 (중복 Pop 방지)
    GameObject root;

    [SerializeField] Color OffColor = new Color(0.922f, 0.902f, 0.851f, 1f); // 미선택 베이직
    [SerializeField] Color OnColor = new Color(1f, 0.788f, 0.157f, 1f); // 선택 노랑

    // [추가] 팝업(OnBoardCanvas)이 켜질 때 Start()보다 먼저 실행되어 마우스 커서를 풀어줌
    void OnEnable()
    {
        if (door != null) return; // 예전 문 앞 트리거 모드에서는 실행하지 않음
        frozeOnEnable = true;
        PlayerFreeze.Push();                    // 플레이어 이동·카메라 회전 정지
        Cursor.lockState = CursorLockMode.None; // 마우스 잠금 해제 (버튼 클릭 가능)
        Cursor.visible = true;                  // 마우스 커서 보이기
    }

    // [추가] 팝업(OnBoardCanvas)이 꺼질 때 자동으로 1인칭 조작 모드로 복귀
    void OnDisable()
    {
        if (!frozeOnEnable) return;
        frozeOnEnable = false;
        PlayerFreeze.Pop(); // [수정] 플레이어 이동만 복구 (마우스는 잠그지 않고 계속 보이게 유지)
    }

    void Start()
    {
        if (door != null) door.SetLocked(true); // 문 트리거 모드일 때만 문을 잠근다
    }

    // 에디터에서 만든 선택 버튼의 OnClick에 연결해서 토글한다.
    public void ToggleOptionButton(Button btn)
    {
        if (btn == null) return;
        var label = btn.GetComponentInChildren<Text>();
        if (label == null) return;

        string raw = label.text.StartsWith("✓ ") ? label.text.Substring(2) : label.text;
        // [추가] 지금 누른 버튼이 5번('불편한 곳 없음 / 자유 탐색')인지 판별
        bool isFreeBtn = raw.Contains("없음") || raw.Contains("자유");
        bool isOn;

        if (picked.Remove(raw))
        {
            // [추가] 이미 켜진 버튼을 다시 눌러 끌 때 activeButtons 목록에서도 제거
            activeButtons.Remove(btn);
            isOn = false;
        }
        else
        {
            // [추가] 5번(자유 탐색)과 1~4번(불편 부위)이 동시에 켜지지 않도록 서로 자동 해제
            if (isFreeBtn)
            {
                // 5번을 눌렀으면 기존에 켜져 있던 1~4번 버튼을 전부 끄고 목록 비우기
                foreach (var b in activeButtons) TurnOffButton(b);
                activeButtons.Clear();
                picked.Clear();
            }
            else
            {
                // 1~4번을 눌렀으면 켜져 있던 5번(없음/자유) 버튼만 찾아서 끄기 (삭제 시 뒤에서부터 순회)
                for (int i = activeButtons.Count - 1; i >= 0; i--)
                {
                    var b = activeButtons[i];
                    var l = b.GetComponentInChildren<Text>();
                    string t = l != null ? (l.text.StartsWith("✓ ") ? l.text.Substring(2) : l.text) : "";
                    if (t.Contains("없음") || t.Contains("자유"))
                    {
                        TurnOffButton(b);
                        activeButtons.RemoveAt(i);
                        picked.Remove(t);
                    }
                }
            }

            picked.Add(raw);
            // [추가] 새로 켠 버튼을 activeButtons에 기억해 두기 (나중에 끌 때 사용)
            activeButtons.Add(btn);
            isOn = true;
        }

        if (btn.targetGraphic != null)
            btn.targetGraphic.color = isOn ? OnColor : OffColor;
        label.text = isOn ? ("✓ " + raw) : raw;

        // [수정] 아무것도 안 골랐거나 5번(자유 탐색)만 골랐을 때는 Summary를 "없음"으로 통일
        bool onlyFree = picked.Count == 0 || (picked.Count == 1 && isFreeBtn);
        IsFreeMode = onlyFree;
        Summary = onlyFree ? "없음" : string.Join(", ", picked);
        Debug.Log("[설문] 불편한 자세: " + Summary);
    }

    // [추가] '분석받기' 버튼 OnClick에 연결 — 5번(자유)이면 바로 시작, 1~4번이면 0초 맞춤 코스 카드 표시
    public void OnClickAnalyze()
    {
        bool onlyFree = picked.Count == 0 || (picked.Count == 1 && (picked[0].Contains("없음") || picked[0].Contains("자유")));
        IsFreeMode = onlyFree;
        Summary = onlyFree ? "없음" : string.Join(", ", picked);

        if (onlyFree || resultPopup == null)
        {
            StartFreeExplore();
            return;
        }

        // AI 호출 없이(대기 0초) 직접 설계한 안전 기구 루트 생성
        BuildRoute(out string title, out string route, out string tip);
        lastRouteText = route; // [추가] 나중에 영상 검색할 때 추천 기구 참고용으로 저장
        if (resultTitleText != null) resultTitleText.text = title;
        if (resultRouteText != null) resultRouteText.text = route;
        if (resultTipText != null) resultTipText.text = tip;

        if (surveyPopup != null) surveyPopup.SetActive(false);
        resultPopup.SetActive(true);
    }

    // [추가] '추천 코스로 시작하기' 버튼 OnClick
    public void StartRecommendedRoute()
    {
        IsFreeMode = false;
        Debug.Log("[온보딩] 추천 코스 모드로 시작! 불편 부위: " + Summary);
        CloseOnboarding();

        // [추가] 추천 코스 HUD 켜기 + 1단계 기구 앞으로 바로 안내!
        if (routeSteps.Count == 0) BuildRoute(out _, out _, out _);
        routeStepIndex = 0;
        if (routeHud != null) routeHud.SetActive(true);
        if (progressPanel != null) progressPanel.SetActive(true); // [추가] 상단 진행도 바 표시
        RefreshRouteHud();

        // 1단계가 씬 이동(GX룸)이 아닌 헬스장 내 기구라면 바로 기구 앞으로 이동해 드림
        if (routeSteps.Count > 0 && !routeSteps[0].Contains("GX"))
            GoCurrentStep();

        CoachCurrentStep(); // [추가] 2D AI 아바타 등장 + Gemini 실시간 맞춤 코칭 + TTS 음성 재생!
    }

    // [추가] '자유 탐색' 버튼 OnClick
    public void StartFreeExplore()
    {
        IsFreeMode = true;
        if (routeHud != null) routeHud.SetActive(false); // [추가] 자유 탐색 시 추천 코스 카드 숨김
        if (progressPanel != null) progressPanel.SetActive(false); // [추가] 자유 탐색 시 진행도 바 숨김
        if (coachBar != null) coachBar.SetActive(false); // [추가] 자유 탐색 시 코칭 바 숨김
        trainerVoice?.Stop();
        Debug.Log("[온보딩] 자유 탐색 모드로 시작!");
        CloseOnboarding();
    }

    // [추가] 추천 코스 HUD '기구 앞으로 이동 →' 버튼 On Click()
    public void GoCurrentStep()
    {
        if (routeSteps.Count == 0 || routeStepIndex >= routeSteps.Count) return;
        string step = routeSteps[routeStepIndex];

        if (step.Contains("GX"))
        {
            SceneManager.LoadScene("GXStudio");
            return;
        }

        Transform target = null;
        if (step.Contains("체스트")) target = pointChestPress;
        else if (step.Contains("익스텐션")) target = pointLegExtension;
        else if (step.Contains("랫풀")) target = pointLatPulldown;
        else if (step.Contains("레그프레스")) target = pointLegPress != null ? pointLegPress : pointLegExtension;

        if (target == null) return;
        if (playerTransform == null)
        {
            var p = GameObject.FindGameObjectWithTag(playerTag);
            if (p != null) playerTransform = p.transform;
        }
        if (playerTransform == null) return;

        // CharacterController 충돌 방지를 위해 잠시 끄고 이동 후 다시 켠다
        var cc = playerTransform.GetComponent<CharacterController>();
        if (cc != null) cc.enabled = false;
        playerTransform.position = target.position;
        playerTransform.rotation = Quaternion.Euler(0f, target.eulerAngles.y, 0f);
        if (cc != null) cc.enabled = true;
    }

    // [추가] 추천 코스 HUD '다음 단계 >' 버튼 On Click()
    public void NextStep()
    {
        if (routeSteps.Count == 0) return;
        if (routeStepIndex + 1 < routeSteps.Count)
        {
            routeStepIndex++;
            RefreshRouteHud();
            if (!routeSteps[routeStepIndex].Contains("GX"))
                GoCurrentStep();
            CoachCurrentStep(); // [추가] 다음 기구 맞춤 AI 코칭 + TTS 재생
        }
        else
        {
            if (routeStepText != null) routeStepText.text = "추천 코스 완료!";
            if (routeMachineText != null) routeMachineText.text = "오늘 코스를 모두 둘러보셨어요";
            if (routeMoveBtnText != null) routeMoveBtnText.text = "다시 이동";
            if (progressSlider != null) progressSlider.value = 1f; // [추가] 진행도 100%
            if (progressText != null) progressText.text = $"추천 코스 완료! ({routeSteps.Count} / {routeSteps.Count} · 100%)";
            PlayCoachMessage("추천 코스를 모두 둘러보셨어요! 정말 수고 많으셨습니다. 오른쪽 위 요약 버튼으로 오늘의 리포트도 확인해 보세요.");
        }
    }

    // [추가] 추천 코스 HUD '< 이전 단계' 버튼 On Click()
    public void PrevStep()
    {
        if (routeSteps.Count == 0 || routeStepIndex <= 0) return; // 1단계일 땐 더 뒤로 안 감
        routeStepIndex--;
        RefreshRouteHud();
        if (!routeSteps[routeStepIndex].Contains("GX"))
            GoCurrentStep();
        CoachCurrentStep(); // [추가] 이전 기구 맞춤 AI 코칭 + TTS 재생
    }

    // [추가] 추천 코스 HUD '✕' 닫기 버튼 On Click()
    public void CloseRouteHud()
    {
        if (routeHud != null) routeHud.SetActive(false);
        if (progressPanel != null) progressPanel.SetActive(false); // [추가] 상단 진행도 바도 함께 닫기
        CloseCoachBar();
    }

    // [추가] 2D 아바타 말풍선 '🔊 다시 듣기' 버튼 On Click()
    public void ReplayCoachVoice()
    {
        if (trainerVoice == null) trainerVoice = FindFirstObjectByType<TrainerVoice>();
        if (!string.IsNullOrEmpty(lastCoachSpeech))
            trainerVoice?.Say(lastCoachSpeech);
    }

    // [추가] 2D 아바타 말풍선 '✕' 닫기 버튼 On Click()
    public void CloseCoachBar()
    {
        coachTicket++;
        trainerVoice?.Stop();
        if (coachBar != null) coachBar.SetActive(false);
    }

    // [추가] 현재 기구 + 어르신 불편 부위에 맞춰 Gemini AI가 실시간 코칭 문장을 만들고 TTS로 읽어줌
    void CoachCurrentStep()
    {
        if (routeSteps.Count == 0 || routeStepIndex >= routeSteps.Count) return;
        string step = routeSteps[routeStepIndex];

        if (geminiClient == null) geminiClient = FindFirstObjectByType<GeminiClient>();
        if (trainerVoice == null) trainerVoice = FindFirstObjectByType<TrainerVoice>();

        trainerVoice?.Stop();
        if (coachBar != null)
        {
            // 껐다가 켜면 Fade-In 애니메이션이 매 단계마다 부드럽게 다시 재생됨
            coachBar.SetActive(false);
            coachBar.SetActive(true);
        }

        int myTicket = ++coachTicket;
        if (coachText != null)
            coachText.text = $"{step} 맞춤 코칭을 준비하고 있어요...";

        if (geminiClient == null)
        {
            PlayCoachMessage(GetFallbackCoaching(step));
            return;
        }

        string prompt =
            $"[어르신 불편 부위: {Summary}]\n" +
            $"어르신이 추천 코스 중 '{step}' 앞으로 이동했다. " +
            "이 운동이 어디에 좋은지, 불편한 부위에 무리가 가지 않도록 어떤 자세로 천천히 하면 좋은지 " +
            "따뜻하고 쉬운 한국어 두 문장으로 코칭해 줘. 영어·괄호·특수기호는 절대 쓰지 마.";

        geminiClient.Ask(prompt, reply =>
        {
            if (myTicket != coachTicket) return; // 이미 다른 단계로 넘어갔으면 무시
            string speech = (string.IsNullOrEmpty(reply) || reply.StartsWith("[오류]"))
                ? GetFallbackCoaching(step)
                : reply.Trim();
            PlayCoachMessage(speech);
        });
    }

    void PlayCoachMessage(string speech)
    {
        lastCoachSpeech = speech;
        if (coachBar != null && !coachBar.activeSelf) coachBar.SetActive(true);
        if (coachText != null) coachText.text = speech;
        if (trainerVoice == null) trainerVoice = FindFirstObjectByType<TrainerVoice>();
        trainerVoice?.Say(speech);
    }

    string GetFallbackCoaching(string step)
    {
        string caution = Summary == "없음" ? "무리하지 마시고" : $"{Summary}에 무리가 가지 않도록";
        if (step.Contains("체스트"))
            return $"여기는 가슴과 팔 힘을 기르는 체스트프레스예요. {caution} 등받이에 등을 편하게 붙이고 천천히 밀어 보세요.";
        if (step.Contains("익스텐션"))
            return $"여기는 허벅지 앞쪽을 튼튼하게 하는 레그 익스텐션이에요. {caution} 가벼운 무게로 다리를 천천히 펴 보세요.";
        if (step.Contains("랫풀"))
            return $"여기는 등 근육을 부드럽게 키워 주는 랫풀다운이에요. {caution} 가슴을 펴고 바를 천천히 내려 보세요.";
        if (step.Contains("GX"))
            return $"여기는 스트레칭을 하는 GX룸 안내 단계예요. {caution} 위 이동 버튼을 눌러 편하게 몸을 풀어 보세요.";
        return $"{step} 기구 앞이에요. {caution} 가볍게 천천히 움직여 보시고 아프면 바로 멈추세요.";
    }

    void RefreshRouteHud()
    {
        if (routeSteps.Count == 0 || routeStepIndex >= routeSteps.Count) return;
        string step = routeSteps[routeStepIndex];
        int current = routeStepIndex + 1;
        int total = routeSteps.Count;
        int remaining = total - current;
        float ratio = (float)current / total;
        int pct = Mathf.RoundToInt(ratio * 100f);

        if (routeStepText != null) routeStepText.text = $"추천 코스 · {current} / {total}";
        if (routeMachineText != null) routeMachineText.text = step;
        if (routeMoveBtnText != null)
            routeMoveBtnText.text = step.Contains("GX") ? "GX룸으로 이동 →" : "기구 앞으로 이동 →";

        // [추가] 상단 진행도 슬라이더 & 남은 개수 문구 자동 갱신
        if (progressSlider != null) progressSlider.value = ratio;
        if (progressText != null)
            progressText.text = remaining > 0
                ? $"{current} / {total} 단계 ({pct}%) · {remaining}개 남았어요"
                : $"{current} / {total} 단계 (100%) · 마지막 단계예요!";
    }

    // [추가] '루틴 영상보기' 버튼 OnClick — 하이브리드 (방식 2 검수 풀 + 방식 1 Gemini 실시간 검색)
    public void OpenRoutineVideo()
    {
        if (searchingVideo) return; // 검색 중 중복 클릭 방지

        // 씬에 있는 GeminiClient 자동 연결 (인스펙터에 안 넣었어도 작동!)
        if (geminiClient == null)
            geminiClient = FindFirstObjectByType<GeminiClient>();

        // 1) 실시간 구글 검색 옵션이 켜져 있으면 먼저 시도 (유료 API 키용), 실패 시 자동으로 2번 검수 풀로 폴백
        if (useLiveGoogleSearch && geminiClient != null)
        {
            searchingVideo = true;
            if (resultTipText != null)
                resultTipText.text = "AI가 몸 상태에 딱 맞는 시범 영상을 찾고 있어요... 잠시만 기다려 주세요!";

            geminiClient.SearchYouTubeVideo(Summary, lastRouteText, (foundUrl, reason) =>
            {
                searchingVideo = false;
                if (!string.IsNullOrEmpty(foundUrl))
                {
                    if (resultTipText != null && !string.IsNullOrEmpty(reason))
                        resultTipText.text = reason;
                    LaunchVideoPopup(foundUrl, GetFallbackVideoTitle());
                }
                else
                {
                    // 무료 키 429 또는 검색 실패 시 -> 즉시 방식 2(검수 풀 + Gemini 선별)로 매끄럽게 전환!
                    PickFromCuratedPoolWithGemini();
                }
            });
            return;
        }

        // 2) 방식 2 (무료 API 키 100% 작동!): 검수된 안전 영상 목록 중 Gemini 4가 몸 상태에 가장 맞는 영상 1개 선별 + 추천 이유 생성
        if (geminiClient != null)
        {
            PickFromCuratedPoolWithGemini();
            return;
        }

        // 3) GeminiClient가 없거나 오프라인일 때는 바로 부위별 기본 영상 열기
        LaunchVideoPopup(GetFallbackVideoUrl(), GetFallbackVideoTitle());
    }

    // [추가] 방식 2: 검수된 안전 영상 목록 중에서 Gemini가 어르신 몸 상태 조합에 가장 맞는 1개를 골라줌 (재생 실패 0%!)
    void PickFromCuratedPoolWithGemini()
    {
        // 인스펙터에 직접 넣은 영상이 있으면 우선 사용, 비어 있으면 내장된 검수 영상 5종 사용!
        VideoItem[] pool = (curatedVideos != null && curatedVideos.Length > 0) ? curatedVideos : DefaultCuratedVideos;

        searchingVideo = true;
        if (resultTipText != null)
            resultTipText.text = "AI가 검수된 안전 영상 중 가장 알맞은 영상을 고르고 있어요...";

        var sb = new System.Text.StringBuilder();
        sb.AppendLine($"어르신이 고른 불편 부위: {Summary}");
        sb.AppendLine($"추천 코스: {lastRouteText.Replace("\n", ", ")}");
        sb.AppendLine("아래 검수된 시니어 운동 영상 목록 중 가장 안전한 1개를 골라 첫 줄에는 번호만(예: 1), 둘째 줄에는 어르신께 추천하는 이유를 공백 포함 35자 이내의 짧은 한 문장으로만 답해줘.");
        for (int i = 0; i < pool.Length; i++)
            sb.AppendLine($"{i + 1}. {pool[i].title} (태그: {pool[i].tags})");

        geminiClient.Ask(sb.ToString(), reply =>
        {
            searchingVideo = false;
            int idx = 0;
            string reason = "";

            if (!string.IsNullOrEmpty(reply) && !reply.StartsWith("[오류]"))
            {
                var lines = reply.Trim().Split(new[] { '\r', '\n' }, System.StringSplitOptions.RemoveEmptyEntries);
                var digits = System.Text.RegularExpressions.Regex.Match(lines[0], @"\d+");
                if (digits.Success && int.TryParse(digits.Value, out int pickedNum))
                    idx = Mathf.Clamp(pickedNum - 1, 0, pool.Length - 1);
                if (lines.Length > 1) reason = lines[1].Trim();
            }

            var chosen = pool[idx];
            if (resultTipText != null && !string.IsNullOrEmpty(reason))
                resultTipText.text = reason;

            string url = !string.IsNullOrEmpty(chosen.url) ? chosen.url : GetFallbackVideoUrl();
            string title = !string.IsNullOrEmpty(chosen.title) ? chosen.title : GetFallbackVideoTitle();
            LaunchVideoPopup(url, title);
        });
    }

    // [추가] 부위별 기본 안전 폴백 URL 선택
    string GetFallbackVideoUrl()
    {
        if (Summary.Contains("허리") && !string.IsNullOrEmpty(backVideoUrl)) return backVideoUrl;
        if ((Summary.Contains("어깨") || Summary.Contains("팔")) && !string.IsNullOrEmpty(shoulderVideoUrl)) return shoulderVideoUrl;
        if (Summary.Contains("무릎") && !string.IsNullOrEmpty(kneeVideoUrl)) return kneeVideoUrl;
        if ((Summary.Contains("하체") || Summary.Contains("서 있기")) && !string.IsNullOrEmpty(legsVideoUrl)) return legsVideoUrl;
        return defaultVideoUrl;
    }

    // [추가] 팝업 상단 제목 선택
    string GetFallbackVideoTitle()
    {
        if (Summary.Contains("허리")) return "허리 맞춤 안전 루틴 영상";
        if (Summary.Contains("어깨") || Summary.Contains("팔")) return "어깨·팔 맞춤 안전 루틴 영상";
        if (Summary.Contains("무릎")) return "무릎 맞춤 안전 루틴 영상";
        if (Summary.Contains("하체") || Summary.Contains("서 있기")) return "하체·체력 맞춤 안전 루틴 영상";
        return "맞춤 루틴 시범 영상";
    }

    // [추가] 실제 영상 팝업 실행 (WebGL = 인앱 YouTubeModal 팝업, 에디터 = 브라우저 열기)
    void LaunchVideoPopup(string url, string modalTitle)
    {
        if (string.IsNullOrEmpty(url)) return;
        Debug.Log($"[온보딩] 루틴 영상 열기: {modalTitle} ({url})");
#if UNITY_WEBGL && !UNITY_EDITOR
        OpenYouTubeModal(url, modalTitle);
#else
        Application.OpenURL(url);
#endif
    }

    void CloseOnboarding()
    {
        if (onboardCanvas != null) onboardCanvas.SetActive(false);
        else gameObject.SetActive(false);
    }

    // [추가] 불편 부위별 안전 추천 코스(고정 설계, AI 개입 없음)
    void BuildRoute(out string title, out string route, out string tip)
    {
        bool avoidBack = Summary.Contains("허리");
        bool avoidShoulder = Summary.Contains("어깨") || Summary.Contains("팔");
        bool avoidKnee = Summary.Contains("무릎");
        bool weakLegs = Summary.Contains("하체") || Summary.Contains("서 있기");

        // [추가] 선택한 불편 부위가 몇 개인지 계산
        int count = (avoidBack ? 1 : 0) + (avoidShoulder ? 1 : 0) + (avoidKnee ? 1 : 0) + (weakLegs ? 1 : 0);

        routeSteps.Clear();

        // [추가] 3~4개 부위가 동시에 불편한 경우(전신 부담) -> 무리한 근력 기구 대신 가벼운 스트레칭 & 상담 우선!
        if (count >= 3)
        {
            routeSteps.Add("GX룸 의자 스트레칭");
            routeSteps.Add("체스트프레스 (가벼운 빈 동작)");
            title = "오늘은 무리 없이 가볍게 시작해요!";
            route = "1단계 · GX룸 의자 스트레칭\n2단계 · 체스트프레스 (가벼운 빈 동작)\n3단계 · 현장 선생님 상담 후 진행 권장";
            tip = "여러 부위가 동시에 불편하시니 무리한 기구보다 가벼운 스트레칭과 둘러보기 위주로 천천히 시작해요.";
            return;
        }

        // [수정] 현재 씬에 배치된 3개 기구(체스트프레스·레그 익스텐션·랫풀다운) + GX룸 기준으로 코스 구성
        // (파워 레그프레스 배치 후 pointLegPress가 연결되면 자동 확장 가능)
        var steps = new List<string>();
        if (!avoidShoulder || avoidKnee || avoidBack)
            steps.Add("체스트프레스");
        if (!avoidKnee || weakLegs || avoidShoulder || avoidBack)
            steps.Add("레그 익스텐션 (가볍게)");
        if (!avoidShoulder)
            steps.Add("랫풀다운");
        steps.Add("GX룸 스트레칭");

        if (steps.Count > 3)
            steps = steps.GetRange(0, 3);
        routeSteps.AddRange(steps);

        title = "안전한 맞춤 추천 코스를 준비했어요!";
        var lines = new List<string>();
        for (int i = 0; i < steps.Count; i++)
            lines.Add($"{i + 1}단계 · {steps[i]}");
        route = string.Join("\n", lines);

        if (avoidBack)
            tip = "허리에 부담이 적은 등받이 좌식 기구 위주로 구성했어요.\n원하시면 언제든 자유롭게 둘러보실 수 있어요.";
        else if (avoidShoulder)
            tip = "팔을 높이 드는 동작은 빼고 안전한 높이의 기구만 모았어요.\n원하시면 언제든 자유롭게 둘러보실 수 있어요.";
        else if (avoidKnee)
            tip = "무릎을 깊게 굽히는 부담은 줄이고 상체·가벼운 하체로 구성했어요.\n원하시면 언제든 자유롭게 둘러보실 수 있어요.";
        else
            tip = "오래 서 있지 않고 모두 앉아서 편하게 다리 힘을 키우는 코스예요.\n원하시면 언제든 자유롭게 둘러보실 수 있어요.";
    }

    void TurnOffButton(Button b)
    {
        var l = b.GetComponentInChildren<Text>();
        if (b.targetGraphic != null) b.targetGraphic.color = OffColor;
        if (l != null && l.text.StartsWith("✓ ")) l.text = l.text.Substring(2);
    }

    void OnTriggerEnter(Collider other)
    {
        if (door == null || done || root != null || !other.CompareTag(playerTag)) return;
        Build();
    }

    void Build()
    {
        var canvas = UiKit.MakeCanvas("SurveyCanvas", 90);
        root = canvas.gameObject;
        var t = canvas.transform;
        UiKit.Panel(t, new Vector2(2000, 1200), Vector2.zero, new Color(0, 0, 0, 0.55f));
        UiKit.Panel(t, new Vector2(1200, 860), Vector2.zero, new Color(0.1f, 0.13f, 0.2f, 0.97f));
        UiKit.Label(t, font, "어느 자세가 불편하신가요?\n(여러 개 골라도 됩니다)", 46, new Vector2(1100, 160), new Vector2(0, 320));

        var off = new Color(0.25f, 0.3f, 0.4f);
        var on = new Color(0.15f, 0.55f, 0.45f);
        for (var i = 0; i < options.Length; i++)
        {
            var text = options[i];
            var b = UiKit.Btn(t, font, text, 40, new Vector2(900, 100), new Vector2(0, 170 - i * 120), off);
            b.onClick.AddListener(() =>
            {
                if (!picked.Remove(text)) picked.Add(text);
                b.targetGraphic.color = picked.Contains(text) ? on : off;
            });
        }
        var go = UiKit.Btn(t, font, "선택 완료", 42, new Vector2(700, 110), new Vector2(0, -330), new Color(0.2f, 0.45f, 0.75f));
        go.onClick.AddListener(Finish);
        PlayerFreeze.Push();
    }

    void Finish()
    {
        Summary = picked.Count == 0 ? "없음" : string.Join(", ", picked);
        done = true;
        PlayerFreeze.Pop();
        Destroy(root);
        if (door != null) door.SetLocked(false);
        Debug.Log("[설문] 불편한 자세: " + Summary);
    }
}
