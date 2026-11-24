using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

// 문 앞 트리거 또는 에디터 UI 팝업에서 불편한 자세를 선택받아 AI 트레이너(DoorSurvey.Summary)에 전달한다.
public class DoorSurvey : MonoBehaviour
{
    [SerializeField] Font font;
    [SerializeField] DoorTrigger door;
    [SerializeField] string playerTag = "Player";
    [SerializeField] string[] options = { "허리를 숙이기 불편해요", "무릎을 굽히기 불편해요", "팔을 들어올리기 불편해요", "오래 서 있기 힘들어요" };

    // 트레이너에게 질문할 때 같이 보낸다.
    public static string Summary { get; private set; } = "없음";

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void ResetSummary() => Summary = "없음";

    readonly List<string> picked = new();
    bool done;
    GameObject root;

    static readonly Color OffColor = new Color(0.165f, 0.204f, 0.278f, 1f); // #2A3447
    static readonly Color OnColor  = new Color(0.133f, 0.651f, 0.498f, 1f); // #22A67F

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
        bool isOn;
        if (picked.Remove(raw))
        {
            isOn = false;
        }
        else
        {
            picked.Add(raw);
            isOn = true;
        }

        if (btn.targetGraphic != null)
            btn.targetGraphic.color = isOn ? OnColor : OffColor;
        label.text = isOn ? ("✓ " + raw) : raw;

        Summary = picked.Count == 0 ? "없음" : string.Join(", ", picked);
        Debug.Log("[설문] 불편한 자세: " + Summary);
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
