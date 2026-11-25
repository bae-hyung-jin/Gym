using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

// [추가] 헬스장 태블릿 기구 도감 UI 컨트롤러
// 05_UI/ExerciseCanvas/GymTabletPanel 의 버튼과 텍스트를 인스펙터에서 직접 연결·편집할 수 있습니다.
public class GymTabletGuide : MonoBehaviour
{
    [Serializable]
    public class MachineEntry
    {
        public string machineName;
        public string targetPart;
        [TextArea(2, 3)] public string howToUse;
        [TextArea(2, 3)] public string safetyTip;
        public string recommendedFor;
        public string searchKeyword;
    }

    [Header("▼ [씬 UI 연결] 05_UI/ExerciseCanvas 안의 태블릿 UI 오브젝트")]
    [SerializeField] GameObject tabletPanel;     // 태블릿 전체 팝업 패널
    [SerializeField] GameObject openButton;      // 우측 상단 '기구 도감 (G)' 열기 버튼
    [SerializeField] Text detailTitleText;       // 우측 상세: 기구 이름
    [SerializeField] Text detailPartText;        // 우측 상세: 운동 부위
    [SerializeField] Text detailHowToText;       // 우측 상세: 사용 방법
    [SerializeField] Text detailCautionText;     // 우측 상세: 안전 팁
    [SerializeField] Text detailRecommendText;   // 우측 상세: 추천 대상
    [SerializeField] Button[] machineButtons;    // 좌측 11종 기구 버튼 (선택 하이라이트용)

