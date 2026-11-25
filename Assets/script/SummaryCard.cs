using System;
using System.Collections;
using System.IO;
using System.Runtime.InteropServices;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement; // [추가] 메인(Intro) 씬 복귀용
using UnityEngine.UI;

// 헬스장 문으로 나가면 Gemini가 네 칸(잘 맞아요 / 선생님께 질문 / 다음에 해 보세요 / 선생님과 먼저 확인)으로 정리한 카드를 보여 준다.
// 카드는 기기에 저장되고(C키로 다시 보기), 이미지로 내려받아 다음 방문 때 선생님께 보여 줄 수 있다.
// 이번 방문에서 한 운동 기록
public static class SessionLog
{
    static readonly System.Collections.Generic.Dictionary<string, int> reps = new();

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reset() => reps.Clear();

    public static void Add(string machine, int n) => reps[machine] = (reps.TryGetValue(machine, out var v) ? v : 0) + n;
    public static int Total { get { var t = 0; foreach (var v in reps.Values) t += v; return t; } }
    public static string Summary()
    {
        if (reps.Count == 0) return "직접 해 본 운동 없음";
        var l = new System.Collections.Generic.List<string>();
        foreach (var kv in reps) l.Add(kv.Key + " " + kv.Value + "회");
        return string.Join(", ", l);
    }
}

public class SummaryCard : MonoBehaviour
{
    [Header("자동 퇴장 감지 (기본 OFF — 위 버튼으로 직접 열기 추천)")]
    [SerializeField] bool autoOpenOnExit = false; // [추가] 문 밖으로 나갈 때 자동으로 띄울지 여부
    [SerializeField] float insideZ = -7f;         // 이보다 안쪽(+z)으로 들어갔다가
    [SerializeField] float outsideZ = -11f;       // 이보다 바깥(-z)으로 나오면 카드를 띄운다
    Transform player;
    bool wasInside;

    [SerializeField] GeminiClient client;

    [Header("SummaryCanvas UI 직접 연결 (디자인·버튼 클릭은 Unity에서 관리)")]
    [SerializeField] GameObject root;             // [추가] SummaryPopup (카드 전체)
    [SerializeField] GameObject openBtn;          // [추가] 오른쪽 위 '체험 끝내기 · 요약' 버튼
    [SerializeField] GameObject buttons;          // [추가] 이미지 저장 시 숨길 하단 버튼 묶음
    [SerializeField] Text sub;                    // [추가] 날짜 · 체험 기구 부제 텍스트
    [SerializeField] Text[] body = new Text[4];   // [추가] 4칸 본문 텍스트 (잘 맞아요 / 질문 / 다음 / 확인)

    [Header("바디맵 하이라이트 & 운동 리스트 (Unity 캔버스에서 위치·색상 수정 가능)")]
    [SerializeField] GameObject markBack;         // [추가] 허리 주의 하이라이트
    [SerializeField] GameObject markShoulder;     // [추가] 어깨·팔 주의 하이라이트
    [SerializeField] GameObject markKnee;         // [추가] 무릎 주의 하이라이트
    [SerializeField] GameObject markLegs;         // [추가] 하체·허벅지 주의 하이라이트
    [SerializeField] GameObject markUpper;        // [추가] 상체 추천·운동 부위 하이라이트
    [SerializeField] GameObject markLower;        // [추가] 하체 추천·운동 부위 하이라이트
    [SerializeField] Text[] routineNames = new Text[3]; // [추가] 오른쪽 운동 리스트 기구명 3줄
    [SerializeField] Text[] routineParts = new Text[3]; // [추가] 오른쪽 운동 리스트 자극 부위 3줄

    const string Key = "summary_card";
    [Serializable] class Data { public string date, machine, ok, ask, next, check; public int reps; }

#if UNITY_WEBGL && !UNITY_EDITOR
    [DllImport("__Internal")] static extern void DownloadFile(string name, byte[] data, int size);
#endif

    Data current;
    bool open;

    void Start()
    {
        // [수정] 옛날 UiKit 코드 생성 30줄 삭제! Unity에서 만든 SummaryCanvas를 그대로 사용
        if (root != null) root.SetActive(false);
    }

    void Update()
    {
        if (root == null) return;

        // [추가] 팝업·운동 중에는 오른쪽 위 '체험 끝내기' 버튼을 깔끔하게 숨김
        bool showOpen = !open && !ExerciseStation.InUse && !PlayerFreeze.Frozen;
        if (openBtn != null && openBtn.activeSelf != showOpen) openBtn.SetActive(showOpen);

        if (autoOpenOnExit)
        {
            if (player == null) { var p = GameObject.FindGameObjectWithTag("Player"); if (p != null) player = p.transform; }
            if (player != null && !open)
            {
                var z = player.position.z;
                if (z > insideZ) wasInside = true;
                else if (z < outsideZ && wasInside) { wasInside = false; Make(SessionLog.Summary(), SessionLog.Total); }
            }
        }

        var kb = Keyboard.current;
        if (kb == null) return;
        if (open && kb.escapeKey.wasPressedThisFrame) Close(); // [추가] ESC로도 요약 카드 닫기
        else if (!open && !PlayerFreeze.Frozen && kb.cKey.wasPressedThisFrame && PlayerPrefs.HasKey(Key))
            Display(JsonUtility.FromJson<Data>(PlayerPrefs.GetString(Key)));
    }

