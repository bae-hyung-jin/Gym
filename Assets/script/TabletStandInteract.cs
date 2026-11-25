using UnityEngine;
using UnityEngine.InputSystem;

// [추가] 각 운동기구 옆 3D 태블릿 스탠드에 부착하는 인터랙션 스크립트
// 플레이어가 태블릿 가까이에서 F 키를 누르거나, 마우스로 3D 태블릿 화면을 클릭하면
// GymTabletGuide 태블릿 화면이 해당 운동기구 설명 페이지로 바로 열립니다!
public class TabletStandInteract : MonoBehaviour
{
    [Header("▼ [기구 도감 인덱스 (0~10)] 인스펙터에서 기구 변경 가능")]
    [Tooltip("0:체스트프레스 1:벤치프레스 2:랫풀다운 3:풀업바 4:암컬 5:파워레그프레스 6:레그익스텐션 7:라잉레그컬 8:힙어덕션 9:V스쿼트 10:천국의계단")]
    [SerializeField] int machineIndex = 0;
    [SerializeField] float interactRange = 2.6f;

    GymTabletGuide tabletGuide;
    Transform player;
    Collider col;

    void Start()
    {
        col = GetComponent<Collider>();
        tabletGuide = FindFirstObjectByType<GymTabletGuide>();
        var p = GameObject.FindGameObjectWithTag("Player");
        if (p != null) player = p.transform;
    }

    void Update()
    {
        if (PlayerFreeze.Frozen || ExerciseStation.InUse) return;
        if (tabletGuide == null) tabletGuide = FindFirstObjectByType<GymTabletGuide>();
        if (player == null)
        {
            var p = GameObject.FindGameObjectWithTag("Player");
            if (p != null) player = p.transform;
        }
        if (tabletGuide == null || player == null) return;

        Vector3 diff = player.position - transform.position;
        diff.y = 0f;
        if (diff.magnitude > interactRange) return;

        var kb = Keyboard.current;
        if (kb != null && kb.fKey.wasPressedThisFrame)
        {
            OpenThisMachine();
            return;
        }

        // 마우스 왼쪽 버튼으로 3D 태블릿을 직접 클릭해도 설명 열기
        var mouse = Mouse.current;
        if (mouse != null && mouse.leftButton.wasPressedThisFrame && col != null)
        {
            var cam = Camera.main;
            if (cam != null)
            {
                Ray ray = cam.ScreenPointToRay(mouse.position.ReadValue());
                if (col.Raycast(ray, out _, interactRange + 2f))
                    OpenThisMachine();
            }
        }
    }

    public void OpenThisMachine()
    {
        if (tabletGuide == null) tabletGuide = FindFirstObjectByType<GymTabletGuide>();
        if (tabletGuide == null) return;
        tabletGuide.SelectMachine(machineIndex);
        tabletGuide.OpenTablet();
    }
}
