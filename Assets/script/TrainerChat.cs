using System.Runtime.InteropServices;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

// 화면 오른쪽 아래 큰 버튼(또는 T키)으로 대화창을 연다.
// 어르신이 글을 쓰지 않아도 되게 자주 묻는 질문을 버튼으로 두고, 그 답은 미리 써 둔 안전한 문장으로 바로 보여 준다.
// 직접 쓴 질문만 Gemini로 보낸다. 어떤 답이든 끝에 "현장 선생님이나 의사와 먼저 확인하세요"를 붙인다.
public class TrainerChat : MonoBehaviour
{
#if UNITY_WEBGL && !UNITY_EDITOR
    [DllImport("__Internal")] static extern string PromptInput(string message, string defaultText);
#endif
    [SerializeField] Font font;
    [SerializeField] GeminiClient client;
    [SerializeField] TrainerVoice voice;

    const string Disclaimer = "\n※ 현장 선생님이나 의사와 먼저 확인하세요.";

    // [수정] 유니티 인스펙터에서 최소 4개만 연결 (버튼 클릭·질문 답변은 전부 Unity OnClick에서 직접 관리!)
    [Header("ChatCanvas 최소 연결 (4개)")]
    [SerializeField] GameObject panel;      // ChatPopup
    [SerializeField] GameObject openBtn;    // Btn_OpenChat
    [SerializeField] InputField input;      // Input_Question
    [SerializeField] Text answer;           // Txt_Answer

    bool waiting;
    int ticket; // 늦게 도착한 옛 답을 버리기 위한 번호

    void Start()
    {
        if (input != null) input.onSubmit.AddListener(_ => Send());

#if UNITY_WEBGL && !UNITY_EDITOR
        // [유지] WebGL에서는 브라우저 입력창(PromptInput)으로 한글 입력 지원
        if (input != null)
        {
            input.interactable = false;
            var size = ((RectTransform)input.transform).rect.size;
            var ask = UiKit.Btn(input.transform, font, "", 1, size, Vector2.zero, new Color(0, 0, 0, 0));
            ask.onClick.AddListener(() => { input.text = PromptInput("궁금한 것을 써 주세요", input.text); Send(); });
        }
#endif
        // 시작할 때는 챗봇 팝업을 닫아둠
        if (panel != null) panel.SetActive(false);
    }

    void Update()
    {
        if (panel == null || openBtn == null) return; // [추가] 연결 전 에러 방지
        var kb = Keyboard.current;
        if (kb == null) return;
        // [수정] 입장 팝업 등 화면이 잠긴(Frozen) 상태에서는 열기 버튼을 숨긴다
        var showOpen = !panel.activeSelf && !ExerciseStation.InUse && !PlayerFreeze.Frozen;
        if (openBtn.activeSelf != showOpen) openBtn.SetActive(showOpen);
        if (showOpen && kb.tKey.wasPressedThisFrame) Toggle();
        else if (panel.activeSelf && kb.escapeKey.wasPressedThisFrame) Toggle();
    }



    // [추가] 질문 버튼 클릭 시 해당 질문을 바로 Gemini AI로 전송!
    public void AskAI(string question)
    {
        if (input != null) input.text = question;
        Send();
    }


    // [수정] public 추가 → Unity 버튼(Btn_OpenChat, Btn_close) OnClick()에서 바로 연결 가능
    public void Toggle()
    {
        if (panel == null || openBtn == null) return;
        var show = !panel.activeSelf;
        panel.SetActive(show);
        openBtn.SetActive(!show); // 창이 열려 있는 동안은 열기 버튼을 숨긴다
        if (show) { PlayerFreeze.Push(); if (answer != null) answer.text = "질문을 누르거나 아래에 직접 써 보세요."; }
        else { ticket++; waiting = false; PlayerFreeze.Pop(); } // 닫으면 기다리던 답은 버린다
    }

    // [수정] public 추가 → 질문 버튼 OnClick()에서 답변 문구를 인스펙터에 직접 입력 가능
    public void ShowAnswer(string text)
    {
        ticket++; waiting = false; // 기다리던 Gemini 답이 있으면 버린다
        if (answer != null) answer.text = text + Disclaimer;
        voice?.Say(text + " 현장 선생님이나 의사와 먼저 확인하세요.");
    }

    // [수정] public 추가 → 보내기 버튼(Btn_Send) OnClick()에서 바로 연결 가능
    public void Send()
    {
        if (input == null || answer == null || client == null) return;
        var text = input.text.Trim();
        if (waiting || text.Length == 0) return;

        waiting = true;
        var my = ++ticket;
        answer.text = "생각하는 중...";
        input.text = "";
        StartCoroutine(Watchdog(my));
        // 설문은 참고만 한다. 손님이 지금 쓴 질문이 우선이고, 질문과 상관없으면 설문 내용은 말하지 않게 한다.
        client.Ask($"[참고: 입장할 때 손님이 불편하다고 고른 자세는 '{DoorSurvey.Summary}'. 아래 질문에서 말한 내용이 항상 우선이며, 질문과 직접 관련이 없으면 이 참고는 언급하지 말 것]\n질문: {text}", reply =>
        {
            if (my != ticket) return; // 이미 시간이 지나 포기했거나 닫은 질문의 답이다
            ticket++; waiting = false;
            if (reply.StartsWith("[오류]")) { answer.text = "지금은 답을 가져오지 못했어요. 위의 질문 버튼을 눌러 보세요."; return; }
            answer.text = reply + Disclaimer;
            voice?.Say(reply + " 현장 선생님이나 의사와 먼저 확인하세요.");
        });
    }

    // 답이 너무 늦으면 계속 "생각하는 중"에 머물지 않고 다시 질문할 수 있게 풀어 준다
    System.Collections.IEnumerator Watchdog(int my)
    {
        yield return new WaitForSecondsRealtime(15f);
        if (my != ticket) yield break;
        ticket++; waiting = false;
        answer.text = "답이 늦어지고 있어요. 위의 질문 버튼을 눌러 보세요.";
        Debug.LogWarning("[TrainerChat] 15초 안에 답이 오지 않았습니다");
    }
}