    // [추가] Unity 버튼(Btn_EndExperience) On Click()에 연결
    public void OpenSummary() => Make(SessionLog.Summary(), SessionLog.Total);

    // [추가] Unity 버튼(Btn_SaveImage) On Click()에 연결
    public void SaveCardImage() => StartCoroutine(SaveImage());

    // [수정] public 변경 → Unity 버튼(Btn_Close) On Click()에 연결
    public void Close()
    {
        if (!open) return;
        open = false;
        if (root != null) root.SetActive(false);
        PlayerFreeze.Pop();
    }

    // [추가] Unity 버튼(Btn_GoMain) On Click()에 연결 — 메인(Intro) 씬으로 복귀
    public void GoToMain()
    {
        Close();
        SceneManager.LoadScene(0); // Build Settings 0번(Intro 씬)으로 안전하게 이동
    }

    // 헬스장을 나올 때 호출한다. Gemini 답이 올 때까지 "정리하는 중"을 보여 준다.
    public void Make(string activity, int reps)
    {
        var d = new Data { date = DateTime.Now.ToString("yyyy.MM.dd"), machine = activity, reps = reps, ok = "정리하는 중...", ask = "정리하는 중...", next = "정리하는 중...", check = "정리하는 중..." };
        Display(d);
        client.Ask($"[손님 정보: 불편한 자세 '{DoorSurvey.Summary}', 한 운동 '{activity}']\n어르신용 운동 체험 요약을 아래 JSON 한 줄만 출력해(설명·코드블록 금지). " +
                   "ok=몸에 잘 맞았을 것 같은 점, ask=현장 선생님께 물어볼 것, next=다음에 해 볼 것, check=선생님과 먼저 확인할 것. 값은 쉬운 한국어 30자 이내.\n" +
                   "{\"ok\":\"\",\"ask\":\"\",\"next\":\"\",\"check\":\"\"}", reply =>
        {
            var a = reply.IndexOf('{'); var b = reply.LastIndexOf('}');
            Data parsed = null;
            if (a >= 0 && b > a) try { parsed = JsonUtility.FromJson<Data>(reply.Substring(a, b - a + 1)); } catch (ArgumentException) { }
            // 못 읽으면 기본 문구. 체험 내용을 잃지 않게 카드는 항상 채운다
            d.ok = Pick(parsed?.ok, activity);
            d.ask = Pick(parsed?.ask, "알맞은 무게와 횟수가 궁금해요");
            d.next = Pick(parsed?.next, "천천히 횟수를 늘려 보세요");
            d.check = Pick(parsed?.check, $"불편한 곳: {DoorSurvey.Summary}");
            Fill(d); // 이미 닫았어도 카드를 다시 띄우지는 않고 저장만 한다
            PlayerPrefs.SetString(Key, JsonUtility.ToJson(d)); PlayerPrefs.Save();
        });
    }

    static string Pick(string v, string fallback) => string.IsNullOrWhiteSpace(v) ? fallback : v.Trim();

    void Display(Data d)
    {
        if (d == null) return;
        Fill(d);
        UpdateBodyMapAndRoutines(); // [추가] 불편 부위·추천 기구에 맞춰 바디맵과 운동 리스트 갱신
        if (open) return;
        open = true; root.SetActive(true); PlayerFreeze.Push();
    }