    [Header("▼ [기구 목록 (인스펙터에서 자유롭게 문구 수정 가능)]")]
    [SerializeField] List<MachineEntry> machines = new()
    {
        new MachineEntry { machineName = "체스트프레스", targetPart = "가슴 · 팔 뒤쪽 · 상체 밀기", howToUse = "등받이에 등을 편하게 붙이고 손잡이를 잡은 뒤, 앞쪽으로 팔을 천천히 뻗어 밀어 주세요.", safetyTip = "밀 때 숨을 내쉬고, 어깨 앞쪽에 통증이 있으면 범위를 줄여 주세요.", recommendedFor = "추천: 초보자 · 허리 부담 없이 상체 근력을 키우고 싶은 분", searchKeyword = "체스트" },
        new MachineEntry { machineName = "플레이트 로디드 벤치프레스", targetPart = "가슴 전체 · 어깨 앞쪽 · 삼두근", howToUse = "벤치에 등을 대고 양발을 바닥에 단단히 디딘 뒤, 양 손잡이를 천장 방향으로 부드럽게 밀어 올리세요.", safetyTip = "어깨가 귀 쪽으로 올라가지 않게 가슴을 펴고, 팔꿈치를 완전히 잠그지 마세요.", recommendedFor = "추천: 상체 근력을 한 단계 더 탄탄하게 키우고 싶은 분", searchKeyword = "벤치프레스" },
        new MachineEntry { machineName = "랫풀다운", targetPart = "등 근육 · 바른 상체 자세", howToUse = "의자에 앉아 위쪽 바를 넓게 잡고, 가슴 위쪽을 향해 팔꿈치를 아래로 천천히 당겨 내리세요.", safetyTip = "허리를 뒤로 과하게 젖히지 말고, 등을 조이는 느낌으로 부드럽게 당기세요.", recommendedFor = "추천: 굽은 등을 펴고 등 근력을 기르고 싶은 분", searchKeyword = "랫풀" },
        new MachineEntry { machineName = "풀업바", targetPart = "등 상부 · 팔 전체 근력", howToUse = "위쪽 바를 어깨너비보다 살짝 넓게 잡고, 가슴이 바에 가까워지도록 천천히 끌어올리세요.", safetyTip = "어깨가 아프면 무리하게 매달리지 말고 편한 범위까지만 천천히 연습하세요.", recommendedFor = "추천: 상체 전반의 당기는 힘과 악력을 기르고 싶은 분", searchKeyword = "풀업" },
        new MachineEntry { machineName = "암컬 머신", targetPart = "팔 앞쪽 (이두근 · 물건 들기 근력)", howToUse = "앞쪽 패드에 팔꿈치를 안정적으로 고정하고, 손잡이를 어깨 쪽으로 천천히 접어 올리세요.", safetyTip = "어깨나 허리 반동을 쓰지 말고 팔 앞쪽 힘으로 부드럽게 올렸다 내려 주세요.", recommendedFor = "추천: 장바구니·물건 들기 등 일상 팔 힘을 기르고 싶은 분", searchKeyword = "암컬" },
        new MachineEntry { machineName = "파워 레그프레스", targetPart = "허벅지 전반 · 엉덩이 근력", howToUse = "등받이에 허리를 꼭 붙이고 발판 중앙에 발을 올린 뒤, 다리 힘으로 발판을 천천히 밀어 주세요.", safetyTip = "무릎을 끝까지 쫙 펴서 잠그지 말고, 약간 여유를 둔 상태로 반복하세요.", recommendedFor = "추천: 허리 부담을 줄이면서 탄탄한 하체 힘을 기르고 싶은 분", searchKeyword = "레그프레스" },
        new MachineEntry { machineName = "레그 익스텐션", targetPart = "허벅지 앞쪽 (대퇴사두근 · 무릎 지지)", howToUse = "의자에 깊게 앉아 손잡이를 잡고, 발목 패드를 들어 올리듯 무릎을 천천히 펴 주세요.", safetyTip = "무릎을 탁 튕기지 말고 끝에서 잠깐 멈춘 뒤 천천히 내려 주세요.", recommendedFor = "추천: 무릎 주변 허벅지 앞쪽 근육을 안전하게 강화하고 싶은 분", searchKeyword = "익스텐션" },
        new MachineEntry { machineName = "라잉 레그컬", targetPart = "허벅지 뒤쪽 (햄스트링 · 무릎 보호)", howToUse = "배와 허벅지를 패드에 대고 엎드린 뒤, 발목 패드를 엉덩이 쪽으로 천천히 접어 올리세요.", safetyTip = "허리가 과하게 꺾이지 않도록 상체를 패드에 붙이고 천천히 내리세요.", recommendedFor = "추천: 허벅지 뒤쪽 근력을 길러 무릎 관절을 보호하고 싶은 분", searchKeyword = "레그컬" },
        new MachineEntry { machineName = "힙 어덕션", targetPart = "허벅지 안쪽 · 골반 안정화", howToUse = "의자에 등을 편히 붙이고 손잡이를 잡은 뒤, 양 무릎을 안쪽으로 천천히 모았다가 풀어 주세요.", safetyTip = "허리가 등받이에서 뜨지 않게 유지하고, 모을 때 숨을 내쉬세요.", recommendedFor = "추천: 걸을 때 중심 잡기·골반 안정화가 필요한 분", searchKeyword = "어덕션" },
        new MachineEntry { machineName = "V-스쿼트", targetPart = "허벅지 전반 · 엉덩이 (허리 지지)", howToUse = "어깨 패드 아래로 들어가 등을 기대고, 무릎을 굽혀 천천히 앉았다가 발판으로 밀어 일어나세요.", safetyTip = "무릎이 안쪽으로 모이지 않게 발끝 방향을 유지하고, 호흡을 참지 마세요.", recommendedFor = "추천: 등받이 도움을 받으며 안정적으로 스쿼트를 하고 싶은 분", searchKeyword = "스쿼트" },
        new MachineEntry { machineName = "천국의 계단 (스텝밀)", targetPart = "심폐 지구력 · 하체 전체 체력", howToUse = "양쪽 손잡이를 가볍게 잡고 발바닥 전체로 계단을 밟으며 일정한 리듬으로 올라가세요.", safetyTip = "상체가 너무 숙여지지 않게 시선은 정면을 보고, 숨이 차면 바로 멈추세요.", recommendedFor = "추천: 걷기 체력과 심폐 지구력을 함께 기르고 싶은 분", searchKeyword = "계단" },
    };

    static readonly Color BtnNormal   = new Color(0.16f, 0.22f, 0.34f, 1f);
    static readonly Color BtnSelected = new Color(0.13f, 0.65f, 0.52f, 1f);

    int selectedIndex = 0;

    void Start()
    {
        if (tabletPanel != null) tabletPanel.SetActive(false);
        SelectMachine(0);
    }

