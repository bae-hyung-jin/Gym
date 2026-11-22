using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

// 버튼 OnClick()에 연결해서 원하는 씬으로 이동 + 로딩바/% 표시
public class SceneLoader : MonoBehaviour
{
    [Header("로딩 UI (선택)")]
    public Image loadingBarFill; // Fill Amount로 차오르는 노랑 바
    public Text percentText;     // "0%" ~ "100%" 표시 텍스트
    public float minLoadingTime = 0.9f; // 로딩바 모션이 부드럽게 보이도록 최소 시간(초)

    bool isLoading;

    public void LoadScene(string sceneName)
    {
        SceneManager.LoadScene(sceneName);
    }

    public void LoadSceneAsync(string sceneName)
    {
        if (isLoading) return;
        StartCoroutine(LoadRoutine(sceneName));
    }

    IEnumerator LoadRoutine(string sceneName)
    {
        isLoading = true;
        UpdateProgress(0f);
        yield return null;

        var op = SceneManager.LoadSceneAsync(sceneName);
        op.allowSceneActivation = false;

        float elapsed = 0f;
        float shown = 0f;

        while (!op.isDone)
        {
            elapsed += Time.unscaledDeltaTime;
            float realProgress = Mathf.Clamp01(op.progress / 0.9f);
            float timeProgress = minLoadingTime > 0f ? Mathf.Clamp01(elapsed / minLoadingTime) : 1f;
            float target = Mathf.Min(realProgress, timeProgress);

            shown = Mathf.MoveTowards(shown, target, Time.unscaledDeltaTime * 1.6f);
            UpdateProgress(shown);

            if (shown >= 0.999f && realProgress >= 0.999f)
            {
                UpdateProgress(1f);
                yield return new WaitForSecondsRealtime(0.1f);
                op.allowSceneActivation = true;
            }

            yield return null;
        }
    }

    void UpdateProgress(float value)
    {
        if (loadingBarFill != null)
        {
            if (loadingBarFill.type == Image.Type.Filled && loadingBarFill.sprite != null)
                loadingBarFill.fillAmount = value;
            else
                loadingBarFill.rectTransform.anchorMax = new Vector2(value, 1f);
        }
        if (percentText != null) percentText.text = Mathf.RoundToInt(value * 100f) + "%";
    }
}