    // [추가] 설문(DoorSurvey.Summary)에 따라 인체 바디맵 부위 하이라이트 + 운동 리스트 3줄을 자동 표시
    void UpdateBodyMapAndRoutines()
    {
        string s = DoorSurvey.Summary ?? "";
        bool hasBack     = s.Contains("허리");
        bool hasShoulder = s.Contains("어깨") || s.Contains("팔");
        bool hasKnee     = s.Contains("무릎");
        bool hasLegs     = s.Contains("하체") || s.Contains("서 있기");

        if (markBack     != null) markBack.SetActive(hasBack);
        if (markShoulder != null) markShoulder.SetActive(hasShoulder);
        if (markKnee     != null) markKnee.SetActive(hasKnee);
        if (markLegs     != null) markLegs.SetActive(hasLegs);
        if (markUpper    != null) markUpper.SetActive(!hasShoulder);
        if (markLower    != null) markLower.SetActive(!hasKnee && !hasLegs);

        // [수정] DoorSurvey에서 생성한 실제 맞춤 코스가 있으면 그대로 반영, 없으면 11종 기구 기반 기본 추천 구성
        string[] names;
        string[] parts;
        var built = DoorSurvey.CurrentRouteSteps;
        if (built != null && built.Count >= 3)
        {
            names = new[] { built[0], built[1], built.Count >= 4 ? $"{built[2]} · {built[3]}" : built[2] };
            parts = new[] { DescribeMachinePart(built[0]), DescribeMachinePart(built[1]), DescribeMachinePart(built[2]) };
        }
        else if (hasShoulder && (hasKnee || hasLegs))
        {
            names = new[] { "힙 어덕션 (가볍게)", "암컬 머신 (가벼운 무게)", "GX룸 의자 스트레칭" };
            parts = new[] { "허벅지 안쪽 · 골반 안정", "팔 앞쪽 근력 (관절 부담 최소)", "전신 관절 부드럽게 풀기" };
        }
        else if (hasShoulder)
        {
            names = new[] { "힙 어덕션", "라잉 레그컬", "파워 레그프레스 · 스텝밀" };
            parts = new[] { "허벅지 안쪽 · 골반 안정", "허벅지 뒤쪽 (햄스트링)", "하체 근력 · 심폐 체력" };
        }
        else if (hasKnee)
        {
            names = new[] { "플레이트 로디드 벤치프레스", "랫풀다운 · 암컬 머신", "힙 어덕션 (가볍게)" };
            parts = new[] { "가슴 · 팔 뒤쪽 근력", "등 근육 · 이두근", "허벅지 안쪽 · 골반 안정" };
        }
        else if (hasLegs)
        {
            names = new[] { "파워 레그프레스", "라잉 레그컬", "힙 어덕션 · 레그 익스텐션" };
            parts = new[] { "허벅지 전반 · 엉덩이", "허벅지 뒤쪽 (무릎 보호)", "허벅지 안쪽 · 앞쪽 균형" };
        }
        else if (hasBack)
        {
            names = new[] { "체스트프레스 (등받이 밀착)", "힙 어덕션", "레그 익스텐션 · 암컬 머신" };
            parts = new[] { "가슴 · 상체 안정", "허벅지 안쪽 · 골반 지지", "하체 · 팔 (허리 부담 최소)" };
        }
        else
        {
            names = new[] { "천국의 계단 (스텝밀)", "플레이트 로디드 벤치프레스", "V-스쿼트 · 랫풀다운" };
            parts = new[] { "심폐 지구력 · 하체 활력", "가슴 · 상체 근력", "하체 전반 · 등 근육 균형" };
        }

        for (int i = 0; i < 3; i++)
        {
            if (routineNames != null && i < routineNames.Length && routineNames[i] != null)
                routineNames[i].text = names[i];
            if (routineParts != null && i < routineParts.Length && routineParts[i] != null)
                routineParts[i].text = parts[i];
        }
    }

    // [추가] 신규 5종 포함 11종 기구별 타겟 부위 쉬운 한국어 설명 반환
    static string DescribeMachinePart(string step)
    {
        if (string.IsNullOrEmpty(step)) return "전신 균형 운동";
        if (step.Contains("어덕션")) return "허벅지 안쪽 · 골반 안정";
        if (step.Contains("레그컬")) return "허벅지 뒤쪽 (햄스트링 · 무릎 보호)";
        if (step.Contains("벤치프레스")) return "가슴 · 팔 뒤쪽 (삼두근)";
        if (step.Contains("계단") || step.Contains("스텝밀")) return "심폐 지구력 · 하체 체력";
        if (step.Contains("스쿼트")) return "허벅지 전반 · 엉덩이 (허리 지지)";
        if (step.Contains("레그프레스")) return "허벅지 · 엉덩이 근력";
        if (step.Contains("익스텐션")) return "허벅지 앞쪽 (대퇴사두)";
        if (step.Contains("체스트")) return "가슴 · 어깨 앞쪽";
        if (step.Contains("랫풀")) return "등 근육 · 상체 자세";
        if (step.Contains("암컬")) return "팔 앞쪽 (이두근)";
        if (step.Contains("풀업")) return "등 상부 · 팔 근력";
        if (step.Contains("GX")) return "전신 관절 이완 · 스트레칭";
        return "전신 균형 · 근력 강화";
    }

    void Fill(Data d)
    {
        if (d == null || body == null || body.Length < 4 || body[0] == null) return;
        current = d;
        body[0].text = d.ok; body[1].text = d.ask; body[2].text = d.next; body[3].text = d.check;
        if (sub != null) sub.text = d.date + "  ·  체험 기록: " + d.machine;
    }

    IEnumerator SaveImage()
    {
        if (buttons != null) buttons.SetActive(false); // 버튼은 이미지에 안 나오게 한다
        yield return new WaitForEndOfFrame();
        var tex = ScreenCapture.CaptureScreenshotAsTexture();
        if (buttons != null) buttons.SetActive(true);
        var png = tex.EncodeToPNG(); Destroy(tex);
        var name = $"요약카드_{DateTime.Now:yyyyMMdd_HHmm}.png";
#if UNITY_WEBGL && !UNITY_EDITOR
        DownloadFile(name, png, png.Length);
#else
        var path = Path.Combine(Application.persistentDataPath, name);
        File.WriteAllBytes(path, png);
        Debug.Log("[요약카드] 저장: " + path);
#endif
    }
}