    void Update()
    {
        var kb = Keyboard.current;
        if (kb == null || tabletPanel == null) return;

        bool canShowOpen = !tabletPanel.activeSelf && !ExerciseStation.InUse && !PlayerFreeze.Frozen;
        if (openButton != null && openButton.activeSelf != canShowOpen)
            openButton.SetActive(canShowOpen);

        if (canShowOpen && kb.gKey.wasPressedThisFrame) OpenTablet();
        else if (tabletPanel.activeSelf && kb.escapeKey.wasPressedThisFrame) CloseTablet();
    }

    // Unity 버튼 OnClick()에서 바로 연결
    public void OpenTablet()
    {
        if (tabletPanel == null || tabletPanel.activeSelf) return;
        tabletPanel.SetActive(true);
        if (openButton != null) openButton.SetActive(false);
        PlayerFreeze.Push();
        SelectMachine(selectedIndex);
    }

    public void CloseTablet()
    {
        if (tabletPanel == null || !tabletPanel.activeSelf) return;
        tabletPanel.SetActive(false);
        PlayerFreeze.Pop();
    }

    // 좌측 기구 버튼 OnClick(int index)에서 바로 호출
    public void SelectMachine(int index)
    {
        if (machines == null || machines.Count == 0) return;
        selectedIndex = Mathf.Clamp(index, 0, machines.Count - 1);
        var m = machines[selectedIndex];

        if (detailTitleText != null)     detailTitleText.text     = m.machineName;
        if (detailPartText != null)      detailPartText.text      = $"운동 부위  ·  {m.targetPart}";
        if (detailHowToText != null)     detailHowToText.text     = $"[사용 방법]\n{m.howToUse}";
        if (detailCautionText != null)   detailCautionText.text   = $"[안전 포인트]\n{m.safetyTip}";
        if (detailRecommendText != null) detailRecommendText.text = m.recommendedFor;

        if (machineButtons != null)
        {
            for (int i = 0; i < machineButtons.Length; i++)
            {
                if (machineButtons[i] != null && machineButtons[i].image != null)
                    machineButtons[i].image.color = (i == selectedIndex) ? BtnSelected : BtnNormal;
            }
        }
    }

    // 태블릿 하단 '이 기구로 이동 →' 버튼 OnClick()
    public void MoveToSelectedMachine()
    {
        if (machines == null || selectedIndex < 0 || selectedIndex >= machines.Count) return;
        string kw = machines[selectedIndex].searchKeyword;
        var playerGo = GameObject.FindGameObjectWithTag("Player");
        if (playerGo == null) { CloseTablet(); return; }

        var stations = FindObjectsByType<ExerciseStation>(FindObjectsSortMode.None);
        foreach (var st in stations)
        {
            if (st == null || !st.enabled) continue;
            string goName = st.gameObject.name;
            bool hit = st.MachineDisplayName.Contains(kw)
                || (kw == "어덕션" && goName.Contains("HipAdduction"))
                || (kw == "레그컬" && goName.Contains("LyingLegCurl"))
                || (kw == "벤치프레스" && goName.Contains("BenchPress"))
                || (kw == "계단" && goName.Contains("StairClimber"))
                || (kw == "스쿼트" && goName.Contains("VSquat"))
                || (kw == "암컬" && goName.Contains("ArmCurl"))
                || (kw == "풀업" && goName.Contains("PullUp"))
                || (kw == "레그프레스" && goName.Contains("PowerLegPress"));
            if (!hit) continue;

            Transform t = st.transform;
            Vector3 fwd = new Vector3(t.forward.x, 0f, t.forward.z).normalized;
            if (fwd.sqrMagnitude < 0.01f) fwd = Vector3.forward;
            Vector3 right = Vector3.Cross(Vector3.up, fwd).normalized;
            bool flipFront = goName.Contains("HipAdduction") || goName.Contains("StairClimber") || goName.Contains("BenchPress");
            Vector3 pos = t.position + (flipFront ? (-fwd * 1.6f + right * 1.6f) : (fwd * 1.8f + right * 1.2f));
            float yaw = Quaternion.LookRotation((t.position - pos).normalized, Vector3.up).eulerAngles.y;

            CloseTablet();
            var cc = playerGo.GetComponent<CharacterController>();
            if (cc != null) cc.enabled = false;
            playerGo.transform.position = new Vector3(pos.x, playerGo.transform.position.y, pos.z);
            playerGo.transform.rotation = Quaternion.Euler(0f, yaw, 0f);
            if (cc != null) cc.enabled = true;
            return;
        }
        CloseTablet();
    }
}
